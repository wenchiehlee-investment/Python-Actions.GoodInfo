# Download Results Count Analyzer - Design Document (v2.0.0)

## Project Overview
Create a Python script `download_results_counts.py` that analyzes download status across all 10 GoodInfo data types by scanning `download_results.csv` files and generating comprehensive status reports with **enhanced visual badge presentation**, **concise time formats**, and **retry rate monitoring**.

## Purpose
Provide automated monitoring and reporting for the GoodInfo data downloader system, enabling quick assessment of download progress, success rates, timing, and **reliability metrics** across all data types with **enhanced visual presentation using shields.io badges**, **compact time display formats**, and **retry rate analysis**.

## Core Requirements

### Input Analysis
- **Scan Strategy**: Automatically discover `download_results.csv` files in predefined data type folders
- **CSV Format**: Parse standard tracking format with columns: `filename,last_update_time,success,process_time,retry_count`
- **Data Types**: Support all 10 GoodInfo data types with their corresponding folders
- **Retry Analysis**: Calculate retry rate metrics for reliability monitoring

### Output Generation
- **Enhanced 8-Column Markdown Table**: Generate status table with shields.io badges, compact time formats, and retry rate monitoring
- **Real-time Metrics**: Calculate current statistics including time differences with compact notation
- **Status Tracking**: Provide comprehensive overview of download health with color-coded visual indicators
- **Reliability Monitoring**: Track retry rates to identify problematic data types requiring attention
- **Oldest Tracking**: Track the oldest update time across all entries for staleness detection

## Data Type Mapping (v2.0.0)

| No | Folder | Description | Automation Schedule |
|----|--------|-------------|-------------------|
| 1 | DividendDetail | Dividend Policy | Weekly (Monday) |
| 2 | BasicInfo | Basic Info | Manual Only |
| 3 | StockDetail | Stock Details | Manual Only |
| 4 | StockBzPerformance | Business Performance | Weekly (Tuesday) |
| 5 | ShowSaleMonChart | Monthly Revenue | Daily |
| 6 | EquityDistribution | Equity Distribution | Weekly (Wednesday) |
| 7 | StockBzPerformance1 | Quarterly Performance | Weekly (Thursday) |
| 8 | ShowK_ChartFlow | EPS x PER Weekly | Weekly (Friday) |
| 9 | StockHisAnaQuar | Quarterly Analysis | Weekly (Saturday) |
| 10 | EquityDistributionClassHis | Equity Class Weekly | Weekly (Sunday) |

## Enhanced Output Format with Retry Rate Monitoring (v2.0.0)

### Updated 8-Column Badge-Enhanced Markdown Table Structure
```markdown
| No | Folder                     | Total                                      | Success                                                   | Failed                                            | Updated from now                                         | Oldest                                          | Duration                                        | Retry Rate                                      |
| -- | -------------------------- | ------------------------------------------ | --------------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| 1  | DividendDetail             | ![](https://img.shields.io/badge/117-blue) | ![](https://img.shields.io/badge/31-success-brightgreen) | ![](https://img.shields.io/badge/86-failed-orange) | ![](https://img.shields.io/badge/1d_4h_ago-yellow)     | ![](https://img.shields.io/badge/3d_2h_ago-orange)   | ![](https://img.shields.io/badge/28m-blue)      | ![](https://img.shields.io/badge/2.3x-orange) |
| 2  | BasicInfo                  | 0                                          | 0                                                         |                                                   | N/A                                                      | N/A                                             | N/A                                             | N/A                                             |
| 10 | EquityDistributionClassHis | ![](https://img.shields.io/badge/117-blue) | ![](https://img.shields.io/badge/117-success-brightgreen) |                                                   | ![](https://img.shields.io/badge/1d_2h_ago-yellow)   | ![](https://img.shields.io/badge/5d_1h_ago-red)     | ![](https://img.shields.io/badge/35m-blue)      | ![](https://img.shields.io/badge/1.1x-yellow) |
```

### Retry Rate Column Specification (NEW v2.0.0)

#### Retry Rate Calculation and Display
```python
def calculate_retry_rate(csv_path: str) -> Dict:
    """Calculate comprehensive retry rate metrics"""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                return {'avg_retry': 0, 'max_retry': 0, 'retry_rate_pct': 0}
            
            retry_counts = []
            for row in rows:
                try:
                    retry_count = int(row.get('retry_count', 0))
                    retry_counts.append(retry_count)
                except (ValueError, TypeError):
                    retry_counts.append(0)
            
            total_retries = sum(retry_counts)
            max_retry = max(retry_counts) if retry_counts else 0
            files_with_retries = sum(1 for count in retry_counts if count > 0)
            
            # Average retry count across all files
            avg_retry = total_retries / len(retry_counts) if retry_counts else 0
            
            # Percentage of files that required retries
            retry_rate_pct = (files_with_retries / len(retry_counts) * 100) if retry_counts else 0
            
            return {
                'avg_retry': round(avg_retry, 1),
                'max_retry': max_retry,
                'retry_rate_pct': round(retry_rate_pct, 1),
                'total_files': len(retry_counts),
                'files_with_retries': files_with_retries
            }
    except Exception:
        return {'avg_retry': 0, 'max_retry': 0, 'retry_rate_pct': 0}

def format_retry_rate_display(retry_stats: Dict) -> str:
    """Format retry rate for compact display"""
    avg_retry = retry_stats.get('avg_retry', 0)
    
    if avg_retry == 0:
        return "1.0x avg"  # No retries = perfect first-attempt success
    
    return f"{avg_retry + 1:.1f}x avg"  # Add 1 because retry_count doesn't include first attempt
```

