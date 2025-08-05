"""
optimade_mcp_server.main
────────────────────────
• `list_resources`  : 暴露文档、白名单、查询结果
• `list_tools`      : query_optimade / list_providers / lint_filter
• `read_resource`   : 让 cline 的 access_mcp_resource 生效
• `call_tool`       : 分派三种工具
"""

import asyncio, logging, os, json, uuid
from pathlib import Path
from dotenv import load_dotenv
import importlib.resources as pkg_resources
from optimade.client import OptimadeClient
from optimade.filterparser import LarkParser
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource
from pydantic import AnyUrl

# ── 0. 环境与日志 ──────────────────────────────────────────────────────────
load_dotenv()
os.environ["HTTP_PROXY"]  = os.getenv("HTTP_PROXY", "")
os.environ["HTTPS_PROXY"] = os.getenv("HTTPS_PROXY", "")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("optimade_mcp_server")

# ── 1. 读取配置 (少量代表 provider + 预设) ──────────────────────────────────
def load_config() -> dict:
    try:
        with pkg_resources.files("optimade_mcp_server.config") \
                          .joinpath("optimade_config.json") \
                          .open("r", encoding="utf-8") as f:
            logger.info("使用打包内配置文件")
            return json.load(f)
    except Exception:
        dev_path = Path(__file__).parent / "config" / "optimade_config.json"
        logger.info("使用开发路径配置")
        return json.loads(dev_path.read_text(encoding="utf-8"))

CONFIG             = load_config()
DEFAULT_BASE_URLS   = CONFIG.get("optimadeBaseUrls", [])
FILTER_PRESETS      = CONFIG.get("filterPresets", [])

# ── 2. 路径常量 & 读取静态资源 ─────────────────────────────────────────────
PKG_DIR  = Path(__file__).parent
DOCS_DIR = PKG_DIR / "docs"
RES_DIR  = PKG_DIR / "results"
RES_DIR.mkdir(exist_ok=True)

def safe_read(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning(f"缺失文件: {path}")
    return "<<FILE MISSING>>"

FILTER_DOC_TEXT = safe_read(DOCS_DIR / "optimade_filters_original.md")
ASK_PROMPT_TEXT = safe_read(DOCS_DIR / "ask_for_provider.txt")
QUERY_JSON      = safe_read(DOCS_DIR / "queryable_props.json")
try:
    QUERYABLE = set(json.loads(QUERY_JSON)["queryableProps"])
except Exception:
    QUERYABLE = set()

# 用于挂载运行期结果
_dynamic_results: dict[str, Path] = {}

# ── 3. MCP Server 对象 ─────────────────────────────────────────────────────
app = Server("optimade")

# 3.1 list_resources --------------------------------------------------------
@app.list_resources()
async def list_resources() -> list[Resource]:
    static = [
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
            description="Representative providers used when baseUrls omitted.",
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
            description="System prompt guiding LLM when baseUrls missing (prefers white‑list fields).",
            content=TextContent(type="text", text=ASK_PROMPT_TEXT),
        ),
        Resource(
            uri="optimade://spec/queryable_props",
            name="Queryable Property White‑List",
            mimeType="application/json",
            description="All identifiers marked 'Query: MUST be queryable property'.",
            content=TextContent(type="text", text=QUERY_JSON),
        )
    ]

    dynamic = [
        Resource(
            uri=f"optimade://results/{k}",
            name=f"Query Result {k[:8]}",
            mimeType="application/json",
            description="Full JSON returned by previous query_optimade.",
            content=TextContent(type="text", text=p.read_text(encoding="utf-8")),
        )
        for k, p in _dynamic_results.items()
    ]
    return static + dynamic

# 3.2 read_resource ---------------------------------------------------------
def _make_text(text: str, mime: str = "text/plain") -> TextContent:
    return TextContent(type="text", text=text, mimeType=mime)

@app.read_resource()
async def read_resource(uri) -> TextContent:
    uri = str(uri)

    if uri == "optimade://docs/filters":
        return _make_text(FILTER_DOC_TEXT, "text/markdown")

    if uri == "optimade://docs/providers":
        return _make_text(json.dumps({"baseUrls": DEFAULT_BASE_URLS}, indent=2),
                          "application/json")

    if uri == "optimade://docs/filter_presets":
        return _make_text(json.dumps(FILTER_PRESETS, indent=2),
                          "application/json")

    if uri == "optimade://prompts/ask_for_provider":
        return _make_text(ASK_PROMPT_TEXT, "text/plain")

    if uri == "optimade://spec/queryable_props":
        return _make_text(QUERY_JSON, "application/json")

    if uri.startswith("optimade://results/"):
        key = uri.rsplit("/", 1)[-1]
        path = _dynamic_results.get(key)
        if path and path.exists():
            return _make_text(path.read_text(encoding="utf-8"), "application/json")

    raise ValueError(f"Resource not found: {uri}")



