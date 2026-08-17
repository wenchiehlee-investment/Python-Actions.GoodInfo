#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
goodinfo_pipeline.py — GoodInfo 三段式管線統一 dispatcher（薄 wrapper）

不重新實作任何抓取/轉換邏輯，只負責：
  1. 偵測目前所在的 repo root（往上尋找 GetAll.py / stage1_excel_to_csv_html.py / FetchCompanyInfo.py）
  2. 確認呼叫的 stage 是否與偵測到的 repo 相符
  3. 用 subprocess 呼叫該 repo 既有的原生腳本，並原封不動轉發剩餘參數

Stages:
  download        Python-Actions.GoodInfo            → GetAll.py <DATA_TYPE> [options]
  download-one    Python-Actions.GoodInfo            → GetGoodInfo.py <STOCK_ID> <DATA_TYPE>
  convert         Python-Actions.GoodInfo.Analyzer   → src/pipelines/stage1_excel_to_csv_html.py [options]
  enrich          Python-Actions.GoodInfo.CompanyInfo → FetchCompanyInfo.py
  update-watchlist (GoodInfo 或 CompanyInfo)          → Get觀察名單.py
  status          印出目前偵測到的 repo 與可用 stage
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

# repo root 標記檔（相對於 repo root），用來判斷目前站在哪個 repo
REPO_MARKERS = {
    "goodinfo": ("GetAll.py", "GetGoodInfo.py"),
    "analyzer": ("src/pipelines/stage1_excel_to_csv_html.py",),
    "companyinfo": ("FetchCompanyInfo.py",),
}

STAGE_TO_REPO = {
    "download": "goodinfo",
    "download-one": "goodinfo",
    "convert": "analyzer",
    "enrich": "companyinfo",
}


def find_repo_root(start: Path) -> tuple[Path, str] | tuple[None, None]:
    """從 start 往上找，回傳 (repo_root, repo_kind)，找不到回傳 (None, None)。"""
    current = start.resolve()
    for parent in [current, *current.parents]:
        for kind, markers in REPO_MARKERS.items():
            if any((parent / m).exists() for m in markers):
                return parent, kind
    return None, None


def run(cmd: list[str], cwd: Path) -> int:
    print(f"[goodinfo_pipeline] $ {' '.join(cmd)}  (cwd={cwd})")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def cmd_download(args: argparse.Namespace, repo_root: Path, extra: list[str]) -> int:
    cmd = [sys.executable, "GetAll.py", args.data_type, *extra]
    return run(cmd, repo_root)


def cmd_download_one(args: argparse.Namespace, repo_root: Path, extra: list[str]) -> int:
    cmd = [sys.executable, "GetGoodInfo.py", args.stock_id, args.data_type, *extra]
    return run(cmd, repo_root)


def cmd_convert(args: argparse.Namespace, repo_root: Path, extra: list[str]) -> int:
    cmd = [sys.executable, "src/pipelines/stage1_excel_to_csv_html.py"]
    if args.output_dir:
        cmd += ["--output-dir", args.output_dir]
    if args.stock_id_file:
        cmd += ["--stock-id-file", args.stock_id_file]
    if args.debug:
        cmd += ["--debug"]
    cmd += extra
    return run(cmd, repo_root)


def cmd_enrich(args: argparse.Namespace, repo_root: Path, extra: list[str]) -> int:
    cmd = [sys.executable, "FetchCompanyInfo.py", *extra]
    return run(cmd, repo_root)


def cmd_update_watchlist(args: argparse.Namespace, repo_root: Path, extra: list[str]) -> int:
    script = repo_root / "Get觀察名單.py"
    if not script.exists():
        print(f"[goodinfo_pipeline] 找不到 Get觀察名單.py（{repo_root}）", file=sys.stderr)
        return 1
    cmd = [sys.executable, "Get觀察名單.py", *extra]
    return run(cmd, repo_root)


def cmd_status(args: argparse.Namespace, repo_root: Path | None, repo_kind: str | None) -> int:
    if repo_root is None:
        print("[goodinfo_pipeline] 未偵測到任何已知的 GoodInfo 系列 repo（GetAll.py / "
              "stage1_excel_to_csv_html.py / FetchCompanyInfo.py 皆不存在於任何上層目錄）")
        return 1
    label = {
        "goodinfo": "① download — Python-Actions.GoodInfo（GetAll.py / GetGoodInfo.py）",
        "analyzer": "② convert — Python-Actions.GoodInfo.Analyzer（stage1_excel_to_csv_html.py）",
        "companyinfo": "③ enrich — Python-Actions.GoodInfo.CompanyInfo（FetchCompanyInfo.py）",
    }[repo_kind]
    print(f"[goodinfo_pipeline] repo root : {repo_root}")
    print(f"[goodinfo_pipeline] 對應段落  : {label}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GoodInfo 三段式管線統一 dispatcher（薄 wrapper，呼叫各 repo 既有腳本）",
    )
    sub = parser.add_subparsers(dest="stage", required=True)

    p_dl = sub.add_parser("download", help="① 批次下載（Python-Actions.GoodInfo / GetAll.py）")
    p_dl.add_argument("data_type", help="DATA_TYPE 1~19")

    p_dl1 = sub.add_parser("download-one", help="① 下載單一股票單一類型（GetGoodInfo.py）")
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

    repo_root, repo_kind = find_repo_root(Path.cwd())

    if args.stage == "status":
        return cmd_status(args, repo_root, repo_kind)

    if repo_root is None:
        print("[goodinfo_pipeline] 未偵測到任何已知的 GoodInfo 系列 repo，請在對應 repo 目錄下執行。",
              file=sys.stderr)
        return 1

    if args.stage in STAGE_TO_REPO and STAGE_TO_REPO[args.stage] != repo_kind:
        expected = STAGE_TO_REPO[args.stage]
        print(f"[goodinfo_pipeline] stage '{args.stage}' 應在 {expected} repo 下執行，"
              f"但目前偵測到的是 {repo_kind}（{repo_root}）。", file=sys.stderr)
        return 1

    if args.stage == "download":
        return cmd_download(args, repo_root, extra)
    if args.stage == "download-one":
        return cmd_download_one(args, repo_root, extra)
    if args.stage == "convert":
        return cmd_convert(args, repo_root, extra)
    if args.stage == "enrich":
        return cmd_enrich(args, repo_root, extra)
    if args.stage == "update-watchlist":
        return cmd_update_watchlist(args, repo_root, extra)

    parser.error(f"未知 stage: {args.stage}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
