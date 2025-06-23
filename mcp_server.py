import asyncio
import logging
import os
import json
from pathlib import Path
from optimade.client import OptimadeClient
from mcp.server import Server
from mcp.types import Tool, TextContent


os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"
# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("optimade_mcp_server")

# 读取配置文件
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "optimade_config.json"

def load_config():
    if not CONFIG_PATH.exists():
        logger.warning(f"配置文件未找到: {CONFIG_PATH}, 使用内置默认")
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        logger.info(f"加载配置: {CONFIG_PATH}")
        return cfg
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return {}

CONFIG = load_config()
DEFAULT_BASE_URLS = CONFIG.get("optimadeBaseUrls", [
    "https://optimade.fly.dev",
    "https://optimade.odbx.science"
])
FILTER_PRESETS = CONFIG.get("filterPresets", [
    {"label": "Ag-only", "filter": "elements HAS \"Ag\""}
])
PRESET_MAP = {entry["label"]: entry["filter"] for entry in FILTER_PRESETS if "label" in entry and "filter" in entry}

# MCP Server 初始化
app = Server("optimade")

@app.list_tools()
async def list_tools() -> list[Tool]:
    preset_descriptions = "\n".join([f"- {label}: {filt}" for label, filt in PRESET_MAP.items()])
    desc = (
        "使用 OPTIMADE 查询结构数据。\n"
        "参数说明：\n"
        "  preset: 可选，使用预定义 filter 预设之一。\n"
        f"    可选预设:\n{preset_descriptions}\n"
        "  filter: 可选，自定义 filter 字符串，如果同时指定 preset，则优先使用 filter。\n"
        "  baseUrls: 可选，字符串列表，覆盖默认的 OPTIMADE 提供者 URL 列表。\n"
        "示例调用:\n"
        "  {\"preset\": \"Ag-only\"}\n"
        "  {\"filter\": \"elements HAS \\\"Si\\\"\", \"baseUrls\": [\"https://optimade.fly.dev\"]}\n"
    )
    input_schema = {
        "type": "object",
        "properties": {
            "preset": {
                "type": "string",
                "description": "filter 预设名称，可选"
            },
            "filter": {
                "type": "string",
                "description": "自定义 filter，如果同时指定 preset，则优先使用此字段"
            },
            "baseUrls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "可选的 OPTIMADE URL 列表，覆盖默认"
            }
        },
        "anyOf": [
            {"required": ["filter"]},
            {"required": ["preset"]}
        ]
    }
    return [
        Tool(
            name="query_optimade",
            description=desc,
            inputSchema=input_schema
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.info(f"call_tool name={name}, arguments={arguments}")
    if name != "query_optimade":
        raise ValueError(f"Unknown tool: {name}")

    # 处理 filter vs preset
    filt = None
    if "filter" in arguments and isinstance(arguments["filter"], str) and arguments["filter"].strip():
        filt = arguments["filter"].strip()
    elif "preset" in arguments and isinstance(arguments["preset"], str):
        preset_name = arguments["preset"]
        if preset_name not in PRESET_MAP:
            raise ValueError(f"未知 preset: {preset_name}. 可选: {list(PRESET_MAP.keys())}")
        filt = PRESET_MAP[preset_name]
    else:
        raise ValueError("必须提供 'filter' 或 'preset' 参数")

    # 处理 baseUrls 覆盖
    if "baseUrls" in arguments:
        bu = arguments["baseUrls"]
        if not isinstance(bu, list) or not all(isinstance(u, str) for u in bu):
            raise ValueError("参数 'baseUrls' 必须是字符串列表")
        if len(bu) == 0:
            raise ValueError("参数 'baseUrls' 列表不能为空")
        base_urls = bu
        logger.info(f"使用用户传入 baseUrls: {base_urls}")
    else:
        base_urls = DEFAULT_BASE_URLS
        logger.info(f"使用默认 baseUrls: {base_urls}")

    # 执行查询
    try:
        logger.info(f"执行 OPTIMADE 查询: filter={filt}")
        client = OptimadeClient(base_urls=base_urls)
        results = client.get(filt)
        text = json.dumps(results, indent=2)
        return [TextContent(type="text", text=text)]
    except Exception as e:
        logger.error(f"查询异常: {e}", exc_info=True)
        return [TextContent(type="text", text=f"查询失败: {str(e)}")]

async def main():
    from mcp.server.stdio import stdio_server
    logger.info("启动 OPTIMADE MCP 服务器...")
    urls = DEFAULT_BASE_URLS
    logger.info(f"默认 OPTIMADE_BASE_URLS: {urls}")
    async with stdio_server() as (r, w):
        try:
            await app.run(r, w, app.create_initialization_options())
        except Exception as e:
            logger.error(f"MCP Server 运行出错: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    asyncio.run(main())
