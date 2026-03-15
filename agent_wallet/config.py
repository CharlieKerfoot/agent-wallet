from __future__ import annotations

from pydantic import BaseModel, Field

from agent_wallet.permissions import Permissions


class AgentConfig(BaseModel):
  """Configuration for a single agent's wallet access."""

  agent_id: str = Field(..., description="Unique identifier for this agent")
  permissions: Permissions = Field(default_factory=Permissions)


class WalletConfig(BaseModel):
  """Top-level configuration for the shared wallet."""

  # CDP credentials — can also come from env vars
  cdp_api_key_id: str | None = Field(default=None, description="CDP API Key ID")
  cdp_api_key_secret: str | None = Field(default=None, description="CDP API Key Secret")
  cdp_wallet_secret: str | None = Field(default=None, description="CDP Wallet Secret")

  network_id: str = Field(default="base-sepolia", description="Network to use")
  wallet_address: str | None = Field(
    default=None,
    description="Existing wallet address to reuse. None = create new wallet.",
  )
  idempotency_key: str | None = Field(
    default=None,
    description="Idempotency key for deterministic wallet creation.",
  )

  agents: dict[str, AgentConfig] = Field(
    default_factory=dict,
    description="Map of agent_id -> AgentConfig",
  )
