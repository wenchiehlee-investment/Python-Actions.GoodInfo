# Python-Actions.GoodInfo - Instructions for v3.2.0

## Project Overview
Create a comprehensive Taiwan stock data downloader for GoodInfo.tw with **18 data types**, automated GitHub Actions, and smart weekly + daily + monthly automation scheduling.

## Version 3.2.0 Features
- **18 Complete Data Types**: Added Weekly K-Line Chart Flow (Type 17) and Daily K-Line Chart Flow (Type 18) for capital flow analysis
- **CSV-ONLY Freshness Policy**: Robust tracking based solely on CSV records (ignores file timestamps) for CI/CD compatibility
- **Enhanced Multi-Frequency Automation**: Optimized scheduling with weekly, daily, and monthly automation patterns
- **Complete Market Coverage**: All major GoodInfo.tw data sources now supported including detailed institutional trading flows, long-term valuation metrics, margin balance trends, and financial ratios
- **Advanced Special Workflows**: Enhanced handling for all complex data types with time-series variations and multi-block pagination
- **Full Documentation**: Usage examples for all 18 data types with detailed workflows and cross-reference integration

## File Structure to Generate

### 1. GetGoodInfo.py (v3.2.0.0)
**Purpose**: Main downloader script with Selenium automation

**Key Features**:
- Support for 18 data types (1-18)
- CSV-based stock mapping with StockID_TWSE_TPEX.csv
- Selenium WebDriver with anti-bot detection and 4-tier element search
- Special workflows for complex data types (pagination, special URLs)
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
    '12': ('eps_per_monthly', 'ShowMonthlyK_ChartFlow', 'ShowK_ChartFlow.asp'),
    '13': ('margin_balance', 'ShowMarginChart', 'ShowMarginChart.asp'),
    '14': ('margin_balance_weekly', 'ShowMarginChartWeek', 'ShowMarginChart.asp'),
    '15': ('margin_balance_monthly', 'ShowMarginChartMonth', 'ShowMarginChart.asp'),
    '16': ('quarterly_fin_ratio', 'StockFinDetail', 'StockFinDetail.asp'),
    '17': ('weekly_k_chartflow', 'ShowWeeklyK_ChartFlow', 'ShowK_ChartFlow.asp'),
    '18': ('daily_k_chartflow', 'ShowDailyK_ChartFlow', 'ShowK_ChartFlow.asp')
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
- **Type 13**: Navigate to Daily Margin Balance view with CHT_CAT=DATE → click "查1年" → wait 5 seconds → XLS download
- **Type 14**: Navigate to Weekly Margin Balance view with CHT_CAT=WEEK → click "查5年" → wait 5 seconds → XLS download
- **Type 15**: Navigate to Monthly Margin Balance view with CHT_CAT=MONTH → click "查20年" → wait 5 seconds → XLS download
- **Type 16**: Navigate to Quarterly Financial Ratio Analysis with RPT_CAT=XX_M_QUAR → wait 5 seconds → XLS download (supports multi-block pagination)
- **Type 17**: Navigate to Weekly K-Line Chart Flow page with CHT_CAT=WEEK → click "查5年" → wait 5 seconds → XLS download
- **Type 18**: Navigate to Daily K-Line Chart Flow page with CHT_CAT=DATE → click "查1年" → wait 5 seconds → XLS download

### 2. Actions.yaml (GitHub Actions Workflow)
**Purpose**: Automated weekly + daily + monthly downloads with enhanced scheduling

**Enhanced Slot-Based Schedule (v3.2.0)** - 2+ hour gaps between tasks:

**SLOT A: 06:00 UTC (14:00 Taiwan) - Weekly Types**
- **Tuesday 6 AM UTC (2 PM Taiwan)**: Type 4 - Business Performance (Weekly)
- **Wednesday 6 AM UTC (2 PM Taiwan)**: Type 6 - Equity Distribution (Weekly)
- **Thursday 6 AM UTC (2 PM Taiwan)**: Type 7 - Quarterly Performance (Weekly)
- **Friday 6 AM UTC (2 PM Taiwan)**: Type 8 - EPS x PER Weekly (Weekly)
- **Saturday 6 AM UTC (2 PM Taiwan)**: Type 9 - Quarterly Analysis (Weekly)
- **Sunday 6 AM UTC (2 PM Taiwan)**: Type 10 - Equity Class Weekly (Weekly)

**SLOT B: 10:00 UTC (18:00 Taiwan) - Daily Type 1**
- **Daily 10 AM UTC (6 PM Taiwan)**: Type 1 - Dividend Policy (Daily)

