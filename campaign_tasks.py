"""Solutions for the campaign_data.csv analytics case.

The notebook uses pandas, so install it with ``pip install pandas`` if needed.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pandas as pd


PLATFORM_COLUMN = "Платформа"
CAMPAIGN_TYPE_COLUMN = "Тип кампании"
CITY_COLUMN = "Город"
CONVERSION_COLUMN = "Конверсия"
BUDGET_COLUMN = "Бюджет"
CLICKS_COLUMN = "Клики"
CAMPAIGN_ID_COLUMN = "ID Кампании"
START_DATE_COLUMN = "Начальная дата"
INCOME_COLUMN = "Доход"


def _read_campaign_data(file_path: str | Path) -> pd.DataFrame:
    """Read the campaign CSV and validate the columns used by this case."""
    data = pd.read_csv(file_path)
    required_columns = {
        PLATFORM_COLUMN,
        CAMPAIGN_TYPE_COLUMN,
        CITY_COLUMN,
        CONVERSION_COLUMN,
        BUDGET_COLUMN,
        CLICKS_COLUMN,
        CAMPAIGN_ID_COLUMN,
        START_DATE_COLUMN,
        INCOME_COLUMN,
    }
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"В CSV отсутствуют столбцы: {missing}")
    return data


def most_effective_platform(file_path: str | Path) -> str:
    """Return the platform with the highest average conversion."""
    data = _read_campaign_data(file_path)
    return data.groupby(PLATFORM_COLUMN)[CONVERSION_COLUMN].mean().idxmax()


def most_successful_campaign_type(file_path: str | Path) -> str:
    """Return the campaign type with the highest average conversion."""
    data = _read_campaign_data(file_path)
    return data.groupby(CAMPAIGN_TYPE_COLUMN)[CONVERSION_COLUMN].mean().idxmax()


def most_successful_city(file_path: str | Path) -> str:
    """Return the city with the highest average conversion."""
    data = _read_campaign_data(file_path)
    return data.groupby(CITY_COLUMN)[CONVERSION_COLUMN].mean().idxmax()


def write_platform_city_results(
    file_path: str | Path,
    output_path: str | Path = "platform_city_results.txt",
) -> None:
    """Write each platform's city budget shares to ``output_path``.

    Platforms retain their first-seen order from the CSV. Cities inside each
    platform are sorted by decreasing share of that platform's total budget.
    """
    data = _read_campaign_data(file_path)
    platform_order = data[PLATFORM_COLUMN].drop_duplicates().tolist()

    grouped = (
        data.groupby([PLATFORM_COLUMN, CITY_COLUMN], sort=False)[BUDGET_COLUMN]
        .sum()
        .reset_index()
    )

    with open(output_path, "w", encoding="utf-8") as result_file:
        for platform in platform_order:
            platform_data = grouped[grouped[PLATFORM_COLUMN] == platform].copy()
            total_budget = platform_data[BUDGET_COLUMN].sum()
            platform_data["Доля затрат"] = (
                platform_data[BUDGET_COLUMN] / total_budget * 100
            )
            platform_data = platform_data.sort_values(
                by="Доля затрат", ascending=False, kind="mergesort"
            )

            result_file.write(f"Для группы {platform}:\n")
            for _, row in platform_data.iterrows():
                share = round(float(row["Доля затрат"]), 2)
                result_file.write(
                    f"- Город: {row[CITY_COLUMN]}, "
                    f"доля затрат на рекламу: {share}%\n"
                )


def calculate_average_budget(file_path: str | Path, platform: str) -> float:
    """Return the average campaign budget for ``platform`` rounded to 2 places."""
    data = _read_campaign_data(file_path)
    platform_data = data[data[PLATFORM_COLUMN] == platform]
    if platform_data.empty:
        raise ValueError(f"Платформа не найдена: {platform}")
    return round(float(platform_data[BUDGET_COLUMN].mean()), 2)


def get_missing_campaign_dates(file_path: str | Path) -> Generator[str, None, None]:
    """Yield dates in the campaign period that have no campaign start.

    Dates are yielded in ascending order in ``YYYY-MM-DD`` format. The period
    is defined by the earliest and latest values in ``Начальная дата``.
    """
    data = _read_campaign_data(file_path)
    start_dates = pd.to_datetime(data[START_DATE_COLUMN], errors="raise")
    launched_dates = set(start_dates.dt.normalize())

    for date in pd.date_range(start_dates.min(), start_dates.max(), freq="D"):
        if date not in launched_dates:
            yield date.strftime("%Y-%m-%d")


def group_campaign_data(file_path: str | Path) -> list[dict[str, object]]:
    """Group total budget and clicks by city, sorted alphabetically by city."""
    data = _read_campaign_data(file_path)
    grouped = (
        data.groupby(CITY_COLUMN, as_index=False, sort=True)
        .agg({CLICKS_COLUMN: "sum", BUDGET_COLUMN: "sum"})
        .rename(
            columns={
                CLICKS_COLUMN: "Количество кликов",
                BUDGET_COLUMN: "Суммарный бюджет",
            }
        )
    )

    return grouped.to_dict(orient="records")


def campaign_generator(
    file_path: str | Path,
    city: str,
    budget: float,
) -> Generator[dict[str, str], None, None]:
    """Yield campaigns in ``city`` with budget above ``budget``.

    Records are sorted by ascending campaign ID and contain the fields required
    by the notebook task. Values are returned as strings, matching the example.
    """
    data = _read_campaign_data(file_path)
    selected = data[
        (data[CITY_COLUMN] == city) & (data[BUDGET_COLUMN] > budget)
    ].sort_values(CAMPAIGN_ID_COLUMN, ascending=True, kind="mergesort")

    for _, row in selected.iterrows():
        yield {
            "ID Кампании": str(row[CAMPAIGN_ID_COLUMN]),
            "Тип": str(row[CAMPAIGN_TYPE_COLUMN]),
            "Платформа": str(row[PLATFORM_COLUMN]),
            "Доход": str(row[INCOME_COLUMN]),
        }


def solve_campaign_case(file_path: str | Path) -> dict[str, str]:
    """Run the three "most successful" tasks and return their variables."""
    return {
        "most_effective_platform": most_effective_platform(file_path),
        "most_successful_campaign_type": most_successful_campaign_type(file_path),
        "most_successful_city": most_successful_city(file_path),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Анализ campaign_data.csv")
    parser.add_argument("file_path", help="Путь к campaign_data.csv")
    args = parser.parse_args()

    print(solve_campaign_case(args.file_path))
    write_platform_city_results(args.file_path)
    print("Создан файл: platform_city_results.txt")
    print("Средний бюджет Google:", calculate_average_budget(args.file_path, "Google"))
    print("Пропущенных дат:", len(list(get_missing_campaign_dates(args.file_path))))
    print("Групп по городам:", len(group_campaign_data(args.file_path)))
