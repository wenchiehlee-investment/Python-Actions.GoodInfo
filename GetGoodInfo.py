#!/usr/bin/env python3
"""
GetGoodInfo.py - Enhanced with Complete 18 Data Types including K-Line Chart Flow Analysis
Version: 3.2.0.0 - Complete 18 Data Types with Weekly/Daily K-Line Chart Flow Analysis
Added Type 17: Weekly K-Line Chart Flow (每週K線走勢圖含三大法人)
Added Type 18: Daily K-Line Chart Flow (每日K線走勢圖含三大法人)
Fixes SSL issues, improves download detection, better Windows compatibility
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import os
import re
import random
import sys
import tempfile
import uuid
import shutil
import subprocess
import platform
from io import StringIO
from datetime import datetime
from urllib.parse import urljoin, urlparse

# Global variable for stock names mapping
STOCK_NAMES = {}

def load_stock_names_from_csv(csv_file='StockID_TWSE_TPEX.csv'):
    """Load stock ID to company name mapping from CSV file"""
    global STOCK_NAMES
    
    try:
        if not os.path.exists(csv_file):
            print(f"警告 CSV file '{csv_file}' not found in current directory")
            print("使用 Using fallback stock names...")
            STOCK_NAMES = {
                '2330': '台積電',
                '0050': '元大台灣50',
                '2454': '聯發科',
                '2317': '鴻海',
                '1301': '台塑'
            }
            return False
        
        print(f"載入 Loading stock names from {csv_file}...")
        # Force string dtype to preserve leading zeros (e.g., 0000 index)
        df = pd.read_csv(csv_file, encoding='utf-8', dtype=str, keep_default_na=False)
        
        if '代號' not in df.columns or '名稱' not in df.columns:
            print("錯誤 CSV file must contain '代號' and '名稱' columns")
            return False
        
        STOCK_NAMES = {}
        for _, row in df.iterrows():
            stock_id = str(row['代號']).strip()
            company_name = str(row['名稱']).strip()
            if stock_id and company_name:
                STOCK_NAMES[stock_id] = company_name
                # Also normalize "0" to "0000" if it ever appears
                if stock_id == '0' and company_name:
                    STOCK_NAMES['0000'] = company_name
        
        print(f"完成 Loaded {len(STOCK_NAMES)} stock mappings from CSV")
        return True
        
    except Exception as e:
        print(f"錯誤 Error reading CSV file: {e}")
        print("使用 Using fallback stock names...")
        STOCK_NAMES = {
            '2330': '台積電',
            '0050': '元大台灣50',
            '2454': '聯發科',
            '2317': '鴻海',
            '1301': '台塑'
        }
        return False

# Enhanced data type mapping - Complete 18 Data Types (v3.2.0)
DATA_TYPES = {
    '1': ('dividend', 'DividendDetail', 'StockDividendPolicy.asp'),
    '2': ('basic', 'BasicInfo', 'BasicInfo.asp'),
    '3': ('detail', 'StockDetail', 'StockDetail.asp'),
    '4': ('performance', 'StockBzPerformance', 'StockBzPerformance.asp'),
    '5': ('revenue', 'ShowSaleMonChart', 'ShowSaleMonChart.asp'),
    '6': ('equity', 'EquityDistribution', 'EquityDistributionCatHis.asp'),
    '7': ('performance_quarter', 'StockBzPerformance1', 'StockBzPerformance.asp'),
    '8': ('eps_per_weekly', 'ShowK_ChartFlow', 'ShowK_ChartFlow.asp'),
    '9': ('quarterly_analysis', 'StockHisAnaQuar', 'StockHisAnaQuar.asp'),
    '10': ('equity_class_weekly', 'EquityDistributionClassHis', 'EquityDistributionClassHis.asp'),
    '11': ('weekly_trading_data', 'WeeklyTradingData', 'ShowK_Chart.asp'),
    '12': ('eps_per_monthly', 'ShowMonthlyK_ChartFlow', 'ShowK_ChartFlow.asp'),
    '13': ('margin_balance', 'ShowMarginChart', 'ShowMarginChart.asp'),
    '14': ('margin_balance_weekly', 'ShowMarginChartWeek', 'ShowMarginChart.asp'),
    '15': ('margin_balance_monthly', 'ShowMarginChartMonth', 'ShowMarginChart.asp'),
    '16': ('quarterly_fin_ratio', 'StockFinDetail', 'StockFinDetail.asp'),
    '17': ('weekly_k_chart_flow', 'ShowWeeklyK_ChartFlow', 'ShowK_ChartFlow.asp'),  # 🆕 NEW Type 17
    '18': ('daily_k_chart_flow', 'ShowDailyK_ChartFlow', 'ShowK_ChartFlow.asp')     # 🆕 NEW Type 18
}

def improved_chrome_cleanup():
    """IMPROVED: Windows-compatible Chrome cleanup"""
    print("清理 Improved Chrome cleanup...")
    
    killed_count = 0
    
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and any(chrome_name in proc.info['name'].lower() 
                                           for chrome_name in ['chrome', 'chromedriver']):
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except ImportError:
        pass
    
    # IMPROVED: Windows-specific cleanup
    if platform.system() == "Windows":
        try:
            # Use proper Windows commands
            result1 = subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                         capture_output=True, text=True, timeout=10)
            result2 = subprocess.run(['taskkill', '/f', '/im', 'chromedriver.exe'], 
                         capture_output=True, text=True, timeout=10)
            
            if result1.returncode == 0 or result2.returncode == 0:
                killed_count += 1
                
        except Exception as e:
            print(f"   Windows cleanup warning: {e}")
    else:
        try:
            subprocess.run(['pkill', '-f', 'chrome'], capture_output=True, timeout=10)
            subprocess.run(['pkill', '-f', 'chromedriver'], capture_output=True, timeout=10)
        except Exception as e:
            print(f"   Unix cleanup warning: {e}")
    
    time.sleep(2)
    print(f"完成 Cleanup completed: {killed_count} processes")
    return True

def wait_for_download_with_validation(download_dir, expected_patterns, timeout_seconds=15, check_interval=1):
    """IMPROVED: Wait for download with proper validation"""
    print(f"   等待下載 Waiting for download in {download_dir}...")
    
    initial_files = set()
    if os.path.exists(download_dir):
        initial_files = set(os.listdir(download_dir))
    
    start_time = time.time()
    
    for elapsed in range(0, timeout_seconds, check_interval):
        time.sleep(check_interval)
        
        if not os.path.exists(download_dir):
            continue
            
        current_files = set(os.listdir(download_dir))
        new_files = current_files - initial_files
        
        # Check for completed downloads (not .crdownload)
        completed_downloads = [f for f in new_files 
                             if f.endswith(('.xls', '.xlsx')) 
                             and not f.endswith('.crdownload')
                             and not f.endswith('.tmp')]
        
        if completed_downloads:
            for downloaded_file in completed_downloads:
                file_path = os.path.join(download_dir, downloaded_file)
                
                # Validate file size and content
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 1024:  # At least 1KB
                        # Quick content validation
                        with open(file_path, 'rb') as f:
                            header = f.read(512)
                            # Check if it looks like an Excel file or HTML-formatted Excel
                            if (header.startswith(b'\xd0\xcf\x11\xe0') or  # OLE
                               header.startswith(b'PK') or  # ZIP-based Excel
                               b'<html' in header.lower() or  # HTML table exported as XLS
                               b'microsoft' in header.lower() or
                               b'excel' in header.lower()):
                                
                                print(f"   ✅ 驗證成功 Valid download: {downloaded_file} ({file_size} bytes)")
                                return downloaded_file, file_path
                        
                        print(f"   ⚠️ 檔案格式疑慮 Questionable file format: {downloaded_file}")
                        return downloaded_file, file_path  # Return anyway, might be valid
                    else:
                        print(f"   ❌ 檔案太小 File too small: {downloaded_file} ({file_size} bytes)")
                        
                except Exception as e:
                    print(f"   ❌ 檔案驗證錯誤 File validation error: {e}")
        
        # Show progress
        if elapsed % 5 == 0 and elapsed > 0:
            print(f"   ⏳ 等待中 Still waiting... ({elapsed}/{timeout_seconds}s)")
    
    print(f"   ❌ 下載超時 Download timeout after {timeout_seconds}s")
    return None, None

def get_current_quarter():
    """Return current year and quarter based on system date."""
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    return now.year, quarter

def shift_quarter(year, quarter, offset):
    """Shift (year, quarter) by offset quarters."""
    total = year * 4 + (quarter - 1) + offset
    if total < 0:
        return 0, 1
    new_year = total // 4
    new_quarter = (total % 4) + 1
    return new_year, new_quarter

def normalize_fin_ratio_table(df):
    """Normalize financial ratio table for merging across blocks."""
    if df is None or df.empty:
        return None

    # Flatten multi-level headers if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            " ".join([str(x).strip() for x in col if str(x) != "nan"]).strip()
            for col in df.columns
        ]

    df.columns = [str(col).strip() for col in df.columns]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")

    if df.shape[1] < 2:
        return None

    first_col = df.columns[0]
    df = df.set_index(first_col)
    df.index = df.index.astype(str).str.strip()
    return df

def read_fin_ratio_table(file_path):
    """Read financial ratio table from downloaded XLS/HTML file."""
    try:
        return pd.read_excel(file_path)
    except Exception:
        try:
            tables = pd.read_html(file_path)
            return tables[0] if tables else None
        except Exception:
            return None

def wait_for_goodinfo_bootstrap(driver, timeout_seconds=20):
    """Wait until GoodInfo's short CLIENT_KEY/REINIT bootstrap page redirects."""
    start_time = time.time()
    last_url = ""

    while time.time() - start_time < timeout_seconds:
        try:
            page_source = driver.page_source or ""
            current_url = driver.current_url
            last_url = current_url

            is_bootstrap_page = (
                "CLIENT_KEY" in page_source
                and "window.location.replace" in page_source
                and re.search(r"<body[^>]*>\s*</body>", page_source, re.IGNORECASE)
            )
            if not is_bootstrap_page:
                return True

            redirect_match = re.search(r"location\.replace\('([^']+)'\)", page_source)
            if redirect_match:
                redirect_url = urljoin(current_url, redirect_match.group(1))
                print(f"   ⏳ GoodInfo 初始化跳轉中 GoodInfo bootstrap redirect: {redirect_url}")
                driver.get(redirect_url)
            else:
                print("   ⏳ GoodInfo 初始化中 GoodInfo bootstrap page detected")

            time.sleep(1)
        except Exception as e:
            print(f"   ⚠️ GoodInfo 初始化等待警告 Bootstrap wait warning: {e}")
            time.sleep(1)

    print(f"   ⚠️ GoodInfo 初始化逾時 Bootstrap wait timed out at: {last_url}")
    return False

