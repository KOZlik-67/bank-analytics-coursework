import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import pandas as pd
import requests

load_dotenv()

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("utils")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    fh = logging.FileHandler(LOGS_DIR / "utils.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def read_transactions_xlsx(file_path: str) -> pd.DataFrame:
    logger.info(f"Чтение транзакций: {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"Файл {file_path} не найден.")
        return pd.DataFrame()
    try:
        df = pd.read_excel(file_path)
        logger.info(f"Загружено записей: {len(df)}")
        return df
    except Exception as e:
        logger.error(f"Ошибка чтения Excel: {e}")
        return pd.DataFrame()


def load_user_settings(file_path: Optional[str] = None) -> Dict[str, Any]:
    if file_path is None:
        file_path = str(
            Path(__file__).resolve().parent.parent / "user_settings.json"
        )
    if not os.path.exists(file_path):
        logger.warning(f"Файл настроек {file_path} не найден.")
        return {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
        }
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Ошибка разбора настроек: {e}")
        return {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
        }


def get_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    logger.info(f"Запрос валют: {currencies}")
    rates: List[Dict[str, Any]] = []
    try:
        response = requests.get(
            "https://www.cbr-xml-daily.ru/daily_json.js", timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            valute = data.get("Valute", {})
            for curr in currencies:
                if curr == "RUB":
                    rates.append({"currency": "RUB", "rate": 1.0})
                elif curr in valute:
                    rate = round(float(valute[curr]["Value"]), 2)
                    rates.append({"currency": curr, "rate": rate})
                else:
                    rates.append({"currency": curr, "rate": 75.0})
            return rates
    except Exception as e:
        logger.error(f"Ошибка запроса валют: {e}")

    fallback_defaults = {"USD": 73.21, "EUR": 87.08}
    for curr in currencies:
        rates.append(
            {"currency": curr, "rate": fallback_defaults.get(curr, 75.0)}
        )
    return rates


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    logger.info(f"Запрос акций: {stocks}")
    token = os.getenv("FINNHUB_API_KEY", "")
    results: List[Dict[str, Any]] = []

    fallback_prices = {
        "AAPL": 150.12,
        "AMZN": 3173.18,
        "GOOGL": 2742.39,
        "MSFT": 296.71,
        "TSLA": 1007.08,
    }

    for stock in stocks:
        price: Optional[float] = None
        if token:
            try:
                url = (
                    f"https://finnhub.io/api/v1/quote?symbol={stock}"
                    f"&token={token}"
                )
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    c = data.get("c")
                    if c and float(c) > 0:
                        price = round(float(c), 2)
            except Exception as e:
                logger.error(f"Ошибка котировки {stock}: {e}")

        if price is None:
            price = fallback_prices.get(stock, 100.0)

        results.append({"stock": stock, "price": price})
    return results
