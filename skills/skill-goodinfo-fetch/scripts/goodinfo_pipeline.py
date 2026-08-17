#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
goodinfo_pipeline.py — GoodInfo 三段式管線統一 dispatcher（薄 wrapper）

不重新實作任何抓取/轉換邏輯，只負責：
  1. 依照本檔案所在位置，找出各段的 kernel 腳本（skills/skill-goodinfo-fetch/kernel/ 下，
     repo 專屬，不隨 skill 同步機制推送/覆寫——不列在 metadata.json 的 files 清單中）
  2. 確認呼叫的 stage 是否與目前 repo 擁有的 kernel 腳本相符
  3. 用 subprocess 呼叫該 kernel 腳本（cwd 固定在 repo root，確保輸出/資料檔相對路徑不變）

目錄慣例（由 metadata.json 的 deployments.local_path 決定）：
  <repo_root>/skills/skill-goodinfo-fetch/scripts/goodinfo_pipeline.py   <- 本檔案，三 repo 同步
  <repo_root>/skills/skill-goodinfo-fetch/kernel/...                     <- repo 專屬，不同步

Stages:
  download        Python-Actions.GoodInfo             → kernel/GetAll.py <DATA_TYPE> [options]
  download-one    Python-Actions.GoodInfo             → kernel/GetGoodInfo.py <STOCK_ID> <DATA_TYPE>
  convert         Python-Actions.GoodInfo.Analyzer    → kernel/stage1_excel_to_csv_html.py [options]
  enrich          Python-Actions.GoodInfo.CompanyInfo → kernel/FetchCompanyInfo.py
  update-watchlist (GoodInfo 或 CompanyInfo)           → kernel/Get觀察名單.py
  status          印出目前偵測到的 repo 與對應段落
