"""Load agent permissions from a YAML config file."""
from agent_wallet import AgentWallet
from agent_wallet.loader import load_config

config = load_config("wallet_config.example.yaml")
wallet = AgentWallet(config)

# Each agent gets a different set of tools based on their YAML config
for agent_id in config.agents:
  tools = wallet.get_tools(agent_id)
  print(f"{agent_id}: {[t['name'] for t in tools]}")
