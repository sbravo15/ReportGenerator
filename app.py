# app.py - Enhanced Interactive Streamlit GUI for Seller Report Generator

import streamlit as st
import pandas as pd
from report_generator import generate_report

st.set_page_config(page_title="📋 Vacant Land Seller Report Generator", layout="wide")

st.title("📋 Vacant Land List - Seller Report")

# Upload CSV file
uploaded_file = st.file_uploader("Upload Propwire CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File successfully loaded!")

    # Display preview
    st.subheader("📑 Preview of Uploaded Data")
    st.dataframe(df.head())

    # Show dataset overview
    st.subheader("🔍 Dataset Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Records", len(df))
        if 'Zip' in df.columns:
            st.metric("Unique ZIP Codes", df['Zip'].nunique())
        if 'Lot (Acres)' in df.columns:
            st.metric("Avg Lot Size (Acres)", round(pd.to_numeric(df['Lot (Acres)'], errors='coerce').mean(), 2))
    with col2:
        if 'Owner Mailing State' in df.columns:
            out_of_state = df[df['Owner Mailing State'].str.upper() != 'FL'].shape[0]
            st.metric("Out-of-State Owners", out_of_state)
        if 'Estimated Equity Percent' in df.columns:
            high_equity = df[pd.to_numeric(df['Estimated Equity Percent'], errors='coerce') > 70].shape[0]
            st.metric("High Equity Leads (>70%)", high_equity)

    # Report generation trigger
    if st.button("Generate PDF Report"):
        with st.spinner("Generating visual report PDF..."):
            report_path = generate_report(df)
        st.success("✅ Report Ready!")
        st.download_button("📥 Download Report", open(report_path, "rb"), file_name="Vacant_Land_Seller_Report.pdf")

else:
    st.info("Upload a CSV file to begin analysis.")
    st.warning("Please upload a CSV file to generate the report.")