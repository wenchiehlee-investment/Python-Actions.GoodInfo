# Python-Actions.GoodInfo - Instructions for v1.7.0

## Project Overview
Create a comprehensive Taiwan stock data downloader for GoodInfo.tw with **9 data types**, automated GitHub Actions, and smart weekly + daily automation scheduling.

## Version 1.7.0 Features
- **9 Complete Data Types**: Added 各季詳細統計資料 (Type 9) for comprehensive quarterly analysis
- **Enhanced Weekly Automation**: Extended smart scheduling with Saturday automation
- **Complete Data Coverage**: All major GoodInfo.tw data sources now supported
- **Advanced Special Workflows**: Enhanced handling for all complex data types
- **Full Documentation**: Usage examples for all 9 data types with detailed workflows

## File Structure to Generate

### 1. GetGoodInfo.py (v1.7.0.0)
**Purpose**: Main downloader script with Selenium automation

**Key Features**:
- Support for 9 data types (1-9)
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
    '8': ('eps_per_weekly', 'ShowK_ChartFlow', 'ShowK_ChartFlow.asp'),
    '9': ('quarterly_analysis', 'StockHisAnaQuar', 'StockHisAnaQuar.asp')
}
```

**Special Workflows**:
- **Type 5**: Click "查20年" button → wait 2 seconds → XLS download
- **Type 7**: Navigate to quarterly view with special URL parameters → click "查60年" → wait 2 seconds → XLS download
- **Type 8**: Navigate to EPS x PER weekly view with RPT_CAT=PER → click "查5年" → wait 2 seconds → XLS download
- **Type 9**: Navigate to quarterly analysis page → wait 1 second → XLS download (standard workflow)

### 2. Actions.yaml (GitHub Actions Workflow)
**Purpose**: Automated weekly + daily downloads with smart scheduling

**Enhanced Weekly + Daily Schedule (v1.7.0)**:
- **Monday 8 AM UTC (4 PM Taiwan)**: Type 1 - Dividend Policy (Weekly)
- **Tuesday 8 AM UTC (4 PM Taiwan)**: Type 4 - Business Performance (Weekly)
- **Wednesday 8 AM UTC (4 PM Taiwan)**: Type 6 - Equity Distribution (Weekly)
- **Thursday 8 AM UTC (4 PM Taiwan)**: Type 7 - Quarterly Performance (Weekly)
- **Friday 8 AM UTC (4 PM Taiwan)**: Type 8 - EPS x PER Weekly (Weekly)
- **Saturday 8 AM UTC (4 PM Taiwan)**: Type 9 - Quarterly Analysis (Weekly) 🆕
- **Daily 12 PM UTC (8 PM Taiwan)**: Type 5 - Monthly Revenue (Daily)

**Manual Trigger Support**: All 9 data types available on-demand

## Data Types Summary (v1.7.0) - Enhanced Weekly + Daily Schedule

| Type | Name | Folder | Schedule | Frequency | Special Workflow |
|------|------|--------|----------|-----------|------------------|
| 1 | Dividend Policy | DividendDetail | Monday 8 AM UTC | Weekly | Standard |
| 2 | Basic Info | BasicInfo | Manual Only | On-demand | Standard |
| 3 | Stock Detail | StockDetail | Manual Only | On-demand | Standard |
| 4 | Business Performance | StockBzPerformance | Tuesday 8 AM UTC | Weekly | Standard |
| 5 | Monthly Revenue | ShowSaleMonChart | Daily 12 PM UTC | Daily | Click "查20年" |
| 6 | Equity Distribution | EquityDistribution | Wednesday 8 AM UTC | Weekly | Standard |
| 7 | Quarterly Performance | StockBzPerformance1 | Thursday 8 AM UTC | Weekly | Special URL + "查60年" |
| 8 | EPS x PER Weekly | ShowK_ChartFlow | Friday 8 AM UTC | Weekly | Special URL + "查5年" |
| 9 | Quarterly Analysis | StockHisAnaQuar | Saturday 8 AM UTC | Weekly | Standard 🆕 |

## Implementation Guidelines

### Data Type 1 - Dividend Policy (股利率政策)
- **URL Pattern**: `StockDividendPolicy.asp?STOCK_ID={stock_id}`
- **Folder**: `DividendDetail/`
- **File Format**: `DividendDetail_{stock_id}_{company_name}.xls`
- **Workflow**: Standard XLS download (click XLS button)
- **Content**: Historical dividend distributions, yield rates, payout ratios, cash dividends, stock dividends
- **Automation**: Weekly (Monday 8 AM UTC)

### Data Type 2 - Basic Info (基本資料)
- **URL Pattern**: `BasicInfo.asp?STOCK_ID={stock_id}`
- **Folder**: `BasicInfo/`
- **File Format**: `BasicInfo_{stock_id}_{company_name}.xls`
- **Workflow**: Find `公司基本資料` table and convert to XLS
- **Content**: Company fundamentals, industry classification, listing information, business description, capital structure
- **Automation**: Manual only (rarely changes)

### Data Type 3 - Stock Details (個股市況)
- **URL Pattern**: `StockDetail.asp?STOCK_ID={stock_id}`
- **Folder**: `StockDetail/`
- **File Format**: `StockDetail_{stock_id}_{company_name}.xls`
- **Workflow**: Standard XLS download (click XLS button)
- **Content**: Trading data, price movements, volume analysis, technical indicators, market statistics
- **Automation**: Manual only (real-time data)

### Data Type 4 - Business Performance (經營績效)
- **URL Pattern**: `StockBzPerformance.asp?STOCK_ID={stock_id}`
- **Folder**: `StockBzPerformance/`
- **File Format**: `StockBzPerformance_{stock_id}_{company_name}.xls`
- **Workflow**: Standard XLS download (click XLS button)
- **Content**: Financial performance metrics, profitability ratios, operational efficiency, ROE/ROA data
- **Automation**: Weekly (Tuesday 8 AM UTC)

### Data Type 5 - Monthly Revenue (每月營收)
- **URL Pattern**: `ShowSaleMonChart.asp?STOCK_ID={stock_id}`
- **Folder**: `ShowSaleMonChart/`
- **File Format**: `ShowSaleMonChart_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to monthly revenue page
  2. Click "查20年" button 
  3. Wait 2 seconds for data to load
  4. Click XLS download button
