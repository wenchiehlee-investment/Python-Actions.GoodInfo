#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GetAll.py - Enhanced Batch Processing for GoodInfo.tw Data (v1.5.0)
Reads stock IDs from StockID_TWSE_TPEX.csv and calls GetGoodInfo.py for each stock
Supports all 7 data types with intelligent processing

Usage: python GetAll.py <parameter> [options]
Examples: 
  python GetAll.py 1          # Dividend data for all stocks
  python GetAll.py 6 --test   # Equity distribution for first 3 stocks (NEW!)
  python GetAll.py 7 --debug  # Quarterly performance with debug output (NEW!)
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

# Data type descriptions for v1.5.0
DATA_TYPE_DESCRIPTIONS = {
    '1': 'Dividend Policy (殖利率政策) - Daily automation',
    '2': 'Basic Info (基本資料) - Manual only',
    '3': 'Stock Details (個股市況) - Manual only',
    '4': 'Business Performance (經營績效) - Daily automation',
    '5': 'Monthly Revenue (每月營收) - Daily automation',
    '6': 'Equity Distribution (股東結構) - Daily automation (NEW!)',
    '7': 'Quarterly Performance (每季經營績效) - Daily automation (NEW!)'
}

def read_stock_ids(csv_file):
    """Read stock IDs from CSV file with enhanced encoding support"""
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
    """Run GetGoodInfo.py for a single stock with enhanced error handling"""
    try:
        cmd = ['python', 'GetGoodInfo.py', str(stock_id), str(parameter)]
        print(f"執行: {' '.join(cmd)}")
        
        # Set environment to use UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Adjust timeout based on data type (special workflows need more time)
        timeout = 150 if parameter in ['5', '7'] else 120  # Extra time for special workflows
        
        # Run the command
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=timeout,
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
        timeout_msg = f"[TIMEOUT] {stock_id} 處理超時"
        if parameter in ['5', '7']:
            timeout_msg += f" (資料類型 {parameter} 需要特殊處理流程，可能需要更長時間)"
        print(timeout_msg)
        return False
    except Exception as e:
        print(f"[ERROR] {stock_id} 執行時發生錯誤: {e}")
        return False

def show_enhanced_usage():
    """Show enhanced usage information for v1.5.0"""
    print("=" * 70)
    print("🚀 Enhanced Batch Stock Data Downloader (v1.5.0)")
    print("📊 Complete 7 Data Types Support with Smart Automation")
    print("=" * 70)
    print()
    print("📋 Usage:")
    print("   python GetAll.py <DATA_TYPE> [OPTIONS]")
    print()
    print("🔢 Data Types (Complete Coverage):")
    for dt, desc in DATA_TYPE_DESCRIPTIONS.items():
        new_badge = " 🆕" if dt in ['6', '7'] else ""
        print(f"   {dt} = {desc}{new_badge}")
    print()
    print("🔧 Options:")
    print("   --test   = Process only first 3 stocks (testing)")
    print("   --debug  = Show detailed error messages")
    print("   --direct = Simple execution mode (compatibility test)")
    print()
    print("📊 Enhanced Examples:")
    print("   python GetAll.py 1          # Daily automated: Dividend data")
    print("   python GetAll.py 4          # Daily automated: Business performance")
    print("   python GetAll.py 5          # Daily automated: Monthly revenue")
    print("   python GetAll.py 6          # Weekly automated: Equity distribution 🆕")
    print("   python GetAll.py 7          # Monthly automated: Quarterly performance 🆕")
    print("   python GetAll.py 2 --test   # Manual: Basic info (test mode)")
    print("   python GetAll.py 6 --debug  # NEW! Equity with debug output")
    print("   python GetAll.py 7 --test   # NEW! Quarterly performance (test)")
    print()
    print("⏰ GitHub Actions Automation Schedule:")
    print("   Daily 8-12 PM UTC: Types 1, 4, 5, 6, 7 (All automated)")
    print("   Manual 24/7: Types 2, 3 (On-demand data)")
    print()

