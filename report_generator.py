from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
from fpdf import FPDF

from core import (
    active_buyers_by_zip,
    active_buyers_count,
    apply_buyer_name_search,
    ScoreConfig,
    SignalConfig,
    ViabilityConfig,
    assign_duplicate_groups,
    build_top_buyers,
    compute_buyer_buybox,
    compute_opportunity_score,
    compute_overlap_signals,
    compute_quality_summary,
    compute_viability_summary,
    dedupe_records,
    detect_quality_flags,
    filter_by_date_range,
    label_viability,
    normalize_buyer_records,
    normalize_propwire_df,
    top_buyer_profiles,
)


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Land Intelligence Report", ln=True)
        self.line(10, 20, 200, 20)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _safe(v, decimals=2):
    if pd.isna(v):
        return "n/a"
    if isinstance(v, (int, float)):
        return f"{v:,.{decimals}f}"
    return str(v)


def _add_metrics(pdf: ReportPDF, title: str, metrics: dict):
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, title, ln=True)
    pdf.set_font("Arial", "", 10)
    for k, v in metrics.items():
        pdf.cell(0, 6, f"- {k}: {_safe(v)}", ln=True)
    pdf.ln(2)


def _prepare(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    return normalize_propwire_df(df)


def _seller_report(pdf: ReportPDF, seller_df: pd.DataFrame, buyer_df: pd.DataFrame, signal_config: SignalConfig):
    flagged = detect_quality_flags(seller_df)
    tagged = assign_duplicate_groups(flagged)
    deduped = dedupe_records(tagged)

    quality_kpis, _ = compute_quality_summary(tagged)

    overlap = pd.DataFrame()
    buybox = pd.DataFrame()
    if not buyer_df.empty:
        overlap = compute_overlap_signals(deduped, buyer_df, signal_config)
        buybox = compute_buyer_buybox(buyer_df, ViabilityConfig())

    labeled = label_viability(deduped, overlap, buybox, ViabilityConfig())
    viability_kpis, reasons = compute_viability_summary(labeled)
    scored = compute_opportunity_score(labeled, ScoreConfig())
    top = scored[scored["viability_status"] == "VIABLE"].head(10)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Seller X-Ray Summary", ln=True)
    pdf.ln(1)

    _add_metrics(
        pdf,
        "List Health",
        {
            "Total Records": quality_kpis["total_records"],
            "Deduped Records": quality_kpis["deduped_records"],
            "Duplicate Rate": f"{quality_kpis['duplicate_rate'] * 100:.1f}%",
            "Missing ZIP Rate": f"{quality_kpis['missing_zip_rate'] * 100:.1f}%",
            "Missing Address/APN Rate": f"{quality_kpis['missing_address_or_apn_rate'] * 100:.1f}%",
            "Invalid Acres Rate": f"{quality_kpis['invalid_acres_rate'] * 100:.1f}%",
        },
    )

    _add_metrics(
        pdf,
        "Viability",
        {
            "Unviable": viability_kpis["unviable_count"],
            "Review": viability_kpis["review_count"],
            "Viable": viability_kpis["viable_count"],
            "Unviable Rate": f"{viability_kpis['unviable_rate'] * 100:.1f}%",
        },
    )

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Top Skip Trace First", ln=True)
    pdf.set_font("Arial", "", 10)
    if top.empty:
        pdf.cell(0, 6, "- No viable records available.", ln=True)
    else:
        for _, row in top.iterrows():
            pdf.cell(
                0,
                6,
                f"- {row.get('zip', '')} | acres={_safe(row.get('lot_acres'))} | score={_safe(row.get('opportunity_score'))} | {row.get('score_reason', '')}",
                ln=True,
            )

    if not reasons.empty:
        pdf.ln(2)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Top Viability Reasons", ln=True)
        pdf.set_font("Arial", "", 10)
        for _, row in reasons.head(8).iterrows():
            pdf.cell(0, 6, f"- {row['reason']}: {int(row['count'])}", ln=True)


def _buyer_report(
    pdf: ReportPDF,
    buyer_df: pd.DataFrame,
    date_range_label: str = "Last 24 months",
    buyer_name_query: str = "",
):
    buyer = normalize_buyer_records(buyer_df)
    buyer = filter_by_date_range(buyer, date_range_label)
    if buyer.empty:
        pdf.cell(0, 6, "No buyer data in selected range.", ln=True)
        return

    top_all = build_top_buyers(buyer)
    top_filtered = apply_buyer_name_search(top_all, buyer_name_query)
    active_count = active_buyers_count(top_all, min_deals=2)
    median_price = buyer["last_sale_amount"].median()

    # Page 1: Summary
    _add_metrics(
        pdf,
        "Buyer Prospecting Summary",
        {
            "Date Range": date_range_label,
            "Active Buyers (2+)": active_count,
            "Median Buy Price": median_price,
        },
    )
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Top 10 Buyers", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in top_filtered.head(10).iterrows():
        pdf.cell(
            0,
            6,
            f"- {row['buyer_name']}: lots={int(row['lots_bought'])}, last_buy={row['last_buy_date']}, avg_acres={_safe(row['avg_acres'])}, median_price={_safe(row['median_price'])}",
            ln=True,
        )

    # Page 2: Active buyers by ZIP
    zip_table = active_buyers_by_zip(buyer, min_deals=2)
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Active Buyers by ZIP", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in zip_table.head(25).iterrows():
        pdf.cell(
            0,
            6,
            f"- {row['zip']}: active_buyers={int(row['active_buyers'])}, total_deals={int(row['total_deals'])}, median_acres={_safe(row['median_acres'])}, median_price={_safe(row['median_price'])}",
            ln=True,
        )

    # Page 3+: Top 5 buyer profiles
    for profile in top_buyer_profiles(buyer, top_n_buyers=5, txns_per_buyer=10):
        pdf.add_page()
        summary = profile["summary"]
        name = profile["buyer_name"]
        _add_metrics(
            pdf,
            f"Buyer Profile: {name}",
            {
                "Lots Bought": summary["lots_bought"],
                "Last Buy Date": summary["last_buy_date"],
                "Avg Acres": summary["avg_acres"],
                "Median Acres": summary["median_acres"],
                "Avg Price": summary["avg_price"],
                "Median Price": summary["median_price"],
            },
        )
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "Last 10 Transactions", ln=True)
        pdf.set_font("Arial", "", 9)
        txns = profile["transactions"]
        if txns.empty:
            pdf.cell(0, 6, "- No transactions.", ln=True)
        else:
            for _, tx in txns.iterrows():
                pdf.cell(
                    0,
                    6,
                    f"- {tx.get('date', 'n/a')} | {tx.get('address_or_apn', '')} | zip={tx.get('zip', '')} | acres={_safe(tx.get('acres'))} | price={_safe(tx.get('price'))}",
                    ln=True,
                )


