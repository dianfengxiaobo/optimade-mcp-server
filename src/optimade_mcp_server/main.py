import asyncio, logging, os, json, uuid
from pathlib import Path
from dotenv import load_dotenv
import importlib.resources as pkg_resources
from optimade.client import OptimadeClient
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource

# ── 0 环境与日志 ───────────────────────────────────────────────────────────
load_dotenv()
os.environ["HTTP_PROXY"]  = os.getenv("HTTP_PROXY", "")
os.environ["HTTPS_PROXY"] = os.getenv("HTTPS_PROXY", "")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("optimade_mcp_server")

# ── 1 读取配置 ─────────────────────────────────────────────────────────────
def load_config() -> dict:
    try:
        with pkg_resources.files("optimade_mcp_server.config") \
                          .joinpath("optimade_config.json") \
                          .open("r", encoding="utf-8") as f:
            logger.info("使用打包内配置文件")
            return json.load(f)
    except Exception:
        dev_path = Path(__file__).parent / "config" / "optimade_config.json"
        return json.loads(dev_path.read_text(encoding="utf-8"))

CONFIG             = load_config()
DEFAULT_BASE_URLS   = CONFIG.get("optimadeBaseUrls", [])
FILTER_PRESETS      = CONFIG.get("filterPresets", [])

# ── 2 常量路径 ─────────────────────────────────────────────────────────────
PKG_DIR   = Path(__file__).parent
DOCS_DIR  = PKG_DIR / "docs"
RES_DIR   = PKG_DIR / "results"
RES_DIR.mkdir(exist_ok=True)

FILTER_DOC_TEXT = (DOCS_DIR / "optimade_filters_original.md").read_text(encoding="utf-8")
ASK_PROMPT_TEXT = (DOCS_DIR / "ask_for_provider.txt").read_text(encoding="utf-8")

# 用于动态追加结果资源
_dynamic_results: dict[str, Path] = {}

# ── 3 MCP Server ───────────────────────────────────────────────────────────
app = Server("optimade")

# 3.1 静态 + 动态资源
@app.list_resources()
async def list_resources() -> list[Resource]:
    static_resources = [
        Resource(
            uri="optimade://docs/filters",
            name="OPTIMADE Filter Reference",
            mimeType="text/markdown",
            description="Complete OPTIMADE filter grammar.",
            content=TextContent(type="text", text=FILTER_DOC_TEXT),
        ),
        Resource(
            uri="optimade://docs/providers",
            name="Default Provider URL List",
            mimeType="application/json",
            description="Representative providers used when 'baseUrls' is omitted.",
            content=TextContent(
                type="text",
                text=json.dumps({"baseUrls": DEFAULT_BASE_URLS}, indent=2, ensure_ascii=False),
            ),
        ),
        Resource(
            uri="optimade://docs/filter_presets",
            name="OPTIMADE Filter Presets",
            mimeType="application/json",
            description="Named filter snippets for inspiration.",
            content=TextContent(
                type="text",
                text=json.dumps(FILTER_PRESETS, indent=2, ensure_ascii=False),
            ),
        ),
        Resource(
            uri="optimade://prompts/ask_for_provider",
            name="Prompt: ask_for_provider",
            mimeType="text/plain",
            description="System prompt that guides LLM when baseUrls are missing.",
            content=TextContent(type="text", text=ASK_PROMPT_TEXT),
        ),
    ]

    # 动态查询结果
    dynamic_resources = [
        Resource(
            uri=f"optimade://results/{key}",
            name=f"Query Result {key[:8]}",
            mimeType="application/json",
            description="Full JSON returned by a previous query_optimade call.",
            content=TextContent(type="text", text=path.read_text(encoding="utf-8")),
        )
        for key, path in _dynamic_results.items()
    ]
    return static_resources + dynamic_resources


