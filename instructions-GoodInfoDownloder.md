# Python-Actions.GoodInfo - Instructions for v1.6.0

## Project Overview
Create a comprehensive Taiwan stock data downloader for GoodInfo.tw with 8 data types, automated GitHub Actions, and smart weekly + daily automation scheduling.

## Version 1.6.0 Features
- **8 Data Types**: Added EPS x PER Weekly (Type 8) to complete data coverage
- **Smart Weekly + Daily Automation**: Optimized scheduling with weekly updates for non-urgent data
- **Server-Friendly Operation**: Reduced from 6 daily runs to intelligent weekly pattern + daily revenue
- **Advanced Special Workflows**: Enhanced handling for complex data types with custom parameters
- **Complete Documentation**: Usage examples for all 8 data types with detailed workflows

## File Structure to Generate

### 1. GetGoodInfo.py (v1.6.0.0)
**Purpose**: Main downloader script with Selenium automation

**Key Features**:
- Support for 8 data types (1-8)
- CSV-based stock mapping with StockID_TWSE_TPEX.csv
- Selenium WebDriver with anti-bot detection
- Special workflows for complex data types
- Enhanced debug output with screenshots and HTML dumps

**Data Types Configuration**:
```python
DATA_TYPES = {
    '1': ('dividend', 'DividendDetail', 'StockDividendPolicy.asp'),
    '2': ('basic', 'BasicInfo', 'BasicInfo.asp'), 
    '3': ('detail', 'StockDetail', 'StockDetail.asp'),
    '4': ('performance', 'StockBzPerformance', 'StockBzPerformance.asp'),
    '5': ('revenue', 'ShowSaleMonChart', 'ShowSaleMonChart.asp'),
    '6': ('equity', 'EquityDistribution', 'EquityDistributionCatHis.asp'),
    '7': ('performance_quarter', 'StockBzPerformance1', 'StockBzPerformance.asp'),
    '8': ('eps_per_weekly', 'ShowK_ChartFlow', 'ShowK_ChartFlow.asp')
}
```

**Special Workflows**:
- **Type 5**: Click "查20年" button → wait 2 seconds → XLS download
- **Type 7**: Navigate to quarterly view with special URL parameters → click "查60年" → wait 2 seconds → XLS download
- **Type 8**: Navigate to EPS x PER weekly view with RPT_CAT=PER → click "查5年" → wait 2 seconds → XLS download

**Command Line Usage**:
```bash
python GetGoodInfo.py STOCK_ID DATA_TYPE
```

**Key Functions to Implement**:
- `load_stock_names_from_csv()`: Load stock mapping from CSV
- `selenium_download_xls()`: Main download function with Selenium
- Special handling for Type 5, 7, and 8 workflows
- Enhanced XLS element detection with multiple patterns
- Debug file generation (HTML + screenshots)

### 2. GetAll.py (Batch Processing Script)
**Purpose**: Process all stocks from CSV file in batch mode

**Features**:
- Read all stock IDs from StockID_TWSE_TPEX.csv
- Support for test mode (--test) - first 3 stocks only
- Debug mode (--debug) for detailed error messages
- Progress tracking with [current/total] format
- 1-second delay between requests for rate limiting (2 seconds for special workflows)
- UTF-8 encoding support for Windows/Linux

**Command Line Options**:
```bash
python GetAll.py DATA_TYPE [--test] [--debug] [--direct]
```

**Key Functions**:
- `read_stock_ids()`: Read CSV with multiple encoding support
- `run_get_good_info()`: Execute GetGoodInfo.py with proper error handling
- Summary statistics reporting

### 3. Get觀察名單.py (Stock List Downloader)
**Purpose**: Download latest Taiwan stock observation list from GitHub

**Features**:
- Download from GitHub repository: `https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv`
- Save as StockID_TWSE_TPEX.csv
- Handle encoding and network errors
- Automatic backup of existing files

### 4. Actions.yaml (GitHub Actions Workflow)
**Purpose**: Automated weekly + daily downloads with smart scheduling

**Smart Weekly + Daily Schedule (v1.6.0)**:
- **Monday 8 AM UTC (4 PM Taiwan)**: Type 1 - Dividend Policy (Weekly)
- **Tuesday 8 AM UTC (4 PM Taiwan)**: Type 4 - Business Performance (Weekly)
- **Wednesday 8 AM UTC (4 PM Taiwan)**: Type 6 - Equity Distribution (Weekly)
- **Thursday 8 AM UTC (4 PM Taiwan)**: Type 7 - Quarterly Performance (Weekly)
- **Friday 8 AM UTC (4 PM Taiwan)**: Type 8 - EPS x PER Weekly (Weekly) 🆕
- **Daily 12 PM UTC (8 PM Taiwan)**: Type 5 - Monthly Revenue (Daily)

