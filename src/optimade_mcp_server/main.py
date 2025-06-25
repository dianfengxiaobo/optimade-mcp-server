import asyncio
import logging
import os
import json
from dotenv import load_dotenv
from pathlib import Path
import importlib.resources as pkg_resources
from optimade.client import OptimadeClient
from mcp.server import Server
from mcp.types import Tool, TextContent

# 加载 .env 文件中的代理设置
load_dotenv()
os.environ["HTTP_PROXY"] = os.getenv("HTTP_PROXY", "")
os.environ["HTTPS_PROXY"] = os.getenv("HTTPS_PROXY", "")

logger = logging.getLogger("optimade_mcp_server")
logging.basicConfig(level=logging.INFO)

# 自动兼容配置路径：开发路径 & 打包路径
def load_config() -> dict:
    try:
        with pkg_resources.files("optimade_mcp_server.config").joinpath("optimade_config.json").open("r", encoding="utf-8") as f:
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

CONFIG = load_config()
DEFAULT_BASE_URLS = CONFIG.get("optimadeBaseUrls", [])
FILTER_PRESETS = CONFIG.get("filterPresets", [])
PRESET_MAP = {entry["label"]: entry["filter"] for entry in FILTER_PRESETS if "label" in entry and "filter" in entry}

app = Server("optimade")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_optimade",
            description="Query the OPTIMADE databases with either a filter or a preset.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "A custom OPTIMADE filter string (e.g., 'elements HAS \"Si\"')"
                    },
                    "preset": {
                        "type": "string",
                        "description": "The name of a predefined filter preset (e.g., 'Ag-only')"
                    },
                    "baseUrls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of OPTIMADE provider base URLs to query"
                    }
                },
                "anyOf": [
                    {"required": ["filter"]},
                    {"required": ["preset"]}
                ]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, args: dict) -> list[TextContent]:
    if name != "query_optimade":
        raise ValueError("Unknown tool")

    filt = args.get("filter")
    if not filt:
        preset = args.get("preset")
        filt = PRESET_MAP.get(preset)
        if not filt:
            raise ValueError("Must specify 'filter' or valid 'preset'")

    urls = args.get("baseUrls") or DEFAULT_BASE_URLS
    client = OptimadeClient(base_urls=urls)
    try:
        results = client.get(filt)
        return [TextContent(type="text", text=json.dumps(results, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"查询失败: {e}")]

async def main():
    from mcp.server.stdio import stdio_server
    logger.info("🔌 启动 OPTIMADE MCP 工具服务...")
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())

def sync_main():
    """同步入口点，用于 console_scripts"""
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())