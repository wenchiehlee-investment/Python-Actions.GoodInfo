#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self_update.py — 通用技能自我更新工具（Generic Skill Self-Updater）

從同目錄的 metadata.json 讀取所有設定，無需修改任何程式碼。
適用於任何遵循標準結構的 skill。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
使用方式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # 模式 A：從 GitHub 登錄庫拉取最新版本到本地副本
  python self_update.py

  # 模式 B：從本地登錄庫推送最新版本到所有已知部署副本，並 git commit + push
  python self_update.py --deploy-all
  python self_update.py --deploy-all --nas-root D:/SynologyDrive/NAS

  # 推送但跳過 git 操作（只複製檔案）
  python self_update.py --deploy-all --no-git

  # 僅列出所有已知部署副本（不做任何動作）
  python self_update.py --list-deployments

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
新技能建立步驟（3 步驟，無需修改此檔案）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 複製此 self_update.py 到新技能資料夾
  2. 建立 metadata.json，填入以下必要欄位：
       "registry" : GitHub URL（用於推導 REMOTE_REPO 與 SKILL_SUBPATH）
       "files"    : 此技能的所有檔案清單（相對路徑）
       "deployments": 所有部署副本的 local_path 清單
  3. 完成，無需修改 self_update.py 任何一行

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
metadata.json 標準結構（必要欄位）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {
    "name": "my-skill",
    "version": "1.0.0",
    "registry": "https://github.com/<owner>/skills/tree/main/common/skill-my-skill",
    "files": [
      "SKILL.md", "metadata.json", "self_update.py",
      "scripts/my_script.py"
    ],
    "deployments": [
      { "repo": "<owner>/skills",   "local_path": "github.com/skills/common/skill-my-skill", "role": "registry" },
      { "repo": "<owner>/ProjectA", "local_path": "github.com/ProjectA/skills/skill-my-skill", "role": "consumer" }
    ]
  }
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

# Fix Windows console encoding for Chinese characters
if platform.system() == "Windows":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Default NAS root（可被 --nas-root 覆蓋）──────────────────────────────────
_DEFAULT_NAS_ROOTS = [
    Path.home() / "SynologyDrive" / "NAS",
    Path("D:/SynologyDrive/NAS"),
    Path("C:/Users") / (Path.home().name) / "SynologyDrive" / "NAS",
]


def _find_default_nas_root() -> Path:
    for p in _DEFAULT_NAS_ROOTS:
        if p.exists():
            return p
    return Path.home() / "SynologyDrive" / "NAS"  # fallback


# ── metadata.json helpers ─────────────────────────────────────────────────────

