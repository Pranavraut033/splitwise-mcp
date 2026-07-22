# Splitwise MCP Server

A Model Context Protocol (MCP) server that connects [Splitwise](https://www.splitwise.com/) to Claude Desktop, Kiro, and other MCP clients, so an AI agent can manage your expenses, groups, and friends in plain language.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)

## Features

- **Full API Access**: Manage expenses, groups, friends, and comments.
- **Natural Language Resolution**: Fuzzy matching for names ("John" -> "John Smith") and groups.
- **Dual Auth**: Supports both OAuth 2.0 (recommended) and API Keys.
- **Smart Caching**: Optimizes performance for static data like categories and currencies.

## Prerequisites

- Python 3.10+
- A Splitwise account and, for OAuth, a [registered Splitwise app](https://secure.splitwise.com/apps)

## Installation

```bash
git clone https://github.com/tarunn2799/splitwise-mcp
cd splitwise-mcp
pip install -e .
```

Not yet published to PyPI — install from source as above.

## Configuration

See [SETUP.md](SETUP.md) for detailed authentication and configuration instructions.

### Quick Config
Run the included setup script:
```
python -m splitwise_mcp_server.oauth_setup
```

Use the keys provided there, and add all three to your `mcp.json`:

```json
{
  "mcpServers": {
    "splitwise": {
      "command": "python",
      "args": ["-m", "splitwise_mcp_server"],
      "env": {
        "SPLITWISE_OAUTH_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

> **Get your Auth Keys**
> You can get your Consumer Key and Secret by registering an app at [https://secure.splitwise.com/apps](https://secure.splitwise.com/apps).

> **IMPORTANT:** Using a Virtual Environment?
> If you installed the package in a `venv` or Conda environment, you must use the **absolute path** to the python executable in your config.
>
> ```json
> "command": "/absolute/path/to/venv/bin/python"
> ```
> See [SETUP.md](SETUP.md#using-a-virtual-environment-venvconda) for details.

## Usage

The server enables natural language interactions with your Splitwise data.

**Examples:**
- "What's my current balance?"
- "Split a $50 dinner with Sarah."
- "Use the receipt I uploaded to split the dinner between Manav and me."
- "Show me expenses from last month."
- "Create a group called 'Ski Trip' with Mike."

## Tools

27 tools across 8 categories. See [TOOLS.md](TOOLS.md) for full parameter/response documentation of each.

| Category | Tools |
|---|---|
| User | `get_current_user`, `get_user` |
| Expense | `create_expense`, `get_expenses`, `get_expense`, `update_expense`, `delete_expense`, `restore_expense` |
| Group | `get_groups`, `get_group`, `create_group`, `delete_group`, `add_user_to_group`, `remove_user_from_group` |
| Friend | `get_friends`, `get_friend`, `create_friend`, `delete_friend` |
| Resolution (fuzzy matching) | `resolve_friend`, `resolve_group`, `resolve_category` |
| Comment | `create_comment`, `get_comments`, `delete_comment` |
| Notification | `get_notifications` |
| Utility | `get_categories`, `get_currencies` |

## Development

```bash
# Setup
git clone https://github.com/tarunn2799/splitwise-mcp
cd splitwise-mcp
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Test
pytest
```

## Deployment

By default the server runs over stdio, for local MCP clients like Claude Desktop or Kiro. It can also run over HTTP for remote hosting (e.g. Prefect Horizon):

```bash
# Set FASTMCP_TRANSPORT=http, or pass --http
FASTMCP_TRANSPORT=http python -m splitwise_mcp_server
# Optional: FASTMCP_HOST (default 0.0.0.0), FASTMCP_PORT (default 8000)
```

`app.py` exposes a module-level `mcp` instance (`app.py:mcp`) as the entrypoint for platforms that expect one, configured via `fastmcp.json`.

## Contributing

Issues and pull requests are welcome against this fork.

## License

MIT License. See [LICENSE](LICENSE) for details.
