#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIXED GetAll.py with CSV-ONLY Based 24-Hour Freshness Policy (v1.8.3 CSV-ONLY)
FIXES: Uses ONLY CSV records for freshness, not file timestamps
Correct logic: Use last_update_time from CSV to determine if stock needs reprocessing
"""

import sys
import csv
import subprocess
import os
import time
import pandas as pd
import signal
from datetime import datetime, timedelta
import psutil
import shutil

# Try to set UTF-8 encoding for Windows console
try:
    if sys.platform.startswith('win'):
        import locale
        os.system('chcp 65001 > nul 2>&1')
except:
    pass

# Data type descriptions (unchanged)
DATA_TYPE_DESCRIPTIONS = {
    '1': 'Dividend Policy (股利政策) - Weekly automation (Monday 8 AM UTC)',
    '2': 'Basic Info (基本資料) - Manual only',
    '3': 'Stock Details (個股市況) - Manual only',
    '4': 'Business Performance (經營績效) - Weekly automation (Tuesday 8 AM UTC)',
    '5': 'Monthly Revenue (每月營收) - Daily automation (12 PM UTC)',
    '6': 'Equity Distribution (股權結構) - Weekly automation (Wednesday 8 AM UTC)',
    '7': 'Quarterly Performance (每季經營績效) - Weekly automation (Thursday 8 AM UTC)',
    '8': 'EPS x PER Weekly (每週EPS本益比) - Weekly automation (Friday 8 AM UTC)',
    '9': 'Quarterly Analysis (各季詳細統計資料) - Weekly automation (Saturday 8 AM UTC)',
    '10': 'Equity Class Weekly (股東持股分級週) - Weekly automation (Sunday 8 AM UTC)'
}

# Global variables for graceful termination
current_results_data = {}
current_process_times = {}
current_retry_stats = {}
current_stock_ids = []
current_parameter = ""
current_stock_mapping = {}

def signal_handler(signum, frame):
    """Handle termination signals gracefully - save CSV before exit"""
    print(f"\n警告 收到終止信號 ({signum}) - 正在儲存進度...")
    
    if current_results_data and current_stock_ids:
        try:
            save_csv_results_csv_only(current_parameter, current_stock_ids, 
                                     current_results_data, current_process_times, 
                                     current_stock_mapping, current_retry_stats)
            processed_count = len(current_results_data)
            success_count = sum(1 for success in current_results_data.values() if success)
            total_attempts = sum(stats.get('attempts', 1) for stats in current_retry_stats.values()) if current_retry_stats else processed_count
            print(f"緊急儲存完成: {processed_count} 股票已處理，{success_count} 成功，{total_attempts} 總嘗試次數")
        except Exception as e:
            print(f"緊急儲存失敗: {e}")
    
    print("程式已安全終止")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def aggressive_chrome_cleanup():
    """Enhanced Chrome process and resource cleanup"""
    cleanup_count = 0
    temp_cleanup_count = 0
    
    try:
        print("🔥 執行強化 Chrome 清理...")
        
        # Method 1: Kill Chrome processes using psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and any(name in proc.info['name'].lower() 
                                           for name in ['chrome', 'chromium', 'chromedriver']):
                    proc.terminate()
                    cleanup_count += 1
                    time.sleep(0.1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Wait for graceful termination
        time.sleep(2)
        
        # Method 2: Force kill remaining processes
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and any(name in proc.info['name'].lower() 
                                           for name in ['chrome', 'chromium']):
                    proc.kill()
                    cleanup_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Method 3: Unix pkill as backup
        try:
            os.system('pkill -f chrome > /dev/null 2>&1')
            os.system('pkill -f chromium > /dev/null 2>&1') 
            os.system('pkill -f chromedriver > /dev/null 2>&1')
        except:
            pass
        
        # Clean temporary directories
        temp_patterns = ['chrome', 'chromium', 'goodinfo', 'selenium', 'webdriver']
        temp_dirs = ['/tmp', '/var/tmp', os.path.expanduser('~/.cache')]
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    for item in os.listdir(temp_dir):
                        if any(pattern in item.lower() for pattern in temp_patterns):
                            item_path = os.path.join(temp_dir, item)
                            try:
                                if os.path.isdir(item_path):
                                    shutil.rmtree(item_path, ignore_errors=True)
                                else:
                                    os.remove(item_path)
                                temp_cleanup_count += 1
                            except:
                                pass
                except:
                    pass
        
        print(f"   Chrome 程序清理: {cleanup_count} 個程序")
        print(f"   暫存檔案清理: {temp_cleanup_count} 個項目")
        return cleanup_count + temp_cleanup_count
        
    except Exception as e:
        print(f"清理過程發生錯誤: {e}")
        return 0

def parse_csv_datetime(date_string):
    """FIXED: Parse CSV datetime strings safely"""
    if not date_string or date_string in ['NOT_PROCESSED', 'NEVER', '', 'nan']:
        return None
    
    try:
        # Handle the format from CSV: '2025-09-03 12:08:54'
        return datetime.strptime(date_string.strip(), '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            # Fallback for date-only format
            return datetime.strptime(date_string.strip(), '%Y-%m-%d')
        except ValueError:
            print(f"   ⚠️ 無法解析時間: {date_string}")
            return None

def run_get_good_info_with_retry(stock_id, parameter, debug_mode=False, max_retries=3):
    """Standard retry mechanism without file validation (CSV-only approach)"""
    
    timeout_config = {
        '1': 90,   '2': 60,   '3': 60,   '4': 75,   '5': 90,
        '6': 90,   '7': 90,   '8': 90,   '9': 75,   '10': 90
    }
    
    base_timeout = timeout_config.get(str(parameter), 75)
    backoff_delays = [0, 10, 30, 60]
    
    start_time = time.time()
    last_error = ""
    
    for attempt in range(1, max_retries + 2):
        try:
            # Resource cleanup before retry attempts
            if attempt > 1:
                print(f"   第 {attempt} 次嘗試 - 執行資源清理...")
                cleanup_count = aggressive_chrome_cleanup()
                
                # Progressive backoff delay
                delay = backoff_delays[min(attempt - 1, len(backoff_delays) - 1)]
                if delay > 0:
                    print(f"   等待 {delay} 秒冷卻時間...")
                    time.sleep(delay)
            
            current_timeout = base_timeout + (attempt - 1) * 30
            
            print(f"   嘗試 {attempt}/4 (超時: {current_timeout}s)")
            
            # Prepare command
            cmd = ['python', 'GetGoodInfo.py', str(stock_id), str(parameter)]
            
            # Set environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=current_timeout,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            
            # Check success based on return code only (CSV-only approach)
            if result.returncode == 0:
                duration = time.time() - start_time
                success_msg = f"✅ {stock_id} 第 {attempt} 次嘗試成功"
                if attempt > 1:
                    success_msg += f" (前 {attempt-1} 次失敗後重試成功)"
                print(success_msg)
                
                # Show output for retries or debug mode
                if (debug_mode or attempt > 1) and result.stdout:
                    output_lines = result.stdout.strip().split('\n')
                    if len(output_lines) <= 3:
                        print(f"   輸出: {result.stdout.strip()}")
                    else:
                        print(f"   輸出: {output_lines[0]}")
                        print(f"        ... ({len(output_lines)} 行輸出)")
                
                return True, attempt, "", duration
            
            # Handle failure
            else:
                error_msg = f"退出碼 {result.returncode}"
                if result.stderr and result.stderr.strip():
                    stderr_lines = result.stderr.strip().split('\n')
                    error_msg += f" - {stderr_lines[0]}"
                    if len(stderr_lines) > 1:
                        error_msg += f" (+{len(stderr_lines)-1} 行錯誤)"
                
                last_error = error_msg
                print(f"   ❌ 第 {attempt} 次嘗試失敗: {error_msg}")
                
                # Don't retry certain error types
                if result.returncode in [2, 127]:
                    print(f"   🛑 致命錯誤，停止重試")
                    break
                
                continue
                
        except subprocess.TimeoutExpired:
            timeout_msg = f"超時 ({current_timeout}秒)"
            last_error = timeout_msg
            print(f"   ⏰ 第 {attempt} 次嘗試超時: {timeout_msg}")
            
            # Force cleanup after timeout
            if attempt < max_retries + 1:
                print(f"   🧹 超時後執行緊急清理...")
                aggressive_chrome_cleanup()
            
            continue
            
        except KeyboardInterrupt:
            print(f"   ⚠️ 用戶中斷執行")
            raise
            
        except Exception as e:
            error_msg = f"執行異常: {str(e)}"
            last_error = error_msg
            print(f"   💥 第 {attempt} 次嘗試異常: {error_msg}")
            continue
    
    # All attempts failed
    duration = time.time() - start_time
    total_attempts = max_retries + 1
    print(f"   ❌ 最終失敗: 經過 4 次嘗試仍失敗")
    print(f"   📝 最後錯誤: {last_error}")
    return False, total_attempts, last_error, duration

def determine_stocks_to_process_csv_only(parameter, all_stock_ids, stock_mapping, debug_mode=False):
    """CSV-ONLY: Determine which stocks need processing based on CSV records only"""
    
    folder_mapping = {
        '1': 'DividendDetail', '2': 'BasicInfo', '3': 'StockDetail',
        '4': 'StockBzPerformance', '5': 'ShowSaleMonChart', '6': 'EquityDistribution',
        '7': 'StockBzPerformance1', '8': 'ShowK_ChartFlow', '9': 'StockHisAnaQuar',
        '10': 'EquityDistributionClassHis'
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
                            'process_time': row.get('process_time', 'NOT_PROCESSED'),
                            'retry_count': int(row.get('retry_count', 0))
                        }
        except Exception as e:
            print(f"無法讀取現有CSV數據: {e}")
    
    # CSV-ONLY: Analyze status based purely on CSV records
    now = datetime.now()
    failed_stocks = []
    not_processed_stocks = []
    fresh_success = []
    expired_success = []
    
    print(f"🔍 CSV-ONLY 分析 {len(all_stock_ids)} 支股票的記錄狀態 (24小時新鮮度政策)...")
    if debug_mode:
        print(f"   當前時間: {now}")
    
    for stock_id in all_stock_ids:
        company_name = stock_mapping.get(stock_id, f'股票{stock_id}')
        
        # Generate expected filename
        if parameter == '7':
            filename = f"StockBzPerformance1_{stock_id}_{company_name}_quarter.xls"
        else:
            filename = f"{folder}_{stock_id}_{company_name}.xls"
        
        # Check CSV record
        if filename in existing_data:
            record = existing_data[filename]
            success = record['success'].lower() == 'true'
            last_update_time_str = record['last_update_time']
            
            if last_update_time_str in ['NOT_PROCESSED', 'NEVER', '']:
                not_processed_stocks.append(stock_id)
                if debug_mode:
                    print(f"   {stock_id}: CSV顯示未處理 -> 需處理")
                continue
            
            # Parse the last_update_time from CSV
            last_update_time = parse_csv_datetime(last_update_time_str)
            
            if last_update_time is None:
                not_processed_stocks.append(stock_id)
                if debug_mode:
                    print(f"   {stock_id}: 無法解析時間 '{last_update_time_str}' -> 需處理")
                continue
            
            # Calculate age based on CSV timestamp
            time_diff = now - last_update_time
            hours_ago = time_diff.total_seconds() / 3600
            
            if debug_mode:
                print(f"   {stock_id}: CSV時間 {last_update_time}, {hours_ago:.1f}h前, 成功={success}")
            
            if not success:
                failed_stocks.append(stock_id)
                if debug_mode:
                    print(f"   {stock_id}: CSV顯示失敗 -> 需重試")
            elif hours_ago <= 24:
                fresh_success.append(stock_id)
                if debug_mode:
                    print(f"   {stock_id}: {hours_ago:.1f}h 新鮮 -> 跳過")
            else:
                expired_success.append(stock_id)
                if debug_mode:
                    print(f"   {stock_id}: {hours_ago:.1f}h 過期 -> 需更新")
        else:
            not_processed_stocks.append(stock_id)
            if debug_mode:
                print(f"   {stock_id}: CSV中無記錄 -> 需處理")
    
    priority_stocks = failed_stocks + not_processed_stocks + expired_success
    
    print(f"處理狀態分析 ({folder}) - CSV-ONLY 24小時新鮮度政策:")
    print(f"   失敗股票: {len(failed_stocks)} (CSV標記失敗)")
    print(f"   未處理股票: {len(not_processed_stocks)} (CSV無記錄或未處理)")
    print(f"   新鮮成功 (≤24小時): {len(fresh_success)} (跳過)")
    print(f"   過期成功 (>24小時): {len(expired_success)} (需更新)")
    
    # Debug: Show specific examples
    if debug_mode and expired_success:
        print(f"   過期股票範例:")
        for stock_id in expired_success[:5]:
            company_name = stock_mapping.get(stock_id, f'股票{stock_id}')
            if parameter == '7':
                filename = f"StockBzPerformance1_{stock_id}_{company_name}_quarter.xls"
            else:
                filename = f"{folder}_{stock_id}_{company_name}.xls"
            
            if filename in existing_data:
                last_update_str = existing_data[filename]['last_update_time']
                last_update_time = parse_csv_datetime(last_update_str)
                if last_update_time:
                    hours_ago = (now - last_update_time).total_seconds() / 3600
                    print(f"     {stock_id}: CSV時間 {last_update_str} ({hours_ago:.1f}h前)")
    
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

def save_csv_results_csv_only(parameter, stock_ids, results_data, process_times, stock_mapping, retry_stats=None):
    """CSV-ONLY: Save CSV results with current timestamp for successful downloads"""
    
    folder_mapping = {
        '1': 'DividendDetail', '2': 'BasicInfo', '3': 'StockDetail',
        '4': 'StockBzPerformance', '5': 'ShowSaleMonChart', '6': 'EquityDistribution',
        '7': 'StockBzPerformance1', '8': 'ShowK_ChartFlow', '9': 'StockHisAnaQuar',
        '10': 'EquityDistributionClassHis'
    }
    folder = folder_mapping.get(parameter, f'DataType{parameter}')
    
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"建立資料夾: {folder}")
    
    csv_filepath = os.path.join(folder, "download_results.csv")
    
    # Load existing data for stocks not processed in current run
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
                            'process_time': row.get('process_time', 'NOT_PROCESSED'),
                            'retry_count': int(row.get('retry_count', 0))
                        }
        except Exception as e:
            print(f"警告: 無法載入現有 CSV: {e}")
    
    try:
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['filename', 'last_update_time', 'success', 'process_time', 'retry_count'])
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for stock_id in stock_ids:
                company_name = stock_mapping.get(stock_id, f'股票{stock_id}')
                
                if parameter == '7':
                    filename = f"StockBzPerformance1_{stock_id}_{company_name}_quarter.xls"
                else:
                    filename = f"{folder}_{stock_id}_{company_name}.xls"
                
                if stock_id in results_data:
                    # Current processing data
                    success = str(results_data[stock_id]).lower()
                    process_time = process_times.get(stock_id, 'NOT_PROCESSED')
                    total_attempts = retry_stats.get(stock_id, {}).get('attempts', 1) if retry_stats else 1
                    retry_count = max(0, total_attempts - 1)
                    
                    # CSV-ONLY: Use current time for successful downloads
                    if success == 'true':
                        last_update = current_time  # Set to current time for successful downloads
                    else:
                        # Failed - preserve existing timestamp if it exists
                        if filename in existing_data:
                            last_update = existing_data[filename]['last_update_time']
                        else:
                            last_update = 'NEVER'
                else:
                    # Existing data (not processed in current run)
                    if filename in existing_data:
                        existing_record = existing_data[filename]
                        last_update = existing_record['last_update_time']
                        success = existing_record['success']
                        process_time = existing_record['process_time']
                        retry_count = existing_record.get('retry_count', 0)
                    else:
                        # New stock not yet processed
                        last_update = 'NEVER'
                        success = 'false'
                        process_time = 'NOT_PROCESSED'
                        retry_count = 0
                
                writer.writerow([filename, last_update, success, process_time, retry_count])
        
        print(f"CSV-ONLY CSV結果已儲存: {csv_filepath}")
        
        # Enhanced summary
        if results_data:
            total_stocks = len(stock_ids)
            processed_count = len(results_data)
            success_count = sum(1 for success in results_data.values() if success)
            success_rate = (success_count / processed_count * 100) if processed_count > 0 else 0
            
            print(f"{folder} 摘要 (CSV-ONLY版本):")
            print(f"   CSV 總股票數: {total_stocks}")
            print(f"   本次處理股票數: {processed_count}")
            print(f"   本次成功數: {success_count}")
            print(f"   本次成功率: {success_rate:.1f}%")
            
            if retry_stats:
                total_attempts = sum(stats.get('attempts', 1) for stats in retry_stats.values())
                total_retries = sum(max(0, stats.get('attempts', 1) - 1) for stats in retry_stats.values())
                print(f"   總嘗試次數: {total_attempts}")
                print(f"   總重試次數: {total_retries}")
            
            print(f"   CSV 位置: {csv_filepath}")
        
    except Exception as e:
        print(f"儲存 CSV 時發生錯誤: {e}")

# Original helper functions (unchanged)
def read_stock_ids(csv_file):
    """Read stock IDs from CSV file with enhanced encoding support"""
    stock_ids = []
    encodings = ['utf-8', 'big5', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                first_line = f.readline()
                f.seek(0)
                reader = csv.reader(f)
                
                # Skip header if detected
                first_row = next(reader)
                if any('股' in str(cell) or 'StockID' in str(cell) or 'ID' in str(cell) 
                      or '代號' in str(cell) or 'Code' in str(cell) for cell in first_row):
                    print(f"偵測到標題行: {first_row}")
                else:
                    stock_id = first_row[0].strip() if first_row and len(first_row) > 0 else ""
                    if stock_id and stock_id.isdigit() and 4 <= len(stock_id) <= 6:
                        stock_ids.append(stock_id)
                
                # Read remaining rows
                for row in reader:
                    if row and len(row) > 0 and row[0].strip():
                        stock_id = row[0].strip()
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
            except Exception:
                continue
        
        if not stock_mapping:
            print("無法載入股票名稱對應，將使用預設名稱")
        
    except Exception as e:
        print(f"載入股票名稱對應時發生錯誤: {e}")
    
    return stock_mapping

def show_enhanced_usage():
    """Show enhanced usage information for v1.8.3 CSV-ONLY"""
    print("=" * 70)
    print("Enhanced Batch Stock Data Downloader (v1.8.3 CSV-ONLY)")
    print("Complete 10 Data Types with CSV-ONLY 24-Hour Freshness Policy")
    print("FIXED: Uses ONLY CSV records for freshness, ignores file timestamps")
    print("=" * 70)
    print()
    print("CSV-ONLY FEATURES:")
    print("   ✅ CSV-ONLY Policy: Uses CSV last_update_time for freshness")
    print("   ✅ No File Checks: Ignores file timestamps entirely")
    print("   ✅ Pipeline Compatible: Works in CI/CD where files are always new")
    print("   ✅ Accurate Tracking: CSV is source of truth for processing history")
    print("   🔧 Enhanced Debug: Detailed CSV record analysis")
    print()
    print("Data Types (Complete 10 Types - v1.8.3 CSV-ONLY):")
    for dt, desc in DATA_TYPE_DESCRIPTIONS.items():
        print(f"   {dt} = {desc}")
    print()
    print("Options:")
    print("   --test   = Process only first 3 stocks (testing)")
    print("   --debug  = Show detailed CSV record analysis")
    print("   --direct = Simple execution mode (compatibility test)")
    print()
    print("CSV-ONLY Examples (v1.8.3):")
    print("   python GetAll.py 1          # CSV-ONLY: accurate freshness from records")
    print("   python GetAll.py 1 --debug  # CSV-ONLY: with detailed record tracking")  
    print("   python GetAll.py 7 --test   # CSV-ONLY: test mode with CSV analysis")
    print()

def main():
    """CSV-ONLY main function with corrected freshness policy (v1.8.3)"""
    global current_results_data, current_process_times, current_stock_ids, current_parameter, current_stock_mapping
    
    print("=" * 70)
    print("Enhanced Batch Stock Data Downloader (v1.8.3 CSV-ONLY)")
    print("Complete 10 Data Types with CSV-ONLY 24-Hour Freshness Policy")
    print("FIXED: Uses ONLY CSV records for freshness determination")
    print("Pipeline compatible - ignores file timestamps entirely")
    print("=" * 70)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        show_enhanced_usage()
        print("Error: Please provide DATA_TYPE parameter")
        print("Examples:")
        print("   python GetAll.py 1      # CSV-ONLY dividend data processing")
        print("   python GetAll.py 6      # CSV-ONLY equity distribution")
        print("   python GetAll.py 7      # CSV-ONLY quarterly performance")
        sys.exit(1)
    
    parameter = sys.argv[1]
    test_mode = '--test' in sys.argv
    debug_mode = '--debug' in sys.argv
    direct_mode = '--direct' in sys.argv
    csv_file = "StockID_TWSE_TPEX.csv"
    
    # Validate data type
    if parameter not in DATA_TYPE_DESCRIPTIONS:
        print(f"Invalid data type: {parameter}")
        print("Valid data types:")
        for dt, desc in DATA_TYPE_DESCRIPTIONS.items():
            print(f" {dt} = {desc}")
        sys.exit(1)
    
    # Check files
    if not os.path.exists(csv_file):
        print(f"[ERROR] 找不到檔案: {csv_file}")
        print("請先執行 Get觀察名單.py 下載股票清單")
        sys.exit(1)
    
    if not os.path.exists("GetGoodInfo.py"):
        print("[ERROR] 找不到 GetGoodInfo.py")
        sys.exit(1)
    
    # Read stock IDs and mapping
    print(f"[讀取] 讀取股票清單: {csv_file}")
    stock_ids = read_stock_ids(csv_file)
    
    if not stock_ids:
        print("[ERROR] 未找到有效的股票代碼")
        sys.exit(1)
    
    print(f"[讀取] 載入股票名稱對應...")
    stock_mapping = load_stock_mapping(csv_file)
    
    # Set global variables for signal handler
    current_stock_ids = stock_ids
    current_parameter = parameter  
    current_stock_mapping = stock_mapping
    global current_retry_stats
    current_retry_stats = {}
    
    print(f"[統計] 找到 {len(stock_ids)} 支股票")
    print(f"前5支股票: {stock_ids[:5]}")
    
    data_desc = DATA_TYPE_DESCRIPTIONS.get(parameter, f"Data Type {parameter}")
    
    if test_mode:
        stock_ids = stock_ids[:3]
        print(f"[測試模式] 只處理前 {len(stock_ids)} 支股票")
    
    if debug_mode:
        print("[除錯模式] 將顯示詳細CSV記錄分析")
    
    print(f"資料類型: {data_desc}")
    print(f"參數: {parameter}")
    print(f"🔧 CSV-ONLY處理: 僅使用CSV記錄判斷新鮮度")
    print(f"✅ 管道相容: 忽略檔案時戳，適用於CI/CD環境")
    print(f"📊 準確追蹤: CSV是處理歷史的唯一真相來源")
    
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    # CSV-ONLY smart processing analysis
    print("CSV-ONLY 智慧處理分析中 (修正的24小時新鮮度政策)...")
    stocks_to_process, processing_strategy = determine_stocks_to_process_csv_only(
        parameter, stock_ids, stock_mapping, debug_mode
    )
    
    if not stocks_to_process:
        print("所有資料都是新鮮的 (CSV顯示24小時內)，無需處理!")
        save_csv_results_csv_only(parameter, stock_ids, {}, {}, stock_mapping, {})
        print("任務完成!")
        return
    
    # Update processing list for test mode
    original_count = len(stock_ids)
    if test_mode and processing_strategy != "UP_TO_DATE":
        stocks_to_process = stocks_to_process[:3]
        print(f"[測試模式] 限制處理 {len(stocks_to_process)} 支股票")
    
    processing_count = len(stocks_to_process)
    print(f"處理策略: {processing_strategy}")
    print(f"處理範圍: {processing_count}/{original_count} 支股票")
    print(f"🔧 CSV-ONLY: 每支股票最多 4 次嘗試機會 (1+3)")
    print(f"✅ 記錄導向: 成功後更新CSV時戳為當前時間")
    print("-" * 70)
    
    # Enhanced batch processing with CSV-ONLY approach
    success_count = 0
    failed_count = 0
    results_data = {}
    process_times = {}
    retry_stats = {}
    
    # Initialize CSV with CSV-ONLY logic
    print(f"初始化 CSV-ONLY CSV 檔案...")
    save_csv_results_csv_only(parameter, stock_ids, {}, {}, stock_mapping, {})
    
    # Process stocks with standard retry mechanism
    total_attempts = 0
    for i, stock_id in enumerate(stocks_to_process, 1):
        print(f"\n[{i}/{len(stocks_to_process)}] 處理股票: {stock_id}")
        
        # Record start time
        current_process_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        process_times[stock_id] = current_process_time
        
        # Execute with standard retry mechanism
        success, attempts, error_msg, duration = run_get_good_info_with_retry(
            stock_id, parameter, debug_mode, max_retries=3
        )
        
        # Record results
        results_data[stock_id] = success
        retry_stats[stock_id] = {
            'attempts': attempts,
            'error': error_msg,
            'duration': duration
        }
        total_attempts += attempts
        
        # Update global variables for signal handler
        current_results_data = results_data.copy()
        current_process_times = process_times.copy()
        current_retry_stats = retry_stats.copy()
        
        if success:
            success_count += 1
            if attempts > 1:
                print(f"   🎯 重試成功: 第 {attempts} 次嘗試成功")
        else:
            failed_count += 1
            print(f"   💥 最終失敗: {attempts} 次嘗試後失敗 (最多4次)")
        
        # Save progress after each stock with CSV-ONLY logic
        try:
            save_csv_results_csv_only(parameter, stock_ids, results_data, process_times, stock_mapping, retry_stats)
            print(f"   📝 CSV-ONLY CSV 已更新 ({i}/{len(stocks_to_process)} 完成)")
        except Exception as e:
            print(f"   ⚠️ CSV 更新失敗: {e}")
        
        # Delay between stocks
        if i < len(stocks_to_process):
            delay = 3 if success else 5
            time.sleep(delay)
    
    # Final CSV save with CSV-ONLY logic
    print("\n" + "=" * 70)
    print("最終 CSV-ONLY CSV 結果...")
    save_csv_results_csv_only(parameter, stock_ids, results_data, process_times, stock_mapping, retry_stats)
    
    # Enhanced Summary with CSV-ONLY approach
    print("\n" + "=" * 70)
    print("Enhanced Execution Summary (v1.8.3 CSV-ONLY) - Pipeline Compatible")
    print("Complete 10 Data Types + CSV-ONLY Freshness + Standard Processing")
    print("=" * 70)
    print(f"資料類型: {data_desc}")
    print(f"處理策略: {processing_strategy}")
    print(f"總股票數: {original_count} 支")
    print(f"需處理股票數: {processing_count} 支") 
    print(f"實際處理: {len(stocks_to_process)} 支股票")
    print(f"最終成功: {success_count} 支")
    print(f"最終失敗: {failed_count} 支")
    print(f"總嘗試次數: {total_attempts} 次")
    print(f"平均嘗試次數: {total_attempts/len(stocks_to_process):.1f} 次/股票")
    
    if processing_count > 0:
        final_success_rate = (success_count / processing_count * 100)
        print(f"🎯 CSV-ONLY 最終成功率: {final_success_rate:.1f}% (標準處理)")
    
    # Show CSV-ONLY improvements
    print(f"\n✅ CSV-ONLY 改善項目:")
    print(f"   • 僅使用CSV: 完全忽略檔案時戳，使用CSV記錄")
    print(f"   • 管道相容: 適用於CI/CD環境，檔案總是新的")
    print(f"   • 準確追蹤: CSV是處理歷史的唯一真相來源")
    print(f"   • 成功更新: 成功處理後立即更新CSV時戳")
    
    print(f"\n結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed_count > 0:
        print(f"\n⚠️ 仍有 {failed_count} 支股票經4次嘗試後失敗")
        print("建議:")
        print("   • 檢查網路連線狀態")
        print("   • 使用 --debug 查看詳細錯誤")
        print("   • 單獨執行失敗股票: python GetGoodInfo.py [股票代號] [類型]")
        print("   • CSV-ONLY: 現在能準確追蹤基於記錄的處理歷史")
    else:
        print(f"\n🎉 完美執行! 所有 {success_count} 支股票均處理成功")
        if total_attempts > len(stocks_to_process):
            improvement = total_attempts - len(stocks_to_process)
            print(f"💪 重試機制額外挽救了 {improvement} 次失敗")
        print(f"✅ CSV-ONLY版本提供準確的記錄導向處理追蹤")

if __name__ == "__main__":
    main()