- **Content**: 20-year monthly revenue data, sales trends, growth patterns, YoY comparisons
- **Automation**: Daily (12 PM UTC automation) - Most time-sensitive

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

### Data Type 8 - EPS x PER Weekly (每週EPS本益比)
- **URL Pattern**: `ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID={stock_id}`
- **Folder**: `ShowK_ChartFlow/`
- **File Format**: `ShowK_ChartFlow_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to EPS x PER weekly page with special parameters
  2. Click "查5年" button 
  3. Wait 2 seconds for data to load
  4. Click XLS download button
- **Content**: Weekly EPS and P/E ratio data for 5-year period, technical analysis data
- **Automation**: Weekly (Friday 8 AM UTC)

### Data Type 9 - 各季詳細統計資料
- **URL Pattern**: `StockHisAnaQuar.asp?STOCK_ID={stock_id}`
- **Folder**: `StockHisAnaQuar/`
- **File Format**: `StockHisAnaQuar_{stock_id}_{company_name}.xls`
- **Workflow**: Standard XLS download (click XLS button)
- **Content**: 4-quarter detailed statistical data including stock price movements, trading volumes, seasonal performance patterns
- **Automation**: Weekly (Saturday 8 AM UTC)

### GitHub Actions Enhancement (v1.7.0)
```yaml
# Enhanced Weekly + Daily Schedule with Saturday
schedule:
  # Weekly at 8 AM UTC (4 PM Taiwan) - Major data types
  - cron: '0 8 * * 1'   # Monday - Type 1 (Dividend Policy)
  - cron: '0 8 * * 2'   # Tuesday - Type 4 (Business Performance)
  - cron: '0 8 * * 3'   # Wednesday - Type 6 (Equity Distribution)
  - cron: '0 8 * * 4'   # Thursday - Type 7 (Quarterly Performance)
  - cron: '0 8 * * 5'   # Friday - Type 8 (EPS x PER Weekly)
  - cron: '0 8 * * 6'   # Saturday - Type 9 (Quarterly Analysis) - NEW!
  
  # Daily at 12 PM UTC (8 PM Taiwan) - Time-sensitive data
  - cron: '0 12 * * *'  # Daily - Type 5 (Monthly Revenue)

# Manual workflow dispatch with all 9 data types
workflow_dispatch:
  inputs:
    data_type:
      description: 'Data Type to download (Complete 9 Data Types)'
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
        - '8'  # EPS x PER Weekly (Weekly - Friday)
        - '9'  # Quarterly Analysis (Weekly - Saturday) - NEW!
