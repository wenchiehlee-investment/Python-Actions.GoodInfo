#!/usr/bin/env python3
"""
Enhanced Download Results Count Analyzer with Compact Time Formats and Oldest Column (v1.9.0)
"""

import os
import csv
import argparse
import datetime
from typing import Dict, List, Optional
from datetime import datetime as dt, timedelta

# Taiwan timezone support
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    TAIPEI_TZ = ZoneInfo("Asia/Taipei")
except ImportError:
    try:
        import pytz  # Fallback for older Python versions
        TAIPEI_TZ = pytz.timezone('Asia/Taipei')
    except ImportError:
        TAIPEI_TZ = None

# Data type to folder mapping based on GoodInfo project structure (v1.9.0)
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
    10: "EquityDistributionClassHis"
}

def get_taipei_time():
    """Get current time in Taiwan timezone."""
    if TAIPEI_TZ:
        return dt.now(TAIPEI_TZ)
    else:
        return dt.now()

def make_badge(text: str, color="blue"):
    """Generate badge, avoiding spaces being converted to %20"""
    if not text or text in ['N/A', 'Never', '0']:
        return ""  # Empty for zero values and N/A
    
    safe_text = text.replace(" ", "_")
    return f"![](https://img.shields.io/badge/{safe_text}-{color})"

def format_time_compact(time_diff: timedelta) -> str:
    """Convert timedelta to compact format like '3d 2h ago'"""
    if time_diff.total_seconds() < 0:
        return "future"
    
    days = time_diff.days
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 and len(parts) < 2:  # Only show minutes if < 2 larger units
        parts.append(f"{minutes}m")
    
    if not parts:
        return "now"
    
    # For "ago" format, limit to max 2 units for readability
    compact_time = " ".join(parts[:2])
    return f"{compact_time} ago"

def format_duration_compact(time_diff: timedelta) -> str:
    """Convert timedelta to compact duration format like '3d 2h'"""
    if time_diff.total_seconds() <= 0:
        return "N/A"
    
    days = time_diff.days
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 and len(parts) < 2:  # Only show minutes if < 2 larger units
        parts.append(f"{minutes}m")
    
    if not parts:
        return "< 1m"
    
    # Limit to max 2 units for compact display
    return " ".join(parts[:2])

def get_time_badge_color(time_text: str) -> str:
    """Determine badge color based on how recent/old the time is."""
    if not time_text or time_text in ['N/A', 'Never', 'Error']:
        return 'lightgrey'
    
    # Color coding for both recency and staleness
    if 'now' in time_text:
        return 'brightgreen'  # Just now
    elif 'm ago' in time_text and 'h' not in time_text and 'd' not in time_text:
        return 'brightgreen'  # Minutes ago
    elif 'h ago' in time_text and 'd' not in time_text:
        return 'yellow'       # Hours ago
    elif '1d' in time_text:
        return 'yellow'       # 1 day ago
    elif '2d' in time_text or '3d' in time_text:
        return 'orange'       # 2-3 days ago
    elif 'd' in time_text:
        return 'red'          # > 3 days ago
    else:
        return 'blue'         # Default color

def safe_parse_date(date_string: str) -> Optional[dt]:
    """Parse date string with fallback for special values."""
    if not date_string or date_string.strip() in ['NOT_PROCESSED', 'NEVER', '']:
        return None
    
    try:
        # Handle various date formats
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S']:
            try:
                parsed_dt = dt.strptime(date_string.strip(), fmt)
                # Assume parsed datetime is in Taiwan timezone
                if TAIPEI_TZ:
                    parsed_dt = parsed_dt.replace(tzinfo=TAIPEI_TZ)
                return parsed_dt
            except ValueError:
                continue
        return None
    except Exception:
        return None

