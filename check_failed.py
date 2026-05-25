#!/usr/bin/env python3
"""Find a data type suitable for failed-only retry.

Outputs only the selected data type id on stdout. Diagnostics go to stderr so
GitHub Actions can safely capture stdout as the workflow input.
"""

import csv
import os
import sys
from datetime import datetime, timezone

FOLDER_MAPPING = {
    1: "DividendDetail",
    2: "BasicInfo",
    3: "StockDetail",
    4: "StockBzPerformance",
    5: "ShowSaleMonChart",
    6: "EquityDistribution",
    7: "StockBzPerformance1",
    8: "ShowK_ChartFlow",
    9: "StockHisAnaQuar",
    10: "EquityDistributionClassHis",
    11: "WeeklyTradingData",
    12: "ShowMonthlyK_ChartFlow",
    13: "ShowMarginChart",
    14: "ShowMarginChartWeek",
    15: "ShowMarginChartMonth",
    16: "StockFinDetail",
    17: "ShowWeeklyK_ChartFlow",
    18: "ShowDailyK_ChartFlow",
}

MANUAL_ONLY_TYPES = {2, 3}
SYSTEMIC_FAILURE_RATIO = 0.90
MIN_SYSTEMIC_ROWS = 10
RATE_LIMIT_COOLDOWN_HOURS = 6
NON_RETRYABLE_STATUSES = {"success", "no_data", "unsupported", "systemic_failed"}

PERIOD_BY_TYPE = {
    1: "daily",
    4: "weekly",
    5: "daily",
    6: "weekly",
    7: "weekly",
    8: "weekly",
    9: "weekly",
    10: "weekly",
    11: "weekly",
    12: "monthly",
    13: "daily",
    14: "weekly",
    15: "monthly",
    16: "monthly",
    17: "weekly",
    18: "daily",
}
STALE_THRESHOLD_DAYS_BY_PERIOD = {
    "daily": 2,
    "weekly": 8,
    "monthly": 35,
}


def parse_utc(value):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def normalize_status(row):
    status = (row.get("status") or "").strip().lower()
    if status:
        return status
    if (row.get("success") or "").strip().lower() == "true":
        return "success"
    return "retryable_failed"


def is_rate_limited_ready(type_id, row, now):
    retry_time = parse_utc(row.get("process_time")) or parse_utc(row.get("last_update_time"))
    if retry_time is not None:
        retry_age_hours = (now - retry_time).total_seconds() / 3600
        if retry_age_hours < RATE_LIMIT_COOLDOWN_HOURS:
            return False

    data_time = parse_utc(row.get("last_update_time")) or retry_time
    if data_time is None:
        return True

    period = PERIOD_BY_TYPE[type_id]
    stale_threshold_days = STALE_THRESHOLD_DAYS_BY_PERIOD[period]
    data_age_days = (now - data_time).total_seconds() / 86400
    return data_age_days >= stale_threshold_days


def count_csv(type_id, path, now):
    with open(path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    failed = 0
    retryable = 0
    waiting_rate_limited = 0
    oldest_actionable = None

    for row in rows:
        status = normalize_status(row)
        if status not in {"success", "no_data", "unsupported", "not_processed", "rate_limited"}:
            failed += 1

        if status in NON_RETRYABLE_STATUSES:
            continue

        if status == "rate_limited" and not is_rate_limited_ready(type_id, row, now):
            waiting_rate_limited += 1
            continue

        # not_processed, rate_limited after cooldown, and unknown failed statuses are actionable.
        retryable += 1
        row_time = parse_utc(row.get("last_update_time")) or parse_utc(row.get("process_time"))
        if row_time and (oldest_actionable is None or row_time < oldest_actionable):
            oldest_actionable = row_time

    return total, failed, retryable, waiting_rate_limited, oldest_actionable


def main():
    now = datetime.now(timezone.utc)
    candidates = []
    skipped_systemic = []

    for type_id, folder in sorted(FOLDER_MAPPING.items()):
        if type_id in MANUAL_ONLY_TYPES:
            continue

        csv_path = os.path.join(folder, "download_results.csv")
        if not os.path.exists(csv_path):
            continue

        try:
            total, failed, retryable, waiting_rate_limited, oldest_actionable = count_csv(type_id, csv_path, now)
        except Exception as exc:
            print(f"WARN: cannot read {csv_path}: {exc}", file=sys.stderr)
            continue

        if total == 0 or retryable == 0:
            if waiting_rate_limited:
                print(
                    f"WAIT rate-limit cooldown: Type {type_id} {folder} "
                    f"waiting={waiting_rate_limited}",
                    file=sys.stderr,
                )
            continue

        fail_ratio = failed / total
        if total >= MIN_SYSTEMIC_ROWS and fail_ratio >= SYSTEMIC_FAILURE_RATIO:
            skipped_systemic.append((type_id, folder, total, failed, fail_ratio))
            continue

        age_seconds = 0
        if oldest_actionable is not None:
            age_seconds = (now - oldest_actionable).total_seconds()
        candidates.append((age_seconds, retryable, type_id, folder, total, failed))

    for type_id, folder, total, failed, fail_ratio in skipped_systemic:
        print(
            f"SKIP systemic failure candidate: Type {type_id} {folder} "
            f"failed={failed}/{total} ({fail_ratio:.0%})",
            file=sys.stderr,
        )

    if not candidates:
        return

    age_seconds, retryable, type_id, folder, total, failed = max(candidates)
    print(
        f"SELECT failed-only retry: Type {type_id} {folder} "
        f"retryable={retryable}/{total}, failed={failed}, "
        f"oldest_actionable_hours={age_seconds / 3600:.1f}",
        file=sys.stderr,
    )
    print(type_id)


if __name__ == "__main__":
    main()
