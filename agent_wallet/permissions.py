from __future__ import annotations

from pydantic import BaseModel, Field


class Permissions(BaseModel):
  """Per-agent permission flags that control what operations are allowed."""

  can_deposit: bool = Field(default=False, description="Allow this agent to deposit (receive) funds")
  can_withdraw: bool = Field(default=False, description="Allow this agent to withdraw (send) funds")
  max_withdraw_per_tx: float | None = Field(
    default=None,
    description="Max amount (in native token units) per withdrawal. None = unlimited.",
  )
  allowed_assets: list[str] | None = Field(
    default=None,
    description="Allowlist of asset symbols (e.g. ['ETH','USDC']). None = all allowed.",
  )

  def check_withdraw(self, amount: float, asset: str = "ETH") -> None:
    if not self.can_withdraw:
      raise PermissionError("This agent is not allowed to withdraw.")
    if self.max_withdraw_per_tx is not None and amount > self.max_withdraw_per_tx:
      raise PermissionError(
        f"Amount {amount} exceeds per-tx limit of {self.max_withdraw_per_tx}"
      )
    if self.allowed_assets is not None and asset not in self.allowed_assets:
      raise PermissionError(f"Asset '{asset}' is not in the allowlist: {self.allowed_assets}")

  def check_deposit(self, asset: str = "ETH") -> None:
    if not self.can_deposit:
      raise PermissionError("This agent is not allowed to deposit.")
    if self.allowed_assets is not None and asset not in self.allowed_assets:
      raise PermissionError(f"Asset '{asset}' is not in the allowlist: {self.allowed_assets}")