#### Retry Rate Badge Color Coding
```python
def get_retry_badge_color(retry_display: str) -> str:
    """Determine badge color for retry rate based on reliability"""
    if not retry_display or retry_display == 'N/A':
        return 'lightgrey'
    
    # Extract numeric value from display (e.g., "2.3x avg" -> 2.3)
    try:
        rate = float(retry_display.split('x')[0])
        
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
```

### Compact Time Format Specification (Unchanged from v1.9.0)

#### Short Time Format Rules
```python
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
```

## Technical Specifications

### Enhanced File Discovery Algorithm
```python
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

# Enhanced CSV parsing with retry_count support
# Expected CSV structure:
# filename,last_update_time,success,process_time,retry_count
```

### Enhanced Metric Calculations (v2.0.0)

#### 1. Total Files
- **Source**: Total rows in CSV (excluding header)
- **Default**: 0 if file missing/empty

#### 2. Success Count  
- **Source**: Count rows where `success=true`
- **Default**: 0 if no successful downloads

#### 3. Failed Count
- **Source**: Count rows where `success=false`  
- **Default**: 0 if no failed downloads

#### 4. Updated From Now (Compact Format)
- **Source**: Time difference between last row's `process_time` and current time
- **Format**: Compact notation like "1d 4h ago", "3h 15m ago", "now"

#### 5. Oldest
- **Source**: Time difference between oldest `last_update_time` across all rows and current time
- **Purpose**: Identify stale data that hasn't been updated in a long time
- **Format**: Compact notation like "3d 2h ago", "5d ago", "Never"

#### 6. Duration
- **Source**: Time difference between last row and first row `process_time`
- **Format**: Compact notation like "2h 15m", "1d 3h", "< 1m"

#### 7. Retry Rate (NEW - v2.0.0)
- **Source**: Average retry attempts across all files in CSV
- **Purpose**: Monitor download reliability and identify problematic data types
- **Format**: "X.Xx avg" where X.X is (average retry_count + 1)
- **Logic**:
  ```python
  # Calculate average retry_count across all rows
  # Add 1 because retry_count represents additional attempts beyond the first
  # Display format: "2.3x avg" means average of 2.3 total attempts per file
  # Color coding: Green (≤1.5x), Yellow (1.6-2.0x), Orange (2.1-3.0x), Red (>3.0x)
  ```

### Enhanced Badge Generation with Retry Rate Support

#### Updated Badge Generator Class (v2.0.0)
```python
class EnhancedBadgeGenerator:
    """Generate shields.io badges with compact time formats and retry rate support"""
    
    def retry_rate_badge(self, retry_display, use_badges=True):
        """Generate retry rate badge with appropriate color coding"""
        if not use_badges or retry_display in ['N/A', 'Error']:
            return retry_display
        
        # Encode for URL (replace spaces with underscores)
        encoded_text = retry_display.replace(' ', '_')
        
        # Determine color based on reliability
        color = self.get_retry_badge_color(retry_display)
        
        return f"![](https://img.shields.io/badge/{encoded_text}-{color})"
```

## Enhanced Output Integration (v2.0.0)

### Updated 8-Column Table Structure
```
| No | Folder | Total | Success | Failed | Updated from now | Oldest | Duration | Retry Rate |
```

### Enhanced README.md Integration
- **8-Column Table**: Update existing status table with retry rate monitoring
- **Reliability Insights**: Visual indicators for download reliability
- **Maintenance Alerts**: Easily identify data types requiring attention
- **Compact Time Display**: All time columns use compact notation for better readability
- **Enhanced Visual Appeal**: Color-coded status indicators with reliability monitoring
- **Staleness Monitoring**: Existing "Oldest" column helps identify data that needs attention
- **Preserve Format**: Maintain compatibility while adding retry rate monitoring
- **Timestamp**: Add "Last updated: YYYY-MM-DD HH:MM:SS (Taiwan)" footer

### Enhanced Visual Features (v2.0.0)

