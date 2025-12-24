#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced GetAll.py with CSV-ONLY Based 24-Hour Freshness Policy (v3.1.0)
ENHANCED: Complete 16 Data Types including Quarterly Financial Ratio Analysis
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

# Enhanced data type descriptions for complete 16 data types (v3.1.0)
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
    '10': 'Equity Class Weekly (股東持股分類週) - Weekly automation (Sunday 8 AM UTC)',
    '11': 'Weekly Trading Data (週交易資料含三大法人) - Weekly automation (Monday Evening)',
    '12': 'EPS x PER Monthly (每月EPS本益比) - Monthly automation (1st Tuesday)', # 🆕 NEW in v3.0.0
    '13': 'Daily Margin Balance (每日融資融券餘額詳細資料) - Daily automation (Evening)', # 🆕 NEW Type 13
    '14': 'Weekly Margin Balance (每周融資融券餘額詳細資料) - Weekly automation (Friday Evening)', # 🆕 NEW Type 14
    '15': 'Monthly Margin Balance (每月融資融券餘額詳細資料) - Monthly automation (1st Wednesday)',
    '16': 'Quarterly Financial Ratio Analysis (單季財務比率表詳細資料) - Monthly automation (1st Wednesday 2:10 PM UTC)' # 🆕 NEW Type 16
}