def save_largest_html_table_as_xls(driver, output_path, min_cells=12):
    """Fallback for pages where GoodInfo renders tables but no XLS button is exposed."""
    try:
        page_source = driver.page_source or ""
        try:
            print(f"   🔍 Fallback URL: {driver.current_url}")
            print(f"   🔍 Fallback title: {driver.title}")
            print(f"   🔍 Page source length: {len(page_source)} chars")
        except Exception:
            pass

        # Detect Chrome browser error pages (ERR_HTTP2_PROTOCOL_ERROR, etc.)
        # These are network/connection errors and should be retried, not treated as "no data"
        if ('<html dir="ltr" lang="en">' in page_source and
                'id="main-frame-error"' in page_source):
            import re
            err_match = re.search(r'"errorCode":"([^"]+)"', page_source)
            err_code = err_match.group(1) if err_match else "UNKNOWN"
            print(f"   ❌ Chrome 網路錯誤 Chrome network error: {err_code} (可重試 retryable)")
            print(f"   ❌ Chrome network error page detected - connection failure, not a no-data page")
            return "chrome_error"

        rate_limit_markers = [
            "瀏覽量異常",
            "暫時關閉服務",
            "請稍後再重新使用",
            "適當調降程式查詢頻率",
        ]
        if any(marker in page_source for marker in rate_limit_markers):
            print("   🚦 GoodInfo rate limit detected: 瀏覽量異常 / 暫時關閉服務")
            print("   🚦 This is not no-data; stop retrying immediately and cool down")
            return "rate_limited"

        # Detect truly empty pages (< 500 chars) — stock has no data for this type.
        # Type 13/14/15 (margin balance) only covers stocks eligible for margin trading;
        # most stocks in the watchlist are ineligible → page is intentionally empty.
        if len(page_source) < 500:
            print(f"   ℹ️ 頁面為空 ({len(page_source)} chars) — 此股票無此類型資料 (margin ineligible or no data)")
            print(f"   ✅ 視為正常跳過 Treating as expected no-data stock (not a failure)")
            return "no_data_expected"

        tables = pd.read_html(StringIO(page_source))
    except Exception as e:
        print(f"   ⚠️ HTML表格 fallback 失敗 HTML table fallback failed: {e}")
        return False

    usable_tables = []
    for table in tables:
        rows, cols = table.shape
        cells = rows * cols
        if rows >= 2 and cols >= 2 and cells >= min_cells:
            usable_tables.append((cells, table))

    if not usable_tables:
        print("   ⚠️ HTML表格 fallback 找不到可用資料表 No usable HTML data table found")
        return False

    usable_tables.sort(key=lambda item: item[0], reverse=True)
    _, best_table = usable_tables[0]
    html_table = best_table.to_html(index=False)

    try:
        if os.path.exists(output_path):
            os.remove(output_path)
        with open(output_path, "w", encoding="utf-8-sig") as f:
            f.write(html_table)
        file_size = os.path.getsize(output_path)
        print(f"   ✅ HTML表格 fallback 已儲存 Saved HTML table fallback: {output_path} ({file_size} bytes)")
        return file_size > 1024
    except Exception as e:
        print(f"   ❌ HTML表格 fallback 儲存失敗 Failed to save HTML table fallback: {e}")
        return False