**Manual Trigger Support**: All 8 data types available on-demand

**Key Workflow Steps**:
1. Checkout code and setup Python 3.9
2. Install dependencies from requirements.txt
3. Setup Chrome browser for Selenium
4. Download latest stock observation list
5. Determine execution parameters based on schedule/manual input
6. Run batch download with proper error handling
7. Commit and push results with detailed commit messages
8. Generate execution summary

**Enhanced Features**:
- Automatic stock list updates before each run
- Support for all 8 data types
- Intelligent weekly + daily scheduling based on data importance
- Test mode support for manual triggers
- Comprehensive file organization
- Detailed logging and progress tracking

### 5. requirements.txt
**Required Dependencies**:
```
selenium>=4.15.0
webdriver-manager>=4.0.0
pandas>=1.5.0
beautifulsoup4>=4.12.0
undetected-chromedriver>=3.5.0
requests>=2.31.0
```

### 6. README.md (v1.6.0)
**Enhanced Documentation** covering:
- All 8 data types with detailed descriptions
- Updated automation strategy for smart weekly + daily scheduling
- Complete usage examples for individual and batch downloads
- Enhanced GitHub Actions documentation with new schedule
- Comprehensive troubleshooting guide
- Special workflow documentation for advanced data types

## Implementation Guidelines

### Data Type 6 - Equity Distribution (股權結構)
- **URL Pattern**: `EquityDistributionCatHis.asp?STOCK_ID={stock_id}`
- **Folder**: `EquityDistribution/`
- **File Format**: `EquityDistribution_{stock_id}_{company_name}.xls`
- **Workflow**: Standard XLS download (click XLS button)
- **Content**: Shareholder structure, institutional holdings, ownership distribution
- **Automation**: Weekly (Wednesday 8 AM UTC)

### Data Type 7 - Quarterly Business Performance (每季經營績效)  
- **URL Pattern**: `StockBzPerformance.asp?STOCK_ID={stock_id}&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR`
- **Folder**: `StockBzPerformance1/`
- **File Format**: `StockBzPerformance1_{stock_id}_{company_name}_quarter.xls`
- **Special Workflow**: 
  1. Navigate to quarterly performance page with special parameters
  2. Click "查60年" button 
  3. Wait 2 seconds for data to load
  4. Click XLS download button
- **Content**: Quarterly financial performance, seasonal trends, YoY comparisons
- **Automation**: Weekly (Thursday 8 AM UTC)

### Data Type 8 - EPS x PER Weekly (每週EPS本益比) - NEW!
- **URL Pattern**: `ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID={stock_id}`
- **Folder**: `ShowK_ChartFlow/`
- **File Format**: `ShowK_ChartFlow_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to EPS x PER weekly page with special parameters
  2. Click "查5年" button 
  3. Wait 2 seconds for data to load
  4. Click XLS download button
- **Content**: Weekly EPS and P/E ratio data for 5-year period, technical analysis data
- **Automation**: Weekly (Friday 8 AM UTC) 🆕

### Enhanced Selenium Configuration
```python
# Add to selenium_download_xls() function
if data_type_code == '7':
    # Special URL for quarterly data
    url = f"https://goodinfo.tw/tw/{asp_file}?STOCK_ID={stock_id}&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR"
    
    # Look for "查60年" button
    sixty_year_patterns = [
        "//input[@value='查60年']",
        "//button[contains(text(), '查60年')]", 
        "//a[contains(text(), '查60年')]",
        "//*[contains(text(), '查60年')]"
    ]
    
elif data_type_code == '8':
    # Special URL for EPS x PER weekly data
    url = f"https://goodinfo.tw/tw/{asp_file}?RPT_CAT=PER&STOCK_ID={stock_id}"
    
    # Look for "查5年" button
    five_year_patterns = [
        "//input[@value='查5年']",
        "//button[contains(text(), '查5年')]", 
        "//a[contains(text(), '查5年')]",
        "//*[contains(text(), '查5年')]"
    ]
