# OPTIMADE MCP SERVER
A Model Context Protocol (MCP) tool for querying Optimade-compatible material databases, fully configurable custom filter presets and provider endpoints.
# 🎯 Overview
This tool enables structured data queries across multiple OPTIMADE databases (e.g., Materials Project, Materials Cloud, COD), via MCP protocol. Key capabilities include:

1.Custom or preset OPTIMADE filter queries

2.Configurable list of OPTIMADE providers via config/optimade_config.json

3.Proxy support via .env file

4.Easily deployable via uvx, cline
# ⚙️ Installation & Usage
## ✅ Recommended via uv
1.Install the tool:
~~~~~~
uv pip install optimade-mcp-server
~~~~~~
2.In cline or any MCP-compatible launcher, configure the tool as follows:
~~~~~~
{
  "mcpServers": {
    "optimade": {
      "command": "uv",
      "args": ["--directory", "optimade-mcp-server", "run", "optimade"]
    }
  }
}
~~~~~~
# 🌐 Proxy Support (Optional)
If you need to use a VPN or proxy, create a .env file in the project root:
~~~~~~
HTTP_PROXY=http://127.0.0.1:<your-port>
HTTPS_PROXY=http://127.0.0.1:<your-port>
~~~~~~
If you don't need a proxy, you can comment out or remove the proxy setup in the source code.
# 🪪 License
This project is licensed under the MIT License. See LICENSE for details.