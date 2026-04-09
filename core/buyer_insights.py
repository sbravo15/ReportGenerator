from __future__ import annotations

import re
from typing import Dict, List

import pandas as pd

from .schema import ensure_canonical


DATE_RANGE_MONTHS = {
    "Last 12 months": 12,
    "Last 24 months": 24,
    "All time": None,
}


def _normalize_entity_tokens(text: str) -> str:
    out = text
    out = re.sub(r"\bL\s*L\s*C\b", "LLC", out)
    out = re.sub(r"\bI\s*N\s*C\b", "INC", out)
    out = re.sub(r"\bL\s*P\b", "LP", out)
    out = re.sub(r"\bL\s*T\s*D\b", "LTD", out)
    return out


def _normalize_zip(value) -> str:
    raw = "" if pd.isna(value) else str(value).strip()
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 5:
        return digits[:5]
    if len(digits) == 0:
        return ""
    return digits.zfill(5)


def normalize_buyer_records(df: pd.DataFrame) -> pd.DataFrame:
    out = ensure_canonical(df).copy()

    first = out.get("owner_first", pd.Series([""] * len(out), index=out.index)).fillna("").astype(str).str.strip()
    last = out.get("owner_last", pd.Series([""] * len(out), index=out.index)).fillna("").astype(str).str.strip()
    buyer_name = (first + " " + last).str.replace(r"\s+", " ", regex=True).str.strip()
    buyer_name = buyer_name.where(buyer_name != "", "UNKNOWN BUYER")
    buyer_name = buyer_name.str.upper().map(_normalize_entity_tokens)

    out["buyer_name"] = buyer_name
    out["zip"] = out.get("zip", pd.Series([""] * len(out), index=out.index)).map(_normalize_zip)

    tx_date = pd.to_datetime(
        out.get("last_sale_date", pd.Series([None] * len(out), index=out.index)),
        errors="coerce",
        utc=False,
    )
    out["transaction_date"] = tx_date
    out["transaction_date_iso"] = tx_date.dt.strftime("%Y-%m-%d")

    out["lot_acres"] = pd.to_numeric(
        out.get("lot_acres", pd.Series([None] * len(out), index=out.index)),
        errors="coerce",
    )
    out["last_sale_amount"] = pd.to_numeric(
        out.get("last_sale_amount", pd.Series([None] * len(out), index=out.index)),
        errors="coerce",
    )

    return out


def filter_by_date_range(df: pd.DataFrame, date_range_label: str) -> pd.DataFrame:
    months = DATE_RANGE_MONTHS.get(date_range_label)
    if months is None:
        return df.copy()

    cutoff = pd.Timestamp.today().normalize() - pd.DateOffset(months=months)
    out = df.copy()
    out = out[out["transaction_date"].notna() & (out["transaction_date"] >= cutoff)]
    return out


def build_top_buyers(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "buyer_name",
                "lots_bought",
                "last_buy_date",
                "avg_acres",
                "median_acres",
                "avg_price",
                "median_price",
            ]
        )

    grouped = (
        df.groupby("buyer_name", dropna=False)
        .agg(
            lots_bought=("buyer_name", "size"),
            last_buy_date=("transaction_date", "max"),
            avg_acres=("lot_acres", "mean"),
            median_acres=("lot_acres", "median"),
            avg_price=("last_sale_amount", "mean"),
            median_price=("last_sale_amount", "median"),
        )
        .reset_index()
        .sort_values(["lots_bought", "last_buy_date"], ascending=[False, False])
    )
    grouped["last_buy_date"] = grouped["last_buy_date"].dt.strftime("%Y-%m-%d")
    return grouped


def apply_buyer_name_search(top_buyers_df: pd.DataFrame, query: str) -> pd.DataFrame:
    q = (query or "").strip().upper()
    if q == "":
        return top_buyers_df
    return top_buyers_df[top_buyers_df["buyer_name"].str.contains(q, na=False)]


def active_buyers_count(top_buyers_df: pd.DataFrame, min_deals: int = 2) -> int:
    if top_buyers_df.empty:
        return 0
    return int((top_buyers_df["lots_bought"] >= min_deals).sum())