def _comparison_report(pdf: ReportPDF, seller_df: pd.DataFrame, buyer_df: pd.DataFrame, signal_config: SignalConfig):
    overlap = compute_overlap_signals(seller_df, buyer_df, signal_config)
    if overlap.empty:
        pdf.cell(0, 6, "No overlapping ZIPs.", ln=True)
        return

    rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    focus = overlap.copy()
    focus["tier_rank"] = focus["demand_tier"].map(rank).fillna(0)
    focus = focus.sort_values(["tier_rank", "heat_index", "buyer_count", "seller_fit_rate"], ascending=False)

    _add_metrics(
        pdf,
        "Comparison Summary",
        {
            "Overlapping ZIPs": len(focus),
            "Top ZIP": focus.iloc[0]["zip"],
            "Avg Demand/Supply": focus["demand_supply_ratio"].mean(),
            "Heat Formula": "(buyer_count*buyer_weight)+(min(ratio,cap)*ratio_weight)",
        },
    )

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Recommended Focus ZIPs", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in focus.head(12).iterrows():
        pdf.cell(
            0,
            6,
            f"- {row['zip']}: tier={row['demand_tier']}, buyers={int(row['buyer_count'])}, sellers={int(row['seller_count'])}, ratio={row['demand_supply_ratio']:.2f}, heat={row['heat_index']:.2f}",
            ln=True,
        )
        pdf.cell(0, 6, f"  action={row['action']} | reason={row['action_reason']}", ln=True)


def generate_report(
    report_type: str,
    seller_df: pd.DataFrame | None = None,
    buyer_df: pd.DataFrame | None = None,
    signal_config: SignalConfig | None = None,
    buyer_date_range_label: str = "Last 24 months",
    buyer_name_query: str = "",
):
    now = datetime.today().strftime("%B %d, %Y")
    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Generated on: {now}", ln=True)
    pdf.ln(2)

    seller = _prepare(seller_df)
    buyer = _prepare(buyer_df)
    cfg = signal_config or SignalConfig()

    if report_type == "seller":
        _seller_report(pdf, seller, buyer, cfg)
        path = "Vacant_Land_Seller_Report.pdf"
    elif report_type == "buyer":
        _buyer_report(pdf, buyer, date_range_label=buyer_date_range_label, buyer_name_query=buyer_name_query)
        path = "Vacant_Land_Buyer_Report.pdf"
    else:
        _comparison_report(pdf, seller, buyer, cfg)
        path = "Vacant_Land_Market_Comparison_Report.pdf"

    pdf.output(path)
    return path
