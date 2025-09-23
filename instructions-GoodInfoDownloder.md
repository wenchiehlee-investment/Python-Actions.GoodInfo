# Python-Actions.GoodInfo - Instructions for v1.9.0

## Project Overview
Create a comprehensive Taiwan stock data downloader for GoodInfo.tw with **11 data types**, automated GitHub Actions, and smart weekly + daily automation scheduling.

## Version 1.9.0 Features
- **11 Complete Data Types**: Added 週交易資料含三大法人 (Type 11) for comprehensive weekly trading data with institutional flows
- **Enhanced Automation**: Optimized weekly scheduling with additional Monday evening slot for complete market microstructure analysis
- **Complete Market Coverage**: All major GoodInfo.tw data sources now supported including detailed institutional trading flows
- **Advanced Special Workflows**: Enhanced handling for all complex data types
- **Full Documentation**: Usage examples for all 11 data types with detailed workflows

## File Structure to Generate

### 1. GetGoodInfo.py (v1.9.0.0)
**Purpose**: Main downloader script with Selenium automation

**Key Features**:
- Support for 11 data types (1-11)
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
    '10': ('equity_class_weekly', 'EquityDistributionClassHis', 'EquityDistributionClassHis.asp'),
    '11': ('weekly_trading_data', 'WeeklyTradingData', 'ShowK_Chart.asp')
}
```

**Special Workflows**:
- **Type 5**: Click "查20年" button → wait 5 seconds → XLS download
- **Type 7**: Navigate to quarterly view with special URL parameters → click "查60年" → wait 5 seconds → XLS download
- **Type 8**: Navigate to EPS x PER weekly view with RPT_CAT=PER → click "查5年" → wait 5 seconds → XLS download
- **Type 9**: Navigate to quarterly analysis page → wait 1 second → XLS download (standard workflow)
- **Type 10**: Navigate to equity distribution class histogram page → click "查5年" → wait 5 seconds → XLS download
- **Type 11**: Navigate to weekly trading data page with CHT_CAT=WEEK → click "查5年" → wait 5 seconds → XLS download

### 2. Actions.yaml (GitHub Actions Workflow)
**Purpose**: Automated weekly + daily downloads with enhanced scheduling

**Enhanced Weekly + Daily Schedule (v1.9.0)**:
- **Monday 8 AM UTC (4 PM Taiwan)**: Type 1 - Dividend Policy (Weekly)
- **Monday 2 PM UTC (10 PM Taiwan)**: Type 11 - Weekly Trading Data (Weekly) 🆕
- **Tuesday 8 AM UTC (4 PM Taiwan)**: Type 4 - Business Performance (Weekly)
- **Wednesday 8 AM UTC (4 PM Taiwan)**: Type 6 - Equity Distribution (Weekly)
- **Thursday 8 AM UTC (4 PM Taiwan)**: Type 7 - Quarterly Performance (Weekly)
- **Friday 8 AM UTC (4 PM Taiwan)**: Type 8 - EPS x PER Weekly (Weekly)
- **Saturday 8 AM UTC (4 PM Taiwan)**: Type 9 - Quarterly Analysis (Weekly)
- **Sunday 8 AM UTC (4 PM Taiwan)**: Type 10 - Equity Class Weekly (Weekly)
- **Daily 12 PM UTC (8 PM Taiwan)**: Type 5 - Monthly Revenue (Daily)

**Manual Trigger Support**: All 11 data types available on-demand

## Data Types Summary (v1.9.0) - Complete Weekly + Daily Schedule

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
| 10 | Equity Class Weekly | EquityDistributionClassHis | Sunday 8 AM UTC | Weekly | Click "查5年" |
| 11 | Weekly Trading Data | WeeklyTradingData | Monday 2 PM UTC | Weekly | Special URL + "查5年" 🆕 |

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
  3. Wait 5 seconds for data to load
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
  3. Wait 5 seconds for data to load
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
  3. Wait 5 seconds for data to load
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

### Data Type 10 - 股東持股分類(週)
- **URL Pattern**: `EquityDistributionClassHis.asp?STOCK_ID={stock_id}`
- **Folder**: `EquityDistributionClassHis/`
- **File Format**: `EquityDistributionClassHis_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to equity distribution class histogram page
  2. Click `查5年` button 
  3. Wait 5 seconds for data to load
  4. Click XLS download button
