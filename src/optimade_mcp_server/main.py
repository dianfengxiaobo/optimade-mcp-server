import asyncio
import logging
import os
import json
from dotenv import load_dotenv
from pathlib import Path
import importlib.resources as pkg_resources
from optimade.client import OptimadeClient
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource

# ── 0 环境 ------------------------------------------------------------------
load_dotenv()
os.environ["HTTP_PROXY"]  = os.getenv("HTTP_PROXY", "")
os.environ["HTTPS_PROXY"] = os.getenv("HTTPS_PROXY", "")

logger = logging.getLogger("optimade_mcp_server")
logging.basicConfig(level=logging.INFO)

# ── 1 读取配置 --------------------------------------------------------------
def load_config() -> dict:
    """优先尝试打包路径；若失败改读开发路径。"""
    try:
        with pkg_resources.files("optimade_mcp_server.config") \
                          .joinpath("optimade_config.json") \
                          .open("r", encoding="utf-8") as f:
            logger.info("使用打包内配置文件")
            return json.load(f)
    except Exception as e:
        logger.warning(f"尝试加载打包配置失败: {e}")

    try:
        dev_path = Path(__file__).parent / "config" / "optimade_config.json"
        with open(dev_path, "r", encoding="utf-8") as f:
            logger.info("使用开发路径配置")
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return {}

CONFIG            = load_config()
DEFAULT_BASE_URLS = CONFIG.get("optimadeBaseUrls", [])
FILTER_PRESETS    = CONFIG.get("filterPresets", [])    # 仅做参考资源

# ── 2 资源文件 --------------------------------------------------------------
DOCS_DIR            = Path(__file__).parent / "docs"
FILTER_DOC_TEXT     = (DOCS_DIR / "optimade_filters_original.md").read_text(encoding="utf-8")
ASK_PROMPT_TEXT = (DOCS_DIR / "ask_for_provider.txt").read_text(encoding="utf-8")

# ── 3 MCP Server ------------------------------------------------------------
app = Server("optimade")

# 3.1 Resource 列表
@app.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="optimade://docs/filters",
            name="OPTIMADE Filter Reference (original)",
            mimeType="text/markdown",
            description="Complete filter grammar & examples.",
            content=TextContent(type="text", text=FILTER_DOC_TEXT),
        ),
        Resource(
            uri="optimade://docs/providers",
            name="OPTIMADE Provider URL List",
            mimeType="application/json",
            description="Default baseUrls used when user omits the field.",
            content=TextContent(
                type="text",
                text=json.dumps({"baseUrls": DEFAULT_BASE_URLS}, indent=2, ensure_ascii=False),
            ),
        ),
        Resource(
            uri="optimade://docs/filter_presets",
            name="OPTIMADE Filter Presets (reference only)",
            mimeType="application/json",
            description="Named filter snippets for user inspiration; "
                        "tool no longer accepts 'preset' parameter.",
            content=TextContent(
                type="text",
                text=json.dumps(FILTER_PRESETS, indent=2, ensure_ascii=False),
            ),
        ),
        Resource(
            uri="optimade://prompts/ask_for_provider",
            name="Prompt: ask_for_provider",
            mimeType="text/plain",
            description="Instructs LLM to query provider list when user omits baseUrls.",
            content=TextContent(type="text", text=ASK_PROMPT_TEXT),
        ),
    ]

# 3.2 Tool 列表
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_optimade",
            description=(
                "Query OPTIMADE providers with a custom filter.\n"
                "• `filter` is mandatory; `baseUrls` is optional.\n"
                "• If `baseUrls` is omitted, the tool falls back to the "
                "default list in resource `optimade://docs/providers`.\n"
                "• Filter grammar: resource `optimade://docs/filters`."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "OPTIMADE filter string, e.g. 'elements HAS \"Si\"'"
                    },
                    "baseUrls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional provider URLs. Leave empty to use defaults."
                    }
                },
                "required": ["filter"]          # ← 只要求 filter
            }
        )
    ]

# 3.3 Tool 调用
@app.call_tool()
async def call_tool(name: str, args: dict) -> list[TextContent]:
    if name != "query_optimade":
        raise ValueError("Unknown tool")

    # ① 必须有 filter
    filt = args.get("filter")
    if not filt:
        raise ValueError("The 'filter' field is required.")

    # ② 兜底选择 provider URL
    urls = args.get("baseUrls") or DEFAULT_BASE_URLS
    if not urls:
        # 极端情况下 config 也无 → 用硬编码公共镜像
        urls = ["https://optimade.fly.dev"]
        logger.warning("No provider URLs configured; falling back to default mirror.")

    # ③ 执行查询
    client = OptimadeClient(base_urls=urls)
    try:
        results = client.get(filt)
        return [TextContent(type="text",
                            text=json.dumps(results, indent=2, ensure_ascii=False))]
    except Exception as e:
        return [TextContent(type="text", text=f"查询失败: {e}")]

# ── 4 启动 ---------------------------------------------------------------
async def main():
    from mcp.server.stdio import stdio_server
    logger.info("🔌 启动 OPTIMADE MCP 工具服务...")
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())

def sync_main():
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())