"""Unit tests for the validation module."""

import numpy as np
import pandas as pd
import pytest

from fraud.data import generate_demo_data
from fraud.validation import ValidationError, validate_transactions


def test_valid_demo_dataset():
    """Verify that deterministic generated demo data passes validation without error."""
    df = generate_demo_data(n_samples=50, seed=42)
    validated = validate_transactions(df)
    assert len(validated) == 50
    assert list(validated.columns) == [
        "transaction_id",
        "amount",
        "historical_average_amount",
        "transactions_last_10m",
        "is_new_device",
    ]
    assert validated["is_new_device"].dtype == bool
    assert validated["transactions_last_10m"].dtype == int


def test_empty_dataframe_rejected():
    """Empty dataframe should raise ValidationError with clear message."""
    df = pd.DataFrame()
    with pytest.raises(ValidationError, match="Input transaction batch is empty"):
        validate_transactions(df)


def test_missing_required_columns():
    """Missing any required column must trigger descriptive error."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TXN-1"],
            "amount": [50.0],
            # missing historical_average_amount, transactions_last_10m, is_new_device
        }
    )
    with pytest.raises(ValidationError, match="Missing required column"):
        validate_transactions(df)


def test_duplicate_transaction_ids_rejected():
    """Duplicate transaction IDs should be rejected."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TXN-101", "TXN-101"],
            "amount": [50.0, 60.0],
            "historical_average_amount": [50.0, 50.0],
            "transactions_last_10m": [0, 1],
            "is_new_device": [False, True],
        }
    )
    with pytest.raises(ValidationError, match="Duplicate transaction_id"):
        validate_transactions(df)


def test_whitespace_padded_duplicate_transaction_ids_rejected():
    """IDs that become duplicates after whitespace normalization must be rejected."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TXN-101", " TXN-101 "],
            "amount": [50.0, 60.0],
            "historical_average_amount": [50.0, 50.0],
            "transactions_last_10m": [0, 1],
            "is_new_device": [False, True],
        }
    )
    with pytest.raises(ValidationError, match="Duplicate transaction_id"):
        validate_transactions(df)


def test_empty_or_whitespace_transaction_ids():
    """Empty or blank transaction IDs should be rejected."""
    df = pd.DataFrame(
        {
            "transaction_id": ["  ", "TXN-102"],
            "amount": [50.0, 60.0],
            "historical_average_amount": [50.0, 50.0],
            "transactions_last_10m": [0, 1],
            "is_new_device": [False, True],
        }
    )
    with pytest.raises(ValidationError, match="empty or blank strings"):
        validate_transactions(df)


@pytest.mark.parametrize("invalid_amount", [0.0, -15.5, np.nan, np.inf, -np.inf])
def test_invalid_amounts_rejected(invalid_amount):
    """Amount <= 0, NaN, or infinite must be rejected."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TXN-001"],
            "amount": [invalid_amount],
            "historical_average_amount": [50.0],
            "transactions_last_10m": [0],
            "is_new_device": [False],
        }
    )
    with pytest.raises(ValidationError):
        validate_transactions(df)


@pytest.mark.parametrize("bool_val", [True, False])
def test_boolean_in_numeric_columns_rejected(bool_val):
    """Boolean values must not be accepted as amounts or counts."""
    df_amt = pd.DataFrame(
        {
            "transaction_id": ["TXN-001"],
            "amount": [bool_val],
            "historical_average_amount": [50.0],
            "transactions_last_10m": [0],
            "is_new_device": [False],
        }
    )
    with pytest.raises(ValidationError):
        validate_transactions(df_amt)

    df_vel = pd.DataFrame(
        {
            "transaction_id": ["TXN-001"],
            "amount": [50.0],
            "historical_average_amount": [50.0],
            "transactions_last_10m": [bool_val],
            "is_new_device": [False],
        }
    )
    with pytest.raises(ValidationError):
        validate_transactions(df_vel)


@pytest.mark.parametrize("invalid_hist", [0.0, -10.0, np.nan, np.inf, -np.inf])
def test_invalid_historical_average_rejected(invalid_hist):
    """Historical average amount <= 0, NaN, or infinite must be rejected."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TXN-001"],
            "amount": [50.0],
            "historical_average_amount": [invalid_hist],
            "transactions_last_10m": [0],
            "is_new_device": [False],
        }
    )
    with pytest.raises(ValidationError):
        validate_transactions(df)


@pytest.mark.parametrize("invalid_velocity", [-1, 2.5, np.nan, np.inf])
def test_invalid_transaction_velocity_rejected(invalid_velocity):
    """Transactions last 10m must be a non-negative whole integer."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TXN-001"],
            "amount": [50.0],
            "historical_average_amount": [50.0],
            "transactions_last_10m": [invalid_velocity],
            "is_new_device": [False],
        }
    )
    with pytest.raises(ValidationError):
        validate_transactions(df)


@pytest.mark.parametrize("invalid_device", ["maybe", 42, "unknown", np.nan])
def test_invalid_boolean_device_rejected(invalid_device):
    """is_new_device must be boolean or strict boolean representation."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TXN-001"],
            "amount": [50.0],
            "historical_average_amount": [50.0],
            "transactions_last_10m": [0],
            "is_new_device": [invalid_device],
        }
    )
    with pytest.raises(ValidationError):
        validate_transactions(df)


def test_boolean_type_coercion():
    """String booleans 'True'/'False' or 1/0 should be normalized cleanly to Python bool."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TXN-001", "TXN-002", "TXN-003", "TXN-004"],
            "amount": [50.0, 60.0, 70.0, 80.0],
            "historical_average_amount": [50.0, 50.0, 50.0, 50.0],
            "transactions_last_10m": [0, 1, 2, 3],
            "is_new_device": ["true", "False", 1, 0],
        }
    )
    clean = validate_transactions(df)
    assert list(clean["is_new_device"]) == [True, False, True, False]

