import pandas as pd
from src.reports import (
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)


def test_spending_by_category(sample_transactions_df) -> None:
    df_res = spending_by_category(
        sample_transactions_df, "Супермаркеты", "20.12.2021"
    )
    assert not df_res.empty
    assert (df_res["Категория"].str.lower() == "супермаркеты").all()


def test_spending_by_category_empty() -> None:
    df_res = spending_by_category(pd.DataFrame(), "Супермаркеты")
    assert df_res.empty


def test_spending_by_weekday(sample_transactions_df) -> None:
    df_res = spending_by_weekday(sample_transactions_df, "20.12.2021")
    assert not df_res.empty
    assert "weekday" in df_res.columns
    assert "mean_spending" in df_res.columns


def test_spending_by_weekday_empty() -> None:
    df_res = spending_by_weekday(pd.DataFrame())
    assert df_res.empty


def test_spending_by_workday(sample_transactions_df) -> None:
    df_res = spending_by_workday(sample_transactions_df, "20.12.2021")
    assert not df_res.empty
    assert "day_type" in df_res.columns
    assert "mean_spending" in df_res.columns


def test_spending_by_workday_empty() -> None:
    df_res = spending_by_workday(pd.DataFrame())
    assert df_res.empty
