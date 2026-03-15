"""Shows how to wire agent-wallet tools into any LLM agent framework.

This is framework-agnostic — the tool dicts work with OpenAI function calling,
Anthropic tool_use, LangChain, or any custom agent loop.
"""
from agent_wallet import AgentWallet, AgentConfig, Permissions, WalletConfig


def build_wallet() -> AgentWallet:
  config = WalletConfig(
    network_id="base-sepolia",
    agents={
      "my-agent": AgentConfig(
        agent_id="my-agent",
        permissions=Permissions(can_deposit=True, can_withdraw=True, max_withdraw_per_tx=0.05),
      ),
    },
  )
  return AgentWallet(config)


# ---- OpenAI function-calling format ------------------------------------

def to_openai_tools(wallet: AgentWallet, agent_id: str) -> list[dict]:
  """Convert wallet tools to OpenAI function-calling format."""
  return [
    {
      "type": "function",
      "function": {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["parameters"],
      },
    }
    for tool in wallet.get_tools(agent_id)
  ]


# ---- Anthropic tool_use format -----------------------------------------

def to_anthropic_tools(wallet: AgentWallet, agent_id: str) -> list[dict]:
  """Convert wallet tools to Anthropic tool_use format."""
  return [
    {
      "name": tool["name"],
      "description": tool["description"],
      "input_schema": tool["parameters"],
    }
    for tool in wallet.get_tools(agent_id)
  ]


# ---- Generic agent loop ------------------------------------------------

def handle_tool_call(wallet: AgentWallet, agent_id: str, tool_name: str, args: dict) -> str:
  """Dispatch a tool call from any LLM agent framework."""
  tools = {t["name"]: t for t in wallet.get_tools(agent_id)}
  if tool_name not in tools:
    return f"Error: tool '{tool_name}' not available for agent '{agent_id}'"
  return tools[tool_name]["invoke"](args)


if __name__ == "__main__":
  wallet = build_wallet()

  print("OpenAI format:", to_openai_tools(wallet, "my-agent"))
  print()
  print("Anthropic format:", to_anthropic_tools(wallet, "my-agent"))
  print()

  # Simulate an agent calling a tool
  result = handle_tool_call(wallet, "my-agent", "wallet_get_balance", {"asset": "eth"})
  print("Balance:", result)
