from __future__ import annotations

import os
from typing import Any

from coinbase_agentkit import (
  AgentKit,
  AgentKitConfig,
  CdpEvmWalletProvider,
  CdpEvmWalletProviderConfig,
  erc20_action_provider,
  wallet_action_provider,
)

from agent_wallet.config import AgentConfig, WalletConfig
from agent_wallet.permissions import Permissions


class AgentWallet:
  """A shared wallet that any agent can plug into, gated by per-agent permissions.

  Usage:
      config = WalletConfig(network_id="base-sepolia", agents={
          "scraper-bot": AgentConfig(
              agent_id="scraper-bot",
              permissions=Permissions(can_deposit=True),
          ),
          "trader-bot": AgentConfig(
              agent_id="trader-bot",
              permissions=Permissions(can_withdraw=True, max_withdraw_per_tx=0.01),
          ),
      })
      wallet = AgentWallet(config)

      # Agent deposits
      address = wallet.get_deposit_address("scraper-bot")

      # Agent withdraws
      result = wallet.withdraw("trader-bot", amount=0.005, to="0xRecipient...")
  """

  def __init__(self, config: WalletConfig | None = None) -> None:
    self._config = config or WalletConfig()
    self._wallet_provider = self._create_wallet_provider()
    self._agentkit = AgentKit(
      AgentKitConfig(
        wallet_provider=self._wallet_provider,
        action_providers=[
          wallet_action_provider(),
          erc20_action_provider(),
        ],
      )
    )

  # ------------------------------------------------------------------
  # Internal
  # ------------------------------------------------------------------

  def _create_wallet_provider(self) -> CdpEvmWalletProvider:
    cfg = self._config
    kwargs: dict[str, Any] = {
      "api_key_id": cfg.cdp_api_key_id or os.environ["CDP_API_KEY_ID"],
      "api_key_secret": cfg.cdp_api_key_secret or os.environ["CDP_API_KEY_SECRET"],
      "wallet_secret": cfg.cdp_wallet_secret or os.environ["CDP_WALLET_SECRET"],
      "network_id": cfg.network_id,
    }
    if cfg.wallet_address:
      kwargs["address"] = cfg.wallet_address
    if cfg.idempotency_key:
      kwargs["idempotency_key"] = cfg.idempotency_key
    return CdpEvmWalletProvider(CdpEvmWalletProviderConfig(**kwargs))

  def _get_permissions(self, agent_id: str) -> Permissions:
    agent_cfg = self._config.agents.get(agent_id)
    if agent_cfg is None:
      raise KeyError(
        f"Agent '{agent_id}' is not registered. "
        f"Add it to WalletConfig.agents first."
      )
    return agent_cfg.permissions

  def _run_action(self, action_name: str, args: dict[str, Any]) -> str:
    """Run a named AgentKit action and return the string result."""
    for provider in self._agentkit.config.action_providers:
      for action in provider.get_actions(self._wallet_provider):
        if action.name == action_name:
          return action.invoke(args)
    raise ValueError(f"Action '{action_name}' not found in configured providers.")

  # ------------------------------------------------------------------
  # Public API
  # ------------------------------------------------------------------

  def register_agent(self, agent_id: str, permissions: Permissions | None = None) -> None:
    """Register a new agent at runtime."""
    if agent_id in self._config.agents:
      raise ValueError(f"Agent '{agent_id}' is already registered.")
    self._config.agents[agent_id] = AgentConfig(
      agent_id=agent_id,
      permissions=permissions or Permissions(),
    )

  def get_wallet_details(self) -> str:
    """Return wallet address and network info."""
    return self._run_action("get_wallet_details", {})

  def get_balance(self, asset: str = "eth") -> str:
    """Get the wallet's balance for a given asset."""
    return self._run_action("get_balance", {"asset_id": asset})

  def get_deposit_address(self, agent_id: str, asset: str = "ETH") -> str:
    """Return the wallet address an agent can send funds to.

    Checks that the agent has deposit permission first.
    """
    perms = self._get_permissions(agent_id)
    perms.check_deposit(asset)
    return self._wallet_provider.get_address()

  def withdraw(
    self,
    agent_id: str,
    amount: float,
    to: str,
    asset: str = "ETH",
  ) -> str:
    """Transfer native token out of the wallet on behalf of an agent.

    Checks withdrawal permissions and per-tx limits.
    """
    perms = self._get_permissions(agent_id)
    perms.check_withdraw(amount, asset)
    return self._run_action(
      "native_transfer",
      {"to": to, "value": str(amount)},
    )

  def transfer_erc20(
    self,
    agent_id: str,
    amount: float,
    to: str,
    contract_address: str,
    asset: str = "ERC20",
  ) -> str:
    """Transfer an ERC-20 token out of the wallet on behalf of an agent."""
    perms = self._get_permissions(agent_id)
    perms.check_withdraw(amount, asset)
    return self._run_action(
      "transfer_erc20",
      {
        "to": to,
        "value": str(amount),
        "contract_address": contract_address,
      },
    )

  def get_tools(self, agent_id: str) -> list[dict[str, Any]]:
    """Return a list of tool dicts an LLM agent can call, pre-filtered by permissions.

    Each tool dict has: name, description, parameters (JSON Schema), invoke (callable).
    This makes it trivial to plug into any agent framework.
    """
    perms = self._get_permissions(agent_id)
    tools: list[dict[str, Any]] = []

    # Always allow read-only operations
    tools.append({
      "name": "wallet_get_balance",
      "description": "Get the wallet balance for a given asset.",
      "parameters": {
        "type": "object",
        "properties": {
          "asset": {"type": "string", "default": "eth"},
        },
      },
      "invoke": lambda args: self.get_balance(args.get("asset", "eth")),
    })

    tools.append({
      "name": "wallet_get_details",
      "description": "Get wallet address and network info.",
      "parameters": {"type": "object", "properties": {}},
      "invoke": lambda args: self.get_wallet_details(),
    })

    if perms.can_deposit:
      tools.append({
        "name": "wallet_get_deposit_address",
        "description": "Get the deposit address for this wallet.",
        "parameters": {
          "type": "object",
          "properties": {
            "asset": {"type": "string", "default": "ETH"},
          },
        },
        "invoke": lambda args: self.get_deposit_address(
          agent_id, args.get("asset", "ETH")
        ),
      })

    if perms.can_withdraw:
      tools.append({
        "name": "wallet_withdraw",
        "description": f"Withdraw native token from the wallet. Max per tx: {perms.max_withdraw_per_tx or 'unlimited'}.",
        "parameters": {
          "type": "object",
          "properties": {
            "amount": {"type": "number"},
            "to": {"type": "string", "description": "Recipient address"},
            "asset": {"type": "string", "default": "ETH"},
          },
          "required": ["amount", "to"],
        },
        "invoke": lambda args: self.withdraw(
          agent_id,
          args["amount"],
          args["to"],
          args.get("asset", "ETH"),
        ),
      })

      tools.append({
        "name": "wallet_transfer_erc20",
        "description": "Transfer an ERC-20 token from the wallet.",
        "parameters": {
          "type": "object",
          "properties": {
            "amount": {"type": "number"},
            "to": {"type": "string"},
            "contract_address": {"type": "string"},
            "asset": {"type": "string", "default": "ERC20"},
          },
          "required": ["amount", "to", "contract_address"],
        },
        "invoke": lambda args: self.transfer_erc20(
          agent_id,
          args["amount"],
          args["to"],
          args["contract_address"],
          args.get("asset", "ERC20"),
        ),
      })

    return tools
