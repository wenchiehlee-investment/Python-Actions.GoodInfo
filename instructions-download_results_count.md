# Download Results Count Analyzer - Design Document (v3.0.0)

## Project Overview
Create a Python script `download_results_counts.py` that analyzes download status across all **11 GoodInfo data types** by scanning `download_results.csv` files and generating comprehensive status reports with **enhanced visual badge presentation**, **concise time formats**, and **retry rate monitoring**.

## Purpose
Provide automated monitoring and reporting for the GoodInfo data downloader system, enabling quick assessment of download progress, success rates, timing, and **reliability metrics** across all data types with **enhanced visual presentation using shields.io badges**, **compact time display formats**, and **retry rate analysis**.

## Core Requirements

### Input Analysis
- **Scan Strategy**: Automatically discover `download_results.csv` files in predefined data type folders
- **CSV Format**: Parse standard tracking format with columns: `filename,last_update_time,success,process_time,retry_count`
- **Data Types**: Support all **11 GoodInfo data types** with their corresponding folders
- **Retry Analysis**: Calculate retry rate metrics for reliability monitoring

### Output Generation
- **Enhanced 8-Column Markdown Table**: Generate status table with shields.io badges, compact time formats, and retry rate monitoring
- **Real-time Metrics**: Calculate current statistics including time differences with compact notation
- **Status Tracking**: Provide comprehensive overview of download health with color-coded visual indicators
- **Reliability Monitoring**: Track retry rates to identify problematic data types requiring attention
- **Oldest Tracking**: Track the oldest update time across all entries for staleness detection

## Enhanced Data Type Mapping (v3.0.0)

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
| 11 | WeeklyTradingData | Weekly Trading Data | Weekly (Monday Evening) 🆕 |

## Enhanced Output Format with Retry Rate Monitoring (v3.0.0)

### Updated 8-Column Badge-Enhanced Markdown Table Structure
```markdown
| No | Folder                     | Total                                      | Success                                                   | Failed                                            | Updated from now                                         | Oldest                                          | Duration                                        | Retry Rate                                      |
| -- | -------------------------- | ------------------------------------------ | --------------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| 1  | DividendDetail             | ![](https://img.shields.io/badge/117-blue) | ![](https://img.shields.io/badge/31-success-brightgreen) | ![](https://img.shields.io/badge/86-failed-orange) | ![](https://img.shields.io/badge/1d_4h_ago-yellow)     | ![](https://img.shields.io/badge/3d_2h_ago-orange)   | ![](https://img.shields.io/badge/28m-blue)      | ![](https://img.shields.io/badge/2.3x-orange) |
| 2  | BasicInfo                  |                                            |                                                           |                                                   | N/A                                                      | N/A                                             | N/A                                             | N/A                                             |
| 10 | EquityDistributionClassHis | ![](https://img.shields.io/badge/117-blue) | ![](https://img.shields.io/badge/117-success-brightgreen) |                                                   | ![](https://img.shields.io/badge/1d_2h_ago-yellow)   | ![](https://img.shields.io/badge/5d_1h_ago-red)     | ![](https://img.shields.io/badge/35m-blue)      | ![](https://img.shields.io/badge/1.1x-yellow) |
| 11 | WeeklyTradingData          | ![](https://img.shields.io/badge/117-blue) | ![](https://img.shields.io/badge/109-success-brightgreen) | ![](https://img.shields.io/badge/8-failed-orange) | ![](https://img.shields.io/badge/6h_ago-yellow)      | ![](https://img.shields.io/badge/1d_ago-yellow)     | ![](https://img.shields.io/badge/2h_15m-blue)   | ![](https://img.shields.io/badge/1.3x-green) |
```

### Type 11 Specific Features (NEW v3.0.0)