**SLOT C: 14:00 UTC (22:00 Taiwan) - Weekly/Monthly Evening**
- **Monday 2 PM UTC (10 PM Taiwan)**: Type 11 - Weekly Trading Data (Weekly)
- **Tuesday 2 PM UTC (10 PM Taiwan)**: Type 12 - EPS x PER Monthly (Monthly - 1st Tuesday)
- **Wednesday 2 PM UTC (10 PM Taiwan)**: Type 15 - Monthly Margin Balance (Monthly - 1st Wednesday)
- **Wednesday 2:10 PM UTC (10:10 PM Taiwan)**: Type 16 - Quarterly Financial Ratio Analysis (Monthly - 1st Wednesday)
- **Thursday 2 PM UTC (10 PM Taiwan)**: Type 17 - Weekly K-Line Chart Flow (Weekly) 🆕
- **Friday 2 PM UTC (10 PM Taiwan)**: Type 14 - Weekly Margin Balance (Weekly)

**SLOT D: 18:00 UTC (02:00 Taiwan+1) - Daily Type 5**
- **Daily 6 PM UTC (2 AM Taiwan+1)**: Type 5 - Monthly Revenue (Daily, Days 1,6-15,22)

**SLOT E: 22:00 UTC (06:00 Taiwan+1) - Daily Type 13**
- **Daily 10 PM UTC (6 AM Taiwan+1)**: Type 13 - Daily Margin Balance (Daily)

**SLOT F: 02:00 UTC (10:00 Taiwan) - Daily Type 18**
- **Daily 2 AM UTC (10 AM Taiwan)**: Type 18 - Daily K-Line Chart Flow (Daily) 🆕

**Manual Trigger Support**: All 18 data types available on-demand

## Data Types Summary (v3.2.0) - Slot-Based Schedule with 2+ Hour Gaps

| Type | Name | Folder | Slot | Schedule | Frequency | Special Workflow |
|------|------|--------|------|----------|-----------|------------------|
| 1 | Dividend Policy | DividendDetail | B | Daily 10 AM UTC | Daily | Standard |
| 2 | Basic Info | BasicInfo | - | Manual Only | On-demand | Standard |
| 3 | Stock Detail | StockDetail | - | Manual Only | On-demand | Standard |
| 4 | Business Performance | StockBzPerformance | A | Tuesday 6 AM UTC | Weekly | Standard |
| 5 | Monthly Revenue | ShowSaleMonChart | D | Daily 6 PM UTC | Daily | Click "查20年" |
| 6 | Equity Distribution | EquityDistribution | A | Wednesday 6 AM UTC | Weekly | Standard |
| 7 | Quarterly Performance | StockBzPerformance1 | A | Thursday 6 AM UTC | Weekly | Special URL + "查60年" |
| 8 | EPS x PER Weekly | ShowK_ChartFlow | A | Friday 6 AM UTC | Weekly | Special URL + "查5年" |
| 9 | Quarterly Analysis | StockHisAnaQuar | A | Saturday 6 AM UTC | Weekly | Standard |
| 10 | Equity Class Weekly | EquityDistributionClassHis | A | Sunday 6 AM UTC | Weekly | Click "查5年" |
| 11 | Weekly Trading Data | WeeklyTradingData | C | Monday 2 PM UTC | Weekly | Special URL + "查5年" |
| 12 | EPS x PER Monthly | ShowMonthlyK_ChartFlow | C | 1st Tuesday 2 PM UTC | Monthly | Special URL + "查20年" |
| 13 | Daily Margin Balance | ShowMarginChart | E | Daily 10 PM UTC | Daily | Special URL + "查1年" |
| 14 | Weekly Margin Balance | ShowMarginChartWeek | C | Friday 2 PM UTC | Weekly | Special URL + "查5年" |
| 15 | Monthly Margin Balance | ShowMarginChartMonth | C | 1st Wednesday 2 PM UTC | Monthly | Special URL + "查20年" |
| 16 | Quarterly Financial Ratio | StockFinDetail | C | 1st Wednesday 2:10 PM UTC | Monthly | Special URL + Wait 5s |
| 17 | Weekly K-Line Chart Flow | ShowWeeklyK_ChartFlow | C | Thursday 2 PM UTC | Weekly | Special URL + "查5年" 🆕 |
| 18 | Daily K-Line Chart Flow | ShowDailyK_ChartFlow | F | Daily 2 AM UTC | Daily | Special URL + "查1年" 🆕 |

