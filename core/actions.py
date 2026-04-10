from dataclasses import dataclass

import pandas as pd


@dataclass
class ActionConfig:
    fit_threshold: float = 0.35
    seller_floor: int = 25


def map_actions(overlap_df: pd.DataFrame, cfg: ActionConfig) -> pd.DataFrame:
    out = overlap_df.copy()
    actions = []
    reasons = []

    for _, row in out.iterrows():
        tier = row.get("demand_tier", "MEDIUM")
        fit_rate = float(row.get("seller_fit_rate", 0.0))
        seller_count = int(row.get("seller_count", 0))
        buyer_count = int(row.get("buyer_count", 0))

        if tier == "HIGH" and fit_rate >= cfg.fit_threshold and seller_count >= cfg.seller_floor:
            actions.append("Skip trace + prioritize outreach")
            reasons.append(
                f"high demand, fit_rate {fit_rate:.2f} >= {cfg.fit_threshold:.2f}, sellers {seller_count} >= {cfg.seller_floor}"
            )
        elif tier == "HIGH" and seller_count < cfg.seller_floor:
            actions.append("Source more sellers / expand list")
            reasons.append(
                f"high demand but sellers {seller_count} < {cfg.seller_floor}"
            )
        elif tier == "LOW" and seller_count >= cfg.seller_floor:
            actions.append("Deprioritize; keep only best lots")
            reasons.append(
                f"low demand with high seller supply ({seller_count})"
            )
        elif tier == "MEDIUM":
            actions.append("Test small batch")
            reasons.append(
                f"medium demand with buyers={buyer_count}, sellers={seller_count}"
            )
        else:
            actions.append("Monitor and validate")
            reasons.append("signals are mixed; validate with small outbound sample")

    out["action"] = actions
    out["action_reason"] = reasons
    return out
