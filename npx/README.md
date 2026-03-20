# trajan-mcp

npm wrapper for the [trajan-mcp](https://pypi.org/project/trajan-mcp/) Python MCP server.

This package allows Node.js users to run the Trajan MCP server via `npx` without manually installing the Python package:

```bash
npx trajan-mcp
```

The wrapper delegates to the Python package using `uvx`, `trajan-mcp` (pip), or `pipx` — whichever is available on your system.

For full documentation, see the [Python package README](https://pypi.org/project/trajan-mcp/) or the [Trajan website](https://www.trajancloud.com).

## Usage in MCP config

```json
{
  "mcpServers": {
    "trajan": {
      "command": "npx",
      "args": ["trajan-mcp"],
      "env": {
        "TRAJAN_API_KEY": "trj_pk_your_key_here"
      }
    }
  }
}
```

## Prerequisites

One of the following must be installed:

- [uv](https://docs.astral.sh/uv/) (recommended — zero-install via `uvx`)
- Python with `pip install trajan-mcp`
- [pipx](https://pipx.pypa.io/)

## License

MIT
