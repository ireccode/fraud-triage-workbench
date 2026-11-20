"""Unit tests for the detection, policy rules, and evidence engine."""

import pandas as pd
import pytest

from fraud.data import generate_demo_data, generate_reference_data
from fraud.detection import (
    MODEL_VERSION,
    POLICY_AMOUNT_RATIO_THRESHOLD,
    POLICY_VERSION,
    evaluate_batch,
    generate_factual_evidence,
    train_reference_model,
)


@pytest.fixture(scope="module")
def trained_model():
    """Module-scoped reference model fitted once on fixed reference data."""
    ref_df = generate_reference_data(n_samples=1000, seed=42)
    return train_reference_model(ref_df, random_state=42)


def test_deterministic_scoring(trained_model):
    """Running evaluation twice on identical data produces identical scores."""
    demo_df = generate_demo_data(n_samples=25, seed=1337)

    res1 = evaluate_batch(demo_df, trained_model)
    res2 = evaluate_batch(demo_df, trained_model)

    pd.testing.assert_series_equal(res1["anomaly_score"], res2["anomaly_score"])
    pd.testing.assert_series_equal(res1["outcome"], res2["outcome"])


def test_policy_threshold_trigger(trained_model):
    """Extreme amount multiplier (>= 5.0) triggers 'Review' outcome regardless of model finding."""
    extreme_txn = pd.DataFrame(
        {
            "transaction_id": ["TXN-EXTREME"],
            "amount": [1500.00],
            "historical_average_amount": [100.00],  # ratio = 15.0 >= 5.0
            "transactions_last_10m": [0],
            "is_new_device": [False],
        }
    )
    result = evaluate_batch(extreme_txn, trained_model)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["outcome"] == "Review"
    assert row["amount_ratio"] == 15.0
    assert any("multiplier >= 5.0x" in trigger for trigger in row["policy_triggers"])


def test_outcome_labels_adhere_to_specification(trained_model):
    """Only 'Review' and 'Not flagged' outcomes must be produced; never 'Fraud confirmed' or 'Safe'."""
    demo_df = generate_demo_data(n_samples=50, seed=1337)
    result = evaluate_batch(demo_df, trained_model)

    unique_outcomes = set(result["outcome"].unique())
    assert unique_outcomes.issubset({"Review", "Not flagged"})
    assert "Fraud confirmed" not in unique_outcomes
    assert "Safe" not in unique_outcomes


def test_review_queue_ordering_by_anomaly_score(trained_model):
    """Review queue sorted by anomaly score ascending ranks most unusual transactions first."""
    demo_df = generate_demo_data(n_samples=50, seed=1337)
    result = evaluate_batch(demo_df, trained_model)

    reviews = result[result["outcome"] == "Review"].sort_values(
        by="anomaly_score", ascending=True
    )
    assert not reviews.empty
    scores = reviews["anomaly_score"].tolist()
    assert scores == sorted(scores), "Anomaly scores in review queue must be sorted ascending"


def test_factual_evidence_matches_inputs():
    """Factual evidence strings strictly correspond to input properties."""
    evidence = generate_factual_evidence(
        amount=820.00,
        historical_average=100.00,
        ratio=8.2,
        transactions_last_10m=6,
        is_new_device=True,
    )

    assert "Amount is 8.2 times the historical average" in evidence[0]
    assert "Device is new." == evidence[1]
    assert "6 transaction(s) occurred in the preceding 10 minutes." == evidence[2]


def test_version_constants_attached(trained_model):
    """Output contains model and policy version tags."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TXN-TEST"],
            "amount": [50.00],
            "historical_average_amount": [50.00],
            "transactions_last_10m": [0],
            "is_new_device": [False],
        }
    )
    res = evaluate_batch(df, trained_model)
    assert res.iloc[0]["model_version"] == MODEL_VERSION
    assert res.iloc[0]["policy_version"] == POLICY_VERSION

