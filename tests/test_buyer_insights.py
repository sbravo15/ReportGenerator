import pandas as pd

from core.buyer_insights import (
    active_buyers_by_zip,
    active_buyers_count,
    build_top_buyers,
    filter_by_date_range,
    normalize_buyer_records,
)


def test_buyer_normalization_and_active_counts():
    df = pd.DataFrame(
        {
            "Owner 1 First Name": [" Acme ", "Acme", "Jane"],
            "Owner 1 Last Name": [" l l c ", "LLC", "Doe"],
            "Zip": ["33981.0", "33981-1234", "33980"],
            "Last Sale Date": ["2025-01-01", "2025-06-01", "2020-01-01"],
            "Lot (Acres)": [0.2, 0.3, 1.0],
            "Last Sale Amount": [100000, 110000, 50000],
        }
    )

    out = normalize_buyer_records(df)
    assert out.loc[0, "buyer_name"] == "ACME LLC"
    assert out.loc[1, "zip"] == "33981"

    recent = filter_by_date_range(out, "Last 24 months")
    top = build_top_buyers(recent)
    assert active_buyers_count(top, min_deals=2) == 1

    zip_table = active_buyers_by_zip(recent, min_deals=2)
    row = zip_table[zip_table["zip"] == "33981"].iloc[0]
    assert int(row["active_buyers"]) == 1
