from datetime import datetime
from functools import wraps
import logging
from pathlib import Path
from typing import Any, Callable, Optional, cast
import pandas as pd

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger = logging.getLogger("reports")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    fh = logging.FileHandler(LOGS_DIR / "reports.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def report_decorator(filename: Optional[str] = None) -> Callable[..., Any]:
    def decorator(
        func: Callable[..., pd.DataFrame]
    ) -> Callable[..., pd.DataFrame]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
            result_df = func(*args, **kwargs)
            out_filename = filename
            if not out_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_filename = f"report_{func.__name__}_{timestamp}.json"

            reports_dir = Path(__file__).resolve().parent.parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            target_path = reports_dir / out_filename

            try:
                if str(out_filename).endswith(".xlsx"):
                    result_df.to_excel(target_path, index=False)
                else:
                    result_df.to_json(
                        target_path,
                        orient="records",
                        force_ascii=False,
                        indent=2,
                    )
                logger.info(f"Отчет сохранен: {target_path}")
            except Exception as e:
                logger.error(f"Ошибка сохранения отчета: {e}")

            return result_df
        return wrapper
    return decorator


def _filter_last_3_months(
    transactions: pd.DataFrame, date: Optional[str] = None
) -> pd.DataFrame:
    if transactions.empty or "Дата операции" not in transactions.columns:
        return pd.DataFrame()

    df = transactions.copy()
    df["parsed_date"] = pd.to_datetime(
        df["Дата операции"], dayfirst=True, errors="coerce"
    )

    if date:
        try:
            end_dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            end_dt = datetime.strptime(date, "%d.%m.%Y")
    else:
        end_dt = datetime.now()

    start_dt = end_dt - pd.DateOffset(months=3)
    mask = (df["parsed_date"] >= start_dt) & (df["parsed_date"] <= end_dt)
    return cast(pd.DataFrame, df[mask].copy())


@report_decorator()
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None,
) -> pd.DataFrame:
    logger.info(f"Отчет по категории: {category}")
    df_period = _filter_last_3_months(transactions, date)
    if (
        df_period.empty
        or "Категория" not in df_period.columns
        or "Сумма платежа" not in df_period.columns
    ):
        return pd.DataFrame()

    mask = (
        (df_period["Категория"].str.lower() == category.lower())
        & (df_period["Сумма платежа"] < 0)
    )
    return cast(pd.DataFrame, df_period[mask])


@report_decorator()
def spending_by_weekday(
    transactions: pd.DataFrame,
    date: Optional[str] = None,
) -> pd.DataFrame:
    logger.info("Отчет по дням недели")
    df_period = _filter_last_3_months(transactions, date)
    if df_period.empty or "Сумма платежа" not in df_period.columns:
        return pd.DataFrame()

    expenses = df_period[df_period["Сумма платежа"] < 0].copy()
    expenses["abs_amount"] = expenses["Сумма платежа"].abs()
    expenses["weekday"] = expenses["parsed_date"].dt.day_name()

    mean_series = expenses.groupby("weekday")["abs_amount"].mean()
    grouped_df = mean_series.reset_index(name="mean_spending")
    return cast(pd.DataFrame, grouped_df)


@report_decorator()
def spending_by_workday(
    transactions: pd.DataFrame,
    date: Optional[str] = None,
) -> pd.DataFrame:
    logger.info("Отчет по рабочим/выходным")
    df_period = _filter_last_3_months(transactions, date)
    if df_period.empty or "Сумма платежа" not in df_period.columns:
        return pd.DataFrame()

    expenses = df_period[df_period["Сумма платежа"] < 0].copy()
    expenses["abs_amount"] = expenses["Сумма платежа"].abs()
    expenses["day_type"] = expenses["parsed_date"].dt.weekday.apply(
        lambda w: "Выходной" if w >= 5 else "Рабочий"
    )

    mean_series = expenses.groupby("day_type")["abs_amount"].mean()
    grouped_df = mean_series.reset_index(name="mean_spending")
    return cast(pd.DataFrame, grouped_df)
