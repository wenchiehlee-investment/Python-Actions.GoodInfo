import os
import csv
from datetime import datetime, timezone, timedelta

# Folder mapping from download_results_counts.py
FOLDER_MAPPING = {
    1: "DividendDetail",
    2: "BasicInfo",
    3: "StockDetail", 
    4: "StockBzPerformance",
    5: "ShowSaleMonChart",
    6: "EquityDistribution",
    7: "StockBzPerformance1",
    8: "ShowK_ChartFlow",
    9: "StockHisAnaQuar",
    10: "EquityDistributionClassHis",
    11: "WeeklyTradingData",
    12: "ShowMonthlyK_ChartFlow",
    13: "ShowMarginChart",
    14: "ShowMarginChartWeek",
    15: "ShowMarginChartMonth",
    16: "StockFinDetail"
}

def get_oldest_data_type():
    now = datetime.now(timezone.utc)
    oldest_time = now
    oldest_type_id = None
    
    # Threshold for staleness
    STALE_THRESHOLD_DAYS = 5

    for type_id, folder in FOLDER_MAPPING.items():
        # Skip manual types
        if type_id in [2, 3]: 
            continue
            
        csv_path = os.path.join(folder, 'download_results.csv')
        
        # Priority 1: If folder/CSV missing, it's never been run. Prioritize immediately.
        if not os.path.exists(csv_path):
            print(f"{type_id}")
            return
            
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # Priority 2: Empty CSV means no successful data. Prioritize.
                if not rows:
                    print(f"{type_id}")
                    return
                
                # Find the LATEST update time for this specific data type folder
                folder_latest_update = datetime.min.replace(tzinfo=timezone.utc)
                valid_rows = 0
                
                for row in rows:
                    try:
                        t_str = row.get('process_time', '')
                        if not t_str: continue
                        
                        # Parse time (CSV times are 'YYYY-MM-DD HH:MM:SS')
                        # We treat them as UTC to match the system
                        ts = datetime.strptime(t_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                        
                        if ts > folder_latest_update:
                            folder_latest_update = ts
                        valid_rows += 1
                    except (ValueError, KeyError):
                        continue
                
                if valid_rows == 0:
                    # CSV exists but no valid dates? Treat as empty.
                    print(f"{type_id}")
                    return

                # Now, find the "Global Oldest" among all folders
                # We want the folder whose "latest update" is the furthest in the past
                if folder_latest_update < oldest_time:
                    oldest_time = folder_latest_update
                    oldest_type_id = type_id
                    
        except Exception:
            continue
            
    # Final Check: Is the oldest data actually "stale" enough?
    if oldest_type_id is not None:
        age = now - oldest_time
        if age.days >= STALE_THRESHOLD_DAYS:
            print(f"{oldest_type_id}")
        else:
            # Nothing is older than 5 days
            pass

if __name__ == "__main__":
    get_oldest_data_type()