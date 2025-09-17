#!/usr/bin/env python3
"""
Enhanced Download Results Count Analyzer with Retry Rate Monitoring (v2.0.0)
FIXED: CSV timestamps are UTC, convert to Taipei timezone for consistent display
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
    UTC_TZ = ZoneInfo("UTC")
except ImportError:
    try:
        import pytz  # Fallback for older Python versions
        TAIPEI_TZ = pytz.timezone('Asia/Taipei')
        UTC_TZ = pytz.timezone('UTC')
    except ImportError:
        TAIPEI_TZ = None
        UTC_TZ = None

# Data type to folder mapping based on GoodInfo project structure (v2.0.0)
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

def get_retry_badge_color(retry_display: str) -> str:
    """Determine badge color for retry rate based on reliability."""
    if not retry_display or retry_display == 'N/A':
        return 'lightgrey'
    
    # Extract numeric value from display (e.g., "2.3x" -> 2.3)
    try:
        rate = float(retry_display.replace('x', ''))
        
        if rate <= 1.0:
            return 'brightgreen'  # Perfect reliability (no retries)
        elif rate <= 1.5:
            return 'green'        # Excellent reliability (low retries)
        elif rate <= 2.0:
            return 'yellow'       # Good reliability (moderate retries)
        elif rate <= 3.0:
            return 'orange'       # Poor reliability (high retries)
        else:
            return 'red'          # Very poor reliability (very high retries)
    except (ValueError, IndexError):
        return 'blue'  # Default for unparseable values

def calculate_retry_rate(retry_counts: List[int]) -> str:
    """Calculate and format retry rate for display."""
    if not retry_counts:
        return 'N/A'
    
    avg_retry = sum(retry_counts) / len(retry_counts)
    # Add 1 because retry_count represents additional attempts beyond the first
    total_attempts_avg = avg_retry + 1.0
    
    return f"{total_attempts_avg:.1f}x"

def safe_parse_date(date_string: str) -> Optional[dt]:
    """Parse date string as UTC and convert to Taipei timezone."""
    if not date_string or date_string.strip() in ['NOT_PROCESSED', 'NEVER', '']:
        return None
    
    try:
        # Handle various date formats
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S']:
            try:
                # FIXED: Parse as timezone-naive first
                parsed_dt = dt.strptime(date_string.strip(), fmt)
                
                # FIXED: Treat parsed datetime as UTC, then convert to Taipei
                if UTC_TZ and TAIPEI_TZ:
                    # Assign UTC timezone to the naive datetime
                    utc_dt = parsed_dt.replace(tzinfo=UTC_TZ)
                    # Convert UTC to Taipei timezone
                    taipei_dt = utc_dt.astimezone(TAIPEI_TZ)
                    return taipei_dt
                elif TAIPEI_TZ:
                    # Fallback: treat as naive and assign Taipei timezone
                    return parsed_dt.replace(tzinfo=TAIPEI_TZ)
                else:
                    return parsed_dt
                
            except ValueError:
                continue
        return None
    except Exception:
        return None

def analyze_csv(csv_path: str) -> Dict:
    """Analyze CSV file with UTC→Taipei timezone conversion."""
    # Get current time in Taipei timezone
    current_time = get_taipei_time()
    
    default_stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'updated_from_now': 'N/A',
        'oldest': 'N/A',
        'duration': 'N/A',
        'retry_rate': 'N/A',
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
            
            # FIXED: Time-based metrics - convert UTC timestamps to Taipei
            process_times = []
            update_times = []
            retry_counts = []
            
            for row in rows:
                # Process time (for Updated from now and Duration)
                # CSV contains UTC timestamps, convert to Taipei
                process_time = safe_parse_date(row['process_time'])
                if process_time:
                    process_times.append(process_time)
                
                # Last update time (for Oldest calculation)
                # CSV contains UTC timestamps, convert to Taipei
                update_time = safe_parse_date(row['last_update_time'])
                if update_time:
                    update_times.append(update_time)
                
                # Retry count (for Retry Rate calculation)
                try:
                    retry_count = int(row.get('retry_count', 0))
                    retry_counts.append(retry_count)
                except (ValueError, TypeError):
                    retry_counts.append(0)
            
            # Calculate Updated from now (most recent process_time)
            # Both times are now in Taipei timezone
            if process_times:
                last_process_time = max(process_times)
                time_diff = current_time - last_process_time
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
            # Both times are now in Taipei timezone
            if update_times:
                oldest_update_time = min(update_times)
                time_diff = current_time - oldest_update_time
                stats['oldest'] = format_time_compact(time_diff)
            else:
                stats['oldest'] = 'Never'
            
            # Calculate Retry Rate
            stats['retry_rate'] = calculate_retry_rate(retry_counts)
            
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
                'RetryRate': 'N/A',
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
                'RetryRate': csv_stats['retry_rate'],
                'error': csv_stats.get('error')
            }
        
        results.append(stats)
    
    return results

def format_table(results: List[Dict]) -> str:
    """Format results into enhanced 8-column badge-enhanced markdown table."""
    header = "| No | Folder | Total | Success | Failed | Updated from now | Oldest | Duration | Retry Rate |\n"
    header += "| -- | -- | -- | -- | -- | -- | -- | -- | -- |\n"

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
            oldest_color = get_time_badge_color(r["Oldest"])
            oldest = make_badge(r["Oldest"], oldest_color)
        else:
            oldest = "N/A"
            
        # Duration is always blue
        if r["Duration"] != "N/A":
            duration = make_badge(r["Duration"], "blue")
        else:
            duration = "N/A"
        
        # Retry Rate with reliability-based color coding
        if r["RetryRate"] != "N/A":
            retry_color = get_retry_badge_color(r["RetryRate"])
            retry_rate = make_badge(r["RetryRate"], retry_color)
        else:
            retry_rate = "N/A"

        rows.append(f"| {no} | {folder} | {total} | {success} | {failed} | {updated} | {oldest} | {duration} | {retry_rate} |")

    return header + "\n".join(rows)

def update_readme(table_text: str):
    """Update README.md status section with enhanced 8-column table."""
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

    # Generate current timestamp in Taiwan timezone (consistent with table calculations)
    current_time = get_taipei_time()
    if TAIPEI_TZ:
        update_time = current_time.strftime('%Y-%m-%d %H:%M:%S') + ' CST'
    else:
        update_time = current_time.strftime('%Y-%m-%d %H:%M:%S') + ' CST'

    # Create new status section with enhanced 8-column table
    new_status = f"## Status\n\nUpdate time: {update_time}\n\n{table_text}\n\n"
    
    # Replace the status section
    new_content = content[:status_start] + new_status + content[next_section:]

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md status section updated successfully with UTC→Taipei timezone conversion")

def analyze_high_retry_folders(results: List[Dict], threshold: float = 2.0) -> List[Dict]:
    """Identify folders with high retry rates that need attention."""
    high_retry_folders = []
    
    for r in results:
        retry_rate = r.get("RetryRate", "N/A")
        if retry_rate != "N/A" and "x" in retry_rate:
            try:
                rate = float(retry_rate.replace('x', ''))
                if rate > threshold:
                    high_retry_folders.append({
                        'folder': r["Folder"],
                        'retry_rate': retry_rate,
                        'rate_value': rate,
                        'total_files': r["Total"],
                        'success': r["Success"],
                        'failed': r["Failed"]
                    })
            except (ValueError, IndexError):
                continue
    
    return sorted(high_retry_folders, key=lambda x: x['rate_value'], reverse=True)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze GoodInfo download results with UTC→Taipei timezone conversion"
    )
    parser.add_argument("--update-readme", action="store_true", help="Update README.md status section with 8-column table")
    parser.add_argument("--show-oldest", action="store_true", help="Highlight folders with oldest data")
    parser.add_argument("--show-high-retry", action="store_true", help="Highlight folders with high retry rates")
    parser.add_argument("--retry-threshold", type=float, default=2.0, help="Threshold for high retry rate alerts (default: 2.0)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed retry rate statistics")
    args = parser.parse_args()

    print("Scanning download results with UTC→Taipei timezone conversion...")
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

    if args.show_high_retry:
        # Find and highlight folders with high retry rates
        high_retry_folders = analyze_high_retry_folders(results, args.retry_threshold)
        
        if high_retry_folders:
            print(f"\nHigh retry rate folders (>{args.retry_threshold}x threshold):")
            for folder_info in high_retry_folders:
                print(f"  - {folder_info['folder']}: {folder_info['retry_rate']} "
                      f"({folder_info['success']}/{folder_info['total_files']} successful)")
        else:
            print(f"\nNo folders detected with retry rates above {args.retry_threshold}x threshold.")

    if args.detailed:
        # Show detailed retry rate statistics
        print("\nDetailed Retry Rate Statistics:")
        total_folders = 0
        folders_with_data = 0
        retry_rates = []
        
        for r in results:
            total_folders += 1
            if r["RetryRate"] != "N/A" and "x" in r["RetryRate"]:
                folders_with_data += 1
                try:
                    rate = float(r["RetryRate"].replace('x', ''))
                    retry_rates.append(rate)
                except (ValueError, IndexError):
                    continue
        
        if retry_rates:
            avg_retry_rate = sum(retry_rates) / len(retry_rates)
            max_retry_rate = max(retry_rates)
            min_retry_rate = min(retry_rates)
            
            print(f"  - Folders analyzed: {folders_with_data}/{total_folders}")
            print(f"  - Average retry rate: {avg_retry_rate:.2f}x")
            print(f"  - Best retry rate: {min_retry_rate:.2f}x")
            print(f"  - Worst retry rate: {max_retry_rate:.2f}x")
            
            # Reliability categories
            excellent = sum(1 for r in retry_rates if r <= 1.5)
            good = sum(1 for r in retry_rates if 1.5 < r <= 2.0)
            poor = sum(1 for r in retry_rates if 2.0 < r <= 3.0)
            very_poor = sum(1 for r in retry_rates if r > 3.0)
            
            print(f"  - Reliability distribution:")
            print(f"    * Excellent (≤1.5x): {excellent} folders")
            print(f"    * Good (1.6-2.0x): {good} folders")
            print(f"    * Poor (2.1-3.0x): {poor} folders")
            print(f"    * Very Poor (>3.0x): {very_poor} folders")

    if args.update_readme:
        update_readme(table_text)

if __name__ == "__main__":
    main()