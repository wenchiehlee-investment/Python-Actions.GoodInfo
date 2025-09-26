# Python-Actions.GoodInfo - Instructions for v2.0.0

## Project Overview
Create a comprehensive Taiwan stock data downloader for GoodInfo.tw with **12 data types**, automated GitHub Actions, and smart weekly + daily + monthly automation scheduling.

## Version 2.0.0 Features
- **12 Complete Data Types**: Added EPS x PER Monthly (Type 12) for comprehensive long-term valuation analysis with 20-year historical data
- **Enhanced Multi-Frequency Automation**: Optimized scheduling with weekly, daily, and monthly automation patterns
- **Complete Market Coverage**: All major GoodInfo.tw data sources now supported including detailed institutional trading flows and long-term valuation metrics
- **Advanced Special Workflows**: Enhanced handling for all complex data types with time-series variations
- **Full Documentation**: Usage examples for all 12 data types with detailed workflows and cross-reference integration

## File Structure to Generate

### 1. GetGoodInfo.py (v2.0.0.0)
**Purpose**: Main downloader script with Selenium automation

**Key Features**:
- Support for 12 data types (1-12)
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
    '11': ('weekly_trading_data', 'WeeklyTradingData', 'ShowK_Chart.asp'),
    '12': ('eps_per_monthly', 'ShowMonthlyK_ChartFlow', 'ShowK_ChartFlow.asp')
}
```

**Special Workflows**:
- **Type 5**: Click "查20年" button → wait 5 seconds → XLS download
- **Type 7**: Navigate to quarterly view with special URL parameters → click "查60年" → wait 5 seconds → XLS download
- **Type 8**: Navigate to EPS x PER weekly view with RPT_CAT=PER → click "查5年" → wait 5 seconds → XLS download
- **Type 9**: Navigate to quarterly analysis page → wait 1 second → XLS download (standard workflow)
- **Type 10**: Navigate to equity distribution class histogram page → click "查5年" → wait 5 seconds → XLS download
- **Type 11**: Navigate to weekly trading data page with CHT_CAT=WEEK → click "查5年" → wait 5 seconds → XLS download
- **Type 12**: Navigate to EPS x PER monthly view with CHT_CAT=MONTH → click "查20年" → wait 5 seconds → XLS download

### 2. Actions.yaml (GitHub Actions Workflow)
**Purpose**: Automated weekly + daily + monthly downloads with enhanced scheduling

**Enhanced Multi-Frequency Schedule (v2.0.0)**:
- **Monday 8 AM UTC (4 PM Taiwan)**: Type 1 - Dividend Policy (Weekly)
- **Monday 2 PM UTC (10 PM Taiwan)**: Type 11 - Weekly Trading Data (Weekly)
- **Tuesday 8 AM UTC (4 PM Taiwan)**: Type 4 - Business Performance (Weekly)
- **Tuesday 2 PM UTC (10 PM Taiwan)**: Type 12 - EPS x PER Monthly (Monthly - 1st Tuesday) 🆕
- **Wednesday 8 AM UTC (4 PM Taiwan)**: Type 6 - Equity Distribution (Weekly)
- **Thursday 8 AM UTC (4 PM Taiwan)**: Type 7 - Quarterly Performance (Weekly)
- **Friday 8 AM UTC (4 PM Taiwan)**: Type 8 - EPS x PER Weekly (Weekly)
- **Saturday 8 AM UTC (4 PM Taiwan)**: Type 9 - Quarterly Analysis (Weekly)
- **Sunday 8 AM UTC (4 PM Taiwan)**: Type 10 - Equity Class Weekly (Weekly)
- **Daily 12 PM UTC (8 PM Taiwan)**: Type 5 - Monthly Revenue (Daily)

**Manual Trigger Support**: All 12 data types available on-demand

## Data Types Summary (v2.0.0) - Complete Multi-Frequency Schedule

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
| 11 | Weekly Trading Data | WeeklyTradingData | Monday 2 PM UTC | Weekly | Special URL + "查5年" |
| 12 | EPS x PER Monthly | ShowMonthlyK_ChartFlow | 1st Tuesday 2 PM UTC | Monthly | Special URL + "查20年" 🆕 |

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

### Data Type 11 - 週交易資料含三大法人
- **URL Pattern**: `ShowK_Chart.asp?STOCK_ID={stock_id}&CHT_CAT=WEEK&PRICE_ADJ=F&SCROLL2Y=600`
- **Folder**: `WeeklyTradingData/`
- **File Format**: `WeeklyTradingData_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to weekly trading data page with CHT_CAT=WEEK parameters
  2. Click `查5年` button 
  3. Wait 5 seconds for data to load
  4. Click XLS download button
