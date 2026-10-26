from datetime import datetime
import json
import logging
from math import ceil
from pathlib import Path
import re
from typing import Any, Dict, List

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger = logging.getLogger("services")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    fh = logging.FileHandler(LOGS_DIR / "services.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def profitable_cashback_categories(
    data: List[Dict[str, Any]], year: int, month: int
) -> str:
    logger.info(f"Анализ кешбэка: {year}-{month:02d}")

    def filter_by_date(item: Dict[str, Any]) -> bool:
        date_str = str(item.get("Дата операции", item.get("date", "")))
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(date_str[:10], "%d.%m.%Y")
            except ValueError:
                return False
        return dt.year == year and dt.month == month

    month_data = filter(filter_by_date, data)
    categories_cashback: Dict[str, float] = {}

    for item in month_data:
        cat = str(item.get("Категория", item.get("category", "Без категории")))
        raw_amt = item.get(
            "Сумма операции", item.get("Сумма платежа", item.get("amount", 0))
        )
        try:
            amt = abs(float(raw_amt))
        except (ValueError, TypeError):
            amt = 0.0

        cashback = amt * 0.01
        categories_cashback[cat] = categories_cashback.get(cat, 0.0) + cashback

    result = {k: int(round(v)) for k, v in categories_cashback.items()}
    return json.dumps(result, ensure_ascii=False, indent=4)


def investment_bank(
    month: str, transactions: List[Dict[str, Any]], limit: int
) -> float:
    logger.info(f"Инвесткопилка: {month}, лимит: {limit}")
    total_saved = 0.0
    target_year, target_month = map(int, month.split("-"))

    for tx in transactions:
        date_str = str(tx.get("Дата операции", tx.get("date", "")))
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(date_str[:10], "%d.%m.%Y")
            except ValueError:
                continue

        if dt.year == target_year and dt.month == target_month:
            raw_amt = tx.get("Сумма операции", tx.get("amount", 0))
            try:
                amt = abs(float(raw_amt))
            except (ValueError, TypeError):
                continue

            if limit > 0:
                rounded_target = ceil(amt / limit) * limit
                diff = round(rounded_target - amt, 2)
                total_saved += diff

    return round(total_saved, 2)


def simple_search(query: str, data: List[Dict[str, Any]]) -> str:
    logger.info(f"Поиск: {query}")
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    results = list(filter(
        lambda x: bool(
            pattern.search(str(x.get("Описание", x.get("description", ""))))
            or pattern.search(str(x.get("Категория", x.get("category", ""))))
        ),
        data,
    ))
    return json.dumps(results, ensure_ascii=False, indent=2)


def search_phone_numbers(data: List[Dict[str, Any]]) -> str:
    logger.info("Поиск телефонных номеров")
    phone_pattern = re.compile(
        r"(?:\+7|8)[\s\-]?(?:\(\d{3}\)|\d{3})?[\s\-]?"
        r"\d{2,3}[\s\-]?\d{2}[\s\-]?\d{2}(?:[\s\-]?\d{2})?"
    )

    results = list(filter(
        lambda x: bool(
            phone_pattern.search(
                str(x.get("Описание", x.get("description", "")))
            )
        ),
        data,
    ))
    return json.dumps(results, ensure_ascii=False, indent=2)


def search_transfers_to_individuals(data: List[Dict[str, Any]]) -> str:
    logger.info("Поиск переводов физлицам")
    individual_pattern = re.compile(r"[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.")

    def is_transfer_to_individual(item: Dict[str, Any]) -> bool:
        category = str(item.get("Категория", item.get("category", "")))
        description = str(item.get("Описание", item.get("description", "")))
        return category == "Переводы" and bool(
            individual_pattern.search(description)
        )

    results = list(filter(is_transfer_to_individual, data))
    return json.dumps(results, ensure_ascii=False, indent=2)
