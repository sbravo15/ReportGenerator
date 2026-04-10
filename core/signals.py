from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .actions import ActionConfig, map_actions
from .demand_tiers import DemandTierConfig, assign_demand_tiers
from .schema import ensure_canonical


@dataclass
class SignalConfig:
    buyer_weight: float = 1.3
    ratio_weight: float = 10.0
    ratio_cap: float = 5.0
    demand_tier: DemandTierConfig = field(default_factory=DemandTierConfig)
    action: ActionConfig = field(default_factory=ActionConfig)


def compute_overlap_signals(
    seller_df: pd.DataFrame,
    buyer_df: pd.DataFrame,
    config: SignalConfig | None = None,
) -> pd.DataFrame:
    cfg = config or SignalConfig()
    seller = ensure_canonical(seller_df)
    buyer = ensure_canonical(buyer_df)

    if "zip" not in seller.columns or "zip" not in buyer.columns:
        return pd.DataFrame(
            columns=[
                "zip",
                "seller_count",
                "buyer_count",
                "demand_supply_ratio",
                "heat_index",
                "seller_avg_lot_acres",
                "seller_median_lot_acres",
                "buyer_p25_acres",
                "buyer_p75_acres",
                "seller_fit_rate",
                "demand_tier",
                "tier_reason",
                "action",
                "action_reason",
            ]
        )

    seller_by_zip = seller.groupby("zip", dropna=False).agg(
        seller_count=("zip", "size"),
        seller_avg_lot_acres=("lot_acres", "mean"),
        seller_median_lot_acres=("lot_acres", "median"),
    )
    buyer_by_zip = buyer.groupby("zip", dropna=False).agg(
        buyer_count=("zip", "size"),
    )

    overlap = seller_by_zip.join(buyer_by_zip, how="inner").reset_index()
    if overlap.empty:
        return pd.DataFrame(
            columns=[
                "zip",
                "seller_count",
                "buyer_count",
                "demand_supply_ratio",
                "heat_index",
                "seller_avg_lot_acres",
                "seller_median_lot_acres",
                "buyer_p25_acres",
                "buyer_p75_acres",
                "seller_fit_rate",
                "demand_tier",
                "tier_reason",
                "action",
                "action_reason",
            ]
        )

    overlap["demand_supply_ratio"] = overlap["buyer_count"] / overlap["seller_count"].clip(lower=1)
    overlap["heat_index"] = (
        overlap["buyer_count"] * cfg.buyer_weight
        + overlap["demand_supply_ratio"].clip(upper=cfg.ratio_cap) * cfg.ratio_weight
    )

    buybox = (
        buyer.groupby("zip")["lot_acres"]
        .quantile([0.25, 0.75])
        .unstack()
        .rename(columns={0.25: "buyer_p25_acres", 0.75: "buyer_p75_acres"})
        .reset_index()
    )
    overlap = overlap.merge(buybox, how="left", on="zip")

    seller_lot_zip = seller[["zip", "lot_acres"]].dropna(subset=["lot_acres"]).copy()

    def _fit_rate(row: pd.Series) -> float:
        low = row.get("buyer_p25_acres")
        high = row.get("buyer_p75_acres")
        if pd.isna(low) or pd.isna(high):
            return 0.0
        z = seller_lot_zip[seller_lot_zip["zip"] == row["zip"]]["lot_acres"]
        if z.empty:
            return 0.0
        return float(((z >= low) & (z <= high)).mean())

    overlap["seller_fit_rate"] = overlap.apply(_fit_rate, axis=1)
    overlap = assign_demand_tiers(overlap, cfg.demand_tier)
    overlap = map_actions(overlap, cfg.action)

    return overlap[
        [
            "zip",
            "seller_count",
            "buyer_count",
            "demand_supply_ratio",
            "heat_index",
            "seller_avg_lot_acres",
            "seller_median_lot_acres",
            "buyer_p25_acres",
            "buyer_p75_acres",
            "seller_fit_rate",
            "demand_tier",
            "tier_reason",
            "action",
            "action_reason",
        ]
    ]
