#!/usr/bin/env python3
"""Find a data type suitable for failed-only retry.

Outputs only the selected data type id on stdout. Diagnostics go to stderr so
GitHub Actions can safely capture stdout as the workflow input.
"""

import csv
import os
import sys
from datetime import datetime, timedelta, timezone

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
    19: "Dividenschedule",
}

MANUAL_ONLY_TYPES = {2, 3}
SYSTEMIC_FAILURE_RATIO = 0.90
MIN_SYSTEMIC_ROWS = 10
NON_RETRYABLE_STATUSES = {"success", "no_data", "unsupported", "systemic_failed"}
TAIPEI_TZ = timezone(timedelta(hours=8))

def parse_utc(value):
    value = (value or "").strip()
    if not value:
        return None
    if value.endswith(" CST"):
        try:
            parsed = datetime.strptime(value[:-4].strip(), "%Y-%m-%d %H:%M:%S")
            return parsed.replace(tzinfo=TAIPEI_TZ).astimezone(timezone.utc)
        except ValueError:
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

def count_csv(path, now):
    with open(path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    accepted = 0
    failed = 0
    retryable = 0
    oldest_actionable = None

    for row in rows:
        status = normalize_status(row)
        if status in {"success", "no_data", "unsupported"}:
            accepted += 1

        if status not in {"success", "no_data", "unsupported", "not_processed", "rate_limited"}:
            failed += 1

        if status in NON_RETRYABLE_STATUSES:
            continue

        # not_processed, rate_limited, and unknown failed statuses are actionable.
        # Follow-up dispatch runs one downloader at a time, so rate-limit recovery
        # comes from short failed-only continuation runs instead of time-based delay.
        retryable += 1
        row_time = parse_utc(row.get("last_update_time")) or parse_utc(row.get("process_time"))
        if row_time and (oldest_actionable is None or row_time < oldest_actionable):
            oldest_actionable = row_time

    return total, accepted, failed, retryable, oldest_actionable

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
            total, accepted, failed, retryable, oldest_actionable = count_csv(csv_path, now)
        except Exception as exc:
            print(f"WARN: cannot read {csv_path}: {exc}", file=sys.stderr)
            continue

        if total == 0 or retryable == 0:
            continue

        fail_ratio = failed / total
        if total >= MIN_SYSTEMIC_ROWS and fail_ratio >= SYSTEMIC_FAILURE_RATIO:
            skipped_systemic.append((type_id, folder, total, failed, fail_ratio))
            continue

        age_seconds = 0
        if oldest_actionable is not None:
            age_seconds = (now - oldest_actionable).total_seconds()
        completion_priority = 1 if accepted < 130 else 0
        candidates.append((completion_priority, retryable, age_seconds, type_id, folder, total, accepted, failed))

    for type_id, folder, total, failed, fail_ratio in skipped_systemic:
        print(
            f"SKIP systemic failure candidate: Type {type_id} {folder} "
            f"failed={failed}/{total} ({fail_ratio:.0%})",
            file=sys.stderr,
        )

    if not candidates:
        return

    completion_priority, retryable, age_seconds, type_id, folder, total, accepted, failed = max(candidates)
    reason = "completion_backlog" if completion_priority else "failed_backlog"
    print(
        f"SELECT failed-only retry: Type {type_id} {folder} "
        f"reason={reason}, accepted={accepted}/{total}, retryable={retryable}, "
        f"failed={failed}, oldest_actionable_hours={age_seconds / 3600:.1f}",
        file=sys.stderr,
    )
    print(type_id)


if __name__ == "__main__":
    main()
