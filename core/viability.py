from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .schema import ensure_canonical


@dataclass
class ViabilityConfig:
    min_acres: float = 0.1
    max_acres: float = 2.0
    min_buybox_sample: int = 10
    buyer_floor: int = 2
    low_demand_status: str = "REVIEW"  # REVIEW or UNVIABLE


def compute_buyer_buybox(buyer_df: pd.DataFrame, config: ViabilityConfig | None = None) -> pd.DataFrame:
    cfg = config or ViabilityConfig()
    buyer = ensure_canonical(buyer_df)

    if buyer.empty:
        return pd.DataFrame(columns=["zip", "p25", "p75", "n", "source"])

    global_p25 = buyer["lot_acres"].quantile(0.25)
    global_p75 = buyer["lot_acres"].quantile(0.75)

    by_zip = buyer.groupby("zip")["lot_acres"].agg(["count", "quantile"])
    # compute quantiles explicitly for clarity
    q = buyer.groupby("zip")["lot_acres"].quantile([0.25, 0.75]).unstack()
    q = q.rename(columns={0.25: "p25", 0.75: "p75"})
    counts = buyer.groupby("zip")["lot_acres"].size().rename("n")
    box = q.join(counts, how="left").reset_index()

    box["source"] = "zip"
    low_n = box["n"] < cfg.min_buybox_sample
    box.loc[low_n, "p25"] = global_p25
    box.loc[low_n, "p75"] = global_p75
    box.loc[low_n, "source"] = "global_fallback"
    return box[["zip", "p25", "p75", "n", "source"]]


def label_viability(
    seller_df: pd.DataFrame,
    overlap_df: pd.DataFrame | None,
    buybox_by_zip: pd.DataFrame | None,
    config: ViabilityConfig | None = None,
) -> pd.DataFrame:
    cfg = config or ViabilityConfig()
    seller = ensure_canonical(seller_df).copy()

    overlap_lookup = pd.DataFrame(columns=["zip", "buyer_count", "heat_index", "demand_tier"])
    if overlap_df is not None and not overlap_df.empty:
        overlap_lookup = overlap_df[[c for c in ["zip", "buyer_count", "heat_index", "demand_tier"] if c in overlap_df.columns]].copy()

    if buybox_by_zip is None:
        buybox_by_zip = pd.DataFrame(columns=["zip", "p25", "p75", "n", "source"])

    seller = seller.merge(overlap_lookup, how="left", on="zip")
    seller = seller.merge(buybox_by_zip, how="left", on="zip")

    status = []
    reasons_col = []

    for _, row in seller.iterrows():
        reasons: list[str] = []

        acres = row.get("lot_acres")
        missing_critical = (row.get("zip", "") == "") or ((row.get("address", "") == "") and (row.get("apn", "") == ""))
        if missing_critical:
            reasons.append("missing_critical_fields")

        if pd.isna(acres) or acres < cfg.min_acres or acres > cfg.max_acres:
            reasons.append("acres_outside_target")

        buyer_count = row.get("buyer_count")
        if pd.notna(buyer_count) and buyer_count < cfg.buyer_floor:
            reasons.append("low_buyer_demand")
        if str(row.get("demand_tier", "")).upper() == "LOW":
            reasons.append("low_heat_tier")

        within_buybox = True
        p25 = row.get("p25")
        p75 = row.get("p75")
        if pd.notna(p25) and pd.notna(p75) and pd.notna(acres):
            within_buybox = bool(p25 <= acres <= p75)
            if not within_buybox:
                reasons.append("buybox_mismatch")

        hard_fail = {"missing_critical_fields", "acres_outside_target"}
        hard = any(r in hard_fail for r in reasons)

        if hard:
            row_status = "UNVIABLE"
        elif "low_buyer_demand" in reasons and cfg.low_demand_status == "UNVIABLE":
            row_status = "UNVIABLE"
        elif reasons:
            row_status = "REVIEW"
        else:
            row_status = "VIABLE"

        status.append(row_status)
        reasons_col.append("; ".join(reasons) if reasons else "clear")

    seller["viability_status"] = status
    seller["viability_reasons"] = reasons_col
    return seller


def compute_viability_summary(seller_df: pd.DataFrame):
    df = seller_df.copy()
    total = max(len(df), 1)

    counts = df.get("viability_status", pd.Series(["VIABLE"] * len(df))).value_counts()
    reason_counts = (
        df.get("viability_reasons", pd.Series(["clear"] * len(df)))
        .astype(str)
        .str.split("; ")
        .explode()
        .value_counts()
        .rename_axis("reason")
        .reset_index(name="count")
    )

    return {
        "unviable_count": int(counts.get("UNVIABLE", 0)),
        "review_count": int(counts.get("REVIEW", 0)),
        "viable_count": int(counts.get("VIABLE", 0)),
        "unviable_rate": float(counts.get("UNVIABLE", 0) / total),
    }, reason_counts
