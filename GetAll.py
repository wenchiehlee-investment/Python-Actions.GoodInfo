#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GetAll.py - Enhanced Batch Processing for GoodInfo.tw Data (v1.6.0)
Reads stock IDs from StockID_TWSE_TPEX.csv and calls GetGoodInfo.py for each stock
Supports all 7 data types with intelligent processing and CSV success tracking
Version: v15 - Smart Processing Priority System

SMART PROCESSING FEATURES:
1. Priority Processing: Handles failed/unprocessed stocks first
2. Smart Refresh: Full scan only when all data is successful but old  
3. Skip Up-to-date: Avoids re-processing recent successful downloads
4. Graceful Termination: Never lose progress on cancellation

Usage: python GetAll.py <parameter> [options]
Examples: 
  python GetAll.py 1          # Dividend data with smart processing
  python GetAll.py 6 --test   # Equity distribution for first 3 stocks (NEW!)
  python GetAll.py 7 --debug  # Quarterly performance with debug output (NEW!)
"""

import sys
import csv
import subprocess
import os
import time
import pandas as pd
import signal
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

# Global variables for graceful termination
current_results_data = {}
current_process_times = {}
current_stock_ids = []
current_parameter = ""
current_stock_mapping = {}

def signal_handler(signum, frame):
    """Handle termination signals gracefully - save CSV before exit"""
    print(f"\n🚨 收到終止信號 ({signum}) - 正在儲存進度...")
    
    if current_results_data and current_stock_ids:
        try:
            save_simple_csv_results(current_parameter, current_stock_ids, 
                                   current_results_data, current_process_times, 
                                   current_stock_mapping)
            processed_count = len(current_results_data)
            success_count = sum(1 for success in current_results_data.values() if success)
            print(f"✅ 緊急儲存完成: {processed_count} 股票已處理，{success_count} 成功")
        except Exception as e:
            print(f"❌ 緊急儲存失敗: {e}")
    
    print("👋 程式已安全終止")
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Add this function after existing functions in GetAll.py
def load_existing_csv_data(folder_name):
    """Load existing CSV data from the specific folder"""
    csv_filepath = os.path.join(folder_name, "download_results.csv")
    existing_data = {}
    
    if os.path.exists(csv_filepath):
        try:
            with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    filename = row.get('filename', '')
                    if filename:
                        existing_data[filename] = {
                            'last_update_time': row.get('last_update_time', 'NEVER'),
                            'success': row.get('success', 'false'),
                            'process_time': row.get('process_time', 'NOT_PROCESSED')
                        }
            print(f"📖 Loaded {len(existing_data)} existing records from {csv_filepath}")
        except Exception as e:
            print(f"⚠️ Warning: Could not load existing CSV: {e}")
    else:
        print(f"📝 No existing {csv_filepath} found - will create new file")
    
    return existing_data

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

def load_stock_mapping(csv_file):
    """Load stock ID to company name mapping from CSV file"""
    stock_mapping = {}
    try:
        encodings = ['utf-8', 'big5', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file, encoding=encoding)
                
                # Check if required columns exist (try different possible column names)
                stock_id_col = None
                company_name_col = None
                
                for col in df.columns:
                    if any(keyword in str(col) for keyword in ['代號', 'ID', 'Code', 'Stock']):
                        stock_id_col = col
                    elif any(keyword in str(col) for keyword in ['名稱', 'Name', 'Company', '公司']):
                        company_name_col = col
                
                if stock_id_col is not None and company_name_col is not None:
                    for _, row in df.iterrows():
                        stock_id = str(row[stock_id_col]).strip()
                        company_name = str(row[company_name_col]).strip()
                        if stock_id and company_name and stock_id != 'nan' and company_name != 'nan':
                            stock_mapping[stock_id] = company_name
                    
                    print(f"✅ 載入 {len(stock_mapping)} 個股票名稱對應")
                    break
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                continue
        
        if not stock_mapping:
            print("⚠️ 無法載入股票名稱對應，將使用預設名稱")
        
    except Exception as e:
        print(f"⚠️ 載入股票名稱對應時發生錯誤: {e}")
    
    return stock_mapping

def determine_stocks_to_process(parameter, all_stock_ids, stock_mapping):
    """Determine which stocks need processing based on existing CSV data"""
    
    # Determine folder based on data type
    if parameter == '7':
        folder = "StockBzPerformance1"
    else:
        folder_mapping = {
            '1': 'DividendDetail',
            '2': 'BasicInfo', 
            '3': 'StockDetail',
            '4': 'StockBzPerformance',
            '5': 'ShowSaleMonChart',
            '6': 'EquityDistribution'
        }
        folder = folder_mapping.get(parameter, f'DataType{parameter}')
    
    # Load existing CSV data
    existing_data = {}
    csv_filepath = os.path.join(folder, "download_results.csv")
    
    if os.path.exists(csv_filepath):
        try:
            with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    filename = row.get('filename', '')
                    if filename:
                        existing_data[filename] = {
                            'last_update_time': row.get('last_update_time', 'NEVER'),
                            'success': row.get('success', 'false'),
                            'process_time': row.get('process_time', 'NOT_PROCESSED')
                        }
        except Exception as e:
            print(f"⚠️ 無法讀取現有CSV數據: {e}")
    
    # Analyze current status
    today = datetime.now().strftime('%Y-%m-%d')
    failed_stocks = []
    not_processed_stocks = []
    successful_today = []
    successful_old = []
    
    for stock_id in all_stock_ids:
        company_name = stock_mapping.get(stock_id, f'股票{stock_id}')
        
        # Generate expected filename
        if parameter == '7':
            filename = f"StockBzPerformance1_{stock_id}_{company_name}_quarter.xls"
        else:
            filename = f"{folder}_{stock_id}_{company_name}.xls"
        
        if filename in existing_data:
            record = existing_data[filename]
            success = record['success'].lower() == 'true'
            process_time = record['process_time']
            
            if process_time == 'NOT_PROCESSED':
                not_processed_stocks.append(stock_id)
            elif not success:  # success=false
                failed_stocks.append(stock_id)
            elif success:  # success=true
                if process_time.startswith(today):
                    successful_today.append(stock_id)
                else:
                    successful_old.append(stock_id)
        else:
            # No record exists
            not_processed_stocks.append(stock_id)
    
    # Decision logic
    priority_stocks = failed_stocks + not_processed_stocks
    
    print(f"📊 處理狀態分析 ({folder}):")
    print(f"   ❌ 失敗股票: {len(failed_stocks)}")
    print(f"   ⏳ 未處理股票: {len(not_processed_stocks)}")  
    print(f"   ✅ 今日成功: {len(successful_today)}")
    print(f"   🕒 過期成功: {len(successful_old)}")
    
    if priority_stocks:
        print(f"🎯 優先處理策略: 處理 {len(priority_stocks)} 個失敗/未處理股票")
        return priority_stocks, "PRIORITY"
    elif successful_old and not successful_today:
        print(f"🔄 全面更新策略: 所有股票成功但資料過期，執行完整掃描")
        return all_stock_ids, "FULL_REFRESH"
    elif successful_today:
        print(f"✅ 無需處理: 所有股票今日已成功處理")
        return [], "UP_TO_DATE"
    else:
        print(f"🆕 初始掃描: 執行首次完整掃描")
        return all_stock_ids, "INITIAL_SCAN"
    """Load existing CSV data from the specific folder"""
    csv_filepath = os.path.join(folder_name, "download_results.csv")
    existing_data = {}
    
    if os.path.exists(csv_filepath):
        try:
            with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    filename = row.get('filename', '')
                    if filename:
                        existing_data[filename] = {
                            'last_update_time': row.get('last_update_time', 'NEVER'),
                            'success': row.get('success', 'false'),
                            'process_time': row.get('process_time', 'NOT_PROCESSED')
                        }
            print(f"📖 從 {csv_filepath} 載入 {len(existing_data)} 筆現有記錄")
        except Exception as e:
            print(f"⚠️ 警告: 無法載入現有 CSV: {e}")
    else:
        print(f"📝 找不到現有 {csv_filepath} - 將建立新檔案")
    
    return existing_data

def save_simple_csv_results(parameter, stock_ids, results_data, process_times, stock_mapping):
    """Save CSV in the specific folder - only current data type, always 118 rows"""
    
    # Determine folder based on data type
    if parameter == '7':
        folder = "StockBzPerformance1"
    else:
        folder_mapping = {
            '1': 'DividendDetail',
            '2': 'BasicInfo', 
            '3': 'StockDetail',
            '4': 'StockBzPerformance',
            '5': 'ShowSaleMonChart',
            '6': 'EquityDistribution'
        }
        folder = folder_mapping.get(parameter, f'DataType{parameter}')
    
    # Ensure folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"📁 建立資料夾: {folder}")
    
    csv_filepath = os.path.join(folder, "download_results.csv")
    
    # Load existing data from this folder only
    existing_data = load_existing_csv_data(folder)
    
    try:
        # Write CSV for this data type only
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['filename', 'last_update_time', 'success', 'process_time'])
            
            # Write data for ALL stocks for this data type
            for stock_id in stock_ids:
                company_name = stock_mapping.get(stock_id, f'股票{stock_id}')
                
                # Generate filename for current data type
                if parameter == '7':
                    filename = f"StockBzPerformance1_{stock_id}_{company_name}_quarter.xls"
                else:
                    filename = f"{folder}_{stock_id}_{company_name}.xls"
                
                # Check if we processed this stock in current run
                if stock_id in results_data:
                    # Current run data - get fresh info
                    file_path = os.path.join(folder, filename)
                    if os.path.exists(file_path):
                        last_update = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        last_update = 'NEVER'
                    
                    success = str(results_data[stock_id]).lower()
                    process_time = process_times.get(stock_id, 'NOT_PROCESSED')
                else:
                    # Not processed in current run - use existing data if available
                    if filename in existing_data:
                        existing_record = existing_data[filename]
                        last_update = existing_record['last_update_time']
                        success = existing_record['success']
                        process_time = existing_record['process_time']
                    else:
                        # No existing data - set defaults
                        last_update = 'NEVER'
                        success = 'false'
                        process_time = 'NOT_PROCESSED'
                
                # Write row
                writer.writerow([filename, last_update, success, process_time])
        
        print(f"📊 CSV 結果已儲存: {csv_filepath}")
        
        # Enhanced summary for this data type only
        if results_data:  # Only show summary if we processed stocks
            total_stocks = len(stock_ids)
            processed_count = len(results_data)
            success_count = sum(1 for success in results_data.values() if success)
            success_rate = (success_count / processed_count * 100) if processed_count > 0 else 0
            
            print(f"📈 {folder} 摘要:")
            print(f"   CSV 總股票數: {total_stocks}")
            print(f"   本次處理股票數: {processed_count}")
            print(f"   本次成功數: {success_count}")
            print(f"   本次成功率: {success_rate:.1f}%")
            print(f"   CSV 位置: {csv_filepath}")
        
    except Exception as e:
        print(f"❌ 儲存 CSV 時發生錯誤: {e}")

def run_get_good_info(stock_id, parameter, debug_mode=False, direct_mode=False):
    """Run GetGoodInfo.py for a single stock with enhanced error handling"""
    try:
        cmd = ['python', 'GetGoodInfo.py', str(stock_id), str(parameter)]
        print(f"執行: {' '.join(cmd)}")
        
        # Set environment to use UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Adjust timeout based on data type (special workflows need more time)
        timeout = 300 if parameter in ['5', '7'] else 100  # Extra time for special workflows
        
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
    """Show enhanced usage information for v1.6.0"""
    print("=" * 70)
    print("🚀 Enhanced Batch Stock Data Downloader (v1.6.0)")
    print("📊 Complete 7 Data Types with Smart Processing Priority")
    print("=" * 70)
    print()
    print("🧠 SMART PROCESSING FEATURES:")
    print("   🎯 Priority: Handles failed/unprocessed stocks first")
    print("   🔄 Smart Refresh: Full scan only when data is old")
    print("   ⏭️ Skip Recent: Avoids re-processing today's successful downloads") 
    print("   🛡️ Safe: Never lose progress on cancellation")
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
    print("   python GetAll.py 1          # Smart processing: dividend data")
    print("   python GetAll.py 4          # Smart processing: business performance")  
    print("   python GetAll.py 5          # Smart processing: monthly revenue")
    print("   python GetAll.py 6          # Smart processing: equity distribution 🆕")
    print("   python GetAll.py 7          # Smart processing: quarterly performance 🆕")
    print("   python GetAll.py 2 --test   # Manual: basic info (test mode)")
    print("   python GetAll.py 6 --debug  # NEW! Equity with debug output")
    print("   python GetAll.py 7 --test   # NEW! Quarterly performance (test)")
    print()
    print("💡 Smart Processing Notes:")
    print("   • Automatically prioritizes failed/unprocessed stocks")
    print("   • Skips recent successful downloads to save time")
    print("   • Full refresh only when all data is successful but old")
    print("   • Delete CSV file to force complete re-processing")
    print()
    print("⏰ GitHub Actions Automation Schedule:")
    print("   Daily 8-12 PM UTC: Types 1, 4, 5, 6, 7 (All automated)")
    print("   Manual 24/7: Types 2, 3 (On-demand data)")
    print()

def main():
    """Enhanced main function with CSV result tracking and graceful termination"""
    global current_results_data, current_process_times, current_stock_ids, current_parameter, current_stock_mapping
    
    print("=" * 70)
    print("🚀 Enhanced Batch Stock Data Downloader (v1.6.0)")
    print("📊 Complete 7 Data Types with Smart Processing Priority")
    print("🛡️ Graceful termination protection enabled")
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
    
    # Load stock mapping for CSV export
    print(f"[讀取] 載入股票名稱對應...")
    stock_mapping = load_stock_mapping(csv_file)
    
    # Set global variables for signal handler
    current_stock_ids = stock_ids
    current_parameter = parameter  
    current_stock_mapping = stock_mapping
    
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
                                  timeout=600)
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
    
    # SMART PROCESSING: Determine which stocks actually need processing
    print("🧠 智慧處理分析中...")
    stocks_to_process, processing_strategy = determine_stocks_to_process(parameter, stock_ids, stock_mapping)
    
    if not stocks_to_process:
        print("✅ 所有資料都是最新的，無需處理！")
        print("📊 產生 CSV 確認...")
        save_simple_csv_results(parameter, stock_ids, {}, {}, stock_mapping)
        print("🎉 任務完成！")
        return
    
    # Update the processing list
    original_count = len(stock_ids)
    if test_mode and processing_strategy != "UP_TO_DATE":
        stocks_to_process = stocks_to_process[:3]  # Apply test mode limit
        print(f"[測試模式] 限制處理 {len(stocks_to_process)} 支股票")
    
    processing_count = len(stocks_to_process)
    print(f"📋 處理策略: {processing_strategy}")
    print(f"📊 處理範圍: {processing_count}/{original_count} 支股票")
    print("-" * 70)
    
    # Process each stock with detailed tracking and incremental CSV updates
    success_count = 0
    failed_count = 0
    results_data = {}  # stock_id -> True/False
    process_times = {}  # stock_id -> process_time_string
    
    # Generate initial CSV with all stocks (preserving existing data)
    print(f"📊 初始化 CSV 檔案...")
    save_simple_csv_results(parameter, stock_ids, {}, {}, stock_mapping)
    
    # Process only the selected stocks (smart processing)
    for i, stock_id in enumerate(stocks_to_process, 1):
        print(f"\n[{i}/{len(stocks_to_process)}] 處理股票: {stock_id}")
        
        # Record process time when we start processing this stock
        current_process_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        process_times[stock_id] = current_process_time
        
        success = run_get_good_info(stock_id, parameter, debug_mode, direct_mode)
        results_data[stock_id] = success
        
        # Update global variables for signal handler
        current_results_data = results_data.copy()
        current_process_times = process_times.copy()
        
        if success:
            success_count += 1
        else:
            failed_count += 1
        
        # INCREMENTAL CSV UPDATE - Save progress after each stock
        # This ensures we don't lose progress if cancelled
        try:
            save_simple_csv_results(parameter, stock_ids, results_data, process_times, stock_mapping)
            print(f"   📄 CSV 已更新 ({i}/{len(stocks_to_process)} 完成)")
        except Exception as e:
            print(f"   ⚠️ CSV 更新失敗: {e}")
        
        # Add small delay to avoid overwhelming the target system
        # Longer delay for special workflows
        delay = 2 if parameter in ['5', '7'] else 1
        if i < len(stocks_to_process):  # Don't sleep after the last item
            time.sleep(delay)
    
    # Final CSV generation (redundant but ensures completeness)
    print("\n" + "=" * 70)
    print("📊 最終 CSV 結果...")
    save_simple_csv_results(parameter, stock_ids, results_data, process_times, stock_mapping)
    
    # Enhanced Summary
    print("\n" + "=" * 70)
    print("🎯 Enhanced Execution Summary (v1.5.0) - Smart Processing")
    print("=" * 70)
    print(f"📊 資料類型: {data_desc}")
    print(f"📋 處理策略: {processing_strategy}")
    print(f"總股票數: {original_count} 支")
    print(f"需處理股票數: {processing_count} 支") 
    print(f"實際處理: {len(stocks_to_process)} 支股票")
    print(f"✅ 成功: {success_count} 支")
    print(f"❌ 失敗: {failed_count} 支")
    if processing_count > 0:
        print(f"📈 本次成功率: {success_count/processing_count*100:.1f}%")
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
    
    # Explain the processing strategy
    strategy_explanations = {
        "PRIORITY": "🎯 優先處理失敗或未處理的股票，提高整體成功率",
        "FULL_REFRESH": "🔄 所有資料過期，執行完整更新以確保資料新鮮度", 
        "UP_TO_DATE": "✅ 所有資料都是最新的，無需處理",
        "INITIAL_SCAN": "🆕 首次掃描，建立完整的資料基線"
    }
    
    if processing_strategy in strategy_explanations:
        print(f"💡 策略說明: {strategy_explanations[processing_strategy]}")
    
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