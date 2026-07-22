# Splitwise MCP Server

A Model Context Protocol (MCP) server for [Splitwise](https://www.splitwise.com/), enabling AI agents to manage expenses, groups, and friends with natural language.

## Features

- **Full API Access**: Manage expenses, groups, friends, and comments.
- **Natural Language Resolution**: Fuzzy matching for names ("John" -> "John Smith") and groups.
- **Dual Auth**: Supports both OAuth 2.0 (recommended) and API Keys.
- **Smart Caching**: Optimizes performance for static data like categories and currencies.

## Installation

```bash
# From PyPI (when published)
pip install splitwise-mcp-server

# From Source
git clone https://github.com/tarunn2799/splitwise-mcp-server
cd splitwise-mcp-server
pip install -e .
```

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

See [TOOLS.md](TOOLS.md) for detailed documentation.

### User Tools
- `get_current_user`: Get authenticated user information
- `get_user`: Get information about a specific user

### Expense Tools
- `create_expense`: Create a new expense with splits
- `get_expenses`: List expenses with optional filters
- `get_expense`: Get detailed expense information
- `update_expense`: Update an existing expense
- `delete_expense`: Delete an expense
- `restore_expense`: Restore a previously deleted expense

### Group Tools
- `get_groups`: List all groups
- `get_group`: Get detailed group information
- `create_group`: Create a new group
- `delete_group`: Delete a group
- `add_user_to_group`: Add a user to a group
- `remove_user_from_group`: Remove a user from a group

### Friend Tools
- `get_friends`: List all friends
- `get_friend`: Get detailed friend information
- `create_friend`: Add a friend by email address
- `delete_friend`: Remove a friendship

### Resolution Tools
- `resolve_friend`: Fuzzy match friend names to user IDs
- `resolve_group`: Fuzzy match group names to group IDs
- `resolve_category`: Fuzzy match category names to category IDs

### Comment Tools
- `create_comment`: Add a comment to an expense
- `get_comments`: Get all comments for an expense
- `delete_comment`: Delete a comment

### Notification Tools
- `get_notifications`: Get recent notifications for the current user

### Utility Tools
- `get_categories`: Get all expense categories
- `get_currencies`: Get all supported currencies

## Development

```bash
# Setup
git clone https://github.com/tarunn2799/splitwise-mcp-server
cd splitwise-mcp-server
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Test
pytest
```

## License

MIT License. See [LICENSE](LICENSE) for details.
