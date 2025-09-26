#!/usr/bin/env python3
"""
GetGoodInfo.py - Enhanced with Complete 12 Data Types including EPS x PER Monthly
Version: 2.0.0.0 - Complete 12 Data Types with Long-Term Monthly P/E Analysis
Added Type 12: EPS x PER Monthly with 20-year historical data and conservative P/E multiples
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
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        if '代號' not in df.columns or '名稱' not in df.columns:
            print("錯誤 CSV file must contain '代號' and '名稱' columns")
            return False
        
        STOCK_NAMES = {}
        for _, row in df.iterrows():
            stock_id = str(row['代號']).strip()
            company_name = str(row['名稱']).strip()
            if stock_id and company_name:
                STOCK_NAMES[stock_id] = company_name
        
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

# Enhanced data type mapping - Complete 12 Data Types (v2.0.0)
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
    '12': ('eps_per_monthly', 'ShowMonthlyK_ChartFlow', 'ShowK_ChartFlow.asp')  # 🆕 NEW Type 12
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

def selenium_download_xls_improved(stock_id, data_type_code):
    """ENHANCED: Selenium download with complete 12 data types support including Type 12"""
    
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
            print("成功 Chrome WebDriver started successfully")
        except Exception as driver_error:
            print(f"失敗 Failed to start Chrome WebDriver: {driver_error}")
            return False
        
        try:
            # IMPROVED: More generous timeouts for SSL issues
            driver.set_page_load_timeout(30)  # Increased for SSL issues
            driver.implicitly_wait(5)
            
            # ENHANCED: Build URL with support for Type 12
            if data_type_code == '7':
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={stock_id}&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR"
                print(f"使用 Using quarterly performance URL with special parameters")
            elif data_type_code == '8':
                url = f"https://goodinfo.tw/tw/{asp_file}?RPT_CAT=PER&STOCK_ID={stock_id}"
                print(f"使用 Using EPS x PER weekly URL with special parameters")
            elif data_type_code == '11':
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={stock_id}&CHT_CAT=WEEK&PRICE_ADJ=F&SCROLL2Y=600"
                print(f"使用 Using weekly trading data URL with special parameters")
            elif data_type_code == '12':
                url = f"https://goodinfo.tw/tw/{asp_file}?RPT_CAT=PER&STOCK_ID={stock_id}&CHT_CAT=MONTH&SCROLL2Y=439"
                print(f"使用 Using monthly P/E URL with special parameters [NEW!]")
            else:
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={stock_id}"
            
            print(f"訪問 Accessing: {url}")
            
            # IMPROVED: Navigate with better error handling
            try:
                driver.get(url)
                print("   ✅ 頁面載入成功 Page loaded successfully")
            except TimeoutException:
                print("   ⚠️ 頁面載入超時，但繼續嘗試 Page load timeout, but continuing...")
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
            
            # ENHANCED: Handle special workflows including new Type 12
            if data_type_code == '5':
                print("處理 IMPROVED workflow for Monthly Revenue data...")
                try:
                    twenty_year_button = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@value='查20年'] | //button[contains(text(), '查20年')] | //a[contains(text(), '查20年')]"))
                    )
                    print("   點擊 Clicking '查20年' button...")
                    driver.execute_script("arguments[0].click();", twenty_year_button)
                    time.sleep(5)  # Wait 5 seconds for data loading
                    print("   ✅ 特殊按鈕點擊完成 Special button clicked")
                except TimeoutException:
                    print("   ⚠️ '查20年' 按鈕未找到，繼續XLS搜尋 Button not found, proceeding with XLS search...")
            
            elif data_type_code == '7':
                print("處理 IMPROVED workflow for Quarterly Business Performance data...")
                try:
                    sixty_year_button = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@value='查60年'] | //button[contains(text(), '查60年')] | //a[contains(text(), '查60年')]"))
                    )
                    print("   點擊 Clicking '查60年' button...")
                    driver.execute_script("arguments[0].click();", sixty_year_button)
                    time.sleep(5)  # Wait 5 seconds for data loading
                    print("   ✅ 特殊按鈕點擊完成 Special button clicked")
                except TimeoutException:
                    print("   ⚠️ '查60年' 按鈕未找到，繼續XLS搜尋 Button not found, proceeding with XLS search...")
            
            elif data_type_code == '8':
                print("處理 IMPROVED workflow for EPS x PER Weekly data...")
                try:
                    five_year_button = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@value='查5年'] | //button[contains(text(), '查5年')] | //a[contains(text(), '查5年')]"))
                    )
                    print("   點擊 Clicking '查5年' button...")
                    driver.execute_script("arguments[0].click();", five_year_button)
                    time.sleep(5)  # Wait 5 seconds for data loading
                    print("   ✅ 特殊按鈕點擊完成 Special button clicked")
                except TimeoutException:
                    print("   ⚠️ '查5年' 按鈕未找到，繼續XLS搜尋 Button not found, proceeding with XLS search...")
            
            elif data_type_code == '10':
                print("處理 IMPROVED workflow for Equity Class Weekly data...")
                try:
                    five_year_button = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@value='查5年'] | //button[contains(text(), '查5年')] | //a[contains(text(), '查5年')]"))
                    )
                    print("   點擊 Clicking '查5年' button...")
                    driver.execute_script("arguments[0].click();", five_year_button)
                    time.sleep(5)  # Wait 5 seconds for data loading
                    print("   ✅ 特殊按鈕點擊完成 Special button clicked")
                except TimeoutException:
                    print("   ⚠️ '查5年' 按鈕未找到，繼續XLS搜尋 Button not found, proceeding with XLS search...")
            
            elif data_type_code == '11':
                print("處理 ENHANCED workflow for Weekly Trading Data with Institutional Flows...")
                try:
                    five_year_button = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@value='查5年'] | //button[contains(text(), '查5年')] | //a[contains(text(), '查5年')]"))
                    )
                    print("   點擊 Clicking '查5年' button for comprehensive trading data...")
                    driver.execute_script("arguments[0].click();", five_year_button)
                    time.sleep(5)  # Wait 5 seconds for institutional data loading
                    print("   ✅ 週交易資料特殊按鈕點擊完成 Weekly trading data special button clicked")
                except TimeoutException:
                    print("   ⚠️ '查5年' 按鈕未找到，繼續XLS搜尋 Button not found, proceeding with XLS search...")
            
            elif data_type_code == '12':
                print("處理 NEW! ENHANCED workflow for EPS x PER Monthly data...")
                try:
                    twenty_year_button = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@value='查20年'] | //button[contains(text(), '查20年')] | //a[contains(text(), '查20年')]"))
                    )
                    print("   點擊 Clicking '查20年' button for 20-year monthly P/E data...")
                    driver.execute_script("arguments[0].click();", twenty_year_button)
                    time.sleep(5)  # Wait 5 seconds for monthly P/E data loading
                    print("   ✅ 月度本益比特殊按鈕點擊完成 Monthly P/E special button clicked [NEW!]")
                except TimeoutException:
                    print("   ⚠️ '查20年' 按鈕未找到，繼續XLS搜尋 Button not found, proceeding with XLS search...")
            
            # IMPROVED: XLS download elements detection with 4-tier search
            print("尋找 Looking for XLS download buttons...")
            
            xls_elements = []
            patterns = [
                "//a[contains(text(), 'XLS') or contains(text(), 'Excel') or contains(text(), '匯出')]",
                "//input[@type='button' and (contains(@value, 'XLS') or contains(@value, '匯出'))]",
                "//a[contains(@onclick, 'ExportToExcel') or contains(@onclick, 'Export')]",
                "//input[contains(@onclick, 'ExportToExcel') or contains(@onclick, 'Export')]"
            ]
            
            for pattern in patterns:
                try:
                    elements = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, pattern))
                    )
                    for elem in elements:
                        if elem not in [x[1] for x in xls_elements]:
                            xls_elements.append(('element', elem))
                            text = elem.text or elem.get_attribute('value') or 'no-text'
                            print(f"   ✅ 找到XLS元素 Found XLS element: '{text}'")
                except TimeoutException:
                    continue
            
            if not xls_elements:
                print("❌ 未找到XLS下載元素 No XLS download elements found")
                
                # Save debug info
                debug_file = f"debug_page_{stock_id}_{data_type_code}.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"   💾 已儲存除錯頁面 Debug page saved: {debug_file}")
                
                # Take debug screenshot
                try:
                    screenshot_file = f"debug_screenshot_{stock_id}_{data_type_code}.png"
                    driver.save_screenshot(screenshot_file)
                    print(f"   📸 已儲存除錯截圖 Debug screenshot saved: {screenshot_file}")
                except:
                    print("   ⚠️ 無法儲存截圖 Cannot save screenshot")
                
                return False
            
            # IMPROVED: Download attempt with validation
            print(f"嘗試 Attempting download with {len(xls_elements)} XLS elements...")
            
            success = False
            for i, (elem_type, element) in enumerate(xls_elements, 1):
                try:
                    element_text = element.text or element.get_attribute('value') or f'element_{i}'
                    print(f"   [{i}/{len(xls_elements)}] 點擊 Clicking: '{element_text}'")
                    
                    # Record files before download
                    pre_download_files = set()
                    if os.path.exists(download_dir):
                        pre_download_files = set(os.listdir(download_dir))
                    
                    # Click element
                    driver.execute_script("arguments[0].click();", element)
                    
                    # IMPROVED: Wait for download with validation
                    downloaded_file, file_path = wait_for_download_with_validation(
                        download_dir, ['.xls', '.xlsx'], timeout_seconds=15
                    )
                    
                    if downloaded_file and file_path:
                        # ENHANCED: Rename file appropriately including Type 12
                        if data_type_code == '7':
                            new_filename = f"{folder_name}_{stock_id}_{company_name}_quarter.xls"
                        else:
                            new_filename = f"{folder_name}_{stock_id}_{company_name}.xls"
                        
                        new_path = os.path.join(download_dir, new_filename)
                        
                        try:
                            if os.path.exists(new_path):
                                os.remove(new_path)
                            os.rename(file_path, new_path)
                            print(f"   ✅ 下載成功並重新命名 Downloaded and renamed: {new_filename}")
                            if data_type_code == '11':
                                print(f"   🏆 週交易資料含三大法人下載完成 Weekly trading data with institutional flows completed")
                            elif data_type_code == '12':
                                print(f"   🆕 月度本益比數據下載完成 Monthly P/E data downloaded successfully [NEW!]")
                        except Exception as rename_error:
                            print(f"   ✅ 下載成功 Downloaded: {downloaded_file}")
                            print(f"   ⚠️ 重新命名失敗 Rename failed: {rename_error}")
                        
                        success = True
                        break
                    else:
                        print(f"   ❌ 元素 {i} 下載失敗 Element {i} download failed")
                        
                except Exception as e:
                    print(f"   ❌ 元素 {i} 點擊錯誤 Element {i} click error: {e}")
                    continue
            
            if success:
                print("🎉 下載流程完成 Download process completed successfully")
                if data_type_code == '11':
                    print("🚀 恭喜！您已成功下載完整的週交易資料含三大法人數據")
                elif data_type_code == '12':
                    print("🚀 恭喜！您已成功下載20年月度本益比數據 - 支援長期估值分析！")
            else:
                print("❌ 所有XLS元素嘗試失敗 All XLS elements failed")
            
            return success
            
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
    """Show usage information with complete 12 data types"""
    print("=" * 70)
    print("GoodInfo.tw XLS File Downloader v2.0.0.0 - Complete 12 Data Types")
    print("Downloads XLS files with ENHANCED long-term valuation analysis")
    print("Uses StockID_TWSE_TPEX.csv for stock mapping")
    print("No Login Required! Complete 12 Data Types with Monthly P/E Analysis!")
    print("NEW: Type 12 - 每月EPS本益比 (EPS x PER Monthly for Long-Term Analysis)")
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
    print("   python GetGoodInfo.py 2330 12    # 台積電 EPS x PER monthly [NEW!]")
    print()
    print("Data Types (Complete 12 Types - v2.0.0 ENHANCED):")
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
    print("   12 = EPS x PER Monthly (每月EPS本益比) [NEW!]")
    print()
    print("Type 12 Features (NEW!):")
    print("   • 20-year monthly EPS and P/E ratio data")
    print("   • Conservative P/E multiples (9X-19X) for long-term analysis")
    print("   • Monthly frequency for fundamental analysis")
    print("   • Backtesting support with extended historical coverage")
    print("   • Complements Type 8 weekly analysis (15X-30X multiples)")
    print("   • Long-term valuation modeling and portfolio management")
    print()
    print("ENHANCEMENTS:")
    print("   • Complete 12 data types with long-term valuation analysis")
    print("   • Better SSL error handling")
    print("   • Improved download validation")
    print("   • Enhanced Windows compatibility")
    print("   • More robust file detection")
    print("   • Better error reporting with screenshots")
    print()

def main():
    """Main function with ENHANCED error handling for complete 12 data types"""
    
    load_stock_names_from_csv()
    
    if len(sys.argv) != 3:
        show_usage()
        print("錯誤 Error: Please provide STOCK_ID and DATA_TYPE")
        print("   Example: python GetGoodInfo.py 2330 12")
        sys.exit(1)
    
    stock_id = sys.argv[1].strip()
    data_type_code = sys.argv[2].strip()
    
    if data_type_code not in DATA_TYPES:
        print(f"錯誤 Invalid data type: {data_type_code}")
        print("   Valid options: 1-12")
        sys.exit(1)
    
    page_type, folder_name, asp_file = DATA_TYPES[data_type_code]
    company_name = STOCK_NAMES.get(stock_id, f'股票{stock_id}')
    
    print("=" * 70)
    print("GoodInfo.tw XLS File Downloader v2.0.0.0 - Complete 12 Data Types")
    print("Downloads XLS files with ENHANCED long-term valuation analysis")
    print("Complete 12 Data Types with comprehensive monthly P/E data!")
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
        if data_type_code in ['5', '7', '8', '10', '11', '12']:
            print(f"提示 Type {data_type_code} uses special workflow - check button availability")
        if data_type_code == '11':
            print("機構數據提示 Type 11 includes institutional flows - if issues persist, try other data types first")
        if data_type_code == '12':
            print("新功能提示 Type 12 is NEW! 20-year monthly P/E data - if issues persist, try weekly Type 8 first")
        
        # Exit with error code for batch processing
        sys.exit(1)

if __name__ == "__main__":
    main()