from mcp.server.fastmcp import FastMCP
from agent_wallet import AgentWallet, Permissions, WalletConfig, AgentConfig
from agent_wallet.loader import load_config

wallet = AgentWallet(load_config("wallet_config.yaml"))
mcp = FastMCP("agent-wallet")


@mcp.tool()
def wallet_get_balance(asset: str = "eth") -> str:
  """Get the wallet balance for a given asset."""
  return wallet.get_balance(asset)


@mcp.tool()
def wallet_get_details() -> str:
  """Get wallet address and network info."""
  return wallet.get_wallet_details()


@mcp.tool()
def wallet_get_deposit_address(agent_id: str, asset: str = "ETH") -> str:
  """Get the deposit address for this wallet."""
  return wallet.get_deposit_address(agent_id, asset)


@mcp.tool()
def wallet_withdraw(agent_id: str, amount: float, to: str, asset: str = "ETH") -> str:
  """Withdraw native token from the wallet."""
  return wallet.withdraw(agent_id, amount, to, asset)


@mcp.tool()
def wallet_transfer_erc20(agent_id: str, amount: float, to: str, contract_address: str) -> str:
  """Transfer an ERC-20 token from the wallet."""
  return wallet.transfer_erc20(agent_id, amount, to, contract_address)


if __name__ == "__main__":
  mcp.run()