## Implementation Guidelines

### Data Type 1 - Dividend Policy (股利率政策)
- **URL Pattern**: `StockDividendPolicy.asp?STOCK_ID={stock_id}`
- **Folder**: `DividendDetail/`
- **File Format**: `DividendDetail_{stock_id}_{company_name}.xls`
- **Workflow**: Standard XLS download (click XLS button)
- **Content**: Historical dividend distributions, yield rates, payout ratios, cash dividends, stock dividends
- **Automation**: SLOT B - Daily (10:00 UTC / 18:00 Taiwan)

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
- **Automation**: SLOT A - Weekly (Tuesday 06:00 UTC / 14:00 Taiwan)

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
- **Automation**: SLOT D - Daily (18:00 UTC / 02:00 Taiwan+1) - Most time-sensitive

### Data Type 6 - Equity Distribution (股權結構)
- **URL Pattern**: `EquityDistributionCatHis.asp?STOCK_ID={stock_id}`
- **Folder**: `EquityDistribution/`
- **File Format**: `EquityDistribution_{stock_id}_{company_name}.xls`
- **Workflow**: Standard XLS download (click XLS button)
- **Content**: Shareholder structure, institutional holdings, ownership distribution
- **Automation**: SLOT A - Weekly (Wednesday 06:00 UTC / 14:00 Taiwan)

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
- **Automation**: SLOT A - Weekly (Thursday 06:00 UTC / 14:00 Taiwan)

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
- **Automation**: SLOT A - Weekly (Friday 06:00 UTC / 14:00 Taiwan)

### Data Type 9 - 各季詳細統計資料
- **URL Pattern**: `StockHisAnaQuar.asp?STOCK_ID={stock_id}`
- **Folder**: `StockHisAnaQuar/`
- **File Format**: `StockHisAnaQuar_{stock_id}_{company_name}.xls`
- **Workflow**: Standard XLS download (click XLS button)
- **Content**: 4-quarter detailed statistical data including stock price movements, trading volumes, seasonal performance patterns
- **Automation**: SLOT A - Weekly (Saturday 06:00 UTC / 14:00 Taiwan)

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
- **Automation**: SLOT A - Weekly (Sunday 06:00 UTC / 14:00 Taiwan)

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
- **Automation**: SLOT C - Weekly (Monday 14:00 UTC / 22:00 Taiwan) 

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
- **Automation**: SLOT C - Monthly (1st Tuesday 14:00 UTC / 22:00 Taiwan)
- **Cross-Reference**: Complements Type 8 (weekly 5-year, 15X-30X multiples) with monthly perspective (20-year, 9X-19X multiples)

### Data Type 13 - Daily Margin Balance (每日融資融券餘額詳細資料) 🆕
- **URL Pattern**: `ShowMarginChart.asp?STOCK_ID={stock_id}&CHT_CAT=DATE`
- **Folder**: `ShowMarginChart/`
- **File Format**: `ShowMarginChart_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to Daily Margin Balance page with special parameters (CHT_CAT=DATE)
  2. Click `查1年` button 
  3. Wait 5 seconds for data to load
  4. Click XLS download button
- **Content**: Daily margin balance details including financing buy/sell, short selling, margin usage rate, maintenance rate, and market sentiment indicators
- **Automation**: SLOT E - Daily (22:00 UTC / 06:00 Taiwan+1)
- **Cross-Reference**: Complements Type 11 (weekly trading data) with granular daily margin statistics

### Data Type 14 - Weekly Margin Balance (每周融資融券餘額詳細資料) 🆕
- **URL Pattern**: `ShowMarginChart.asp?STOCK_ID={stock_id}&PRICE_ADJ=F&CHT_CAT=WEEK&SCROLL2Y=500`
- **Folder**: `ShowMarginChartWeek/`
- **File Format**: `ShowMarginChartWeek_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to Weekly Margin Balance page with special parameters (CHT_CAT=WEEK)
  2. Click `查5年` button 
  3. Wait 5 seconds for data to load
  4. Click XLS download button
- **Content**: Weekly aggregated margin balance, 5-year history
- **Automation**: SLOT C - Weekly (Friday 14:00 UTC / 22:00 Taiwan)

