# Python-Actions.GoodInfo - Instructions for v1.8.0

## Project Overview
Create a comprehensive Taiwan stock data downloader for GoodInfo.tw with **10 data types**, automated GitHub Actions, and smart weekly + daily automation scheduling.

## Version 1.8.0 Features
- **10 Complete Data Types**: Added 股東持股分級(週) (Type 10) for comprehensive weekly equity distribution analysis
- **Enhanced 7-Day Automation**: Extended smart scheduling with Sunday automation for complete weekly coverage
- **Complete Data Coverage**: All major GoodInfo.tw data sources now supported
- **Advanced Special Workflows**: Enhanced handling for all complex data types
- **Full Documentation**: Usage examples for all 10 data types with detailed workflows

## File Structure to Generate

### 1. GetGoodInfo.py (v1.8.0.0)
**Purpose**: Main downloader script with Selenium automation

**Key Features**:
- Support for 10 data types (1-10)
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
    '9': ('quarterly_analysis', 'StockHisAnaQuar', 'StockHisAnaQuar.asp'),
    '10': ('equity_class_weekly', 'EquityDistributionClassHis', 'EquityDistributionClassHis.asp')
}
```

**Special Workflows**:
- **Type 5**: Click "查20年" button → wait 2 seconds → XLS download
- **Type 7**: Navigate to quarterly view with special URL parameters → click "查60年" → wait 2 seconds → XLS download
- **Type 8**: Navigate to EPS x PER weekly view with RPT_CAT=PER → click "查5年" → wait 2 seconds → XLS download
- **Type 9**: Navigate to quarterly analysis page → wait 1 second → XLS download (standard workflow)
- **Type 10**: Navigate to equity distribution class histogram page → click "查5年" → wait 2 seconds → XLS download

### 2. Actions.yaml (GitHub Actions Workflow)
**Purpose**: Automated weekly + daily downloads with smart scheduling

**Enhanced 7-Day Weekly + Daily Schedule (v1.8.0)**:
- **Monday 8 AM UTC (4 PM Taiwan)**: Type 1 - Dividend Policy (Weekly)
- **Tuesday 8 AM UTC (4 PM Taiwan)**: Type 4 - Business Performance (Weekly)
- **Wednesday 8 AM UTC (4 PM Taiwan)**: Type 6 - Equity Distribution (Weekly)
- **Thursday 8 AM UTC (4 PM Taiwan)**: Type 7 - Quarterly Performance (Weekly)
- **Friday 8 AM UTC (4 PM Taiwan)**: Type 8 - EPS x PER Weekly (Weekly)
- **Saturday 8 AM UTC (4 PM Taiwan)**: Type 9 - Quarterly Analysis (Weekly)
- **Sunday 8 AM UTC (4 PM Taiwan)**: Type 10 - Equity Class Weekly (Weekly) 🆕
- **Daily 12 PM UTC (8 PM Taiwan)**: Type 5 - Monthly Revenue (Daily)

**Manual Trigger Support**: All 10 data types available on-demand

## Data Types Summary (v1.8.0) - Complete 7-Day Weekly + Daily Schedule

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
| 9 | Quarterly Analysis | StockHisAnaQuar | Saturday 8 AM UTC | Weekly | Standard |
| 10 | Equity Class Weekly | EquityDistributionClassHis | Sunday 8 AM UTC | Weekly | Click "查5年" 🆕 |

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
  2. Click `查5年` button 
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

### Data Type 10 - 股東持股分級(週) 🆕
- **URL Pattern**: `EquityDistributionClassHis.asp?STOCK_ID={stock_id}`
- **Folder**: `EquityDistributionClassHis/`
- **File Format**: `EquityDistributionClassHis_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to equity distribution class histogram page
  2. Click `查5年` button 
  3. Wait 2 seconds for data to load
  4. Click XLS download button
- **Content**: Weekly equity distribution class histogram data for 5-year period, shareholder classification trends
- **Automation**: Weekly (Sunday 8 AM UTC) 🆕

### GitHub Actions Enhancement (v1.8.0)
```yaml
# Complete 7-Day Weekly Schedule with Sunday
schedule:
  # Weekly at 8 AM UTC (4 PM Taiwan) - Major data types
  - cron: '0 8 * * 1'   # Monday - Type 1 (Dividend Policy)
  - cron: '0 8 * * 2'   # Tuesday - Type 4 (Business Performance)
  - cron: '0 8 * * 3'   # Wednesday - Type 6 (Equity Distribution)
  - cron: '0 8 * * 4'   # Thursday - Type 7 (Quarterly Performance)
  - cron: '0 8 * * 5'   # Friday - Type 8 (EPS x PER Weekly)
  - cron: '0 8 * * 6'   # Saturday - Type 9 (Quarterly Analysis)
  - cron: '0 8 * * 0'   # Sunday - Type 10 (Equity Class Weekly) - NEW!
  
  # Daily at 12 PM UTC (8 PM Taiwan) - Time-sensitive data
  - cron: '0 12 * * *'  # Daily - Type 5 (Monthly Revenue)

# Manual workflow dispatch with all 10 data types
workflow_dispatch:
  inputs:
    data_type:
      description: 'Data Type to download (Complete 10 Data Types)'
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
        - '9'  # Quarterly Analysis (Weekly - Saturday)
        - '10' # Equity Class Weekly (Weekly - Sunday) - NEW!
```

