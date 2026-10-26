from datetime import datetime
import json
import pandas as pd
from src.views import events_view, get_greeting, home_view


def test_get_greeting() -> None:
    assert get_greeting(datetime(2021, 12, 1, 7, 0)) == "Доброе утро"
    assert get_greeting(datetime(2021, 12, 1, 14, 0)) == "Добрый день"
    assert get_greeting(datetime(2021, 12, 1, 19, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2021, 12, 1, 2, 0)) == "Доброй ночи"


def test_home_view(sample_transactions_df) -> None:
    res_str = home_view("2021-12-21 15:00:00", sample_transactions_df)
    data = json.loads(res_str)
    assert data["greeting"] == "Добрый день"
    assert "cards" in data
    assert len(data["cards"]) > 0
    assert "top_transactions" in data
    assert len(data["top_transactions"]) <= 5
    assert "currency_rates" in data
    assert "stock_prices" in data


def test_home_view_empty_df() -> None:
    res_str = home_view("2021-12-21 15:00:00", pd.DataFrame())
    data = json.loads(res_str)
    assert data["greeting"] == "Добрый день"
    assert data["cards"] == []
    assert data["top_transactions"] == []


def test_events_view(sample_transactions_df) -> None:
    res_str = events_view("2021-12-21", sample_transactions_df, "M")
    data = json.loads(res_str)
    assert "expenses" in data
    assert "income" in data
    assert "total_amount" in data["expenses"]
    assert "total_amount" in data["income"]


def test_events_view_ranges(sample_transactions_df) -> None:
    for r in ["W", "Y", "ALL"]:
        res_str = events_view("2021-12-21", sample_transactions_df, r)
        data = json.loads(res_str)
        assert "expenses" in data


def test_events_view_empty_df() -> None:
    res_str = events_view("2021-12-21", pd.DataFrame())
    data = json.loads(res_str)
    assert data == {}
