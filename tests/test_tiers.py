import pandas as pd

from core.demand_tiers import DemandTierConfig, assign_demand_tiers


def test_demand_tier_percentile_rules():
    df = pd.DataFrame(
        {
            "zip": ["1", "2", "3", "4", "5"],
            "buyer_count": [8, 4, 3, 1, 6],
            "heat_index": [30.0, 20.0, 10.0, 5.0, 25.0],
        }
    )

    out = assign_demand_tiers(
        df,
        DemandTierConfig(
            high_percentile=0.8,
            low_percentile=0.2,
            high_buyer_floor=5,
            medium_buyer_min=2,
            medium_buyer_max=4,
        ),
    )

    by_zip = out.set_index("zip")
    assert by_zip.loc["1", "demand_tier"] == "HIGH"
    assert by_zip.loc["4", "demand_tier"] == "LOW"
    assert by_zip.loc["2", "demand_tier"] == "MEDIUM"
    assert isinstance(by_zip.loc["1", "tier_reason"], str)
