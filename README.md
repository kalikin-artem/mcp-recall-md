<h1 align="center">mcp-recall-md</h1>

<p align="center">
  Local semantic search for your markdown notes — via <a href="https://modelcontextprotocol.io/">MCP</a><br>
  Search by meaning, not keywords. 100% offline.
</p>

<p align="center">
  <a href="#install">Install</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="#tools">Tools</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="#auto-indexing">Auto-indexing</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="#recallignore">.recallignore</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="#troubleshooting">Troubleshooting</a>
</p>

---

## Install

### Option A: uvx (recommended, no install needed)

```json
{
  "mcpServers": {
    "mcp-recall-md": {
      "command": "uvx",
      "args": ["mcp-recall-md", "--vaults", "C:/Users/you/notes"]
    }
  }
}
```

### Option B: pip

```bash
pip install mcp-recall-md
```

```json
{
  "mcpServers": {
    "mcp-recall-md": {
      "command": "mcp-recall-md",
      "args": ["--vaults", "C:/Users/you/notes"]
    }
  }
}
```

### Option C: Download exe (no Python needed)

1. Download **mcp-recall-md.exe** from the [latest release](https://github.com/kalikin-artem/mcp-recall-md/releases)
2. Put it in a permanent folder (e.g. `C:\Tools\mcp-recall-md\`)
3. Add to MCP config:

```json
{
  "mcpServers": {
    "mcp-recall-md": {
      "command": "C:/Tools/mcp-recall-md/mcp-recall-md.exe",
      "args": ["--vaults", "C:/Users/you/notes"]
    }
  }
}
```

Multiple vaults? Just list them:

```json
"args": ["--vaults", "C:/notes/work", "C:/notes/personal", "C:/docs"]
```

Add the config to `.mcp.json` (Claude Code) or `claude_desktop_config.json` (Claude Desktop), then restart.

---

## Tools

| Tool | Parameters | What it does |
|------|-----------|-------------|
| `index` | `key`, `content` | Store or update an article |
| `search` | `query`, `limit` | Semantic similarity search |
| `remove` | `key` | Delete an article |

---

## Auto-indexing

When `--vaults` is provided, the server automatically:

1. Indexes all existing `.md` files on startup (skips unchanged files on restart)
2. Watches for new, modified, and deleted files in real time

No separate watcher process needed — it's all one command.

Without `--vaults`, the server runs in manual mode (use the `index` tool to add content).

---

## .recallignore

Drop a `.recallignore` file in any vault root to control which files get indexed. Uses standard `.gitignore` syntax.

**Exclude specific folders:**

```gitignore
.obsidian/
_templates/
drafts/
```

**Include only specific folders** (exclude everything else):

```gitignore
*
!notes/
!docs/
```

Each vault gets its own `.recallignore` — they're independent.

---

## CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--vaults` | none | Paths to markdown folders to index and watch |
| `--db-path` | `~/.mcp-recall-md/db` | ChromaDB storage location |
| `--verbose` | off | Enable debug logging to stderr |

---

## Logs

Logs are always written to `~/.mcp-recall-md/server.log` (5 MB max, 3 rotated backups).

Add `--verbose` for additional debug output to stderr.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Search returns nothing | Make sure `--vaults` is set, or use the `index` tool manually |
| First run is slow | Embedding model (~80 MB) downloads once |
| Need to debug | Add `--verbose` flag, check `~/.mcp-recall-md/server.log` |

---

## License

MIT
