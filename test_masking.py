import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import argparse
import sys

def setup_current_driver():
    """Exact replica of current GetGoodInfo.py driver setup"""
    print("[模式] 使用 Current (原始) 設定")
    
    chrome_options = Options()
    
    # 複製自 GetGoodInfo.py 的 prefs
    prefs = {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.notifications": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 複製自 GetGoodInfo.py 的 arguments
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
    
    # SSL settings from GetGoodInfo.py
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--ignore-certificate-errors-ssl")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def setup_improved_driver():
    """Enhanced stealth driver setup"""
    print("[模式] 使用 Improved (強化偽裝) 設定")
    
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    
    # 強化偽裝參數
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7')
    
    # 嘗試繞過 GPU 檢測
    options.add_argument('--ignore-gpu-blocklist')
    options.add_argument('--enable-webgl')
    
    # 真實 User-Agent (更新版本)
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    options.add_argument(f'--user-agent={user_agent}')

    driver = uc.Chrome(options=options, version_main=None)
    
    # CDP 指紋遮蔽
    try:
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "platform": "Win32",
            "acceptLanguage": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        })
    except:
        pass
        
    return driver

def run_test(mode):
    driver = None
    try:
        if mode == 'current':
            driver = setup_current_driver()
        else:
            driver = setup_improved_driver()
            
        driver.set_page_load_timeout(30)
        
        target_url = "https://goodinfo.tw/tw/StockDividendPolicy.asp?STOCK_ID=2330"
        print(f"正在訪問: {target_url}")
        
        driver.get(target_url)
        print("頁面請求已發送")
        
        time.sleep(8)  # 等待加載
        
        # 1. 檢查標題
        title = driver.title
        print(f"網頁標題: {title}")
        
        # 2. 檢查關鍵元素 (XLS 按鈕)
        print("尋找 XLS 按鈕...")
        xls_found = False
        try:
            # 複製自 GetGoodInfo.py 的 XPATH
            patterns = [
                "//a[contains(text(), 'XLS') or contains(text(), 'Excel') or contains(text(), '匯出')]",
                "//input[@type='button' and (contains(@value, 'XLS') or contains(@value, '匯出'))]"
            ]
            for p in patterns:
                elems = driver.find_elements(By.XPATH, p)
                if elems:
                    print(f"✅ 找到按鈕: {len(elems)} 個 (Pattern: {p})")
                    xls_found = True
                    break
        except Exception as e:
            print(f"搜尋元素時發生錯誤: {e}")
            
        if not xls_found:
            print("❌ 失敗: 未找到 XLS 按鈕")
            
        # 3. 儲存證據
        prefix = f"test_{mode}"
        driver.save_screenshot(f"{prefix}.png")
        with open(f"{prefix}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"證據已儲存: {prefix}.png, {prefix}.html")
        
    except Exception as e:
        print(f"執行發生例外: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['current', 'improved'], default='current', help='Test mode')
    args = parser.parse_args()
    
    run_test(args.mode)