@app.read_resource()
async def read_resource(uri: str) -> TextContent:
    # 静态部分
    static = {
        "optimade://docs/filters": TextContent(type="text", text=FILTER_DOC_TEXT),
        "optimade://docs/providers": TextContent(
            type="text",
            text=json.dumps({"baseUrls": DEFAULT_BASE_URLS}, indent=2, ensure_ascii=False),
        ),
        "optimade://docs/filter_presets": TextContent(
            type="text",
            text=json.dumps(FILTER_PRESETS, indent=2, ensure_ascii=False),
        ),
        "optimade://prompts/ask_for_provider": TextContent(type="text", text=ASK_PROMPT_TEXT),
    }
    if uri in static:
        return static[uri]

    # 动态查询结果
    if uri.startswith("optimade://results/"):
        key = uri.rsplit("/", 1)[-1]
        path = _dynamic_results.get(key)
        if path and path.exists():
            return TextContent(type="text", text=path.read_text(encoding="utf-8"))

    raise ValueError(f"Resource not found: {uri}")


# 3.2 工具定义
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # 3.2.1 查询工具（移除分页参数）
        Tool(
            name="query_optimade",
            description=(
                "Query OPTIMADE providers with a custom filter.\n"
                "• `filter` mandatory; `baseUrls` optional.\n"
                "• If `baseUrls` omitted, falls back to resource `optimade://docs/providers`.\n"
                "• Returns a summary and saves full result as downloadable resource."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string"},
                    "baseUrls": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["filter"]
            }
        ),
        # 3.2.2 新增：实时抓取全部 Provider 列表
        Tool(
            name="list_providers",
            description=(
                "Fetch the current global OPTIMADE provider list via OptimadeClient "
                "and return as JSON."
            ),
            inputSchema={"type": "object", "properties": {}}
        )
    ]

# 3.3 工具实现
@app.call_tool()
async def call_tool(name: str, args: dict) -> list[TextContent]:
    if name == "query_optimade":
        return await _handle_query_optimade(args)
    elif name == "list_providers":
        return await _handle_list_providers()
    else:
        raise ValueError("Unknown tool")

# ── 3.3.a 查询工具逻辑 ────────────────────────────────────────────────────
async def _handle_query_optimade(args: dict) -> list[TextContent]:
    filt = args["filter"]
    urls = args.get("baseUrls") or DEFAULT_BASE_URLS

    if not urls:
        urls = ["https://optimade.fly.dev"]

    client = OptimadeClient(base_urls=urls)
    try:
        results = client.get(filt)
    except Exception as e:
        return [TextContent(type="text", text=f"查询失败: {e}")]

    results, total, preview_block = None, 0, []

    try:
        results = client.get(filt, page_limit=page_limit, page_offset=page_off)
    except Exception as e:
        return [TextContent(type="text", text=f"查询失败: {e}")]

    # ------- ① 兼容 dict / OptimadeQueryResults ------------------------------
    if isinstance(results, dict):
        raw_json = results
        total    = len(raw_json.get("data", []))
        data     = raw_json.get("data", [])
    else:
        raw_json = results.raw
        total    = results.meta.get("data_available", len(results.data))
        data     = results.data

    preview_block = [
        {
            "id": (d["id"] if isinstance(d, dict) else d.id),
            "formula": (
                d["attributes"].get("chemical_formula_reduced")
                if isinstance(d, dict) else d.attributes.get("chemical_formula_reduced")
            )
        } for d in data[:5]
    ]

    # ------- ② 保存完整 JSON ---------------------------------------------------
    key  = uuid.uuid4().hex
    path = RES_DIR / f"{key}.json"
    path.write_text(json.dumps(raw_json, indent=2, ensure_ascii=False))
    _dynamic_results[key] = path

    # 预览摘要
    total = results.meta.get("data_available", len(results.data))
    preview = [
        {
            "id": r.id,
            "formula": r.attributes.get("chemical_formula_reduced"),
            "url": r.links.self
        }
        for r in results.data[:min(len(results.data), 5)]
    ]

    return [TextContent(type="text")]

# ── 3.3.b Provider 抓取工具 ───────────────────────────────────────────────
async def _handle_list_providers() -> list[TextContent]:
    try:
        provider_client = OptimadeClient()   # Discover mode
        urls = sorted(provider_client.base_urls)
        text = "Discovered OPTIMADE provider URLs:\n" + "\n".join(f"- {u}" for u in urls)
    except Exception as e:
        text = f"Failed to fetch provider list: {e}"
    return [TextContent(type="text", text=text)]

# ── 4 启动 ────────────────────────────────────────────────────────────────
async def main():
    from mcp.server.stdio import stdio_server
    logger.info("🔌 OPTIMADE MCP Server started")
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