```

### GitHub Actions Enhancement (v1.6.0)
```yaml
# Smart Weekly + Daily Schedule
schedule:
  # Weekly at 8 AM UTC (4 PM Taiwan) - Major data types
  - cron: '0 8 * * 1'   # Monday - Type 1 (Dividend Policy)
  - cron: '0 8 * * 2'   # Tuesday - Type 4 (Business Performance)
  - cron: '0 8 * * 3'   # Wednesday - Type 6 (Equity Distribution)
  - cron: '0 8 * * 4'   # Thursday - Type 7 (Quarterly Performance)
  - cron: '0 8 * * 5'   # Friday - Type 8 (EPS x PER Weekly)
  
  # Daily at 12 PM UTC (8 PM Taiwan) - Time-sensitive data
  - cron: '0 12 * * *'  # Daily - Type 5 (Monthly Revenue)

# Manual workflow dispatch with all 8 data types
workflow_dispatch:
  inputs:
    data_type:
      description: 'Data Type to download (Complete 8 Data Types)'
      required: true
      default: '1'
      type: choice
      options:
        - '1'  # Dividend Policy (Weekly - Monday)
        - '2'  # Basic Info (Manual only)
        - '3'  # Stock Detail (Manual only)
        - '4'  # Business Performance (Weekly - Tuesday)
        - '5'  # Monthly Revenue (Daily)
        - '6'  # Equity Distribution (Weekly - Wednesday)
        - '7'  # Quarterly Performance (Weekly - Thursday)
        - '8'  # EPS x PER Weekly (Weekly - Friday) - NEW!