```

## Version History for v1.7.0
- ✅ **9 Complete Data Types** - Added Quarterly Analysis (Type 9) for comprehensive quarterly statistical analysis
- ✅ **Saturday Automation** - Extended smart weekly scheduling to include Saturday for Type 9
- ✅ **Complete Coverage** - All major GoodInfo.tw data sources now supported
- ✅ **Enhanced Documentation** - Complete usage examples and troubleshooting for all 9 data types
- ✅ **Optimized Scheduling** - Balanced weekly distribution across 6 days with daily revenue tracking

## Smart Automation Philosophy (v1.7.0)

### **Weekly Updates (8 AM UTC / 4 PM Taiwan)**
- **Types 1, 4, 6, 7, 8, 9**: Major financial data distributed across 6 weekdays
- **Optimal Timing**: End of Taiwan business day for fresh data processing
- **Server-Friendly**: Distributed across weekdays to prevent overload
- **Complete Coverage**: All major analysis types covered weekly

### **Daily Updates (12 PM UTC / 8 PM Taiwan)**
- **Type 5**: Monthly revenue data (most time-sensitive for investors)
- **Evening Timing**: After Taiwan market close for comprehensive revenue updates
- **High Priority**: Revenue data gets daily attention due to its importance

### **Manual Access (24/7)**
- **Types 2, 3**: Basic info and market details (rarely change, on-demand only)
- **All Types 1-9**: Available via manual triggers for immediate needs
- **Flexibility**: Complete control over data refresh timing when needed

## Quick Start for v1.7.0
1. **Setup**: Clone repository and install dependencies
2. **Download Stock List**: `python Get觀察名單.py`
3. **Test All Data Types**: 
   - `python GetGoodInfo.py 2330 1` (Dividend Policy - Monday automation)
   - `python GetGoodInfo.py 2330 4` (Business Performance - Tuesday automation)
   - `python GetGoodInfo.py 2330 5` (Monthly Revenue - Daily automation)
   - `python GetGoodInfo.py 2330 6` (Equity Distribution - Wednesday automation)
   - `python GetGoodInfo.py 2330 7` (Quarterly Performance - Thursday automation)
   - `python GetGoodInfo.py 2330 8` (EPS x PER Weekly - Friday automation)
   - `python GetGoodInfo.py 2330 9` (Quarterly Analysis - Saturday automation) 🆕
4. **Batch Processing**: `python GetAll.py 9 --test`
5. **GitHub Actions**: Automatically runs with enhanced weekly + daily schedule

## Expected Output Structure for v1.7.0
```
DividendDetail/          # Type 1 - Weekly (Monday)
BasicInfo/               # Type 2 - Manual only
StockDetail/             # Type 3 - Manual only  
StockBzPerformance/      # Type 4 - Weekly (Tuesday)
ShowSaleMonChart/        # Type 5 - Daily (most important)
EquityDistribution/      # Type 6 - Weekly (Wednesday)
StockBzPerformance1/     # Type 7 - Weekly (Thursday)
ShowK_ChartFlow/         # Type 8 - Weekly (Friday)
StockHisAnaQuar/         # Type 9 - Weekly (Saturday) 🆕
```

## 📊 Download Status Tracking (download_results.csv)

The system uses intelligent CSV-based tracking to monitor download progress and optimize batch processing efficiency across all 8 data types.

### 📍 Location and Structure

Each data type maintains its own tracking file:
```
DividendDetail/download_results.csv
BasicInfo/download_results.csv  
StockDetail/download_results.csv
StockBzPerformance/download_results.csv
ShowSaleMonChart/download_results.csv
EquityDistribution/download_results.csv
StockBzPerformance1/download_results.csv
ShowK_ChartFlow/download_results.csv
```

### 📋 CSV Format

**Header Structure:**
```csv
filename,last_update_time,success,process_time
```

**Column Definitions:**
- `filename`: Expected XLS filename based on stock ID and company name
- `last_update_time`: File modification timestamp when successfully downloaded, or `NEVER`
- `success`: `true` for successful downloads, `false` for failures
- `process_time`: When processing was attempted, or `NOT_PROCESSED` if never tried

### 📄 Example Content

```csv
filename,last_update_time,success,process_time
DividendDetail_2330_台積電.xls,2025-01-15 14:30:25,true,2025-01-15 14:30:23
DividendDetail_0050_元大台灣50.xls,NEVER,false,2025-01-15 14:32:10
DividendDetail_2454_聯發科.xls,2025-01-14 16:45:12,true,2025-01-14 16:45:10
DividendDetail_2317_鴻海.xls,NOT_PROCESSED,false,NOT_PROCESSED
```

### 🧠 Smart Processing Logic

The CSV enables intelligent batch processing with four strategies:

#### 1. PRIORITY Processing
**Triggers when:** Failed or unprocessed stocks exist
**Action:** Process only failed (`success=false`) and unprocessed stocks first
**Benefits:** Maximizes success rate by focusing on problematic stocks

#### 2. FULL_REFRESH Processing  
**Triggers when:** All stocks successful but data is old (not from today)
**Action:** Process all stocks to refresh outdated data
**Benefits:** Ensures data freshness across entire dataset

#### 3. UP_TO_DATE Status
**Triggers when:** All stocks successfully processed today
**Action:** Skip processing entirely
**Benefits:** Avoids unnecessary server load and API calls

#### 4. INITIAL_SCAN Processing
**Triggers when:** No CSV file exists
**Action:** Process all stocks to establish baseline
**Benefits:** Creates complete initial dataset

### 🔄 Update Mechanism

**Incremental Updates:** CSV is updated after each individual stock processing
**Progress Protection:** Never lose progress if batch job is interrupted
**Status Logic:**
- **Success:** `last_update_time` = actual file modification time
- **Failure:** `last_update_time` preserves previous value or remains `NEVER`
- **Process Time:** Always updated when processing is attempted

### 📁 Filename Generation Rules

**Standard Pattern:** `{folder}_{stock_id}_{company_name}.xls`
- Example: `DividendDetail_2330_台積電.xls`

**Special Cases:**
- **Type 7:** `StockBzPerformance1_{stock_id}_{company_name}_quarter.xls`
- Example: `StockBzPerformance1_2330_台積電_quarter.xls`

### 🎯 Usage Examples

**View Current Status:**
```bash
# Check dividend data status
cat DividendDetail/download_results.csv | head -5