def _load_local_meta(base_dir: Path) -> dict:
    meta_path = base_dir / "metadata.json"
    try:
        with open(meta_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[self_update] 無法讀取 metadata.json：{e}", file=sys.stderr)
        sys.exit(1)


def _parse_registry_url(registry_url: str) -> tuple[str, str, str]:
    """
    從 registry URL 解析出 REMOTE_REPO、SKILL_SUBPATH、SKILL_FOLDER_NAME。

    範例：
      https://github.com/wenchiehlee/skills/tree/main/common/skill-mlx-api-client-ocr
      → remote_repo    = "wenchiehlee/skills"
      → skill_subpath  = "common/skill-mlx-api-client-ocr"
      → folder_name    = "skill-mlx-api-client-ocr"
    """
    path = registry_url.replace("https://github.com/", "").strip("/")
    parts = path.split("/")
    if len(parts) < 5 or parts[2] != "tree":
        raise ValueError(f"無法解析 registry URL：{registry_url}")
    remote_repo = f"{parts[0]}/{parts[1]}"
    skill_subpath = "/".join(parts[4:])
    folder_name = parts[-1]
    return remote_repo, skill_subpath, folder_name


def _remote_raw_url(remote_repo: str, skill_subpath: str, relative_path: str) -> str:
    return f"https://raw.githubusercontent.com/{remote_repo}/main/{skill_subpath}/{relative_path}"


def _fetch_remote(remote_repo: str, skill_subpath: str, relative_path: str) -> bytes:
    url = _remote_raw_url(remote_repo, skill_subpath, relative_path)
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read()


def _parse_version(version: str) -> tuple:
    try:
        return tuple(int(p) for p in version.strip().split("."))
    except Exception:
        return (0, 0, 0)


def _content_hash(files: dict[str, bytes]) -> str:
    """Hash sorted relative paths and bytes so every platform gets one value."""
    digest = hashlib.sha256()
    for relative_path in sorted(files):
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(files[relative_path])
        digest.update(b"\0")
    return digest.hexdigest()


def _local_files(base_dir: Path, files: list[str]) -> tuple[dict[str, bytes], list[str]]:
    """Read declared local files and return bytes plus missing paths."""
    present: dict[str, bytes] = {}
    missing: list[str] = []
    for relative_path in files:
        path = base_dir / relative_path
        if path.is_file():
            present[relative_path] = path.read_bytes()
        else:
            missing.append(relative_path)
            present[relative_path] = b""
    return present, missing


def _git_skill_dirty(base_dir: Path, files: list[str]) -> bool:
    """Return whether declared skill files have uncommitted Git changes."""
    repo_root = _find_git_root(base_dir)
    if repo_root is None:
        return False
    ok, status = _git(
        ["status", "--porcelain", "--", str(base_dir.resolve().relative_to(repo_root))],
        cwd=repo_root,
    )
    return ok and bool(status.strip())


# ── Git helpers ───────────────────────────────────────────────────────────────

def _find_git_root(path: Path) -> Path | None:
    """從 path 向上尋找最近的 .git 目錄，回傳 git repo 根目錄。"""
    current = path.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def _git(args: list[str], cwd: Path, label: str = "") -> tuple[bool, str]:
    """執行 git 指令，回傳 (success, output)。"""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            tag = f"[git{' '+label if label else ''}]"
            print(f"  {tag} ✗ 失敗（rc={result.returncode}）: {output[:200]}", file=sys.stderr)
            return False, output
        return True, output
    except FileNotFoundError:
        print("  [git] ✗ git 指令不存在，請安裝 git。", file=sys.stderr)
        return False, ""


def _git_commit_and_push(target_dir: Path, skill_folder_name: str, version: str) -> bool:
    """
    在 target_dir 所屬的 git repo 中，
    將 skill 資料夾的變更 add → commit → pull --rebase → push。
    回傳是否成功。
    """
    repo_root = _find_git_root(target_dir)
    if repo_root is None:
        print(f"  [git] ✗ 找不到 git repo root（{target_dir}）", file=sys.stderr)
        return False

    # 計算 skill 資料夾相對於 repo root 的路徑
    rel_skill_path = target_dir.resolve().relative_to(repo_root)

    print(f"  [git] repo: {repo_root.name}  skill: {rel_skill_path}")

    # 1. git add <skill_folder>
    ok, _ = _git(["add", str(rel_skill_path)], cwd=repo_root, label="add")
    if not ok:
        return False

    # 2. 檢查是否有變更需要 commit
    ok, status = _git(["status", "--porcelain", str(rel_skill_path)], cwd=repo_root)
    if not status.strip():
        print(f"  [git] ~ 無變更，略過 commit + push")
        return True

    # 3. git commit
    commit_msg = f"chore: sync {skill_folder_name} to v{version}"
    ok, _ = _git(["commit", "-m", commit_msg], cwd=repo_root, label="commit")
    if not ok:
        return False
    print(f"  [git] ✓ commit: {commit_msg}")

    # 4. git pull --rebase --autostash
    #    --autostash：自動 stash repo 內其他未提交修改，rebase 後自動 pop
    #    解決「cannot pull with rebase: You have unstaged changes」錯誤
    ok, out = _git(["pull", "--rebase", "--autostash"], cwd=repo_root, label="pull --rebase")
    if not ok:
        print(f"  [git] ⚠️  pull --rebase --autostash 失敗，仍嘗試 push", file=sys.stderr)

    # 5. git push
    result = subprocess.run(
        ["git", "push"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    push_out = (result.stdout + result.stderr).strip()

    # LFS lock warning 會讓 rc=1 但實際 push 成功（輸出含 "Locking support detected"）
    lfs_warning_only = (
        result.returncode != 0
        and "Locking support detected" in push_out
        and ("->") in push_out  # 有實際推送的 ref
    )
    if result.returncode == 0 or lfs_warning_only:
        if lfs_warning_only:
            print(f"  [git] ✓ push 完成（LFS lock warning，已忽略）")
        else:
            print(f"  [git] ✓ push 完成")
        return True
    else:
        print(f"  [git push] ✗ 失敗（rc={result.returncode}）: {push_out[:300]}", file=sys.stderr)
        return False


# ── 模式 A：從 GitHub 拉取更新 ───────────────────────────────────────────────

def check_and_update(
    base_dir: Path,
    *,
    check_only: bool = False,
    repair_drift: bool = False,
    force: bool = False,
) -> bool:
    """Compare with the registry and optionally apply a safe full update."""
    meta = _load_local_meta(base_dir)
    registry_url = meta.get("registry", "")
    files: list[str] = meta.get("files", [])
    local_v: str = meta.get("version", "0.0.0")

    if not registry_url or not files:
        print("[self_update] metadata.json 缺少 registry 或 files。", file=sys.stderr)
        return False

    try:
        remote_repo, skill_subpath, _ = _parse_registry_url(registry_url)
        remote_meta = json.loads(
            _fetch_remote(remote_repo, skill_subpath, "metadata.json").decode("utf-8")
        )
    except Exception as e:
        print(f"[self_update] 無法取得登錄庫 metadata：{e}", file=sys.stderr)
        return False

    remote_v: str = remote_meta.get("version", "0.0.0")
    remote_files: list[str] = remote_meta.get("files", files)
    fetched: dict[str, bytes] = {}
    for relative_path in remote_files:
        try:
            fetched[relative_path] = _fetch_remote(remote_repo, skill_subpath, relative_path)
        except Exception as e:
            print(f"[self_update] 下載失敗 {relative_path}: {e}", file=sys.stderr)
            return False

    local_data, missing = _local_files(base_dir, remote_files)
    local_hash = _content_hash(local_data)
    remote_hash = _content_hash(fetched)
    version_cmp = (_parse_version(remote_v) > _parse_version(local_v)) - (
        _parse_version(remote_v) < _parse_version(local_v)
    )
    drift = bool(missing) or local_hash != remote_hash

    print(f"[self_update] Registry : v{remote_v} sha256:{remote_hash[:16]}")
    print(f"[self_update] Local    : v{local_v} sha256:{local_hash[:16]}")
    if missing:
        print(f"[self_update] Missing  : {', '.join(missing)}")
    print(f"[self_update] Status   : {'content drift' if drift else 'synchronized'}")

    if check_only:
        return version_cmp == 0 and not drift
    if version_cmp < 0 and not force:
        print("[self_update] 拒絕降級；如確定要降級請使用 --force。", file=sys.stderr)
        return False
    if version_cmp == 0 and not drift:
        print(f"[self_update] 已是最新版本（本地 {local_v}，登錄庫 {remote_v}）")
        return False
    if version_cmp == 0 and drift and not repair_drift and not force:
        print("[self_update] 偵測到同版本內容漂移；請使用 --repair-drift。", file=sys.stderr)
        return False
    if drift and _git_skill_dirty(base_dir, remote_files) and not force:
        print("[self_update] skill 有未提交變更；請先提交或使用 --force。", file=sys.stderr)
        return False

    reason = f"{local_v} → {remote_v}" if version_cmp > 0 else f"同版本 {remote_v} 内容修復"
    print(f"[self_update] 開始同步（{reason}）…")
    backups: dict[Path, bytes] = {}
    written: list[Path] = []
    try:
        for relative_path, data in fetched.items():
            destination = base_dir / relative_path
            if destination.exists():
                backups[destination] = destination.read_bytes()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=destination.parent, delete=False
            ) as temporary:
                temporary.write(data)
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, destination)
            written.append(destination)
    except Exception as e:
        for destination in written:
            if destination in backups:
                destination.write_bytes(backups[destination])
            elif destination.exists():
                destination.unlink()
        print(f"[self_update] 更新失敗，已回復：{e}", file=sys.stderr)
        return False

    print(f"[self_update] 更新完成（{remote_v}，sha256:{remote_hash[:16]}）")
    return True


# ── 模式 B：推送到所有部署副本 ───────────────────────────────────────────────

def deploy_all(nas_root: Path, no_git: bool = False) -> None:
    """
    從本地登錄庫推送最新版本到 metadata.json deployments 清單中的所有 consumer 副本，
    並對每個 consumer repo 執行 git add + commit + push。
    """
    registry_dir = Path(__file__).resolve().parent
    meta = _load_local_meta(registry_dir)

    registry_version: str = meta.get("version", "0.0.0")
    files: list[str] = meta.get("files", [])
    deployments: list[dict] = meta.get("deployments", [])
    registry_url: str = meta.get("registry", "")
    skill_name: str = meta.get("name", "unknown")

    if not files:
        print("[deploy-all] metadata.json 缺少 'files' 欄位，無法同步。", file=sys.stderr)
        return
    if not deployments:
        print("[deploy-all] metadata.json 缺少 'deployments' 欄位，無部署副本可同步。")
        return

    try:
        _, _, skill_folder_name = _parse_registry_url(registry_url)
    except ValueError as e:
        print(f"[deploy-all] {e}", file=sys.stderr)
        return

    consumers = [d for d in deployments if d.get("role") != "registry"]
    print(f"[deploy-all] Skill  : {skill_name} v{registry_version}")
    print(f"[deploy-all] 資料夾 : {skill_folder_name}")
    print(f"[deploy-all] Git     : {'停用 (--no-git)' if no_git else '啟用（自動 commit + push）'}")
    print(f"[deploy-all] 副本數  : {len(consumers)}\n")

    success, skipped, git_failed = 0, 0, 0

    for dep in consumers:
        local_path = dep.get("local_path", "")
        repo = dep.get("repo", "")
        target_dir = nas_root / local_path

        print(f"── [{repo}] ──────────────────────────────")

        # 若目標路徑不存在，在同層目錄尋找舊名稱
        if not target_dir.exists():
            parent = target_dir.parent
            if not parent.exists():
                print(f"  ✗ parent 目錄不存在：{parent}", file=sys.stderr)
                skipped += 1
                continue
            old_candidates = [
                d for d in parent.iterdir()
                if d.is_dir() and d.name != skill_folder_name
                and any(kw in d.name.lower() for kw in ["skill", "ocr", "mlx", "whisper", "mac"])
            ]
            if len(old_candidates) == 1:
                old_dir = old_candidates[0]
                print(f"  重命名: {old_dir.name} → {skill_folder_name}")
                old_dir.rename(target_dir)
            elif len(old_candidates) == 0:
                print(f"  目標不存在，建立新目錄")
                target_dir.mkdir(parents=True, exist_ok=True)
            else:
                names = [d.name for d in old_candidates]
                print(f"  ✗ 找到多個候選舊資料夾，無法自動判斷：{names}", file=sys.stderr)
                skipped += 1
                continue

        # 若資料夾名稱不符，重命名
        if target_dir.exists() and target_dir.name != skill_folder_name:
            new_target = target_dir.parent / skill_folder_name
            print(f"  重命名: {target_dir.name} → {skill_folder_name}")
            target_dir.rename(new_target)
            target_dir = new_target

        # 同步所有檔案（從 registry 複製到副本）
        dep_version = "?"
        meta_file = target_dir / "metadata.json"
        if meta_file.exists():
            try:
                dep_version = json.loads(meta_file.read_text(encoding="utf-8")).get("version", "?")
            except Exception:
                pass

        print(f"  檔案同步: v{dep_version} → v{registry_version}")
        for rel_path in files:
            src = registry_dir / rel_path
            dst = target_dir / rel_path
            if src.exists():
                try:
                    if src.resolve() == dst.resolve():
                        print(f"  ~ {rel_path}（來源與目標相同，略過）")
                        continue
                except Exception:
                    pass
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print(f"  ✓ {rel_path}")
            else:
                print(f"  ✗ 來源不存在：{rel_path}", file=sys.stderr)

        # Git commit + push
        if no_git:
            print(f"  [git] 略過（--no-git）")
        else:
            git_ok = _git_commit_and_push(target_dir, skill_folder_name, registry_version)
            if not git_ok:
                git_failed += 1

        success += 1
        print()

    # 也對 registry 本身 commit + push
    if not no_git:
        print(f"── [registry] ──────────────────────────────")
        _git_commit_and_push(registry_dir, skill_folder_name, registry_version)
        print()

    print("━" * 50)
    print(f"[deploy-all] 完成：{success} 同步，{skipped} 略過，{git_failed} git 失敗")


# ── 模式 C：列出所有部署副本 ─────────────────────────────────────────────────

def list_deployments(nas_root: Path) -> None:
    """列出所有已知部署副本及其版本狀態。"""
    registry_dir = Path(__file__).resolve().parent
    meta = _load_local_meta(registry_dir)
    deployments: list[dict] = meta.get("deployments", [])
    registry_version: str = meta.get("version", "0.0.0")

    print(f"Skill: {meta.get('name')} — Registry v{registry_version}")
    print(f"{'Role':<10} {'Repo':<35} {'Version':<10} {'Status'}")
    print("-" * 75)
    for dep in deployments:
        local_path = dep.get("local_path", "")
        repo = dep.get("repo", "?")
        role = dep.get("role", "consumer")
        target_dir = nas_root / local_path
        meta_file = target_dir / "metadata.json"
        if meta_file.exists():
            dep_v = json.loads(open(meta_file, encoding="utf-8").read()).get("version", "?")
            ok = "✅ up-to-date" if dep_v == registry_version else f"⚠️  outdated ({dep_v})"
        else:
            dep_v = "—"
            ok = "❌ not found" if not target_dir.exists() else "⚠️  no metadata"
        print(f"{role:<10} {repo:<35} {dep_v:<10} {ok}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="通用技能自我更新工具 — 從 metadata.json 讀取所有設定",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--deploy-all",
        action="store_true",
        help="從本地登錄庫推送最新版本到所有已知部署副本，並自動 git commit + push",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="與 --deploy-all 搭配使用：只複製檔案，跳過 git commit + push",
    )
    parser.add_argument(
        "--list-deployments",
        action="store_true",
        help="列出所有已知部署副本及其版本狀態",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="只檢查版本與內容 hash，不修改檔案；不一致時返回非零",
    )
    parser.add_argument(
        "--repair-drift",
        action="store_true",
        help="修復相同版本但內容不同的 skill 檔案",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="允許覆寫未提交變更或降級；請謹慎使用",
    )
    parser.add_argument(
        "--nas-root",
        type=Path,
        default=None,
        help="NAS 根目錄路徑（預設自動偵測，通常為 ~/SynologyDrive/NAS）",
    )
    args = parser.parse_args()

    nas_root = args.nas_root or _find_default_nas_root()

    if args.deploy_all:
        deploy_all(nas_root, no_git=args.no_git)
    elif args.list_deployments:
        list_deployments(nas_root)
    else:
        base_dir = Path(__file__).resolve().parent
        ok = check_and_update(
            base_dir,
            check_only=args.check,
            repair_drift=args.repair_drift,
            force=args.force,
        )
        if args.check and not ok:
            raise SystemExit(1)