def find_xls_download_elements(driver, timeout_seconds=5):
    """Find GoodInfo export controls across anchors, inputs, and buttons (legacy)."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    xls_elements = []
    seen = set()
    patterns = [
        "//a[contains(text(), 'XLS') or contains(text(), 'Excel') or contains(text(), '匯出')]",
        "//button[contains(text(), 'XLS') or contains(text(), 'Excel') or contains(text(), '匯出')]",
        "//input[@type='button' and (contains(@value, 'XLS') or contains(@value, 'Excel') or contains(@value, '匯出'))]",
        "//*[self::a or self::button or self::input][contains(@onclick, 'ExportToExcel') or contains(@onclick, 'Export') or contains(@onclick, 'export') or contains(@onclick, 'xls') or contains(@onclick, 'XLS')]",
        "//*[self::a or self::button or self::input][contains(@title, 'XLS') or contains(@title, 'Excel') or contains(@title, '匯出')]",
    ]

    for pattern in patterns:
        try:
            elements = WebDriverWait(driver, timeout_seconds).until(
                EC.presence_of_all_elements_located((By.XPATH, pattern))
            )
            for elem in elements:
                elem_id = elem.id
                if elem_id in seen:
                    continue
                seen.add(elem_id)
                xls_elements.append(('element', elem))
                text = elem.text or elem.get_attribute('value') or elem.get_attribute('title') or 'no-text'
                print(f"   ✅ 找到XLS元素 Found XLS element: '{text}'")
        except TimeoutException:
            continue
    return xls_elements


def extract_table_via_new_mechanism(driver, download_dir, folder_name, stock_id, company_name, data_type_code):
    """
    GoodInfo changed from XLS buttons to <select class='sel_opt_black'> dropdowns.
    This function directly extracts the tblDetail table HTML from the page
    instead of relying on the browser download mechanism (which fails with Blob URLs
    in headless mode without CDP setup).
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    import re

    def cleanup_table_html(table_html):
        table_html = re.sub(
            r'<!--DummyTHead-->.*?<!--/DummyTHead-->',
            '', table_html, flags=re.DOTALL
        )
        table_html = re.sub(
            r'<!--NoExport-->.*?<!--/NoExport-->',
            '', table_html, flags=re.DOTALL
        )
        return table_html

    def save_table_html(table_html, table_name):
        if not table_html or len(table_html) < 200:
            print(f"   ⚠️ 表格 {table_name} 內容不足，跳過")
            return False

        output_content = ('<html><head><meta charset="UTF-8"></head><body>'
                          + cleanup_table_html(table_html) + '</body></html>')

        if data_type_code == '7':
            new_filename = f"{folder_name}_{stock_id}_{company_name}_quarter.xls"
        else:
            new_filename = f"{folder_name}_{stock_id}_{company_name}.xls"

        output_path = os.path.join(download_dir, new_filename)
        if os.path.exists(output_path):
            os.remove(output_path)

        with open(output_path, 'w', encoding='utf-8-sig') as f:
            f.write(output_content)

        file_size = os.path.getsize(output_path)
        if file_size > 1024:
            print(f"   ✅ 直接提取表格成功 {new_filename} ({file_size} bytes) from {table_name}")
            return True

        print(f"   ❌ 儲存檔案太小 {file_size} bytes from {table_name}, trying next table")
        return False

    # Wait for either the newer export select or a rendered data table. Some
    # GoodInfo pages expose tblDetail without any export dropdown.
    ready = False
    for elapsed in range(25):
        try:
            state = driver.execute_script("""
                return {
                    selects: document.querySelectorAll('select.sel_opt_black').length,
                    tables: Array.from(document.querySelectorAll('table')).filter(function(tbl) {
                        return tbl.rows && tbl.rows.length >= 2 && tbl.innerText.trim().length > 80;
                    }).length
                };
            """)
            if state and (state.get('selects', 0) > 0 or state.get('tables', 0) > 0):
                ready = True
                break
        except Exception:
            pass
        time.sleep(1)

    if not ready:
        try:
            print(f"   🔍 超時時URL Timeout URL: {driver.current_url}")
            print(f"   🔍 超時時標題 Timeout title: {driver.title}")
            # Log a snippet of the page source to diagnose what GoodInfo is showing
            src_snippet = (driver.page_source or "")[:300].replace('\n', ' ')
            print(f"   🔍 頁面源碼片段 Page source snippet: {src_snippet}")
        except Exception:
            pass
        print("   ❌ 未找到新式匯出選單或資料表 No export select or data table found")
        return False

    # Find all export select dropdowns and collect target table variable names.
    target_tables = []
    try:
        selects = driver.find_elements(By.CSS_SELECTOR, "select.sel_opt_black")
        for sel in selects:
            onchange = sel.get_attribute('onchange') or ''
            options = [o.text.strip() for o in sel.find_elements(By.TAG_NAME, 'option')]
            if '匯出XLS' in options:
                match = re.search(r'RptExtraFunc\((\w+),', onchange)
                if match:
                    table_var = match.group(1)
                    target_tables.append(table_var)
                    print(f"   找到目標表格變數 Found table variable: {table_var}")
    except Exception as e:
        print(f"   ⚠️ 搜尋表格變數失敗: {e}")

    # Add rendered table ids as fallback candidates. This covers pages where
    # GoodInfo renders data but omits the export select.
    try:
        dom_tables = driver.execute_script("""
            return Array.from(document.querySelectorAll('table')).map(function(tbl, idx) {
                return {
                    id: tbl.id || '',
                    html: tbl.outerHTML,
                    rows: tbl.rows ? tbl.rows.length : 0,
                    cells: tbl.querySelectorAll('td,th').length,
                    textLength: tbl.innerText ? tbl.innerText.trim().length : 0,
                    index: idx
                };
            }).filter(function(tbl) {
                return tbl.rows >= 2 && tbl.cells >= 4 && tbl.textLength > 80;
            }).sort(function(a, b) {
                return (b.cells + b.textLength) - (a.cells + a.textLength);
            });
        """)
    except Exception as e:
        print(f"   ⚠️ 搜尋DOM資料表失敗: {e}")
        dom_tables = []

    for table_id in ['tblDetail'] + [t for t in target_tables if t != 'tblDetail']:
        if table_id and table_id not in target_tables:
            target_tables.append(table_id)

    for table in dom_tables:
        table_id = table.get('id')
        if table_id and table_id not in target_tables:
            target_tables.append(table_id)

    if not target_tables and not dom_tables:
        print("   ❌ 未找到新式匯出選單或可用資料表 No export select or usable data table found")
        return False

    # Prefer tblDetail as primary table; fall back to other named tables.
    ordered = []
    for table_var in ['tblDetail'] + target_tables:
        if table_var and table_var not in ordered:
            ordered.append(table_var)

    for table_var in ordered:
        try:
            table_html = driver.execute_script(f"""
                var tbl = window['{table_var}'] || document.getElementById('{table_var}');
                if (!tbl) return null;
                return tbl.outerHTML;
            """)

            if save_table_html(table_html, table_var):
                return True

        except Exception as e:
            print(f"   ❌ 提取表格 {table_var} 失敗: {e}")
            continue

    # Last resort: save the largest usable table even when it has no id.
    for table in dom_tables:
        table_name = table.get('id') or f"table[{table.get('index', '?')}]"
        if save_table_html(table.get('html'), table_name):
            return True

    return False