# Global variables for graceful termination
current_results_data = {}
current_process_times = {}
current_last_update_times = {}  # NEW: Track actual completion times
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
                                     current_stock_mapping, current_retry_stats,
                                     current_last_update_times)  # NEW: Pass completion times
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
    """Enhanced retry mechanism with Type 12 considerations"""
    
    # Enhanced timeout configuration including Type 12
    timeout_config = {
        '1': 90,   '2': 60,   '3': 60,   '4': 75,   '5': 90,
        '6': 90,   '7': 90,   '8': 90,   '9': 75,   '10': 90,
        '11': 120, '12': 90, '13': 90, '14': 90, '15': 90  # 🆕 Types 13-15 timeouts set to 90s
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
            
            # Enhanced timeout for Types 11 and 12
            current_timeout = base_timeout + (attempt - 1) * 30
            if str(parameter) in ['11', '12', '13', '14', '15', '16'] and attempt > 1:
                current_timeout += 30  # Additional time for complex data types
            
            print(f"   嘗試 {attempt}/4 (超時: {current_timeout}s)")
            if str(parameter) == '11':
                print(f"   🔵 Type 11: 週交易資料含三大法人數據處理中...")
            elif str(parameter) == '12':
                print(f"   🆕 Type 12: 每月EPS本益比長期數據處理中...")
            elif str(parameter) == '13':
                print(f"   🆕 Type 13: 每日融資融券餘額數據處理中...")
            elif str(parameter) == '14':
                print(f"   🆕 Type 14: 每周融資融券餘額數據處理中...")
            elif str(parameter) == '15':
                print(f"   🆕 Type 15: 每月融資融券餘額數據處理中...")
            elif str(parameter) == '16':
                print(f"   🆕 Type 16: 單季財務比率表數據處理中...")
            
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
                if str(parameter) == '11':
                    success_msg += f" [Type 11 機構資料完成]"
                elif str(parameter) == '12':
                    success_msg += f" [Type 12 月度P/E完成]"
                elif str(parameter) == '13':
                    success_msg += f" [Type 13 融資融券完成]"
                elif str(parameter) == '14':
                    success_msg += f" [Type 14 每周融資融券完成]"
            elif str(parameter) == '15':
                success_msg += f" [Type 15 每月融資融券完成]"
            elif str(parameter) == '16':
                success_msg += f" [Type 16 單季財務比率表完成]"
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
            if str(parameter) == '11':
                timeout_msg += " [Type 11 機構數據複雜度]"
            elif str(parameter) == '12':
                timeout_msg += " [Type 12 月度數據複雜度]"
            elif str(parameter) == '13':
                timeout_msg += " [Type 13 每日數據複雜度]"
            elif str(parameter) == '14':
                timeout_msg += " [Type 14 每周數據複雜度]"
            elif str(parameter) == '15':
                timeout_msg += " [Type 15 每月數據複雜度]"
            elif str(parameter) == '16':
                timeout_msg += " [Type 16 單季數據複雜度]"
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
    failure_msg = f"   ❌ 最終失敗: 經過 4 次嘗試仍失敗"
    if str(parameter) == '11':
        failure_msg += f" [Type 11 機構數據處理失敗]"
    elif str(parameter) == '12':
        failure_msg += f" [Type 12 月度P/E處理失敗]"
    elif str(parameter) == '13':
        failure_msg += f" [Type 13 融資融券處理失敗]"
    elif str(parameter) == '14':
        failure_msg += f" [Type 14 每周融資融券處理失敗]"
    elif str(parameter) == '15':
        failure_msg += f" [Type 15 每月融資融券處理失敗]"
    elif str(parameter) == '16':
        failure_msg += f" [Type 16 單季財務比率表處理失敗]"
    print(failure_msg)
    print(f"   🔍 最後錯誤: {last_error}")
    return False, total_attempts, last_error, duration

def determine_stocks_to_process_csv_only(parameter, all_stock_ids, stock_mapping, debug_mode=False):
    """Enhanced CSV-ONLY: Determine which stocks need processing including Type 12 support"""
    
    # Enhanced folder mapping for complete 16 data types (v3.1.0)
    folder_mapping = {
        '1': 'DividendDetail', '2': 'BasicInfo', '3': 'StockDetail',
        '4': 'StockBzPerformance', '5': 'ShowSaleMonChart', '6': 'EquityDistribution',
        '7': 'StockBzBzPerformance1', '8': 'ShowK_ChartFlow', '9': 'StockHisAnaQuar',
        '10': 'EquityDistributionClassHis', '11': 'WeeklyTradingData', '12': 'ShowMonthlyK_ChartFlow',
        '13': 'ShowMarginChart', '14': 'ShowMarginChartWeek', '15': 'ShowMarginChartMonth',
        '16': 'StockFinDetail'  # 🆕 NEW Type 16
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
    
    # Enhanced CSV-ONLY analysis with Type 12 considerations
    now = datetime.now()
    failed_stocks = []
    not_processed_stocks = []
    fresh_success = []
    expired_success = []
    
    print(f"📋 CSV-ONLY 分析 {len(all_stock_ids)} 支股票的記錄狀態 (24小時新鮮度政策)...")
    if str(parameter) == '11':
        print(f"   🔵 Type 11: 週交易資料含三大法人 - 機構數據複雜度處理")
    elif str(parameter) == '12':
        print(f"   🆕 Type 12: 每月EPS本益比 - 20年月度P/E數據複雜度處理")
    elif str(parameter) == '13':
        print(f"   🆕 Type 13: 每日融資融券餘額 - 每日數據複雜度處理")
    elif str(parameter) == '14':
        print(f"   🆕 Type 14: 每周融資融券餘額 - 每周數據複雜度處理")
    elif str(parameter) == '15':
        print(f"   🆕 Type 15: 每月融資融券餘額 - 每月數據複雜度處理")
    elif str(parameter) == '16':
        print(f"   🆕 Type 16: 單季財務比率表 - 單季比率分析數據處理")
    if debug_mode:
        print(f"   當前時間: {now}")
    
    for stock_id in all_stock_ids:
        company_name = stock_mapping.get(stock_id, f'股票{stock_id}')
        
        # Generate expected filename with Type 12 support
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
                debug_msg = f"   {stock_id}: CSV時間 {last_update_time}, {hours_ago:.1f}h前, 成功={success}"
                if str(parameter) == '11':
                    debug_msg += " [Type 11]"
                elif str(parameter) == '12':
                    debug_msg += " [Type 12]"
                elif str(parameter) == '13':
                    debug_msg += " [Type 13]"
                elif str(parameter) == '14':
                    debug_msg += " [Type 14]"
                elif str(parameter) == '15':
                    debug_msg += " [Type 15]"
                print(debug_msg)
            
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
    
    # Enhanced debug for Types 11-16
    if debug_mode and expired_success and str(parameter) in ['11', '12', '13', '14', '15']:
        type_label = f"Type {parameter}"
        if parameter == '11': type_label = '🔵 Type 11'
        elif parameter in ['12', '13', '14', '15']: type_label = f'🆕 Type {parameter}'
        
        print(f"   {type_label} 過期股票範例:")
        for stock_id in expired_success[:5]:
            company_name = stock_mapping.get(stock_id, f'股票{stock_id}')
            filename = f"{folder}_{stock_id}_{company_name}.xls"
            
            if filename in existing_data:
                last_update_str = existing_data[filename]['last_update_time']
                last_update_time = parse_csv_datetime(last_update_str)
                if last_update_time:
                    hours_ago = (now - last_update_time).total_seconds() / 3600
                    data_type_label = "機構數據" if parameter == '11' else ("月度P/E" if parameter == '12' else ("每日融資" if parameter == '13' else ("每周融資" if parameter == '14' else "每月融資")))
                    print(f"     {stock_id}: CSV時間 {last_update_str} ({hours_ago:.1f}h前) [{data_type_label}]")
    
    if priority_stocks:
        reprocess_reasons = []
        if failed_stocks:
            reprocess_reasons.append(f"{len(failed_stocks)}個失敗")
        if not_processed_stocks:
            reprocess_reasons.append(f"{len(not_processed_stocks)}個未處理")
        if expired_success:
            reprocess_reasons.append(f"{len(expired_success)}個過期成功")
        
        reason_str = "、".join(reprocess_reasons)
        strategy_msg = f"需要處理策略: 處理 {len(priority_stocks)} 個股票 ({reason_str})"
        if str(parameter) == '11':
            strategy_msg += f" [Type 11 機構數據]"
        elif str(parameter) == '12':
            strategy_msg += f" [Type 12 月度P/E]"
        elif str(parameter) == '13':
            strategy_msg += f" [Type 13 融資融券]"
        elif str(parameter) == '14':
            strategy_msg += f" [Type 14 每周融資融券]"
        elif str(parameter) == '15':
            strategy_msg += f" [Type 15 每月融資融券]"
        print(strategy_msg)
        return priority_stocks, "REPROCESS_NEEDED"
    elif fresh_success:
        print(f"無需處理: 所有 {len(fresh_success)} 個股票在24小時內已成功處理")
        return [], "UP_TO_DATE"
    else:
        scan_msg = f"初始掃描: 執行首次完整掃描"
        if str(parameter) == '11':
            scan_msg += f" [Type 11 機構數據初始化]"
        elif str(parameter) == '12':
            scan_msg += f" [Type 12 月度P/E初始化]"
        elif str(parameter) == '13':
            scan_msg += f" [Type 13 融資融券初始化]"
        elif str(parameter) == '14':
            scan_msg += f" [Type 14 每周融資融券初始化]"
        elif str(parameter) == '15':
            scan_msg += f" [Type 15 每月融資融券初始化]"
        elif str(parameter) == '16':
            scan_msg += f" [Type 16 單季財務比率表初始化]"
        print(scan_msg)
        return all_stock_ids, "INITIAL_SCAN"

def save_csv_results_csv_only(parameter, stock_ids, results_data, process_times, stock_mapping, retry_stats=None, last_update_times=None):
    """Enhanced CSV-ONLY: Save CSV results with per-stock completion timestamps"""
    
    # Enhanced folder mapping for complete 16 data types (v3.1.0)
    folder_mapping = {
        '1': 'DividendDetail', '2': 'BasicInfo', '3': 'StockDetail',
        '4': 'StockBzPerformance', '5': 'ShowSaleMonChart', '6': 'EquityDistribution',
        '7': 'StockBzPerformance1', '8': 'ShowK_ChartFlow', '9': 'StockHisAnaQuar',
        '10': 'EquityDistributionClassHis', '11': 'WeeklyTradingData', '12': 'ShowMonthlyK_ChartFlow',
        '13': 'ShowMarginChart', '14': 'ShowMarginChartWeek', '15': 'ShowMarginChartMonth',
        '16': 'StockFinDetail'  # 🆕 NEW Type 16
    }
    folder = folder_mapping.get(parameter, f'DataType{parameter}')
    
    if not os.path.exists(folder):
        os.makedirs(folder)
        create_msg = f"建立資料夾: {folder}"
        if str(parameter) == '11':
            create_msg += f" [🔵 Type 11 機構數據資料夾]"
        elif str(parameter) == '12':
            create_msg += f" [🆕 Type 12 月度P/E資料夾]"
        elif str(parameter) == '13':
            create_msg += f" [🆕 Type 13 融資融券資料夾]"
        elif str(parameter) == '14':
            create_msg += f" [🆕 Type 14 每周融資融券資料夾]"
        elif str(parameter) == '15':
            create_msg += f" [🆕 Type 15 每月融資融券資料夾]"
        elif str(parameter) == '16':
            create_msg += f" [🆕 Type 16 單季財務比率表資料夾]"
        print(create_msg)
    
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
                
                # Enhanced filename generation with Type 12 support
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

                    # NEW: Use per-stock completion time for accurate timestamps
                    if success == 'true':
                        # Use actual download completion time if available, fallback to current_time
                        last_update = last_update_times.get(stock_id, current_time) if last_update_times else current_time
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
        
        save_msg = f"CSV-ONLY CSV結果已儲存: {csv_filepath}"
        if str(parameter) == '11':
            save_msg += f" [🔵 Type 11 機構數據記錄]"
        elif str(parameter) == '12':
            save_msg += f" [🆕 Type 12 月度P/E記錄]"
        elif str(parameter) == '13':
            save_msg += f" [🆕 Type 13 融資融券記錄]"
        elif str(parameter) == '14':
            save_msg += f" [🆕 Type 14 每周融資融券記錄]"
        elif str(parameter) == '15':
            save_msg += f" [🆕 Type 15 每月融資融券記錄]"
        elif str(parameter) == '16':
            save_msg += f" [🆕 Type 16 單季財務比率表記錄]"
        print(save_msg)
        
        # Enhanced summary with Types 11-16 support
        if results_data:
            total_stocks = len(stock_ids)
            processed_count = len(results_data)
            success_count = sum(1 for success in results_data.values() if success)
            success_rate = (success_count / processed_count * 100) if processed_count > 0 else 0
            
            summary_title = f"{folder} 摘要 (CSV-ONLY版本"
            if str(parameter) == '11':
                summary_title += f" - Type 11 機構數據"
            elif str(parameter) == '12':
                summary_title += f" - Type 12 月度P/E"
            elif str(parameter) == '13':
                summary_title += f" - Type 13 融資融券"
            elif str(parameter) == '14':
                summary_title += f" - Type 14 每周融資融券"
            elif str(parameter) == '15':
                summary_title += f" - Type 15 每月融資融券"
            elif str(parameter) == '16':
                summary_title += f" - Type 16 單季財務比率表"
            summary_title += "):"
            print(summary_title)
            
            print(f"   CSV 總股票數: {total_stocks}")
            print(f"   本次處理股票數: {processed_count}")
            print(f"   本次成功數: {success_count}")
            print(f"   本次成功率: {success_rate:.1f}%")
            
            if retry_stats:
                total_attempts = sum(stats.get('attempts', 1) for stats in retry_stats.values())
                total_retries = sum(max(0, stats.get('attempts', 1) - 1) for stats in retry_stats.values())
                print(f"   總嘗試次數: {total_attempts}")
                print(f"   總重試次數: {total_retries}")
                
                # Types 11-16 specific retry analysis
                if str(parameter) in ['11', '12', '13', '14', '15', '16'] and total_retries > 0:
                    avg_retries = total_retries / processed_count if processed_count > 0 else 0
                    if parameter == '11':
                        data_type_label = "機構數據複雜度"
                    elif parameter == '12':
                        data_type_label = "月度P/E複雜度"
                    elif parameter == '16':
                        data_type_label = "單季比率複雜度"
                    else:
                        data_type_label = "融資融券複雜度"
                    print(f"   {'🔵' if parameter == '11' else '🆕'} Type {parameter} 平均重試: {avg_retries:.1f} ({data_type_label})")
            
            print(f"   CSV 位置: {csv_filepath}")
        
    except Exception as e:
        print(f"儲存 CSV 時發生錯誤: {e}")

# Original helper functions (enhanced for Type 12)
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
    """Show enhanced usage information for v3.1.0 with complete 16 data types"""
    print("=" * 70)
    print("Enhanced Batch Stock Data Downloader (v3.1.0)")
    print("Complete 16 Data Types with CSV-ONLY 24-Hour Freshness Policy")
    print("ENHANCED: EPS x PER Monthly & Multi-Frequency Margin Balance for Long-Term Valuation & Sentiment Analysis")
    print("FIXED: Uses ONLY CSV records for freshness, ignores file timestamps")
    print("=" * 70)
    print()
    print("CSV-ONLY FEATURES:")
    print("   ✅ CSV-ONLY Policy: Uses CSV last_update_time for freshness")
    print("   ✅ No File Checks: Ignores file timestamps entirely")
    print("   ✅ Pipeline Compatible: Works in CI/CD where files are always new")
    print("   ✅ Accurate Tracking: CSV is source of truth for processing history")
    print("   🔵 Type 11 Support: Weekly Trading Data with Institutional Flows")
    print("   🆕 Type 12 Support: EPS x PER Monthly for Long-Term Analysis")
    print("   🆕 Type 13 Support: Daily Margin Balance for Market Sentiment")
    print("   🆕 Type 14 Support: Weekly Margin Balance")
    print("   🆕 Type 15 Support: Monthly Margin Balance")
    print("   🆕 Type 16 Support: Quarterly Financial Ratio Analysis")
    print("   🔧 Enhanced Debug: Detailed CSV record analysis")
    print()
    print("Data Types (Complete 16 Types - v3.1.0 ENHANCED):")
    for dt, desc in DATA_TYPE_DESCRIPTIONS.items():
        if dt == '11':
            print(f"   {dt} = {desc} 🔵")
        elif dt in ['12', '13', '14', '15', '16']:
            print(f"   {dt} = {desc} 🆕 NEW!")
        else:
            print(f"   {dt} = {desc}")
    print()
    print("Type 12 Features (NEW!):")
    print("   📊 20-year monthly EPS and P/E ratio data")
    print("   📈 Conservative P/E multiples (9X-19X) for long-term analysis")
    print("   📅 Monthly frequency for fundamental analysis")
    print("   🔍 Backtesting support with extended historical coverage")
    print("   📋 Complements Type 8 weekly analysis (15X-30X multiples)")
    print("   🎯 Long-term valuation modeling and portfolio management")
    print()
    print("Type 13/14/15 Features (NEW!):")
    print("   📊 Margin Balance & Short Selling data (Daily/Weekly/Monthly)")
    print("   📈 Margin Usage Rate & Maintenance Rate analysis")
    print("   📅 Multi-frequency suitable for market sentiment tracking")
    print("   🔍 1-year (Daily), 5-year (Weekly), 20-year (Monthly) history")
    print("   📋 Complements Type 11 weekly trading data")
    print()
    print("Type 16 Features (NEW!):")
    print("   📊 Quarterly financial ratio analysis (latest 10 quarters)")
    print("   📈 Profitability, efficiency, and solvency ratio review")
    print("   📅 Quarterly granularity for fundamentals tracking")
    print("   📋 Complements quarterly performance and analysis types")
    print()
    print("Options:")
    print("   --test   = Process only first 3 stocks (testing)")
    print("   --debug  = Show detailed CSV record analysis")
    print("   --direct = Simple execution mode (compatibility test)")
    print()
    print("CSV-ONLY Examples (v3.1.0):")
    print("   python GetAll.py 1          # CSV-ONLY: accurate freshness from records")
    print("   python GetAll.py 11         # CSV-ONLY: Type 11 institutional flows 🔵")
    print("   python GetAll.py 12         # CSV-ONLY: Type 12 monthly P/E analysis 🆕")
    print("   python GetAll.py 13         # CSV-ONLY: Type 13 daily margin balance 🆕")
    print("   python GetAll.py 14         # CSV-ONLY: Type 14 weekly margin balance 🆕")
    print("   python GetAll.py 15         # CSV-ONLY: Type 15 monthly margin balance 🆕")
    print("   python GetAll.py 16         # CSV-ONLY: Type 16 quarterly financial ratio analysis 🆕")
    print("   python GetAll.py 12 --debug # CSV-ONLY: Type 12 with detailed analysis 🆕")  
    print("   python GetAll.py 7 --test   # CSV-ONLY: test mode with CSV analysis")
    print()

def main():
    """Enhanced CSV-ONLY main function with complete 16 data types support (v3.1.0)"""
    global current_results_data, current_process_times, current_last_update_times, current_stock_ids, current_parameter, current_stock_mapping
    
    print("=" * 70)
    print("Enhanced Batch Stock Data Downloader (v3.1.0)")
    print("Complete 16 Data Types with CSV-ONLY 24-Hour Freshness Policy")
    print("ENHANCED: EPS x PER Monthly for Long-Term Valuation Analysis")
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
        print("   python GetAll.py 11     # CSV-ONLY weekly trading data 🔵")
        print("   python GetAll.py 12     # CSV-ONLY monthly P/E analysis (NEW!) 🆕")
        print("   python GetAll.py 13     # CSV-ONLY daily margin balance (NEW!) 🆕")
        print("   python GetAll.py 14     # CSV-ONLY weekly margin balance (NEW!) 🆕")
        print("   python GetAll.py 15     # CSV-ONLY monthly margin balance (NEW!) 🆕")
        sys.exit(1)
    
    parameter = sys.argv[1]
    test_mode = '--test' in sys.argv
    debug_mode = '--debug' in sys.argv
    direct_mode = '--direct' in sys.argv
    csv_file = "StockID_TWSE_TPEX.csv"
    
    # Enhanced validation for complete 16 data types
    if parameter not in DATA_TYPE_DESCRIPTIONS:
        print(f"Invalid data type: {parameter}")
        print("Valid data types:")
        for dt, desc in DATA_TYPE_DESCRIPTIONS.items():
            if dt == '11':
                print(f" {dt} = {desc} 🔵")
            elif dt in ['12', '13', '14', '15', '16']:
                print(f" {dt} = {desc} 🆕 NEW!")
            else:
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
        test_msg = f"[測試模式] 只處理前 {len(stock_ids)} 支股票"
        if parameter == '11':
            test_msg += f" [🔵 Type 11 測試]"
        elif parameter == '12':
            test_msg += f" [🆕 Type 12 測試]"
        elif parameter == '13':
            test_msg += f" [🆕 Type 13 測試]"
        elif parameter == '14':
            test_msg += f" [🆕 Type 14 測試]"
        elif parameter == '15':
            test_msg += f" [🆕 Type 15 測試]"
        elif parameter == '16':
            test_msg += f" [🆕 Type 16 測試]"
        print(test_msg)
    
    if debug_mode:
        debug_msg = "[除錯模式] 將顯示詳細CSV記錄分析"
        if parameter == '11':
            debug_msg += f" [🔵 Type 11 機構數據分析]"
        elif parameter == '12':
            debug_msg += f" [🆕 Type 12 月度P/E分析]"
        elif parameter == '13':
            debug_msg += f" [🆕 Type 13 融資融券分析]"
        elif parameter == '14':
            debug_msg += f" [🆕 Type 14 融資融券分析]"
        elif parameter == '15':
            debug_msg += f" [🆕 Type 15 融資融券分析]"
        elif parameter == '16':
            debug_msg += f" [🆕 Type 16 財務比率分析]"
        print(debug_msg)
    
    print(f"資料類型: {data_desc}")
    if parameter == '11':
        print(f"🔵 Type 11 特色:")
        print(f"   📊 完整週交易資料含OHLC價格數據")
        print(f"   💰 交易量與成交金額分析") 
        print(f"   🏛️ 三大法人資金流向 (外資/投信/自營)")
        print(f"   📈 融資融券與借券賣出數據")
        print(f"   🔍 市場微結構分析")
    elif parameter == '12':
        print(f"🆕 NEW! Type 12 特色:")
        print(f"   📊 20年月度EPS與本益比數據")
        print(f"   📈 保守本益比倍數 (9X-19X) 長期分析")
        print(f"   📅 月度頻率適合基本面分析")
        print(f"   🔍 支援回測與長期投資策略")
        print(f"   📋 補充Type 8週度分析 (15X-30X倍數)")
        print(f"   🎯 長期估值建模與組合管理")
    elif parameter == '13':
        print(f"🆕 NEW! Type 13 特色:")
        print(f"   📊 每日融資融券餘額詳細資料")
        print(f"   📈 融資使用率與維持率分析")
        print(f"   📅 每日頻率適合市場情緒追蹤")
        print(f"   🔍 1年期每日歷史數據")
        print(f"   📋 補充Type 11週度交易數據")
    elif parameter == '14':
        print(f"🆕 NEW! Type 14 特色:")
        print(f"   📊 每周融資融券餘額詳細資料")
        print(f"   📈 5年期每周歷史數據")
    elif parameter == '15':
        print(f"🆕 NEW! Type 15 特色:")
        print(f"   📊 每月融資融券餘額詳細資料")
        print(f"   📈 20年期每月歷史數據")
    elif parameter == '16':
        print(f"🆕 NEW! Type 16 特色:")
        print(f"   📊 單季財務比率表詳細資料 (近10季)")
        print(f"   📈 獲利、成長、效率與償債能力指標")
    
    print(f"參數: {parameter}")
    print(f"🔧 CSV-ONLY處理: 僅使用CSV記錄判斷新鮮度")
    print(f"✅ 管道相容: 忽略檔案時戳，適用於CI/CD環境")
    print(f"📊 準確追蹤: CSV是處理歷史的唯一真相來源")
    
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    # Enhanced CSV-ONLY smart processing analysis with Type 12 support
    print("CSV-ONLY 智慧處理分析中 (修正的24小時新鮮度政策)...")
    if parameter == '11':
        print("🔵 Type 11: 執行機構資金流向數據分析...")
    elif parameter == '12':
        print("🆕 Type 12: 執行月度本益比長期數據分析...")
    elif parameter == '13':
        print("🆕 Type 13: 執行每日融資融券數據分析...")
    elif parameter == '14':
        print("🆕 Type 14: 執行每周融資融券數據分析...")
    elif parameter == '15':
        print("🆕 Type 15: 執行每月融資融券數據分析...")
    elif parameter == '16':
        print("🆕 Type 16: 執行單季財務比率表數據分析...")
    
    stocks_to_process, processing_strategy = determine_stocks_to_process_csv_only(
        parameter, stock_ids, stock_mapping, debug_mode
    )
    
    if not stocks_to_process:
        finish_msg = "所有資料都是新鮮的 (CSV顯示24小時內)，無需處理!"
        if parameter == '11':
            finish_msg += f" [🔵 Type 11 機構數據已是最新]"
        elif parameter == '12':
            finish_msg += f" [🆕 Type 12 月度P/E已是最新]"
        elif parameter == '13':
            finish_msg += f" [🆕 Type 13 融資融券已是最新]"
        elif parameter == '14':
            finish_msg += f" [🆕 Type 14 每周融資融券已是最新]"
        elif parameter == '15':
            finish_msg += f" [🆕 Type 15 每月融資融券已是最新]"
        elif parameter == '16':
            finish_msg += f" [🆕 Type 16 單季財務比率表已是最新]"
        print(finish_msg)
        save_csv_results_csv_only(parameter, stock_ids, {}, {}, stock_mapping, {})
        print("任務完成!")
        return
    
    # Update processing list for test mode
    original_count = len(stock_ids)
    if test_mode and processing_strategy != "UP_TO_DATE":
        stocks_to_process = stocks_to_process[:3]
        test_limit_msg = f"[測試模式] 限制處理 {len(stocks_to_process)} 支股票"
        if parameter == '11':
            test_limit_msg += f" [🔵 Type 11 測試]"
        elif parameter == '12':
            test_limit_msg += f" [🆕 Type 12 測試]"
        elif parameter == '13':
            test_limit_msg += f" [🆕 Type 13 測試]"
        elif parameter == '14':
            test_limit_msg += f" [🆕 Type 14 測試]"
        elif parameter == '15':
            test_limit_msg += f" [🆕 Type 15 測試]"
        elif parameter == '16':
            test_limit_msg += f" [🆕 Type 16 測試]"
        print(test_limit_msg)
    
    processing_count = len(stocks_to_process)
    print(f"處理策略: {processing_strategy}")
    print(f"處理範圍: {processing_count}/{original_count} 支股票")
    print(f"🔧 CSV-ONLY: 每支股票最多 4 次嘗試機會 (1+3)")
    if parameter == '11':
        print(f"🔵 Type 11: 機構數據複雜度 - 延長超時與重試間隔")
    elif parameter == '12':
        print(f"🆕 Type 12: 月度P/E複雜度 - 20年數據處理優化")
    elif parameter == '13':
        print(f"🆕 Type 13: 每日數據複雜度 - 每日融資融券處理優化")
    elif parameter in ['14', '15']:
        print(f"🆕 Type {parameter}: 融資融券數據複雜度 - 處理優化")
    elif parameter == '16':
        print(f"🆕 Type 16: 單季財務比率表數據複雜度 - 處理優化")
    print(f"✅ 記錄導向: 成功後更新CSV時戳為當前時間")
    print("-" * 70)
    
    # Enhanced batch processing with CSV-ONLY approach and Types 11/12 support
    success_count = 0
    failed_count = 0
    results_data = {}
    process_times = {}
    last_update_times = {}  # NEW: Track actual completion time per stock
    retry_stats = {}
    
    # Initialize CSV with enhanced CSV-ONLY logic
    init_msg = f"初始化 CSV-ONLY CSV 檔案..."
    if parameter == '11':
        init_msg += f" [🔵 Type 11 機構數據結構]"
    elif parameter == '12':
        init_msg += f" [🆕 Type 12 月度P/E結構]"
    elif parameter == '13':
        init_msg += f" [🆕 Type 13 融資融券結構]"
    elif parameter == '14':
        init_msg += f" [🆕 Type 14 每周融資融券結構]"
    elif parameter == '15':
        init_msg += f" [🆕 Type 15 每月融資融券結構]"
    elif parameter == '16':
        init_msg += f" [🆕 Type 16 單季財務比率表結構]"
    print(init_msg)
    save_csv_results_csv_only(parameter, stock_ids, {}, {}, stock_mapping, {})
    
    # Enhanced processing with Types 11/12 considerations
    total_attempts = 0
    for i, stock_id in enumerate(stocks_to_process, 1):
        # Skip TAIEX (0000) for unsupported data types
        if stock_id == '0000' and str(parameter) in ['1', '4', '5', '6', '7', '9', '10', '12', '15', '16']:
            print(f"\n[{i}/{len(stocks_to_process)}] ⚠️ 跳過 TAIEX (0000): Data Type {parameter} 不支援此指數")
            # Record as handled (success=True) to prevent retries and ensure correct CSV entry
            results_data[stock_id] = True
            process_times[stock_id] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            retry_stats[stock_id] = {'attempts': 1, 'error': 'Skipped (Unsupported Index)', 'duration': 0}
            continue

        process_msg = f"\n[{i}/{len(stocks_to_process)}] 處理股票: {stock_id}"
        if parameter == '11':
            process_msg += f" [🔵 Type 11 機構數據]"
        elif parameter == '12':
            process_msg += f" [🆕 Type 12 月度P/E]"
        elif parameter == '13':
            process_msg += f" [🆕 Type 13 融資融券]"
        elif parameter == '14':
            process_msg += f" [🆕 Type 14 每周融資融券]"
        elif parameter == '15':
            process_msg += f" [🆕 Type 15 每月融資融券]"
        elif parameter == '16':
            process_msg += f" [🆕 Type 16 單季財務比率表]"
        print(process_msg)
        
        # Record start time
        current_process_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        process_times[stock_id] = current_process_time
        
        # Execute with enhanced retry mechanism including Types 11/12 support
        success, attempts, error_msg, duration = run_get_good_info_with_retry(
            stock_id, parameter, debug_mode, max_retries=3
        )

        # NEW: Record actual completion time (when download finished)
        download_complete_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        last_update_times[stock_id] = download_complete_time

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
        current_last_update_times = last_update_times.copy()  # NEW: Track completion times
        current_retry_stats = retry_stats.copy()
        
        if success:
            success_count += 1
            success_msg = f"   🎯 "
            if attempts > 1:
                success_msg += f"重試成功: 第 {attempts} 次嘗試成功"
            else:
                success_msg += f"首次成功"
            if parameter == '11':
                success_msg += f" [Type 11 機構數據完成]"
            elif parameter == '12':
                success_msg += f" [Type 12 月度P/E完成]"
            elif parameter == '13':
                success_msg += f" [Type 13 融資融券完成]"
            elif parameter == '14':
                success_msg += f" [Type 14 每周融資融券完成]"
            elif parameter == '15':
                success_msg += f" [Type 15 每月融資融券完成]"
            elif parameter == '16':
                success_msg += f" [Type 16 單季財務比率表完成]"
            print(success_msg)
        else:
            failed_count += 1
            failure_msg = f"   💥 最終失敗: {attempts} 次嘗試後失敗 (最多4次)"
            if parameter == '11':
                failure_msg += f" [Type 11 機構數據失敗]"
            elif parameter == '12':
                failure_msg += f" [Type 12 月度P/E失敗]"
            elif parameter == '13':
                failure_msg += f" [Type 13 融資融券失敗]"
            elif parameter == '14':
                failure_msg += f" [Type 14 每周融資融券失敗]"
            elif parameter == '15':
                failure_msg += f" [Type 15 每月融資融券失敗]"
            elif parameter == '16':
                failure_msg += f" [Type 16 單季財務比率表失敗]"
            print(failure_msg)
        
        # Save progress after each stock with enhanced CSV-ONLY logic
        try:
            save_csv_results_csv_only(parameter, stock_ids, results_data, process_times, stock_mapping, retry_stats, last_update_times)
            progress_msg = f"   📁 CSV-ONLY CSV 已更新 ({i}/{len(stocks_to_process)} 完成)"
            if parameter == '11':
                progress_msg += f" [Type 11]"
            elif parameter == '12':
                progress_msg += f" [Type 12]"
            elif parameter == '13':
                progress_msg += f" [Type 13]"
            elif parameter == '14':
                progress_msg += f" [Type 14]"
            elif parameter == '15':
                progress_msg += f" [Type 15]"
            elif parameter == '16':
                progress_msg += f" [Type 16]"
            print(progress_msg)
        except Exception as e:
            print(f"   ⚠️ CSV 更新失敗: {e}")
        
        # Enhanced delay between stocks with Types 11-16 considerations
        if i < len(stocks_to_process):
            if parameter in ['11', '12', '13', '14', '15', '16']:
                delay = 5 if success else 8  # Extended for complex data types
            else:
                delay = 3 if success else 5
            time.sleep(delay)
    
    # Final CSV save with enhanced CSV-ONLY logic
    print("\n" + "=" * 70)
    final_save_msg = "最終 CSV-ONLY CSV 結果..."
    if parameter == '11':
        final_save_msg += f" [🔵 Type 11 機構數據完整記錄]"
    elif parameter == '12':
        final_save_msg += f" [🆕 Type 12 月度P/E完整記錄]"
    elif parameter == '13':
        final_save_msg += f" [🆕 Type 13 融資融券完整記錄]"
    elif parameter == '14':
        final_save_msg += f" [🆕 Type 14 每周融資融券完整記錄]"
    elif parameter == '15':
        final_save_msg += f" [🆕 Type 15 每月融資融券完整記錄]"
    elif parameter == '16':
        final_save_msg += f" [🆕 Type 16 單季財務比率表完整記錄]"
    print(final_save_msg)
    save_csv_results_csv_only(parameter, stock_ids, results_data, process_times, stock_mapping, retry_stats, last_update_times)
    
    # Enhanced Summary with CSV-ONLY approach and Types 11/12 support
    print("\n" + "=" * 70)
    print("Enhanced Execution Summary (v3.1.0) - Pipeline Compatible")
    print("Complete 16 Data Types + CSV-ONLY Freshness + Enhanced Processing")
    if parameter == '11':
        print("🔵 Type 11 Weekly Trading Data with Institutional Flows")
    elif parameter == '12':
        print("🆕 NEW! Type 12 EPS x PER Monthly for Long-Term Analysis")
    elif parameter == '13':
        print("🆕 NEW! Type 13 Daily Margin Balance for Market Sentiment")
    elif parameter == '14':
        print("🆕 NEW! Type 14 Weekly Margin Balance")
    elif parameter == '15':
        print("🆕 NEW! Type 15 Monthly Margin Balance")
    elif parameter == '16':
        print("🆕 NEW! Type 16 Quarterly Financial Ratio Analysis")
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
        success_rate_msg = f"🎯 CSV-ONLY 最終成功率: {final_success_rate:.1f}%"
        if parameter == '11':
            success_rate_msg += f" (Type 11 機構數據處理)"
        elif parameter == '12':
            success_rate_msg += f" (Type 12 月度P/E處理)"
        elif parameter == '13':
            success_rate_msg += f" (Type 13 融資融券處理)"
        elif parameter == '14':
            success_rate_msg += f" (Type 14 每周融資融券處理)"
        elif parameter == '15':
            success_rate_msg += f" (Type 15 每月融資融券處理)"
        elif parameter == '16':
            success_rate_msg += f" (Type 16 單季財務比率表處理)"
        else:
            success_rate_msg += f" (標準處理)"
        print(success_rate_msg)
    
    # Show enhanced CSV-ONLY improvements with Types 11/12 features
    print(f"\n✅ CSV-ONLY 改善項目:")
    print(f"   • 僅使用CSV: 完全忽略檔案時戳，使用CSV記錄")
    print(f"   • 管道相容: 適用於CI/CD環境，檔案總是新的")
    print(f"   • 準確追蹤: CSV是處理歷史的唯一真相來源")
    print(f"   • 成功更新: 成功處理後立即更新CSV時戳")
    if parameter == '11':
        print(f"   🔵 Type 11 增強:")
        print(f"     - 機構資金流向數據支援")
        print(f"     - 延長超時時間適應複雜度")
        print(f"     - 專用重試間隔配置")
        print(f"     - 完整週交易數據記錄")
    elif parameter == '12':
        print(f"   🆕 Type 12 增強:")
        print(f"     - 月度本益比長期數據支援")
        print(f"     - 20年歷史數據處理優化")
        print(f"     - 保守倍數分析 (9X-19X)")
        print(f"     - 長期估值模型支援")
        print(f"     - 補充週度分析 (Type 8)")
    elif parameter == '13':
        print(f"   🆕 Type 13 增強:")
        print(f"     - 每日融資融券餘額數據支援")
        print(f"     - 1年期每日歷史數據")
        print(f"     - 市場情緒指標追蹤")
        print(f"     - 補充Type 11週度數據")
    elif parameter in ['14', '15']:
        print(f"   🆕 Type {parameter} 增強:")
        print(f"     - 融資融券餘額數據支援")
        print(f"     - 歷史數據趨勢分析")
    elif parameter == '16':
        print(f"   🆕 Type 16 增強:")
        print(f"     - 單季財務比率表數據支援")
        print(f"     - 近10季財務比率趨勢追蹤")
    
    print(f"\n結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed_count > 0:
        print(f"\n⚠️ 仍有 {failed_count} 支股票經4次嘗試後失敗")
        print("建議:")
        print("   • 檢查網路連線狀態")
        print("   • 使用 --debug 查看詳細錯誤")
        print("   • 單獨執行失敗股票: python GetGoodInfo.py [股票代號] [類型]")
        print("   • CSV-ONLY: 現在能準確追蹤基於記錄的處理歷史")
        if parameter == '11':
            print("   🔵 Type 11 特別建議:")
            print("     - 機構數據複雜，可能需要多次重試")
            print("     - 檢查網路穩定性以處理大量數據")
            print("     - 考慮在網路較佳時段重新執行")
        elif parameter == '12':
            print("   🆕 Type 12 特別建議:")
            print("     - 20年月度數據量大，需要穩定連線")
            print("     - 檢查磁碟空間以存儲大量歷史資料")
            print("     - 考慮分批處理以降低單次負載")
            print("     - 與Type 8搭配使用獲得完整P/E分析")
        elif parameter == '13':
            print("   🆕 Type 13 特別建議:")
            print("     - 每日數據更新頻繁，確保使用最新數據")
            print("     - 檢查 '查1年' 按鈕是否可用")
            print("     - 適合在收盤後執行 (Evening)")
        elif parameter in ['14', '15']:
            print(f"   🆕 Type {parameter} 特別建議:")
            print("     - 檢查相關按鈕 ('查5年'/'查20年') 是否可用")
        elif parameter == '16':
            print("   🆕 Type 16 特別建議:")
            print("     - 等待 5 秒讓季度資料載入後再下載")
    else:
        complete_msg = f"\n🎉 完美執行! 所有 {success_count} 支股票均處理成功"
        if parameter == '11':
            complete_msg += f" [🔵 Type 11 機構數據完整]"
        elif parameter == '12':
            complete_msg += f" [🆕 Type 12 月度P/E完整]"
        elif parameter == '13':
            complete_msg += f" [🆕 Type 13 融資融券完整]"
        elif parameter == '14':
            complete_msg += f" [🆕 Type 14 每周融資融券完整]"
        elif parameter == '15':
            complete_msg += f" [🆕 Type 15 每月融資融券完整]"
        elif parameter == '16':
            complete_msg += f" [🆕 Type 16 單季財務比率表完整]"
        print(complete_msg)
        
        if total_attempts > len(stocks_to_process):
            improvement = total_attempts - len(stocks_to_process)
            improvement_msg = f"💪 重試機制額外挽救了 {improvement} 次失敗"
            if parameter == '11':
                improvement_msg += f" [Type 11 機構數據韌性]"
            elif parameter == '12':
                improvement_msg += f" [Type 12 月度數據韌性]"
            elif parameter == '13':
                improvement_msg += f" [Type 13 每日數據韌性]"
            elif parameter in ['14', '15']:
                improvement_msg += f" [Type {parameter} 數據韌性]"
            elif parameter == '16':
                improvement_msg += f" [Type 16 單季數據韌性]"
            print(improvement_msg)
        
        final_achievement = f"✅ CSV-ONLY版本提供準確的記錄導向處理追蹤"
        if parameter == '11':
            final_achievement += f"\n🚀 Type 11 機構資金流向數據下載完成 - 包含外資、投信、自營完整交易資訊!"
        elif parameter == '12':
            final_achievement += f"\n🚀 Type 12 月度本益比數據下載完成 - 包含20年月度P/E分析支援長期投資策略!"
        elif parameter == '13':
            final_achievement += f"\n🚀 Type 13 每日融資融券餘額下載完成 - 包含每日市場情緒指標!"
        elif parameter == '14':
            final_achievement += f"\n🚀 Type 14 每周融資融券餘額下載完成!"
        elif parameter == '15':
            final_achievement += f"\n🚀 Type 15 每月融資融券餘額下載完成!"
        print(final_achievement)

if __name__ == "__main__":
    main()
