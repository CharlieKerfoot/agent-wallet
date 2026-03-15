"""Basic usage: plug any agent into the shared wallet."""
from agent_wallet import AgentWallet, Permissions, WalletConfig, AgentConfig

# --- 1. Configure the wallet and agent permissions ----------------------

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

# --- 2. Each agent gets only the tools it's allowed to use ---------------

earner_tools = wallet.get_tools("earner")
print("Earner tools:", [t["name"] for t in earner_tools])
# => ['wallet_get_balance', 'wallet_get_details', 'wallet_get_deposit_address']

spender_tools = wallet.get_tools("spender")
print("Spender tools:", [t["name"] for t in spender_tools])
# => ['wallet_get_balance', 'wallet_get_details', 'wallet_withdraw', 'wallet_transfer_erc20']

# --- 3. Use the tools directly (or pass them to your LLM agent) ---------

# Check balance
balance = wallet.get_balance()
print("Wallet balance:", balance)

# Get deposit address (earner is allowed)
address = wallet.get_deposit_address("earner")
print("Deposit to:", address)

# Withdraw (spender is allowed, earner would be denied)
# result = wallet.withdraw("spender", amount=0.005, to="0xRecipient...")

# This would raise PermissionError:
# wallet.withdraw("earner", amount=0.005, to="0xRecipient...")

# --- 4. Register a new agent at runtime ---------------------------------

wallet.register_agent("new-bot", Permissions(can_deposit=True, can_withdraw=True))
print("Registered new-bot, tools:", [t["name"] for t in wallet.get_tools("new-bot")])