def main():
    """Enhanced main function with comprehensive 7-type support"""
    print("=" * 70)
    print("🚀 Enhanced Batch Stock Data Downloader (v1.5.0)")
    print("📊 Complete 7 Data Types with Intelligent Processing")
    print("=" * 70)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        show_enhanced_usage()
        print("❌ Error: Please provide DATA_TYPE parameter")
        print("💡 Examples:")
        print("   python GetAll.py 1      # Dividend data")
        print("   python GetAll.py 6      # NEW! Equity distribution")
        print("   python GetAll.py 7      # NEW! Quarterly performance")
        sys.exit(1)
    
    parameter = sys.argv[1]
    test_mode = '--test' in sys.argv
    debug_mode = '--debug' in sys.argv
    direct_mode = '--direct' in sys.argv
    csv_file = "StockID_TWSE_TPEX.csv"
    
    # Validate data type
    if parameter not in DATA_TYPE_DESCRIPTIONS:
        print(f"❌ Invalid data type: {parameter}")
        print("✅ Valid data types:")
        for dt, desc in DATA_TYPE_DESCRIPTIONS.items():
            new_badge = " 🆕" if dt in ['6', '7'] else ""
            print(f"   {dt} = {desc}{new_badge}")
        sys.exit(1)
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"[ERROR] 找不到檔案: {csv_file}")
        print("請先執行 Get觀察名單.py 下載股票清單")
        print("命令: python Get觀察名單.py")
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
    
    # Get data type description
    data_desc = DATA_TYPE_DESCRIPTIONS.get(parameter, f"Data Type {parameter}")
    
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
    
    print(f"📊 資料類型: {data_desc}")
    print(f"參數: {parameter}")
    
    # Show special workflow information
    if parameter == '5':
        print("🔄 特殊流程: 每月營收 - 自動點擊 '查20年' 按鈕")
    elif parameter == '6':
        print("📈 NEW! 股東結構分析 - 標準 XLS 下載")
    elif parameter == '7':
        print("🔄 NEW! 特殊流程: 每季經營績效 - 特殊 URL + 自動點擊 '查60年' 按鈕")
    
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
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
        # Longer delay for special workflows
        delay = 2 if parameter in ['5', '7'] else 1
        if i < len(stock_ids):  # Don't sleep after the last item
            time.sleep(delay)
    
    # Enhanced Summary
    print("\n" + "=" * 70)
    print("🎯 Enhanced Execution Summary (v1.5.0)")
    print("=" * 70)
    print(f"📊 資料類型: {data_desc}")
    print(f"總共處理: {len(stock_ids)} 支股票")
    print(f"✅ 成功: {success_count} 支")
    print(f"❌ 失敗: {failed_count} 支")
    print(f"📈 成功率: {success_count/len(stock_ids)*100:.1f}%")
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show automation information
    automation_info = {
        '1': '每日自動化 (Daily 8 AM UTC)',
        '4': '每日自動化 (Daily 9 AM UTC)', 
        '5': '每日自動化 (Daily 10 AM UTC)',
        '6': '每日自動化 (Daily 11 AM UTC) 🆕',
        '7': '每日自動化 (Daily 12 PM UTC) 🆕',
        '2': '手動執行 (Manual trigger only)',
        '3': '手動執行 (Manual trigger only)'
    }
    
    automation = automation_info.get(parameter, '手動執行')
    print(f"🤖 自動化狀態: {automation}")
    
    if failed_count > 0:
        print(f"\n⚠️ 警告: 有 {failed_count} 支股票處理失敗")
        print("💡 建議:")
        print("   • 使用 --debug 查看詳細錯誤訊息")
        print("   • 使用 --test 先測試少數股票")
        print("   • 檢查網路連線狀況")
        if parameter in ['5', '7']:
            print(f"   • 資料類型 {parameter} 使用特殊處理流程，可能需要更多時間")
    
    if parameter in ['6', '7']:
        print(f"\n🆕 NEW! 資料類型 {parameter} 已成功處理!")
        print("📁 請檢查對應資料夾中的檔案")

if __name__ == "__main__":
    main()