# Python-Actions.GoodInfo - Instructions for v1.5.0

## Project Overview
Create a comprehensive Taiwan stock data downloader for GoodInfo.tw with 7 data types, automated GitHub Actions, and enhanced quarterly performance support.

## Version 1.5.0 Features
- **7 Data Types**: Added Equity Distribution (Type 6) and Quarterly Business Performance (Type 7)
- **Enhanced GitHub Actions**: 5 daily runs with 1-hour intervals for optimal coverage
- **Improved Error Handling**: Better debug output and special workflow handling
- **Enhanced Documentation**: Complete usage examples for all data types

## File Structure to Generate

### 1. GetGoodInfo.py (v1.5.0.0)
**Purpose**: Main downloader script with Selenium automation

**Key Features**:
- Support for 7 data types (1-7)
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
    '7': ('performance_quarter', 'StockBzPerformance1', 'StockBzPerformance.asp')
}
```

**Special Workflows**:
- **Type 5**: Click "查20年" button → wait 2 seconds → XLS download
- **Type 7**: Navigate to quarterly view with special URL parameters → click "查60年" → wait 2 seconds → XLS download

**Command Line Usage**:
```bash
python GetGoodInfo.py STOCK_ID DATA_TYPE
```

**Key Functions to Implement**:
- `load_stock_names_from_csv()`: Load stock mapping from CSV
- `selenium_download_xls()`: Main download function with Selenium
- Special handling for Type 5 and Type 7 workflows
- Enhanced XLS element detection with multiple patterns
- Debug file generation (HTML + screenshots)

### 2. GetAll.py (Batch Processing Script)
**Purpose**: Process all stocks from CSV file in batch mode

**Features**:
- Read all stock IDs from StockID_TWSE_TPEX.csv
- Support for test mode (--test) - first 3 stocks only
- Debug mode (--debug) for detailed error messages
- Progress tracking with [current/total] format
- 1-second delay between requests for rate limiting
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
**Purpose**: Automated daily downloads with enhanced scheduling

**Enhanced Schedule (v1.5.0)**:
- **8 AM UTC (4 PM Taiwan)**: Type 1 - Dividend Policy (Daily)
- **9 AM UTC (5 PM Taiwan)**: Type 4 - Business Performance (Daily)  
- **10 AM UTC (6 PM Taiwan)**: Type 5 - Monthly Revenue (Daily)
- **11 AM UTC (7 PM Taiwan)**: Type 6 - Equity Distribution (Daily)
- **12 PM UTC (8 PM Taiwan)**: Type 7 - Quarterly Performance (Daily)

**Manual Trigger Support**: All 7 data types available on-demand

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
- Support for all 7 data types
- Intelligent scheduling based on data update frequency
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

### 6. README.md (v1.5.0)
**Enhanced Documentation** covering:
- All 7 data types with detailed descriptions
- Updated automation strategy for 5 scheduled runs
- Complete usage examples for individual and batch downloads
- Enhanced GitHub Actions documentation
- Weekly and monthly scheduling for new data types
- Comprehensive troubleshooting guide

## Implementation Guidelines

### Data Type 6 - Equity Distribution (股東結構)
- **URL Pattern**: `EquityDistributionCatHis.asp?STOCK_ID={stock_id}`
- **Folder**: `EquityDistribution/`
- **File Format**: `EquityDistribution_{stock_id}_{company_name}.xls`
- **Workflow**: Standard XLS download (click XLS button)
- **Content**: Shareholder structure, institutional holdings, ownership distribution

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
```

### GitHub Actions Enhancement
```yaml
# Add to schedule section
schedule:
  - cron: '0 8 * * *'   # Daily - Type 1 (Dividend)
  - cron: '0 9 * * *'   # Daily - Type 4 (Business Performance)  
  - cron: '0 10 * * *'  # Daily - Type 5 (Monthly Revenue)
  - cron: '0 11 * * *'  # Daily - Type 6 (Equity Distribution)
  - cron: '0 12 * * *'  # Daily - Type 7 (Quarterly Performance)
```

### Error Handling Enhancements
- Enhanced XLS element detection with 4 different search methods
- Debug file generation for failed downloads
- Special workflow error recovery for Types 5 and 7
- Network timeout protection (60 seconds)
- Encoding detection for CSV files

### Testing Strategy
- Use `--test` flag for testing with 3 stocks
- Manual workflow triggers for immediate testing
- Debug output for troubleshooting
- Screenshot capture for failed downloads

## Version History for v1.5.0
- ✅ **7 Complete Data Types** - Added Equity Distribution (Type 6) and Quarterly Performance (Type 7)
- ✅ **Enhanced Automation** - 5 scheduled runs with intelligent frequency-based timing
- ✅ **Special Workflows** - Advanced handling for quarterly data with URL parameters
- ✅ **Improved GitHub Actions** - Weekly and monthly scheduling for appropriate data types
- ✅ **Enhanced Error Handling** - Better debug output and recovery mechanisms
- ✅ **Complete Documentation** - Comprehensive usage examples for all 7 data types

## Quick Start for v1.5.0
1. **Setup**: Clone repository and install dependencies
2. **Download Stock List**: `python Get觀察名單.py`
3. **Test New Data Types**: 
   - `python GetGoodInfo.py 2330 6` (Equity Distribution)
   - `python GetGoodInfo.py 2330 7` (Quarterly Performance)
4. **Batch Processing**: `python GetAll.py 6 --test`
5. **GitHub Actions**: Automatically runs 5 times daily with 1-hour intervals

## Expected Output Structure for v1.5.0
```
DividendDetail/          # Type 1 - Daily updates
BasicInfo/               # Type 2 - Manual only
StockDetail/             # Type 3 - Manual only  
StockBzPerformance/      # Type 4 - Daily updates
ShowSaleMonChart/        # Type 5 - Daily updates
EquityDistribution/      # Type 6 - Weekly updates (NEW)
StockBzPerformance1/     # Type 7 - Monthly updates (NEW)
```

This creates a comprehensive, production-ready Taiwan stock data downloader with 5 daily automated runs and complete coverage of GoodInfo.tw data sources.