#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GetAll.py - Enhanced Batch Processing for GoodInfo.tw Data (v1.7.0-FIXED)
Reads stock IDs from StockID_TWSE_TPEX.csv and calls GetGoodInfo.py for each stock
Supports all 9 data types with intelligent processing and CSV success tracking
Version: v1.7.0-FIXED - Complete 9 Data Types + 24-Hour Freshness Policy + CSV Update Bug Fix

SMART PROCESSING FEATURES:
1. Priority Processing: Handles failed/unprocessed stocks first
2. 24-Hour Freshness Policy: Data older than 24 hours is considered expired (NEW!)
3. Smart Refresh: Full scan when data is expired or failed
4. Graceful Termination: Never lose progress on cancellation
5. COMPLETE 9 DATA TYPES: Added Quarterly Analysis (Type 9)
6. ENHANCED AUTOMATION: 6-day weekly schedule + daily revenue
7. CSV UPDATE BUG FIX: Properly updates process_time for reprocessed stocks (FIXED!)

Usage: python GetAll.py <parameter> [options]
Examples: 
  python GetAll.py 1          # Dividend data with smart processing
  python GetAll.py 6 --test   # Equity distribution for first 3 stocks
  python GetAll.py 7 --debug  # Quarterly performance with debug output
  python GetAll.py 8 --test   # EPS x PER weekly for first 3 stocks
  python GetAll.py 9 --test   # Quarterly analysis for first 3 stocks (NEW!)