#### Weekly Trading Data with Institutional Flows
- **Comprehensive OHLC Data**: Weekly open, high, low, close prices
- **Volume Analysis**: Trading volume and turnover metrics
- **Institutional Flows**: Foreign investors (外資), Investment trusts (投信), Proprietary trading (自營)
- **Margin Trading**: Financing (融資) and securities lending (融券) data
- **Market Microstructure**: Advanced trading pattern analysis
- **5-Year Coverage**: Historical data spanning 5 years for trend analysis

#### Type 11 Monitoring Considerations
- **Complex Data Structure**: More comprehensive dataset requiring enhanced validation
- **Institutional Data Dependencies**: Multiple data sources that may have varying reliability
- **Enhanced Processing Time**: Expect longer download durations due to data complexity
- **Retry Rate Expectations**: May have higher retry rates due to institutional data complexity

### Retry Rate Column Specification (Unchanged from v2.0.0)

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
        return "1.0x"  # No retries = perfect first-attempt success
    
    return f"{avg_retry + 1:.1f}x"  # Add 1 because retry_count doesn't include first attempt
```

#### Retry Rate Badge Color Coding
```python
def get_retry_badge_color(retry_display: str) -> str:
    """Determine badge color for retry rate based on reliability"""
    if not retry_display or retry_display == 'N/A':
        return 'lightgrey'
    
    # Extract numeric value from display (e.g., "2.3x" -> 2.3)
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

### Compact Time Format Specification (Unchanged from v2.0.0)

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
    return f"{compact_time}_ago"
```

## Technical Specifications

### Enhanced File Discovery Algorithm (v3.0.0)
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
    10: "EquityDistributionClassHis",
    11: "WeeklyTradingData"  # 🆕 NEW in v3.0.0
}

# Enhanced CSV parsing with retry_count support
# Expected CSV structure:
# filename,last_update_time,success,process_time,retry_count
```

### Enhanced Metric Calculations (v3.0.0)

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
- **Format**: Compact notation like "1d_4h_ago", "3h_15m_ago", "now"

#### 5. Oldest
- **Source**: Time difference between oldest `last_update_time` across all rows and current time
- **Purpose**: Identify stale data that hasn't been updated in a long time
- **Format**: Compact notation like "3d_2h_ago", "5d_ago", "Never"

#### 6. Duration
- **Source**: Time difference between last row and first row `process_time`
- **Format**: Compact notation like "2h_15m", "1d_3h", "< 1m"

#### 7. Retry Rate (Enhanced for Type 11 - v3.0.0)
- **Source**: Average retry attempts across all files in CSV
- **Purpose**: Monitor download reliability and identify problematic data types
- **Format**: "X.Xx" where X.X is (average retry_count + 1)
- **Type 11 Considerations**: May exhibit higher retry rates due to complex institutional data
- **Logic**:
  ```python
  # Calculate average retry_count across all rows
  # Add 1 because retry_count represents additional attempts beyond the first
  # Display format: "2.3x" means average of 2.3 total attempts per file
  # Color coding: Green (≤1.5x), Yellow (1.6-2.0x), Orange (2.1-3.0x), Red (>3.0x)
  # Type 11 threshold adjustments: Consider 1.8x as acceptable due to complexity
  ```

### Enhanced Badge Generation with Type 11 Support

#### Updated Badge Generator Class (v3.0.0)
```python
class EnhancedBadgeGenerator:
    """Generate shields.io badges with compact time formats and Type 11 support"""
    
    def retry_rate_badge(self, retry_display, data_type=None, use_badges=True):
        """Generate retry rate badge with Type 11 considerations"""
        if not use_badges or retry_display in ['N/A', 'Error']:
            return retry_display
        
        # Encode for URL (replace spaces with underscores)
        encoded_text = retry_display.replace(' ', '_')
        
        # Determine color based on reliability with Type 11 adjustments
        color = self.get_retry_badge_color_enhanced(retry_display, data_type)
        
        return f"![](https://img.shields.io/badge/{encoded_text}-{color})"
    
    def get_retry_badge_color_enhanced(self, retry_display: str, data_type: int = None) -> str:
        """Enhanced color determination with Type 11 considerations"""
        if not retry_display or retry_display == 'N/A':
            return 'lightgrey'
        
        try:
            rate = float(retry_display.replace('x', ''))
            
            # Type 11 has more lenient thresholds due to complexity
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
            else:
                # Standard thresholds for other types
                if rate <= 1.0:
                    return 'brightgreen'
                elif rate <= 1.5:
                    return 'green'
                elif rate <= 2.0:
                    return 'yellow'
                elif rate <= 3.0:
                    return 'orange'
                else:
                    return 'red'
        except (ValueError, IndexError):
            return 'blue'
```