- **Content**: Comprehensive weekly trading data including OHLC prices, volume, institutional flows (外資/投信/自營), margin trading (融資/融券), and market microstructure analysis
- **Automation**: Weekly (Monday 2 PM UTC) 

### Data Type 12 - EPS x PER Monthly (每月EPS本益比) 🆕
- **URL Pattern**: `ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID={stock_id}&CHT_CAT=MONTH&SCROLL2Y=439`
- **Folder**: `ShowMonthlyK_ChartFlow/`
- **File Format**: `ShowMonthlyK_ChartFlow_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to EPS x PER monthly page with special parameters (CHT_CAT=MONTH)
  2. Click `查20年` button 
  3. Wait 5 seconds for data to load
  4. Click XLS download button
- **Content**: Monthly EPS and P/E ratio data for 20-year period with P/E target prices at 9X, 11X, 13X, 15X, 17X, 19X multiples, long-term valuation trends, technical analysis data with extended historical coverage
- **Automation**: Monthly (1st Tuesday 2 PM UTC)
- **Cross-Reference**: Complements Type 8 (weekly 5-year, 15X-30X multiples) with monthly perspective (20-year, 9X-19X multiples)

### GitHub Actions Enhancement (v2.0.0)
```yaml
# Enhanced Multi-Frequency Schedule with Type 12
schedule:
  # Weekly at 8 AM UTC (4 PM Taiwan) - Major data types
  - cron: '0 8 * * 1'   # Monday - Type 1 (Dividend Policy)
  - cron: '0 8 * * 2'   # Tuesday - Type 4 (Business Performance)
  - cron: '0 8 * * 3'   # Wednesday - Type 6 (Equity Distribution)
  - cron: '0 8 * * 4'   # Thursday - Type 7 (Quarterly Performance)
  - cron: '0 8 * * 5'   # Friday - Type 8 (EPS x PER Weekly)
  - cron: '0 8 * * 6'   # Saturday - Type 9 (Quarterly Analysis)
  - cron: '0 8 * * 0'   # Sunday - Type 10 (Equity Class Weekly)
  
  # Additional afternoon slots for specialized data
  - cron: '0 14 * * 1'  # Monday 2 PM UTC - Type 11 (Weekly Trading Data)
  - cron: '0 14 1-7 * 2' # First Tuesday 2 PM UTC - Type 12 (EPS x PER Monthly) - NEW!
  
  # Daily at 12 PM UTC (8 PM Taiwan) - Time-sensitive data
  - cron: '0 12 * * *'  # Daily - Type 5 (Monthly Revenue)

# Manual workflow dispatch with all 12 data types
workflow_dispatch:
  inputs:
    data_type:
      description: 'Data Type to download (Complete 12 Data Types)'
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
        - '11' # Weekly Trading Data (Weekly - Monday Evening)
        - '12' # EPS x PER Monthly (Monthly - First Tuesday) - NEW!
