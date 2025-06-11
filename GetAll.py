#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GetAll.py
Reads stock IDs from StockID_TWSE_TPEX.csv and calls GetGoodInfo.py for each stock
Usage: python GetAll.py <parameter>
Example: python GetAll.py 1
"""

import sys
import csv
import subprocess
import os
import time
from datetime import datetime

# Try to set UTF-8 encoding for Windows console
try:
    if sys.platform.startswith('win'):
        import locale
        # Set console to handle UTF-8 if possible
        os.system('chcp 65001 > nul 2>&1')
except:
    pass

def read_stock_ids(csv_file):
    """Read stock IDs from CSV file"""
    stock_ids = []
    
    # Try different encodings
    encodings = ['utf-8', 'big5', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                # Try to detect if first line is header
                first_line = f.readline()
                f.seek(0)
                
                reader = csv.reader(f)
                
                # Skip header if it looks like one (contains Chinese characters or "StockID")
                first_row = next(reader)
                if any('股' in str(cell) or 'StockID' in str(cell) or 'ID' in str(cell) or '代號' in str(cell) or 'Code' in str(cell) for cell in first_row):
                    print(f"偵測到標頭行: {first_row}")
                else:
                    # First row is data, add it back
                    stock_id = first_row[0].strip() if first_row and len(first_row) > 0 else ""
                    if stock_id and stock_id.isdigit() and 4 <= len(stock_id) <= 6:
                        stock_ids.append(stock_id)
                
                # Read remaining rows
                for row in reader:
                    if row and len(row) > 0 and row[0].strip():
                        # Assume stock ID is in first column
                        stock_id = row[0].strip()
                        # Basic validation - stock IDs are usually 4-6 digits
                        if stock_id.isdigit() and 4 <= len(stock_id) <= 6:
                            stock_ids.append(stock_id)
            
            print(f"成功使用 {encoding} 編碼讀取檔案")
            break
            
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"使用 {encoding} 編碼時發生錯誤: {e}")
            continue
    
    return stock_ids

def run_get_good_info(stock_id, parameter, debug_mode=False, direct_mode=False):
    """Run GetGoodInfo.py for a single stock"""
    try:
        cmd = ['python', 'GetGoodInfo.py', str(stock_id), str(parameter)]
        print(f"執行: {' '.join(cmd)}")
        
        # Set environment to use UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Run the command
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=60,  # 60 second timeout
                              env=env,
                              encoding='utf-8',
                              errors='replace')  # Replace problematic characters
        
        if result.returncode == 0:
            print(f"[OK] {stock_id} 處理成功")
            if result.stdout:
                print(f"輸出: {result.stdout.strip()}")
        else:
            print(f"[FAIL] {stock_id} 處理失敗 (退出碼: {result.returncode})")
            
            # Show both stdout and stderr
            if result.stdout and result.stdout.strip():
                print(f"標準輸出: {result.stdout.strip()}")
            
            if result.stderr and result.stderr.strip():
                error_msg = result.stderr.strip()
                if debug_mode:
                    print(f"標準錯誤: {error_msg}")
                else:
                    error_lines = error_msg.split('\n')
                    if len(error_lines) > 3:
                        print(f"標準錯誤: {error_lines[0]}")
                        print(f"         {error_lines[1]}")
                        print(f"         ... (共 {len(error_lines)} 行錯誤，使用 --debug 查看完整訊息)")
                    else:
                        print(f"標準錯誤: {error_msg}")
            
            if not result.stdout.strip() and not result.stderr.strip():
                print("錯誤: 無任何輸出訊息")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {stock_id} 處理超時")
        return False
    except Exception as e:
        print(f"[ERROR] {stock_id} 執行時發生錯誤: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("批次股票資訊下載程式")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("使用方法: python GetAll.py <參數> [選項]")
        print("範例: python GetAll.py 1")
        print("測試: python GetAll.py 1 --test  (只處理前3支股票)")
        print("除錯: python GetAll.py 1 --debug (顯示完整錯誤訊息)")
        print("直接測試: python GetAll.py 1 --direct (不使用subprocess，直接運行)")
        sys.exit(1)
    
    parameter = sys.argv[1]
    test_mode = '--test' in sys.argv
    debug_mode = '--debug' in sys.argv
    direct_mode = '--direct' in sys.argv
    csv_file = "StockID_TWSE_TPEX.csv"
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"[ERROR] 找不到檔案: {csv_file}")
        print("請先執行 Get觀察名單.py 下載股票清單")
        sys.exit(1)
    
    # Check if GetGoodInfo.py exists
    if not os.path.exists("GetGoodInfo.py"):
        print("[ERROR] 找不到 GetGoodInfo.py")
        print("請確認 GetGoodInfo.py 存在於同一目錄下")
        sys.exit(1)
    
    # Read stock IDs
    print(f"[讀取] 讀取股票清單: {csv_file}")
    stock_ids = read_stock_ids(csv_file)
    
    if not stock_ids:
        print("[ERROR] 未找到有效的股票代碼")
        sys.exit(1)
    
    print(f"[統計] 找到 {len(stock_ids)} 支股票")
    print(f"前5支股票: {stock_ids[:5]}")  # Show first 5 for verification
    
    if test_mode:
        stock_ids = stock_ids[:3]  # Only process first 3 stocks in test mode
        print(f"[測試模式] 只處理前 {len(stock_ids)} 支股票")
    
    if debug_mode:
        print("[除錯模式] 將顯示完整錯誤訊息")
    
    if direct_mode:
        print("[直接模式] 測試 GetGoodInfo.py 是否可正常執行")
        # Test GetGoodInfo.py directly first
        print("測試執行: python GetGoodInfo.py")
        try:
            result = subprocess.run(['python', 'GetGoodInfo.py'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            print(f"直接執行結果 - 退出碼: {result.returncode}")
            if result.stdout:
                print(f"標準輸出: {result.stdout}")
            if result.stderr:
                print(f"標準錯誤: {result.stderr}")
        except Exception as e:
            print(f"直接執行失敗: {e}")
        print("-" * 40)
    print(f"參數: {parameter}")
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Process each stock
    success_count = 0
    failed_count = 0
    
    for i, stock_id in enumerate(stock_ids, 1):
        print(f"\n[{i}/{len(stock_ids)}] 處理股票: {stock_id}")
        
        success = run_get_good_info(stock_id, parameter, debug_mode, direct_mode)
        
        if success:
            success_count += 1
        else:
            failed_count += 1
        
        # Add small delay to avoid overwhelming the target system
        if i < len(stock_ids):  # Don't sleep after the last item
            time.sleep(1)  # 1 second delay
    
    # Summary
    print("\n" + "=" * 60)
    print("執行結果統計")
    print("=" * 60)
    print(f"總共處理: {len(stock_ids)} 支股票")
    print(f"成功: {success_count} 支")
    print(f"失敗: {failed_count} 支")
    print(f"成功率: {success_count/len(stock_ids)*100:.1f}%")
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed_count > 0:
        print(f"\n[警告] 有 {failed_count} 支股票處理失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()