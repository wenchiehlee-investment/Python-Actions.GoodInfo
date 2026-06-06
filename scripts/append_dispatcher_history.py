#!/usr/bin/env python3
"""Append one GoodInfo dispatcher/downloader history row."""

import argparse
import csv
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


TAIPEI_TZ = timezone(timedelta(hours=8))
EXPECTED_ROWS = 130
ACCEPTED_STATUSES = {"success", "no_data", "unsupported"}
NON_ACTIONABLE_STATUSES = {"success", "no_data", "unsupported", "not_processed", "rate_limited"}

FOLDER_BY_TYPE = {
    "1": "DividendDetail",
    "2": "BasicInfo",
    "3": "StockDetail",
    "4": "StockBzPerformance",
    "5": "ShowSaleMonChart",
    "6": "EquityDistribution",
    "7": "StockBzPerformance1",
    "8": "ShowK_ChartFlow",
    "9": "StockHisAnaQuar",
    "10": "EquityDistributionClassHis",
    "11": "WeeklyTradingData",
    "12": "ShowMonthlyK_ChartFlow",
    "13": "ShowMarginChart",
    "14": "ShowMarginChartWeek",
    "15": "ShowMarginChartMonth",
    "16": "StockFinDetail",
    "17": "ShowWeeklyK_ChartFlow",
    "18": "ShowDailyK_ChartFlow",
}

FIELDNAMES = [
    "logged_at",
    "workflow_run_id",
    "workflow_run_number",
    "workflow_sha",
    "event_name",
    "dispatch_reason",
    "data_type",
    "folder",
    "type_name",
    "retry_failed_only",
    "test_mode",
    "download_status",
    "script_exit_code",
    "download_duration_seconds",
    "total_rows",
    "expected_rows",
    "accepted_rows",
    "accepted_progress",
    "success_rows",
    "success_progress",
    "retryable_failed_rows",
    "rate_limited_rows",
    "no_data_rows",
    "unsupported_rows",
    "systemic_failed_rows",
    "not_processed_rows",
    "try_touched_rows",
    "try_success_rows",
    "oldest_actionable_time",
    "oldest_success_time",
    "newest_success_time",
    "run_url",
]


def normalize_status(row):
    status = (row.get("status") or "").strip().lower()
    if status:
        return status
    if (row.get("success") or "").strip().lower() == "true":
        return "success"
    return "retryable_failed"


def parse_time(value):
    value = (value or "").strip()
    if not value:
        return None
    if value.endswith(" CST"):
        try:
            parsed = datetime.strptime(value[:-4].strip(), "%Y-%m-%d %H:%M:%S")
            return parsed.replace(tzinfo=TAIPEI_TZ)
        except ValueError:
            return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc).astimezone(TAIPEI_TZ)
            return parsed.astimezone(TAIPEI_TZ)
        except ValueError:
            continue
    return None


def format_time(value):
    if not value:
        return ""
    return value.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M:%S CST")


def row_time(row):
    return parse_time(row.get("last_update_time")) or parse_time(row.get("process_time"))


def summarize_download_results(path, run_started_at):
    if not path.exists():
        return {
            "total_rows": 0,
            "accepted_rows": 0,
            "success_rows": 0,
            "retryable_failed_rows": 0,
            "rate_limited_rows": 0,
            "no_data_rows": 0,
            "unsupported_rows": 0,
            "systemic_failed_rows": 0,
            "not_processed_rows": 0,
            "try_touched_rows": 0,
            "try_success_rows": 0,
            "oldest_actionable_time": "",
            "oldest_success_time": "",
            "newest_success_time": "",
        }

    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    statuses = [normalize_status(row) for row in rows]
    success_times = [
        parsed for row, status in zip(rows, statuses)
        if status == "success" and (parsed := row_time(row))
    ]
    actionable_times = [
        parsed for row, status in zip(rows, statuses)
        if status not in NON_ACTIONABLE_STATUSES and (parsed := row_time(row))
    ]

    try_touched = 0
    try_success = 0
    if run_started_at:
        for row, status in zip(rows, statuses):
            parsed = row_time(row)
            if parsed and parsed >= run_started_at:
                try_touched += 1
                if status == "success":
                    try_success += 1

    return {
        "total_rows": len(rows),
        "accepted_rows": sum(1 for status in statuses if status in ACCEPTED_STATUSES),
        "success_rows": sum(1 for status in statuses if status == "success"),
        "retryable_failed_rows": sum(1 for status in statuses if status not in NON_ACTIONABLE_STATUSES),
        "rate_limited_rows": sum(1 for status in statuses if status == "rate_limited"),
        "no_data_rows": sum(1 for status in statuses if status == "no_data"),
        "unsupported_rows": sum(1 for status in statuses if status == "unsupported"),
        "systemic_failed_rows": sum(1 for status in statuses if status == "systemic_failed"),
        "not_processed_rows": sum(1 for status in statuses if status == "not_processed"),
        "try_touched_rows": try_touched,
        "try_success_rows": try_success,
        "oldest_actionable_time": format_time(min(actionable_times)) if actionable_times else "",
        "oldest_success_time": format_time(min(success_times)) if success_times else "",
        "newest_success_time": format_time(max(success_times)) if success_times else "",
    }


def progress(numerator, denominator):
    return f"{numerator}/{denominator}" if denominator else f"{numerator}/0"


def append_row(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-type", required=True)
    parser.add_argument("--type-name", default="")
    parser.add_argument("--dispatch-reason", default="")
    parser.add_argument("--retry-failed-only", default="false")
    parser.add_argument("--test-mode", default="false")
    parser.add_argument("--download-status", default="")
    parser.add_argument("--script-exit-code", default="")
    parser.add_argument("--download-duration-seconds", default="")
    parser.add_argument("--run-started-at", default="")
    parser.add_argument("--output", default="data/dispatcher_history.csv")
    args = parser.parse_args()

    folder = FOLDER_BY_TYPE.get(args.data_type, "")
    run_started_at = parse_time(args.run_started_at)
    summary = summarize_download_results(Path(folder) / "download_results.csv", run_started_at) if folder else {}
    expected_rows = EXPECTED_ROWS

    row = {
        "logged_at": datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M:%S CST"),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "workflow_run_number": os.environ.get("GITHUB_RUN_NUMBER", ""),
        "workflow_sha": os.environ.get("GITHUB_SHA", ""),
        "event_name": os.environ.get("GITHUB_EVENT_NAME", ""),
        "dispatch_reason": args.dispatch_reason,
        "data_type": args.data_type,
        "folder": folder,
        "type_name": args.type_name,
        "retry_failed_only": args.retry_failed_only,
        "test_mode": args.test_mode,
        "download_status": args.download_status,
        "script_exit_code": args.script_exit_code,
        "download_duration_seconds": args.download_duration_seconds,
        "expected_rows": expected_rows,
        "run_url": (
            f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
            f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/"
            f"{os.environ.get('GITHUB_RUN_ID', '')}"
        ),
    }
    row.update(summary)
    row["accepted_progress"] = progress(int(row.get("accepted_rows") or 0), expected_rows)
    row["success_progress"] = progress(int(row.get("success_rows") or 0), int(row.get("total_rows") or 0))

    append_row(Path(args.output), row)
    print(
        f"Appended dispatcher history: Type {args.data_type} "
        f"accepted={row['accepted_progress']} success={row['success_progress']} "
        f"reason={args.dispatch_reason or '-'}"
    )


if __name__ == "__main__":
    main()