```

## Version History for v2.0.0
- ✅ **12 Complete Data Types** - Added EPS x PER Monthly (Type 12) for comprehensive long-term valuation analysis with 20-year historical data
- ✅ **Multi-Frequency Automation** - Optimized scheduling with weekly, daily, and monthly automation patterns
- ✅ **Complete Valuation Coverage** - Both weekly (5-year) and monthly (20-year) EPS/P/E analysis for comprehensive valuation modeling
- ✅ **Enhanced Documentation** - Complete usage examples and troubleshooting for all 12 data types with cross-reference integration
- ✅ **Long-Term Analysis** - Extended historical coverage for monthly valuation metrics supporting backtesting and trend analysis

## Smart Automation Philosophy (v2.0.0)

### **Enhanced Multi-Frequency Coverage**
- **Weekly (8 AM UTC / 4 PM Taiwan + 2 PM UTC / 10 PM Taiwan)**: Types 1, 4, 6, 7, 8, 9, 10, 11
- **Daily (12 PM UTC / 8 PM Taiwan)**: Type 5 (Monthly revenue - most time-sensitive)
- **Monthly (1st Tuesday 2 PM UTC / 10 PM Taiwan)**: Type 12 (Long-term valuation analysis) 🆕
- **Manual (24/7)**: Types 2, 3 (rarely changing data) + all types on-demand

### **Optimal Timing Strategy**
- **Business Day Close**: Fresh data processing after market close
- **Evening Slots**: Specialized data (institutional flows, long-term analysis)
- **Server-Friendly**: Distribution across time prevents overload
- **Complete Coverage**: All analysis frequencies covered with optimal resource allocation

### **Cross-Reference Integration (Enhanced for v2.0.0)**
- **Type 8 + Type 12**: Weekly vs Monthly EPS/P/E analysis for multi-timeframe valuation modeling
- **Type 5 + Type 11**: Revenue trends vs institutional flows correlation analysis
- **Type 6 + Type 10**: Equity distribution consistency validation across timeframes
- **Type 4 + Type 7**: Annual vs quarterly performance pattern analysis

## Quick Start for v2.0.0
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
   - `python GetGoodInfo.py 2330 11` (Weekly Trading Data - Monday evening automation)
   - `python GetGoodInfo.py 2330 12` (EPS x PER Monthly - Monthly automation) 🆕
4. **Batch Processing**: `python GetAll.py 12 --test`
5. **GitHub Actions**: Automatically runs with enhanced multi-frequency schedule

## Expected Output Structure for v2.0.0
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
WeeklyTradingData/               # Type 11 - Weekly (Monday Evening)
ShowMonthlyK_ChartFlow/          # Type 12 - Monthly (First Tuesday) 🆕
```

## Technical Implementation Notes

### Smart Scheduling Benefits for v2.0.0
- **Complete Frequency Coverage**: Weekly, daily, and monthly patterns optimized for different data types
- **Enhanced Valuation Analysis**: Both short-term (weekly) and long-term (monthly) P/E analysis
- **Server Load**: Multi-frequency distribution prevents server overload
- **Resource Efficiency**: Monthly updates for long-term data saves computational resources
- **Data Freshness**: Maintains critical information currency across all timeframes
- **Scalability**: Pattern accommodates complete temporal coverage

### Enhanced Automation Schedule Logic
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
  echo "Monday Evening: Weekly Trading Data with Institutional Flows"
elif [[ "$HOUR" == "14" && "$DAY_OF_WEEK" == "2" ]]; then
  # Monthly on first Tuesday
  DAY_OF_MONTH=$(date +%d)
  if [[ $DAY_OF_MONTH -le 7 ]]; then
    DATA_TYPE="12"  # Monthly - EPS x PER Monthly
    echo "Monthly: EPS x PER Monthly Data (First Tuesday) [NEW!]"
  fi
fi
```

## Data Type 12 Detailed Specifications

### Key Differentiators from Type 8
- **Timeframe**: Monthly vs Weekly granularity
- **Historical Coverage**: 20-year vs 5-year data depth
- **Analysis Purpose**: Long-term trend analysis vs short-term technical analysis
- **URL Parameters**: `CHT_CAT=MONTH` vs default weekly view
- **Button Action**: "查20年" vs "查5年" for extended historical coverage

### Monthly P/E Analysis Benefits
- **Long-Term Valuation Trends**: 20-year monthly data supports comprehensive valuation modeling
- **Seasonal Pattern Detection**: Monthly granularity reveals annual cyclical patterns
- **Backtesting Support**: Extended history enables robust strategy backtesting
- **Macro Correlation**: Monthly frequency aligns with economic indicator reporting
- **Portfolio Management**: Supports long-term investment decision making

### Cross-Reference Integration Opportunities
- **Type 8 + Type 12**: Multi-timeframe P/E analysis (5-year weekly + 20-year monthly)
- **Type 5 + Type 12**: Revenue seasonality vs P/E valuation patterns
- **Type 4 + Type 12**: Business performance correlation with long-term valuation
- **Type 1 + Type 12**: Dividend policy impact on long-term P/E trends

### Data Quality & Validation Rules
- **Consistency Check**: Monthly aggregations should align with weekly data in Type 8
- **P/E Ratio Validation**: Reasonable ranges and trend continuity
- **EPS Consistency**: Alignment with quarterly earnings data
- **Historical Integrity**: No data gaps in 20-year historical series
- **Cross-Validation**: Compare with other valuation metrics for consistency

This creates a comprehensive, production-ready Taiwan stock data downloader with enhanced multi-frequency automation (weekly/daily/monthly), complete coverage of GoodInfo.tw data sources including the new Type 12 long-term monthly valuation analysis, and optimized scheduling distribution for maximum efficiency and coverage.