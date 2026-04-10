from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd


BUCKET_ORDER = ["UNVIABLE", "INFILL", "LARGE_LOT", "BIG_LOT", "MINI_TRACT", "XL", "UNKNOWN"]


def detect_on_market(df: pd.DataFrame, listing_col: str = "listing_status") -> pd.Series:
    if listing_col not in df.columns:
        return pd.Series([False] * len(df), index=df.index)
    status = df[listing_col].fillna("").astype(str).str.upper().str.strip()
    keywords = ["ACTIVE", "PENDING", "LIST", "FORSALE", "FOR SALE", "CONTINGENT", "COMING SOON", "MLS"]
    return status.apply(lambda x: any(k in x for k in keywords))


def lot_size_class(acres) -> str:
    if pd.isna(acres):
        return "UNKNOWN"
    if acres < 0.12:
        return "UNVIABLE"
    if acres <= 0.30:
        return "INFILL"
    if acres <= 0.50:
        return "LARGE_LOT"
    if acres <= 1.0:
        return "BIG_LOT"
    if acres <= 5.0:
        return "MINI_TRACT"
    return "XL"


def apply_size_preset(df: pd.DataFrame, preset_name: str, bucket_col: str = "lot_size_class") -> pd.DataFrame:
    if bucket_col not in df.columns:
        return df
    if preset_name == "All":
        return df
    mapping = {
        "UNVIABLE (<0.12)": "UNVIABLE",
        "INFILL (0.12-0.30)": "INFILL",
        "LARGE_LOT (>0.30-0.50)": "LARGE_LOT",
        "BIG_LOT (>0.50-1.0)": "BIG_LOT",
        "MINI_TRACT (>1.0-5.0)": "MINI_TRACT",
        "XL (5+)": "XL",
        "UNKNOWN": "UNKNOWN",
    }
    target = mapping.get(preset_name)
    if target is None:
        return df
    return df[df[bucket_col] == target]


def add_lot_size_class(df: pd.DataFrame, acres_col: str = "lot_acres", out_col: str = "lot_size_class") -> pd.DataFrame:
    out = df.copy()
    out[out_col] = out.get(acres_col, pd.Series([None] * len(out), index=out.index)).apply(lot_size_class)
    return out


def compute_duplicate_metrics(tagged_df: pd.DataFrame, total_records: int | None = None) -> Dict[str, float]:
    total = int(total_records if total_records is not None else len(tagged_df))
    if tagged_df.empty or "is_duplicate" not in tagged_df.columns:
        return {
            "total_uploaded": total,
            "duplicate_rows_raw": 0,
            "duplicate_groups": 0,
            "largest_duplicate_group_size": 0,
            "deduped_records": total,
            "duplicate_rate_pct": 0.0,
        }

    dup_groups = (
        tagged_df[tagged_df["is_duplicate"]]
        .groupby("duplicate_group_id", dropna=False)
        .size()
        .rename("group_size")
        .reset_index()
    )
    duplicate_rows_raw = int(sum(max(int(v) - 1, 0) for v in dup_groups["group_size"])) if not dup_groups.empty else 0
    deduped_records = int(max(total - duplicate_rows_raw, 0))
    duplicate_rate_pct = (duplicate_rows_raw / total * 100.0) if total > 0 else 0.0

    return {
        "total_uploaded": total,
        "duplicate_rows_raw": duplicate_rows_raw,
        "duplicate_groups": int(len(dup_groups)),
        "largest_duplicate_group_size": int(dup_groups["group_size"].max()) if not dup_groups.empty else 0,
        "deduped_records": deduped_records,
        "duplicate_rate_pct": duplicate_rate_pct,
    }


def lot_bucket_counts(df: pd.DataFrame, bucket_col: str = "lot_size_class") -> Dict[str, int]:
    values = df[bucket_col].value_counts().to_dict() if bucket_col in df.columns else {}
    return {bucket: int(values.get(bucket, 0)) for bucket in BUCKET_ORDER}


def build_working_dataset(
    tagged_df: pd.DataFrame,
    deduped_df: pd.DataFrame,
    *,
    use_deduped: bool,
    off_market_only: bool,
    size_preset: str,
) -> pd.DataFrame:
    base = deduped_df.copy() if use_deduped else tagged_df.copy()
    base["on_market"] = detect_on_market(base)
    if off_market_only:
        base = base[~base["on_market"]].copy()
    base = add_lot_size_class(base)
    base = apply_size_preset(base, size_preset)
    return base


def build_export_frames(
    *,
    tagged_df: pd.DataFrame,
    deduped_df: pd.DataFrame,
    viable_labeled_df: pd.DataFrame,
    scored_df: pd.DataFrame,
    use_deduped: bool,
    off_market_only: bool,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    skip_trace_ready = scored_df[scored_df.get("viability_status", "") == "VIABLE"].copy()
    clean_outreach = skip_trace_ready.copy() if not skip_trace_ready.empty else viable_labeled_df.copy()

    review_parts = []
    duplicate_review = tagged_df[tagged_df.get("is_duplicate", False)].copy()
    if not duplicate_review.empty:
        duplicate_review["review_reason"] = "duplicate_cluster"
        review_parts.append(duplicate_review)

    if off_market_only:
        on_market_removed = (deduped_df if use_deduped else tagged_df).copy()
        on_market_removed["on_market"] = detect_on_market(on_market_removed)
        on_market_removed = on_market_removed[on_market_removed["on_market"]].copy()
        if not on_market_removed.empty:
            on_market_removed["review_reason"] = "on_market_removed"
            review_parts.append(on_market_removed)

    if "lot_size_class" in viable_labeled_df.columns:
        size_review = viable_labeled_df[viable_labeled_df["lot_size_class"].isin(["UNVIABLE", "UNKNOWN"])].copy()
        if not size_review.empty:
            size_review["review_reason"] = "unviable_or_unknown_size"
            review_parts.append(size_review)

    if "viability_status" in viable_labeled_df.columns:
        viability_review = viable_labeled_df[viable_labeled_df["viability_status"].isin(["UNVIABLE", "REVIEW"])].copy()
        if not viability_review.empty:
            viability_review["review_reason"] = viability_review["viability_status"].astype(str).str.lower()
            review_parts.append(viability_review)

    review_file = pd.concat(review_parts, ignore_index=True) if review_parts else pd.DataFrame()
    return clean_outreach, review_file