"""
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding for Chinese characters
if platform.system() == "Windows":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent   # .../skills/skill-goodinfo-fetch/scripts
SKILL_DIR = SCRIPT_DIR.parent                  # .../skills/skill-goodinfo-fetch
KERNEL_DIR = SKILL_DIR / "kernel"              # repo 專屬，不同步
REPO_ROOT = SKILL_DIR.parent.parent            # repo root

KERNEL_MARKERS = {
    "goodinfo": ("GetAll.py", "GetGoodInfo.py"),
    "analyzer": ("stage1_excel_to_csv_html.py",),
    "companyinfo": ("FetchCompanyInfo.py",),
}

STAGE_TO_REPO = {
    "download": "goodinfo",
    "download-one": "goodinfo",
    "convert": "analyzer",
    "enrich": "companyinfo",
}

STAGE_LABEL = {
    "goodinfo": "① download — Python-Actions.GoodInfo（kernel/GetAll.py / kernel/GetGoodInfo.py）",
    "analyzer": "② convert — Python-Actions.GoodInfo.Analyzer（kernel/stage1_excel_to_csv_html.py）",
    "companyinfo": "③ enrich — Python-Actions.GoodInfo.CompanyInfo（kernel/FetchCompanyInfo.py）",
}


def detect_repo_kind() -> str | None:
    for kind, markers in KERNEL_MARKERS.items():
        if any((KERNEL_DIR / m).exists() for m in markers):
            return kind
    return None


def run(cmd: list[str]) -> int:
    print(f"[goodinfo_pipeline] $ {' '.join(cmd)}  (cwd={REPO_ROOT})")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def cmd_download(args: argparse.Namespace, extra: list[str]) -> int:
    return run([sys.executable, str(KERNEL_DIR / "GetAll.py"), args.data_type, *extra])


def cmd_download_one(args: argparse.Namespace, extra: list[str]) -> int:
    return run([sys.executable, str(KERNEL_DIR / "GetGoodInfo.py"), args.stock_id, args.data_type, *extra])


def cmd_convert(args: argparse.Namespace, extra: list[str]) -> int:
    cmd = [sys.executable, str(KERNEL_DIR / "stage1_excel_to_csv_html.py")]
    if args.output_dir:
        cmd += ["--output-dir", args.output_dir]
    if args.stock_id_file:
        cmd += ["--stock-id-file", args.stock_id_file]
    if args.debug:
        cmd += ["--debug"]
    cmd += extra
    return run(cmd)


def cmd_enrich(args: argparse.Namespace, extra: list[str]) -> int:
    return run([sys.executable, str(KERNEL_DIR / "FetchCompanyInfo.py"), *extra])


def cmd_update_watchlist(args: argparse.Namespace, extra: list[str]) -> int:
    script = KERNEL_DIR / "Get觀察名單.py"
    if not script.exists():
        print(f"[goodinfo_pipeline] 找不到 {script}", file=sys.stderr)
        return 1
    return run([sys.executable, str(script), *extra])


def cmd_status(repo_kind: str | None) -> int:
    if repo_kind is None:
        print(f"[goodinfo_pipeline] 未偵測到任何已知的 kernel 腳本（{KERNEL_DIR} 為空或不存在）")
        return 1
    print(f"[goodinfo_pipeline] repo root : {REPO_ROOT}")
    print(f"[goodinfo_pipeline] kernel dir: {KERNEL_DIR}")
    print(f"[goodinfo_pipeline] 對應段落  : {STAGE_LABEL[repo_kind]}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GoodInfo 三段式管線統一 dispatcher（薄 wrapper，呼叫本 repo 的 kernel/ 腳本）",
    )
    sub = parser.add_subparsers(dest="stage", required=True)

    p_dl = sub.add_parser("download", help="① 批次下載（Python-Actions.GoodInfo / kernel/GetAll.py）")
    p_dl.add_argument("data_type", help="DATA_TYPE 1~19")

    p_dl1 = sub.add_parser("download-one", help="① 下載單一股票單一類型（kernel/GetGoodInfo.py）")
    p_dl1.add_argument("stock_id")
    p_dl1.add_argument("data_type")

    p_cv = sub.add_parser("convert", help="② xls → CSV（Python-Actions.GoodInfo.Analyzer / stage1）")
    p_cv.add_argument("--output-dir", default=None)
    p_cv.add_argument("--stock-id-file", default=None)
    p_cv.add_argument("--debug", action="store_true")

    sub.add_parser("enrich", help="③ 公司層級 metadata 富化（Python-Actions.GoodInfo.CompanyInfo）")
    sub.add_parser("update-watchlist", help="更新觀察名單（GoodInfo 或 CompanyInfo repo 皆可）")
    sub.add_parser("status", help="印出目前偵測到的 repo 與對應段落")

    args, extra = parser.parse_known_args()

    repo_kind = detect_repo_kind()

    if args.stage == "status":
        return cmd_status(repo_kind)

    if repo_kind is None:
        print(f"[goodinfo_pipeline] 未偵測到任何已知的 kernel 腳本（{KERNEL_DIR}）。"
              f"請確認 skills/skill-goodinfo-fetch/kernel/ 下已有該 repo 的腳本。", file=sys.stderr)
        return 1

    if args.stage in STAGE_TO_REPO and STAGE_TO_REPO[args.stage] != repo_kind:
        expected = STAGE_TO_REPO[args.stage]
        print(f"[goodinfo_pipeline] stage '{args.stage}' 應在 {expected} repo 下執行，"
              f"但目前偵測到的是 {repo_kind}（{KERNEL_DIR}）。", file=sys.stderr)
        return 1

    if args.stage == "download":
        return cmd_download(args, extra)
    if args.stage == "download-one":
        return cmd_download_one(args, extra)
    if args.stage == "convert":
        return cmd_convert(args, extra)
    if args.stage == "enrich":
        return cmd_enrich(args, extra)
    if args.stage == "update-watchlist":
        return cmd_update_watchlist(args, extra)

    parser.error(f"未知 stage: {args.stage}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
