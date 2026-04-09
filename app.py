from __future__ import annotations

import io

import altair as alt
import pandas as pd
import streamlit as st

from core import (
    ActionConfig,
    DATE_RANGE_MONTHS,
    DemandTierConfig,
    ScoreConfig,
    SignalConfig,
    ViabilityConfig,
    BUCKET_ORDER,
    add_lot_size_class,
    active_buyers_count,
    apply_size_preset,
    apply_buyer_name_search,
    assign_duplicate_groups,
    build_export_frames,
    build_working_dataset,
    build_top_buyers,
    buyer_summary,
    buyer_transactions,
    buyer_zip_breakdown,
    compute_duplicate_metrics,
    compute_buyer_buybox,
    compute_opportunity_score,
    compute_overlap_signals,
    compute_quality_summary,
    compute_viability_summary,
    dedupe_records,
    lot_bucket_counts,
    detect_quality_flags,
    filter_by_date_range,
    label_viability,
    normalize_buyer_records,
    normalize_propwire_df,
)
from report_generator import generate_report


st.set_page_config(page_title="Land Intelligence Console", layout="wide")

if "buyer_report_bytes" not in st.session_state:
    st.session_state["buyer_report_bytes"] = None
if "buyer_report_name" not in st.session_state:
    st.session_state["buyer_report_name"] = "Vacant_Land_Buyer_Report.pdf"


@st.cache_data
def read_csv_cached(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(file_bytes))


@st.cache_data
def normalize_df_cached(file_bytes: bytes) -> pd.DataFrame:
    raw = read_csv_cached(file_bytes)
    return normalize_propwire_df(raw)


@st.cache_data
def quality_stage(df: pd.DataFrame) -> pd.DataFrame:
    return detect_quality_flags(df)


@st.cache_data
def duplicate_stage(df: pd.DataFrame) -> pd.DataFrame:
    return assign_duplicate_groups(df)


@st.cache_data
def dedupe_stage(df: pd.DataFrame) -> pd.DataFrame:
    return dedupe_records(df)