- **Content**: Weekly equity distribution class histogram data for 5-year period, shareholder classification trends
- **Automation**: Weekly (Sunday 8 AM UTC)

### Data Type 11 - 週交易資料含三大法人 🆕
- **URL Pattern**: `ShowK_Chart.asp?STOCK_ID={stock_id}&CHT_CAT=WEEK&PRICE_ADJ=F&SCROLL2Y=600`
- **Folder**: `WeeklyTradingData/`
- **File Format**: `WeeklyTradingData_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to weekly trading data page with CHT_CAT=WEEK parameters
  2. Click `查5年` button 
  3. Wait 5 seconds for data to load
  4. Click XLS download button
- **Content**: Comprehensive weekly trading data including OHLC prices, volume, institutional flows (外資/投信/自營), margin trading (融資/融券), and market microstructure analysis
- **Automation**: Weekly (Monday 2 PM UTC) 🆕

### GitHub Actions Enhancement (v1.9.0)
```yaml
# Enhanced Weekly Schedule with Type 11
schedule:
  # Weekly at 8 AM UTC (4 PM Taiwan) - Major data types
  - cron: '0 8 * * 1'   # Monday - Type 1 (Dividend Policy)
  - cron: '0 8 * * 2'   # Tuesday - Type 4 (Business Performance)
  - cron: '0 8 * * 3'   # Wednesday - Type 6 (Equity Distribution)
  - cron: '0 8 * * 4'   # Thursday - Type 7 (Quarterly Performance)
  - cron: '0 8 * * 5'   # Friday - Type 8 (EPS x PER Weekly)
  - cron: '0 8 * * 6'   # Saturday - Type 9 (Quarterly Analysis)
  - cron: '0 8 * * 0'   # Sunday - Type 10 (Equity Class Weekly)
  
  # Additional Monday slot for comprehensive trading data
  - cron: '0 14 * * 1'  # Monday 2 PM UTC - Type 11 (Weekly Trading Data) - NEW!
  
  # Daily at 12 PM UTC (8 PM Taiwan) - Time-sensitive data
  - cron: '0 12 * * *'  # Daily - Type 5 (Monthly Revenue)

# Manual workflow dispatch with all 11 data types
workflow_dispatch:
  inputs:
    data_type:
      description: 'Data Type to download (Complete 11 Data Types)'
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
        - '10' # Equity Class Weekly (Weekly - Sunday)
        - '11' # Weekly Trading Data (Weekly - Monday Evening) - NEW!
```

## Version History for v1.9.0
- ✅ **11 Complete Data Types** - Added Weekly Trading Data with Institutional Flows (Type 11) for comprehensive market microstructure analysis
- ✅ **Enhanced Automation** - Optimized weekly scheduling with additional Monday evening slot for complete coverage
- ✅ **Complete Market Coverage** - All major GoodInfo.tw data sources now covered including detailed institutional flows
- ✅ **Enhanced Documentation** - Complete usage examples and troubleshooting for all 11 data types
- ✅ **Institutional Analysis** - Comprehensive foreign investor, investment trust, and proprietary trading data

## Smart Automation Philosophy (v1.9.0)

### **Enhanced Weekly Coverage (8 AM UTC / 4 PM Taiwan + 2 PM UTC / 10 PM Taiwan)**
- **Types 1, 4, 6, 7, 8, 9, 10**: Major financial data distributed across 7-day week
- **Type 11**: Additional Monday evening slot for comprehensive trading data analysis
- **Optimal Timing**: Business day close for fresh data processing + evening for institutional flow analysis
- **Server-Friendly**: Enhanced distribution across week to prevent overload
- **Complete Coverage**: All major analysis types covered weekly with full institutional data

### **Daily Updates (12 PM UTC / 8 PM Taiwan)**
- **Type 5**: Monthly revenue data (most time-sensitive for investors)
- **Evening Timing**: After Taiwan market close for comprehensive revenue updates
- **High Priority**: Revenue data gets daily attention due to its importance

### **Manual Access (24/7)**
- **Types 2, 3**: Basic info and market details (rarely change, on-demand only)
- **All Types 1-11**: Available via manual triggers for immediate needs
- **Flexibility**: Complete control over data refresh timing when needed

## Quick Start for v1.9.0
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
   - `python GetGoodInfo.py 2330 10` (Equity Class Weekly - Sunday automation)
   - `python GetGoodInfo.py 2330 11` (Weekly Trading Data - Monday evening automation) 🆕
4. **Batch Processing**: `python GetAll.py 11 --test`
5. **GitHub Actions**: Automatically runs with enhanced weekly + daily schedule

## Expected Output Structure for v1.9.0
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
EquityDistributionClassHis/      # Type 10 - Weekly (Sunday)
WeeklyTradingData/               # Type 11 - Weekly (Monday Evening) 🆕
```

