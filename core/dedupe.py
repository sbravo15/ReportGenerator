from __future__ import annotations

import re

import pandas as pd

from .schema import ensure_canonical


SUFFIX_MAP = {
    " STREET": " ST",
    " AVENUE": " AVE",
    " ROAD": " RD",
    " DRIVE": " DR",
    " LANE": " LN",
    " COURT": " CT",
    " PLACE": " PL",
    " BOULEVARD": " BLVD",
}


def normalize_address(value: str) -> str:
    s = str(value or "").upper().strip()
    s = re.sub(r"[^A-Z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    for old, new in SUFFIX_MAP.items():
        s = s.replace(old, new)
    return s


def assign_duplicate_groups(df: pd.DataFrame, enable_weak_owner_key: bool = True) -> pd.DataFrame:
    out = ensure_canonical(df).copy()
    out["_address_norm"] = out.get("address", "").map(normalize_address)
    out["_apn_norm"] = out.get("apn", "").astype(str).str.upper().str.strip()
    owner_last = out.get("owner_last", pd.Series([""] * len(out), index=out.index))
    owner_mailing_address = out.get("owner_mailing_address", pd.Series([""] * len(out), index=out.index))
    out["_owner_key"] = (
        owner_last.astype(str).str.upper().str.strip()
        + "|"
        + owner_mailing_address.map(normalize_address)
    )

    out["duplicate_method"] = ""
    out["duplicate_group_id"] = ""

    apn_counts = out["_apn_norm"].value_counts()
    apn_dupes = out["_apn_norm"].isin(apn_counts[apn_counts > 1].index) & (out["_apn_norm"] != "")
    out.loc[apn_dupes, "duplicate_method"] = "apn_exact"
    out.loc[apn_dupes, "duplicate_group_id"] = "APN|" + out.loc[apn_dupes, "_apn_norm"]

    unresolved = out["duplicate_method"] == ""
    addr_counts = out.loc[unresolved, "_address_norm"].value_counts()
    addr_dupes = unresolved & out["_address_norm"].isin(addr_counts[addr_counts > 1].index) & (out["_address_norm"] != "")
    out.loc[addr_dupes, "duplicate_method"] = "address_norm"
    out.loc[addr_dupes, "duplicate_group_id"] = "ADDR|" + out.loc[addr_dupes, "_address_norm"]

    if enable_weak_owner_key:
        unresolved = out["duplicate_method"] == ""
        owner_counts = out.loc[unresolved, "_owner_key"].value_counts()
        owner_dupes = unresolved & out["_owner_key"].isin(owner_counts[owner_counts > 1].index) & (~out["_owner_key"].str.startswith("|"))
        out.loc[owner_dupes, "duplicate_method"] = "owner_mailing_weak"
        out.loc[owner_dupes, "duplicate_group_id"] = "OWN|" + out.loc[owner_dupes, "_owner_key"]

    out["is_duplicate"] = out["duplicate_method"] != ""
    return out


def dedupe_records(df: pd.DataFrame, strategy: str = "most_complete") -> pd.DataFrame:
    tagged = assign_duplicate_groups(df)
    non_dupes = tagged[~tagged["is_duplicate"]].copy()
    dupes = tagged[tagged["is_duplicate"]].copy()

    if dupes.empty:
        return tagged.drop(columns=["_address_norm", "_apn_norm", "_owner_key"], errors="ignore")

    if strategy == "most_complete":
        completeness = dupes.notna().sum(axis=1)
        dupes = dupes.assign(_completeness=completeness)
        best = (
            dupes.sort_values(["duplicate_group_id", "_completeness"], ascending=[True, False])
            .drop_duplicates(subset=["duplicate_group_id"], keep="first")
            .drop(columns=["_completeness"], errors="ignore")
        )
    else:
        best = dupes.drop_duplicates(subset=["duplicate_group_id"], keep="first")

    out = pd.concat([non_dupes, best], ignore_index=True)
    return out.drop(columns=["_address_norm", "_apn_norm", "_owner_key"], errors="ignore")