def apply_filters(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    out = df.copy()
    st.sidebar.markdown(f"### {prefix} Filters")

    if "zip" in out.columns:
        zip_values = sorted([z for z in out["zip"].dropna().astype(str).unique() if z])
        zips = st.sidebar.multiselect(f"{prefix} ZIP", zip_values, key=f"{prefix}_zip")
        if zips:
            out = out[out["zip"].isin(zips)]

    if "lot_acres" in out.columns and out["lot_acres"].notna().any():
        min_a = float(out["lot_acres"].min())
        max_a = float(out["lot_acres"].max())
        if min_a < max_a:
            lo, hi = st.sidebar.slider(
                f"{prefix} Lot Acres",
                min_value=min_a,
                max_value=max_a,
                value=(min_a, max_a),
                key=f"{prefix}_lot",
            )
            out = out[(out["lot_acres"] >= lo) & (out["lot_acres"] <= hi)]

    return out


def render_buyer_view(buyer_df: pd.DataFrame):
    if buyer_df.empty:
        st.info("Upload a buyer list to view buyer intelligence.")
        return

    buyer = normalize_buyer_records(buyer_df)

    controls_col1, controls_col2 = st.columns([1, 2])
    with controls_col1:
        date_range = st.selectbox(
            "Date range",
            list(DATE_RANGE_MONTHS.keys()),
            index=1,
            key="buyer_date_range",
        )
    with controls_col2:
        buyer_query = st.text_input(
            "Buyer name search",
            value=st.session_state.get("buyer_name_query", ""),
            key="buyer_name_query",
            placeholder="Search buyer name...",
        )

    filtered_buyer = filter_by_date_range(buyer, date_range)
    top_buyers_all = build_top_buyers(filtered_buyer)
    top_buyers = apply_buyer_name_search(top_buyers_all, buyer_query).sort_values("lots_bought", ascending=False)
    active_buyers = active_buyers_count(top_buyers_all, min_deals=2)

    st.metric("Active Buyers (2+ deals)", active_buyers)

    st.subheader("Top Buyers")
    left, right = st.columns([2.2, 1.2])

    selected_buyer_name = None
    with left:
        table_df = top_buyers[
            ["buyer_name", "lots_bought", "last_buy_date", "avg_acres", "median_acres", "avg_price", "median_price"]
        ].head(250)
        selection_supported = True
        try:
            selection = st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="buyer_top_buyers_table",
            )
            rows = selection.selection.get("rows", []) if selection is not None else []
            if rows:
                selected_buyer_name = str(table_df.iloc[rows[0]]["buyer_name"])
        except TypeError:
            selection_supported = False
            st.dataframe(table_df, use_container_width=True, hide_index=True)

        if not selection_supported:
            buyer_options = table_df["buyer_name"].tolist()
            selected_buyer_name = st.selectbox(
                "Select buyer for details",
                buyer_options if buyer_options else [""],
                key="buyer_details_select_fallback",
            )

    with right:
        st.markdown("#### Buyer Details")
        if not selected_buyer_name and not top_buyers.empty:
            selected_buyer_name = str(top_buyers.iloc[0]["buyer_name"])

        if selected_buyer_name:
            summary = buyer_summary(filtered_buyer, selected_buyer_name)
            m1, m2 = st.columns(2)
            m1.metric("Lots bought", int(summary["lots_bought"]))
            m2.metric("Last buy date", summary["last_buy_date"])
            m3, m4 = st.columns(2)
            m3.metric("Avg acres", "n/a" if pd.isna(summary["avg_acres"]) else f"{summary['avg_acres']:.2f}")
            m4.metric("Median acres", "n/a" if pd.isna(summary["median_acres"]) else f"{summary['median_acres']:.2f}")
            m5, m6 = st.columns(2)
            m5.metric("Avg price", "n/a" if pd.isna(summary["avg_price"]) else f"${summary['avg_price']:,.0f}")
            m6.metric("Median price", "n/a" if pd.isna(summary["median_price"]) else f"${summary['median_price']:,.0f}")

            zip_break = buyer_zip_breakdown(filtered_buyer, selected_buyer_name)
            st.markdown("ZIP breakdown")
            st.dataframe(zip_break, use_container_width=True, hide_index=True)

            zip_options = ["All"] + zip_break["zip"].dropna().astype(str).tolist()
            drawer_zip = st.selectbox("Transactions ZIP filter", zip_options, key="buyer_drawer_zip_filter")
            tx = buyer_transactions(filtered_buyer, selected_buyer_name, zip_filter=drawer_zip)
            st.markdown("Transactions")
            st.dataframe(tx, use_container_width=True, hide_index=True)

    st.session_state["buyer_view_filtered_df"] = filtered_buyer
    st.session_state["buyer_view_date_range"] = date_range
    st.session_state["buyer_view_name_query"] = buyer_query

    if st.button("Download report", key="buyer_download_report_btn"):
        report_path = generate_report(
            "buyer",
            buyer_df=filtered_buyer,
            buyer_date_range_label=date_range,
            buyer_name_query=buyer_query,
        )
        with open(report_path, "rb") as f:
            st.session_state["buyer_report_bytes"] = f.read()
        st.session_state["buyer_report_name"] = report_path

    if st.session_state.get("buyer_report_bytes"):
        st.download_button(
            "Download Buyer Report PDF",
            data=st.session_state["buyer_report_bytes"],
            file_name=st.session_state.get("buyer_report_name", "Vacant_Land_Buyer_Report.pdf"),
            mime="application/pdf",
            key="buyer_download_report_pdf",
        )