def buyer_summary(df: pd.DataFrame, buyer_name: str) -> Dict[str, object]:
    sub = df[df["buyer_name"] == buyer_name].copy()
    if sub.empty:
        return {
            "lots_bought": 0,
            "last_buy_date": "n/a",
            "avg_acres": None,
            "median_acres": None,
            "avg_price": None,
            "median_price": None,
        }

    last_buy = sub["transaction_date"].max()
    return {
        "lots_bought": int(len(sub)),
        "last_buy_date": "n/a" if pd.isna(last_buy) else last_buy.strftime("%Y-%m-%d"),
        "avg_acres": sub["lot_acres"].mean(),
        "median_acres": sub["lot_acres"].median(),
        "avg_price": sub["last_sale_amount"].mean(),
        "median_price": sub["last_sale_amount"].median(),
    }


def buyer_zip_breakdown(df: pd.DataFrame, buyer_name: str) -> pd.DataFrame:
    sub = df[df["buyer_name"] == buyer_name].copy()
    if sub.empty:
        return pd.DataFrame(columns=["zip", "deals_count", "percent_of_deals", "median_acres", "median_price", "last_buy_date"])

    total = max(len(sub), 1)
    out = (
        sub.groupby("zip", dropna=False)
        .agg(
            deals_count=("zip", "size"),
            median_acres=("lot_acres", "median"),
            median_price=("last_sale_amount", "median"),
            last_buy_date=("transaction_date", "max"),
        )
        .reset_index()
        .sort_values("deals_count", ascending=False)
    )
    out["percent_of_deals"] = (out["deals_count"] / total) * 100.0
    out["last_buy_date"] = out["last_buy_date"].dt.strftime("%Y-%m-%d")
    return out


def buyer_transactions(df: pd.DataFrame, buyer_name: str, zip_filter: str = "All") -> pd.DataFrame:
    sub = df[df["buyer_name"] == buyer_name].copy()
    if zip_filter != "All":
        sub = sub[sub["zip"] == zip_filter]

    if sub.empty:
        return pd.DataFrame(columns=["date", "address_or_apn", "zip", "acres", "price", "seller"])

    address = sub.get("address", pd.Series([""] * len(sub), index=sub.index)).fillna("").astype(str).str.strip()
    apn = sub.get("apn", pd.Series([""] * len(sub), index=sub.index)).fillna("").astype(str).str.strip()
    address_or_apn = address.where(address != "", apn)

    tx_data = {
        "date": sub["transaction_date_iso"],
        "address_or_apn": address_or_apn,
        "zip": sub["zip"],
        "acres": sub["lot_acres"],
        "price": sub["last_sale_amount"],
        "_date_sort": sub["transaction_date"],
    }
    if "seller" in sub.columns:
        tx_data["seller"] = sub["seller"].fillna("").astype(str)

    tx = pd.DataFrame(tx_data).sort_values("_date_sort", ascending=False)

    return tx.drop(columns=["_date_sort"])


def active_buyers_by_zip(df: pd.DataFrame, min_deals: int = 2) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["zip", "active_buyers", "total_deals", "median_acres", "median_price"])

    buyer_zip_counts = (
        df.groupby(["zip", "buyer_name"], dropna=False)
        .size()
        .rename("deals_count")
        .reset_index()
    )
    active = (
        buyer_zip_counts[buyer_zip_counts["deals_count"] >= min_deals]
        .groupby("zip")
        .size()
        .rename("active_buyers")
    )

    zip_stats = (
        df.groupby("zip", dropna=False)
        .agg(
            total_deals=("zip", "size"),
            median_acres=("lot_acres", "median"),
            median_price=("last_sale_amount", "median"),
        )
        .join(active, how="left")
        .fillna({"active_buyers": 0})
        .reset_index()
    )
    zip_stats["active_buyers"] = zip_stats["active_buyers"].astype(int)
    return zip_stats.sort_values(["active_buyers", "total_deals"], ascending=[False, False])


def top_buyer_profiles(df: pd.DataFrame, top_n_buyers: int = 5, txns_per_buyer: int = 10) -> List[Dict[str, object]]:
    top = build_top_buyers(df).head(top_n_buyers)
    profiles: List[Dict[str, object]] = []
    for _, row in top.iterrows():
        name = row["buyer_name"]
        summary = buyer_summary(df, name)
        txns = buyer_transactions(df, name).head(txns_per_buyer)
        profiles.append({"buyer_name": name, "summary": summary, "transactions": txns})
    return profiles
