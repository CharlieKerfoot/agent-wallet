"""Load WalletConfig from a YAML file."""
from __future__ import annotations

from pathlib import Path

import yaml

from agent_wallet.config import AgentConfig, WalletConfig
from agent_wallet.permissions import Permissions


def load_config(path: str | Path) -> WalletConfig:
  """Parse a YAML config file into a WalletConfig."""
  raw = yaml.safe_load(Path(path).read_text())

  agents: dict[str, AgentConfig] = {}
  for agent_id, agent_raw in raw.get("agents", {}).items():
    perms_raw = agent_raw.get("permissions", {})
    agents[agent_id] = AgentConfig(
      agent_id=agent_id,
      permissions=Permissions(**perms_raw),
    )

  return WalletConfig(
    cdp_api_key_id=raw.get("cdp_api_key_id"),
    cdp_api_key_secret=raw.get("cdp_api_key_secret"),
    cdp_wallet_secret=raw.get("cdp_wallet_secret"),
    network_id=raw.get("network_id", "base-sepolia"),
    wallet_address=raw.get("wallet_address"),
    idempotency_key=raw.get("idempotency_key"),
    agents=agents,
  )