```

### Error Handling Enhancements
- Enhanced XLS element detection with 4 different search methods
- Debug file generation for failed downloads
- Special workflow error recovery for Types 5, 7, and 8
- Network timeout protection (60 seconds)
- Encoding detection for CSV files
- Button click retry mechanism for complex workflows

### Testing Strategy
- Use `--test` flag for testing with 3 stocks
- Manual workflow triggers for immediate testing
- Debug output for troubleshooting
- Screenshot capture for failed downloads
- Individual data type testing: `python GetGoodInfo.py 2330 8`

## Data Types Summary (v1.6.0) - Smart Weekly + Daily Schedule

| Type | Name | Folder | Schedule | Frequency | Special Workflow |
|------|------|--------|----------|-----------|------------------|
| 1 | Dividend Policy | DividendDetail | Monday 8 AM UTC | Weekly | Standard |
| 2 | Basic Info | BasicInfo | Manual Only | On-demand | Standard |
| 3 | Stock Detail | StockDetail | Manual Only | On-demand | Standard |
| 4 | Business Performance | StockBzPerformance | Tuesday 8 AM UTC | Weekly | Standard |
| 5 | Monthly Revenue | ShowSaleMonChart | Daily 12 PM UTC | Daily | Click "查20年" |
| 6 | Equity Distribution | EquityDistribution | Wednesday 8 AM UTC | Weekly | Standard |
| 7 | Quarterly Performance | StockBzPerformance1 | Thursday 8 AM UTC | Weekly | Special URL + "查60年" |
| 8 | EPS x PER Weekly | ShowK_ChartFlow | Friday 8 AM UTC | Weekly | Special URL + "查5年" 🆕 |

## Version History for v1.6.0
- ✅ **8 Complete Data Types** - Added EPS x PER Weekly (Type 8) for comprehensive technical analysis
- ✅ **Smart Weekly + Daily Automation** - Optimized scheduling with weekly pattern for major data types
- ✅ **Server-Friendly Operation** - Reduced server load with intelligent timing distribution
- ✅ **Advanced Special Workflows** - Enhanced handling for Types 5, 7, and 8 with custom parameters
- ✅ **Complete GitHub Actions** - Full automation support for all 8 data types with smart scheduling
- ✅ **Enhanced Error Handling** - Improved debug output and recovery mechanisms for complex workflows
- ✅ **Comprehensive Documentation** - Complete usage examples and troubleshooting for all 8 data types

## Smart Automation Philosophy (v1.6.0)

### **Weekly Updates (8 AM UTC / 4 PM Taiwan)**
- **Types 1, 4, 6, 7, 8**: Major financial data that doesn't require daily updates
- **Optimal Timing**: End of Taiwan business day for fresh data processing
- **Server-Friendly**: Distributed across weekdays to prevent overload
- **Complete Coverage**: All major analysis types covered weekly

### **Daily Updates (12 PM UTC / 8 PM Taiwan)**
- **Type 5**: Monthly revenue data (most time-sensitive for investors)
- **Evening Timing**: After Taiwan market close for comprehensive revenue updates
- **High Priority**: Revenue data gets daily attention due to its importance

### **Manual Access (24/7)**
- **Types 2, 3**: Basic info and market details (rarely change, on-demand only)
- **All Types**: Available via manual triggers for immediate needs
- **Flexibility**: Complete control over data refresh timing when needed

## Quick Start for v1.6.0
1. **Setup**: Clone repository and install dependencies
2. **Download Stock List**: `python Get觀察名單.py`
3. **Test All Data Types**: 
   - `python GetGoodInfo.py 2330 1` (Dividend Policy - Monday automation)
   - `python GetGoodInfo.py 2330 4` (Business Performance - Tuesday automation)
   - `python GetGoodInfo.py 2330 5` (Monthly Revenue - Daily automation)
   - `python GetGoodInfo.py 2330 6` (Equity Distribution - Wednesday automation)
   - `python GetGoodInfo.py 2330 7` (Quarterly Performance - Thursday automation)
   - `python GetGoodInfo.py 2330 8` (EPS x PER Weekly - Friday automation) 🆕
4. **Batch Processing**: `python GetAll.py 8 --test`
5. **GitHub Actions**: Automatically runs with smart weekly + daily schedule

## Expected Output Structure for v1.6.0
```
DividendDetail/          # Type 1 - Weekly (Monday)
BasicInfo/               # Type 2 - Manual only
StockDetail/             # Type 3 - Manual only  
StockBzPerformance/      # Type 4 - Weekly (Tuesday)
ShowSaleMonChart/        # Type 5 - Daily (most important)
EquityDistribution/      # Type 6 - Weekly (Wednesday)
StockBzPerformance1/     # Type 7 - Weekly (Thursday)
ShowK_ChartFlow/         # Type 8 - Weekly (Friday) 🆕
```

## Technical Implementation Notes

### Smart Scheduling Benefits
- **Server Load**: Reduced from 6 daily requests to intelligent weekly pattern + 1 daily
- **Resource Efficiency**: Weekly updates for non-urgent data saves computational resources
- **Data Freshness**: Daily revenue updates maintain critical information currency
- **Failure Recovery**: Distributed schedule allows more time for retry mechanisms
- **Scalability**: Pattern can accommodate additional data types without server overload

### Special Workflow Implementation for Type 8
```python
# In selenium_download_xls() function
if data_type_code == '8':
    # Navigate to EPS x PER weekly page
    url = f"https://goodinfo.tw/tw/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID={stock_id}"
    driver.get(url)
    
    # Wait for page to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    
    # Look for "查5年" button and click it
    five_year_button_found = False
    five_year_patterns = [
        "//input[@value='查5年']",
        "//button[contains(text(), '查5年')]",
        "//a[contains(text(), '查5年')]",
        "//*[contains(text(), '查5年')]"
    ]
    
    for pattern in five_year_patterns:
        try:
            button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, pattern))
            )
            button.click()
            five_year_button_found = True
            time.sleep(2)  # Wait for data to load
            break
        except:
            continue
    
    if not five_year_button_found:
        print(f"Warning: Could not find '查5年' button for {stock_id}")
```

### Automation Schedule Logic
```yaml
# In GitHub Actions determine parameters step
if [[ "$HOUR" == "08" ]]; then
  # 8 AM UTC - Weekly types based on day of week
  case $DAY_OF_WEEK in
    1) DATA_TYPE="1"; echo "Monday: Dividend Policy Data" ;;
    2) DATA_TYPE="4"; echo "Tuesday: Business Performance Data" ;;
    3) DATA_TYPE="6"; echo "Wednesday: Equity Distribution Data" ;;
    4) DATA_TYPE="7"; echo "Thursday: Quarterly Performance Data" ;;
    5) DATA_TYPE="8"; echo "Friday: EPS x PER Weekly Data [NEW!]" ;;
  esac
elif [[ "$HOUR" == "12" ]]; then
  DATA_TYPE="5"  # Daily - Monthly revenue data
  echo "Daily: Monthly Revenue Data"
fi
```

This creates a comprehensive, production-ready Taiwan stock data downloader with smart weekly + daily automation, complete coverage of GoodInfo.tw data sources, and server-friendly operation with the new EPS x PER Weekly data type for enhanced technical analysis capabilities.