def verify_monthly_revenue_freshness(file_path, stock_id):
    if not os.path.exists(file_path):
        return True
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        import re
        dates = re.findall(r'\b\d{4}/\d{2}\b', content)
        if dates:
            unique_dates = sorted(list(set(dates)), reverse=True)
            latest_date_str = unique_dates[0]
            try:
                ly, lm = map(int, latest_date_str.split('/'))
                from datetime import datetime
                now = datetime.now()
                # 每月 10 號到 15 號之間，強制檢查前一個月的營收是否已更新進來
                if 10 <= now.day <= 15:
                    if now.month == 1:
                        expected_year = now.year - 1
                        expected_month = 12
                    else:
                        expected_year = now.year
                        expected_month = now.month - 1
                    
                    if (ly, lm) < (expected_year, expected_month):
                        print(f"   ⚠️ [新鮮度驗證失敗] 檔案最新日期為 {latest_date_str}，但今日為 {now.strftime('%Y-%m-%d')}，預期應有 {expected_year}/{expected_month:02d} 的營收。將標記為下載失敗以便重試。")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return False
            except Exception as val_err:
                print(f"   ⚠️ 進行月營收新鮮度驗證時發生解析錯誤: {val_err}")
        return True
    except Exception as e:
        print(f"   ⚠️ 進行月營收新鮮度驗證時發生錯誤: {e}")
        return True

def selenium_download_xls_improved(stock_id, data_type_code):
    success = _selenium_download_xls_improved_internal(stock_id, data_type_code)
    if success and data_type_code == '5':
        # Perform freshness verification on success
        page_type, folder_name, asp_file = DATA_TYPES[data_type_code]
        company_name = STOCK_NAMES.get(stock_id, f'股票{stock_id}')
        if stock_id == '0000' and company_name.startswith('股票'):
            company_name = '台灣加權指數'
        new_filename = f"{folder_name}_{stock_id}_{company_name}.xls"
        download_dir = os.path.join(os.getcwd(), folder_name)
        output_path = os.path.join(download_dir, new_filename)
        
        if not verify_monthly_revenue_freshness(output_path, stock_id):
            return False
    return success

