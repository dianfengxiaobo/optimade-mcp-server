import asyncio
import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from optimade.client import OptimadeClient
from mcp.server import Server
from mcp.types import Tool, TextContent

# ✅ 加载 .env 中的代理配置
load_dotenv()
if os.getenv("HTTP_PROXY"):
    os.environ["HTTP_PROXY"] = os.getenv("HTTP_PROXY")
if os.getenv("HTTPS_PROXY"):
    os.environ["HTTPS_PROXY"] = os.getenv("HTTPS_PROXY")

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("optimade_mcp_server")

# 读取配置文件
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "optimade_config.json"

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"加载配置失败: {e}")
        return {}

CONFIG = load_config()
DEFAULT_BASE_URLS = CONFIG.get("optimadeBaseUrls", [
    "https://optimade.fly.dev",
    "https://optimade.odbx.science"
])
FILTER_PRESETS = CONFIG.get("filterPresets", [
    {"label": "Ag-only", "filter": "elements HAS \"Ag\""}
])
PRESET_MAP = {p["label"]: p["filter"] for p in FILTER_PRESETS if "label" in p and "filter" in p}

# ✅ MCP Server 初始化
app = Server("optimade")

@app.list_tools()
async def list_tools() -> list[Tool]:
    desc = (
        "查询 OPTIMADE 数据库\n"
        "支持 filter / preset / baseUrls\n"
        "示例： {\"preset\": \"Ag-only\"} 或 {\"filter\": \"elements HAS \\\"Si\\\"\"}"
    )
    return [
        Tool(
            name="query_optimade",
            description=desc,
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string"},
                    "preset": {"type": "string"},
                    "baseUrls": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "anyOf": [{"required": ["filter"]}, {"required": ["preset"]}]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "query_optimade":
        raise ValueError("Unknown tool")

    filt = arguments.get("filter") or PRESET_MAP.get(arguments.get("preset", ""))
    if not filt:
        raise ValueError("必须提供 filter 或合法的 preset")

    base_urls = arguments.get("baseUrls") or DEFAULT_BASE_URLS

    try:
        client = OptimadeClient(base_urls=base_urls)
        results = client.get(filt)
        return [TextContent(type="text", text=json.dumps(results, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"查询失败: {e}")]

# ✅ main 函数作为 CLI 调用入口
async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())
