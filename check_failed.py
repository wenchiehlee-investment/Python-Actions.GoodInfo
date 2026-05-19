#!/usr/bin/env python3
"""Find a data type suitable for failed-only retry.

Outputs only the selected data type id on stdout. Diagnostics go to stderr so
GitHub Actions can safely capture stdout as the workflow input.
"""

import csv
import os
import sys

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


def count_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    total = len(rows)
    failed = sum(1 for row in rows if row.get("success", "").lower() == "false")
    success = sum(1 for row in rows if row.get("success", "").lower() == "true")
    return total, success, failed


def main():
    candidates = []
    skipped_systemic = []

    for type_id, folder in sorted(FOLDER_MAPPING.items()):
        if type_id in MANUAL_ONLY_TYPES:
            continue

        csv_path = os.path.join(folder, "download_results.csv")
        if not os.path.exists(csv_path):
            continue

        try:
            total, success, failed = count_csv(csv_path)
        except Exception as exc:
            print(f"WARN: cannot read {csv_path}: {exc}", file=sys.stderr)
            continue

        if failed == 0 or total == 0:
            continue

        fail_ratio = failed / total
        if total >= MIN_SYSTEMIC_ROWS and fail_ratio >= SYSTEMIC_FAILURE_RATIO:
            skipped_systemic.append((type_id, folder, total, success, failed, fail_ratio))
            continue

        candidates.append((failed, fail_ratio, type_id, folder, total, success))

    for type_id, folder, total, success, failed, fail_ratio in skipped_systemic:
        print(
            f"SKIP systemic failure candidate: Type {type_id} {folder} "
            f"failed={failed}/{total} ({fail_ratio:.0%}), success={success}",
            file=sys.stderr,
        )

    if not candidates:
        return

    failed, fail_ratio, type_id, folder, total, success = max(candidates)
    print(
        f"SELECT failed-only retry: Type {type_id} {folder} "
        f"failed={failed}/{total} ({fail_ratio:.0%}), success={success}",
        file=sys.stderr,
    )
    print(type_id)


if __name__ == "__main__":
    main()
