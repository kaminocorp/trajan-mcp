# trajan-mcp

MCP server for [Trajan](https://www.trajancloud.com) — connect AI agents to your developer workspace.

Gives AI agents (Claude Desktop, Claude Code, Cursor, Windsurf, custom agents) read/write access to your Trajan product's documentation, work items, repositories, and project context via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Quick start

### 1. Create an API key

In Trajan, go to **Product Settings > API Keys** and create a key with the scopes you need:

| Scope | Grants |
|-------|--------|
| `mcp:read` | Read product metadata, documents, work items, repositories |
| `mcp:write` | Create and update documents and work items |
| `mcp:admin` | Trigger doc generation, sync documents to GitHub |

### 2. Configure your MCP client

#### Claude Code

```bash
claude mcp add trajan trajan-mcp -e TRAJAN_API_KEY=trj_pk_your_key_here
```

Or add to `.claude/settings.json` / `.mcp.json`:

```json
{
  "mcpServers": {
    "trajan": {
      "command": "trajan-mcp",
      "env": {
        "TRAJAN_API_KEY": "trj_pk_your_key_here"
      }
    }
  }
}
```

#### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "trajan": {
      "command": "trajan-mcp",
      "env": {
        "TRAJAN_API_KEY": "trj_pk_your_key_here"
      }
    }
  }
}
```

#### Cursor / Windsurf

Add to your MCP settings (`.cursor/mcp.json` or equivalent):

```json
{
  "mcpServers": {
    "trajan": {
      "command": "trajan-mcp",
      "env": {
        "TRAJAN_API_KEY": "trj_pk_your_key_here"
      }
    }
  }
}
```

### 3. Install

The `trajan-mcp` command must be available on your `PATH`. Choose one:

```bash
# pip (global or virtualenv)
pip install trajan-mcp

# uv
uv pip install trajan-mcp

# Zero-install via uvx (runs directly from PyPI, no install needed)
# Use "uvx trajan-mcp" as the command in your MCP config instead of "trajan-mcp"
```

If using `uvx`, change the `"command"` in your MCP config to `"uvx"` and add `"args": ["trajan-mcp"]`:

```json
{
  "mcpServers": {
    "trajan": {
      "command": "uvx",
      "args": ["trajan-mcp"],
      "env": {
        "TRAJAN_API_KEY": "trj_pk_your_key_here"
      }
    }
  }
}
```

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRAJAN_API_KEY` | Yes | — | Product-scoped API key (`trj_pk_...`) |
| `TRAJAN_API_URL` | No | `https://api.trajancloud.com` | Trajan API base URL |

## Available tools

### Read tools (`mcp:read`)

| Tool | Description |
|------|-------------|
| `get_product_overview` | Product metadata, repositories, doc/work-item counts |
| `list_documents` | List documents (titles only, filterable by type) |
| `get_document` | Full document with markdown content |
| `search_documents` | Full-text search across titles and content |
| `list_work_items` | List tasks/features/bugs (filterable by status, type) |
| `get_work_item` | Full work item detail |
| `list_repositories` | Repositories linked to the product |
| `get_repository_tree` | File tree of a linked GitHub repository |
| `get_repository_file` | Read a single file from a linked repository |

### Write tools (`mcp:write`)

| Tool | Description |
|------|-------------|
| `create_document` | Create a new document (blueprint, plan, note, etc.) |
| `update_document` | Update an existing document's title, content, or type |
| `create_work_item` | Create a task, feature request, or bug report |
| `update_work_item` | Update a work item's status, priority, tags, etc. |

### Admin tools (`mcp:admin`)

| Tool | Description |
|------|-------------|
| `generate_docs` | Trigger AI documentation generation (full or additive) |
| `get_docs_generation_status` | Poll generation progress |
| `get_codebase_context` | Get AI-generated codebase analysis |
| `sync_docs_to_repo` | Push documents to the linked GitHub repository |

## Browsable resources

MCP resources are data URIs that agents can discover and read directly (e.g. via Claude Desktop's sidebar).

| Resource URI | Description |
|---|---|
| `product://overview` | Product metadata and entity counts |
| `docs://list` | All documents (titles only) |
| `docs://{document_id}` | Full document with content |
| `workitems://list` | All work items |
| `workitems://{item_id}` | Full work item detail |
| `repos://list` | Linked repositories |
| `repo://{repository_id}/tree` | Repository file tree |
| `codebase://context` | AI-generated codebase analysis |

## Example agent workflow

```
1. get_product_overview()          → Understand the product
2. get_codebase_context()          → Check existing analysis
3. list_documents()                → See current doc inventory
4. generate_docs(mode="additive")  → Fill gaps in docs
5. get_docs_generation_status()    → Poll until complete
6. list_documents()                → See new docs
7. sync_docs_to_repo()             → Push to GitHub
```

## Development

```bash
cd trajan-mcp
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Run directly
TRAJAN_API_KEY=trj_pk_... trajan-mcp
```

## License

MIT
