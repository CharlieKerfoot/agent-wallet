# Agent Wallet

A model/agent-agnostic shared wallet with per-agent permissions, powered by [Coinbase AgentKit](https://github.com/coinbase/agentkit).

Give every AI agent its own permission scope on a single onchain wallet — deposit-only bots, spend-capped traders, read-only monitors, or full-access admins — without writing any blockchain code.

## Features

- **Per-agent permissions** — fine-grained control over deposit, withdraw, per-tx limits, and asset whitelists
- **Framework-agnostic tools** — `get_tools()` returns JSON-schema tool dicts ready for OpenAI, Anthropic, LangChain, or any LLM framework
- **Runtime registration** — add or update agents on the fly
- **YAML or code config** — configure via `wallet_config.yaml` or directly in Python
- **Built on AgentKit** — leverages Coinbase's production-grade wallet infrastructure

## Quickstart

### Install

```bash
uv add agent-wallet
```

### Set up credentials

Get your CDP API keys from [portal.cdp.coinbase.com](https://portal.cdp.coinbase.com) and set them as environment variables:

```bash
cp .env.example .env
# edit .env with your keys
```

```
CDP_API_KEY_ID=your-key-id
CDP_API_KEY_SECRET=your-key-secret
CDP_WALLET_SECRET=your-wallet-secret
```

### Basic usage

```python
from agent_wallet import AgentWallet, Permissions, WalletConfig, AgentConfig

config = WalletConfig(
  network_id="base-sepolia",
  agents={
    "earner": AgentConfig(
      agent_id="earner",
      permissions=Permissions(can_deposit=True, can_withdraw=False),
    ),
    "spender": AgentConfig(
      agent_id="spender",
      permissions=Permissions(
        can_withdraw=True,
        max_withdraw_per_tx=0.01,
        allowed_assets=["ETH"],
      ),
    ),
  },
)

wallet = AgentWallet(config)

# Each agent only gets the tools it's allowed to use
earner_tools = wallet.get_tools("earner")
# => ['wallet_get_balance', 'wallet_get_details', 'wallet_get_deposit_address']

spender_tools = wallet.get_tools("spender")
# => ['wallet_get_balance', 'wallet_get_details', 'wallet_withdraw', 'wallet_transfer_erc20']

# Register new agents at runtime
wallet.register_agent("monitor", Permissions(can_deposit=False, can_withdraw=False))
```

### YAML config

```yaml
# wallet_config.yaml
network_id: base-sepolia

agents:
  monitor-bot:
    permissions:
      can_deposit: false
      can_withdraw: false

  earner-bot:
    permissions:
      can_deposit: true
      can_withdraw: false
      allowed_assets: [ETH, USDC]

  spender-bot:
    permissions:
      can_deposit: false
      can_withdraw: true
      max_withdraw_per_tx: 0.01
      allowed_assets: [ETH]

  admin-bot:
    permissions:
      can_deposit: true
      can_withdraw: true
```

```python
from agent_wallet import AgentWallet
from agent_wallet.loader import load_config

config = load_config("wallet_config.yaml")
wallet = AgentWallet(config)
```

## Permissions

Each agent is assigned a `Permissions` object with the following fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `can_deposit` | `bool` | `False` | Allow receiving funds |
| `can_withdraw` | `bool` | `False` | Allow sending funds |
| `max_withdraw_per_tx` | `float \| None` | `None` | Per-transaction withdrawal cap |
| `allowed_assets` | `list[str] \| None` | `None` | Asset whitelist (e.g. `["ETH", "USDC"]`) |

Calling a gated operation without permission raises `PermissionError`.

## API

| Method | Description |
|---|---|
| `AgentWallet(config)` | Initialize with a `WalletConfig` |
| `get_tools(agent_id)` | Get LLM-ready tool dicts scoped to the agent's permissions |
| `register_agent(agent_id, permissions)` | Register a new agent at runtime |
| `get_wallet_details()` | Return wallet address and network info |
| `get_balance(asset="eth")` | Get wallet balance |
| `get_deposit_address(agent_id, asset="ETH")` | Get deposit address (requires `can_deposit`) |
| `withdraw(agent_id, amount, to, asset="ETH")` | Transfer native token (requires `can_withdraw`) |
| `transfer_erc20(agent_id, amount, to, contract_address)` | Transfer ERC-20 token (requires `can_withdraw`) |

## MCP Server

Agent Wallet ships with a [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes wallet operations as MCP tools, letting any MCP-compatible client or agent interact with the wallet directly.

### Running the server

```bash
uv run mcp_server.py
```

The server loads its configuration from `wallet_config.yaml` in the project root.

### Available tools

| Tool | Description |
|---|---|
| `wallet_get_balance` | Get the wallet balance for a given asset |
| `wallet_get_details` | Get wallet address and network info |
| `wallet_get_deposit_address` | Get the deposit address (requires agent with `can_deposit`) |
| `wallet_withdraw` | Withdraw native token (requires agent with `can_withdraw`) |
| `wallet_transfer_erc20` | Transfer an ERC-20 token (requires agent with `can_withdraw`) |

### Client configuration

Add to your MCP client config (e.g. Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agent-wallet": {
      "command": "uv",
      "args": ["run", "mcp_server.py"],
      "cwd": "/path/to/agent-wallet"
    }
  }
}
```

## Requirements

- Python >= 3.12
- [Coinbase Developer Platform](https://portal.cdp.coinbase.com) API keys
