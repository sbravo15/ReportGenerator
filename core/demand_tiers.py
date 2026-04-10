from dataclasses import dataclass

import pandas as pd


@dataclass
class DemandTierConfig:
    high_percentile: float = 0.8
    low_percentile: float = 0.2
    high_buyer_floor: int = 5
    medium_buyer_min: int = 2
    medium_buyer_max: int = 4


def assign_demand_tiers(overlap_df: pd.DataFrame, cfg: DemandTierConfig) -> pd.DataFrame:
    if overlap_df.empty:
        out = overlap_df.copy()
        out["demand_tier"] = pd.Series(dtype="object")
        out["tier_reason"] = pd.Series(dtype="object")
        return out

    out = overlap_df.copy()
    high_cut = out["heat_index"].quantile(cfg.high_percentile)
    low_cut = out["heat_index"].quantile(cfg.low_percentile)

    tiers = []
    reasons = []
    for _, row in out.iterrows():
        buyer_count = int(row["buyer_count"])
        heat_index = float(row["heat_index"])

        high_rule = heat_index >= high_cut and buyer_count >= cfg.high_buyer_floor
        low_rule = heat_index <= low_cut or buyer_count < cfg.medium_buyer_min
        medium_volume = cfg.medium_buyer_min <= buyer_count <= cfg.medium_buyer_max

        if high_rule:
            tiers.append("HIGH")
            reasons.append(
                f"heat in top {int((1 - cfg.high_percentile) * 100)}% and buyers >= {cfg.high_buyer_floor}"
            )
        elif low_rule:
            tiers.append("LOW")
            if buyer_count < cfg.medium_buyer_min:
                reasons.append(f"buyer_count < {cfg.medium_buyer_min}")
            else:
                reasons.append(f"heat in bottom {int(cfg.low_percentile * 100)}%")
        else:
            tiers.append("MEDIUM")
            if medium_volume:
                reasons.append(
                    f"buyer_count between {cfg.medium_buyer_min}-{cfg.medium_buyer_max}"
                )
            else:
                reasons.append("mid-tier heat index")

    out["demand_tier"] = tiers
    out["tier_reason"] = reasons
    return out