def render_comparison(seller_df: pd.DataFrame, buyer_df: pd.DataFrame):
    st.subheader("Comparison")
    if seller_df.empty or buyer_df.empty:
        st.info("Upload both seller and buyer lists to run comparison.")
        return pd.DataFrame()

    st.sidebar.markdown("### Comparison Controls")
    buyer_weight = st.sidebar.number_input("Buyer weight", value=1.3, step=0.1)
    ratio_weight = st.sidebar.number_input("Ratio weight", value=10.0, step=0.5)
    ratio_cap = st.sidebar.number_input("Ratio cap", value=5.0, step=0.5)

    high_pct = st.sidebar.slider("High tier percentile", 0.50, 0.95, 0.80, 0.01)
    low_pct = st.sidebar.slider("Low tier percentile", 0.05, 0.50, 0.20, 0.01)
    high_floor = st.sidebar.number_input("High tier buyer floor", min_value=1, value=5)
    med_min = st.sidebar.number_input("Medium buyer min", min_value=1, value=2)
    med_max = st.sidebar.number_input("Medium buyer max", min_value=1, value=4)

    fit_x = st.sidebar.slider("Fit threshold X", 0.05, 1.0, 0.35, 0.01)
    seller_s = st.sidebar.number_input("Seller floor S", min_value=1, value=25)

    cfg = SignalConfig(
        buyer_weight=float(buyer_weight),
        ratio_weight=float(ratio_weight),
        ratio_cap=float(ratio_cap),
        demand_tier=DemandTierConfig(
            high_percentile=float(high_pct),
            low_percentile=float(low_pct),
            high_buyer_floor=int(high_floor),
            medium_buyer_min=int(med_min),
            medium_buyer_max=int(med_max),
        ),
        action=ActionConfig(fit_threshold=float(fit_x), seller_floor=int(seller_s)),
    )

    overlap = compute_overlap_signals(seller_df, buyer_df, cfg)
    st.session_state["comparison_signal_config"] = cfg

    if overlap.empty:
        st.warning("No overlapping ZIPs.")
        return overlap

    st.caption(
        "Formula: demand_supply_ratio = buyer_count / max(seller_count,1); "
        "heat_index = (buyer_count * buyer_weight) + (min(demand_supply_ratio, ratio_cap) * ratio_weight)."
    )

    rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    focus = overlap.copy()
    focus["tier_rank"] = focus["demand_tier"].map(rank).fillna(0)
    focus = focus.sort_values(["tier_rank", "heat_index", "buyer_count", "seller_fit_rate"], ascending=False)

    c1, c2, c3 = st.columns(3)
    c1.metric("Overlapping ZIPs", len(focus))
    c2.metric("Top ZIP", str(focus.iloc[0]["zip"]))
    c3.metric("Avg Ratio", f"{focus['demand_supply_ratio'].mean():.2f}")

    st.subheader("Recommended Focus ZIPs")
    st.dataframe(
        focus[
            [
                "zip",
                "seller_count",
                "buyer_count",
                "demand_supply_ratio",
                "heat_index",
                "demand_tier",
                "tier_reason",
                "seller_fit_rate",
                "action",
                "action_reason",
            ]
        ],
        use_container_width=True,
    )

    top = focus.head(15)
    bars = top.melt(
        id_vars=["zip", "demand_tier", "demand_supply_ratio", "heat_index"],
        value_vars=["seller_count", "buyer_count"],
        var_name="series",
        value_name="count",
    )
    bars["series"] = bars["series"].replace({"seller_count": "Seller", "buyer_count": "Buyer"})

    tier_scale = alt.Scale(domain=["HIGH", "MEDIUM", "LOW"], range=["#12733d", "#de9f00", "#b42318"])
    bar_chart = (
        alt.Chart(bars)
        .mark_bar()
        .encode(
            x=alt.X("zip:N", title="ZIP"),
            y=alt.Y("count:Q", title="Count"),
            xOffset="series:N",
            color=alt.Color("demand_tier:N", scale=tier_scale, title="Demand Tier"),
            tooltip=["zip", "series", "count", alt.Tooltip("demand_supply_ratio:Q", format=".2f"), alt.Tooltip("heat_index:Q", format=".2f")],
        )
        .properties(height=300)
    )
    st.altair_chart(bar_chart, use_container_width=True)

    y_axis = st.radio("Quadrant Y", ["seller_count", "seller_fit_rate"], horizontal=True)
    scatter = (
        alt.Chart(top)
        .mark_circle(opacity=0.85)
        .encode(
            x=alt.X("buyer_count:Q", title="Buyer Count"),
            y=alt.Y(f"{y_axis}:Q", title="Seller Count" if y_axis == "seller_count" else "Seller Fit Rate"),
            size=alt.Size("heat_index:Q", title="Heat Index"),
            color=alt.Color("demand_tier:N", scale=tier_scale),
            tooltip=["zip", "buyer_count", "seller_count", alt.Tooltip("seller_fit_rate:Q", format=".2f"), alt.Tooltip("heat_index:Q", format=".2f")],
        )
        .properties(height=300, title="Opportunity Quadrants")
    )
    st.altair_chart(scatter, use_container_width=True)

    return overlap


