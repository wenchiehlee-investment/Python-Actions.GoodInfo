# Download Results Count Analyzer - Design Document (v1.8.0)

## Project Overview
Create a Python script `download_results_counts.py` that analyzes download status across all 10 GoodInfo data types by scanning `download_results.csv` files and generating comprehensive status reports with **visual badge enhancements**.

## Purpose
Provide automated monitoring and reporting for the GoodInfo data downloader system, enabling quick assessment of download progress, success rates, and timing across all data types with **enhanced visual presentation using shields.io badges**.

## Core Requirements

### Input Analysis
- **Scan Strategy**: Automatically discover `download_results.csv` files in predefined data type folders
- **CSV Format**: Parse standard tracking format with columns: `filename,last_update_time,success,process_time`
- **Data Types**: Support all 10 GoodInfo data types with their corresponding folders

### Output Generation
- **Enhanced Markdown Table**: Generate status table with shields.io badges for visual appeal
- **Real-time Metrics**: Calculate current statistics including time differences
- **Status Tracking**: Provide comprehensive overview of download health with color-coded visual indicators

## Data Type Mapping (v1.8.0)

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
| 10 | EquityDistributionClassHis | Equity Class Weekly | Weekly (Sunday) 🆕 |

## Technical Specifications

### File Discovery Algorithm
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
```

### CSV Parsing Logic
```python
# Expected CSV structure:
# filename,last_update_time,success,process_time
# 
# Parse requirements:
# - Handle empty files (header only)
# - Handle missing files (folder exists but no CSV)
# - Handle malformed dates (use 'NEVER', 'NOT_PROCESSED')
# - Count boolean success values correctly
```

### Metric Calculations

#### 1. Total Files
- **Source**: Total rows in CSV (excluding header)
- **Default**: 0 if file missing/empty

#### 2. Success Count  
- **Source**: Count rows where `success=true`
- **Default**: 0 if no successful downloads

#### 3. Failed Count
- **Source**: Count rows where `success=false`  
- **Default**: 0 if no failed downloads

#### 4. Updated From Now
- **Source**: Time difference between last row's `process_time` and current time
- **Logic**: 
  ```python
  # Get last row's process_time
  # Handle special values: 'NOT_PROCESSED', 'NEVER'
  # Calculate: datetime.now() - last_process_time
  # Format: "X days Y hours ago" or "Never"
  ```

#### 5. Duration
- **Source**: Time difference between last row and first row `process_time`
- **Logic**:
  ```python
  # Get first non-header row's process_time
  # Get last row's process_time  
  # Handle edge cases: single row, all NOT_PROCESSED
  # Calculate: last_time - first_time
  # Format: "X days Y hours" or "N/A"
  ```

### Time Handling Strategy

#### Date Format Support
- **ISO Format**: `2025-01-15 14:30:25`
- **Special Values**: `NOT_PROCESSED`, `NEVER`
- **Timezone**: Taiwan timezone (Asia/Taipei) with fallback support

#### Display Format
```python
def format_time_ago(time_diff):
    """Convert timedelta to human-readable format"""
    if time_diff.days > 0:
        return f"{time_diff.days} days {time_diff.seconds//3600} hours ago"
    elif time_diff.seconds > 3600:
        return f"{time_diff.seconds//3600} hours ago"
    else:
        return f"{time_diff.seconds//60} minutes ago"

def format_duration(time_diff):
    """Convert timedelta to duration format"""
    if time_diff.days > 0:
        return f"{time_diff.days} days {time_diff.seconds//3600} hours"
    elif time_diff.seconds > 3600:
        return f"{time_diff.seconds//3600} hours"
    else:
        return f"{time_diff.seconds//60} minutes"
