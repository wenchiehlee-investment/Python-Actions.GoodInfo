# Download Results Count Analyzer - Design Document (v1.9.0)

## Project Overview
Create a Python script `download_results_counts.py` that analyzes download status across all 10 GoodInfo data types by scanning `download_results.csv` files and generating comprehensive status reports with **enhanced visual badge presentation** and **concise time formats**.

## Purpose
Provide automated monitoring and reporting for the GoodInfo data downloader system, enabling quick assessment of download progress, success rates, and timing across all data types with **enhanced visual presentation using shields.io badges** and **compact time display formats**.

## Core Requirements

### Input Analysis
- **Scan Strategy**: Automatically discover `download_results.csv` files in predefined data type folders
- **CSV Format**: Parse standard tracking format with columns: `filename,last_update_time,success,process_time`
- **Data Types**: Support all 10 GoodInfo data types with their corresponding folders

### Output Generation
- **Enhanced Markdown Table**: Generate status table with shields.io badges and concise time formats
- **Real-time Metrics**: Calculate current statistics including time differences with compact notation
- **Status Tracking**: Provide comprehensive overview of download health with color-coded visual indicators
- **Oldest Tracking**: Track the oldest update time across all entries for staleness detection

## Data Type Mapping (v1.9.0)

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

## Enhanced Output Format with Compact Time Presentation

### Updated Badge-Enhanced Markdown Table Structure (v1.9.0)
```markdown
| No | Folder                     | Total                                      | Success                                                   | Failed                                            | Updated from now                                         | Oldest                                          | Duration                                        |
| -- | -------------------------- | ------------------------------------------ | --------------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| 1  | DividendDetail             | ![](https://img.shields.io/badge/117-blue) | ![](https://img.shields.io/badge/117-success-brightgreen) |                                                   | ![](https://img.shields.io/badge/1d_4h_ago-yellow)     | ![](https://img.shields.io/badge/3d_2h_ago-orange)   | ![](https://img.shields.io/badge/28m-blue)      |
| 2  | BasicInfo                  | 0                                          | 0                                                         |                                                   | N/A                                                      | N/A                                             | N/A                                             |
| 10 | EquityDistributionClassHis | ![](https://img.shields.io/badge/117-blue) | ![](https://img.shields.io/badge/117-success-brightgreen) |                                                   | ![](https://img.shields.io/badge/1d_2h_ago-yellow)   | ![](https://img.shields.io/badge/5d_1h_ago-red)     | ![](https://img.shields.io/badge/35m-blue)      |
```

### Compact Time Format Specification (v1.9.0)

#### Short Time Format Rules
```python
def format_time_compact(time_diff: timedelta) -> str:
    """Convert timedelta to compact format like '3d 2h 15m ago'"""
    if time_diff.total_seconds() < 0:
        return "Future"
    
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
```

## New Metric: Oldest Update Time

### Purpose and Implementation
The "Oldest" column tracks the oldest `last_update_time` across all entries in the CSV file to identify potentially stale data that might need attention.

#### Oldest Time Calculation Logic
```python
def calculate_oldest_time(csv_path: str) -> Optional[str]:
    """Find the oldest last_update_time in the CSV file"""
    current_time = get_taipei_time()
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                return None
                
            # Parse all last_update_time values
            update_times = []
            for row in rows:
                time_parsed = safe_parse_date(row['last_update_time'])
                if time_parsed:
                    update_times.append(time_parsed)
            
            if not update_times:
                return 'Never'
                
            # Find the oldest time
            oldest_time = min(update_times)
            
            # Calculate time difference from now
            if current_time.tzinfo and oldest_time.tzinfo:
                time_diff = current_time - oldest_time
            else:
                # Fallback for timezone handling
                current_naive = current_time.replace(tzinfo=None) if current_time.tzinfo else current_time
                oldest_naive = oldest_time.replace(tzinfo=None) if oldest_time.tzinfo else oldest_time
                time_diff = current_naive - oldest_naive
                
            return format_time_compact(time_diff)
            
    except Exception:
        return 'Error'
```

