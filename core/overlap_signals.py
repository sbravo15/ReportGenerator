from dataclasses import dataclass, field
from math import log1p

import pandas as pd

from .actions import ActionConfig, map_actions
from .demand_tiers import DemandTierConfig, assign_demand_tiers


@dataclass
class OverlapConfig:
    demand_tier: DemandTierConfig = field(default_factory=DemandTierConfig)
    action: ActionConfig = field(default_factory=ActionConfig)


def _coerce_zip_and_lot(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Zip" in out.columns:
        out["Zip"] = out["Zip"].astype(str).str.strip()
    out["Lot (Acres)"] = pd.to_numeric(
        out.get("Lot (Acres)", pd.Series([None] * len(out), index=out.index)),
        errors="coerce",
    )
    return out


def _owner_display_name(df: pd.DataFrame) -> pd.Series:
    first = df.get("Owner 1 First Name", pd.Series([""] * len(df), index=df.index)).fillna("").astype(str).str.strip()
    last = df.get("Owner 1 Last Name", pd.Series([""] * len(df), index=df.index)).fillna("").astype(str).str.strip()
    full = (first + " " + last).str.strip()
    name = full.where(full != "", last)
    name = name.where(name != "", first)
    return name.where(name != "", "UNKNOWN OWNER")


def compute_overlap_signals(
    seller_df: pd.DataFrame,
    buyer_df: pd.DataFrame,
    config: OverlapConfig,
) -> pd.DataFrame:
    seller = _coerce_zip_and_lot(seller_df)
    buyer = _coerce_zip_and_lot(buyer_df)

    if "Zip" not in seller.columns or "Zip" not in buyer.columns:
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

    seller_zip = seller.groupby("Zip").agg(
        seller_count=("Zip", "size"),
        seller_avg_lot_acres=("Lot (Acres)", "mean"),
        seller_median_lot_acres=("Lot (Acres)", "median"),
    )
    buyer_zip = buyer.groupby("Zip").agg(buyer_count=("Zip", "size"))

    overlap = seller_zip.join(buyer_zip, how="inner").reset_index().rename(columns={"Zip": "zip"})
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
    overlap["heat_index"] = overlap.apply(
        lambda row: row["demand_supply_ratio"] * log1p(row["buyer_count"]),
        axis=1,
    )

    buyer_band = (
        buyer.groupby("Zip")["Lot (Acres)"]
        .quantile([0.25, 0.75])
        .unstack()
        .rename(columns={0.25: "buyer_p25_acres", 0.75: "buyer_p75_acres"})
        .reset_index()
        .rename(columns={"Zip": "zip"})
    )
    overlap = overlap.merge(buyer_band, on="zip", how="left")

    seller_lots = seller[["Zip", "Lot (Acres)"]].copy().rename(columns={"Zip": "zip"})

    def _fit_rate_for_zip(row: pd.Series) -> float:
        zip_lots = seller_lots[seller_lots["zip"] == row["zip"]]["Lot (Acres)"].dropna()
        if zip_lots.empty:
            return 0.0
        low = row.get("buyer_p25_acres")
        high = row.get("buyer_p75_acres")
        if pd.isna(low) or pd.isna(high):
            return 0.0
        return float(((zip_lots >= low) & (zip_lots <= high)).mean())

    overlap["seller_fit_rate"] = overlap.apply(_fit_rate_for_zip, axis=1)

    overlap = assign_demand_tiers(overlap, config.demand_tier)
    overlap = map_actions(overlap, config.action)

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


def zip_drilldown(
    zip_code: str,
    seller_df: pd.DataFrame,
    buyer_df: pd.DataFrame,
    overlap_df: pd.DataFrame,
    top_n: int = 25,
):
    seller = _coerce_zip_and_lot(seller_df)
    buyer = _coerce_zip_and_lot(buyer_df)
    zip_code = str(zip_code).strip()

    zip_row = overlap_df[overlap_df["zip"].astype(str) == zip_code]
    p25 = None
    p75 = None
    if not zip_row.empty:
        p25 = zip_row.iloc[0].get("buyer_p25_acres")
        p75 = zip_row.iloc[0].get("buyer_p75_acres")

    buyers_zip = buyer[buyer["Zip"] == zip_code].copy()
    buyers_zip["Buyer Name"] = _owner_display_name(buyers_zip)
    buyers_zip["Last Sale Date"] = pd.to_datetime(
        buyers_zip.get("Last Sale Date", pd.Series([None] * len(buyers_zip), index=buyers_zip.index)),
        errors="coerce",
    )
    buyer_profiles = (
        buyers_zip.groupby("Buyer Name", dropna=False)
        .agg(
            lots_bought=("Zip", "size"),
            median_acres=("Lot (Acres)", "median"),
            last_buy_date=("Last Sale Date", "max"),
        )
        .reset_index()
        .sort_values(["lots_bought", "last_buy_date"], ascending=[False, False])
        .head(top_n)
    )
    buyer_profiles["last_buy_recency_days"] = (
        pd.Timestamp.today().normalize() - buyer_profiles["last_buy_date"]
    ).dt.days

    sellers_zip = seller[seller["Zip"] == zip_code].copy()
    sellers_zip["match_buyer_band"] = False
    if p25 is not None and p75 is not None and pd.notna(p25) and pd.notna(p75):
        sellers_zip["match_buyer_band"] = sellers_zip["Lot (Acres)"].between(p25, p75, inclusive="both")

    match_sellers = sellers_zip.sort_values("match_buyer_band", ascending=False).head(top_n)

    return buyer_profiles, match_sellers