## Version History for v1.8.0
- ✅ **10 Complete Data Types** - Added Equity Distribution Class Weekly (Type 10) for comprehensive weekly shareholder analysis
- ✅ **Sunday Automation** - Extended smart weekly scheduling to include Sunday for complete 7-day coverage
- ✅ **Complete Weekly Coverage** - All major GoodInfo.tw data sources now covered across full week
- ✅ **Enhanced Documentation** - Complete usage examples and troubleshooting for all 10 data types
- ✅ **Perfect Load Distribution** - Balanced weekly distribution across 7 days with daily revenue tracking

## Smart Automation Philosophy (v1.8.0)

### **Complete Weekly Coverage (8 AM UTC / 4 PM Taiwan)**
- **Types 1, 4, 6, 7, 8, 9, 10**: Major financial data distributed across full 7-day week
- **Optimal Timing**: End of Taiwan business day for fresh data processing
- **Server-Friendly**: Perfect distribution across weekdays to prevent overload
- **Complete Coverage**: All major analysis types covered weekly with full week utilization

### **Daily Updates (12 PM UTC / 8 PM Taiwan)**
- **Type 5**: Monthly revenue data (most time-sensitive for investors)
- **Evening Timing**: After Taiwan market close for comprehensive revenue updates
- **High Priority**: Revenue data gets daily attention due to its importance

### **Manual Access (24/7)**
- **Types 2, 3**: Basic info and market details (rarely change, on-demand only)
- **All Types 1-10**: Available via manual triggers for immediate needs
- **Flexibility**: Complete control over data refresh timing when needed

## Quick Start for v1.8.0
1. **Setup**: Clone repository and install dependencies
2. **Download Stock List**: `python Get觀察名單.py`
3. **Test All Data Types**: 
   - `python GetGoodInfo.py 2330 1` (Dividend Policy - Monday automation)
   - `python GetGoodInfo.py 2330 4` (Business Performance - Tuesday automation)
   - `python GetGoodInfo.py 2330 5` (Monthly Revenue - Daily automation)
   - `python GetGoodInfo.py 2330 6` (Equity Distribution - Wednesday automation)
   - `python GetGoodInfo.py 2330 7` (Quarterly Performance - Thursday automation)
   - `python GetGoodInfo.py 2330 8` (EPS x PER Weekly - Friday automation)
   - `python GetGoodInfo.py 2330 9` (Quarterly Analysis - Saturday automation)
   - `python GetGoodInfo.py 2330 10` (Equity Class Weekly - Sunday automation) 🆕
4. **Batch Processing**: `python GetAll.py 10 --test`
5. **GitHub Actions**: Automatically runs with complete 7-day weekly + daily schedule

## Expected Output Structure for v1.8.0
```
DividendDetail/                   # Type 1 - Weekly (Monday)
BasicInfo/                        # Type 2 - Manual only
StockDetail/                      # Type 3 - Manual only  
StockBzPerformance/              # Type 4 - Weekly (Tuesday)
ShowSaleMonChart/                # Type 5 - Daily (most important)
EquityDistribution/              # Type 6 - Weekly (Wednesday)
StockBzPerformance1/             # Type 7 - Weekly (Thursday)
ShowK_ChartFlow/                 # Type 8 - Weekly (Friday)
StockHisAnaQuar/                 # Type 9 - Weekly (Saturday)
EquityDistributionClassHis/      # Type 10 - Weekly (Sunday) 🆕
```

## Technical Implementation Notes

### Smart Scheduling Benefits for v1.8.0
- **Complete Coverage**: 10 data types with perfect 7-day weekly distribution
- **Server Load**: Optimal distribution prevents server overload across full week
- **Resource Efficiency**: Weekly updates for non-urgent data saves computational resources
- **Data Freshness**: Daily revenue updates maintain critical information currency
- **Failure Recovery**: Full week distribution allows maximum time for retry mechanisms
- **Scalability**: Pattern accommodates complete data coverage without performance issues

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
    6) DATA_TYPE="9"; echo "Saturday: Quarterly Analysis Data" ;;
    0) DATA_TYPE="10"; echo "Sunday: Equity Class Weekly Data [NEW!]" ;;
  esac
elif [[ "$HOUR" == "12" ]]; then
  DATA_TYPE="5"  # Daily - Monthly revenue data
  echo "Daily: Monthly Revenue Data"
fi
```

This creates a comprehensive, production-ready Taiwan stock data downloader with complete 7-day weekly + daily automation, full coverage of GoodInfo.tw data sources including the new Type 10 equity distribution class weekly data, and server-friendly operation with optimal 7-day weekly distribution.