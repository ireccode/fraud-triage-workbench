"""Validation module for input transaction batches."""

from typing import List
import numpy as np
import pandas as pd


class ValidationError(ValueError):
    """Raised when an input transaction dataset violates validation rules."""

    def __init__(self, message: str, errors: List[str] | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or [message]


REQUIRED_COLUMNS = [
    "transaction_id",
    "amount",
    "historical_average_amount",
    "transactions_last_10m",
    "is_new_device",
]


def validate_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean input transaction batch.

    Rules:
    1. Input must not be None and must be a DataFrame.
    2. Input must not be empty (at least 1 row).
    3. Required columns must be present.
    4. Transaction IDs must be non-empty strings and strictly unique.
    5. Numeric fields (amount, historical_average_amount, transactions_last_10m)
       must not contain missing, NaN, or infinite values.
    6. amount and historical_average_amount must be strictly greater than 0.
    7. transactions_last_10m must be non-negative integers (>= 0).
    8. is_new_device must be boolean (or strict boolean-compatible: bool, 0/1, True/False).

    Returns:
        Cleaned, typed DataFrame with required columns.

    Raises:
        ValidationError with actionable explanations.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValidationError("Input data must be a valid pandas DataFrame.")

    if df.empty:
        raise ValidationError("Input transaction batch is empty. Please provide at least one transaction.")

    # 1. Column presence check
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValidationError(
            f"Missing required column(s): {', '.join(missing_cols)}. "
            f"Required schema: {', '.join(REQUIRED_COLUMNS)}."
        )

    # Work on a copy with only required columns
    clean_df = df[REQUIRED_COLUMNS].copy()
    errors: List[str] = []

    # 2. Transaction ID checks: non-empty, unique, string-like
    txn_ids = clean_df["transaction_id"]
    if txn_ids.isna().any():
        errors.append("transaction_id contains null or missing values.")
    else:
        # Normalize by converting to string and stripping leading/trailing whitespace
        clean_df["transaction_id"] = txn_ids.astype(str).str.strip()
        if (clean_df["transaction_id"] == "").any():
            errors.append("transaction_id contains empty or blank strings.")

        duplicates = clean_df[clean_df.duplicated(subset=["transaction_id"], keep=False)]
        if not duplicates.empty:
            dup_sample = duplicates["transaction_id"].unique()[:3].tolist()
            errors.append(f"Duplicate transaction_id values detected: {dup_sample}.")

    # 3. Numeric checks: amount
    try:
        clean_df["amount"] = pd.to_numeric(clean_df["amount"])
    except (ValueError, TypeError):
        errors.append("Column 'amount' contains non-numeric values.")

    # 4. Numeric checks: historical_average_amount
    try:
        clean_df["historical_average_amount"] = pd.to_numeric(clean_df["historical_average_amount"])
    except (ValueError, TypeError):
        errors.append("Column 'historical_average_amount' contains non-numeric values.")

    # 5. Non-finite, NaN, and positive checks for amounts
    if "amount" in clean_df and pd.api.types.is_numeric_dtype(clean_df["amount"]):
        if clean_df["amount"].isna().any() or np.isinf(clean_df["amount"]).any():
            errors.append("Column 'amount' contains NaN, null, or infinite values.")
        elif (clean_df["amount"] <= 0).any():
            errors.append("Column 'amount' must be strictly positive (> 0.00).")

    if "historical_average_amount" in clean_df and pd.api.types.is_numeric_dtype(
        clean_df["historical_average_amount"]
    ):
        if (
            clean_df["historical_average_amount"].isna().any()
            or np.isinf(clean_df["historical_average_amount"]).any()
        ):
            errors.append("Column 'historical_average_amount' contains NaN, null, or infinite values.")
        elif (clean_df["historical_average_amount"] <= 0).any():
            errors.append("Column 'historical_average_amount' must be strictly positive (> 0.00).")

    # 6. transactions_last_10m: non-negative integer
    try:
        raw_vel = pd.to_numeric(clean_df["transactions_last_10m"])
        if raw_vel.isna().any() or np.isinf(raw_vel).any():
            errors.append("Column 'transactions_last_10m' contains NaN, null, or infinite values.")
        else:
            # Check if all values are exact integers
            if not np.all(raw_vel.to_numpy() == raw_vel.round().to_numpy()):
                errors.append("Column 'transactions_last_10m' must contain whole integers, not decimals.")
            elif (raw_vel < 0).any():
                errors.append("Column 'transactions_last_10m' must be non-negative (>= 0).")
            else:
                clean_df["transactions_last_10m"] = raw_vel.astype(int)
    except (ValueError, TypeError):
        errors.append("Column 'transactions_last_10m' contains non-numeric values.")

    # 7. is_new_device: boolean
    raw_device = clean_df["is_new_device"]
    if raw_device.isna().any():
        errors.append("Column 'is_new_device' contains null or missing values.")
    else:
        # Check if values are boolean or unambiguous boolean representations
        valid_bools = {True, False, 1, 0, "true", "false", "True", "False", "1", "0", 1.0, 0.0}
        invalid_mask = ~raw_device.isin(valid_bools)
        if invalid_mask.any():
            errors.append("Column 'is_new_device' contains non-boolean values.")
        else:
            # Normalize to python bool
            mapping = {
                True: True,
                False: False,
                1: True,
                0: False,
                "true": True,
                "True": True,
                "1": True,
                "false": False,
                "False": False,
                "0": False,
                1.0: True,
                0.0: False,
            }
            clean_df["is_new_device"] = raw_device.map(mapping).astype(bool)

    if errors:
        summary_msg = f"Validation failed with {len(errors)} error(s): " + "; ".join(errors)
        raise ValidationError(summary_msg, errors=errors)

    clean_df["transaction_id"] = clean_df["transaction_id"].astype(str).str.strip()
    return clean_df

