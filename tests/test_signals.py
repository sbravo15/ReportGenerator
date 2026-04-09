import pandas as pd

from core import SignalConfig, compute_overlap_signals


def test_compute_overlap_signals_required_columns_and_formula():
    seller = pd.DataFrame(
        {
            "Address": ["1 A ST", "2 A ST", "3 B ST"],
            "Zip": ["11111", "11111", "22222"],
            "Lot (Acres)": [0.2, 0.4, 1.0],
        }
    )
    buyer = pd.DataFrame(
        {
            "Address": ["X", "Y", "Z"],
            "Zip": ["11111", "11111", "33333"],
            "Lot (Acres)": [0.25, 0.35, 1.4],
        }
    )

    cfg = SignalConfig(buyer_weight=1.3, ratio_weight=10.0, ratio_cap=5.0)
    out = compute_overlap_signals(seller, buyer, cfg)

    expected_cols = {
        "zip",
        "seller_count",
        "buyer_count",
        "demand_supply_ratio",
        "heat_index",
    }
    assert expected_cols.issubset(set(out.columns))

    row = out.loc[out["zip"] == "11111"].iloc[0]
    assert row["seller_count"] == 2
    assert row["buyer_count"] == 2
    assert row["demand_supply_ratio"] == 1.0
    assert row["heat_index"] == (2 * 1.3) + (1.0 * 10.0)
