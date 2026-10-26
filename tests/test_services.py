import json
from src.services import (
    investment_bank,
    profitable_cashback_categories,
    search_phone_numbers,
    search_transfers_to_individuals,
    simple_search,
)


def test_profitable_cashback_categories() -> None:
    data = [
        {
            "Дата операции": "2021-12-10",
            "Категория": "Кафе",
            "Сумма операции": 5000,
        },
        {
            "Дата операции": "2021-12-15",
            "Категория": "Кафе",
            "Сумма операции": 5000,
        },
        {
            "Дата операции": "2021-11-10",
            "Категория": "Кафе",
            "Сумма операции": 3000,
        },
    ]
    res = json.loads(profitable_cashback_categories(data, 2021, 12))
    assert res.get("Кафе") == 100


def test_investment_bank() -> None:
    data = [
        {"Дата операции": "2021-12-01", "Сумма операции": 1712},
        {"Дата операции": "2021-12-05", "Сумма операции": 250},
        {"Дата операции": "2021-11-05", "Сумма операции": 250},
    ]
    saved = investment_bank("2021-12", data, 50)
    assert saved == 38.0


def test_simple_search() -> None:
    data = [
        {"Описание": "Покупка книг в Буквоеде", "Категория": "Книги"},
        {"Описание": "Бензин Лукойл", "Категория": "Авто"},
    ]
    res = json.loads(simple_search("букв", data))
    assert len(res) == 1
    assert res[0]["Категория"] == "Книги"


def test_search_phone_numbers() -> None:
    data = [
        {"Описание": "Перевод +7 921 11-22-33"},
        {"Описание": "Оплата мобильной связи 89000000000"},
        {"Описание": "Покупка в магазине"},
    ]
    res = json.loads(search_phone_numbers(data))
    assert len(res) == 2


def test_search_transfers_to_individuals() -> None:
    data = [
        {"Категория": "Переводы", "Описание": "Перевод Валерий А."},
        {"Категория": "Переводы", "Описание": "Перевод на карту Tinkoff"},
        {"Категория": "Супермаркеты", "Описание": "Иван И."},
    ]
    res = json.loads(search_transfers_to_individuals(data))
    assert len(res) == 1
    assert res[0]["Описание"] == "Перевод Валерий А."


def test_services_edge_cases() -> None:
    broken_data = [
        {"Дата операции": "не_дата", "Сумма операции": "не_число"},
        {"Дата операции": "2021-12-01", "Сумма операции": "abc"},
        {"Дата операции": "2021-12-02", "Сумма операции": None},
    ]
    res_cashback = profitable_cashback_categories(broken_data, 2021, 12)
    assert json.loads(res_cashback) == {"Без категории": 0}

    saved = investment_bank("2021-12", broken_data, 50)
    assert saved == 0.0