def analyze_csv(csv_path: str) -> Dict:
    """Analyze a single download_results.csv file with enhanced metrics."""
    current_time = get_taipei_time()
    
    default_stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'updated_from_now': 'N/A',
        'oldest': 'N/A',
        'duration': 'N/A',
        'error': None
    }
    
    if not os.path.exists(csv_path):
        default_stats['error'] = 'File not found'
        return default_stats
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check if file has required columns
            if not reader.fieldnames:
                return default_stats
                
            required_cols = ['filename', 'last_update_time', 'success', 'process_time']
            if not all(col in reader.fieldnames for col in required_cols):
                default_stats['error'] = 'Invalid CSV format'
                return default_stats
            
            rows = list(reader)
            
            if not rows:
                return default_stats
            
            # Calculate basic statistics
            stats = {
                'total': len(rows),
                'success': sum(1 for row in rows if row['success'].lower() == 'true'),
                'failed': sum(1 for row in rows if row['success'].lower() == 'false'),
                'error': None
            }
            
            # Enhanced time-based metrics calculation
            process_times = []
            update_times = []
            
            for row in rows:
                # Process time (for Updated from now and Duration)
                process_time = safe_parse_date(row['process_time'])
                if process_time:
                    process_times.append(process_time)
                
                # Last update time (for Oldest calculation)
                update_time = safe_parse_date(row['last_update_time'])
                if update_time:
                    update_times.append(update_time)
            
            # Calculate Updated from now (most recent process_time)
            if process_times:
                last_process_time = max(process_times)
                
                # Ensure both times are timezone-aware for proper comparison
                if TAIPEI_TZ and last_process_time.tzinfo is None:
                    last_process_time = last_process_time.replace(tzinfo=TAIPEI_TZ)
                
                # Calculate time difference
                if current_time.tzinfo and last_process_time.tzinfo:
                    time_diff = current_time - last_process_time
                else:
                    # Fallback for timezone-naive comparison
                    current_naive = current_time.replace(tzinfo=None) if current_time.tzinfo else current_time
                    last_naive = last_process_time.replace(tzinfo=None) if last_process_time.tzinfo else last_process_time
                    time_diff = current_naive - last_naive
                
                stats['updated_from_now'] = format_time_compact(time_diff)
                
                # Duration (time span from first to last processing)
                if len(process_times) > 1:
                    first_process_time = min(process_times)
                    duration_diff = last_process_time - first_process_time
                    stats['duration'] = format_duration_compact(duration_diff)
                else:
                    stats['duration'] = "single batch"
            else:
                stats['updated_from_now'] = 'Never'
                stats['duration'] = 'N/A'
            
            # Calculate Oldest (oldest last_update_time)
            if update_times:
                oldest_update_time = min(update_times)
                
                # Ensure timezone consistency
                if TAIPEI_TZ and oldest_update_time.tzinfo is None:
                    oldest_update_time = oldest_update_time.replace(tzinfo=TAIPEI_TZ)
                
                # Calculate time difference
                if current_time.tzinfo and oldest_update_time.tzinfo:
                    time_diff = current_time - oldest_update_time
                else:
                    # Fallback for timezone-naive comparison
                    current_naive = current_time.replace(tzinfo=None) if current_time.tzinfo else current_time
                    oldest_naive = oldest_update_time.replace(tzinfo=None) if oldest_update_time.tzinfo else oldest_update_time
                    time_diff = current_naive - oldest_naive
                
                stats['oldest'] = format_time_compact(time_diff)
            else:
                stats['oldest'] = 'Never'
            
            return stats
            
    except Exception as e:
        default_stats['error'] = f"Error reading file: {str(e)}"
        return default_stats

def scan_all_folders() -> List[Dict]:
    """Scan all data type folders and analyze their CSV files."""
    results = []
    
    for data_type in sorted(FOLDER_MAPPING.keys()):
        folder_name = FOLDER_MAPPING[data_type]
        csv_path = os.path.join(folder_name, 'download_results.csv')
        
        # Check if folder exists
        if not os.path.exists(folder_name):
            stats = {
                'No': data_type,
                'Folder': folder_name,
                'Total': 0,
                'Success': 0,
                'Failed': 0,
                'Updated': 'N/A',
                'Oldest': 'N/A',
                'Duration': 'N/A',
                'error': 'Folder not found'
            }
        else:
            # Analyze CSV file
            csv_stats = analyze_csv(csv_path)
            stats = {
                'No': data_type,
                'Folder': folder_name,
                'Total': csv_stats['total'],
                'Success': csv_stats['success'],
                'Failed': csv_stats['failed'],
                'Updated': csv_stats['updated_from_now'],
                'Oldest': csv_stats['oldest'],
                'Duration': csv_stats['duration'],
                'error': csv_stats.get('error')
            }
        
        results.append(stats)
    
    return results

