from unittest.mock import patch
import pandas as pd
from src.main import run_demo


@patch("src.main.read_transactions_xlsx")
def test_run_demo_empty(mock_read: object) -> None:
    mock_read.return_value = pd.DataFrame()
    run_demo()


@patch("src.main.read_transactions_xlsx")
def test_run_demo_success(
    mock_read: object, sample_transactions_df: pd.DataFrame
) -> None:
    mock_read.return_value = sample_transactions_df
    run_demo()
