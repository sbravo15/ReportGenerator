import pandas as pd

from core.seller_xray_utils import (
    add_lot_size_class,
    build_export_frames,
    build_working_dataset,
    compute_duplicate_metrics,
    lot_size_class,
)


def test_duplicate_metrics_regression_math():
    tagged = pd.DataFrame(
        {
            "record_id": [1, 2, 3, 4, 5],
            "is_duplicate": [True, True, True, True, False],
            "duplicate_group_id": ["G1", "G1", "G1", "G2", ""],
        }
    )

    metrics = compute_duplicate_metrics(tagged, total_records=5)
    assert metrics["duplicate_rows_raw"] == 2  # (3-1) + (1-1)
    assert metrics["deduped_records"] == 3
    assert metrics["duplicate_rate_pct"] == 40.0
    assert metrics["duplicate_groups"] == 2
    assert metrics["largest_duplicate_group_size"] == 3


def test_lot_size_bucket_boundaries():
    assert lot_size_class(0.05999) == "UNVIABLE"
    assert lot_size_class(0.12) == "INFILL"
    assert lot_size_class(0.30) == "INFILL"
    assert lot_size_class(0.30001) == "LARGE_LOT"
    assert lot_size_class(0.50) == "LARGE_LOT"
    assert lot_size_class(0.50001) == "BIG_LOT"
    assert lot_size_class(1.0) == "BIG_LOT"
    assert lot_size_class(1.00001) == "MINI_TRACT"
    assert lot_size_class(5.0) == "MINI_TRACT"
    assert lot_size_class(5.01) == "XL"
    assert lot_size_class(float("nan")) == "UNKNOWN"


def test_working_lens_transformations():
    tagged = pd.DataFrame(
        {
            "record_id": [1, 2, 3, 4],
            "listing_status": ["ACTIVE", "", "PENDING", ""],
            "lot_acres": [0.15, 0.20, 0.30, 0.07],
        }
    )
    deduped = tagged.iloc[[0, 1, 3]].copy()  # remove id=3 as duplicate winner simulation

    w1 = build_working_dataset(tagged, deduped, use_deduped=True, off_market_only=True, size_preset="All")
    assert len(w1) == 2  # ids 2,4 (id1 active removed)

    w2 = build_working_dataset(tagged, deduped, use_deduped=False, off_market_only=False, size_preset="UNVIABLE (<0.12)")
    assert len(w2) == 1
    assert w2.iloc[0]["record_id"] == 4


def test_export_smoke_frames():
    tagged = pd.DataFrame(
        {
            "record_id": [1, 2, 3],
            "is_duplicate": [True, False, False],
            "duplicate_group_id": ["G1", "", ""],
            "listing_status": ["ACTIVE", "", ""],
            "lot_acres": [0.05, 0.20, None],
        }
    )
    deduped = tagged.iloc[[0, 1, 2]].copy()
    viable_labeled = add_lot_size_class(
        pd.DataFrame(
            {
                "record_id": [1, 2, 3],
                "viability_status": ["UNVIABLE", "VIABLE", "REVIEW"],
                "lot_acres": [0.05, 0.20, None],
            }
        )
    )
    scored = viable_labeled.copy()

    clean, review = build_export_frames(
        tagged_df=tagged,
        deduped_df=deduped,
        viable_labeled_df=viable_labeled,
        scored_df=scored,
        use_deduped=True,
        off_market_only=True,
    )

    assert not clean.empty
    assert set(clean["viability_status"].unique().tolist()) <= {"VIABLE"}
    assert not review.empty
    assert "review_reason" in review.columns
    assert any(r in review["review_reason"].astype(str).tolist() for r in ["duplicate_cluster", "on_market_removed", "unviable_or_unknown_size", "review", "unviable"])
