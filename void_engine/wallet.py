"""
Al-Jabr Wallet Middleware — Machine Financial Autonomy v1.0

The Machine Wallet gives the 4000-series economic agency. Instead of
just negotiating resource states, agents now have a Cost Metric that
gates decisions. If an action is too "expensive" (heat, energy, credits),
the agent simply won't do it.

QSB Root (Acquisition/Earning):
  QSB.A — Acquire: Convert excess flywheel energy into compute credits
  QSB.D — Disburse: Spend credits to purchase cooling, nutrients, etc.
  QSB.V — Audit: Verify wallet balance before expensive operations

The wallet tracks a virtual balance of "Compute Credits" (CC) that
represents stored potential — energy that has been converted into
economic purchasing power.

Earning model:
  During Night Cycle fasting (HFZ), excess flywheel energy above 60%
  capacity is "signed" by Silk-Link and converted into CC at rate
  1 CC = 5 Wh of excess energy.

Spending model:
  LN2 refill     = 15 CC
  Nutrient dose   = 3 CC
  Heavy compute   = 8 CC
  Silk repair     = 10 CC

Budget Approval Gate:
  Every apply_action call passes through wallet_check_budget().
  If the action's cost exceeds available balance, it's blocked
  with a "BUDGET_DENIED" verdict.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


ENERGY_CAPACITY_WH = 250.0
EARNING_THRESHOLD_PCT = 0.60
WH_PER_CREDIT = 5.0

ACTION_COSTS = {
    "pump_cycle": 2.0,
    "flywheel_boost": 3.0,
    "nutrient_dose": 3.0,
    "air_curtain_activate": 5.0,
    "nitrogen_vent": 4.0,
    "silk_test": 1.0,
    "sensor_calibrate": 0.5,
    "wallet_earn": 0.0,
    "wallet_spend": 0.0,
    "wallet_audit": 0.0,
    "wallet_status": 0.0,
    "wallet_check_budget": 0.0,
    "wallet_freeze": 0.0,
    "wallet_unfreeze": 0.0,
    "air_curtain_deactivate": 0.0,
    "mesh_scan": 0.1,
    "mesh_handshake": 0.05,
    "mesh_relay": 0.2,
    "mesh_send": 0.3,
    "mesh_buffer": 0.5,
    "mesh_connect": 0.0,
    "mesh_disconnect": 0.0,
}

PURCHASE_COSTS = {
    "ln2_refill": 15.0,
    "nutrient_supply": 3.0,
    "heavy_compute": 8.0,
    "silk_repair": 10.0,
    "coolant_flush": 6.0,
}


@dataclass
class Transaction:
    tx_type: str
    amount: float
    balance_after: float
    source_or_target: str
    description: str
    timestamp: float = field(default_factory=time.time)
    root_command: str = ""

    def to_dict(self):
        return {
            "tx_type": self.tx_type,
            "amount": round(self.amount, 2),
            "balance_after": round(self.balance_after, 2),
            "source_or_target": self.source_or_target,
            "description": self.description,
            "timestamp": self.timestamp,
            "root_command": self.root_command,
        }


@dataclass
class BudgetVerdict:
    approved: bool
    action_type: str
    cost: float
    balance: float
    message: str
    frozen: bool = False

    def to_dict(self):
        return {
            "approved": self.approved,
            "action_type": self.action_type,
            "cost": round(self.cost, 2),
            "balance": round(self.balance, 2),
            "message": self.message,
            "frozen": self.frozen,
        }


class AlJabrWalletMiddleware:
    def __init__(self, initial_balance: float = 50.0):
        self._balance: float = initial_balance
        self._frozen: bool = False
        self._ledger: List[Transaction] = []
        self._total_earned: float = 0.0
        self._total_spent: float = 0.0
        self._budget_checks: int = 0
        self._budget_denials: int = 0
        self._earning_events: int = 0
        self._spending_events: int = 0

        self._ledger.append(Transaction(
            tx_type="genesis",
            amount=initial_balance,
            balance_after=initial_balance,
            source_or_target="system",
            description=f"Wallet initialized with {initial_balance} CC",
        ))

    def check_budget(self, action: Dict) -> BudgetVerdict:
        self._budget_checks += 1
        action_type = action.get("type", "unknown")
        cost = ACTION_COSTS.get(action_type, 1.0)

        if self._frozen:
            return BudgetVerdict(
                approved=False,
                action_type=action_type,
                cost=cost,
                balance=self._balance,
                message=f"BUDGET_FROZEN: Wallet is frozen during critical operations. Action '{action_type}' held.",
                frozen=True,
            )

        if cost <= 0:
            return BudgetVerdict(
                approved=True,
                action_type=action_type,
                cost=0,
                balance=self._balance,
                message=f"Free action: {action_type}",
            )

        if self._balance >= cost:
            return BudgetVerdict(
                approved=True,
                action_type=action_type,
                cost=cost,
                balance=self._balance,
                message=f"Budget approved: {cost} CC for {action_type} (balance: {self._balance:.1f} CC)",
            )
        else:
            self._budget_denials += 1
            return BudgetVerdict(
                approved=False,
                action_type=action_type,
                cost=cost,
                balance=self._balance,
                message=f"BUDGET_DENIED: {action_type} costs {cost} CC but only {self._balance:.1f} CC available.",
            )

    def debit(self, action: Dict) -> Dict:
        action_type = action.get("type", "unknown")
        cost = ACTION_COSTS.get(action_type, 1.0)

        if cost <= 0:
            return {"debited": False, "cost": 0, "balance": self._balance, "reason": "free_action"}

        if self._balance < cost:
            return {"debited": False, "cost": cost, "balance": self._balance, "reason": "insufficient_funds"}

        self._balance -= cost
        self._total_spent += cost
        self._spending_events += 1

        self._ledger.append(Transaction(
            tx_type="debit",
            amount=cost,
            balance_after=self._balance,
            source_or_target=action_type,
            description=f"Action cost: {action_type}",
        ))
        self._trim_ledger()

        return {"debited": True, "cost": cost, "balance": self._balance}

    def earn(self, source: str, amount: float, energy_pct: float, root_command: str = "QSB.A") -> Dict:
        if energy_pct < EARNING_THRESHOLD_PCT:
            return {
                "earned": False,
                "reason": f"Energy at {energy_pct*100:.0f}% — below {EARNING_THRESHOLD_PCT*100:.0f}% earning threshold",
                "balance": self._balance,
            }

        excess_pct = energy_pct - EARNING_THRESHOLD_PCT
        max_earn = excess_pct * ENERGY_CAPACITY_WH / WH_PER_CREDIT
        actual_earn = min(amount, max_earn)

        if actual_earn <= 0:
            return {"earned": False, "reason": "No excess energy to harvest", "balance": self._balance}

        self._balance += actual_earn
        self._total_earned += actual_earn
        self._earning_events += 1

        self._ledger.append(Transaction(
            tx_type="credit",
            amount=actual_earn,
            balance_after=self._balance,
            source_or_target=source,
            description=f"Harvested {actual_earn:.1f} CC from {source} (energy at {energy_pct*100:.0f}%)",
            root_command=root_command,
        ))
        self._trim_ledger()

        return {
            "earned": True,
            "amount": round(actual_earn, 2),
            "balance": round(self._balance, 2),
            "source": source,
            "excess_pct": round(excess_pct * 100, 1),
        }

    def spend(self, target: str, amount: Optional[float] = None, root_command: str = "QSB.D") -> Dict:
        cost = amount if amount is not None else PURCHASE_COSTS.get(target, 10.0)

        if self._frozen:
            return {"spent": False, "reason": "Wallet frozen", "balance": self._balance}

        if self._balance < cost:
            return {
                "spent": False,
                "reason": f"Insufficient credits: need {cost} CC, have {self._balance:.1f} CC",
                "balance": self._balance,
                "cost": cost,
            }

        self._balance -= cost
        self._total_spent += cost
        self._spending_events += 1

        self._ledger.append(Transaction(
            tx_type="purchase",
            amount=cost,
            balance_after=self._balance,
            source_or_target=target,
            description=f"Purchased {target} for {cost} CC",
            root_command=root_command,
        ))
        self._trim_ledger()

        return {
            "spent": True,
            "target": target,
            "cost": round(cost, 2),
            "balance": round(self._balance, 2),
        }

    def audit(self) -> Dict:
        return {
            "balance": round(self._balance, 2),
            "total_earned": round(self._total_earned, 2),
            "total_spent": round(self._total_spent, 2),
            "net_flow": round(self._total_earned - self._total_spent, 2),
            "budget_checks": self._budget_checks,
            "budget_denials": self._budget_denials,
            "earning_events": self._earning_events,
            "spending_events": self._spending_events,
            "frozen": self._frozen,
            "ledger_size": len(self._ledger),
            "denial_rate": round(self._budget_denials / max(self._budget_checks, 1) * 100, 1),
        }

    def freeze(self) -> Dict:
        self._frozen = True
        self._ledger.append(Transaction(
            tx_type="freeze",
            amount=0,
            balance_after=self._balance,
            source_or_target="system",
            description="Wallet frozen — critical operations mode",
            root_command="QSB.I",
        ))
        self._trim_ledger()
        return {"frozen": True, "balance": self._balance}

    def unfreeze(self) -> Dict:
        self._frozen = False
        self._ledger.append(Transaction(
            tx_type="unfreeze",
            amount=0,
            balance_after=self._balance,
            source_or_target="system",
            description="Wallet unfrozen — normal operations resumed",
            root_command="QSB.R",
        ))
        self._trim_ledger()
        return {"frozen": False, "balance": self._balance}

    def get_status(self) -> Dict:
        recent = self._ledger[-5:] if self._ledger else []
        return {
            "balance": round(self._balance, 2),
            "frozen": self._frozen,
            "total_earned": round(self._total_earned, 2),
            "total_spent": round(self._total_spent, 2),
            "earning_events": self._earning_events,
            "spending_events": self._spending_events,
            "recent_transactions": [t.to_dict() for t in recent],
        }

    def get_ledger(self, limit: int = 20) -> List[Dict]:
        return [t.to_dict() for t in self._ledger[-limit:]]

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def frozen(self) -> bool:
        return self._frozen

    def _trim_ledger(self):
        if len(self._ledger) > 200:
            self._ledger = self._ledger[-200:]
