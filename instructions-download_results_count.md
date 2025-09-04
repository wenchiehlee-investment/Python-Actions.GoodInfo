# Download Results Count Analyzer - Design Document (v1.8.0)

## Project Overview
Create a Python script `download_results_counts.py` that analyzes download status across all 10 GoodInfo data types by scanning `download_results.csv` files and generating comprehensive status reports.

## Purpose
Provide automated monitoring and reporting for the GoodInfo data downloader system, enabling quick assessment of download progress, success rates, and timing across all data types including the new Type 10 Equity Class Weekly data.

## Core Requirements

### Input Analysis
- **Scan Strategy**: Automatically discover `download_results.csv` files in predefined data type folders
- **CSV Format**: Parse standard tracking format with columns: `filename,last_update_time,success,process_time`
- **Data Types**: Support all 10 GoodInfo data types with their corresponding folders

### Output Generation
- **Markdown Table**: Generate status table matching README.md format
- **Real-time Metrics**: Calculate current statistics including time differences
- **Status Tracking**: Provide comprehensive overview of download health

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
- **Timezone**: Assume local timezone or UTC

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

## Output Format

### Markdown Table Structure
```markdown
|No| Folder |Total|Success| Failed|Updated from now|Duration|
|--| -- |--|--|--|--|--|
|1| DividendDetail |245|198|47|2 hours ago|3 days 4 hours|
|2| BasicInfo |245|0|0|Never|N/A|
|3| StockDetail |245|156|89|1 day ago|2 days 6 hours|
|10| EquityDistributionClassHis |245|201|44|1 hour ago|2 days 4 hours|
```

### Error Handling Display
- **Missing Folder**: Show "N/A" for all metrics
- **Empty CSV**: Show 0 for counts, "Never" for times
- **Invalid Data**: Show "Error" and continue processing other folders

## Implementation Features

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

# Date parsing with fallback
def safe_parse_date(date_string):
    if date_string in ['NOT_PROCESSED', 'NEVER', '']:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None
```

### Performance Optimization
- **Lazy Loading**: Only read CSV files when folder exists
- **Memory Efficient**: Process files one at a time
- **Fast Scanning**: Use os.path.exists() for folder detection

## Usage Scenarios

### Development Monitoring
```bash
# Check current status during development
python download_results_counts.py

# Integrate into CI/CD pipeline
python download_results_counts.py > status_report.md
```

### Automated Reporting
```bash
# Generate status for README.md update
python download_results_counts.py --update-readme

# Create detailed report with timestamps
python download_results_counts.py --detailed
```

## Output Integration

### README.md Integration
- **Replace Section**: Update existing status table in README.md
- **Preserve Format**: Maintain compatibility with existing documentation
- **Timestamp**: Add "Last updated: YYYY-MM-DD HH:MM:SS" footer

### Standalone Reports
- **Console Output**: Default behavior shows table in terminal
- **File Output**: Option to save as separate markdown file
- **JSON Export**: Optional structured data export for automation

## Advanced Features

### Command Line Options
```bash
python download_results_counts.py [OPTIONS]

Options:
  --output FILE     Save output to specific file
  --format FORMAT   Output format: table|json|csv
  --detailed        Include additional metrics
  --update-readme   Update README.md status section
  --help           Show help message
```

### Extended Metrics
- **Average Success Rate**: Percentage across all data types
- **Most Recent Activity**: Which data type was updated most recently
- **Completion Estimate**: Predicted time to complete failed downloads

### Integration Points
- **GitHub Actions**: Generate reports during automated runs
- **Monitoring Systems**: Export metrics for external monitoring
- **Email Reports**: Format suitable for automated email notifications

## Type 10 Specific Features (v1.8.0)

### Special Considerations for Equity Class Weekly
- **Sunday Automation**: Type 10 runs on Sunday 8 AM UTC (4 PM Taiwan)
- **Special Workflow**: Uses "查5年" button click workflow similar to Type 8
- **File Pattern**: `EquityDistributionClassHis_{stock_id}_{company_name}.xls`
- **Content Analysis**: 5-year weekly equity distribution class histogram data

### Monitoring Integration
- **Complete Week Coverage**: All 7 days now have automated data types
- **Perfect Load Distribution**: Sunday completes the weekly automation cycle
- **Enhanced Error Handling**: Type 10 included in special workflow timeout logic

### Reporting Enhancements
- **Version Tracking**: Include v1.8.0 version info in detailed reports
- **New Data Type Badge**: Mark Type 10 as "NEW!" in documentation
- **Complete Coverage**: Emphasize full 10 data type support

## Testing Strategy

### Unit Tests
```python
# Test CSV parsing with various formats
# Test time calculation edge cases
# Test missing file handling
# Test malformed data recovery
# Test Type 10 specific file patterns
```

### Integration Tests
```python
# Test with real download_results.csv files
# Test folder discovery across all 10 data types
# Test README.md update functionality
# Test Type 10 EquityDistributionClassHis folder handling
```

### Edge Case Testing
- Empty folders
- Corrupted CSV files  
- Future dates in process_time
- Unicode characters in filenames
- Very large CSV files (1000+ stocks)
- Type 10 specific filename patterns

## Maintenance Considerations

### Extensibility
- **New Data Types**: Easy addition of data type 11, 12, etc.
- **Custom Folders**: Support for non-standard folder names
- **Flexible CSV Format**: Adapt to CSV schema changes

### Monitoring
- **Log Generation**: Optional logging for debugging
- **Performance Metrics**: Track script execution time
- **Error Reporting**: Detailed error messages for troubleshooting

### Documentation Updates
- **Keep Sync**: Update when CSV format changes
- **Version Control**: Track changes to calculation logic (v1.8.0 updates)
- **User Guide**: Maintain clear usage instructions

## Version History

### v1.8.0 Updates
- Added Data Type 10 (EquityDistributionClassHis) support
- Complete 10 data type coverage
- Perfect 7-day weekly automation support
- Enhanced error handling for special workflow data types
- Updated documentation for complete weekly coverage

This design creates a comprehensive, maintainable solution for monitoring GoodInfo download status across all 10 data types with robust error handling and flexible output options, now including complete support for the new Type 10 Equity Class Weekly data.