# Count successful downloads
grep "true" DividendDetail/download_results.csv | wc -l

# Find failed downloads
grep "false" DividendDetail/download_results.csv
```

**Force Complete Refresh:**
```bash
# Delete CSV to trigger INITIAL_SCAN
rm DividendDetail/download_results.csv
python GetAll.py 1
```

**Manual CSV Analysis:**
```bash
# Show processing summary
echo "Total stocks: $(tail -n +2 DividendDetail/download_results.csv | wc -l)"
echo "Successful: $(grep -c 'true' DividendDetail/download_results.csv)"
echo "Failed: $(grep -c 'false' DividendDetail/download_results.csv)"
echo "Unprocessed: $(grep -c 'NOT_PROCESSED' DividendDetail/download_results.csv)"
```

### ⚡ Performance Benefits

**Efficiency Gains:**
- Skip recently successful downloads (saves ~80% processing time)
- Prioritize failed stocks (improves overall success rate)
- Resume interrupted batches (zero progress loss)
- Automatic retry logic (handles temporary failures)

**Resource Optimization:**
- Reduces server load on GoodInfo.tw
- Minimizes bandwidth usage
- Optimizes GitHub Actions runtime
- Prevents duplicate downloads

### 🔧 Advanced Features

**Smart Scheduling Integration:** CSV status influences GitHub Actions automation
**Error Recovery:** Failed downloads automatically queued for next run  
**Progress Visualization:** Clear success/failure tracking across all data types
**Batch Optimization:** Processes only necessary stocks per run

### 📈 Monitoring Tips

**Regular Checks:**
```bash
# Quick status overview
for folder in */download_results.csv; do
  echo "=== $(dirname $folder) ==="
  echo "Success: $(grep -c 'true' $folder)"
  echo "Failed: $(grep -c 'false' $folder)"
  echo ""
done
```

## Technical Implementation Notes

### Smart Scheduling Benefits for v1.7.0
- **Complete Coverage**: 9 data types with optimized 6-day weekly distribution
- **Server Load**: Balanced distribution prevents server overload
- **Resource Efficiency**: Weekly updates for non-urgent data saves computational resources
- **Data Freshness**: Daily revenue updates maintain critical information currency
- **Failure Recovery**: Distributed schedule allows more time for retry mechanisms
- **Scalability**: Pattern accommodates full data coverage without performance issues

### Automation Schedule Logic Enhancement
```yaml
# In GitHub Actions determine parameters step
if [[ "$HOUR" == "08" ]]; then
  # 8 AM UTC - Weekly types based on day of week
  case $DAY_OF_WEEK in
    1) DATA_TYPE="1"; echo "Monday: Dividend Policy Data" ;;
    2) DATA_TYPE="4"; echo "Tuesday: Business Performance Data" ;;
    3) DATA_TYPE="6"; echo "Wednesday: Equity Distribution Data" ;;
    4) DATA_TYPE="7"; echo "Thursday: Quarterly Performance Data" ;;
    5) DATA_TYPE="8"; echo "Friday: EPS x PER Weekly Data" ;;
    6) DATA_TYPE="9"; echo "Saturday: Quarterly Analysis Data [NEW!]" ;;
  esac
elif [[ "$HOUR" == "12" ]]; then
  DATA_TYPE="5"  # Daily - Monthly revenue data
  echo "Daily: Monthly Revenue Data"
fi
```

This creates a comprehensive, production-ready Taiwan stock data downloader with enhanced weekly + daily automation, complete coverage of GoodInfo.tw data sources including the new Type 9 quarterly analysis, and server-friendly operation with optimal 6-day weekly distribution.