def format_table(results: List[Dict]) -> str:
    """Format results into enhanced 7-column badge-enhanced markdown table."""
    header = "| No | Folder | Total | Success | Failed | Updated from now | Oldest | Duration |\n"
    header += "| -- | -- | -- | -- | -- | -- | -- | -- |\n"

    rows = []
    for r in results:
        no = r["No"]
        folder = r["Folder"]

        # Handle totals with badges
        total = make_badge(str(r["Total"]), "blue") if r["Total"] and r["Total"] > 0 else ""
        
        # Handle success with green badges
        success = make_badge(str(r["Success"]), "success-brightgreen") if r["Success"] and r["Success"] > 0 else ""
        
        # Handle failed with orange badges
        failed = make_badge(str(r["Failed"]), "failed-orange") if r["Failed"] and r["Failed"] > 0 else ""

        # Handle Updated from now with recency-based color coding
        if r["Updated"] != "N/A":
            time_color = get_time_badge_color(r["Updated"])
            updated = make_badge(r["Updated"], time_color)
        else:
            updated = "N/A"
        
        # Handle Oldest with staleness-based color coding
        if r["Oldest"] != "N/A":
            oldest_color = get_time_badge_color(r["Oldest"])  # Same color logic as updated
            oldest = make_badge(r["Oldest"], oldest_color)
        else:
            oldest = "N/A"
            
        # Duration is always blue
        if r["Duration"] != "N/A":
            duration = make_badge(r["Duration"], "blue")
        else:
            duration = "N/A"

        rows.append(f"| {no} | {folder} | {total} | {success} | {failed} | {updated} | {oldest} | {duration} |")

    return header + "\n".join(rows)

def update_readme(table_text: str):
    """Update README.md status section with enhanced 7-column table."""
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print("README.md not found, skipping update")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the status section
    status_start = content.find('## Status')
    if status_start == -1:
        print("No status section found in README.md, skipping update")
        return

    # Find the end of the status table (next ## section)
    next_section = content.find('\n## ', status_start + 1)
    if next_section == -1:
        next_section = len(content)

    # Generate current timestamp in Taiwan timezone
    current_time = get_taipei_time()
    if TAIPEI_TZ:
        update_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        update_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

    # Create new status section with enhanced 7-column table
    new_status = f"## Status\n\nUpdate time: {update_time}\n\n{table_text}\n\n"
    
    # Replace the status section
    new_content = content[:status_start] + new_status + content[next_section:]

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md status section updated successfully with enhanced 7-column table")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze GoodInfo download results across all 10 data types with enhanced badges and compact time formats (v1.9.0)"
    )
    parser.add_argument("--update-readme", action="store_true", help="Update README.md status section with enhanced table")
    parser.add_argument("--show-oldest", action="store_true", help="Highlight folders with oldest data")
    args = parser.parse_args()

    print("Scanning download results across all 10 data types with enhanced metrics...")
    results = scan_all_folders()
    table_text = format_table(results)

    print(table_text)

    if args.show_oldest:
        # Find and highlight the folder with the oldest data
        oldest_folder = None
        oldest_time = None
        
        for r in results:
            if r["Oldest"] != "N/A" and r["Oldest"] != "Never":
                # Simple heuristic: look for 'd' in the oldest time to find stale data
                if 'd' in r["Oldest"] and 'ago' in r["Oldest"]:
                    if oldest_folder is None:
                        oldest_folder = r["Folder"]
                        oldest_time = r["Oldest"]
                    # Could add more sophisticated comparison logic here
        
        if oldest_folder:
            print(f"\nOldest data detected in: {oldest_folder} ({oldest_time})")
        else:
            print("\nNo significantly stale data detected.")

    if args.update_readme:
        update_readme(table_text)

if __name__ == "__main__":
    main()