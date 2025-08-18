# OPTIMADE MCP SERVER
A Model Context Protocol (MCP) tool for querying Optimade-compatible material databases, fully configurable custom filter presets and provider endpoints.

---

# 🎯 Overview
This tool enables structured data queries across multiple OPTIMADE databases (e.g., Materials Project, Materials Cloud, COD), via MCP protocol. Key capabilities include:

1.Custom or preset OPTIMADE filter queries

2.Configurable list of OPTIMADE providers via config/optimade_config.json

3.Proxy support via .env file

4.Easily deployable via uvx, cline

Note: The query requires two parameters. One is the optimade query filter, and the other is the database to be queried.

---

## ✨ Features

- **MCP Resources** the model can read on demand:
  - `optimade://docs/filters` – Filter grammar & examples (Markdown)
  - `optimade://spec/queryable_props` – **Whitelist** of fields marked *“Query: MUST be a queryable property …”* (JSON)
  - `optimade://docs/providers` – Default provider URLs (JSON, generated from config)
  - `optimade://docs/filter_presets` – Named filter snippets (JSON)
  - `optimade://prompts/ask_for_provider` – System prompt to guide URL selection & linting (Text)
  - `optimade://results/<uuid>` – **Dynamic**: full JSON of past queries
- **Tools**
  - `lint_filter(filter)` → `"ok"` / `"warn: …"` / `"syntax error: …"`  
    (Warn = not in whitelist but allowed; Syntax error = blocked)
  - `query_optimade(filter, baseUrls?)` → preview (first 5) + link to full JSON resource
  - `list_providers()` → Discover global public OPTIMADE endpoints
- **Provider fallback**  
  1) user-provided `baseUrls` → 2) config defaults → 3) fallback single mirror (`https://optimade.fly.dev`)
- **Proxy-ready** via `.env` (`HTTP_PROXY`, `HTTPS_PROXY`).

---

## 🧩 What the LLM can read (Resources)

| URI | Type | Purpose |
|-----|------|--------|
| `optimade://docs/filters` | `text/markdown` | Full grammar & examples |
| `optimade://spec/queryable_props` | `application/json` | **Whitelist**: fields marked “MUST be queryable” |
| `optimade://docs/providers` | `application/json` | Default provider URLs from config |
| `optimade://docs/filter_presets` | `application/json` | Named filter snippets for inspiration |
| `optimade://prompts/ask_for_provider` | `text/plain` | System prompt to guide URL choice & linting |
| `optimade://results/<uuid>` | `application/json` | **Dynamic**: full JSON from previous queries |

> **Important**: Resources are **not auto-injected**. Your MCP client must call `resources/read` (or you configure startup/workflow to read them).

---

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
    "optimade_mcp_server": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uvx",
      "args": [
        "optimade-mcp-server"
      ]
    }
  }
}
~~~~~~

---

# 🌐 Proxy Support (Optional)
If you need to use a VPN or proxy, create a .env file in the project root:
~~~~~~
HTTP_PROXY=http://127.0.0.1:<your-port>
HTTPS_PROXY=http://127.0.0.1:<your-port>
~~~~~~
If you don't need a proxy, you can comment out or remove the proxy setup in the source code.

---

# 🪪 License
This project is licensed under the MIT License. See LICENSE for details.

---

## 🙋 FAQ

**Q:** Are resources auto‑injected into the model’s context?  
**A:** No. The client must call `resources/read` (or configure a startup/workflow step). The server **does** apply provider fallback automatically if `baseUrls` are omitted.

**Q:** Can I use non‑whitelisted fields (like `band_gap`)?  
**A:** Yes. `lint_filter` returns `warn: band_gap`. The model should show a warning and ask you to confirm before querying.

**Q:** How do I export the full result?  
**A:** The server always saves a full JSON under `optimade://results/<uuid>`. 