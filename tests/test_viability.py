import pandas as pd

from core import ViabilityConfig, compute_buyer_buybox, label_viability


def test_viability_labels_with_buybox_and_critical_fields():
    seller = pd.DataFrame(
        {
            "Address": ["1 A St", "", "3 C St"],
            "APN": ["", "", "X3"],
            "Zip": ["11111", "11111", "11111"],
            "Lot (Acres)": [0.3, 0.4, 3.0],
        }
    )
    buyer = pd.DataFrame(
        {
            "Address": ["B1", "B2", "B3", "B4"],
            "Zip": ["11111", "11111", "11111", "11111"],
            "Lot (Acres)": [0.2, 0.3, 0.4, 0.5],
        }
    )

    buybox = compute_buyer_buybox(buyer, ViabilityConfig(min_buybox_sample=2))
    labeled = label_viability(
        seller,
        overlap_df=pd.DataFrame({"zip": ["11111"], "buyer_count": [4], "heat_index": [14], "demand_tier": ["HIGH"]}),
        buybox_by_zip=buybox,
        config=ViabilityConfig(min_acres=0.1, max_acres=2.0, buyer_floor=2),
    )

    statuses = labeled["viability_status"].tolist()
    assert statuses[0] in {"VIABLE", "REVIEW"}
    assert statuses[1] == "UNVIABLE"  # missing address and APN
    assert statuses[2] == "UNVIABLE"  # acres outside target
