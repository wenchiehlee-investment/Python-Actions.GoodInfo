#!/usr/bin/env python3
"""
Enhanced Download Results Count Analyzer with Retry Rate Monitoring (v4.0.0)
ENHANCED: Complete 12 Data Types including EPS x PER Monthly for Long-Term Analysis
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

# Enhanced data type to folder mapping for complete 12 GoodInfo data types (v4.0.0)
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
    12: "ShowMonthlyK_ChartFlow"  # 🆕 NEW in v4.0.0 - EPS x PER Monthly for Long-Term Analysis
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
    """Enhanced retry rate color determination with Types 11 & 12 considerations."""
    if not retry_display or retry_display == 'N/A':
        return 'lightgrey'
    
    # Extract numeric value from display (e.g., "2.3x" -> 2.3)
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
        
        # Type 12 has moderate thresholds due to large dataset processing
        elif data_type == 12:
            if rate <= 1.1:
                return 'brightgreen'  # Excellent for Type 12
            elif rate <= 1.6:
                return 'green'        # Good for Type 12
            elif rate <= 2.2:
                return 'yellow'       # Acceptable for Type 12
            elif rate <= 3.0:
                return 'orange'       # Poor for Type 12
            else:
                return 'red'          # Very poor for Type 12
        
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
    """Enhanced CSV analysis with Types 11 & 12 considerations and UTC→Taipei timezone conversion."""
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
            
            # Type-specific metrics
            if data_type == 11:
                stats['type_11_complexity'] = 'institutional_flows'
                # Additional Type 11 monitoring can be added here
            elif data_type == 12:
                stats['type_12_complexity'] = 'long_term_pe_analysis'
                stats['dataset_size'] = 'large_20_year'
                # Additional Type 12 monitoring can be added here
            
            return stats
            
    except Exception as e:
        default_stats['error'] = f"Error reading file: {str(e)}"
        return default_stats

def scan_all_folders() -> List[Dict]:
    """Scan all 12 data type folders and analyze their CSV files."""
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
    """Update README.md status section with enhanced 8-column table supporting all 12 data types."""
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

    # Create new status section with enhanced 8-column table for all 12 data types
    new_status = f"## Status\n\nUpdate time: {update_time}\n\n{table_text}\n\n"
    
    # Replace the status section
    new_content = content[:status_start] + new_status + content[next_section:]

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md status section updated successfully with complete 12 data types support (UTC→Taipei timezone conversion)")

def analyze_high_retry_folders_enhanced(results: List[Dict], threshold: float = 2.0) -> List[Dict]:
    """Enhanced analysis to identify folders with high retry rates, with Types 11 & 12 considerations."""
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

def analyze_type_12_health(results: List[Dict]) -> Dict:
    """Analyze Type 12 (EPS x PER Monthly) specific health metrics."""
    type_12_data = None
    
    for r in results:
        if r.get("data_type") == 12 or r["No"] == 12:
            type_12_data = r
            break
    
    if not type_12_data:
        return {"status": "not_found", "message": "Type 12 data not available"}
    
    health_analysis = {
        "status": "available",
        "folder": type_12_data["Folder"],
        "total_files": type_12_data["Total"],
        "success_rate": 0,
        "retry_rate": type_12_data["RetryRate"],
        "valuation_data_health": "unknown",
        "recommendations": []
    }
    
    # Calculate success rate
    if type_12_data["Total"] > 0:
        health_analysis["success_rate"] = (type_12_data["Success"] / type_12_data["Total"]) * 100
    
    # Analyze valuation data health based on retry rate
    retry_rate_str = type_12_data["RetryRate"]
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
        health_analysis["recommendations"].append("Consider Type 12 specific error handling improvements")
        health_analysis["recommendations"].append("Verify 20-year monthly P/E data processing capability")
    
    return health_analysis

def analyze_multi_timeframe_consistency(results: List[Dict]) -> Dict:
    """Analyze consistency between Type 8 (weekly) and Type 12 (monthly) P/E data."""
    type_8_data = None
    type_12_data = None
    
    for r in results:
        if r.get("data_type") == 8 or r["No"] == 8:
            type_8_data = r
        elif r.get("data_type") == 12 or r["No"] == 12:
            type_12_data = r
    
    analysis = {
        "status": "incomplete",
        "type_8_available": type_8_data is not None,
        "type_12_available": type_12_data is not None,
        "consistency_score": "unknown",
        "recommendations": []
    }
    
    if not type_8_data:
        analysis["recommendations"].append("Type 8 (weekly P/E) data not available for comparison")
    
    if not type_12_data:
        analysis["recommendations"].append("Type 12 (monthly P/E) data not available for comparison")
    
    if type_8_data and type_12_data:
        analysis["status"] = "available"
        
        # Compare success rates
        type_8_success_rate = (type_8_data["Success"] / type_8_data["Total"]) * 100 if type_8_data["Total"] > 0 else 0
        type_12_success_rate = (type_12_data["Success"] / type_12_data["Total"]) * 100 if type_12_data["Total"] > 0 else 0
        
        # Compare retry rates
        type_8_retry = type_8_data["RetryRate"]
        type_12_retry = type_12_data["RetryRate"]
        
        analysis["type_8_success_rate"] = type_8_success_rate
        analysis["type_12_success_rate"] = type_12_success_rate
        analysis["type_8_retry_rate"] = type_8_retry
        analysis["type_12_retry_rate"] = type_12_retry
        
        # Determine consistency
        success_diff = abs(type_8_success_rate - type_12_success_rate)
        
        if success_diff <= 5:
            analysis["consistency_score"] = "excellent"
        elif success_diff <= 10:
            analysis["consistency_score"] = "good"
        elif success_diff <= 20:
            analysis["consistency_score"] = "moderate"
            analysis["recommendations"].append("Investigate differences between weekly and monthly P/E processing")
        else:
            analysis["consistency_score"] = "poor"
            analysis["recommendations"].append("Significant discrepancy between Type 8 and Type 12 success rates")
            analysis["recommendations"].append("Review processing differences between 5-year and 20-year datasets")
    
    return analysis

def main():
    """Enhanced main entry point with complete 12 data types support."""
    parser = argparse.ArgumentParser(
        description="Analyze GoodInfo download results for all 12 data types with UTC→Taipei timezone conversion"
    )
    parser.add_argument("--update-readme", action="store_true", help="Update README.md status section with 8-column table")
    parser.add_argument("--show-oldest", action="store_true", help="Highlight folders with oldest data")
    parser.add_argument("--show-high-retry", action="store_true", help="Highlight folders with high retry rates")
    parser.add_argument("--retry-threshold", type=float, default=2.0, help="Threshold for high retry rate alerts (default: 2.0, Type 11: 2.5, Type 12: 2.2)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed retry rate statistics")
    parser.add_argument("--type-11-focus", action="store_true", help="Show detailed Type 11 institutional data analysis")
    parser.add_argument("--type-12-focus", action="store_true", help="Show detailed Type 12 long-term P/E analysis")
    parser.add_argument("--institutional-health", action="store_true", help="Show Type 11 institutional data source health")
    parser.add_argument("--valuation-health", action="store_true", help="Show Type 12 valuation data consistency analysis")
    parser.add_argument("--multi-timeframe", action="store_true", help="Compare Types 8 & 12 for P/E analysis consistency")
    args = parser.parse_args()

    print("Scanning download results for all 12 data types with UTC→Taipei timezone conversion...")
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
            print(f"\nHigh retry rate folders (Type 11 threshold: ≥2.5x, Type 12 threshold: ≥2.2x):")
            for folder_info in high_retry_folders:
                threshold_note = ""
                if folder_info['data_type'] == 11:
                    threshold_note = " (Type 11 - institutional data complexity)"
                elif folder_info['data_type'] == 12:
                    threshold_note = " (Type 12 - large dataset processing)"
                
                print(f"  - {folder_info['folder']}: {folder_info['retry_rate']} "
                      f"({folder_info['success']}/{folder_info['total_files']} successful){threshold_note}")
        else:
            print(f"\nNo folders detected with retry rates above threshold (adjusted for Types 11 & 12 complexity).")

    if args.detailed:
        # Enhanced detailed statistics including Types 11 & 12
        print("\nDetailed Retry Rate Statistics (12 Data Types):")
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

    if args.type_11_focus or args.institutional_health:
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
        # Type 12 specific analysis
        type_12_health = analyze_type_12_health(results)
        
        print(f"\nType 12 (EPS x PER Monthly) Health Analysis:")
        if type_12_health["status"] == "not_found":
            print(f"  - {type_12_health['message']}")
        else:
            print(f"  - Folder: {type_12_health['folder']}")
            print(f"  - Total files: {type_12_health['total_files']}")
            print(f"  - Success rate: {type_12_health['success_rate']:.1f}%")
            print(f"  - Retry rate: {type_12_health['retry_rate']}")
            print(f"  - Valuation data health: {type_12_health['valuation_data_health']}")
            
            if type_12_health['recommendations']:
                print(f"  - Recommendations:")
                for rec in type_12_health['recommendations']:
                    print(f"    * {rec}")

    if args.multi_timeframe:
        # Multi-timeframe P/E analysis consistency
        consistency_analysis = analyze_multi_timeframe_consistency(results)
        
        print(f"\nMulti-Timeframe P/E Analysis Consistency (Types 8 & 12):")
        print(f"  - Status: {consistency_analysis['status']}")
        print(f"  - Type 8 available: {consistency_analysis['type_8_available']}")
        print(f"  - Type 12 available: {consistency_analysis['type_12_available']}")
        
        if consistency_analysis['status'] == 'available':
            print(f"  - Type 8 success rate: {consistency_analysis['type_8_success_rate']:.1f}%")
            print(f"  - Type 12 success rate: {consistency_analysis['type_12_success_rate']:.1f}%")
            print(f"  - Type 8 retry rate: {consistency_analysis['type_8_retry_rate']}")
            print(f"  - Type 12 retry rate: {consistency_analysis['type_12_retry_rate']}")
            print(f"  - Consistency score: {consistency_analysis['consistency_score']}")
        
        if consistency_analysis['recommendations']:
            print(f"  - Recommendations:")
            for rec in consistency_analysis['recommendations']:
                print(f"    * {rec}")

    if args.update_readme:
        update_readme_enhanced(table_text)

if __name__ == "__main__":
    main()