### Data Type 15 - Monthly Margin Balance (每月融資融券餘額詳細資料) 🆕
- **URL Pattern**: `ShowMarginChart.asp?STOCK_ID={stock_id}&PRICE_ADJ=F&CHT_CAT=MONTH&SCROLL2Y=400`
- **Folder**: `ShowMarginChartMonth/`
- **File Format**: `ShowMarginChartMonth_{stock_id}_{company_name}.xls`
- **Special Workflow**: 
  1. Navigate to Monthly Margin Balance page with special parameters (CHT_CAT=MONTH)
  2. Click `查20年` button 
  3. Wait 5 seconds for data to load
  4. Click XLS download button
- **Content**: Monthly aggregated margin balance, 20-year history
- **Automation**: SLOT C - Monthly (1st Wednesday 14:00 UTC / 22:00 Taiwan)

### Data Type 16 - Quarterly Financial Ratio Analysis (單季財務比率表詳細資料)
- **URL Pattern**: `StockFinDetail.asp?RPT_CAT=XX_M_QUAR&STOCK_ID={stock_id}`
- **Folder**: `StockFinDetail/`
- **File Format**: `StockFinDetail_{stock_id}_{company_name}.xls`
- **Special Workflow**:
  1. Navigate to Quarterly Financial Ratio Analysis page with special parameters
  2. Wait 5 seconds for data to load
  3. Click XLS download button
  4. Supports multi-block pagination for full history (merged into one transposed XLS)
- **Content**: Quarterly Financial Ratio Analysis, latest 10-quarter data (profitability, efficiency, leverage)
- **Automation**: SLOT C - Monthly (1st Wednesday 14:10 UTC / 22:10 Taiwan)

### Data Type 17 - Weekly K-Line Chart Flow (週K線圖資金流向) 🆕
- **URL Pattern**: `ShowK_ChartFlow.asp?STOCK_ID={stock_id}&CHT_CAT=WEEK&PRICE_ADJ=F&SCROLL2Y=500`
- **Folder**: `ShowWeeklyK_ChartFlow/`
- **File Format**: `ShowWeeklyK_ChartFlow_{stock_id}_{company_name}.xls`
- **Special Workflow**:
  1. Navigate to Weekly K-Line Chart Flow page with CHT_CAT=WEEK parameters
  2. Click `查5年` button
  3. Wait 5 seconds for data to load
  4. Click XLS download button
- **Content**: 5-year weekly K-Line chart with capital flow data, institutional capital flow trends, weekly price and volume patterns
- **Automation**: SLOT C - Weekly (Thursday 14:00 UTC / 22:00 Taiwan)
- **Cross-Reference**: Complements Type 8 (EPS x PER Weekly) and Type 18 (Daily K-Line Chart Flow)

### Data Type 18 - Daily K-Line Chart Flow (日K線圖資金流向) 🆕
- **URL Pattern**: `ShowK_ChartFlow.asp?STOCK_ID={stock_id}&CHT_CAT=DATE&PRICE_ADJ=F&SCROLL2Y=500`
- **Folder**: `ShowDailyK_ChartFlow/`
- **File Format**: `ShowDailyK_ChartFlow_{stock_id}_{company_name}.xls`
- **Special Workflow**:
  1. Navigate to Daily K-Line Chart Flow page with CHT_CAT=DATE parameters
  2. Click `查1年` button
  3. Wait 5 seconds for data to load
  4. Click XLS download button
- **Content**: 1-year daily K-Line chart with capital flow data, daily capital flow tracking, short-term price momentum analysis
- **Automation**: SLOT F - Daily (02:00 UTC / 10:00 Taiwan)
- **Cross-Reference**: Complements Type 17 (Weekly K-Line Chart Flow) for multi-timeframe capital flow analysis

