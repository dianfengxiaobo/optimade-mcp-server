import asyncio
import logging
import os
import json
from optimade.client import OptimadeClient
from mcp.server import Server
from mcp.types import Tool, TextContent


os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("optimade_mcp_server")

def get_optimade_config():
    """
    获取 OPTIMADE 基础 URL 列表：
      - 优先读取环境变量 OPTIMADE_BASE_URLS（逗号分隔）
      - 否则使用内置默认列表
    """
    env = os.getenv("OPTIMADE_BASE_URLS")
    if env:
        urls = [u.strip() for u in env.split(",") if u.strip()]
        if urls:
            logger.info(f"使用环境变量 OPTIMADE_BASE_URLS: {urls}")
            return urls
    default_urls = [
        "https://optimade.fly.dev",
        "https://optimade.odbx.science"
    ]
    logger.info(f"使用默认 OPTIMADE_BASE_URLS: {default_urls}")
    return default_urls

# 初始化 MCP Server，名称可自定义，例如 "optimade"
app = Server("optimade")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    列出该 MCP Server 提供的工具。
    这里只有一个工具: "query_optimade"，接收 filter 字符串，
    可选参数 baseUrls 通过环境变量或默认值决定。
    """
    logger.info("list_tools() called")
    # 定义工具的输入 schema: JSON schema 形式
    return [
        Tool(
            name="query_optimade",
            description="使用 OPTIMADE filter 查询结构数据，返回 JSON 字符串",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": 'OPTiMADE filter 表达式，例如: elements HAS "Ag"'
                    },
                    "baseUrls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "可选的 OPTIMADE 基础 URL 列表，优先于环境变量",
                    }
                },
                "required": ["filter"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    调用指定工具。这里只支持 name == "query_optimade"。
    arguments: {"filter": str, "baseUrls": [str,...] (可选)}
    返回 list[TextContent]，通常一个 TextContent 包含 JSON 字符串结果。
    """
    logger.info(f"call_tool() called: name={name}, arguments={arguments}")
    if name != "query_optimade":
        raise ValueError(f"Unknown tool: {name}")

    # 提取 filter
    filt = arguments.get("filter")
    if not isinstance(filt, str) or not filt.strip():
        raise ValueError("参数 'filter' 必须是非空字符串")

    # 提取或获取 baseUrls
    base_urls = arguments.get("baseUrls")
    if base_urls is not None:
        if not isinstance(base_urls, list) or not all(isinstance(u, str) for u in base_urls):
            raise ValueError("参数 'baseUrls' 必须是字符串列表")
        # 如果用户显式传 baseUrls，但列表为空，可报错或 fallback
        if len(base_urls) == 0:
            raise ValueError("参数 'baseUrls' 列表不能为空")
        logger.info(f"使用用户传入的 baseUrls: {base_urls}")
    else:
        base_urls = get_optimade_config()

    # 执行 OPTIMADE 查询
    try:
        logger.info(f"执行 OPTIMADE 查询: filter={filt}, base_urls={base_urls}")
        client = OptimadeClient(base_urls=base_urls)
        results = client.get(filt)
        # 将结果转换为 JSON 字符串
        text = json.dumps(results, indent=2)
        return [TextContent(type="text", text=text)]
    except Exception as e:
        logger.error(f"查询异常: {e}", exc_info=True)
        # 返回错误信息给客户端
        return [TextContent(type="text", text=f"查询失败: {str(e)}")]

async def main():
    """
    启动 MCP stdio 服务器主函数。
    """
    from mcp.server.stdio import stdio_server

    logger.info("Starting OPTIMADE MCP server...")
    # 记录配置信息（可选）
    urls = get_optimade_config()
    logger.info(f"默认 OPTIMADE_BASE_URLS: {urls}")

    # 启动 stdio server，等待 MCP 客户端连接
    async with stdio_server() as (read_stream, write_stream):
        try:
            # create_initialization_options() 可传自定义初始化选项，这里用默认
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except Exception as e:
            logger.error(f"MCP Server 运行出错: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    # 在 Windows 下，确保 asyncio 事件循环策略兼容
    # Python 3.8+ on Windows: 可使用 ProactorEventLoop（默认）
    asyncio.run(main())
