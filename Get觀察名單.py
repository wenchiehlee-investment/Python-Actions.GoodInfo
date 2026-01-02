#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get觀察名單.py
Version: 2.0
Description: Downloads Taiwan stock market observation and focus lists from GitHub repository.
             1. 觀察名單.csv -> StockID_TWSE_TPEX.csv (Observation list)
             2. 專注名單.csv -> StockID_TWSE_TPEX_focus.csv (Focus list)
"""

import requests
import os
import time
from datetime import datetime

def download_file(url, output_file, description, add_taiex=False):
    """Download a file from a URL and save it locally."""
    try:
        print(f"正在下載 {description}...")
        print(f"來源: {url}")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        content = response.content.decode('utf-8')

        # Add TAIEX if requested and not present
        if add_taiex:
             if "0000,台灣加權指數" not in content and "0000,??????????" not in content:
                print("加入台灣加權指數 (0000) 到名單中...")
                if not content.endswith('\n'):
                    content += '\n'
                content += "0000,台灣加權指數\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        file_size = os.path.getsize(output_file)
        print(f"✅ {description} 下載成功!")
        print(f"   儲存為: {output_file}")
        print(f"   大小: {file_size:,} bytes")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ {description} 下載失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 處理 {description} 時發生錯誤: {e}")
        return False

def main():
    print("=" * 60)
    print(f"台灣股市名單下載程式 v2.0")
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    base_url = "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main"
    
    # Task 1: Observation List
    # URL encoded: %E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv
    url_obs = f"{base_url}/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv"
    file_obs = "StockID_TWSE_TPEX.csv"
    success_obs = download_file(url_obs, file_obs, "觀察名單", add_taiex=True)

    print("-" * 60)

    # Task 2: Focus List
    # URL encoded: %E5%B0%88%E6%B3%A8%E5%90%8D%E5%96%AE.csv
    url_focus = f"{base_url}/%E5%B0%88%E6%B3%A8%E5%90%8D%E5%96%AE.csv"
    file_focus = "StockID_TWSE_TPEX_focus.csv"
    success_focus = download_file(url_focus, file_focus, "專注名單", add_taiex=False)

    print("=" * 60)
    if success_obs and success_focus:
        print("所有名單更新完成! 🎉")
    else:
        print("部分名單更新失敗，請檢查錯誤訊息。 ⚠️")
        if not success_obs and not success_focus:
             exit(1)

if __name__ == "__main__":
    main()