### Color Coding for Oldest Column
```python
def get_oldest_badge_color(time_text: str) -> str:
    """Determine badge color for oldest time based on staleness"""
    if not time_text or time_text in ['N/A', 'Never', 'Error']:
        return 'lightgrey'
    
    # Color coding based on staleness (older = more concerning)
    if 'now' in time_text or ('m ago' in time_text and 'h' not in time_text and 'd' not in time_text):
        return 'brightgreen'  # Very fresh (< 1 hour)
    elif 'h ago' in time_text and 'd' not in time_text:
        return 'yellow'       # Recent (hours old)
    elif '1d' in time_text:
        return 'yellow'       # 1 day old
    elif '2d' in time_text or '3d' in time_text:
        return 'orange'       # 2-3 days old (getting stale)
    elif 'd' in time_text:
        return 'red'          # > 3 days old (stale)
    else:
        return 'blue'         # Default
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

# Scan pattern: {folder}/download_results.csv
# Handle missing files gracefully with default values
# Calculate both process_time (most recent) and last_update_time (oldest) metrics
```

### Enhanced CSV Parsing Logic
```python
# Expected CSV structure:
# filename,last_update_time,success,process_time
# 
# Enhanced parse requirements (v1.9.0):
# - Handle empty files (header only)
# - Handle missing files (folder exists but no CSV)
# - Handle malformed dates (use 'NEVER', 'NOT_PROCESSED')
# - Count boolean success values correctly
# - Track both process_time (latest) and last_update_time (oldest) for comprehensive timing
# - Calculate compact time formats for all time-based metrics
```

### Enhanced Metric Calculations (v1.9.0)

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
- **Logic**: 
  ```python
  # Get last row's process_time (most recent processing)
  # Handle special values: 'NOT_PROCESSED', 'NEVER'
  # Calculate: datetime.now() - last_process_time
  # Format: compact notation with max 2 time units
  ```

#### 5. Oldest (NEW - v1.9.0)
- **Source**: Time difference between oldest `last_update_time` across all rows and current time
- **Purpose**: Identify stale data that hasn't been updated in a long time
- **Format**: Compact notation like "3d 2h ago", "5d ago", "Never"
- **Logic**:
  ```python
  # Get oldest last_update_time across all rows
  # Handle edge cases: no valid times, all NOT_PROCESSED
  # Calculate: datetime.now() - oldest_update_time
  # Format: compact notation with appropriate staleness color coding
  ```

#### 6. Duration (Compact Format)
- **Source**: Time difference between last row and first row `process_time`
- **Format**: Compact notation like "2h 15m", "1d 3h", "< 1m"
- **Logic**:
  ```python
  # Get first non-header row's process_time
  # Get last row's process_time  
  # Handle edge cases: single row, all NOT_PROCESSED
  # Calculate: last_time - first_time
  # Format: compact duration with max 2 time units
  ```

### Enhanced Badge Generation with Compact Time Support

#### Updated Badge Generator Class (v1.9.0)
```python
class EnhancedBadgeGenerator:
    """Generate shields.io badges with compact time formats"""
    
    def __init__(self, use_badges=True):
        self.base_url = "https://img.shields.io/badge/"
        self.use_badges = use_badges
    
    def compact_time_badge(self, time_text, badge_type="updated"):
        """Generate time badge with compact format and appropriate color"""
        if not self.use_badges or time_text in ['N/A', 'Never', 'Error']:
            return time_text
        
        # Encode compact time text for URL (underscore approach)
        encoded_text = self.encode_compact_time(time_text)
        
        # Determine color based on badge type and time value
        if badge_type == "duration":
            color = "blue"  # Duration is always informational
        elif badge_type == "oldest":
            color = self.get_oldest_badge_color(time_text)  # Staleness-based coloring
        else:  # "updated"
            color = self.get_recency_color(time_text)  # Recency-based coloring
        
        return f"![](https://img.shields.io/badge/{encoded_text}-{color})"
    
    def encode_compact_time(self, time_text):
        """Encode compact time format for shields.io using underscore approach"""
        return time_text.replace(' ', '_')
    
    def get_recency_color(self, time_text):
        """Color coding for 'Updated from now' based on recency"""
        if 'now' in time_text:
            return 'brightgreen'  # Just updated
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
            return 'blue'         # Default
    
    def get_oldest_badge_color(self, time_text):
        """Color coding for 'Oldest' based on data staleness"""
        # Same logic as recency but with staleness interpretation
        # Older data gets warmer colors (orange/red) to indicate need for attention
        return self.get_recency_color(time_text)  # Same color logic applies
```

## Enhanced Output Integration (v1.9.0)

### Updated Table Structure
```
| No | Folder | Total | Success | Failed | Updated from now | Oldest | Duration |
```

