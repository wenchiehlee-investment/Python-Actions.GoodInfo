#!/usr/bin/env python3
"""
GetGoodInfo.py - XLS File Downloader for GoodInfo.tw
Version: 1.4.3.0 - Command Line Version with CSV Stock Mapping + DATA_TYPE=5 Support
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

# Data type mapping - Updated to include DATA_TYPE=5
DATA_TYPES = {
    '1': ('dividend', 'DividendDetail', 'StockDividendPolicy.asp'),
    '2': ('basic', 'BasicInfo', 'BasicInfo.asp'),
    '3': ('detail', 'StockDetail', 'StockDetail.asp'),
    '4': ('performance', 'StockBzPerformance', 'StockBzPerformance.asp'),
    '5': ('revenue', 'ShowSaleMonChart', 'ShowSaleMonChart.asp')
}

def selenium_download_xls(stock_id, data_type_code):
    """Use Selenium to download XLS files with proper naming"""
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
        
        # Setup Chrome options with download directory
        chrome_options = Options()
        
        # Set download directory to the specific folder
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
        
        # Anti-detection options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Setup driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Remove automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            # Build URL
            url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={stock_id}"
            
            print(f"🔗 Accessing: {url}")
            
            # Navigate to page
            driver.get(url)
            
            # Wait for page to load (handle initialization)
            print("⏳ Waiting for page to load...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for initialization to complete
            max_wait = 10
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
            time.sleep(3)
            
            # Special handling for DATA_TYPE=5 (Monthly Revenue)
            if data_type_code == '5':
                print("🔄 Special workflow for Monthly Revenue data...")
                try:
                    # Look for "查20年" button first
                    print("🔍 Looking for '查20年' button...")
                    
                    twenty_year_patterns = [
                        "//input[@value='查20年']",
                        "//button[contains(text(), '查20年')]",
                        "//a[contains(text(), '查20年')]",
                        "//*[contains(text(), '查20年')]",
                        "//input[contains(@value, '20年')]",
                        "//input[contains(@onclick, '20')]"
                    ]
                    
                    twenty_year_button = None
                    for pattern in twenty_year_patterns:
                        buttons = driver.find_elements(By.XPATH, pattern)
                        if buttons:
                            twenty_year_button = buttons[0]
                            print(f"   Found '查20年' button using pattern: {pattern}")
                            break
                    
                    if twenty_year_button:
                        print("🖱️ Clicking '查20年' button...")
                        driver.execute_script("arguments[0].click();", twenty_year_button)
                        
                        print("⏳ Waiting 2 seconds for data to load...")
                        time.sleep(2)
                        
                        print("✅ Ready to look for XLS download button")
                    else:
                        print("⚠️ '查20年' button not found, proceeding with XLS search...")
                        
                        # Debug: show all clickable elements to help find the button
                        all_inputs = driver.find_elements(By.TAG_NAME, "input")[:10]
                        all_buttons = driver.find_elements(By.TAG_NAME, "button")[:10]
                        
                        print("   Available input elements:")
                        for i, inp in enumerate(all_inputs):
                            value = inp.get_attribute('value') or 'no-value'
                            onclick = inp.get_attribute('onclick') or 'no-onclick'
                            print(f"     {i+1}. value='{value}' onclick='{onclick}'")
                        
                        print("   Available button elements:")
                        for i, btn in enumerate(all_buttons):
                            text = btn.text or 'no-text'
                            onclick = btn.get_attribute('onclick') or 'no-onclick'
                            print(f"     {i+1}. text='{text}' onclick='{onclick}'")
                
                except Exception as e:
                    print(f"⚠️ Error in special workflow: {e}")
                    print("   Continuing with standard XLS search...")
            
            # Look for XLS download links/buttons with enhanced detection
            print("🔍 Looking for XLS download buttons...")
            
            # Save page source for debugging
            page_source = driver.page_source
            
            # Enhanced XLS element detection
            xls_elements = []
            
            # Method 1: Find links with XLS-related text (expanded search)
            link_patterns = [
                "//a[contains(text(), 'XLS') or contains(text(), 'Excel') or contains(text(), '匯出') or contains(text(), 'Export')]",
                "//a[contains(text(), 'xls') or contains(text(), 'excel') or contains(text(), '下載') or contains(text(), 'download')]",
                "//a[contains(@href, 'xls') or contains(@href, 'excel') or contains(@href, 'export')]",
                "//a[contains(@title, 'XLS') or contains(@title, 'Excel') or contains(@title, '匯出')]"
            ]
            
            for pattern in link_patterns:
                links = driver.find_elements(By.XPATH, pattern)
                for link in links:
                    if link not in [x[1] for x in xls_elements]:
                        xls_elements.append(('link', link))
                        print(f"   Found XLS link: '{link.text}' (href: {link.get_attribute('href')})")
            
            # Method 2: Find buttons with XLS-related text (expanded search)
            button_patterns = [
                "//input[@type='button' and (contains(@value, 'XLS') or contains(@value, 'Excel') or contains(@value, '匯出') or contains(@value, 'Export'))]",
                "//input[@type='button' and (contains(@value, 'xls') or contains(@value, 'excel') or contains(@value, '下載') or contains(@value, 'download'))]",
                "//button[contains(text(), 'XLS') or contains(text(), 'Excel') or contains(text(), '匯出') or contains(text(), '下載')]",
                "//input[@type='submit' and (contains(@value, 'XLS') or contains(@value, '匯出'))]"
            ]
            
            for pattern in button_patterns:
                buttons = driver.find_elements(By.XPATH, pattern)
                for button in buttons:
                    if button not in [x[1] for x in xls_elements]:
                        xls_elements.append(('button', button))
                        print(f"   Found XLS button: '{button.get_attribute('value') or button.text}'")
            
            # Method 3: Look for specific GoodInfo.tw patterns
            goodinfo_patterns = [
                "//a[contains(@onclick, 'ExportToExcel')]",
                "//a[contains(@onclick, 'Export')]",
                "//input[contains(@onclick, 'ExportToExcel')]",
                "//input[contains(@onclick, 'Export')]",
                "//*[contains(@class, 'export')]",
                "//*[contains(@id, 'export')]",
                "//img[@alt='Excel' or @alt='XLS']/../..",
                "//img[contains(@src, 'excel') or contains(@src, 'xls')]/../.."
            ]
            
            for pattern in goodinfo_patterns:
                elements = driver.find_elements(By.XPATH, pattern)
                for elem in elements:
                    if elem not in [x[1] for x in xls_elements]:
                        xls_elements.append(('goodinfo', elem))
                        print(f"   Found GoodInfo pattern: '{elem.text or elem.get_attribute('value')}' (tag: {elem.tag_name})")
            
            # Method 4: Debug - show all clickable elements if no XLS elements found
            if not xls_elements:
                print("🔍 No XLS elements found. Debugging all clickable elements...")
                
                # Find all links and buttons for debugging
                all_links = driver.find_elements(By.TAG_NAME, "a")[:20]  # Limit to first 20
                all_buttons = driver.find_elements(By.XPATH, "//input[@type='button'] | //input[@type='submit'] | //button")[:20]
                
                print(f"   Found {len(all_links)} links (showing first 20):")
                for i, link in enumerate(all_links):
                    href = link.get_attribute('href') or 'no-href'
                    text = link.text.strip() or 'no-text'
                    print(f"     {i+1}. '{text}' -> {href}")
                
                print(f"   Found {len(all_buttons)} buttons (showing first 20):")
                for i, btn in enumerate(all_buttons):
                    value = btn.get_attribute('value') or btn.text or 'no-value'
                    onclick = btn.get_attribute('onclick') or 'no-onclick'
                    print(f"     {i+1}. '{value}' onclick: {onclick}")
                
                # Save page source to file for inspection
                with open(f"debug_page_{stock_id}.html", "w", encoding="utf-8") as f:
                    f.write(page_source)
                print(f"   💾 Saved page source to debug_page_{stock_id}.html")
                
                # Take a screenshot for debugging
                try:
                    driver.save_screenshot(f"debug_screenshot_{stock_id}.png")
                    print(f"   📸 Saved screenshot to debug_screenshot_{stock_id}.png")
                except:
                    print(f"   ⚠️ Could not save screenshot")
            
            if not xls_elements:
                print("❌ No XLS download elements found after enhanced search")
                return False
            
            # Get initial file list in download directory
            initial_files = set(os.listdir(download_dir) if os.path.exists(download_dir) else [])
            
            # Try to download from the first XLS element
            success = False
            for elem_type, element in xls_elements:
                try:
                    element_text = element.text if element.text else element.get_attribute('value')
                    print(f"🖱️ Clicking {elem_type}: '{element_text}'")
                    
                    # Click the element
                    driver.execute_script("arguments[0].click();", element)
                    
                    # Wait for download to start/complete
                    print("⏳ Waiting for download...")
                    max_wait_download = 15
                    
                    for wait_sec in range(max_wait_download):
                        time.sleep(1)
                        
                        # Check for new files in download directory
                        if os.path.exists(download_dir):
                            current_files = set(os.listdir(download_dir))
                            new_files = current_files - initial_files
                            
                            # Look for downloaded files (XLS, XLSX, but not temp files)
                            downloaded_files = [f for f in new_files if f.endswith(('.xls', '.xlsx')) and not f.endswith('.crdownload')]
                            
                            if downloaded_files:
                                for downloaded_file in downloaded_files:
                                    old_path = os.path.join(download_dir, downloaded_file)
                                    
                                    # Create new filename with exact format requested
                                    new_filename = f"{folder_name}_{stock_id}_{company_name}.xls"
                                    new_path = os.path.join(download_dir, new_filename)
                                    
                                    # Remove existing file if it exists (to avoid rename conflicts)
                                    if os.path.exists(new_path):
                                        os.remove(new_path)
                                        print(f"   Removed existing file: {new_filename}")
                                    
                                    # Rename file
                                    try:
                                        os.rename(old_path, new_path)
                                        print(f"✅ Downloaded and renamed to: {folder_name}\\{new_filename}")
                                        success = True
                                    except Exception as e:
                                        print(f"✅ Downloaded: {folder_name}\\{downloaded_file}")
                                        print(f"⚠️ Could not rename: {e}")
                                        success = True
                                
                                break  # Successfully downloaded
                    
                    if success:
                        break  # No need to try other elements
                    else:
                        print(f"   No download detected for {elem_type}")
                        
                except Exception as e:
                    print(f"   Error clicking {elem_type}: {e}")
                    continue
            
            return success
            
        finally:
            driver.quit()
        
    except ImportError:
        print("❌ Selenium not available. Install with: pip install selenium webdriver-manager")
        return False
    except Exception as e:
        print(f"❌ Selenium error: {e}")
        return False

def show_usage():
    """Show usage information"""
    print("=" * 60)
    print("🚀 GoodInfo.tw XLS File Downloader v1.4.3.0")
    print("📁 Downloads XLS files directly from export buttons")
    print("📊 Uses StockID_TWSE_TPEX.csv for stock mapping")
    print("🎉 No Login Required!")
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
    print()
    print("🔢 Data Types:")
    print("   1 = Dividend Policy (殖利率政策)")
    print("   2 = Basic Info (基本資料)")
    print("   3 = Stock Details (個股市況)")
    print("   4 = Business Performance (經營績效)")
    print("   5 = Monthly Revenue (每月營收)")
    print()
    print("📈 Sample Stock IDs from CSV:")
    sample_count = 0
    for stock_id, name in STOCK_NAMES.items():
        if sample_count < 10:
            print(f"   {stock_id} = {name}")
            sample_count += 1
        else:
            break
    if len(STOCK_NAMES) > 10:
        print(f"   ... and {len(STOCK_NAMES) - 10} more stocks")
    print()
    print("📁 Output Examples:")
    print("   DividendDetail\\DividendDetail_2330_台積電.xls")
    print("   BasicInfo\\BasicInfo_0050_元大台灣50.xls")
    print("   StockDetail\\StockDetail_2454_聯發科.xls")
    print("   StockBzPerformance\\StockBzPerformance_2330_台積電.xls")
    print("   ShowSaleMonChart\\ShowSaleMonChart_2330_台積電.xls")
    print()

def main():
    """Main function with command line arguments"""
    
    # Load stock names from CSV file first
    load_stock_names_from_csv()
    
    # Check command line arguments
    if len(sys.argv) != 3:
        show_usage()
        print("❌ Error: Please provide STOCK_ID and DATA_TYPE")
        print("   Example: python GetGoodInfo.py 2330 1")
        sys.exit(1)
    
    stock_id = sys.argv[1].strip()
    data_type_code = sys.argv[2].strip()
    
    # Validate data type
    if data_type_code not in DATA_TYPES:
        print(f"❌ Invalid data type: {data_type_code}")
        print("   Valid options: 1 (dividend), 2 (basic), 3 (detail), 4 (performance), 5 (revenue)")
        sys.exit(1)
    
    # Get info
    page_type, folder_name, asp_file = DATA_TYPES[data_type_code]
    company_name = STOCK_NAMES.get(stock_id, f'股票{stock_id}')
    
    # Check if stock ID exists in our mapping
    if stock_id not in STOCK_NAMES:
        print(f"⚠️ Stock ID '{stock_id}' not found in CSV mapping")
        print(f"   Will use fallback name: {company_name}")
        print(f"   Consider checking if '{stock_id}' is correct")
        print()
    
    print("=" * 60)
    print("🚀 GoodInfo.tw XLS File Downloader v1.4.3.0")
    print("📁 Downloads XLS files with Selenium")
    print("=" * 60)
    print(f"📊 Stock: {stock_id} ({company_name})")
    print(f"📋 Data Type: {page_type} ({DATA_TYPES[data_type_code][0]})")
    print(f"📁 Save to: {folder_name}\\{folder_name}_{stock_id}_{company_name}.xls")
    print("=" * 60)
    
    # Start download
    success = selenium_download_xls(stock_id, data_type_code)
    
    if success:
        print(f"\n🎉 Download completed successfully!")
        print(f"📁 Check the '{folder_name}' folder for your XLS file")
    else:
        print(f"\n❌ Download failed for {stock_id}")
        print("💡 Common issues:")
        print("   • Stock ID not found on GoodInfo.tw")
        print("   • Network connection problems")
        print("   • Page structure changed")

if __name__ == "__main__":
    main()