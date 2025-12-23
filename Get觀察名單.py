#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get觀察名單.py
Downloads Taiwan stock market observation list from GitHub repository
and saves it as StockID_TWSE_TPEX.csv
"""

import requests
import os
from datetime import datetime

def download_stock_list():
    """Download stock observation list from GitHub and save locally"""
    
    # Source URL
    url = "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv"
    
    # Output filename
    output_file = "StockID_TWSE_TPEX.csv"
    
    try:
        print(f"開始下載觀察名單...")
        print(f"來源: {url}")
        
        # Download the file
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Save to file
        content = response.content.decode('utf-8')
        
        # Check if TAIEX is already in the list
        if "0000,台灣加權指數" not in content and "0000,??????????" not in content:
            print("加入台灣加權指數 (0000) 到名單中...")
            if not content.endswith('\n'):
                content += '\n'
            content += "0000,台灣加權指數\n"
            
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Get file size
        file_size = os.path.getsize(output_file)
        
        print(f"✅ 下載成功!")
        print(f"檔案名稱: {output_file}")
        print(f"檔案大小: {file_size:,} bytes")
        print(f"下載時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Try to read first few lines to verify content
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                print(f"檔案標頭: {first_line}")
        except UnicodeDecodeError:
            # Try with different encoding
            with open(output_file, 'r', encoding='big5') as f:
                first_line = f.readline().strip()
                print(f"檔案標頭: {first_line}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下載失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 處理檔案時發生錯誤: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("=" * 50)
    print("台灣股市觀察名單下載程式")
    print("=" * 50)
    
    success = download_stock_list()
    
    if success:
        print("\n程式執行完成! 🎉")
    else:
        print("\n程式執行失敗! ❌")
        exit(1)

if __name__ == "__main__":
    main()