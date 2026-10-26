from unittest.mock import patch
from src.utils import (
    get_currency_rates,
    get_stock_prices,
    load_user_settings,
    read_transactions_xlsx,
)


def test_read_transactions_xlsx_not_found() -> None:
    df = read_transactions_xlsx("non_existent_file.xlsx")
    assert df.empty


def test_load_user_settings(tmp_path) -> None:
    p = tmp_path / "settings.json"
    p.write_text(
        '{"user_currencies": ["USD"], "user_stocks": ["AAPL"]}',
        encoding="utf-8",
    )
    settings = load_user_settings(str(p))
    assert settings["user_currencies"] == ["USD"]
    assert settings["user_stocks"] == ["AAPL"]


def test_load_user_settings_not_found() -> None:
    settings = load_user_settings("invalid_path.json")
    assert "user_currencies" in settings
    assert "user_stocks" in settings


@patch("requests.get")
def test_get_currency_rates_success(mock_get) -> None:
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "Valute": {"USD": {"Value": 75.5}, "EUR": {"Value": 85.2}}
    }
    rates = get_currency_rates(["USD", "EUR", "RUB"])
    assert len(rates) == 3
    assert rates[0]["currency"] == "USD"
    assert rates[0]["rate"] == 75.5
    assert rates[2]["currency"] == "RUB"
    assert rates[2]["rate"] == 1.0


@patch("requests.get")
def test_get_currency_rates_fallback(mock_get) -> None:
    mock_get.side_effect = Exception("Network error")
    rates = get_currency_rates(["USD", "EUR"])
    assert len(rates) == 2
    assert rates[0]["rate"] > 0


@patch("requests.get")
def test_get_stock_prices_fallback(mock_get) -> None:
    mock_get.side_effect = Exception("Network error")
    stocks = get_stock_prices(["AAPL"])
    assert len(stocks) == 1
    assert stocks[0]["stock"] == "AAPL"
    assert stocks[0]["price"] > 0
