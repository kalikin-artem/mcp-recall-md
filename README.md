<h1 align="center">mcp-recall-md</h1>

<p align="center">
  Local semantic search for your markdown notes — via <a href="https://modelcontextprotocol.io/">MCP</a><br>
  Search by meaning, not keywords. 100% offline.
</p>

<p align="center">
  <a href="#-install">Install</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="#-tools">Tools</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="#-auto-indexing">Auto-indexing</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="#-troubleshooting">Troubleshooting</a>
</p>

---

## Install

### Option A: Python users

```bash
pip install mcp-recall-md
```

Add to your MCP config (`.mcp.json` for Claude Code, `claude_desktop_config.json` for Claude Desktop):

```json
{
  "mcpServers": {
    "mcp-recall-md": {
      "command": "mcp-recall-md",
      "args": []
    }
  }
}
```

### Option B: Download exe (no Python needed)

1. Download **mcp-recall-md.exe** from the [latest release](https://github.com/kalikin-artem/mcp-recall-md/releases)
2. Put it in a permanent folder (e.g. `C:\Tools\mcp-recall-md\`)
3. Add to MCP config:

```json
{
  "mcpServers": {
    "mcp-recall-md": {
      "command": "C:/Tools/mcp-recall-md/mcp-recall-md.exe",
      "args": []
    }
  }
}
```

Restart your app. Start asking:

> *"Search my knowledge base for Kubernetes networking"*
>
> *"Find my notes about AWS Bedrock"*

---

## Tools

| Tool | Parameters | What it does |
|------|-----------|-------------|
| `index` | `key`, `content` | Store or update an article |
| `search` | `query`, `limit` | Semantic similarity search |
| `remove` | `key` | Delete an article |

---

## Auto-indexing

To auto-index a folder of `.md` files and watch for changes:

```bash
mcp-recall-md-watcher --vault "C:/Users/you/notes"
```

This indexes all existing files on startup, then watches for new and modified files in real time.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Search returns nothing | Index files first — run the watcher or use the `index` tool |
| First run is slow | Embedding model (~80 MB) downloads once |
| Need to debug | Add `--verbose` flag |

---

## License

MIT