```

## Enhanced Output Format with Visual Badges

### Badge-Enhanced Markdown Table Structure
```markdown
| No | Folder                     | Total                                      | Success                                                   | Failed                                            | Updated from now                                         | Duration                                        |
| -- | -------------------------- | ------------------------------------------ | --------------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------- |
| 1  | DividendDetail             | ![](https://img.shields.io/badge/117-blue) | ![](https://img.shields.io/badge/117-success-brightgreen) |                                                   | ![](https://img.shields.io/badge/1d_4h_ago-blue)     | ![](https://img.shields.io/badge/28m-blue)      |
| 2  | BasicInfo                  | 0                                          | 0                                                         |                                                   | N/A                                                      | N/A                                             |
| 10 | EquityDistributionClassHis | ![](https://img.shields.io/badge/117-blue) | ![](https://img.shields.io/badge/117-success-brightgreen) |                                                   | ![](https://img.shields.io/badge/1d_2h_ago-yellow)   | ![](https://img.shields.io/badge/35m-blue)      |
```

### Badge Generation Logic

#### Count Badges
```python
def generate_count_badge(count, badge_type="count"):
    """Generate shields.io badge for counts"""
    if count == 0:
        return ""  # Empty cell for zero values
    
    if badge_type == "total":
        return f"![](https://img.shields.io/badge/{count}-blue)"
    elif badge_type == "success":
        return f"![](https://img.shields.io/badge/{count}-success-brightgreen)"
    elif badge_type == "failed":
        return f"![](https://img.shields.io/badge/{count}-failed-orange)"
    
    return f"![](https://img.shields.io/badge/{count}-blue)"
```

#### Time-Based Badges with Color Coding
```python
def generate_time_badge(time_text, is_duration=False):
    """Generate time badge with appropriate color based on recency"""
    if time_text in ['N/A', 'Never']:
        return time_text  # No badge for N/A values
    
    # URL encode the time text for badge (use underscore approach for reliability)
    encoded_text = time_text.replace(' ', '_')
    
    if is_duration:
        # Duration badges are always blue
        return f"![](https://img.shields.io/badge/{encoded_text}-blue)"
    
    # Color coding for "Updated from now" based on recency
    color = get_time_badge_color(time_text)
    return f"![](https://img.shields.io/badge/{encoded_text}-{color})"

def get_time_badge_color(time_text):
    """Determine badge color based on how recent the update was"""
    if 'Just now' in time_text or ('minute' in time_text and 'hour' not in time_text and 'day' not in time_text):
        return 'brightgreen'  # Very recent (< 1 hour)
    elif 'hour' in time_text and 'day' not in time_text:
        if 'hours' in time_text:
            # Extract hours for more precise coloring
            hours = extract_hours_from_text(time_text)
            if hours <= 6:
                return 'brightgreen'  # Recent (< 6 hours)
            else:
                return 'yellow'       # Somewhat recent (6-24 hours)
        return 'brightgreen'
    elif '1 day' in time_text or '1d' in time_text:
        return 'yellow'               # 1 day old
    elif 'day' in time_text:
        days = extract_days_from_text(time_text)
        if days <= 3:
            return 'orange'           # 2-3 days old
        else:
            return 'red'              # > 3 days old
    else:
        return 'blue'                 # Default color
```

### Visual Enhancement Features

#### Badge Styling Rules
1. **Total Counts**: Always blue badges
2. **Success Counts**: Green badges with "success" label
3. **Failed Counts**: Orange badges with "failed" label
4. **Zero Values**: Empty cells (no badge)
5. **Time Recency**: Color-coded based on how recent:
   - 🟢 Green: Just now, < 6 hours
   - 🟡 Yellow: 6-24 hours, 1 day
   - 🟠 Orange: 2-3 days
   - 🔴 Red: > 3 days
6. **Duration**: Always blue (neutral information)
7. **N/A Values**: Plain text, no badge

#### Badge Encoding Strategy
```python
def encode_badge_text(text):
    """Encode text for shields.io URLs - using underscore approach for reliability"""
    # Use underscore replacement to avoid double-encoding issues
    # This is a pragmatic solution that ensures consistent rendering
    return text.replace(" ", "_")
```

### Error Handling Display
- **Missing Folder**: Show "N/A" for all metrics (plain text)
- **Empty CSV**: Show 0 for counts (no badges), "Never" for times
- **Invalid Data**: Show "Error" and continue processing other folders

## Implementation Features

### Enhanced Badge Generation
```python
class BadgeGenerator:
    """Generate shields.io badges for various metrics"""
    
    def __init__(self, use_badges=True):
        self.base_url = "https://img.shields.io/badge/"
        self.use_badges = use_badges
    
    def count_badge(self, count, label_type="total"):
        """Generate count badge with appropriate styling"""
        if not self.use_badges or count == 0:
            return ""
        
        color_map = {
            "total": "blue",
            "success": "success-brightgreen", 
            "failed": "failed-orange"
        }
        
        color = color_map.get(label_type, "blue")
        return f"![](https://img.shields.io/badge/{count}-{color})"
    
    def time_badge(self, time_text, badge_type="updated"):
        """Generate time badge with color coding"""
        if not self.use_badges or time_text in ['N/A', 'Never']:
            return time_text
        
        encoded_text = self.encode_text(time_text)
        
        if badge_type == "duration":
            color = "blue"
        else:
            color = self.get_recency_color(time_text)
        
        return f"![](https://img.shields.io/badge/{encoded_text}-{color})"
    
    def encode_text(self, text):
        """Encode text for shields.io using underscore approach"""
        return text.replace(' ', '_')
    
    def get_recency_color(self, time_text):
        """Color coding based on recency using regex pattern matching"""
        # Detailed implementation as specified above
        pass
```

### Robust Error Handling
```python
# File system errors
try:
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Process CSV
except FileNotFoundError:
    return default_stats()
except PermissionError:
    print(f"Warning: Cannot access {csv_path}")
    return default_stats()
```

### Data Validation
```python
# CSV row validation
def validate_csv_row(row):
    required_columns = ['filename', 'last_update_time', 'success', 'process_time']
    return len(row) >= len(required_columns)

# Date parsing with Taiwan timezone support
def safe_parse_date(date_string):
    if date_string in ['NOT_PROCESSED', 'NEVER', '']:
        return None
    try:
        dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        if TAIPEI_TZ:
            dt = dt.replace(tzinfo=TAIPEI_TZ)
        return dt
    except ValueError:
        return None
```

### Performance Optimization
- **Lazy Loading**: Only read CSV files when folder exists
- **Memory Efficient**: Process files one at a time
- **Fast Scanning**: Use os.path.exists() for folder detection
- **Badge Caching**: Cache badge generation for repeated values

## Usage Scenarios

### Development Monitoring
```bash
# Check current status with enhanced visual presentation
python download_results_counts.py

# Generate enhanced status for README.md update
python download_results_counts.py --format enhanced-table

# Create detailed report with badges
python download_results_counts.py --detailed --format badges
```

### Automated Reporting
```bash
# Generate enhanced status for README.md update
python download_results_counts.py --update-readme --format badges

# Create detailed report with visual enhancements
python download_results_counts.py --detailed --format enhanced
```

## Output Integration

### README.md Integration with Badges
- **Replace Section**: Update existing status table with badge-enhanced version
- **Visual Appeal**: Enhanced readability with color-coded status indicators
- **Preserve Format**: Maintain compatibility while adding visual enhancements
- **Timestamp**: Add "Last updated: YYYY-MM-DD HH:MM:SS (Taiwan)" footer

### Standalone Reports
- **Console Output**: Default shows enhanced table in terminal
- **File Output**: Option to save as enhanced markdown file
- **JSON Export**: Optional structured data export for automation
- **Plain Table**: Fallback option for environments that don't support badges

## Advanced Features

### Command Line Options
```bash
python download_results_counts.py [OPTIONS]

Options:
  --output FILE         Save output to specific file
  --format FORMAT       Output format: table|enhanced-table|badges|json (default: enhanced-table)
  --detailed            Include additional metrics and timestamps
  --update-readme       Update README.md status section with badges
  --plain              Disable badges (fallback mode)
  --help               Show help message
```

### Extended Visual Features
- **Status Overview**: Color-coded summary of overall system health
- **Trend Indicators**: Visual indicators for improving/declining performance
- **Priority Highlighting**: Enhanced visibility for critical status issues
- **Mobile-Friendly**: Badges scale well on different screen sizes

### Integration Points
- **GitHub Pages**: Enhanced visual presentation for documentation sites
- **Monitoring Dashboards**: Export badge URLs for external monitoring systems
- **Email Reports**: HTML format with visual badges for automated notifications
- **CI/CD Integration**: Enhanced status reporting in GitHub Actions

## Type 10 Specific Features (v1.8.0)

### Special Considerations for Equity Class Weekly
- **Sunday Automation**: Type 10 runs on Sunday 8 AM UTC (4 PM Taiwan)
- **Special Workflow**: Uses "查5年" button click workflow similar to Type 8
- **File Pattern**: `EquityDistributionClassHis_{stock_id}_{company_name}.xls`
- **Content Analysis**: 5-year weekly equity distribution class histogram data

### Visual Enhancements for Type 10
- **New Badge**: Special "NEW!" indicator for Type 10 in documentation
- **Complete Coverage Badge**: Highlight complete 10 data type support
- **Sunday Schedule Badge**: Visual indicator for Sunday automation completion

## Testing Strategy

### Unit Tests
```python
# Test badge generation with various inputs
# Test CSV parsing with badge output
# Test time calculation and color coding
# Test missing file handling with badge fallback
# Test Type 10 specific badge patterns
# Test underscore encoding for special characters
```

### Integration Tests
```python
# Test badge rendering in various markdown environments
# Test folder discovery with enhanced output
# Test README.md update with badge integration
# Test Type 10 EquityDistributionClassHis folder with badges
# Test color coding accuracy across different time ranges
```

### Visual Tests
- Badge rendering in GitHub
- Mobile compatibility
- Dark/light theme compatibility
- Screen reader accessibility
- Badge loading performance

## Maintenance Considerations

### Extensibility
- **New Badge Types**: Easy addition of new visual indicators
- **Color Schemes**: Customizable color coding for different environments
- **Badge Providers**: Support for alternative badge services beyond shields.io

### Monitoring
- **Badge Performance**: Track badge loading times and failures
- **Visual Consistency**: Ensure consistent rendering across platforms
- **Accessibility**: Maintain compatibility with screen readers and accessibility tools

### Documentation Updates
- **Keep Visual**: Update screenshots and examples when badge format changes
- **Version Control**: Track changes to badge generation logic (v1.8.0 updates)
- **User Guide**: Maintain clear usage instructions for enhanced features

## Version History

### v1.8.0 Updates
- Added **Visual Badge Enhancement** with shields.io integration
- **Complete 10 data type coverage** with enhanced visual presentation
- **Color-coded status indicators** based on recency and success rates
- **Enhanced README.md integration** with badge-based status table
- **Mobile-friendly visual design** that scales across devices
- **Improved accessibility** while maintaining visual appeal
- **Underscore encoding solution** for reliable badge rendering

This enhanced design creates a comprehensive, visually appealing, and maintainable solution for monitoring GoodInfo download status across all 10 data types with robust error handling, flexible output options, and enhanced visual presentation using shields.io badges for improved readability and status comprehension.