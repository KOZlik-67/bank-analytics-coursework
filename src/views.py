from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from src.utils import get_currency_rates, get_stock_prices, load_user_settings

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger = logging.getLogger("views")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    fh = logging.FileHandler(LOGS_DIR / "views.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def get_greeting(dt: datetime) -> str:
    hour = dt.hour
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def home_view(date_time_str: str, df: pd.DataFrame) -> str:
    logger.info(f"Главная страница: {date_time_str}")
    dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")

    greeting = get_greeting(dt)
    settings = load_user_settings()
    currs = settings.get("user_currencies", ["USD", "EUR"])
    currency_rates = get_currency_rates(currs)
    default_stocks = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    stocks = settings.get("user_stocks", default_stocks)
    stock_prices = get_stock_prices(stocks)

    if df.empty or "Дата операции" not in df.columns:
        return json.dumps(
            {
                "greeting": greeting,
                "cards": [],
                "top_transactions": [],
                "currency_rates": currency_rates,
                "stock_prices": stock_prices,
            },
            ensure_ascii=False,
            indent=2,
        )

    df_copy = df.copy()
    df_copy["parsed_date"] = pd.to_datetime(
        df_copy["Дата операции"], dayfirst=True, errors="coerce"
    )

    start_date = dt.replace(day=1, hour=0, minute=0, second=0)
    mask = (
        (df_copy["parsed_date"] >= start_date)
        & (df_copy["parsed_date"] <= dt)
    )
    month_df = df_copy[mask].copy()

    cards_list: List[Dict[str, Any]] = []
    if (
        "Номер карты" in month_df.columns
        and "Сумма платежа" in month_df.columns
    ):
        spent_mask = (
            (month_df["Сумма платежа"] < 0)
            & (month_df["Номер карты"].notna())
        )
        cards_spent = month_df[spent_mask].copy()

        for card_number, group in cards_spent.groupby("Номер карты"):
            card_str = str(card_number).replace("*", "").strip()
            last_digits = card_str[-4:] if len(card_str) >= 4 else card_str
            total_spent = round(abs(float(group["Сумма платежа"].sum())), 2)
            cashback = round(total_spent / 100.0, 2)
            cards_list.append({
                "last_digits": last_digits,
                "total_spent": total_spent,
                "cashback": cashback,
            })

    top_transactions: List[Dict[str, Any]] = []
    if not month_df.empty and "Сумма платежа" in month_df.columns:
        month_df["abs_amount"] = month_df["Сумма платежа"].abs()
        sorted_df = month_df.sort_values(
            by="abs_amount", ascending=False
        ).head(5)
        for _, row in sorted_df.iterrows():
            top_transactions.append({
                "date": (
                    row["parsed_date"].strftime("%d.%m.%Y")
                    if pd.notna(row["parsed_date"])
                    else ""
                ),
                "amount": round(float(row.get("Сумма платежа", 0.0)), 2),
                "category": str(row.get("Категория", "")),
                "description": str(row.get("Описание", "")),
            })

    result = {
        "greeting": greeting,
        "cards": cards_list,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


def events_view(
    date_str: str, df: pd.DataFrame, range_type: Optional[str] = "M"
) -> str:
    logger.info(f"События: {date_str}, диапазон: {range_type}")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        dt = datetime.strptime(date_str, "%d.%m.%Y")

    if df.empty or "Дата операции" not in df.columns:
        return json.dumps({}, ensure_ascii=False)

    df_copy = df.copy()
    df_copy["parsed_date"] = pd.to_datetime(
        df_copy["Дата операции"], dayfirst=True, errors="coerce"
    )

    if range_type == "W":
        start_date = dt - pd.Timedelta(value=int(dt.weekday()), unit="D")
        start_date = start_date.replace(hour=0, minute=0, second=0)
    elif range_type == "Y":
        start_date = dt.replace(month=1, day=1, hour=0, minute=0, second=0)
    elif range_type == "ALL":
        start_date = datetime.min
    else:
        start_date = dt.replace(day=1, hour=0, minute=0, second=0)

    end_date = dt.replace(hour=23, minute=59, second=59)
    mask = (
        (df_copy["parsed_date"] >= start_date)
        & (df_copy["parsed_date"] <= end_date)
    )
    filtered_df = df_copy[mask].copy()

    has_payment = "Сумма платежа" in filtered_df.columns
    if has_payment:
        expenses_df = filtered_df[filtered_df["Сумма платежа"] < 0].copy()
    else:
        expenses_df = pd.DataFrame()

    expenses_total = 0
    if not expenses_df.empty:
        expenses_total = round(abs(float(expenses_df["Сумма платежа"].sum())))

    main_expenses: List[Dict[str, Any]] = []
    transfers_and_cash: List[Dict[str, Any]] = []

    if not expenses_df.empty and "Категория" in expenses_df.columns:
        tc_mask = expenses_df["Категория"].isin(["Переводы", "Наличные"])
        tc_df = expenses_df[tc_mask]
        for cat_name, grp in tc_df.groupby("Категория"):
            transfers_and_cash.append({
                "category": str(cat_name),
                "amount": round(abs(float(grp["Сумма платежа"].sum()))),
            })
        transfers_and_cash.sort(key=lambda x: x["amount"], reverse=True)

        cat_group = (
            expenses_df.groupby("Категория")["Сумма платежа"]
            .apply(lambda s: abs(s.sum()))
            .sort_values(ascending=False)
        )
        top_7 = cat_group.head(7)
        other_sum = cat_group.iloc[7:].sum() if len(cat_group) > 7 else 0

        for cat_k, amt_v in top_7.items():
            main_expenses.append({
                "category": str(cat_k),
                "amount": round(float(amt_v)),
            })
        if other_sum > 0:
            main_expenses.append({
                "category": "Остальное",
                "amount": round(float(other_sum)),
            })

    if has_payment:
        income_df = filtered_df[filtered_df["Сумма платежа"] > 0].copy()
    else:
        income_df = pd.DataFrame()

    income_total = 0
    if not income_df.empty:
        income_total = round(float(income_df["Сумма платежа"].sum()))

    main_income: List[Dict[str, Any]] = []
    if not income_df.empty and "Категория" in income_df.columns:
        inc_group = (
            income_df.groupby("Категория")["Сумма платежа"]
            .sum()
            .sort_values(ascending=False)
        )
        for cat_inc_k, amt_inc_v in inc_group.items():
            main_income.append({
                "category": str(cat_inc_k),
                "amount": round(float(amt_inc_v)),
            })

    settings = load_user_settings()
    currs = settings.get("user_currencies", ["USD", "EUR"])
    currency_rates = get_currency_rates(currs)
    default_stocks = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    stocks = settings.get("user_stocks", default_stocks)
    stock_prices = get_stock_prices(stocks)

    result = {
        "expenses": {
            "total_amount": expenses_total,
            "main": main_expenses,
            "transfers_and_cash": transfers_and_cash,
        },
        "income": {
            "total_amount": income_total,
            "main": main_income,
        },
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }
    return json.dumps(result, ensure_ascii=False, indent=2)
