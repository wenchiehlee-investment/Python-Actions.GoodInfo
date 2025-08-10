#!/usr/bin/env python3
"""
GetGoodInfo.py - XLS File Downloader for GoodInfo.tw
Version: 1.5.0.2 - Aggressive Chrome WebDriver Fix
Usage: python GetGoodInfo.py STOCK_ID DATA_TYPE
Example: python GetGoodInfo.py 2330 1
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
            print(f"⚠️ CSV file '{csv_file}' not found in current directory")
            print("📁 Using fallback stock names...")
            # Fallback to some common stocks if CSV is not available
            STOCK_NAMES = {
                '2330': '台積電',
                '0050': '元大台灣50',
                '2454': '聯發科',
                '2317': '鴻海',
                '1301': '台塑'
            }
            return False
        
        # Read CSV file
        print(f"📖 Loading stock names from {csv_file}...")
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        # Check if required columns exist
        if '代號' not in df.columns or '名稱' not in df.columns:
            print("❌ CSV file must contain '代號' and '名稱' columns")
            return False
        
        # Create mapping dictionary
        STOCK_NAMES = {}
        for _, row in df.iterrows():
            stock_id = str(row['代號']).strip()
            company_name = str(row['名稱']).strip()
            if stock_id and company_name:
                STOCK_NAMES[stock_id] = company_name
        
        print(f"✅ Loaded {len(STOCK_NAMES)} stock mappings from CSV")
        return True
        
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        print("📁 Using fallback stock names...")
        # Fallback to some common stocks
        STOCK_NAMES = {
            '2330': '台積電',
            '0050': '元大台灣50',
            '2454': '聯發科',
            '2317': '鴻海',
            '1301': '台塑'
        }
        return False

# Data type mapping - Updated to include all 7 DATA_TYPES
DATA_TYPES = {
    '1': ('dividend', 'DividendDetail', 'StockDividendPolicy.asp'),
    '2': ('basic', 'BasicInfo', 'BasicInfo.asp'),
    '3': ('detail', 'StockDetail', 'StockDetail.asp'),
    '4': ('performance', 'StockBzPerformance', 'StockBzPerformance.asp'),
    '5': ('revenue', 'ShowSaleMonChart', 'ShowSaleMonChart.asp'),
    '6': ('equity', 'EquityDistribution', 'EquityDistributionCatHis.asp'),
    '7': ('performance_quarter', 'StockBzPerformance1', 'StockBzPerformance.asp')
}

def aggressive_chrome_cleanup():
    """Aggressively clean up Chrome processes and directories"""
    print("🔥 Performing aggressive Chrome cleanup...")
    
    # Step 1: Kill Chrome processes using multiple methods
    killed_count = 0
    
    # Method 1: Using psutil (if available)
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and any(chrome_name in proc.info['name'].lower() 
                                           for chrome_name in ['chrome', 'chromedriver']):
                    print(f"   Killing {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except ImportError:
        pass
    
    # Method 2: Using system commands
    if platform.system() == "Windows":
        try:
            subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                         capture_output=True, text=True)
            subprocess.run(['taskkill', '/f', '/im', 'chromedriver.exe'], 
                         capture_output=True, text=True)
            print("   Used Windows taskkill for Chrome processes")
        except:
            pass
    else:
        try:
            subprocess.run(['pkill', '-f', 'chrome'], capture_output=True)
            subprocess.run(['pkill', '-f', 'chromedriver'], capture_output=True)
            print("   Used Unix pkill for Chrome processes")
        except:
            pass
    
    # Step 2: Wait for processes to terminate
    print("   Waiting 3 seconds for processes to terminate...")
    time.sleep(3)
    
    # Step 3: Clean up temp directories
    temp_dir = tempfile.gettempdir()
    patterns = [
        os.path.join(temp_dir, "chrome_user_data_*"),
        os.path.join(temp_dir, "scoped_dir*"),
        os.path.join(temp_dir, ".com.google.Chrome.*"),
        os.path.join(temp_dir, "tmp*chrome*"),
    ]
    
    cleaned_count = 0
    for pattern in patterns:
        import glob
        for temp_path in glob.glob(pattern):
            try:
                if os.path.isdir(temp_path):
                    shutil.rmtree(temp_path, ignore_errors=True)
                    cleaned_count += 1
                elif os.path.isfile(temp_path):
                    os.remove(temp_path)
                    cleaned_count += 1
            except:
                pass
    
    print(f"✅ Aggressive cleanup completed: {killed_count} processes, {cleaned_count} temp items")
    return True

def selenium_download_xls(stock_id, data_type_code):
    """Use Selenium to download XLS files with aggressive Chrome setup"""
    
    # Perform aggressive cleanup first
    aggressive_chrome_cleanup()
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Get data type info
        if data_type_code not in DATA_TYPES:
            print(f"❌ Invalid data type: {data_type_code}")
            return False
        
        page_type, folder_name, asp_file = DATA_TYPES[data_type_code]
        
        # Get company name
        company_name = STOCK_NAMES.get(stock_id, f'股票{stock_id}')
        
        # Create folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print(f"📁 Created folder: {folder_name}")
        
        print(f"🌐 Starting download for {stock_id} ({company_name}) - {folder_name}")
        
        # Create multiple fallback directories
        temp_base = tempfile.gettempdir()
        temp_dirs = []
        
        for i in range(3):  # Try 3 different temp directories
            temp_user_data_dir = os.path.join(temp_base, f"chrome_goodinfo_{uuid.uuid4().hex[:8]}_{i}")
            temp_dirs.append(temp_user_data_dir)
            
            # Ensure directory doesn't exist
            if os.path.exists(temp_user_data_dir):
                try:
                    shutil.rmtree(temp_user_data_dir)
                except:
                    continue
            
            # Try to create it
            try:
                os.makedirs(temp_user_data_dir, exist_ok=True)
                print(f"📁 Created temp directory: {temp_user_data_dir}")
                break
            except:
                continue
        else:
            print("❌ Could not create any temp directory, trying without user data dir")
            temp_user_data_dir = None
        
        # Setup Chrome options with MAXIMUM compatibility
        chrome_options = Options()
        
        # Set download directory
        download_dir = os.path.join(os.getcwd(), folder_name)
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2,
            "intl.accept_languages": "zh-TW,zh,en-US,en"
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Add user data directory if we have one
        if temp_user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={temp_user_data_dir}")
        
        # MAXIMUM Chrome arguments for stability and compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-translate")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--metrics-recording-only")
        chrome_options.add_argument("--no-report-upload")
        chrome_options.add_argument("--remote-debugging-port=0")
        
        # Use headless mode to avoid GUI conflicts
        chrome_options.add_argument("--headless=new")  # Use new headless mode
        
        # Anti-detection (though less important in headless)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        print("🔧 Using headless mode for maximum compatibility")
        
        # Setup driver with timeout
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Chrome WebDriver started successfully")
        except Exception as driver_error:
            print(f"❌ Failed to start Chrome WebDriver: {driver_error}")
            
            # Fallback: Try without user data directory
            if temp_user_data_dir:
                print("🔄 Retrying without user data directory...")
                chrome_options = Options()
                chrome_options.add_experimental_option("prefs", prefs)
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--remote-debugging-port=0")
                
                try:
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("✅ Chrome WebDriver started successfully (fallback mode)")
                    temp_user_data_dir = None  # Don't try to clean up
                except Exception as fallback_error:
                    print(f"❌ Fallback also failed: {fallback_error}")
                    return False
            else:
                return False
        
        # Remove automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            # Build URL - Special handling for DATA_TYPE=7 (Quarterly Performance)
            if data_type_code == '7':
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={stock_id}&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR"
                print(f"🔗 Using quarterly performance URL with special parameters")
            else:
                url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={stock_id}"
            
            print(f"🔗 Accessing: {url}")
            
            # Navigate to page with timeout
            driver.set_page_load_timeout(30)
            driver.get(url)
            
            # Wait for page to load
            print("⏳ Waiting for page to load...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for initialization to complete
            max_wait = 15
            for wait_time in range(max_wait):
                page_source = driver.page_source
                if '初始化中' not in page_source and 'åå§åä¸­' not in page_source:
                    print("✅ Page initialization completed")
                    break
                elif wait_time < max_wait - 1:
                    print(f"   Still initializing... ({wait_time + 1}/{max_wait})")
                    time.sleep(1)
                else:
                    print("⚠️ Page still initializing after waiting")
            
            # Additional wait for content to fully load
            time.sleep(5)
            
            # Special handling for DATA_TYPE=5 and DATA_TYPE=7
            if data_type_code == '5':
                print("🔄 Special workflow for Monthly Revenue data...")
                try:
                    twenty_year_patterns = [
                        "//input[@value='查20年']",
                        "//button[contains(text(), '查20年')]",
                        "//a[contains(text(), '查20年')]",
                        "//*[contains(text(), '查20年')]"
                    ]
                    
                    twenty_year_button = None
                    for pattern in twenty_year_patterns:
                        buttons = driver.find_elements(By.XPATH, pattern)
                        if buttons:
                            twenty_year_button = buttons[0]
                            print(f"   Found '查20年' button")
                            break
                    
                    if twenty_year_button:
                        print("🖱️ Clicking '查20年' button...")
                        driver.execute_script("arguments[0].click();", twenty_year_button)
                        time.sleep(3)
                        print("✅ Ready to look for XLS download button")
                    else:
                        print("⚠️ '查20年' button not found, proceeding with XLS search...")
                
                except Exception as e:
                    print(f"⚠️ Error in special workflow for Type 5: {e}")
            
            elif data_type_code == '7':
                print("🔄 Special workflow for Quarterly Business Performance data...")
                try:
                    sixty_year_patterns = [
                        "//input[@value='查60年']",
                        "//button[contains(text(), '查60年')]",
                        "//a[contains(text(), '查60年')]",
                        "//*[contains(text(), '查60年')]"
                    ]
                    
                    sixty_year_button = None
                    for pattern in sixty_year_patterns:
                        buttons = driver.find_elements(By.XPATH, pattern)
                        if buttons:
                            sixty_year_button = buttons[0]
                            print(f"   Found '查60年' button")
                            break
                    
                    if sixty_year_button:
                        print("🖱️ Clicking '查60年' button...")
                        driver.execute_script("arguments[0].click();", sixty_year_button)
                        time.sleep(3)
                        print("✅ Ready to look for XLS download button")
                    else:
                        print("⚠️ '查60年' button not found, proceeding with XLS search...")
                
                except Exception as e:
                    print(f"⚠️ Error in special workflow for Type 7: {e}")
            
            # Look for XLS download elements
            print("🔍 Looking for XLS download buttons...")
            
            xls_elements = []
            
            # Enhanced XLS element detection
            patterns = [
                "//a[contains(text(), 'XLS') or contains(text(), 'Excel') or contains(text(), '匯出')]",
                "//input[@type='button' and (contains(@value, 'XLS') or contains(@value, '匯出'))]",
                "//a[contains(@onclick, 'ExportToExcel') or contains(@onclick, 'Export')]",
                "//input[contains(@onclick, 'ExportToExcel') or contains(@onclick, 'Export')]"
            ]
            
            for pattern in patterns:
                elements = driver.find_elements(By.XPATH, pattern)
                for elem in elements:
                    if elem not in [x[1] for x in xls_elements]:
                        xls_elements.append(('element', elem))
                        text = elem.text or elem.get_attribute('value') or 'no-text'
                        print(f"   Found XLS element: '{text}'")
            
            if not xls_elements:
                print("❌ No XLS download elements found")
                
                # Save debug files
                with open(f"debug_page_{stock_id}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"   💾 Saved page source to debug_page_{stock_id}.html")
                
                try:
                    driver.save_screenshot(f"debug_screenshot_{stock_id}.png")
                    print(f"   📸 Saved screenshot to debug_screenshot_{stock_id}.png")
                except:
                    print("   ⚠️ Could not save screenshot")
                
                return False
            
            # Try to download
            initial_files = set(os.listdir(download_dir) if os.path.exists(download_dir) else [])
            
            success = False
            for elem_type, element in xls_elements:
                try:
                    element_text = element.text or element.get_attribute('value') or 'unknown'
                    print(f"🖱️ Clicking: '{element_text}'")
                    
                    driver.execute_script("arguments[0].click();", element)
                    
                    print("⏳ Waiting for download...")
                    for wait_sec in range(20):  # Wait up to 20 seconds
                        time.sleep(1)
                        
                        if os.path.exists(download_dir):
                            current_files = set(os.listdir(download_dir))
                            new_files = current_files - initial_files
                            downloaded_files = [f for f in new_files if f.endswith(('.xls', '.xlsx')) and not f.endswith('.crdownload')]
                            
                            if downloaded_files:
                                for downloaded_file in downloaded_files:
                                    old_path = os.path.join(download_dir, downloaded_file)
                                    
                                    if data_type_code == '7':
                                        new_filename = f"{folder_name}_{stock_id}_{company_name}_quarter.xls"
                                    else:
                                        new_filename = f"{folder_name}_{stock_id}_{company_name}.xls"
                                    
                                    new_path = os.path.join(download_dir, new_filename)
                                    
                                    if os.path.exists(new_path):
                                        os.remove(new_path)
                                    
                                    try:
                                        os.rename(old_path, new_path)
                                        print(f"✅ Downloaded and renamed to: {folder_name}\\{new_filename}")
                                        success = True
                                    except Exception as e:
                                        print(f"✅ Downloaded: {folder_name}\\{downloaded_file}")
                                        success = True
                                
                                break
                    
                    if success:
                        break
                    else:
                        print(f"   No download detected")
                        
                except Exception as e:
                    print(f"   Error clicking element: {e}")
                    continue
            
            return success
            
        finally:
            try:
                driver.quit()
                print("🔧 Chrome WebDriver closed")
            except:
                pass
            
            # Cleanup temp directories
            if temp_user_data_dir and os.path.exists(temp_user_data_dir):
                try:
                    shutil.rmtree(temp_user_data_dir, ignore_errors=True)
                    print(f"🗑️ Cleaned up temporary directory")
                except:
                    pass
        
    except ImportError:
        print("❌ Selenium not available. Install with: pip install selenium webdriver-manager")
        return False
    except Exception as e:
        print(f"❌ Selenium error: {e}")
        return False

def show_usage():
    """Show usage information"""
    print("=" * 60)
    print("🚀 GoodInfo.tw XLS File Downloader v1.5.0.2")
    print("📁 Downloads XLS files directly from export buttons")
    print("📊 Uses StockID_TWSE_TPEX.csv for stock mapping")
    print("🎉 No Login Required! Complete 7 Data Types!")
    print("🔥 AGGRESSIVE Chrome WebDriver fix with headless mode")
    print("=" * 60)
    print()
    print("📋 Usage:")
    print("   python GetGoodInfo.py STOCK_ID DATA_TYPE")
    print()
    print("📊 Examples:")
    print("   python GetGoodInfo.py 2330 1    # 台積電 dividend data")
    print("   python GetGoodInfo.py 0050 2    # 元大台灣50 basic info")
    print("   python GetGoodInfo.py 2454 3    # 聯發科 stock details")
    print("   python GetGoodInfo.py 2330 4    # 台積電 business performance")
    print("   python GetGoodInfo.py 2330 5    # 台積電 monthly revenue")
    print("   python GetGoodInfo.py 2330 6    # 台積電 equity distribution")
    print("   python GetGoodInfo.py 2330 7    # 台積電 quarterly performance")
    print()
    print("🔢 Data Types (Complete 7 Types):")
    print("   1 = Dividend Policy (殖利率政策)")
    print("   2 = Basic Info (基本資料)")
    print("   3 = Stock Details (個股市況)")
    print("   4 = Business Performance (經營績效)")
    print("   5 = Monthly Revenue (每月營收)")
    print("   6 = Equity Distribution (股東結構)")
    print("   7 = Quarterly Performance (每季經營績效)")
    print()

def main():
    """Main function with command line arguments"""
    
    # Load stock names from CSV file first
    load_stock_names_from_csv()
    
    # Check command line arguments
    if len(sys.argv) != 3:
        show_usage()
        print("❌ Error: Please provide STOCK_ID and DATA_TYPE")
        print("   Example: python GetGoodInfo.py 2330 4")
        sys.exit(1)
    
    stock_id = sys.argv[1].strip()
    data_type_code = sys.argv[2].strip()
    
    # Validate data type
    if data_type_code not in DATA_TYPES:
        print(f"❌ Invalid data type: {data_type_code}")
        print("   Valid options: 1-7")
        sys.exit(1)
    
    # Get info
    page_type, folder_name, asp_file = DATA_TYPES[data_type_code]
    company_name = STOCK_NAMES.get(stock_id, f'股票{stock_id}')
    
    print("=" * 60)
    print("🚀 GoodInfo.tw XLS File Downloader v1.5.0.2")
    print("📁 Downloads XLS files with Selenium - 7 Data Types!")
    print("🔥 AGGRESSIVE Chrome WebDriver fix with headless mode")
    print("=" * 60)
    print(f"📊 Stock: {stock_id} ({company_name})")
    print(f"📋 Data Type: {page_type} ({DATA_TYPES[data_type_code][0]})")
    
    if data_type_code == '7':
        filename = f"{folder_name}_{stock_id}_{company_name}_quarter.xls"
    else:
        filename = f"{folder_name}_{stock_id}_{company_name}.xls"
    
    print(f"📁 Save to: {folder_name}\\{filename}")
    print("=" * 60)
    
    # Start download
    success = selenium_download_xls(stock_id, data_type_code)
    
    if success:
        print(f"\n🎉 Download completed successfully!")
        print(f"📁 Check the '{folder_name}' folder for your XLS file")
    else:
        print(f"\n❌ Download failed for {stock_id}")
        print("💡 Try running the cleanup script first: python cleanup_chrome.py")

if __name__ == "__main__":
    main()