from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class ScoreConfig:
    w_demand_tier: float = 0.30
    w_heat: float = 0.30
    w_buybox_fit: float = 0.20
    w_completeness: float = 0.20
    w_penalty: float = 0.40


def compute_opportunity_score(seller_df: pd.DataFrame, config: ScoreConfig | None = None) -> pd.DataFrame:
    cfg = config or ScoreConfig()
    df = seller_df.copy()

    tier_map = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.2}
    tier_score = df.get("demand_tier", pd.Series(["LOW"] * len(df))).map(tier_map).fillna(0.2)

    heat = pd.to_numeric(df.get("heat_index", pd.Series([0.0] * len(df))), errors="coerce").fillna(0)
    heat_norm = heat / max(float(heat.max()), 1.0)

    p25 = pd.to_numeric(df.get("p25", pd.Series([None] * len(df))), errors="coerce")
    p75 = pd.to_numeric(df.get("p75", pd.Series([None] * len(df))), errors="coerce")
    acres = pd.to_numeric(df.get("lot_acres", pd.Series([None] * len(df))), errors="coerce")
    buybox_fit = ((acres >= p25) & (acres <= p75)).fillna(False).astype(float)

    completeness = pd.to_numeric(df.get("data_completeness_score", pd.Series([0.0] * len(df))), errors="coerce").fillna(0)

    penalties = df.get("viability_status", pd.Series(["VIABLE"] * len(df))).map({"UNVIABLE": 1.0, "REVIEW": 0.5, "VIABLE": 0.0}).fillna(0.0)

    score = (
        cfg.w_demand_tier * tier_score
        + cfg.w_heat * heat_norm
        + cfg.w_buybox_fit * buybox_fit
        + cfg.w_completeness * completeness
        - cfg.w_penalty * penalties
    )

    df["within_buybox_band"] = buybox_fit.astype(bool)
    df["opportunity_score"] = (score * 100).clip(lower=0).round(1)
    df["score_reason"] = df.apply(score_explanation, axis=1)
    return df.sort_values("opportunity_score", ascending=False)


def score_explanation(seller_row: pd.Series) -> str:
    parts = []
    parts.append(f"tier={seller_row.get('demand_tier', 'LOW')}")
    parts.append(f"heat={float(seller_row.get('heat_index', 0)):.2f}")
    parts.append("buybox_match" if bool(seller_row.get("within_buybox_band", False)) else "buybox_mismatch")
    parts.append(f"status={seller_row.get('viability_status', 'REVIEW')}")
    return " | ".join(parts)