# 3.3 list_tools ------------------------------------------------------------
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_optimade",
            description=(
                "Query OPTIMADE providers with a custom filter.\n"
                "• If baseUrls omitted, falls back to default providers.\n"
                "• Runs lint first: syntax errors block query; non‑white‑list fields only warn."
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
        Tool(
            name="lint_filter",
            description="Return 'ok', 'warn: …', or 'syntax error: …' for a filter string.",
            inputSchema={
                "type": "object",
                "properties": {"filter": {"type": "string"}},
                "required": ["filter"]
            }
        ),
        Tool(
            name="list_providers",
            description="Fetch global public OPTIMADE provider URLs via OptimadeClient.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

# ── 3.4 工具实现 -----------------------------------------------------------
@app.call_tool()
async def call_tool(name: str, args: dict) -> list[TextContent]:
    if name == "lint_filter":
        return [_lint_filter(args["filter"])]
    if name == "list_providers":
        return [_handle_list_providers()]
    if name == "query_optimade":
        return await _handle_query_optimade(args)
    raise ValueError("Unknown tool")

# --- lint_filter 内部逻辑 ---------------------------------------------------
def _lint_filter(filt: str) -> TextContent:
    # 1. 语法
    try:
        tree = LarkParser().parse(filt)
    except Exception as e:
        return TextContent(type="text", text=f"syntax error: {e}")

    # 2. 字段收集
    identifiers = {
        tok.value for tok in tree.scan_values(
            lambda v: hasattr(v, 'type') and v.type == 'IDENTIFIER'
        )
    }
    illegal = sorted(identifiers - QUERYABLE)
    msg = "ok" if not illegal else ("warn: " + ", ".join(illegal))
    return TextContent(type="text", text=msg)

# --- list_providers --------------------------------------------------------
def _handle_list_providers() -> TextContent:
    try:
        urls = sorted(OptimadeClient().base_urls)
        text = "Discovered OPTIMADE provider URLs:\n" + "\n".join(f"- {u}" for u in urls)
    except Exception as e:
        text = f"Failed to fetch provider list: {e}"
    return TextContent(type="text", text=text)

# --- query_optimade --------------------------------------------------------
async def _handle_query_optimade(args: dict) -> list[TextContent]:
    filt = args["filter"]
    urls = args.get("baseUrls") or DEFAULT_BASE_URLS or ["https://optimade.fly.dev"]

    # 0. lint
    lint_msg = _lint_filter(filt).text
    if lint_msg.startswith("syntax error"):
        return [TextContent(type="text", text=f"lint failed: {lint_msg}")]

    warn_note = ""
    if lint_msg.startswith("warn:"):
        warn_note = f"(⚠ 非白名单字段: {lint_msg[5:]})\n"

    # 1. 查询
    try:
        results = OptimadeClient(base_urls=urls).get(filt)
    except Exception as e:
        return [TextContent(type="text", text=f"查询失败: {e}")]

    # 2. 统一拆包
    if isinstance(results, dict):
        raw_json = results
        if "structures" in raw_json:                # 多 provider 聚合格式
            provider_map = next(iter(raw_json["structures"].values()))
            data_list = []
            total = 0
            for body in provider_map.values():
                data = body.get("data", [])
                total += body.get("meta", {}).get("data_available", len(data))
                data_list.extend(data)
        else:
            data_list = raw_json.get("data", [])
            total = len(data_list)
    else:
        raw_json = results.raw
        data_list = results.data
        total = results.meta.get("data_available", len(data_list))

    # 3. 保存完整 JSON
    key  = uuid.uuid4().hex
    path = RES_DIR / f"{key}.json"
    path.write_text(json.dumps(raw_json, indent=2, ensure_ascii=False))
    _dynamic_results[key] = path

    # 4. 摘要
    preview = []
    for d in data_list[:5]:
        if isinstance(d, dict):
            pid   = d.get("id")
            attrs = d.get("attributes", {})
        else:
            pid   = d.id
            attrs = d.attributes
        preview.append({"id": pid, "formula": attrs.get("chemical_formula_reduced")})

    summary = (
        warn_note +
        f"Total matched structures: {total}\n"
        f"Preview (first {len(preview)}):\n"
        f"{json.dumps(preview, indent=2, ensure_ascii=False)}\n\n"
        f"Full result saved to resource: optimade://results/{key}\n"
        f"Use `resources/read` to download."
    )
    return [TextContent(type="text", text=summary)]

# ── 4. 启动 ────────────────────────────────────────────────────────────────
async def main():
    from mcp.server.stdio import stdio_server
    logger.info("🔌 OPTIMADE MCP Server started")
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
