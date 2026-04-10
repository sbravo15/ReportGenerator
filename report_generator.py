# report_generator.py - Generalized Seller Report with Visuals

import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# ---------------------------
# Generate charts and save them to 'assets/' folder
# ---------------------------
def generate_charts(df):
    os.makedirs("assets", exist_ok=True)

    df['Lot (Acres)'] = pd.to_numeric(df['Lot (Acres)'], errors='coerce')

    # 1. Lot Size Histogram
    plt.figure(figsize=(6, 4))
    sns.histplot(df['Lot (Acres)'].dropna(), bins=30, kde=False)
    plt.title("Lot Size Distribution (Acres)")
    plt.xlabel("Lot Size")
    plt.ylabel("Property Count")
    plt.tight_layout()
    plt.savefig("assets/lot_size_hist.png")
    plt.close()

    # 2. ZIP Distribution Bar Chart
    top_zips = df['Zip'].value_counts().head(10)
    plt.figure(figsize=(6, 4))
    top_zips.plot(kind='bar', color='skyblue')
    plt.title("Top ZIP Codes by Property Count")
    plt.ylabel("Property Count")
    plt.tight_layout()
    plt.savefig("assets/zip_distribution.png")
    plt.close()

    # 3. Absentee Owner Pie Chart
    if 'Owner Mailing State' in df.columns:
        absentee_counts = df['Owner Mailing State'].apply(
            lambda x: 'Out-of-State' if str(x).strip().upper() != 'FL' else 'In-State'
        ).value_counts()
        plt.figure(figsize=(4, 4))
        absentee_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140)
        plt.title("Absentee Owner Breakdown")
        plt.tight_layout()
        plt.savefig("assets/absentee_pie.png")
        plt.close()

# ---------------------------
# Generate PDF report using charts and insights
# ---------------------------
def generate_report(df):
    generate_charts(df)

    df['Lot (Acres)'] = pd.to_numeric(df['Lot (Acres)'], errors='coerce')
    df['Estimated Equity Percent'] = pd.to_numeric(df['Estimated Equity Percent'], errors='coerce')
    df['Ownership Length (Months)'] = pd.to_numeric(df['Ownership Length (Months)'], errors='coerce')

    lot_stats = {
        'Total Records': len(df),
        'Avg Lot Size': round(df['Lot (Acres)'].mean(), 2),
        'Median Lot Size': round(df['Lot (Acres)'].median(), 2),
        'Max Lot Size': round(df['Lot (Acres)'].max(), 2),
        'Min Lot Size': round(df['Lot (Acres)'].min(), 2),
        'Std Dev': round(df['Lot (Acres)'].std(), 2)
    }

    top_zips = df['Zip'].value_counts().head(5)

    absentee_count = None
    if 'Owner Mailing State' in df.columns:
        absentee_count = df[df['Owner Mailing State'].str.upper() != 'FL'].shape[0]

    report_date = datetime.today().strftime('%B %d, %Y')

    pdf = FPDF()
    pdf.add_page()

    # Title Section
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Vacant Land Seller Insights Report", ln=True, align="C")
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Generated on: {report_date}", ln=True, align="C")
    pdf.ln(10)

    # Lot Size Stats
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Lot Size Statistics", ln=True)
    pdf.set_font("Arial", '', 12)
    for k, v in lot_stats.items():
        pdf.cell(200, 8, txt=f"{k}: {v}", ln=True)
    pdf.ln(5)

    # Absentee Owner Stats
    if absentee_count is not None:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Absentee Owners", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 8, txt=f"Out-of-State Owners: {absentee_count} of {len(df)}", ln=True)
        pdf.image("assets/absentee_pie.png", x=30, w=150)
        pdf.ln(10)

    # ZIP Stats
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Top ZIP Codes", ln=True)
    pdf.set_font("Arial", '', 12)
    for zip_code, count in top_zips.items():
        pdf.cell(200, 8, txt=f"{zip_code}: {count} sellers", ln=True)
    pdf.image("assets/zip_distribution.png", x=20, w=170)
    pdf.ln(10)

    # Lot Size Chart
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Lot Size Distribution", ln=True)
    pdf.image("assets/lot_size_hist.png", x=20, w=170)

    # Save PDF
    report_path = "Vacant_Land_Seller_Report.pdf"
    pdf.output(report_path)
    return report_path