## Enhanced Output Integration (v3.0.0)

### Updated 8-Column Table Structure
```
| No | Folder | Total | Success | Failed | Updated from now | Oldest | Duration | Retry Rate |
```

### Enhanced README.md Integration
- **8-Column Table**: Update existing status table with Type 11 support
- **Reliability Insights**: Visual indicators for download reliability including Type 11
- **Maintenance Alerts**: Easily identify data types requiring attention
- **Compact Time Display**: All time columns use compact notation for better readability
- **Enhanced Visual Appeal**: Color-coded status indicators with Type 11 considerations
- **Staleness Monitoring**: Existing "Oldest" column helps identify data that needs attention
- **Type 11 Monitoring**: Special considerations for complex institutional data
- **Preserve Format**: Maintain compatibility while adding comprehensive Type 11 support
- **Timestamp**: Add "Last updated: YYYY-MM-DD HH:MM:SS (Taiwan)" footer

### Enhanced Visual Features (v3.0.0)

#### 8-Column Badge Styling Rules
1. **Total/Success/Failed Counts**: Enhanced for Type 11 data volume
2. **Time Badges**: All use compact formats (e.g., "1d_4h_ago", "3h_15m", "now")
3. **Retry Rate Badges**: Enhanced column with Type 11 reliability considerations
4. **Color Coding Enhanced**:
   - **Updated from now**: Green → Yellow → Orange → Red (based on recency)
   - **Oldest**: Same color scale but represents staleness concern level
   - **Duration**: Always blue (neutral information)
   - **Retry Rate**: Enhanced thresholds for Type 11 complexity
5. **Zero Values**: Empty cells (no badge)
6. **N/A Values**: Plain text, no badge

#### Enhanced Type 11 Benefits
- **Institutional Flow Monitoring**: Track comprehensive trading data reliability
- **Complex Data Validation**: Enhanced retry rate analysis for multi-source data
- **Market Analysis Support**: Ensure institutional data quality for analysis
- **Trading Pattern Integrity**: Monitor data completeness for trading insights
- **Performance Benchmarking**: Compare Type 11 performance against simpler data types

## Advanced Implementation Features (v3.0.0)

### Enhanced Error Handling with Type 11 Support
```python
def analyze_csv_enhanced(csv_path: str, data_type: int = None) -> Dict:
    """Enhanced CSV analysis with Type 11 considerations"""
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
    
    # ... existing time calculations ...
    
    # Enhanced: Calculate retry rate metrics with Type 11 considerations
    retry_counts = []
    for row in rows:
        try:
            retry_count = int(row.get('retry_count', 0))
            retry_counts.append(retry_count)
        except (ValueError, TypeError):
            retry_counts.append(0)
    
    if retry_counts:
        avg_retry = sum(retry_counts) / len(retry_counts)
        # Format as "X.Xx" showing total attempts (retry_count + 1)
        total_attempts_avg = avg_retry + 1.0
        stats['retry_rate'] = f"{total_attempts_avg:.1f}x"
        
        # Type 11 specific metrics
        if data_type == 11:
            stats['type_11_complexity_factor'] = 'high'
            stats['institutional_data_sources'] = 3  # Foreign, Investment Trust, Proprietary
    else:
        stats['retry_rate'] = 'N/A'
    
    return stats
```