## Technical Implementation Notes

### Smart Scheduling Benefits for v1.9.0
- **Enhanced Coverage**: 11 data types with optimized weekly distribution including institutional analysis
- **Server Load**: Enhanced distribution prevents server overload with additional evening slot
- **Resource Efficiency**: Weekly updates for non-urgent data saves computational resources
- **Data Freshness**: Daily revenue updates + evening institutional flow analysis maintain critical information currency
- **Failure Recovery**: Enhanced distribution allows maximum time for retry mechanisms
- **Scalability**: Pattern accommodates complete data coverage including complex institutional analysis

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
    0) DATA_TYPE="10"; echo "Sunday: Equity Class Weekly Data" ;;
  esac
elif [[ "$HOUR" == "12" ]]; then
  DATA_TYPE="5"  # Daily - Monthly revenue data
  echo "Daily: Monthly Revenue Data"
elif [[ "$HOUR" == "14" && "$DAY_OF_WEEK" == "1" ]]; then
  DATA_TYPE="11"  # Monday Evening - Weekly trading data with institutional flows
  echo "Monday Evening: Weekly Trading Data with Institutional Flows [NEW!]"
fi
```

## Data Type 11 Detailed Specifications

### Column Structure (22 Data Columns + 6 Metadata Columns)
Based on `raw_column_definition.md`, Type 11 includes:

#### Trading Metadata (2 columns)
- `交易_週別`: Trading week identifier (YYYY-MM-DD format)
- `交易_日數`: Number of trading days in the week

#### OHLC Price Data (7 columns)
- `開盤_價格_元`: Week opening price (NT$)
- `最高_價格_元`: Week highest price (NT$)
- `最低_價格_元`: Week lowest price (NT$)
- `收盤_價格_元`: Week closing price (NT$)
- `漲跌_價格_元`: Price change from previous week (NT$)
- `漲跌_pct`: Price change percentage from previous week
- `振幅_pct`: Weekly price range percentage

#### Volume Data (2 columns)
- `成交_張數`: Total trading volume in lots
- `成交_金額_億`: Total turnover amount (hundred million NT$)

#### Institutional Trading (6 columns)
- `法人買賣超_千張`: Institutional net buying total (thousands of lots)
- `外資_淨買超_千張`: Foreign institutional investor net buying
- `投信_淨買超_千張`: Investment trust net buying
- `自營_淨買超_千張`: Proprietary trading net buying
- `法人_合計_千張`: Total institutional net buying
- `外資_持股_pct`: Foreign investor ownership percentage

#### Margin Trading (5 columns)
- `融資_增減_張`: Change in margin buying positions (lots)
- `融資_餘額_張`: Margin buying balance (lots)
- `融券_增減_張`: Change in short selling positions (lots)
- `融券_餘額_張`: Short selling balance (lots)
- `券資比_pct`: Short selling to margin buying ratio percentage

### Data Quality & Validation Rules
- **Price Consistency**: High ≥ Open, Close; Low ≤ Open, Close
- **Volume Validation**: Volume and turnover amount consistency
- **Institutional Sum Check**: Foreign + Investment Trust + Proprietary = Total
- **Percentage Validation**: All percentage fields within reasonable ranges
- **Margin Balance Logic**: Balance changes match reported increases/decreases

### Cross-Reference Integration Opportunities
- **Type 5 (Monthly Revenue)**: Compare institutional flows with revenue announcements
- **Type 8 (Weekly P/E Flow)**: Validate price data consistency across weekly sources
- **Type 10 (Weekly Equity Distribution)**: Cross-check foreign ownership percentages
- **Type 9 (Quarterly Historical)**: Quarterly aggregation validation

This creates a comprehensive, production-ready Taiwan stock data downloader with enhanced weekly + daily automation, full coverage of GoodInfo.tw data sources including the new Type 11 comprehensive weekly trading data with institutional flows, and server-friendly operation with optimized scheduling distribution.