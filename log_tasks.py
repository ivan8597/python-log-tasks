from collections import defaultdict
from datetime import datetime
from statistics import median
import re


def count_success_and_failure(file_path):
    """Return (successful_attempts, failed_attempts) from a log file."""
    total_attempts = 0
    failures = 0

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            if "Обновляем подписку пользователю" in line:
                total_attempts += 1

            if "ERROR" in line and "ошибка при списании" in line:
                failures += 1

    successes = total_attempts - failures
    return successes, failures


def auto_renewal_sub(file_path):
    """Write cumulative average and median values to auto_renewal_result.txt."""
    values = []
    phrase = "количество людей с автопродлением подписки:"

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            if phrase in line:
                value_text = line.split(phrase, 1)[1].strip()
                values.append(int(value_text))

    average_values = []
    median_values = []
    running_sum = 0

    for index, value in enumerate(values, start=1):
        running_sum += value
        average_values.append(round(running_sum / index, 2))
        median_values.append(median(values[:index]))

    with open("auto_renewal_result.txt", "w", encoding="utf-8") as result_file:
        for value in values:
            result_file.write(f"{value}\n")
        result_file.write(f"Среднее: {average_values}\n")
        result_file.write(f"Медиана: {median_values}\n")


def sub_renewal_by_day(file_path):
    """Write successful subscription renewals grouped by weekday."""
    weekdays = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    ]

    attempts = []
    last_attempt_by_user = {}

    attempt_pattern = re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?"
        r"Обновляем подписку пользователю id:\s*(?P<user_id>\d+)"
    )
    error_pattern = re.compile(
        r"У пользователя с id:\s*(?P<user_id>\d+).*?"
        r"ошибка при списании"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            attempt_match = attempt_pattern.search(line)

            if attempt_match:
                date_text = attempt_match.group("date")
                user_id = int(attempt_match.group("user_id"))
                operation_date = datetime.strptime(
                    date_text,
                    "%Y-%m-%d %H:%M:%S,%f",
                )
                weekday = weekdays[operation_date.weekday()]
                attempt = {
                    "user_id": user_id,
                    "weekday": weekday,
                    "failed": False,
                }
                attempts.append(attempt)
                last_attempt_by_user[user_id] = attempt

            error_match = error_pattern.search(line)

            if error_match:
                user_id = int(error_match.group("user_id"))
                if user_id in last_attempt_by_user:
                    last_attempt_by_user[user_id]["failed"] = True

    successful_by_day = defaultdict(int)

    for attempt in attempts:
        if not attempt["failed"]:
            successful_by_day[attempt["weekday"]] += 1

    with open("weekdays.txt", "w", encoding="utf-8") as result_file:
        result_file.write("Количество обновлений подписки по дням недели:\n")
        for weekday in weekdays:
            result_file.write(f"{weekday}: {successful_by_day[weekday]}\n")