### GitHub Actions Enhancement (v3.2.0) - Slot-Based Schedule
```yaml
# Slot-Based Schedule with 2+ Hour Gaps (v3.2.0)
schedule:
  # SLOT A: 06:00 UTC (14:00 Taiwan) - Weekly Types
  - cron: '0 6 * * 2'   # Tuesday - Type 4 (Business Performance)
  - cron: '0 6 * * 3'   # Wednesday - Type 6 (Equity Distribution)
  - cron: '0 6 * * 4'   # Thursday - Type 7 (Quarterly Performance)
  - cron: '0 6 * * 5'   # Friday - Type 8 (EPS x PER Weekly)
  - cron: '0 6 * * 6'   # Saturday - Type 9 (Quarterly Analysis)
  - cron: '0 6 * * 0'   # Sunday - Type 10 (Equity Class Weekly)

  # SLOT B: 10:00 UTC (18:00 Taiwan) - Type 1 Daily
  - cron: '0 10 * * *'  # Daily - Type 1 (Dividend Policy)

  # SLOT C: 14:00 UTC (22:00 Taiwan) - Weekly/Monthly Evening
  - cron: '0 14 * * 1'  # Monday 2 PM UTC - Type 11 (Weekly Trading Data)
  - cron: '0 14 1-7 * 2' # First Tuesday 2 PM UTC - Type 12 (EPS x PER Monthly)
  - cron: '0 14 1-7 * 3' # First Wednesday 2 PM UTC - Type 15 (Monthly Margin Balance)
  - cron: '10 14 1-7 * 3' # First Wednesday 2:10 PM UTC - Type 16 (Quarterly Fin Ratio)
  - cron: '0 14 * * 4'  # Thursday 2 PM UTC - Type 17 (Weekly K-Line Chart Flow) - NEW!
  - cron: '0 14 * * 5'  # Friday 2 PM UTC - Type 14 (Weekly Margin Balance)

  # SLOT D: 18:00 UTC (02:00 Taiwan+1) - Type 5 Daily
  - cron: '0 18 6-15 * *'   # Days 6-15 - Type 5 (Monthly Revenue)
  - cron: '0 18 1,22 * *'   # Days 1 & 22 - Type 5 (Monthly Revenue)

  # SLOT E: 22:00 UTC (06:00 Taiwan+1) - Type 13 Daily
  - cron: '0 22 * * *'  # Daily - Type 13 (Daily Margin Balance)

  # SLOT F: 02:00 UTC (10:00 Taiwan) - Type 18 Daily
  - cron: '0 2 * * *'   # Daily - Type 18 (Daily K-Line Chart Flow) - NEW!

# Manual workflow dispatch with all 18 data types
workflow_dispatch:
  inputs:
    data_type:
      description: 'Data Type to download (Complete 18 Data Types)'
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
        - '12' # EPS x PER Monthly (Monthly - First Tuesday)
        - '13' # Daily Margin Balance (Daily - Evening)
        - '14' # Weekly Margin Balance (Weekly - Friday Evening)
        - '15' # Monthly Margin Balance (Monthly - First Wednesday)
        - '16' # Quarterly Financial Ratio (Monthly - First Wednesday)
        - '17' # Weekly K-Line Chart Flow (Weekly - Thursday Evening) - NEW!
        - '18' # Daily K-Line Chart Flow (Daily - Midnight) - NEW!
```

## Version History for v3.2.0
- ✅ **18 Complete Data Types** - Added Weekly K-Line Chart Flow (Type 17) and Daily K-Line Chart Flow (Type 18)
- ✅ **Capital Flow Analysis** - Weekly and daily K-Line chart with capital flow data for multi-timeframe analysis
- ✅ **CSV-ONLY Freshness Policy** - Switched to reliable CSV-record based freshness tracking
- ✅ **Multi-Frequency Automation** - Optimized scheduling with weekly, daily, and monthly automation patterns
- ✅ **Complete Valuation & Sentiment Coverage** - P/E analysis plus multi-timeframe margin sentiment tracking
- ✅ **Enhanced Documentation** - Complete usage examples and troubleshooting for all 18 data types
- ✅ **Long-Term & Short-Term Analysis** - From 20-year monthly trends to daily capital flow changes

## Smart Automation Philosophy (v3.2.0)

### **Slot-Based Schedule with 2+ Hour Gaps**
- **SLOT A (06:00 UTC / 14:00 Taiwan)**: Types 4, 6, 7, 8, 9, 10 (Weekly)
- **SLOT B (10:00 UTC / 18:00 Taiwan)**: Type 1 (Daily)
- **SLOT C (14:00 UTC / 22:00 Taiwan)**: Types 11, 14, 17 (Weekly) + Types 12, 15, 16 (Monthly)
- **SLOT D (18:00 UTC / 02:00 Taiwan+1)**: Type 5 (Daily)
- **SLOT E (22:00 UTC / 06:00 Taiwan+1)**: Type 13 (Daily)
- **SLOT F (02:00 UTC / 10:00 Taiwan)**: Type 18 (Daily) 🆕
- **Manual (24/7)**: Types 2, 3 (rarely changing data) + all types on-demand

### **Optimal Timing Strategy**
- **2+ Hour Gaps**: Each slot separated by 4 hours to accommodate 1-1.5 hour task duration
- **Business Day Close**: Fresh data processing after market close
- **Evening Slots**: Specialized data (institutional flows, long-term analysis)
- **No Conflicts**: Slot-based design eliminates schedule overlap
- **Complete Coverage**: All 18 data types with comprehensive scheduling

