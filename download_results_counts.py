#!/usr/bin/env python3
"""
Enhanced Download Results Count Analyzer with Retry Rate Monitoring (v6.0.0)
ENHANCED: Complete 15 Data Types including Multi-Frequency Margin Balance for Long-Term Analysis
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

# Enhanced data type to folder mapping for complete 15 GoodInfo data types (v6.0.0)
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
    13: "ShowMarginChart",     # 🆕 NEW in v5.0.0 - Daily Margin Balance
    14: "ShowMarginChartWeek", # 🆕 NEW in v6.0.0 - Weekly Margin Balance
    15: "ShowMarginChartMonth" # 🆕 NEW in v6.0.0 - Monthly Margin Balance
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
        return 'blue'         # Hours ago
    elif '1d' in time_text:
        return 'yellow'       # 1 day ago
    elif '2d' in time_text or '3d' in time_text:
        return 'orange'       # 2-3 days ago
    elif 'd' in time_text:
        return 'red'          # > 3 days ago
    else:
        return 'blue'         # Default color

def get_retry_badge_color_enhanced(retry_display: str, data_type: int = None) -> str:
    """Enhanced retry rate color determination with Types 11-15 considerations."""
    if not retry_display or retry_display == 'N/A':
        return 'lightgrey'
    
    try:
        rate = float(retry_display.replace('x', ''))
        
        # Type 11 has more lenient thresholds due to institutional data complexity
        if data_type == 11:
            if rate <= 1.2:
                return 'brightgreen'  # Excellent for Type 11
            elif rate <= 1.8:
                return 'green'        # Good for Type 11
            elif rate <= 2.5:
                return 'yellow'       # Acceptable for Type 11
            elif rate <= 3.5:
                return 'orange'       # Poor for Type 11
            else:
                return 'red'          # Very poor for Type 11
        
        # Type 12 and 15 have moderate thresholds due to large dataset/aggregated processing
        elif data_type in [12, 15]:
            if rate <= 1.1:
                return 'brightgreen'  # Excellent for Type 12/15
            elif rate <= 1.6:
                return 'green'        # Good for Type 12/15
            elif rate <= 2.2:
                return 'yellow'       # Acceptable for Type 12/15
            elif rate <= 3.0:
                return 'orange'       # Poor for Type 12/15
            else:
                return 'red'          # Very poor for Type 12/15
        
        # Type 13 and 14 are standard, but daily/weekly margin balance. 
        # Use standard thresholds for now, but can be adjusted later if needed.
        elif data_type in [13, 14]:
            if rate <= 1.0:
                return 'brightgreen'  # Perfect reliability
            elif rate <= 1.5:
                return 'green'        # Excellent reliability
            elif rate <= 2.0:
                return 'yellow'       # Good reliability
            elif rate <= 3.0:
                return 'orange'       # Poor reliability
            else:
                return 'red'          # Very poor reliability
        
        else:
            # Standard thresholds for other types
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

def analyze_csv_enhanced(csv_path: str, data_type: int = None) -> Dict:
    """Enhanced CSV analysis with Types 11-15 considerations and UTC→Taipei timezone conversion."""
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
        'data_type': data_type,
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
                'data_type': data_type,
                'error': None
            }
            
            # ENHANCED: Time-based metrics - convert UTC timestamps to Taipei
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
            
            # Enhanced: Calculate Retry Rate with Types 11 & 12 considerations
            stats['retry_rate'] = calculate_retry_rate(retry_counts)
            
            # Type-specific metrics (ENHANCED for Types 11-15)
            if data_type == 11:
                stats['type_11_complexity'] = 'institutional_flows'
            elif data_type in [12, 15]: # Type 12 and Type 15 (Monthly Margin) are large datasets
                stats['type_complexity'] = 'large_dataset'
                stats['historical_coverage'] = '20_year'
            elif data_type in [13, 14]: # Type 13 (Daily Margin) and Type 14 (Weekly Margin) are standard
                stats['type_complexity'] = 'standard_margin'
            
            return stats
            
    except Exception as e:
        default_stats['error'] = f"Error reading file: {str(e)}"
        return default_stats

def scan_all_folders() -> List[Dict]:
    """Scan all 15 data type folders and analyze their CSV files."""
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
            # Analyze CSV file with data type context
            csv_stats = analyze_csv_enhanced(csv_path, data_type)
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
                'error': csv_stats.get('error'),
                'data_type': data_type
            }
        
        results.append(stats)
    
    return results

def format_table_enhanced(results: List[Dict]) -> str:
    """Format results into enhanced 8-column badge-enhanced markdown table with Types 11 & 12 support."""
    header = "| No | Folder | Total | Success | Failed | Updated from now | Oldest | Duration | Retry Rate |\n"
    header += "| -- | -- | -- | -- | -- | -- | -- | -- | -- |\n"

    rows = []
    for r in results:
        no = r["No"]
        folder = r["Folder"]
        data_type = r.get("data_type", no)

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
        
        # Enhanced: Retry Rate with Types 11 & 12 considerations
        if r["RetryRate"] != "N/A":
            retry_color = get_retry_badge_color_enhanced(r["RetryRate"], data_type)
            retry_rate = make_badge(r["RetryRate"], retry_color)
        else:
            retry_rate = "N/A"

        rows.append(f"| {no} | {folder} | {total} | {success} | {failed} | {updated} | {oldest} | {duration} | {retry_rate} |")

    return header + "\n".join(rows)

def update_readme_enhanced(table_text: str):
    """Update README.md status section with enhanced 8-column table supporting all 15 data types."""
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

    # Create new status section with enhanced 8-column table for all 15 data types
    new_status = f"## Status\n\nUpdate time: {update_time}\n\n{table_text}\n\n"
    
    # Replace the status section
    new_content = content[:status_start] + new_status + content[next_section:]

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md status section updated successfully with complete 15 data types support (UTC→Taipei timezone conversion)")

def analyze_high_retry_folders_enhanced(results: List[Dict], threshold: float = 2.0) -> List[Dict]:
    """Enhanced analysis to identify folders with high retry rates, with Types 11-15 considerations."""
    high_retry_folders = []
    
    for r in results:
        retry_rate = r.get("RetryRate", "N/A")
        data_type = r.get("data_type", r["No"])
        
        if retry_rate != "N/A" and "x" in retry_rate:
            try:
                rate = float(retry_rate.replace('x', ''))
                
                # Enhanced threshold logic for Types 11 & 12
                effective_threshold = threshold
                if data_type == 11:
                    effective_threshold = max(threshold, 2.5)  # More lenient for Type 11
                elif data_type == 12:
                    effective_threshold = max(threshold, 2.2)  # Moderate for Type 12
                
                if rate > effective_threshold:
                    high_retry_folders.append({
                        'folder': r["Folder"],
                        'retry_rate': retry_rate,
                        'rate_value': rate,
                        'total_files': r["Total"],
                        'success': r["Success"],
                        'failed': r["Failed"],
                        'data_type': data_type,
                        'threshold_used': effective_threshold
                    })
            except (ValueError, IndexError):
                continue
    
    return sorted(high_retry_folders, key=lambda x: x['rate_value'], reverse=True)

def analyze_type_11_health(results: List[Dict]) -> Dict:
    """Analyze Type 11 (Weekly Trading Data) specific health metrics."""
    type_11_data = None
    
    for r in results:
        if r.get("data_type") == 11 or r["No"] == 11:
            type_11_data = r
            break
    
    if not type_11_data:
        return {"status": "not_found", "message": "Type 11 data not available"}
    
    health_analysis = {
        "status": "available",
        "folder": type_11_data["Folder"],
        "total_files": type_11_data["Total"],
        "success_rate": 0,
        "retry_rate": type_11_data["RetryRate"],
        "institutional_data_health": "unknown",
        "recommendations": []
    }
    
    # Calculate success rate
    if type_11_data["Total"] > 0:
        health_analysis["success_rate"] = (type_11_data["Success"] / type_11_data["Total"]) * 100
    
    # Analyze institutional data health based on retry rate
    retry_rate_str = type_11_data["RetryRate"]
    if retry_rate_str != "N/A" and "x" in retry_rate_str:
        try:
            retry_rate_val = float(retry_rate_str.replace('x', ''))
            
            if retry_rate_val <= 1.5:
                health_analysis["institutional_data_health"] = "excellent"
            elif retry_rate_val <= 2.0:
                health_analysis["institutional_data_health"] = "good"
            elif retry_rate_val <= 2.5:
                health_analysis["institutional_data_health"] = "acceptable"
            elif retry_rate_val <= 3.5:
                health_analysis["institutional_data_health"] = "concerning"
                health_analysis["recommendations"].append("Monitor institutional data source stability")
            else:
                health_analysis["institutional_data_health"] = "poor"
                health_analysis["recommendations"].append("Investigate institutional data source issues")
                health_analysis["recommendations"].append("Consider adjusting download timeout settings")
        except (ValueError, IndexError):
            health_analysis["institutional_data_health"] = "unknown"
    
    # Add success rate recommendations
    if health_analysis["success_rate"] < 90:
        health_analysis["recommendations"].append("Review download process for institutional data complexity")
    
    if health_analysis["success_rate"] < 80:
        health_analysis["recommendations"].append("Consider Type 11 specific error handling improvements")
    
    return health_analysis

def analyze_type_12_15_health(results: List[Dict]) -> Dict:
    """Analyze Type 12 (EPS x PER Monthly) and Type 15 (Monthly Margin Balance) specific health metrics."""
    type_12_data = None
    type_15_data = None
    
    for r in results:
        if r.get("data_type") == 12 or r["No"] == 12:
            type_12_data = r
        elif r.get("data_type") == 15 or r["No"] == 15:
            type_15_data = r
    
    # Prioritize Type 12 if available, otherwise Type 15
    target_data = type_12_data if type_12_data else type_15_data
    target_type = 12 if type_12_data else 15

    if not target_data:
        return {"status": "not_found", "message": f"Type 12/15 data not available"}
    
    health_analysis = {
        "status": "available",
        "folder": target_data["Folder"],
        "total_files": target_data["Total"],
        "success_rate": 0,
        "retry_rate": target_data["RetryRate"],
        "valuation_data_health": "unknown",
        "recommendations": []
    }
    
    # Calculate success rate
    if target_data["Total"] > 0:
        health_analysis["success_rate"] = (target_data["Success"] / target_data["Total"]) * 100
    
    # Analyze valuation/margin data health based on retry rate
    retry_rate_str = target_data["RetryRate"]
    if retry_rate_str != "N/A" and "x" in retry_rate_str:
        try:
            retry_rate_val = float(retry_rate_str.replace('x', ''))
            
            if retry_rate_val <= 1.3:
                health_analysis["valuation_data_health"] = "excellent"
            elif retry_rate_val <= 1.8:
                health_analysis["valuation_data_health"] = "good"
            elif retry_rate_val <= 2.2:
                health_analysis["valuation_data_health"] = "acceptable"
            elif retry_rate_val <= 3.0:
                health_analysis["valuation_data_health"] = "concerning"
                health_analysis["recommendations"].append("Monitor large dataset processing stability")
            else:
                health_analysis["valuation_data_health"] = "poor"
                health_analysis["recommendations"].append("Investigate 20-year dataset download issues")
                health_analysis["recommendations"].append("Consider adjusting timeout settings for large datasets")
        except (ValueError, IndexError):
            health_analysis["valuation_data_health"] = "unknown"
    
    # Add success rate recommendations
    if health_analysis["success_rate"] < 90:
        health_analysis["recommendations"].append("Review download process for large dataset complexity")
    
    if health_analysis["success_rate"] < 80:
        health_analysis["recommendations"].append("Consider Type 12/15 specific error handling improvements")
        health_analysis["recommendations"].append("Verify 20-year monthly data processing capability")
    
    return health_analysis

def analyze_type_13_14_health(results: List[Dict]) -> Dict:
    """Analyze Type 13 (Daily Margin Balance) and Type 14 (Weekly Margin Balance) specific health metrics."""
    type_13_data = None
    type_14_data = None

    for r in results:
        if r.get("data_type") == 13 or r["No"] == 13:
            type_13_data = r
        elif r.get("data_type") == 14 or r["No"] == 14:
            type_14_data = r

    # Prioritize Type 13 if available, otherwise Type 14
    target_data = type_13_data if type_13_data else type_14_data
    target_type = 13 if type_13_data else 14

    if not target_data:
        return {"status": "not_found", "message": f"Type 13/14 data not available"}
    
    health_analysis = {
        "status": "available",
        "folder": target_data["Folder"],
        "total_files": target_data["Total"],
        "success_rate": 0,
        "retry_rate": target_data["RetryRate"],
        "sentiment_data_health": "unknown",
        "recommendations": []
    }
    
    if target_data["Total"] > 0:
        health_analysis["success_rate"] = (target_data["Success"] / target_data["Total"]) * 100
    
    retry_rate_str = target_data["RetryRate"]
    if retry_rate_str != "N/A" and "x" in retry_rate_str:
        try:
            retry_rate_val = float(retry_rate_str.replace('x', ''))
            if retry_rate_val <= 1.2:
                health_analysis["sentiment_data_health"] = "excellent"
            elif retry_rate_val <= 1.8:
                health_analysis["sentiment_data_health"] = "good"
            elif retry_rate_val <= 2.5:
                health_analysis["sentiment_data_health"] = "acceptable"
            else:
                health_analysis["sentiment_data_health"] = "concerning"
                health_analysis["recommendations"].append("Monitor margin data source stability")
        except (ValueError, IndexError):
            health_analysis["sentiment_data_health"] = "unknown"
    
    if health_analysis["success_rate"] < 90:
        health_analysis["recommendations"].append("Review download process for margin data")
    
    return health_analysis

def analyze_multi_timeframe_consistency(results: List[Dict]) -> Dict:
    """Analyze consistency between Type 8 (weekly) & Type 12 (monthly) P/E and Type 13/14/15 margin data."""
    type_8_data = None
    type_12_data = None
    type_13_data = None
    type_14_data = None
    type_15_data = None
    
    for r in results:
        if r.get("data_type") == 8 or r["No"] == 8:
            type_8_data = r
        elif r.get("data_type") == 12 or r["No"] == 12:
            type_12_data = r
        elif r.get("data_type") == 13 or r["No"] == 13:
            type_13_data = r
        elif r.get("data_type") == 14 or r["No"] == 14:
            type_14_data = r
        elif r.get("data_type") == 15 or r["No"] == 15:
            type_15_data = r
    
    analysis = {
        "status": "incomplete",
        "pe_consistency": "unknown",
        "margin_consistency": "unknown",
        "recommendations": []
    }
    
    # --- P/E Consistency (Type 8 vs Type 12) ---
    pe_comparison = {"type_8_available": type_8_data is not None, "type_12_available": type_12_data is not None}
    
    if not type_8_data:
        analysis["recommendations"].append("Type 8 (weekly P/E) data not available for P/E comparison")
    if not type_12_data:
        analysis["recommendations"].append("Type 12 (monthly P/E) data not available for P/E comparison")
    
    if type_8_data and type_12_data:
        type_8_success_rate = (type_8_data["Success"] / type_8_data["Total"]) * 100 if type_8_data["Total"] > 0 else 0
        type_12_success_rate = (type_12_data["Success"] / type_12_data["Total"]) * 100 if type_12_data["Total"] > 0 else 0
        success_diff = abs(type_8_success_rate - type_12_success_rate)
        
        if success_diff <= 5:
            analysis["pe_consistency"] = "excellent"
        elif success_diff <= 10:
            analysis["pe_consistency"] = "good"
        else:
            analysis["pe_consistency"] = "poor"
            analysis["recommendations"].append("Significant discrepancy between weekly and monthly P/E success rates")
    
    # --- Margin Consistency (Type 13 vs Type 14 vs Type 15) ---
    margin_comparison = {
        "type_13_available": type_13_data is not None,
        "type_14_available": type_14_data is not None,
        "type_15_available": type_15_data is not None
    }

    if not type_13_data:
        analysis["recommendations"].append("Type 13 (daily margin) data not available for margin comparison")
    if not type_14_data:
        analysis["recommendations"].append("Type 14 (weekly margin) data not available for margin comparison")
    if not type_15_data:
        analysis["recommendations"].append("Type 15 (monthly margin) data not available for margin comparison")

    if type_13_data and type_14_data and type_15_data:
        # Simple check: if all are successful, consider consistent
        if type_13_data["Success"] > 0 and type_14_data["Success"] > 0 and type_15_data["Success"] > 0:
            analysis["margin_consistency"] = "excellent"
        else:
            analysis["margin_consistency"] = "mixed"
            analysis["recommendations"].append("Check success rates for daily/weekly/monthly margin data")
    elif (type_13_data and type_14_data) or (type_13_data and type_15_data) or (type_14_data and type_15_data):
        analysis["margin_consistency"] = "partial"
        analysis["recommendations"].append("Only partial margin data available for consistency check")
    
    analysis["status"] = "complete" # Mark as complete even if some types are missing for comparison
    return analysis

def main():
    """Enhanced main entry point with complete 15 data types support."""
    parser = argparse.ArgumentParser(
        description="Analyze GoodInfo download results for all 15 data types with UTC→Taipei timezone conversion"
    )
    parser.add_argument("--update-readme", action="store_true", help="Update README.md status section with 8-column table")
    parser.add_argument("--show-oldest", action="store_true", help="Highlight folders with oldest data")
    parser.add_argument("--show-high-retry", action="store_true", help="Highlight folders with high retry rates")
    parser.add_argument("--retry-threshold", type=float, default=2.0, help="Threshold for high retry rate alerts (default: 2.0, Type 11: 2.5, Type 12/15: 2.2, Type 13/14: 2.0)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed retry rate statistics")
    parser.add_argument("--type-11-focus", action="store_true", help="Show detailed Type 11 institutional data analysis")
    parser.add_argument("--type-12-focus", action="store_true", help="Show detailed Type 12 long-term P/E analysis")
    parser.add_argument("--institutional-health", action="store_true", help="Show Type 11 institutional data source health")
    parser.add_argument("--valuation-health", action="store_true", help="Show Type 12 valuation data consistency analysis")
    parser.add_argument("--sentiment-health", action="store_true", help="Show Type 13/14/15 sentiment data availability")
    parser.add_argument("--multi-timeframe", action="store_true", help="Compare Types 8 & 12 for P/E analysis consistency")
    parser.add_argument("--type-13-focus", action="store_true", help="Show detailed Type 13 daily margin analysis")
    parser.add_argument("--type-14-focus", action="store_true", help="Show detailed Type 14 weekly margin analysis")
    parser.add_argument("--type-15-focus", action="store_true", help="Show detailed Type 15 monthly margin analysis")
    args = parser.parse_args()

    print("Scanning download results for all 15 data types with UTC→Taipei timezone conversion...")
    results = scan_all_folders()
    table_text = format_table_enhanced(results)

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
        # Enhanced analysis with Types 11 & 12 considerations
        high_retry_folders = analyze_high_retry_folders_enhanced(results, args.retry_threshold)
        
        if high_retry_folders:
            print(f"\nHigh retry rate folders (adjusted for Types 11-15 complexity):")
            for folder_info in high_retry_folders:
                threshold_note = ""
                if folder_info['data_type'] == 11:
                    threshold_note = " (Type 11 - institutional data complexity)"
                elif folder_info['data_type'] in [12, 15]:
                    threshold_note = " (Type 12/15 - large dataset/aggregated processing)"
                elif folder_info['data_type'] in [13, 14]:
                    threshold_note = " (Type 13/14 - standard margin data)"
                
                print(f"  - {folder_info['folder']}: {folder_info['retry_rate']} "
                      f"({folder_info['success']}/{folder_info['total_files']} successful){threshold_note}")
        else:
            print(f"\nNo folders detected with retry rates above threshold (adjusted for Types 11 & 12 complexity).")

    if args.detailed:
        # Enhanced detailed statistics including Types 11-15
        print("\nDetailed Retry Rate Statistics (15 Data Types):")
        total_folders = 0
        folders_with_data = 0
        retry_rates = []
        type_11_found = False
        type_12_found = False
        
        for r in results:
            total_folders += 1
            if r["RetryRate"] != "N/A" and "x" in r["RetryRate"]:
                folders_with_data += 1
                try:
                    rate = float(r["RetryRate"].replace('x', ''))
                    retry_rates.append(rate)
                    if r.get("data_type") == 11 or r["No"] == 11:
                        type_11_found = True
                        print(f"  - Type 11 (WeeklyTradingData): {r['RetryRate']} - Institutional flows complexity")
                    elif r.get("data_type") == 12 or r["No"] == 12:
                        type_12_found = True
                        print(f"  - Type 12 (ShowMonthlyK_ChartFlow): {r['RetryRate']} - 20-year dataset processing")
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
            
            # Enhanced reliability categories with Types 11 & 12 considerations
            excellent = sum(1 for r in retry_rates if r <= 1.5)
            good = sum(1 for r in retry_rates if 1.5 < r <= 2.0)
            poor = sum(1 for r in retry_rates if 2.0 < r <= 3.0)
            very_poor = sum(1 for r in retry_rates if r > 3.0)
            
            print(f"  - Reliability distribution:")
            print(f"    * Excellent (≤1.5x): {excellent} folders")
            print(f"    * Good (1.6-2.0x): {good} folders")
            print(f"    * Poor (2.1-3.0x): {poor} folders")
            print(f"    * Very Poor (>3.0x): {very_poor} folders")
            
            if type_11_found:
                print(f"  - Type 11 uses enhanced thresholds due to institutional data complexity")
            if type_12_found:
                print(f"  - Type 12 uses moderate thresholds due to large dataset processing")

    if args.type_13_focus:
        type_13_health = analyze_type_13_14_health(results)
        print(f"\nType 13 (Daily Margin Balance) Health Analysis:")
        if type_13_health["status"] == "not_found":
            print(f"  - {type_13_health['message']}")
        else:
            print(f"  - Folder: {type_13_health['folder']}")
            print(f"  - Total files: {type_13_health['total_files']}")
            print(f"  - Success rate: {type_13_health['success_rate']:.1f}%")
            print(f"  - Retry rate: {type_13_health['retry_rate']}")
            print(f"  - Sentiment data health: {type_13_health['sentiment_data_health']}")
            if type_13_health['recommendations']:
                print(f"  - Recommendations:")
                for rec in type_13_health['recommendations']:
                    print(f"    * {rec}")

    if args.type_14_focus:
        type_14_health = analyze_type_13_14_health(results) # Re-use for Type 14 logic, will check for Type 14 data
        print(f"\nType 14 (Weekly Margin Balance) Health Analysis:")
        if type_14_health["status"] == "not_found":
            print(f"  - {type_14_health['message']}")
        else:
            print(f"  - Folder: {type_14_health['folder']}")
            print(f"  - Total files: {type_14_health['total_files']}")
            print(f"  - Success rate: {type_14_health['success_rate']:.1f}%")
            print(f"  - Retry rate: {type_14_health['retry_rate']}")
            print(f"  - Sentiment data health: {type_14_health['sentiment_data_health']}")
            if type_14_health['recommendations']:
                print(f"  - Recommendations:")
                for rec in type_14_health['recommendations']:
                    print(f"    * {rec}")
    
    if args.type_15_focus:
        type_15_health = analyze_type_12_15_health(results) # Re-use for Type 15 logic, will check for Type 15 data
        print(f"\nType 15 (Monthly Margin Balance) Health Analysis:")
        if type_15_health["status"] == "not_found":
            print(f"  - {type_15_health['message']}")
        else:
            print(f"  - Folder: {type_15_health['folder']}")
            print(f"  - Total files: {type_15_health['total_files']}")
            print(f"  - Success rate: {type_15_health['success_rate']:.1f}%")
            print(f"  - Retry rate: {type_15_health['retry_rate']}")
            print(f"  - Valuation data health: {type_15_health['valuation_data_health']}")
            if type_15_health['recommendations']:
                print(f"  - Recommendations:")
                for rec in type_15_health['recommendations']:
                    print(f"    * {rec}")

    if args.institutional_health:
        # Type 11 specific analysis
        type_11_health = analyze_type_11_health(results)
        
        print(f"\nType 11 (Weekly Trading Data) Health Analysis:")
        if type_11_health["status"] == "not_found":
            print(f"  - {type_11_health['message']}")
        else:
            print(f"  - Folder: {type_11_health['folder']}")
            print(f"  - Total files: {type_11_health['total_files']}")
            print(f"  - Success rate: {type_11_health['success_rate']:.1f}%")
            print(f"  - Retry rate: {type_11_health['retry_rate']}")
            print(f"  - Institutional data health: {type_11_health['institutional_data_health']}")
            
            if type_11_health['recommendations']:
                print(f"  - Recommendations:")
                for rec in type_11_health['recommendations']:
                    print(f"    * {rec}")

    if args.type_12_focus or args.valuation_health:
        # Type 12 and Type 15 specific analysis
        type_12_15_health = analyze_type_12_15_health(results)
        
        print(f"\nType 12/15 (EPS x PER Monthly / Monthly Margin Balance) Health Analysis:")
        if type_12_15_health["status"] == "not_found":
            print(f"  - {type_12_15_health['message']}")
        else:
            print(f"  - Folder: {type_12_15_health['folder']}")
            print(f"  - Total files: {type_12_15_health['total_files']}")
            print(f"  - Success rate: {type_12_15_health['success_rate']:.1f}%")
            print(f"  - Retry rate: {type_12_15_health['retry_rate']}")
            print(f"  - Valuation/Margin data health: {type_12_15_health['valuation_data_health']}")
            
            if type_12_15_health['recommendations']:
                print(f"  - Recommendations:")
                for rec in type_12_15_health['recommendations']:
                    print(f"    * {rec}")

    if args.sentiment_health:
        type_13_14_15_health = analyze_type_13_14_health(results) # Assuming a combined function
        
        print(f"\nType 13/14/15 (Daily/Weekly/Monthly Margin Balance) Health Analysis:")
        if type_13_14_15_health["status"] == "not_found":
            print(f"  - {type_13_14_15_health['message']}")
        else:
            print(f"  - Folder: {type_13_14_15_health['folder']}")
            print(f"  - Total files: {type_13_14_15_health['total_files']}")
            print(f"  - Success rate: {type_13_14_15_health['success_rate']:.1f}%")
            print(f"  - Retry rate: {type_13_14_15_health['retry_rate']}")
            print(f"  - Sentiment data health: {type_13_14_15_health['sentiment_data_health']}")
            
            if type_13_14_15_health['recommendations']:
                print(f"  - Recommendations:")
                for rec in type_13_14_15_health['recommendations']:
                    print(f"    * {rec}")

    if args.multi_timeframe:
        # Multi-timeframe P/E and Margin analysis consistency
        consistency_analysis = analyze_multi_timeframe_consistency(results)
        
        print(f"\nMulti-Timeframe P/E and Margin Analysis Consistency:")
        print(f"  - Overall Status: {consistency_analysis['status']}")
        
        if consistency_analysis['pe_consistency'] != "unknown":
            print(f"  - P/E Consistency (Types 8 & 12): {consistency_analysis['pe_consistency']}")
        if consistency_analysis['margin_consistency'] != "unknown":
            print(f"  - Margin Consistency (Types 13/14/15): {consistency_analysis['margin_consistency']}")
        
        if consistency_analysis['recommendations']:
            print(f"  - Recommendations:")
            for rec in consistency_analysis['recommendations']:
                print(f"    * {rec}")

    if args.update_readme:
        update_readme_enhanced(table_text)

if __name__ == "__main__":
    main()