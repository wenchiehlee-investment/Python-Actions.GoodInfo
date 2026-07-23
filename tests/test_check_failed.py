import csv
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import check_failed


FIELDNAMES = [
    "filename",
    "last_update_time",
    "success",
    "process_time",
    "retry_count",
    "status",
    "error_reason",
]


def write_results(folder, rows):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "download_results.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def row(status):
    return {
        "filename": "sample.xls",
        "last_update_time": "2026-07-01 00:00:00 CST",
        "success": "true" if status == "success" else "false",
        "process_time": "2026-07-01 00:00:00 CST",
        "retry_count": "1",
        "status": status,
        "error_reason": "",
    }


def run_main_in(path):
    old_cwd = os.getcwd()
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        os.chdir(path)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            check_failed.main()
    finally:
        os.chdir(old_cwd)
    return stdout.getvalue().strip(), stderr.getvalue()


class CheckFailedSelectionTest(unittest.TestCase):
    def test_regular_candidate_still_wins_before_systemic_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            write_results(
                os.path.join(tmpdir, "ShowSaleMonChart"),
                [row("success")] + [row("retryable_failed") for _ in range(132)],
            )
            write_results(
                os.path.join(tmpdir, "Dividenschedule"),
                [row("success") for _ in range(130)] + [row("retryable_failed") for _ in range(3)],
            )

            selected, diagnostics = run_main_in(tmpdir)

        self.assertEqual(selected, "19")
        self.assertIn("SKIP systemic failure candidate: Type 5", diagnostics)
        self.assertIn("SELECT failed-only retry: Type 19", diagnostics)

    def test_systemic_completion_backlog_is_selected_when_no_regular_candidate_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            write_results(
                os.path.join(tmpdir, "WeeklyTradingData"),
                [row("retryable_failed") for _ in range(133)],
            )

            selected, diagnostics = run_main_in(tmpdir)

        self.assertEqual(selected, "11")
        self.assertIn("SKIP systemic failure candidate: Type 11", diagnostics)
        self.assertIn("SELECT systemic failed-only retry: Type 11", diagnostics)


if __name__ == "__main__":
    unittest.main()