### Enhanced README.md Integration
- **Replace Section**: Update existing status table with 7-column badge-enhanced version
- **Compact Time Display**: All time columns use compact notation for better readability
- **Enhanced Visual Appeal**: Color-coded status indicators with compact time formats
- **Staleness Monitoring**: New "Oldest" column helps identify data that needs attention
- **Preserve Format**: Maintain compatibility while adding enhanced time features
- **Timestamp**: Add "Last updated: YYYY-MM-DD HH:MM:SS (Taiwan)" footer

### Enhanced Visual Features (v1.9.0)

#### Compact Badge Styling Rules
1. **Total/Success/Failed Counts**: Unchanged badge styling
2. **Time Badges**: All use compact formats (e.g., "1d 4h ago", "3h 15m", "now")
3. **Color Coding Enhanced**:
   - **Updated from now**: Green → Yellow → Orange → Red (based on recency)
   - **Oldest**: Same color scale but represents staleness concern level
   - **Duration**: Always blue (neutral information)
4. **Zero Values**: Empty cells (no badge)
5. **N/A Values**: Plain text, no badge

#### Enhanced Time Format Benefits
- **Readability**: Compact notation easier to scan in tables
- **Consistency**: All time columns use same compact format
- **Space Efficiency**: Shorter text fits better in table columns
- **Professional**: Clean, technical appearance
- **Badge Compatibility**: Compact format works better in shields.io URLs

## Advanced Implementation Features (v1.9.0)

### Enhanced Error Handling with Oldest Calculation
```python
def analyze_csv_enhanced(csv_path: str) -> Dict:
    """Enhanced CSV analysis with oldest time calculation"""
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
    
    # ... existing error handling ...
    
    # Enhanced time calculations
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
        time_diff = current_time - last_process_time
        stats['updated_from_now'] = format_time_compact(time_diff)
    
    # Calculate Oldest (oldest last_update_time)
    if update_times:
        oldest_update_time = min(update_times)
        time_diff = current_time - oldest_update_time
        stats['oldest'] = format_time_compact(time_diff)
    
    # Calculate Duration (span of process_times)
    if len(process_times) > 1:
        duration_diff = max(process_times) - min(process_times)
        stats['duration'] = format_duration_compact(duration_diff)
    
    return stats
```

### Enhanced Command Line Options (v1.9.0)
```bash
python download_results_counts.py [OPTIONS]

Options:
  --output FILE         Save output to specific file
  --format FORMAT       Output format: table|enhanced-table|compact-badges|json (default: compact-badges)
  --detailed            Include additional metrics and timestamps
  --update-readme       Update README.md status section with compact badges
  --plain              Disable badges (fallback mode with compact times)
  --show-oldest        Highlight folders with oldest data (for maintenance)
  --help               Show help message
```

## Testing Strategy (v1.9.0)

### Unit Tests for Compact Time Format
```python
# Test compact time formatting with various inputs
def test_compact_time_format():
    assert format_time_compact(timedelta(days=1, hours=4)) == "1d 4h ago"
    assert format_time_compact(timedelta(hours=3, minutes=15)) == "3h 15m ago"
    assert format_time_compact(timedelta(minutes=30)) == "30m ago"
    assert format_time_compact(timedelta(seconds=30)) == "now"

# Test oldest time calculation
def test_oldest_calculation():
    # Test with various last_update_time scenarios
    pass

# Test badge generation with compact formats
def test_compact_badge_generation():
    # Test URL encoding of compact time formats
    # Test color coding logic for oldest vs updated columns
    pass
```

### Integration Tests for Enhanced Table
```python
# Test 7-column table generation
# Test README.md update with new column
# Test compact time badge rendering
# Test oldest time tracking across different CSV files
```

## Version History

### v1.9.0 Updates (NEW)
- **Added Oldest Column** - Track oldest `last_update_time` for staleness monitoring
- **Compact Time Formats** - All time displays use concise "1d 4h ago" notation
- **Enhanced Time Tracking** - Separate tracking of process_time vs last_update_time
- **Improved Badge Generation** - Compact time format support in shields.io badges
- **Better Staleness Detection** - Visual indicators for data that needs attention
- **7-Column Table Layout** - Updated table structure with comprehensive time metrics
- **Enhanced README Integration** - Improved status table with compact time display

### v1.8.0 Features (Previous)
- Complete 10 data types with visual badge enhancement
- Color-coded status indicators
- Enhanced README.md integration
- Mobile-friendly visual design

This enhanced design (v1.9.0) creates a more comprehensive and visually efficient solution for monitoring GoodInfo download status with compact time formats, staleness detection, and improved time-based metrics tracking across all 10 data types.