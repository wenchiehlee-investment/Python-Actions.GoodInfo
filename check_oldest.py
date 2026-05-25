#!/usr/bin/env python3
"""Select the automatic data type with the stalest row-level data.

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
EXPECTED_ROWS = 130
ACCEPTED_STATUSES = {"success", "no_data", "unsupported"}

# Freshness SLA by collection period. Completion gaps are handled by
# failed-only runs before any full freshness refresh is considered.
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
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
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


def summarize_type(type_id, folder):
    csv_path = os.path.join(folder, "download_results.csv")
    if not os.path.exists(csv_path):
        return {
            "type_id": type_id,
            "folder": folder,
            "reason": "missing_csv",
            "priority": 3,
            "age_seconds": float("inf"),
        }

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return {
            "type_id": type_id,
            "folder": folder,
            "reason": "empty_csv",
            "priority": 3,
            "age_seconds": float("inf"),
        }

    accepted_rows = [row for row in rows if normalize_status(row) in ACCEPTED_STATUSES]
    if len(rows) < EXPECTED_ROWS:
        return {
            "type_id": type_id,
            "folder": folder,
            "reason": f"short_csv rows={len(rows)} accepted={len(accepted_rows)}",
            "priority": 2,
            "age_seconds": float("inf"),
        }

    if len(accepted_rows) < EXPECTED_ROWS:
        # Completion gaps are handled by check_failed.py as failed-only work.
        # Do not convert a 129/130 or pending-heavy CSV into a full 130-row refresh.
        return {
            "type_id": type_id,
            "folder": folder,
            "reason": f"completion_backlog rows={len(rows)} accepted={len(accepted_rows)}",
            "priority": 0,
            "age_seconds": 0,
        }

    oldest_time = None
    for row in accepted_rows:
        row_time = parse_utc(row.get("last_update_time")) or parse_utc(row.get("process_time"))
        if row_time and (oldest_time is None or row_time < oldest_time):
            oldest_time = row_time

    if oldest_time is None:
        return {
            "type_id": type_id,
            "folder": folder,
            "reason": "no_valid_row_times",
            "priority": 2,
            "age_seconds": float("inf"),
        }

    age = datetime.now(timezone.utc) - oldest_time
    period = PERIOD_BY_TYPE[type_id]
    stale_threshold_days = STALE_THRESHOLD_DAYS_BY_PERIOD[period]
    return {
        "type_id": type_id,
        "folder": folder,
        "reason": (
            f"period={period} oldest_row_age={age} "
            f"threshold={stale_threshold_days}d"
        ),
        "priority": 1 if age.days >= stale_threshold_days else 0,
        "age_seconds": age.total_seconds(),
    }


def main():
    candidates = []
    for type_id, folder in sorted(FOLDER_MAPPING.items()):
        if type_id in MANUAL_ONLY_TYPES:
            continue
        try:
            summary = summarize_type(type_id, folder)
        except Exception as exc:
            print(f"WARN: cannot inspect Type {type_id} {folder}: {exc}", file=sys.stderr)
            continue
        if summary["priority"] > 0:
            candidates.append(summary)

    if not candidates:
        return

    selected = max(candidates, key=lambda item: (item["priority"], item["age_seconds"]))
    print(
        f"SELECT stale/full run: Type {selected['type_id']} {selected['folder']} "
        f"reason={selected['reason']}",
        file=sys.stderr,
    )
    print(selected["type_id"])


if __name__ == "__main__":
    main()
