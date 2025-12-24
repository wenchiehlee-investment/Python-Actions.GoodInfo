# GEMINI Code Companion Documentation for Python-Actions.GoodInfo

This document provides a streamlined overview for developers and AI agents to understand, run, and contribute to this project.

## 1. Project Overview

This repository contains a set of Python scripts designed to automatically download 16 different types of stock data from the Taiwanese stock information website, `GoodInfo.tw`.

It uses a web scraping approach with `Selenium` and `undetected-chromedriver` to simulate a user clicking the "Export to XLS" buttons on the website. The project is designed for automation, with built-in scheduling via GitHub Actions and intelligent tracking of downloaded files.

## 2. Core Components

*   **`GetGoodInfo.py`**: The main engine. A command-line script that downloads a specific data type for a single stock ID.
*   **`GetAll.py`**: The batch processor. This script iterates through a list of stock IDs and calls `GetGoodInfo.py` for each one. It has a "CSV-ONLY" freshness policy, meaning it checks a `download_results.csv` log file to decide if a stock's data needs updating (failed previously or older than 24 hours).
*   **`Get觀察名單.py`**: A utility script to download the master list of stock IDs (`StockID_TWSE_TPEX.csv`) from an external GitHub source. This list is augmented with "加權指數" (TAIEX) by default for comprehensive market-level analysis.
*   **Data Directories**: Folders like `DividendDetail/`, `ShowMarginChart/`, etc., where the downloaded 16 categories of `.xls` files and `download_results.csv` logs are stored.
*   **GitHub Actions Workflows**:
    *   **`Actions.yaml`**: The main automation scheduler that runs `GetAll.py` for different data types on a predefined weekly, daily, and monthly schedule, including a cleanup step for unwanted files.
    *   **`sync.yaml`**: A workflow for syncing generated output data to other repositories.

## 3. Getting Started

### 3.1. Prerequisites

*   Python 3.x
*   Google Chrome browser installed.

### 3.2. Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/wenchiehlee/Python-Actions.GoodInfo.git
    cd Python-Actions.GoodInfo
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download the stock list:**
    ```bash
    python Get觀察名單.py
    ```

### 3.3. Manual Usage

#### Download data for a single stock:

The script takes a stock ID (numeric or "加權指數") and a numeric data type code (1-16).

```bash
# Example: Download monthly revenue (Type 5) for TSMC (2330)
python GetGoodInfo.py 2330 5

# Example: Download daily margin balance (Type 13) for TAIEX (加權指數)
python GetGoodInfo.py 加權指數 13
```

#### Batch download for all stocks:

This is the primary script for bulk updates.

```bash
# Example: Download monthly revenue (Type 5) for all stocks
python GetAll.py 5

# Example: Run in test mode (only processes the first 3 stocks)
python GetAll.py 5 --test
```

## 4. Key Architectural Points

*   **Decoupled Scripts**: `GetGoodInfo.py` handles the atomic download task, while `GetAll.py` manages the batch logic. This is a clean separation of concerns.
*   **Stateful Batch Processing**: `GetAll.py` is not stateless. It relies on the `download_results.csv` in each data directory to know what to do. This prevents re-downloading fresh data and allows it to retry failed jobs.
*   **"CSV-ONLY" Freshness Policy**: The decision to process a stock is based exclusively on the content of `download_results.csv` (status and timestamp), not the file modification time of the `.xls` files. This is crucial for making the logic work correctly in CI/CD pipelines where all files might have recent timestamps.
*   **Robustness**: The downloader (`GetGoodInfo.py`) has multiple fallback methods to find the download button, and the batch processor (`GetAll.py`) has a multi-attempt retry mechanism. GitHub Actions workflows also include a cleanup step for unwanted temporary files.

## 5. Automation

The repository uses GitHub Actions workflows to run `GetAll.py` on a schedule. The schedule is designed to distribute the load on the `GoodInfo.tw` server by downloading 16 different data types on predefined weekly, daily, and monthly schedules.

*   **File**: The main scheduler workflow is defined in `.github/workflows/Actions.yaml`. The syncing workflow is `.github/workflows/sync.yaml`.
*   **Triggers**: The workflows run on a `schedule` (cron) and can also be triggered manually (`workflow_dispatch`).
*   **Logic**: The scheduler script determines which `DATA_TYPE` to run based on the day and time, encompassing all 16 types and including cleanup logic.