def _selenium_download_xls_improved_internal(stock_id, data_type_code):
    """ENHANCED: Selenium download with complete 16 data types support including Financial Ratio Analysis"""
    
    improved_chrome_cleanup()
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, WebDriverException
        from webdriver_manager.chrome import ChromeDriverManager
        
        if data_type_code not in DATA_TYPES:
            print(f"錯誤 Invalid data type: {data_type_code}")
            return False
        
        page_type, folder_name, asp_file = DATA_TYPES[data_type_code]
        company_name = STOCK_NAMES.get(stock_id, f'股票{stock_id}')
        if stock_id == '0000' and company_name.startswith('股票'):
            company_name = '台灣加權指數'
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print(f"建立 Created folder: {folder_name}")
        
        print(f"開始 Starting ENHANCED download for {stock_id} ({company_name}) - {folder_name}")
        
        # IMPROVED: Chrome setup with better SSL handling
        chrome_options = Options()
        
        download_dir = os.path.join(os.getcwd(), folder_name)
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # IMPROVED: Better Chrome arguments for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--remote-debugging-port=0")
        
        # IMPROVED: SSL and security settings
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        chrome_options.add_argument("--ignore-certificate-errors-ssl")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        print("設定 Using improved headless mode with SSL handling")
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # PREVENTION-FIRST: Hide navigator.webdriver using CDP
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                """
            })
            
            print("成功 Chrome WebDriver started successfully (Stealth Mode)")
        except Exception as driver_error:
            print(f"失敗 Failed to start Chrome WebDriver: {driver_error}")
            return False
        
        try:
            # IMPROVED: More generous timeouts for SSL issues
            driver.set_page_load_timeout(30)  # Increased for SSL issues
            driver.implicitly_wait(5)
            
            # Map 0000 to real TAIEX ID for URL
            url_stock_id = '加權指數' if stock_id == '0000' else stock_id

            if data_type_code == '16':
                print("使用 Using Quarterly Financial Ratio Analysis multi-block download [NEW!]")

                def load_page_with_wait(url):
                    print(f"訪問 Accessing: {url}")
                    try:
                        driver.get(url)
                        print("   ✅ 頁面載入成功 Page loaded successfully")
                        wait_for_goodinfo_bootstrap(driver, timeout_seconds=20)
                    except TimeoutException:
                        print("   ⚠️ 頁面載入超時，但繼續嘗試 Page load timeout, but continuing...")
                        wait_for_goodinfo_bootstrap(driver, timeout_seconds=10)
                    except Exception as e:
                        print(f"   ❌ 頁面載入錯誤 Page load error: {e}")
                        return False

                    print("等待 Waiting for page elements...")
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        print("   ✅ 頁面主體載入完成 Page body loaded")
                    except TimeoutException:
                        print("   ⚠️ 頁面主體載入超時，但繼續 Page body timeout, but continuing...")

                    max_wait = 8
                    for wait_time in range(max_wait):
                        try:
                            page_source = driver.page_source
                            if 'initializing' not in page_source.lower() and '初始化中' not in page_source:
                                print("   ✅ 頁面初始化完成 Page initialization completed")
                                break
                        except Exception:
                            pass

                        if wait_time < max_wait - 1:
                            print(f"   ⏳ 初始化中 Still initializing... ({wait_time + 1}/{max_wait})")
                            time.sleep(1)
                        else:
                            print("   ⚠️ 初始化超時，但繼續 Initialization timeout, but continuing...")
                    return True

                combined_df = None
                existing_columns = set()
                no_new_blocks = 0
                year, quarter = get_current_quarter()
                max_blocks = 40
                merged_output_path = os.path.join(download_dir, f"{folder_name}_{stock_id}_{company_name}.xls")

                for block in range(max_blocks):
                    qry_time = f"{year}{quarter}"
                    url = f"https://goodinfo.tw/tw/{asp_file}?RPT_CAT=XX_M_QUAR&STOCK_ID={url_stock_id}&QRY_TIME={qry_time}"
                    print(f"📘 Type 16 區段下載 Block {block + 1}/{max_blocks} - QRY_TIME={qry_time}")

                    if not load_page_with_wait(url):
                        break

                    print("   ⏳ 等待資料載入 Waiting 5 seconds for data loading...")
                    time.sleep(5)

                    # Extract table directly using new mechanism
                    try:
                        table_html = driver.execute_script("""
                            var tbl = window['tblDetail'] || document.getElementById('tblDetail');
                            if (!tbl) return null;
                            return tbl.outerHTML;
                        """)
                        if not table_html or len(table_html) < 200:
                            print("❌ 未找到 tblDetail 或內容不足 tblDetail not found or empty")
                            break
                        print(f"   ✅ 直接提取表格 HTML ({len(table_html)} chars)")
                        downloaded = True
                    except Exception as e:
                        print(f"❌ 提取 tblDetail 失敗: {e}")
                        break

                    try:
                        from io import StringIO
                        block_tables = pd.read_html(StringIO(table_html))
                        raw_df = block_tables[0] if block_tables else None
                    except Exception as e:
                        print(f"   ⚠️ 解析HTML表格失敗: {e}")
                        raw_df = None

                    block_df = normalize_fin_ratio_table(raw_df)
                    if block_df is None or block_df.empty:
                        print("   ⚠️ 無有效資料表，略過此區段 No usable table, skipping block")
                    else:
                        if block == 0 and os.path.exists(merged_output_path):
                            existing_df = read_fin_ratio_table(merged_output_path)
                            existing_norm = normalize_fin_ratio_table(existing_df)
                            if existing_norm is not None and not existing_norm.empty:
                                existing_quarters = set(existing_norm.index.astype(str).str.strip())
                                block_quarters = set(str(col).strip() for col in block_df.columns)
                                if block_quarters.issubset(existing_quarters):
                                    print("   ✅ 已是最新資料，跳過後續區段 No new quarters found, skipping remaining blocks")
                                    return True

                        new_cols = set(block_df.columns) - existing_columns
                        if combined_df is None:
                            combined_df = block_df
                        else:
                            combined_df = pd.concat([combined_df, block_df], axis=1)
                            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
                        existing_columns.update(block_df.columns)
                        if not new_cols:
                            no_new_blocks += 1
                            print("   ⚠️ 區段無新增季度資料 No new quarters found")
                        else:
                            no_new_blocks = 0

                    if no_new_blocks >= 2:
                        print("🔚 已無新資料，停止下載 No new data in consecutive blocks")
                        break

                    year, quarter = shift_quarter(year, quarter, -10)

                if combined_df is None or combined_df.empty:
                    print("❌ 無法合併任何資料 No data collected for merge")
                    return False

                merged_df = combined_df.T
                merged_path = os.path.join(download_dir, f"{folder_name}_{stock_id}_{company_name}.xls")
                html_table = merged_df.to_html(index=True)
                with open(merged_path, "w", encoding="utf-8-sig") as f:
                    f.write(html_table)
                print(f"✅ 合併完成 Merged full history saved: {merged_path}")
                return True
            
            # ENHANCED: Build URL with support for Type 16
            if data_type_code == '7':
                # Old URL with YEAR_PERIOD/SCROLL2Y params returns ASP 500; use minimal params
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={url_stock_id}&RPT_CAT=M_QUAR"
                print(f"使用 Using quarterly performance URL (RPT_CAT=M_QUAR)")
            elif data_type_code == '8':
                url = f"https://goodinfo.tw/tw/{asp_file}?RPT_CAT=PER&STOCK_ID={url_stock_id}"
                print(f"使用 Using EPS x PER weekly URL with special parameters")
            elif data_type_code == '11':
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={url_stock_id}&CHT_CAT=WEEK"
                print(f"使用 Using weekly trading data URL")
            elif data_type_code == '12':
                url = f"https://goodinfo.tw/tw/{asp_file}?RPT_CAT=PER&STOCK_ID={url_stock_id}&CHT_CAT=MONTH"
                print(f"使用 Using monthly P/E URL")
            elif data_type_code == '13':
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={url_stock_id}&CHT_CAT=DATE"
                print(f"使用 Using Daily Margin Balance URL")
            elif data_type_code == '14':
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={url_stock_id}&CHT_CAT=WEEK"
                print(f"使用 Using Weekly Margin Balance URL")
            elif data_type_code == '15':
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={url_stock_id}&PRICE_ADJ=F&CHT_CAT=MONTH&SCROLL2Y=400"
                print(f"使用 Using Monthly Margin Balance URL with PRICE_ADJ=F")
            elif data_type_code == '16':
                url = f"https://goodinfo.tw/tw/{asp_file}?RPT_CAT=XX_M_QUAR&STOCK_ID={url_stock_id}"
                print(f"使用 Using Quarterly Financial Ratio Analysis URL with special parameters [NEW!]")
            elif data_type_code == '17':
                url = f"https://goodinfo.tw/tw/{asp_file}?RPT_CAT=WEEK&STOCK_ID={url_stock_id}&CHT_CAT=WEEK"
                print(f"使用 Using Weekly K-Line Chart Flow URL with RPT_CAT=WEEK [NEW!]")
            elif data_type_code == '18':
                url = f"https://goodinfo.tw/tw/{asp_file}?RPT_CAT=DATE&STOCK_ID={url_stock_id}&CHT_CAT=DATE"
                print(f"使用 Using Daily K-Line Chart Flow URL with RPT_CAT=DATE [NEW!]")
            else:
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={url_stock_id}"
            
            print(f"訪問 Accessing: {url}")
            
            # IMPROVED: Navigate with better error handling
            try:
                driver.get(url)
                print("   ✅ 頁面載入成功 Page loaded successfully")
                wait_for_goodinfo_bootstrap(driver, timeout_seconds=20)
            except TimeoutException:
                print("   ⚠️ 頁面載入超時，但繼續嘗試 Page load timeout, but continuing...")
                wait_for_goodinfo_bootstrap(driver, timeout_seconds=10)
            except Exception as e:
                print(f"   ❌ 頁面載入錯誤 Page load error: {e}")
                return False
            
            # IMPROVED: Wait for page elements
            print("等待 Waiting for page elements...")
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("   ✅ 頁面主體載入完成 Page body loaded")
            except TimeoutException:
                print("   ⚠️ 頁面主體載入超時，但繼續 Page body timeout, but continuing...")
            
            # IMPROVED: Wait for initialization
            max_wait = 8
            for wait_time in range(max_wait):
                try:
                    page_source = driver.page_source
                    if 'initializing' not in page_source.lower() and '初始化中' not in page_source:
                        print("   ✅ 頁面初始化完成 Page initialization completed")
                        break
                except:
                    pass
                
                if wait_time < max_wait - 1:
                    print(f"   ⏳ 初始化中 Still initializing... ({wait_time + 1}/{max_wait})")
                    time.sleep(1)
                else:
                    print("   ⚠️ 初始化超時，但繼續 Initialization timeout, but continuing...")
            
            time.sleep(3)  # Additional stabilization time

            # Log actual URL and page title for diagnostics
            try:
                actual_url = driver.current_url
                page_title = driver.title
                print(f"   🔍 當前URL Current URL: {actual_url}")
                print(f"   🔍 頁面標題 Page title: {page_title}")
            except Exception as e:
                print(f"   ⚠️ 無法取得URL/標題 Cannot get URL/title: {e}")

            # PRIMARY: Use new GoodInfo export mechanism (select dropdown with 匯出XLS)
            # GoodInfo replaced all XLS buttons with <select class="sel_opt_black"> dropdowns.
            # Range buttons (查20年, 查5年, etc.) are also removed; pages now load full data by default.
            print("尋找 Looking for new export select dropdowns (GoodInfo v2 mechanism)...")
            if extract_table_via_new_mechanism(driver, download_dir, folder_name, stock_id, company_name, data_type_code):
                print("🎉 新機制提取成功 Download completed via new export select mechanism")
                return True

            # FALLBACK 1: Legacy XLS button detection (old GoodInfo mechanism)
            print("嘗試備用方案 Trying legacy XLS button detection...")
            xls_elements = find_xls_download_elements(driver, timeout_seconds=5)

            if xls_elements:
                print(f"嘗試 Attempting download with {len(xls_elements)} legacy XLS elements...")
                success = False
                for i, (elem_type, element) in enumerate(xls_elements, 1):
                    try:
                        element_text = element.text or element.get_attribute('value') or f'element_{i}'
                        print(f"   [{i}/{len(xls_elements)}] 點擊 Clicking: '{element_text}'")
                        driver.execute_script("arguments[0].click();", element)
                        downloaded_file, file_path = wait_for_download_with_validation(
                            download_dir, ['.xls', '.xlsx'], timeout_seconds=15
                        )
                        if downloaded_file and file_path:
                            new_filename = (
                                f"{folder_name}_{stock_id}_{company_name}_quarter.xls"
                                if data_type_code == '7'
                                else f"{folder_name}_{stock_id}_{company_name}.xls"
                            )
                            new_path = os.path.join(download_dir, new_filename)
                            try:
                                if os.path.exists(new_path):
                                    os.remove(new_path)
                                os.rename(file_path, new_path)
                                print(f"   ✅ 舊機制下載成功 Legacy download: {new_filename}")
                            except Exception as rename_error:
                                print(f"   ✅ 下載成功 Downloaded: {downloaded_file} (rename failed: {rename_error})")
                            success = True
                            break
                        else:
                            print(f"   ❌ 元素 {i} 下載失敗 Element {i} download failed")
                    except Exception as e:
                        print(f"   ❌ 元素 {i} 點擊錯誤: {e}")
                        continue

                if success:
                    print("🎉 舊機制下載完成 Legacy download completed")
                    return True

            # FALLBACK 2: Extract largest HTML table from page source
            print("❌ 所有XLS方式失敗，嘗試HTML表格 fallback All XLS methods failed, trying HTML table fallback...")
            fallback_filename = (
                f"{folder_name}_{stock_id}_{company_name}_quarter.xls"
                if data_type_code == '7'
                else f"{folder_name}_{stock_id}_{company_name}.xls"
            )
            fallback_path = os.path.join(download_dir, fallback_filename)
            fallback_result = save_largest_html_table_as_xls(driver, fallback_path)
            if fallback_result == "chrome_error":
                # Network error (ERR_HTTP2_PROTOCOL_ERROR etc.) - signal as retryable
                print("❌ Chrome 網路錯誤，此股票應重試 Chrome network error - stock should be retried")
                sys.exit(4)  # exit code 4 = Chrome network error (retryable)
            if fallback_result == "rate_limited":
                print("🚦 GoodInfo rate limited this request; stop immediate retry")
                sys.exit(5)  # exit code 5 = GoodInfo rate limit / anti-bot block
            if fallback_result == "no_data_expected":
                # Empty page = stock has no margin data (ineligible) — exit 0 (success/skip)
                print("ℹ️ 此股票無此類型資料，正常跳過 No data for this type — skipping as expected")
                sys.exit(0)
            if fallback_result:
                print("🎉 使用HTML表格 fallback 完成下載流程 Download completed with HTML table fallback")
                return True

            # Save debug info on total failure
            debug_file = f"debug_page_{stock_id}_{data_type_code}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"   💾 已儲存除錯頁面 Debug page saved: {debug_file}")
            try:
                screenshot_file = f"debug_screenshot_{stock_id}_{data_type_code}.png"
                driver.save_screenshot(screenshot_file)
                print(f"   📸 已儲存除錯截圖 Debug screenshot saved: {screenshot_file}")
            except Exception:
                print("   ⚠️ 無法儲存截圖 Cannot save screenshot")

            return False
            
        finally:
            try:
                driver.quit()
                print("關閉 Chrome WebDriver closed")
            except:
                pass
        
    except ImportError:
        print("錯誤 Selenium not available. Install with: pip install selenium webdriver-manager")
        return False
    except Exception as e:
        print(f"錯誤 Selenium error: {e}")
        return False

def show_usage():
    """Show usage information with complete 18 data types"""
    print("=" * 70)
    print("GoodInfo.tw XLS File Downloader v3.2.0.0 - Complete 18 Data Types")
    print("Downloads XLS files with ENHANCED K-Line Chart Flow analysis & multi-frequency data")
    print("Uses StockID_TWSE_TPEX.csv for stock mapping")
    print("No Login Required! Complete 18 Data Types with K-Line Chart Flow Analysis!")
    print("NEW: Type 17 - 每週K線走勢圖含三大法人 (Weekly K-Line Chart Flow)")
    print("NEW: Type 18 - 每日K線走勢圖含三大法人 (Daily K-Line Chart Flow)")
    print("=" * 70)
    print()
    print("Usage:")
    print("   python GetGoodInfo.py STOCK_ID DATA_TYPE")
    print()
    print("Examples:")
    print("   python GetGoodInfo.py 2330 1     # 台積電 dividend data")
    print("   python GetGoodInfo.py 0050 2     # 元大台灣50 basic info")
    print("   python GetGoodInfo.py 2454 3     # 聯發科 stock details")
    print("   python GetGoodInfo.py 2330 4     # 台積電 business performance")
    print("   python GetGoodInfo.py 2330 5     # 台積電 monthly revenue")
    print("   python GetGoodInfo.py 2330 6     # 台積電 equity distribution")
    print("   python GetGoodInfo.py 2330 7     # 台積電 quarterly performance")
    print("   python GetGoodInfo.py 2330 8     # 台積電 EPS x PER weekly")
    print("   python GetGoodInfo.py 2330 9     # 台積電 quarterly analysis")
    print("   python GetGoodInfo.py 2330 10    # 台積電 equity class weekly")
    print("   python GetGoodInfo.py 2330 11    # 台積電 weekly trading data")
    print("   python GetGoodInfo.py 2330 12    # 台積電 EPS x PER monthly")
    print("   python GetGoodInfo.py 2330 13    # 台積電 Daily Margin Balance")
    print("   python GetGoodInfo.py 2330 14    # 台積電 Weekly Margin Balance")
    print("   python GetGoodInfo.py 2330 15    # 台積電 Monthly Margin Balance")
    print("   python GetGoodInfo.py 2330 16    # 台積電 quarterly financial ratio analysis")
    print("   python GetGoodInfo.py 2330 17    # 台積電 Weekly K-Line Chart Flow [NEW!]")
    print("   python GetGoodInfo.py 2330 18    # 台積電 Daily K-Line Chart Flow [NEW!]")
    print()
    print("Data Types (Complete 18 Types - v3.2.0 ENHANCED):")
    print("   1 = Dividend Policy (殖利率政策)")
    print("   2 = Basic Info (基本資料)")
    print("   3 = Stock Details (個股市況)")
    print("   4 = Business Performance (經營績效)")
    print("   5 = Monthly Revenue (每月營收)")
    print("   6 = Equity Distribution (股權結構)")
    print("   7 = Quarterly Performance (每季經營績效)")
    print("   8 = EPS x PER Weekly (每週EPS本益比)")
    print("   9 = Quarterly Analysis (各季詳細統計資料)")
    print("   10 = Equity Class Weekly (股東持股分類週)")
    print("   11 = Weekly Trading Data (週交易資料含三大法人)")
    print("   12 = EPS x PER Monthly (每月EPS本益比)")
    print("   13 = Daily Margin Balance (每日融資融券餘額詳細資料)")
    print("   14 = Weekly Margin Balance (每周融資融券餘額詳細資料)")
    print("   15 = Monthly Margin Balance (每月融資融券餘額詳細資料)")
    print("   16 = Quarterly Financial Ratio Analysis (單季財務比率表詳細資料)")
    print("   17 = Weekly K-Line Chart Flow (每週K線走勢圖含三大法人) [NEW!]")
    print("   18 = Daily K-Line Chart Flow (每日K線走勢圖含三大法人) [NEW!]")
    print()
    print("Type 17-18 Features (NEW!):")
    print("   • Type 17: Weekly K-Line Chart Flow with institutional flows (5-year history)")
    print("   • Type 18: Daily K-Line Chart Flow with institutional flows (1-year history)")
    print("   • Includes OHLC prices, volume, and institutional trading data (外資/投信/自營)")
    print("   • Multi-frequency data for comprehensive technical and flow analysis")
    print()
    print("ENHANCEMENTS:")
    print("   • Complete 18 data types with K-Line Chart Flow analysis")
    print("   • Better SSL error handling")
    print("   • Improved download validation")
    print("   • Enhanced Windows compatibility")
    print("   • More robust file detection")
    print("   • Better error reporting with screenshots")
    print()

def main():
    """Main function with ENHANCED error handling for complete 18 data types"""

    load_stock_names_from_csv()

    if len(sys.argv) != 3:
        show_usage()
        print("錯誤 Error: Please provide STOCK_ID and DATA_TYPE")
        print("   Example: python GetGoodInfo.py 2330 17")
        sys.exit(1)

    stock_id = sys.argv[1].strip()
    data_type_code = sys.argv[2].strip()

    if data_type_code not in DATA_TYPES:
        print(f"錯誤 Invalid data type: {data_type_code}")
        print("   Valid options: 1-18")
        sys.exit(1)

    page_type, folder_name, asp_file = DATA_TYPES[data_type_code]
    company_name = STOCK_NAMES.get(stock_id, f'股票{stock_id}')
    if stock_id == '0000' and company_name.startswith('股票'):
        company_name = '台灣加權指數'

    print("=" * 70)
    print("GoodInfo.tw XLS File Downloader v3.2.0.0 - Complete 18 Data Types")
    print("Downloads XLS files with ENHANCED K-Line Chart Flow analysis & multi-frequency data")
    print("Complete 18 Data Types with K-Line Chart Flow analysis support!")
    print("=" * 70)
    print(f"股票 Stock: {stock_id} ({company_name})")
    print(f"類型 Data Type: {page_type} ({DATA_TYPES[data_type_code][0]})")
    
    if data_type_code == '7':
        filename = f"{folder_name}_{stock_id}_{company_name}_quarter.xls"
    else:
        filename = f"{folder_name}_{stock_id}_{company_name}.xls"
    
    print(f"儲存 Save to: {folder_name}\\{filename}")
    
    # ENHANCED: Show workflow details for all special types including Type 12
    if data_type_code == '5':
        print("流程 IMPROVED workflow: Click '查20年' → Wait 5s → XLS download")
    elif data_type_code == '7':
        print("流程 IMPROVED workflow: Special URL + Click '查60年' → Wait 5s → XLS download")
    elif data_type_code == '8':
        print("流程 IMPROVED workflow: Special URL + Click '查5年' → Wait 5s → XLS download")
    elif data_type_code == '9':
        print("流程 Standard workflow: Navigate to page → XLS download")
    elif data_type_code == '10':
        print("流程 IMPROVED workflow: Click '查5年' → Wait 5s → XLS download")
    elif data_type_code == '11':
        print("流程 ENHANCED workflow: Special URL + Click '查5年' → Wait 5s → XLS download")
        print("功能 Features: OHLC + Volume + Institutional Flows + Margin Trading Data")
    elif data_type_code == '12':
        print("流程 NEW! ENHANCED workflow: Special URL + Click '查20年' → Wait 5s → XLS download")
        print("功能 Features: 20-Year Monthly P/E + Conservative Multiples (9X-19X) + Long-Term Analysis")
    elif data_type_code == '13':
        print("流程 NEW! ENHANCED workflow: Special URL + Click '查1年' → Wait 5s → XLS download")
        print("功能 Features: Daily Margin Balance + Margin Usage Rate + Margin Maintenance Rate")
    elif data_type_code == '14':
        print("流程 NEW! ENHANCED workflow: Special URL + Click '查5年' → Wait 5s → XLS download")
        print("功能 Features: Weekly Margin Balance + 5-Year History")
    elif data_type_code == '15':
        print("流程 NEW! ENHANCED workflow: Special URL + Click '查20年' → Wait 5s → XLS download")
        print("功能 Features: Monthly Margin Balance + 20-Year History")
    elif data_type_code == '16':
        print("流程 NEW! ENHANCED workflow: Special URL + QRY_TIME pagination → Wait 5s → XLS download")
        print("功能 Features: Quarterly Financial Ratio Analysis (full history merged, transposed output)")
    elif data_type_code == '17':
        print("流程 NEW! ENHANCED workflow: Special URL + Click '查5年' → Wait 5s → XLS download")
        print("功能 Features: Weekly K-Line Chart Flow + OHLC + Volume + Institutional Flows (外資/投信/自營)")
    elif data_type_code == '18':
        print("流程 NEW! ENHANCED workflow: Special URL + Click '查1年' → Wait 5s → XLS download")
        print("功能 Features: Daily K-Line Chart Flow + OHLC + Volume + Institutional Flows (外資/投信/自營)")

    print("=" * 70)
    
    start_time = time.time()
    success = selenium_download_xls_improved(stock_id, data_type_code)
    end_time = time.time()
    
    execution_time = end_time - start_time
    
    if success:
        print(f"\n✅ 完成 Download completed successfully in {execution_time:.1f} seconds!")
        print(f"檢查 Check the '{folder_name}' folder for your XLS file")
        
        if data_type_code == '11':
            print("🎊 恭喜您成功下載了全新的週交易資料含三大法人數據！")
            print("📊 This includes comprehensive institutional trading analysis!")
        elif data_type_code == '12':
            print("🎊 恭喜您成功下載了20年月度本益比數據！")
            print("📈 This includes 20-year monthly P/E analysis for long-term investment strategies!")
        elif data_type_code == '13':
            print("🎊 恭喜您成功下載了每日融資融券餘額詳細資料！")
            print("📊 This includes daily margin balance details for market sentiment analysis!")
        elif data_type_code == '14':
            print("🎊 恭喜您成功下載了每周融資融券餘額詳細資料！")
            print("📊 This includes weekly aggregated margin balance data!")
        elif data_type_code == '15':
            print("🎊 恭喜您成功下載了每月融資融券餘額詳細資料！")
            print("📊 This includes monthly aggregated margin balance data!")
        elif data_type_code == '16':
            print("🎊 恭喜您成功下載了單季財務比率表詳細資料！")
            print("📊 This includes the latest 10-quarter financial ratio analysis!")
        elif data_type_code == '17':
            print("🎊 恭喜您成功下載了每週K線走勢圖含三大法人數據！")
            print("📊 This includes weekly OHLC, volume, and institutional trading flows!")
        elif data_type_code == '18':
            print("🎊 恭喜您成功下載了每日K線走勢圖含三大法人數據！")
            print("📊 This includes daily OHLC, volume, and institutional trading flows!")

        # IMPROVED: Verify file actually exists and provide details
        expected_path = os.path.join(folder_name, filename)
        if os.path.exists(expected_path):
            file_size = os.path.getsize(expected_path)
            file_time = datetime.fromtimestamp(os.path.getmtime(expected_path))
            print(f"驗證 File verified: {file_size} bytes, modified {file_time}")
        else:
            print("⚠️ 警告 Warning: Expected file not found at exact path")
            
    else:
        print(f"\n❌ 失敗 Download failed for {stock_id} after {execution_time:.1f} seconds")
        print("除錯 Debug files saved - check debug_page_*.html and debug_screenshot_*.png")
        print("建議 Suggestions:")
        print("   • Check network connection")
        print("   • Verify stock ID is valid")
        print("   • Try running again (temporary network issues)")
        if data_type_code in ['5', '7', '8', '10', '11', '12', '13', '14', '15', '16']:
            print(f"提示 Type {data_type_code} uses special workflow - check button availability")
        if data_type_code == '11':
            print("機構數據提示 Type 11 includes institutional flows - if issues persist, try other data types first")
        if data_type_code == '12':
            print("新功能提示 Type 12 is NEW! 20-year monthly P/E data - if issues persist, try weekly Type 8 first")
        if data_type_code == '13':
            print("新功能提示 Type 13 is NEW! Daily Margin Balance data - check if '查1年' button is available")
        if data_type_code == '14':
            print("新功能提示 Type 14 is NEW! Weekly Margin Balance data - check if '查5年' button is available")
        if data_type_code == '15':
            print("新功能提示 Type 15 is NEW! Monthly Margin Balance data - check if '查20年' button is available")
        if data_type_code == '16':
            print("新功能提示 Type 16 is NEW! Quarterly Financial Ratio Analysis data - allow extra load time before download")
        
        # Exit with error code for batch processing
        sys.exit(1)

if __name__ == "__main__":
    main()