### **Cross-Reference Integration (Enhanced for v3.2.0)**
- **Type 8 + Type 12**: Weekly vs Monthly EPS/P/E analysis for multi-timeframe valuation modeling
- **Type 5 + Type 11**: Revenue trends vs institutional flows correlation analysis
- **Type 13 + Type 14 + Type 15**: Daily vs Weekly vs Monthly margin sentiment analysis
- **Type 6 + Type 10**: Equity distribution consistency validation across timeframes
- **Type 4 + Type 7 + Type 16**: Annual vs quarterly performance vs ratio analysis
- **Type 17 + Type 18**: Weekly vs Daily K-Line chart capital flow analysis for multi-timeframe momentum 🆕

## Quick Start for v3.2.0
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
   - `python GetGoodInfo.py 2330 12` (EPS x PER Monthly - Monthly automation)
   - `python GetGoodInfo.py 2330 13` (Daily Margin Balance - Daily automation)
   - `python GetGoodInfo.py 2330 14` (Weekly Margin Balance - Weekly automation)
   - `python GetGoodInfo.py 2330 15` (Monthly Margin Balance - Monthly automation)
   - `python GetGoodInfo.py 2330 16` (Quarterly Financial Ratio - Monthly automation)
   - `python GetGoodInfo.py 2330 17` (Weekly K-Line Chart Flow - Weekly automation) 🆕
   - `python GetGoodInfo.py 2330 18` (Daily K-Line Chart Flow - Daily automation) 🆕
4. **Batch Processing (CSV-ONLY)**: `python GetAll.py 18 --test`
5. **GitHub Actions**: Automatically runs with enhanced multi-frequency schedule

## Expected Output Structure for v3.2.0 (Slot-Based)
```
DividendDetail/                   # Type 1 - SLOT B (Daily 10:00 UTC)
BasicInfo/                        # Type 2 - Manual only
StockDetail/                      # Type 3 - Manual only
StockBzPerformance/              # Type 4 - SLOT A (Tuesday 06:00 UTC)
ShowSaleMonChart/                # Type 5 - SLOT D (Daily 18:00 UTC)
EquityDistribution/              # Type 6 - SLOT A (Wednesday 06:00 UTC)
StockBzPerformance1/             # Type 7 - SLOT A (Thursday 06:00 UTC)
ShowK_ChartFlow/                 # Type 8 - SLOT A (Friday 06:00 UTC)
StockHisAnaQuar/                 # Type 9 - SLOT A (Saturday 06:00 UTC)
EquityDistributionClassHis/      # Type 10 - SLOT A (Sunday 06:00 UTC)
WeeklyTradingData/               # Type 11 - SLOT C (Monday 14:00 UTC)
ShowMonthlyK_ChartFlow/          # Type 12 - SLOT C (1st Tuesday 14:00 UTC)
ShowMarginChart/                 # Type 13 - SLOT E (Daily 22:00 UTC)
ShowMarginChartWeek/             # Type 14 - SLOT C (Friday 14:00 UTC)
ShowMarginChartMonth/            # Type 15 - SLOT C (1st Wednesday 14:00 UTC)
StockFinDetail/                  # Type 16 - SLOT C (1st Wednesday 14:10 UTC)
ShowWeeklyK_ChartFlow/           # Type 17 - SLOT C (Thursday 14:00 UTC) 🆕
ShowDailyK_ChartFlow/            # Type 18 - SLOT F (Daily 02:00 UTC) 🆕
```

## Data Type 16 Detailed Specifications

### Key Differentiators
- **Timeframe**: Quarterly
- **Historical Depth**: Latest 10 quarters
- **Focus**: Fundamental ratio analysis
- **Indicators**: ROE, ROA, Gross Margin, Net Profit Margin, Debt Ratio, Turnover Ratios

### Financial Ratio Benefits
- **Fundamentals Tracking**: Verify financial health trends
- **Profitability Analysis**: Monitor margin expansion/contraction
- **Efficiency Metrics**: Asset turnover and inventory management
- **Solvency Check**: Debt levels and interest coverage

This creates a comprehensive, production-ready Taiwan stock data downloader with enhanced multi-frequency automation (weekly/daily/monthly), complete coverage of GoodInfo.tw data sources including Type 12/15 long-term analysis, Type 13/14 sentiment tracking, Type 16 fundamental ratios, and the new Type 17/18 K-Line chart capital flow analysis, optimized scheduling distribution for maximum efficiency and coverage.
