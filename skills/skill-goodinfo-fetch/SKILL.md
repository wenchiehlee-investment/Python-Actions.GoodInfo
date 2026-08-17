---
name: skill-goodinfo-fetch
description: GoodInfo.tw 台股資料三段式管線（下載 XLS → 轉換 CSV → 公司層級富化）的統一入口技能，同一份技能同步部署於 Python-Actions.GoodInfo、Python-Actions.GoodInfo.Analyzer、Python-Actions.GoodInfo.CompanyInfo 三個 repo。
---

# GoodInfo Fetch Skill（GoodInfo 資料擷取三段式管線）

這是一個**跨三個 repo 共用**的技能，由兩層組成：

- **同步層**（三 repo 完全相同副本）：`SKILL.md` / `metadata.json` / `self_update.py` / `scripts/goodinfo_pipeline.py`，由 registry 的 `self_update.py --deploy-all` 推送，內容三 repo 一致。
- **kernel 層**（repo 專屬，不同步）：`kernel/` 下放置該 repo 實際下載/轉換/富化用的核心腳本（原本放在各 repo 根目錄，現已搬移至此）。`kernel/` **不列在 `metadata.json` 的 `files` 清單中**，因此同步機制不會互相覆寫或搬運彼此的 kernel 腳本，三 repo 的 `kernel/` 內容各自獨立。

`scripts/goodinfo_pipeline.py` 是一支**薄 wrapper（thin dispatcher）**：它不重新實作任何抓取/轉換邏輯，只依照自身檔案位置找到同層的 `../kernel/`，偵測目前 repo 擁有哪些 kernel 腳本，並用 subprocess 呼叫（cwd 固定在 repo root，維持原本以 cwd 為準的相對路徑輸出行為）。三段管線分屬三個獨立 repo：

## 三段式管線總覽

| 段 | Repo | 角色 | 輸入 → 輸出 | kernel 腳本（`skills/skill-goodinfo-fetch/kernel/`） |
| -- | -- | -- | -- | -- |
| ① download | `Python-Actions.GoodInfo` | 用 Selenium 從 GoodInfo.tw 下載原始報表，19 種資料類型（股利、營收、股權結構、K線、融資券…） | GoodInfo.tw 網頁 → `<Type資料夾>/*_{stock_id}_{name}.xls` | `GetAll.py`（批次）/ `GetGoodInfo.py`（單檔）/ `Get觀察名單.py`（股票清單） |
| ② convert | `Python-Actions.GoodInfo.Analyzer` | Stage1 Extraction：把 18 種類型的 `.xls` 解析、清洗欄位、轉成結構化 CSV | 各 `<Type資料夾>/*.xls` → `data/stage1_raw/raw_*.csv` | `stage1_excel_to_csv_html.py`（原路徑 `src/pipelines/stage1_excel_to_csv_html.py`） |
| ③ enrich | `Python-Actions.GoodInfo.CompanyInfo` | **不是 xls→csv 鏈的延續**，而是獨立的公司層級 metadata 富化：GoodInfo 主要業務/市值 + TWSE ISIN 產業別/市場別 + MoneyDJ ETF 權重 + TAIFEX 大盤佔比 + Gemini 概念股判斷 | 觀察名單 + GoodInfo + isin.twse.com.tw + MoneyDJ + TAIFEX → `raw_companyinfo.csv` | `FetchCompanyInfo.py` / `Get觀察名單.py` |

> Analyzer repo 內雖仍留有 stage2~stage6（cleaning/analysis/calibration/validation/dashboard）的程式與文件，但**目前只有 stage1（本技能的 ② convert）在實際使用**，其餘階段已不再需要，本技能與此 wrapper 也只涵蓋 stage1。`raw_companyinfo.csv`（③ 的輸出）與 `data/stage1_raw/raw_*.csv`（② 的輸出）彼此平行、無先後相依，不需要依序執行。

## 適用場景

- 需要在任一 GoodInfo 相關 repo 中，快速判斷「這裡負責管線的哪一段」以及「該呼叫哪支腳本」。
- 需要跨 repo 觸發下載/轉換/富化其中一段，且不想手動記憶三個 repo 各自的腳本路徑與參數格式。
- 需要理解某個 CSV 欄位或資料類型，是源自哪一段管線、哪個原始腳本。

## 核心腳本與指令

技能的統一入口是技能目錄下的 `scripts/goodinfo_pipeline.py`。它會偵測 `skills/skill-goodinfo-fetch/kernel/` 下實際存在哪些腳本，藉此判斷目前 repo 對應哪一段，並代為呼叫該 kernel 腳本。若目前 repo 與指定 stage 不符，會直接報錯並提示應在哪個 repo 執行。指令一律從 repo root 執行（例如 `python skills/skill-goodinfo-fetch/scripts/goodinfo_pipeline.py ...`），與搬移前直接 `python GetAll.py ...` 的執行位置相同。

### ① download — 在 `Python-Actions.GoodInfo` 執行

```bash
# 批次下載某資料類型（DATA_TYPE = 1~19），選項會原封不動轉給 GetAll.py
python scripts/goodinfo_pipeline.py download <DATA_TYPE> [--test] [--debug] [--direct] [--failed-only]

# 下載單一股票單一資料類型
python scripts/goodinfo_pipeline.py download-one <STOCK_ID> <DATA_TYPE>

# 更新觀察名單（股票代號清單）
python scripts/goodinfo_pipeline.py update-watchlist
```

### ② convert — 在 `Python-Actions.GoodInfo.Analyzer` 執行

```bash
# Stage1 Extraction：xls → data/stage1_raw/raw_*.csv，選項原封不動轉給 stage1_excel_to_csv_html.py
python scripts/goodinfo_pipeline.py convert [--output-dir data/stage1_raw] [--stock-id-file StockID_TWSE_TPEX.csv] [--debug]
```

### ③ enrich — 在 `Python-Actions.GoodInfo.CompanyInfo` 執行

```bash
# 更新觀察名單
python scripts/goodinfo_pipeline.py update-watchlist

# 擷取並富化公司層級 metadata → raw_companyinfo.csv（無額外參數，需先設定 GEMINI_API_KEY 環境變數才能啟用概念股判斷）
python scripts/goodinfo_pipeline.py enrich
```

### 通用：查詢目前 repo 對應哪一段

```bash
python scripts/goodinfo_pipeline.py status
```

## 依賴需求

依段落不同，需要目前所在 repo 既有的 `requirements.txt`（`pandas`、`requests`、`beautifulsoup4`、`selenium` / `undetected-chromedriver`、`webdriver-manager`，③ 另需 `google-genai`、`python-dotenv`）。本 wrapper 本身除 Python 標準函式庫外無額外依賴。

## 注意事項

- 此 wrapper 不會跨 repo 遠端呼叫；三段各自必須在**該段所屬的 repo 目錄**下執行（或透過 NAS 相對路徑找得到該 repo）。
- ① 的 GoodInfo.tw 下載使用 Selenium + Chrome，需本機/CI 環境已安裝 Chrome。
- ③ 的 Gemini 概念股判斷為選用功能，未設定 `GEMINI_API_KEY` 時會自動略過。
