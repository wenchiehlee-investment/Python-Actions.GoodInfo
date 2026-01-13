import os
import csv
from datetime import datetime, timezone

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
    # Initialize with current time
    oldest_time = datetime.now(timezone.utc)
    oldest_type_id = 11 # Default fallback to Weekly Trading Data if all else fails
    
    found_any = False

    for type_id, folder in FOLDER_MAPPING.items():
        # Skip manual types (Basic Info and Stock Details don't need regular updates)
        if type_id in [2, 3]: 
            continue
            
        csv_path = os.path.join(folder, 'download_results.csv')
        
        # If folder or CSV doesn't exist, this data type is "empty/never run".
        # We should prioritize it immediately.
        if not os.path.exists(csv_path):
            print(f"{type_id}") # Print ID and exit
            return
            
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if not rows:
                    # Empty CSV means no data, prioritize it
                    print(f"{type_id}")
                    return
                
                # Find the LATEST 'process_time' in this folder.
                # This represents when this data type was LAST updated.
                # We want to find the folder whose "last update" was the longest time ago.
                
                folder_latest_update = datetime.min.replace(tzinfo=timezone.utc)
                
                for row in rows:
                    try:
                        # Parse time (CSV times are UTC string like '2026-01-02 14:12:01')
                        # We append ' UTC' to match format if needed, or just assume UTC
                        t_str = row.get('process_time', '')
                        if not t_str: continue
                        
                        # Handle potential formats
                        ts = datetime.strptime(t_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                        
                        if ts > folder_latest_update:
                            folder_latest_update = ts
                    except (ValueError, KeyError):
                        continue
                
                # Now compare this folder's "latest update" with our running "oldest found so far"
                if folder_latest_update < oldest_time:
                    oldest_time = folder_latest_update
                    oldest_type_id = type_id
                    found_any = True
                    
        except Exception:
            # On error reading a folder, maybe skip or prioritize? 
            # Let's skip to avoid getting stuck on a corrupt file
            continue
            
    print(f"{oldest_type_id}")

if __name__ == "__main__":
    get_oldest_data_type()
