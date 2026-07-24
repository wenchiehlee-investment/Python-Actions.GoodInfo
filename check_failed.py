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
EXPECTED_ROWS = 130
SYSTEMIC_FAILURE_RATIO = 0.90
MIN_SYSTEMIC_ROWS = 10
SYSTEMIC_STARVATION_HOURS = 48
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
    has_rate_limited = False

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
        if status == "rate_limited":
            has_rate_limited = True
        # Cooldown must measure the LAST ATTEMPT (process_time), not the last
        # successful update (last_update_time). With the old precedence a stock
        # whose upstream page is legitimately stale (e.g. revenue not yet
        # published after a typhoon-delayed filing deadline) always looked
        # "3 days old", so the 12h cooldown never engaged and every follow-up
        # dispatch re-triggered a full retry run — a ~8-minute retry storm
        # (11 consecutive failed Actions runs on 2026-07-13).
        row_time = parse_utc(row.get("process_time")) or parse_utc(row.get("last_update_time"))
        if row_time and (oldest_actionable is None or row_time < oldest_actionable):
            oldest_actionable = row_time

    return total, accepted, failed, retryable, oldest_actionable, has_rate_limited

def main():
    now = datetime.now(timezone.utc)
    candidates = []
    systemic_candidates = []
    skipped_systemic = []

    for type_id, folder in sorted(FOLDER_MAPPING.items()):
        if type_id in MANUAL_ONLY_TYPES:
            continue

        csv_path = os.path.join(folder, "download_results.csv")
        if not os.path.exists(csv_path):
            continue

        try:
            total, accepted, failed, retryable, oldest_actionable, has_rate_limited = count_csv(csv_path, now)
        except Exception as exc:
            print(f"WARN: cannot read {csv_path}: {exc}", file=sys.stderr)
            continue

        if total == 0 or retryable == 0:
            continue

        # Cooldown check to prevent infinite loop for persistent failures.
        # rate_limited rows stay exempt: they are meant to be retried immediately
        # through short failed-only continuation runs (see comment in count_csv).
        if oldest_actionable is not None and not has_rate_limited:
            age_hours = (now - oldest_actionable).total_seconds() / 3600
            if age_hours < 12:
                print(
                    f"DEBUG: Type {type_id} {folder} failed backlog in cooldown. "
                    f"Last attempt: {age_hours:.1f}h ago",
                    file=sys.stderr,
                )
                continue

        age_seconds = 0
        if oldest_actionable is not None:
            age_seconds = (now - oldest_actionable).total_seconds()
        completion_priority = 1 if accepted < EXPECTED_ROWS else 0

        fail_ratio = failed / total
        is_systemic = total >= MIN_SYSTEMIC_ROWS and fail_ratio >= SYSTEMIC_FAILURE_RATIO
        # A systemic type that has sat untouched past the starvation threshold
        # would otherwise be excluded forever as long as ANY other type still
        # has ordinary (non-systemic) failures anywhere in the 19 types - since
        # the systemic bucket only ever gets picked when `candidates` is empty.
        # Past this threshold, let it compete as a normal candidate instead.
        starved = is_systemic and (age_seconds / 3600) >= SYSTEMIC_STARVATION_HOURS

        if is_systemic and not starved:
            skipped_systemic.append((type_id, folder, total, failed, fail_ratio))
            if completion_priority:
                systemic_candidates.append(
                    (completion_priority, retryable, age_seconds, type_id, folder, total, accepted, failed)
                )
            continue

        if starved:
            print(
                f"PROMOTE starved systemic candidate: Type {type_id} {folder} "
                f"failed={failed}/{total} ({fail_ratio:.0%}), stuck for {age_seconds / 3600:.1f}h "
                f">= {SYSTEMIC_STARVATION_HOURS}h threshold; competing as a normal candidate",
                file=sys.stderr,
            )

        candidates.append((completion_priority, retryable, age_seconds, type_id, folder, total, accepted, failed))

    for type_id, folder, total, failed, fail_ratio in skipped_systemic:
        print(
            f"SKIP systemic failure candidate: Type {type_id} {folder} "
            f"failed={failed}/{total} ({fail_ratio:.0%})",
            file=sys.stderr,
        )

    if not candidates and systemic_candidates:
        completion_priority, retryable, age_seconds, type_id, folder, total, accepted, failed = max(systemic_candidates)
        print(
            f"SELECT systemic failed-only retry: Type {type_id} {folder} "
            f"reason=systemic_completion_backlog, accepted={accepted}/{total}, "
            f"retryable={retryable}, failed={failed}, "
            f"oldest_actionable_hours={age_seconds / 3600:.1f}",
            file=sys.stderr,
        )
        print(type_id)
        return

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