def _pct(value: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{(value / total) * 100:.1f}%"


def _seller_fingerprint(df: pd.DataFrame) -> tuple:
    if df.empty:
        return (0, "")
    key_col = "record_id" if "record_id" in df.columns else df.columns[0]
    sample = "|".join(df[key_col].astype(str).head(200).tolist())
    return (len(df), hash(sample))


def render_seller_xray(seller_df: pd.DataFrame, buyer_df: pd.DataFrame, overlap_cfg: SignalConfig):
    st.subheader("Seller X-Ray (Pre-Skip Trace)")
    if seller_df.empty:
        st.info("Upload seller data to run Seller X-Ray.")
        return

    flagged = quality_stage(seller_df)
    tagged = duplicate_stage(flagged)
    deduped = dedupe_stage(tagged)

    # Core working controls
    c1, c2, c3 = st.columns([1, 1, 1.2])
    with c1:
        use_deduped = st.toggle("Deduped dataset", value=True, key="seller_use_deduped")
    with c2:
        remove_on_market = st.toggle("Off-market only", value=True, key="seller_off_market_only")
    with c3:
        size_preset = st.selectbox(
            "Size preset",
            [
                "All",
                "UNVIABLE (<0.12)",
                "INFILL (0.12-0.30)",
                "LARGE_LOT (>0.30-0.50)",
                "BIG_LOT (>0.50-1.0)",
                "MINI_TRACT (>1.0-5.0)",
                "XL (5+)",
                "UNKNOWN",
            ],
            index=0,
            key="seller_size_preset",
        )

    working = build_working_dataset(
        tagged_df=tagged,
        deduped_df=deduped,
        use_deduped=use_deduped,
        off_market_only=remove_on_market,
        size_preset=size_preset,
    )

    # SECTION C: VIABILITY ENGINE
    min_acres = st.sidebar.number_input("Min target acres", min_value=0.0, value=0.12, step=0.05)
    max_acres = st.sidebar.number_input("Max target acres", min_value=0.1, value=2.00, step=0.10)
    buyer_floor = st.sidebar.number_input("Buyer floor per ZIP", min_value=0, value=2)
    min_buybox_n = st.sidebar.number_input("Buybox min sample", min_value=1, value=10)
    low_demand_status = st.sidebar.selectbox("Low demand status", ["REVIEW", "UNVIABLE"], index=0)

    viability_cfg = ViabilityConfig(
        min_acres=float(min_acres),
        max_acres=float(max_acres),
        min_buybox_sample=int(min_buybox_n),
        buyer_floor=int(buyer_floor),
        low_demand_status=str(low_demand_status),
    )
    calc_signature = (
        _seller_fingerprint(working),
        _seller_fingerprint(buyer_df),
        min_acres,
        max_acres,
        buyer_floor,
        min_buybox_n,
        low_demand_status,
    )
    seller_cache = st.session_state.get("seller_xray_cache", {})
    if seller_cache.get("signature") == calc_signature:
        overlap = seller_cache["overlap"]
        buybox = seller_cache["buybox"]
        viable_labeled = seller_cache["viable_labeled"]
        scored = seller_cache["scored"]
    else:
        overlap = pd.DataFrame()
        buybox = pd.DataFrame(columns=["zip", "p25", "p75", "n", "source"])
        if not buyer_df.empty:
            overlap = compute_overlap_signals(working, buyer_df, overlap_cfg)
            buybox = compute_buyer_buybox(buyer_df, viability_cfg)

        viable_labeled = label_viability(working, overlap, buybox, viability_cfg)
        viable_labeled = add_lot_size_class(viable_labeled)
        scored = compute_opportunity_score(viable_labeled, ScoreConfig())
        st.session_state["seller_xray_cache"] = {
            "signature": calc_signature,
            "overlap": overlap,
            "buybox": buybox,
            "viable_labeled": viable_labeled,
            "scored": scored,
        }

    # SECTION A + B Executive Strip (always visible)
    quality_kpis, issues = compute_quality_summary(tagged)
    dup_groups = (
        tagged[tagged["is_duplicate"]]
        .groupby(["duplicate_group_id", "duplicate_method"], dropna=False)
        .size()
        .rename("group_size")
        .reset_index()
        .sort_values("group_size", ascending=False)
    )
    dup_metrics = compute_duplicate_metrics(tagged, total_records=int(quality_kpis["total_records"]))
    total_records = int(dup_metrics["total_uploaded"])
    duplicate_rows_raw = int(dup_metrics["duplicate_rows_raw"])
    deduped_records = int(dup_metrics["deduped_records"])
    duplicate_groups = int(dup_metrics["duplicate_groups"])
    largest_group = int(dup_metrics["largest_duplicate_group_size"])
    duplicate_rate_pct = float(dup_metrics["duplicate_rate_pct"])

    st.markdown("### A) List Health  |  B) Duplicates")
    r1 = st.columns(4)
    r1[0].metric("Total Uploaded", total_records)
    r1[1].metric("Duplicate Rows (Raw)", duplicate_rows_raw)
    r1[2].metric("Deduped Records", deduped_records)
    r1[3].metric("Duplicate Rate", f"{duplicate_rate_pct:.1f}%")

    # Lot size intelligence row (working denominator)
    working_rows = int(len(viable_labeled))
    bucket_order = ["UNVIABLE", "INFILL", "LARGE_LOT", "BIG_LOT", "MINI_TRACT", "XL", "UNKNOWN"]
    bucket_labels = {
        "UNVIABLE": "UNVIABLE (<0.12)",
        "INFILL": "INFILL (0.12-0.30)",
        "LARGE_LOT": "LARGE_LOT (>0.30-0.50)",
        "BIG_LOT": "BIG_LOT (>0.50-1.0)",
        "MINI_TRACT": "MINI_TRACT (>1.0-5.0)",
        "XL": "XL (5+)",
        "UNKNOWN": "UNKNOWN",
    }
    bucket_counts = lot_bucket_counts(viable_labeled)
    st.markdown("### Lot Size Intelligence")
    r2 = st.columns(len(bucket_order))
    for i, bucket in enumerate(bucket_order):
        count = int(bucket_counts.get(bucket, 0))
        r2[i].metric(bucket_labels[bucket], f"{count} ({_pct(count, working_rows)})")

    st.caption(
        f"Working Lens: Deduped {'ON' if use_deduped else 'OFF'} | Off-market {'ON' if remove_on_market else 'OFF'} | "
        f"Size preset: {size_preset} | Working rows: {working_rows}"
    )

    # Critical seller signals (based on current working lens)
    mail_state = viable_labeled.get("owner_mailing_state", pd.Series([""] * len(viable_labeled), index=viable_labeled.index))
    prop_state = viable_labeled.get("state", pd.Series([""] * len(viable_labeled), index=viable_labeled.index))
    absentee_mask = (
        mail_state.fillna("").astype(str).str.upper().str.strip() != prop_state.fillna("").astype(str).str.upper().str.strip()
    ) & mail_state.fillna("").astype(str).str.strip().ne("")
    absentee_count = int(absentee_mask.sum())

    eq_series = pd.to_numeric(
        viable_labeled.get("estimated_equity_percent", pd.Series([None] * len(viable_labeled), index=viable_labeled.index)),
        errors="coerce",
    )
    high_equity_mask = eq_series >= 60
    high_equity_count = int(high_equity_mask.fillna(False).sum())

    default_amt = pd.to_numeric(
        viable_labeled.get("default_amount", pd.Series([0] * len(viable_labeled), index=viable_labeled.index)),
        errors="coerce",
    ).fillna(0)
    auction_dt = pd.to_datetime(
        viable_labeled.get("auction_date", pd.Series([None] * len(viable_labeled), index=viable_labeled.index)),
        errors="coerce",
    )
    distress_mask = (default_amt > 0) | auction_dt.notna()
    distress_count = int(distress_mask.sum())

    company_mask = (
        viable_labeled.get("owner_type", pd.Series([""] * len(viable_labeled), index=viable_labeled.index))
        .fillna("")
        .astype(str)
        .str.upper()
        .str.contains("COMPANY|INVESTOR|LLC|CORP", regex=True)
    )
    company_count = int(company_mask.sum())

    st.markdown("### Critical Signals")
    sig_cols = st.columns(4)
    sig_cols[0].metric("Absentee Owners", f"{absentee_count} ({_pct(absentee_count, working_rows)})")
    sig_cols[1].metric("High Equity (>=60%)", f"{high_equity_count} ({_pct(high_equity_count, working_rows)})")
    sig_cols[2].metric("Distress Flags", f"{distress_count} ({_pct(distress_count, working_rows)})")
    sig_cols[3].metric("Company/Investor Owners", f"{company_count} ({_pct(company_count, working_rows)})")

    # Primary chart (always visible)
    bucket_chart_df = pd.DataFrame(
        {
            "bucket": ["UNVIABLE", "INFILL", "LARGE_LOT", "BIG_LOT", "MINI_TRACT", "XL", "UNKNOWN"],
            "count": [
                int(bucket_counts.get("UNVIABLE", 0)),
                int(bucket_counts.get("INFILL", 0)),
                int(bucket_counts.get("LARGE_LOT", 0)),
                int(bucket_counts.get("BIG_LOT", 0)),
                int(bucket_counts.get("MINI_TRACT", 0)),
                int(bucket_counts.get("XL", 0)),
                int(bucket_counts.get("UNKNOWN", 0)),
            ],
        }
    )
    st.bar_chart(bucket_chart_df.set_index("bucket")["count"])

    # C + D calculations
    viability_kpis, reasons = compute_viability_summary(viable_labeled)

    tabs = st.tabs(["Overview", "Cleaning Details", "Size Breakdown", "Records Preview"])

    with tabs[0]:
        st.markdown("### C) Viability Engine  |  D) Action Plan")
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Unviable lots", f"{viability_kpis['unviable_count']} ({viability_kpis['unviable_rate'] * 100:.1f}%)")
        v2.metric("Review", viability_kpis["review_count"])
        v3.metric("Viable", viability_kpis["viable_count"])
        v4.metric("Working records", len(viable_labeled))

        funnel_df = pd.DataFrame(
            {
                "stage": ["Uploaded", "After Dedupe", "After Working Lens"],
                "rows": [total_records, deduped_records if use_deduped else total_records, working_rows],
            }
        )
        funnel_df["stage"] = pd.Categorical(
            funnel_df["stage"],
            categories=["Uploaded", "After Dedupe", "After Working Lens"],
            ordered=True,
        )
        funnel_df = funnel_df.sort_values("stage")
        removed_dupes = max(total_records - (deduped_records if use_deduped else total_records), 0)
        removed_lens = max((deduped_records if use_deduped else total_records) - working_rows, 0)
        st.caption(
            f"Flow: Uploaded -> After Dedupe -> After Working Lens | "
            f"Removed by dedupe: {removed_dupes} | Removed by working lens: {removed_lens}"
        )
        st.bar_chart(funnel_df.set_index("stage")["rows"])

    with tabs[1]:
        with st.expander("List Health Issues (recommended fixes)", expanded=False):
            st.dataframe(issues.head(200), use_container_width=True)

        with st.expander("Duplicate Groups (Top 25)", expanded=False):
            st.dataframe(dup_groups.head(25), use_container_width=True)

        with st.expander("Missing critical fields", expanded=False):
            missing_tbl = pd.DataFrame(
                [
                    {"field": "missing_zip", "count": int(flagged["missing_zip"].sum()) if "missing_zip" in flagged.columns else 0},
                    {
                        "field": "missing_address_and_apn",
                        "count": int(flagged["missing_address_and_apn"].sum()) if "missing_address_and_apn" in flagged.columns else 0,
                    },
                    {"field": "invalid_acres", "count": int(flagged["invalid_acres"].sum()) if "invalid_acres" in flagged.columns else 0},
                ]
            )
            st.dataframe(missing_tbl, use_container_width=True, hide_index=True)

    with tabs[2]:
        bucket_table = pd.DataFrame(
            {
                "bucket_name": ["UNVIABLE", "INFILL", "LARGE_LOT", "BIG_LOT", "MINI_TRACT", "XL", "UNKNOWN"],
                "count": [
                    int(bucket_counts.get("UNVIABLE", 0)),
                    int(bucket_counts.get("INFILL", 0)),
                    int(bucket_counts.get("LARGE_LOT", 0)),
                    int(bucket_counts.get("BIG_LOT", 0)),
                    int(bucket_counts.get("MINI_TRACT", 0)),
                    int(bucket_counts.get("XL", 0)),
                    int(bucket_counts.get("UNKNOWN", 0)),
                ],
            }
        )
        bucket_table["percent_of_working"] = bucket_table["count"].apply(lambda x: _pct(int(x), working_rows))
        st.dataframe(bucket_table, use_container_width=True, hide_index=True)

        if "zip" in viable_labeled.columns:
            zip_small = (
                viable_labeled.groupby("zip", dropna=False)
                .agg(rows=("zip", "size"), median_acres=("lot_acres", "median"))
                .reset_index()
                .sort_values("rows", ascending=False)
                .head(25)
            )
            st.dataframe(zip_small, use_container_width=True, hide_index=True)

    with tabs[3]:
        preview = viable_labeled.copy()
        size_filter_opt = st.selectbox(
            "Lot_Size_Class filter",
            ["All", "UNVIABLE", "INFILL", "LARGE_LOT", "BIG_LOT", "MINI_TRACT", "XL", "UNKNOWN"],
            index=0,
            key="seller_preview_size_filter",
        )
        if size_filter_opt != "All" and "lot_size_class" in preview.columns:
            preview = preview[preview["lot_size_class"] == size_filter_opt]

        viability_options = ["All"]
        if "viability_status" in preview.columns:
            viability_options += sorted([v for v in preview["viability_status"].dropna().astype(str).unique().tolist()])
        viability_filter = st.selectbox("viability_status filter", viability_options, index=0, key="seller_preview_viability_filter")
        if viability_filter != "All" and "viability_status" in preview.columns:
            preview = preview[preview["viability_status"] == viability_filter]

        preview_cap = preview.head(200)
        st.dataframe(preview_cap, use_container_width=True)
        if len(preview) > 200:
            st.caption(f"Preview capped at 200 of {len(preview)} rows.")

    # Consolidated exports (max 2 buttons)
    st.markdown("### Exports")
    clean_outreach, review_file = build_export_frames(
        tagged_df=tagged,
        deduped_df=deduped,
        viable_labeled_df=viable_labeled,
        scored_df=scored,
        use_deduped=use_deduped,
        off_market_only=remove_on_market,
    )

    st.download_button(
        "Download Clean Outreach List (CSV)",
        clean_outreach.to_csv(index=False).encode("utf-8"),
        "clean_outreach_list.csv",
        "text/csv",
    )
    st.download_button(
        "Download Review File (CSV)",
        review_file.to_csv(index=False).encode("utf-8"),
        "seller_review_file.csv",
        "text/csv",
    )

    return viable_labeled


st.title("Land Intelligence Console")
st.caption("Pre-skip trace Seller X-Ray + demand-aware wholesaling decisions.")

seller_file = st.file_uploader("Upload Seller CSV", type="csv", key="seller_file")
buyer_file = st.file_uploader("Upload Buyer CSV", type="csv", key="buyer_file")

seller_df = pd.DataFrame()
buyer_df = pd.DataFrame()
if seller_file is not None:
    seller_df = normalize_df_cached(seller_file.getvalue())
if buyer_file is not None:
    buyer_df = normalize_df_cached(buyer_file.getvalue())

if not seller_df.empty:
    seller_df = apply_filters(seller_df, "Seller")
if not buyer_df.empty:
    buyer_df = apply_filters(buyer_df, "Buyer")

signal_cfg = SignalConfig()

seller_tab, buyer_tab, comparison_tab = st.tabs(["Seller View", "Buyer View", "Comparison"])

with seller_tab:
    seller_scored = render_seller_xray(seller_df, buyer_df, signal_cfg)

with buyer_tab:
    render_buyer_view(buyer_df)

with comparison_tab:
    overlap_df = render_comparison(seller_df, buyer_df)

st.markdown("---")
st.subheader("Reports")
report_mode = st.radio("Report Type", ["seller", "buyer", "comparison"], horizontal=True)
if st.button("Generate PDF Report"):
    buyer_report_df = st.session_state.get("buyer_view_filtered_df", buyer_df)
    path = generate_report(
        report_mode,
        seller_df=seller_df if not seller_df.empty else None,
        buyer_df=buyer_report_df if isinstance(buyer_report_df, pd.DataFrame) and not buyer_report_df.empty else None,
        signal_config=st.session_state.get("comparison_signal_config", signal_cfg),
        buyer_date_range_label=st.session_state.get("buyer_view_date_range", "Last 24 months"),
        buyer_name_query=st.session_state.get("buyer_view_name_query", ""),
    )
    with open(path, "rb") as f:
        st.download_button("Download PDF Report", f.read(), file_name=path, mime="application/pdf")
