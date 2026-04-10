import pandas as pd

from core import assign_duplicate_groups, dedupe_records, normalize_address


def test_normalize_address_and_dedupe():
    assert normalize_address("123 Main Street.") == "123 MAIN ST"

    df = pd.DataFrame(
        {
            "APN": ["A1", "A1", "B2"],
            "Address": ["123 Main St", "123 Main Street", "500 Oak Rd"],
            "Zip": ["11111", "11111", "22222"],
            "Lot (Acres)": [0.2, 0.2, 0.9],
        }
    )

    tagged = assign_duplicate_groups(df)
    assert tagged["is_duplicate"].sum() == 2

    deduped = dedupe_records(df)
    assert len(deduped) == 2