#### 8-Column Badge Styling Rules
1. **Total/Success/Failed Counts**: Unchanged badge styling
2. **Time Badges**: All use compact formats (e.g., "1d 4h ago", "3h 15m", "now")
3. **Retry Rate Badges**: New column with reliability-based color coding
4. **Color Coding Enhanced**:
   - **Updated from now**: Green → Yellow → Orange → Red (based on recency)
   - **Oldest**: Same color scale but represents staleness concern level
   - **Duration**: Always blue (neutral information)
   - **Retry Rate**: Green → Yellow → Orange → Red (based on reliability)
5. **Zero Values**: Empty cells (no badge)
6. **N/A Values**: Plain text, no badge

#### Enhanced Retry Rate Benefits
- **Reliability Monitoring**: Quickly identify unreliable data types
- **Maintenance Prioritization**: Focus efforts on high-retry folders
- **Trend Analysis**: Track reliability changes over time
- **Quality Assurance**: Ensure download processes are working efficiently
- **Resource Planning**: Understand which data types need more attention

## Advanced Implementation Features (v2.0.0)

### Enhanced Error Handling with Retry Rate Calculation
```python
def analyze_csv_enhanced(csv_path: str) -> Dict:
    """Enhanced CSV analysis with retry rate calculation"""
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
    
    # ... existing time calculations ...
    
    # NEW: Calculate retry rate metrics
    retry_counts = []
    for row in rows:
        try:
            retry_count = int(row.get('retry_count', 0))
            retry_counts.append(retry_count)
        except (ValueError, TypeError):
            retry_counts.append(0)
    
    if retry_counts:
        avg_retry = sum(retry_counts) / len(retry_counts)
        # Format as "X.Xx avg" showing total attempts (retry_count + 1)
        total_attempts_avg = avg_retry + 1.0
        stats['retry_rate'] = f"{total_attempts_avg:.1f}x avg"
    else:
        stats['retry_rate'] = 'N/A'
    
    return stats
```

### Enhanced Command Line Options (v2.0.0)
```bash
python download_results_counts.py [OPTIONS]

Options:
  --output FILE         Save output to specific file
  --format FORMAT       Output format: table|enhanced-table|compact-badges|json (default: compact-badges)
  --detailed            Include additional metrics and timestamps
  --update-readme       Update README.md status section with 8-column table
  --plain              Disable badges (fallback mode with compact times)
  --show-oldest        Highlight folders with oldest data (for maintenance)
  --show-high-retry    Highlight folders with high retry rates (NEW)
  --retry-threshold X   Set threshold for high retry rate alerts (default: 2.0)
  --help               Show help message
```

## Testing Strategy (v2.0.0)

### Unit Tests for Retry Rate Calculation
```python
# Test retry rate calculation with various inputs
def test_retry_rate_calculation():
    assert calculate_retry_rate_display([0, 0, 1, 2]) == "1.8x avg"  # (0+0+1+2)/4 + 1
    assert calculate_retry_rate_display([0, 0, 0, 0]) == "1.0x avg"  # Perfect reliability
    assert calculate_retry_rate_display([3, 4, 5]) == "5.0x avg"     # High retry rate

# Test badge color coding for retry rates
def test_retry_badge_colors():
    assert get_retry_badge_color("1.0x avg") == "brightgreen"  # Perfect
    assert get_retry_badge_color("1.8x avg") == "yellow"       # Moderate
    assert get_retry_badge_color("3.2x avg") == "red"          # Poor
```

### Integration Tests for 8-Column Table
```python
# Test 8-column table generation with retry rate
# Test README.md update with new column
# Test retry rate badge rendering
# Test high retry rate detection and alerts
```

## Reliability Monitoring Features (NEW v2.0.0)

### High Retry Rate Detection
- **Automatic Detection**: Identify folders with retry rates above threshold (default: 2.0x)
- **Alert System**: Highlight problematic data types in output
- **Maintenance Guidance**: Provide actionable insights for improving reliability

### Retry Rate Analysis
- **Average Calculation**: Sum of all retry_count values / total files + 1
- **Threshold-Based Coloring**: Visual indicators based on reliability levels
- **Trend Monitoring**: Track changes in retry rates over time

## Version History

### v2.0.0 Updates (NEW)
- **Added Retry Rate Column** - Monitor download reliability across all data types
- **8-Column Table Layout** - Extended table structure with comprehensive retry monitoring
- **Enhanced Reliability Monitoring** - Visual indicators for problematic data types
- **Maintenance Prioritization** - Easily identify folders needing attention
- **Advanced Color Coding** - Retry rate badges with reliability-based colors
- **High Retry Detection** - Automatic alerting for poor reliability patterns
- **Enhanced CLI Options** - New flags for retry rate analysis and thresholds

### v1.9.0 Features (Previous)
- Added Oldest Column for staleness monitoring
- Compact time formats for all time displays
- Enhanced time tracking with process_time vs last_update_time separation
- 7-column table layout with comprehensive time metrics

This enhanced design (v2.0.0) creates a comprehensive solution for monitoring both GoodInfo download status and reliability, with the new retry rate column providing critical insights into download quality and maintenance needs across all 10 data types.