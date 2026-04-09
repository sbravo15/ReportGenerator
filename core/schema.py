from __future__ import annotations

import re
from typing import Dict, Iterable

import pandas as pd


CANONICAL_ALIASES: Dict[str, Iterable[str]] = {
    "record_id": ["Id", "Record Id", "Property Id"],
    "address": ["Address", "Property Address", "Site Address"],
    "city": ["City", "Property City"],
    "state": ["State", "Property State"],
    "zip": ["Zip", "ZIP", "Postal Code"],
    "county": ["County"],
    "apn": ["APN", "Parcel Id", "Parcel Number", "Parcel", "APN/Parcel"],
    "lot_acres": ["Lot (Acres)", "Lot Acres", "Acreage"],
    "owner_first": ["Owner 1 First Name", "Owner First Name"],
    "owner_last": ["Owner 1 Last Name", "Owner Last Name"],
    "owner_mailing_address": ["Owner Mailing Address", "Mailing Address"],
    "owner_mailing_city": ["Owner Mailing City", "Mailing City"],
    "owner_mailing_state": ["Owner Mailing State", "Mailing State"],
    "owner_type": ["Owner Type"],
    "listing_status": ["Listing Status"],
    "days_on_market": ["Days on Market"],
    "last_sale_date": ["Last Sale Date"],
    "last_sale_amount": ["Last Sale Amount"],
    "estimated_equity_percent": ["Estimated Equity Percent"],
    "default_amount": ["Default Amount"],
    "auction_date": ["Auction Date"],
}


def _normalize_col_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())


def _resolve_columns(df: pd.DataFrame) -> Dict[str, str]:
    normalized_map = {_normalize_col_name(c): c for c in df.columns}
    resolved: Dict[str, str] = {}
    for canonical, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            key = _normalize_col_name(alias)
            if key in normalized_map:
                resolved[canonical] = normalized_map[key]
                break
    return resolved


def normalize_propwire_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    resolved = _resolve_columns(out)

    for canonical, raw_col in resolved.items():
        out[canonical] = out[raw_col]

    for text_col in [
        "address",
        "city",
        "state",
        "zip",
        "county",
        "apn",
        "owner_first",
        "owner_last",
        "owner_mailing_address",
        "owner_mailing_city",
        "owner_mailing_state",
        "owner_type",
        "listing_status",
    ]:
        if text_col in out.columns:
            out[text_col] = out[text_col].fillna("").astype(str).str.strip()

    for numeric_col in [
        "lot_acres",
        "days_on_market",
        "last_sale_amount",
        "estimated_equity_percent",
        "default_amount",
    ]:
        if numeric_col in out.columns:
            out[numeric_col] = pd.to_numeric(out[numeric_col], errors="coerce")

    for date_col in ["last_sale_date", "auction_date"]:
        if date_col in out.columns:
            out[date_col] = pd.to_datetime(out[date_col], errors="coerce")

    if "zip" in out.columns:
        out["zip"] = out["zip"].str.replace(r"\.0$", "", regex=True)
    if "state" in out.columns:
        out["state"] = out["state"].str.upper()
    if "owner_mailing_state" in out.columns:
        out["owner_mailing_state"] = out["owner_mailing_state"].str.upper()

    return out


def ensure_canonical(df: pd.DataFrame) -> pd.DataFrame:
    required = {"zip", "lot_acres", "address", "apn"}
    if required.issubset(set(df.columns)):
        return df.copy()
    return normalize_propwire_df(df)