### Enhanced Command Line Options (v3.0.0)
```bash
python download_results_counts.py [OPTIONS]

Options:
  --output FILE         Save output to specific file
  --format FORMAT       Output format: table|enhanced-table|compact-badges|json (default: compact-badges)
  --detailed            Include additional metrics and timestamps
  --update-readme       Update README.md status section with 8-column table
  --plain              Disable badges (fallback mode with compact times)
  --show-oldest        Highlight folders with oldest data (for maintenance)
  --show-high-retry    Highlight folders with high retry rates
  --retry-threshold X   Set threshold for high retry rate alerts (default: 2.0, Type 11: 2.5)
  --type-11-focus      Show detailed Type 11 institutional data analysis
  --institutional-health Show Type 11 institutional data source health
  --help               Show help message
```

## Testing Strategy (v3.0.0)

### Unit Tests for Type 11 Support
```python
# Test Type 11 retry rate calculation with institutional data complexity
def test_type_11_retry_rate_calculation():
    # Type 11 may have higher acceptable retry rates
    assert calculate_retry_rate_display([0, 1, 2, 1], data_type=11) == "2.0x"
    assert get_retry_badge_color_enhanced("2.0x", data_type=11) == "green"  # Acceptable for Type 11
    assert get_retry_badge_color_enhanced("2.0x", data_type=1) == "yellow"   # Different for other types

# Test Type 11 folder handling
def test_type_11_folder_support():
    assert FOLDER_MAPPING[11] == "WeeklyTradingData"
    # Test CSV analysis for WeeklyTradingData folder
    # Test badge generation for Type 11 specific data
```

### Integration Tests for Complete 11-Type System
```python
# Test complete 11-data-type table generation
# Test README.md update with Type 11 support
# Test Type 11 institutional data health monitoring
# Test retry rate analysis across all 11 data types
```

## Type 11 Monitoring Features (NEW v3.0.0)

### Institutional Data Health Analysis
- **Multi-Source Validation**: Monitor foreign investor, investment trust, and proprietary trading data separately
- **Data Completeness Scoring**: Ensure all institutional flow components are present
- **Cross-Reference Validation**: Verify institutional data consistency across time periods

### Enhanced Reliability Metrics for Type 11
- **Institutional Data Threshold**: Higher acceptable retry rates (up to 2.5x) due to complexity
- **Data Source Dependency**: Monitor individual institutional data source reliability
- **Market Hours Correlation**: Analyze download success rates relative to Taiwan market hours

### Type 11 Specific Alerting
- **Institutional Data Gaps**: Alert when foreign investor or investment trust data is missing
- **Trading Data Inconsistencies**: Detect volume/price data mismatches
- **Extended Processing Times**: Monitor for Type 11 downloads exceeding expected durations

## Version History

### v3.0.0 Updates (NEW)
- **Added Type 11 Support** - Complete Weekly Trading Data with Institutional Flows monitoring
- **Enhanced 11-Data-Type Coverage** - Full support for all GoodInfo data types
- **Type 11 Specific Monitoring** - Specialized reliability thresholds for complex institutional data
- **Institutional Health Analysis** - Multi-source data validation for Type 11
- **Enhanced Documentation** - Complete Type 11 integration guidance
- **Advanced CLI Options** - Type 11 focused analysis and reporting tools

### v2.0.0 Features (Previous)
- Added Retry Rate Column - Monitor download reliability across all data types
- 8-Column Table Layout - Extended table structure with comprehensive retry monitoring
- Enhanced Reliability Monitoring - Visual indicators for problematic data types
- Maintenance Prioritization - Easily identify folders needing attention

### v1.9.0 Features (Base)
- Added Oldest Column for staleness monitoring
- Compact time formats for all time displays
- Enhanced time tracking with process_time vs last_update_time separation
- 7-column table layout with comprehensive time metrics

This enhanced design (v3.0.0) creates a comprehensive solution for monitoring both GoodInfo download status and reliability across all **11 data types**, with specialized support for Type 11's complex institutional flow data and enhanced reliability monitoring capabilities.