"""

import sys
import csv
import subprocess
import os
import time
import pandas as pd
import signal
from datetime import datetime, timedelta

# Try to set UTF-8 encoding for Windows console
try:
    if sys.platform.startswith('win'):
        import locale
        # Set console to handle UTF-8 if possible
        os.system('chcp 65001 > nul 2>&1')
except:
    pass

# Data type descriptions for v1.7.0 - Complete 9 Data Types (Enhanced Weekly + Daily Schedule)
DATA_TYPE_DESCRIPTIONS = {
    '1': 'Dividend Policy (股利政策) - Weekly automation (Monday 8 AM UTC)',
    '2': 'Basic Info (基本資料) - Manual only',
    '3': 'Stock Details (個股市況) - Manual only',
    '4': 'Business Performance (經營績效) - Weekly automation (Tuesday 8 AM UTC)',
    '5': 'Monthly Revenue (每月營收) - Daily automation (12 PM UTC)',
    '6': 'Equity Distribution (股權結構) - Weekly automation (Wednesday 8 AM UTC)',
    '7': 'Quarterly Performance (每季經營績效) - Weekly automation (Thursday 8 AM UTC)',
    '8': 'EPS x PER Weekly (每週EPS本益比) - Weekly automation (Friday 8 AM UTC)',
    '9': 'Quarterly Analysis (各季詳細統計資料) - Weekly automation (Saturday 8 AM UTC) - NEW!'
}

# Global variables for graceful termination
current_results_data = {}
current_process_times = {}
current_stock_ids = []
current_parameter = ""
current_stock_mapping = {}

def signal_handler(signum, frame):
    """Handle termination signals gracefully - save CSV before exit"""
    print(f"\n警告 收到終止信號 ({signum}) - 正在儲存進度...")
    
    if current_results_data and current_stock_ids:
        try:
            save_simple_csv_results(current_parameter, current_stock_ids, 
                                   current_results_data, current_process_times, 
                                   current_stock_mapping)
            processed_count = len(current_results_data)
            success_count = sum(1 for success in current_results_data.values() if success)
            print(f"緊急儲存完成: {processed_count} 股票已處理，{success_count} 成功")
        except Exception as e:
            print(f"緊急儲存失敗: {e}")
    
    print("程式已安全終止")
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

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
                    print(f"偵測到標題行: {first_row}")
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
                    
                    print(f"載入 {len(stock_mapping)} 個股票名稱對應")
                    break
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                continue
        
        if not stock_mapping:
            print("無法載入股票名稱對應，將使用預設名稱")
        
    except Exception as e:
        print(f"載入股票名稱對應時發生錯誤: {e}")
    
    return stock_mapping

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
            print(f"從 {csv_filepath} 載入 {len(existing_data)} 筆現有記錄")
        except Exception as e:
            print(f"警告: 無法載入現有 CSV: {e}")
    else:
        print(f"找不到現有 {csv_filepath} - 將建立新檔案")
    
    return existing_data

def safe_parse_datetime(date_string):
    """Safely parse datetime string with fallback handling"""
    if date_string in ['NOT_PROCESSED', 'NEVER', '', None]:
        return None
    
    try:
        return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            # Try alternative format
            return datetime.strptime(date_string, '%Y-%m-%d')
        except ValueError:
            return None

def determine_stocks_to_process(parameter, all_stock_ids, stock_mapping):
    """Determine which stocks need processing based on 24-hour freshness policy"""
    
    # Determine folder based on data type (Updated for Type 9)
    folder_mapping = {
        '1': 'DividendDetail',
        '2': 'BasicInfo', 
        '3': 'StockDetail',
        '4': 'StockBzPerformance',
        '5': 'ShowSaleMonChart',
        '6': 'EquityDistribution',
        '7': 'StockBzPerformance1',
        '8': 'ShowK_ChartFlow',
        '9': 'StockHisAnaQuar'
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
            print(f"無法讀取現有CSV數據: {e}")
    
    # Analyze current status with 24-hour freshness policy
    now = datetime.now()
    failed_stocks = []
    not_processed_stocks = []
    fresh_success = []       # Within 24 hours AND success=true
    expired_success = []     # >24 hours old but success=true (needs reprocessing)
    
    for stock_id in all_stock_ids:
        company_name = stock_mapping.get(stock_id, f'股票{stock_id}')
        
        # Generate expected filename (Updated for Type 9)
        if parameter == '7':
            filename = f"StockBzPerformance1_{stock_id}_{company_name}_quarter.xls"
        else:
            filename = f"{folder}_{stock_id}_{company_name}.xls"
        
        if filename in existing_data:
            record = existing_data[filename]
            success = record['success'].lower() == 'true'
            process_time_str = record['process_time']
            
            if process_time_str == 'NOT_PROCESSED':
                not_processed_stocks.append(stock_id)
            elif not success:  # success=false
                failed_stocks.append(stock_id)
            elif success:  # success=true, check freshness
                process_time = safe_parse_datetime(process_time_str)
                if process_time:
                    # Calculate hours difference
                    time_diff = now - process_time
                    hours_ago = time_diff.total_seconds() / 3600
                    
                    if hours_ago <= 24:
                        fresh_success.append(stock_id)      # Fresh, no need to reprocess
                    else:
                        expired_success.append(stock_id)    # Expired, treat as needs reprocessing
                else:
                    # Can't parse process_time, treat as not processed
                    not_processed_stocks.append(stock_id)
        else:
            # No record exists
            not_processed_stocks.append(stock_id)
    
    # Decision logic with 24-hour freshness policy
    priority_stocks = failed_stocks + not_processed_stocks + expired_success
    
    print(f"處理狀態分析 ({folder}) - 24小時新鮮度策略:")
    print(f"   失敗股票: {len(failed_stocks)}")
    print(f"   未處理股票: {len(not_processed_stocks)}")  
    print(f"   新鮮成功 (24小時內): {len(fresh_success)}")
    print(f"   過期成功 (>24小時): {len(expired_success)}")
    
    if priority_stocks:
        reprocess_reasons = []
        if failed_stocks:
            reprocess_reasons.append(f"{len(failed_stocks)}個失敗")
        if not_processed_stocks:
            reprocess_reasons.append(f"{len(not_processed_stocks)}個未處理")
        if expired_success:
            reprocess_reasons.append(f"{len(expired_success)}個過期成功")
        
        reason_str = "、".join(reprocess_reasons)
        print(f"需要處理策略: 處理 {len(priority_stocks)} 個股票 ({reason_str})")
        return priority_stocks, "REPROCESS_NEEDED"
    elif fresh_success:
        print(f"無需處理: 所有 {len(fresh_success)} 個股票在24小時內已成功處理")
        return [], "UP_TO_DATE"
    else:
        print(f"初始掃描: 執行首次完整掃描")
        return all_stock_ids, "INITIAL_SCAN"

def save_simple_csv_results(parameter, stock_ids, results_data, process_times, stock_mapping):
    """
    Save CSV in the specific folder with Type 9 support and FIXED CSV update logic
    
    CRITICAL FIX: Properly updates process_time for reprocessed stocks instead of preserving old timestamps
    """
    
    # Determine folder based on data type (Updated for Type 9)
    folder_mapping = {
        '1': 'DividendDetail',
        '2': 'BasicInfo', 
        '3': 'StockDetail',
        '4': 'StockBzPerformance',
        '5': 'ShowSaleMonChart',
        '6': 'EquityDistribution',
        '7': 'StockBzPerformance1',
        '8': 'ShowK_ChartFlow',
        '9': 'StockHisAnaQuar'
    }
    folder = folder_mapping.get(parameter, f'DataType{parameter}')
    
    # Ensure folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"建立資料夾: {folder}")
    
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
                
                # Generate filename for current data type (Updated for Type 9)
                if parameter == '7':
                    filename = f"StockBzPerformance1_{stock_id}_{company_name}_quarter.xls"
                else:
                    filename = f"{folder}_{stock_id}_{company_name}.xls"
                
                # CRITICAL FIX: Check if we processed this stock in current run
                if stock_id in results_data:
                    # CURRENT RUN DATA - Always use new timestamps for reprocessed stocks
                    success = str(results_data[stock_id]).lower()
                    process_time = process_times.get(stock_id, 'NOT_PROCESSED')
                    
                    print(f"DEBUG: 處理股票 {stock_id} - 成功: {success}, 處理時間: {process_time}")
                    
                    if success == 'true':
                        # SUCCESS - get current file modification time (file was updated)
                        file_path = os.path.join(folder, filename)
                        if os.path.exists(file_path):
                            last_update = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            last_update = 'NEVER'  # This shouldn't happen if success=true
                    else:
                        # FAILED - file was NOT updated, but still preserve old last_update_time if exists
                        if filename in existing_data:
                            last_update = existing_data[filename]['last_update_time']
                        else:
                            last_update = 'NEVER'  # Never successfully downloaded
                    
                    # IMPORTANT: Always use the NEW process_time for reprocessed stocks
                    # Don't fall back to existing_data process_time for reprocessed stocks
                    
                else:
                    # NOT processed in current run - use existing data if available
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
        
        print(f"CSV結果已儲存: {csv_filepath}")
        
        # Enhanced summary for this data type only
        if results_data:  # Only show summary if we processed stocks
            total_stocks = len(stock_ids)
            processed_count = len(results_data)
            success_count = sum(1 for success in results_data.values() if success)
            success_rate = (success_count / processed_count * 100) if processed_count > 0 else 0
            
            print(f"{folder} 摘要:")
            print(f"   CSV 總股票數: {total_stocks}")
            print(f"   本次處理股票數: {processed_count}")
            print(f"   本次成功數: {success_count}")
            print(f"   本次成功率: {success_rate:.1f}%")
            print(f"   CSV 位置: {csv_filepath}")
        
        # ADDITIONAL DEBUG: Show which stocks were reprocessed
        if results_data:
            reprocessed_stocks = [stock_id for stock_id in results_data.keys()]
            print(f"DEBUG: 本次重新處理的股票: {len(reprocessed_stocks)} 支")
            if len(reprocessed_stocks) <= 10:
                print(f"DEBUG: 重新處理列表: {', '.join(reprocessed_stocks)}")
        
    except Exception as e:
        print(f"儲存 CSV 時發生錯誤: {e}")

def run_get_good_info(stock_id, parameter, debug_mode=False, direct_mode=False):
    """Run GetGoodInfo.py for a single stock with enhanced error handling"""
    try:
        cmd = ['python', 'GetGoodInfo.py', str(stock_id), str(parameter)]
        print(f"執行: {' '.join(cmd)}")
        
        # Set environment to use UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Adjust timeout based on data type (special workflows need more time)
        timeout = 360 if parameter in ['5', '7', '8'] else 100  # Standard timeout for Type 9
        
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
        if parameter in ['5', '7', '8']:
            timeout_msg += f" (資料類型 {parameter} 需要特殊處理流程，可能需要更長時間)"
        elif parameter == '9':
            timeout_msg += f" (資料類型 {parameter} 使用標準流程)"
        print(timeout_msg)
        return False
    except Exception as e:
        print(f"[ERROR] {stock_id} 執行時發生錯誤: {e}")
        return False

def show_enhanced_usage():
    """Show enhanced usage information for v1.7.0-FIXED"""
    print("=" * 70)
    print("Enhanced Batch Stock Data Downloader (v1.7.0-FIXED)")
    print("Complete 9 Data Types with Enhanced Weekly Automation")
    print("24-Hour Freshness Policy + CSV Update Bug Fix (FIXED!)")
    print("=" * 70)
    print()
    print("SMART PROCESSING FEATURES:")
    print("   Priority: Handles failed/unprocessed stocks first")
    print("   24-Hour Freshness: Data older than 24 hours needs reprocessing (NEW!)")
    print("   Smart Refresh: Full scan when data is expired or failed")
    print("   Safe: Never lose progress on cancellation")
    print("   COMPLETE: All 9 data types with quarterly analysis support")
    print("   CSV FIX: Properly updates timestamps for reprocessed stocks (FIXED!)")
    print()
    print("Usage:")
    print("   python GetAll.py <DATA_TYPE> [OPTIONS]")
    print()
    print("Data Types (Complete 9 Data Types - v1.7.0):")
    for dt, desc in DATA_TYPE_DESCRIPTIONS.items():
        new_badge = " - NEW!" if dt == '9' else ""
        print(f"   {dt} = {desc}{new_badge}")
    print()
    print("Options:")
    print("   --test   = Process only first 3 stocks (testing)")
    print("   --debug  = Show detailed error messages")
    print("   --direct = Simple execution mode (compatibility test)")
    print()
    print("Enhanced Examples (v1.7.0-FIXED):")
    print("   python GetAll.py 1          # Smart processing: dividend data")
    print("   python GetAll.py 4          # Smart processing: business performance")  
    print("   python GetAll.py 5          # Smart processing: monthly revenue (CSV BUG FIXED!)")
    print("   python GetAll.py 6          # Smart processing: equity distribution")
    print("   python GetAll.py 7          # Smart processing: quarterly performance")
    print("   python GetAll.py 8          # Smart processing: EPS x PER weekly")
    print("   python GetAll.py 9          # Smart processing: quarterly analysis - NEW!")
    print("   python GetAll.py 2 --test   # Manual: basic info (test mode)")
    print("   python GetAll.py 9 --debug  # NEW! Quarterly analysis with debug output")
    print("   python GetAll.py 9 --test   # NEW! Quarterly analysis (test mode)")
    print()
    print("Smart Processing Notes (24-Hour Freshness Policy):")
    print("   • Automatically prioritizes failed/unprocessed stocks")
    print("   • Data older than 24 hours is considered expired and reprocessed")
    print("   • Only fresh data (within 24 hours) is skipped to save time")
    print("   • Delete CSV file to force complete re-processing")
    print("   • Special workflows for Types 5, 7, and 8")
    print("   • Standard workflow for Type 9")
    print("   • FIXED: Reprocessed stocks now get updated timestamps (no more mixed dates!)")
    print()
    print("Enhanced GitHub Actions Automation (v1.7.0):")
    print("   Monday 8 AM UTC (4 PM Taiwan): Type 1 - Dividend Policy")
    print("   Tuesday 8 AM UTC (4 PM Taiwan): Type 4 - Business Performance")
    print("   Wednesday 8 AM UTC (4 PM Taiwan): Type 6 - Equity Distribution")
    print("   Thursday 8 AM UTC (4 PM Taiwan): Type 7 - Quarterly Performance")
    print("   Friday 8 AM UTC (4 PM Taiwan): Type 8 - EPS x PER Weekly")
    print("   Saturday 8 AM UTC (4 PM Taiwan): Type 9 - Quarterly Analysis - NEW!")
    print("   Daily 12 PM UTC (8 PM Taiwan): Type 5 - Monthly Revenue")
    print("   Manual 24/7: Types 2, 3 - On-demand data")
    print()

def main():
    """Enhanced main function with CSV result tracking and Type 9 support + CSV Bug Fix"""
    global current_results_data, current_process_times, current_stock_ids, current_parameter, current_stock_mapping
    
    print("=" * 70)
    print("Enhanced Batch Stock Data Downloader (v1.7.0-FIXED)")
    print("Complete 9 Data Types with Enhanced Weekly Automation")
    print("24-Hour Freshness Policy + CSV Update Bug Fix")
    print("Graceful termination protection enabled")
    print("NEW! Quarterly Analysis (Type 9) support added")
    print("FIXED! CSV process_time update bug for reprocessed stocks")
    print("=" * 70)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        show_enhanced_usage()
        print("Error: Please provide DATA_TYPE parameter")
        print("Examples:")
        print("   python GetAll.py 1      # Dividend data")
        print("   python GetAll.py 5      # Monthly revenue (CSV BUG FIXED!)")
        print("   python GetAll.py 6      # Equity distribution")
        print("   python GetAll.py 7      # Quarterly performance")
        print("   python GetAll.py 8      # EPS x PER weekly")
        print("   python GetAll.py 9      # Quarterly analysis (NEW!)")
        sys.exit(1)
    
    parameter = sys.argv[1]
    test_mode = '--test' in sys.argv
    debug_mode = '--debug' in sys.argv
    direct_mode = '--direct' in sys.argv
    csv_file = "StockID_TWSE_TPEX.csv"
    
    # Validate data type (Updated for Type 9)
    if parameter not in DATA_TYPE_DESCRIPTIONS:
        print(f"Invalid data type: {parameter}")
        print("Valid data types:")
        for dt, desc in DATA_TYPE_DESCRIPTIONS.items():
            new_badge = " - NEW!" if dt == '9' else ""
            print(f" {dt} = {desc}{new_badge}")
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
    
    print(f"資料類型: {data_desc}")
    print(f"參數: {parameter}")
    print(f"24小時新鮮度策略: 啟用 (資料超過24小時將重新處理)")
    print(f"CSV更新修正: 啟用 (重新處理的股票將正確更新時間戳記)")
    
    # Show special workflow information (Updated for Type 9)
    if parameter == '5':
        print("特殊流程: 每月營收 - 自動點擊 '查20年' 按鈕")
        print("CSV修正: 已修復重新處理股票的時間戳記更新問題")
    elif parameter == '7':
        print("特殊流程: 每季經營績效 - 特殊 URL + 自動點擊 '查60年' 按鈕")
    elif parameter == '8':
        print("特殊流程: EPS x PER週線 - 特殊 URL + 自動點擊 '查5年' 按鈕")
    elif parameter == '9':
        print("標準流程: 各季詳細統計資料 - 標準 XLS 下載")
    
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    # SMART PROCESSING: Determine which stocks actually need processing with 24-hour policy
    print("智慧處理分析中 (24小時新鮮度策略)...")
    stocks_to_process, processing_strategy = determine_stocks_to_process(parameter, stock_ids, stock_mapping)
    
    if not stocks_to_process:
        print("所有資料都是新鮮的 (24小時內)，無需處理!")
        print("產生 CSV 確認...")
        save_simple_csv_results(parameter, stock_ids, {}, {}, stock_mapping)
        print("任務完成!")
        return
    
    # Update the processing list
    original_count = len(stock_ids)
    if test_mode and processing_strategy != "UP_TO_DATE":
        stocks_to_process = stocks_to_process[:3]  # Apply test mode limit
        print(f"[測試模式] 限制處理 {len(stocks_to_process)} 支股票")
    
    processing_count = len(stocks_to_process)
    print(f"處理策略: {processing_strategy}")
    print(f"處理範圍: {processing_count}/{original_count} 支股票")
    print("-" * 70)
    
    # Process each stock with detailed tracking and incremental CSV updates
    success_count = 0
    failed_count = 0
    results_data = {}  # stock_id -> True/False
    process_times = {}  # stock_id -> process_time_string
    
    # Generate initial CSV with all stocks (preserving existing data)
    print(f"初始化 CSV 檔案...")
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
            print(f"   CSV 已更新 ({i}/{len(stocks_to_process)} 完成)")
        except Exception as e:
            print(f"   CSV 更新失敗: {e}")
        
        # Add small delay to avoid overwhelming the target system
        # Standard delay for all data types (Type 9 uses standard workflow)
        delay = 2 if parameter in ['5', '7', '8'] else 1
        if i < len(stocks_to_process):  # Don't sleep after the last item
            time.sleep(delay)
    
    # Final CSV generation (redundant but ensures completeness)
    print("\n" + "=" * 70)
    print("最終 CSV 結果...")
    save_simple_csv_results(parameter, stock_ids, results_data, process_times, stock_mapping)
    
    # Enhanced Summary
    print("\n" + "=" * 70)
    print("Enhanced Execution Summary (v1.7.0-FIXED) - Complete 9 Data Types")
    print("24-Hour Freshness Policy + CSV Update Bug Fix")
    print("=" * 70)
    print(f"資料類型: {data_desc}")
    print(f"處理策略: {processing_strategy}")
    print(f"總股票數: {original_count} 支")
    print(f"需處理股票數: {processing_count} 支") 
    print(f"實際處理: {len(stocks_to_process)} 支股票")
    print(f"成功: {success_count} 支")
    print(f"失敗: {failed_count} 支")
    if processing_count > 0:
        print(f"本次成功率: {success_count/processing_count*100:.1f}%")
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show automation information (Updated for v1.7.0 - Enhanced Weekly + Daily)
    automation_info = {
        '1': '每週自動化 (Weekly Monday 8 AM UTC)',
        '4': '每週自動化 (Weekly Tuesday 8 AM UTC)', 
        '5': '每日自動化 (Daily 12 PM UTC) + CSV修正',
        '6': '每週自動化 (Weekly Wednesday 8 AM UTC)',
        '7': '每週自動化 (Weekly Thursday 8 AM UTC)',
        '8': '每週自動化 (Weekly Friday 8 AM UTC)',
        '9': '每週自動化 (Weekly Saturday 8 AM UTC) - NEW!',
        '2': '手動執行 (Manual trigger only)',
        '3': '手動執行 (Manual trigger only)'
    }
    
    automation = automation_info.get(parameter, '手動執行')
    print(f"自動化狀態: {automation}")
    
    # Explain the processing strategy
    strategy_explanations = {
        "REPROCESS_NEEDED": "優先處理失敗、未處理或過期(>24小時)的股票",
        "UP_TO_DATE": "所有資料都在24小時內且成功，無需處理",
        "INITIAL_SCAN": "首次掃描，建立完整的資料基線"
    }
    
    if processing_strategy in strategy_explanations:
        print(f"策略說明: {strategy_explanations[processing_strategy]}")
    
    # Show 24-hour policy information
    print(f"\n24小時新鮮度策略: 資料超過24小時自動視為過期需重新處理")
    print(f"CSV修正說明: 重新處理的股票現在會正確更新process_time時間戳記")
    
    if failed_count > 0:
        print(f"\n警告: 有 {failed_count} 支股票處理失敗")
        print("建議:")
        print("   • 使用 --debug 查看詳細錯誤訊息")
        print("   • 使用 --test 先測試少數股票")
        print("   • 檢查網路連線狀況")
        if parameter in ['5', '7', '8']:
            print(f"   • 資料類型 {parameter} 使用特殊處理流程，可能需要更多時間")
        elif parameter == '9':
            print(f"   • 資料類型 {parameter} 使用標準流程")
    
    if parameter == '9':
        print(f"\nNEW! 資料類型 9 (各季詳細統計資料) 已成功處理!")
        print("提供4季詳細統計數據包含股價變動、交易量、季節性表現")
        print("請檢查 StockHisAnaQuar 資料夾中的檔案")
    
    if parameter == '5':
        print(f"\nFIXED! 資料類型 5 (每月營收) CSV時間戳記更新問題已修復!")
        print("重新處理的股票現在會正確更新process_time，不再保留舊的時間戳記")
        print("Duration計算現在應該顯示正確的處理時間跨度")

if __name__ == "__main__":
    main()