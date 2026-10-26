from pathlib import Path
from typing import Any, Dict, List, cast
from src.reports import (
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)
from src.services import (
    investment_bank,
    profitable_cashback_categories,
    search_phone_numbers,
    search_transfers_to_individuals,
    simple_search,
)
from src.utils import read_transactions_xlsx
from src.views import events_view, home_view


def run_demo() -> None:
    root = Path(__file__).resolve().parent.parent
    data_path = root / "data" / "operations.xlsx"
    df = read_transactions_xlsx(str(data_path))

    if df.empty:
        print("Файл operations.xlsx не найден или пуст.")
        return

    home_json = home_view("2021-12-21 15:30:00", df)
    events_json = events_view("2021-12-21", df, "M")

    raw_records = df.to_dict(orient="records")
    dict_records = cast(List[Dict[str, Any]], raw_records)

    saved = investment_bank("2021-12", dict_records, 50)
    phones = search_phone_numbers(dict_records)
    transfers = search_transfers_to_individuals(dict_records)
    search_res = simple_search("перевод", dict_records)
    cashback_res = profitable_cashback_categories(dict_records, 2021, 12)

    rep_weekday = spending_by_weekday(df, "21.12.2021")
    rep_workday = spending_by_workday(df, "21.12.2021")
    rep_cat = spending_by_category(df, "Супермаркеты", "21.12.2021")

    print(f"Главная страница: {len(home_json)} символов")
    print(f"События: {len(events_json)} символов")
    print(f"Найдено телефонов: {len(phones)}, переводов: {len(transfers)}")
    print(f"Поиск: {len(search_res)}, кешбэк: {len(cashback_res)}")
    print(f"Отчеты: {len(rep_cat)}, {len(rep_workday)}, {len(rep_weekday)}")
    print(f"Инвесткопилка: {saved}")


if __name__ == "__main__":
    run_demo()
