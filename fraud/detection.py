"""Anomaly detection, policy rules, and factual evidence generation.

Separates unsupervised model findings (IsolationForest decision_function) from
deterministic business policy decisions (e.g. amount_ratio >= 5.0).
Provides deterministic factual evidence matching exact input values without
claiming internal model explainability.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from fraud.data import generate_reference_data
from fraud.telemetry import TelemetryCollector
from fraud.validation import validate_transactions

MODEL_VERSION: str = "isoforest-v1.0"
POLICY_VERSION: str = "policy-rule-or-model-v1.0"

# Illustrative policy choice threshold
POLICY_AMOUNT_RATIO_THRESHOLD: float = 5.0

FEATURE_COLUMNS = ["amount_ratio", "transactions_last_10m", "is_new_device"]


def build_feature_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Derive features from raw validated transactions.

    Returns:
        Tuple of (feature_dataframe, amount_ratio_series)
    """
    amount_ratio = df["amount"] / df["historical_average_amount"]
    features = pd.DataFrame(
        {
            "amount_ratio": amount_ratio,
            "transactions_last_10m": df["transactions_last_10m"].astype(float),
            "is_new_device": df["is_new_device"].astype(int),
        },
        index=df.index,
    )
    return features, amount_ratio


def train_reference_model(
    reference_df: Optional[pd.DataFrame] = None,
    random_state: int = 42,
    contamination: float = 0.05,
    n_estimators: int = 100,
) -> IsolationForest:
    """Train IsolationForest baseline once on the fixed reference dataset.

    Parameters are strictly pinned for reproducible scoring.
    """
    if reference_df is None:
        reference_df = generate_reference_data(n_samples=1000, seed=random_state)

    validated_ref = validate_transactions(reference_df)
    features, _ = build_feature_matrix(validated_ref)

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=1,
    )
    model.fit(features[FEATURE_COLUMNS])
    return model


def generate_factual_evidence(
    amount: float,
    historical_average: float,
    ratio: float,
    transactions_last_10m: int,
    is_new_device: bool,
) -> List[str]:
    """Produce deterministic factual statements from raw input values.

    These reflect observed input properties and rule boundaries; they do NOT
    represent or explain the internal mathematical reasoning of the IsolationForest.
    """
    evidence: List[str] = [
        f"Amount is {ratio:.1f} times the historical average (${amount:.2f} vs ${historical_average:.2f}).",
        "Device is new." if is_new_device else "Device is known (not new).",
        f"{transactions_last_10m} transaction(s) occurred in the preceding 10 minutes.",
    ]
    return evidence


def evaluate_batch(
    df: pd.DataFrame,
    model: IsolationForest,
    collector: Optional[TelemetryCollector] = None,
) -> pd.DataFrame:
    """Validate, score, and apply policy rules to a batch of transactions.

    Returns:
        DataFrame enriched with anomaly scores, model findings, policy triggers,
        deterministic evidence, and version tags.
    """
    if collector:
        collector.log_run_started(total_records=len(df) if df is not None else 0)

    try:
        clean_df = validate_transactions(df)
        if collector:
            collector.log_validation_completed(valid_count=len(clean_df))
    except Exception as exc:
        if collector:
            collector.log_validation_failed(str(exc))
            collector.log_run_failed(f"Validation failed: {exc}")
        raise

    features, amount_ratios = build_feature_matrix(clean_df)

    # Scikit-learn IsolationForest: decision_function lower means more unusual (outlier)
    scores = model.decision_function(features[FEATURE_COLUMNS])
    preds = model.predict(features[FEATURE_COLUMNS])  # -1 for outlier, 1 for inlier

    result_rows: List[Dict[str, Any]] = []
    review_count = 0

    for idx, (row_idx, row) in enumerate(clean_df.iterrows()):
        ratio = float(amount_ratios.iloc[idx])
        score = float(scores[idx])
        is_model_outlier = bool(preds[idx] == -1)
        is_ratio_outlier = bool(ratio >= POLICY_AMOUNT_RATIO_THRESHOLD)

        model_finding = "Outlier" if is_model_outlier else "Inlier"

        triggers: List[str] = []
        if is_model_outlier:
            triggers.append("Model anomaly finding (IsolationForest)")
        if is_ratio_outlier:
            triggers.append(
                f"Amount multiplier >= {POLICY_AMOUNT_RATIO_THRESHOLD:.1f}x (illustrative policy rule)"
            )

        policy_triggered = is_model_outlier or is_ratio_outlier
        outcome = "Review" if policy_triggered else "Not flagged"
        if policy_triggered:
            review_count += 1

        evidence = generate_factual_evidence(
            amount=float(row["amount"]),
            historical_average=float(row["historical_average_amount"]),
            ratio=ratio,
            transactions_last_10m=int(row["transactions_last_10m"]),
            is_new_device=bool(row["is_new_device"]),
        )

        row_result = {
            "transaction_id": row["transaction_id"],
            "amount": float(row["amount"]),
            "historical_average_amount": float(row["historical_average_amount"]),
            "amount_ratio": round(ratio, 2),
            "transactions_last_10m": int(row["transactions_last_10m"]),
            "is_new_device": bool(row["is_new_device"]),
            "anomaly_score": round(score, 4),
            "model_finding": model_finding,
            "policy_triggers": triggers if triggers else ["None"],
            "outcome": outcome,
            "evidence": evidence,
            "model_version": MODEL_VERSION,
            "policy_version": POLICY_VERSION,
        }
        result_rows.append(row_result)

        if collector:
            collector.log_transaction_scored(
                transaction_id=str(row["transaction_id"]),
                model_version=MODEL_VERSION,
                policy_version=POLICY_VERSION,
                outcome=outcome,
                anomaly_score=score,
                policy_triggered=policy_triggered,
            )

    results_df = pd.DataFrame(result_rows)

    if collector:
        total = len(results_df)
        rate = (review_count / total) if total > 0 else 0.0
        collector.log_run_completed(
            total_analysed=total,
            review_count=review_count,
            review_rate=rate,
        )

    return results_df

