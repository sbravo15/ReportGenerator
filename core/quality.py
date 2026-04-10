from __future__ import annotations

import re

import pandas as pd

from .schema import ensure_canonical


ZIP_RE = re.compile(r"^\d{5}$")


def detect_quality_flags(seller_df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_canonical(seller_df)
    out = df.copy()

    out["missing_zip"] = out.get("zip", pd.Series([""] * len(out), index=out.index)).eq("")
    out["invalid_zip"] = ~out.get("zip", pd.Series([""] * len(out), index=out.index)).astype(str).str.match(ZIP_RE)

    address_blank = out.get("address", pd.Series([""] * len(out), index=out.index)).eq("")
    apn_blank = out.get("apn", pd.Series([""] * len(out), index=out.index)).eq("")
    out["missing_address_and_apn"] = address_blank & apn_blank

    lot_acres = pd.to_numeric(out.get("lot_acres", pd.Series([None] * len(out), index=out.index)), errors="coerce")
    out["invalid_acres"] = lot_acres.isna() | (lot_acres <= 0)

    present_fields = pd.DataFrame(
        {
            "zip": ~out["missing_zip"],
            "address_or_apn": ~out["missing_address_and_apn"],
            "lot_acres": ~out["invalid_acres"],
        }
    )
    out["data_completeness_score"] = present_fields.mean(axis=1)
    return out


def compute_quality_summary(flagged_df: pd.DataFrame):
    df = detect_quality_flags(flagged_df)
    total = max(len(df), 1)

    deduped_records = len(df)
    if "is_duplicate" in df.columns:
        duplicate_groups = (
            df[df["is_duplicate"]]
            .groupby("duplicate_group_id", dropna=False)
            .size()
        )
        duplicate_excess = int((duplicate_groups - 1).clip(lower=0).sum())
        deduped_records = int(len(df) - duplicate_excess)

    duplicate_rate = 0.0
    if "is_duplicate" in df.columns:
        duplicate_rate = float(df["is_duplicate"].mean())

    kpis = {
        "total_records": int(len(df)),
        "deduped_records": int(deduped_records),
        "duplicate_rate": duplicate_rate,
        "missing_zip_rate": float(df["missing_zip"].mean()),
        "missing_address_or_apn_rate": float(df["missing_address_and_apn"].mean()),
        "invalid_acres_rate": float(df["invalid_acres"].mean()),
    }

    issues = pd.DataFrame(
        [
            {
                "issue_type": "missing_zip",
                "affected_count": int(df["missing_zip"].sum()),
                "affected_pct": float(df["missing_zip"].mean()),
                "recommended_fix": "Append ZIP from county/address reference or drop rows.",
            },
            {
                "issue_type": "missing_address_and_apn",
                "affected_count": int(df["missing_address_and_apn"].sum()),
                "affected_pct": float(df["missing_address_and_apn"].mean()),
                "recommended_fix": "Require at least address or APN before enrichment.",
            },
            {
                "issue_type": "invalid_zip",
                "affected_count": int(df["invalid_zip"].sum()),
                "affected_pct": float(df["invalid_zip"].mean()),
                "recommended_fix": "Normalize ZIP to 5 digits.",
            },
            {
                "issue_type": "invalid_acres",
                "affected_count": int(df["invalid_acres"].sum()),
                "affected_pct": float(df["invalid_acres"].mean()),
                "recommended_fix": "Backfill lot acres from square-feet/source listing.",
            },
        ]
    ).sort_values("affected_count", ascending=False)

    return kpis, issues
