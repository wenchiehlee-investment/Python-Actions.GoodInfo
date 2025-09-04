# Python-Actions.GoodInfo - GoodInfo.tw XLS Downloader

🚀 Automated XLS file downloader for Taiwan stock data from GoodInfo.tw using Selenium

## Status
Update time: 2025-09-04 21:52:19

|No| Folder |Total|Success| Failed|Updated from now|Duration|
|--| -- |--|--|--|--|--|
|1| DividendDetail |117|117|0|2 days 6 hours ago|28 minutes|
|2| BasicInfo |0|0|0|N/A|N/A|
|3| StockDetail |0|0|0|N/A|N/A|
|4| StockBzPerformance |117|117|0|2 days 5 hours ago|27 minutes|
|5| ShowSaleMonChart |117|117|0|8 hours ago|1 days 1 hours|
|6| EquityDistribution |117|81|36|1 days 12 hours ago|1 hours 21 minutes|
|7| StockBzPerformance1 |117|117|0|1 days 16 hours ago|38 minutes|
|8| ShowK_ChartFlow |117|117|0|4 days 11 hours ago|35 minutes|
|9| StockHisAnaQuar |117|117|0|5 days 14 hours ago|32 minutes|
|10| EquityDistributionClassHis |0|0|0|N/A|N/A|


## 📋 Features

- **No Login Required** - Downloads XLS files directly from export buttons
- **Auto-Updated Stock List** - Downloads latest observation list from GitHub
- **Batch Processing** - Process all stocks automatically with GetAll.py
- **10 Data Types** - Complete coverage of GoodInfo.tw data sources
- **Complete 7-Day Weekly + Daily Automation** - Perfect scheduling with server-friendly approach
- **Anti-Bot Detection** - Uses undetected-chromedriver for reliability
- **Advanced Special Workflows** - Enhanced handling for complex data types
- **Intelligent Progress Tracking** - CSV-based status monitoring with smart processing

## 📂 Repository Structure

```
├── GetGoodInfo.py                   # Main downloader script (v1.8.0.0)
├── GetAll.py                        # Batch processing script
├── Get觀察名單.py                    # Stock list downloader
├── StockID_TWSE_TPEX.csv            # Stock ID and name mappings (auto-updated)
├── requirements.txt                 # Python dependencies
├── .github/workflows/Actions.yml    # GitHub Actions workflow (Complete 7-Day Weekly + Daily v1.8.0)
├── instructions-GoodInfoDownloader.md # Development instructions (v1.8.0)
└── README.md                        # This file
```

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Python-Actions.GoodInfo.git
   cd Python-Actions.GoodInfo
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download latest stock list**
   ```bash
   python Get觀察名單.py
   ```

4. **Verify Chrome installation** (for Selenium)
   - Chrome browser will be automatically managed by webdriver-manager

## 🎯 Usage

### Individual Stock Download

```bash
python GetGoodInfo.py STOCK_ID DATA_TYPE
```

### Batch Processing

```bash
python GetAll.py DATA_TYPE [OPTIONS]
```

### Stock List Management

```bash
python Get觀察名單.py
```

### Parameters

- **STOCK_ID**: Taiwan stock code (e.g., 2330, 0050, 2454)
- **DATA_TYPE**: Type of data to download
  - `1` = Dividend Policy (殖利率政策) - https://goodinfo.tw/tw/StockDividendPolicy.asp?STOCK_ID=xxxx - Click "XLS" button to get CSV file named as `DividendDetail_{stock_id}_{stock_company}.xls`
  - `2` = Basic Info (基本資料) - https://goodinfo.tw/tw/BasicInfo.asp?STOCK_ID=xxxx - Find `公司基本資料` table and convert to XLS
  - `3` = Stock Details (個股市況) - https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID=xxxx - Get stock market data
  - `4` = Business Performance (經營績效) - https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID=xxxx - Click "XLS" button to get CSV file named as `StockBzPerformance_{stock_id}_{stock_company}.xls`
  - `5` = Monthly Revenue (每月營收) - https://goodinfo.tw/tw/ShowSaleMonChart.asp?STOCK_ID=xxxx - Click "查20年" button and 2 seconds later click "XLS" button to get CSV file named as `ShowSaleMonChart_{stock_id}_{stock_company}.xls`
  - `6` = Equity Distribution (股權結構) - https://goodinfo.tw/tw/EquityDistributionCatHis.asp?STOCK_ID=xxxx - Click "XLS" button to get CSV file named as `EquityDistribution_{stock_id}_{stock_company}.xls`
  - `7` = Quarterly Business Performance (每季經營績效) - https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID=xxxx&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR - Click "查60年" button and 2 seconds later click "XLS" button to get CSV file named as `StockBzPerformance1_{stock_id}_{stock_company}_quarter.xls`
  - `8` = EPS x PER Weekly (每週EPS本益比) - https://goodinfo.tw/tw/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID=xxxx - Click "查5年" button and 2 seconds later click "XLS" button to get CSV file named as `ShowK_ChartFlow_{stock_id}_{stock_company}.xls`
  - `9` = Quarterly Analysis (各季詳細統計資料) - https://goodinfo.tw/tw/StockHisAnaQuar.asp?STOCK_ID=xxxx - Click "XLS" button to get CSV file named as `StockHisAnaQuar_{stock_id}_{stock_company}.xls`
  - `10` = Equity Class Weekly (股東持股分級週) - https://goodinfo.tw/tw/EquityDistributionClassHis.asp?STOCK_ID=xxxx - Click "查5年" button and 2 seconds later click "XLS" button to get CSV file named as `EquityDistributionClassHis_{stock_id}_{stock_company}.xls`

### Batch Options

- `--test` = Process only first 3 stocks (for testing)
- `--debug` = Show detailed error messages
- `--direct` = Simple execution mode

### Examples

#### Individual Downloads
```bash
# Download TSMC dividend data
python GetGoodInfo.py 2330 1

# Download 0050 ETF basic info
python GetGoodInfo.py 0050 2

# Download MediaTek stock details
python GetGoodInfo.py 2454 3

# Download TSMC business performance data
python GetGoodInfo.py 2330 4

# Download TSMC monthly revenue data
python GetGoodInfo.py 2330 5

# Download TSMC equity distribution data
python GetGoodInfo.py 2330 6

# Download TSMC quarterly business performance
python GetGoodInfo.py 2330 7

# Download TSMC EPS x PER weekly data
python GetGoodInfo.py 2330 8

# Download TSMC quarterly analysis data
python GetGoodInfo.py 2330 9

# Download TSMC equity class weekly data (NEW!)
python GetGoodInfo.py 2330 10
```

#### Batch Downloads
```bash
# Download dividend data for all stocks
python GetAll.py 1

# Test with first 3 stocks only
python GetAll.py 1 --test

# Download basic info with debug output
python GetAll.py 2 --debug

# Download stock details for all stocks
python GetAll.py 3

# Download business performance for all stocks
python GetAll.py 4

# Download monthly revenue for all stocks
python GetAll.py 5

# Download equity distribution for all stocks
python GetAll.py 6

# Download quarterly performance for all stocks
python GetAll.py 7

# Download EPS x PER weekly for all stocks
python GetAll.py 8

# Download quarterly analysis for all stocks
python GetAll.py 9

# Download equity class weekly for all stocks (NEW!)
python GetAll.py 10
```

#### Update Stock List
```bash
# Download latest observation list
python Get觀察名單.py
```

## 📊 Supported Stocks

The script automatically downloads the latest Taiwan stock observation list from GitHub, ensuring you always have the most current stock data available.

### Popular Examples:
- `2330` - 台積電 (TSMC)
- `0050` - 元大台灣50
- `2454` - 聯發科 (MediaTek)
- `2317` - 鴻海 (Foxconn)
- `2382` - 廣達 (Quanta)

### Stock List Source:
- **Source**: [GitHub Repository](https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv)
- **Auto-updates**: Run `Get觀察名單.py` to get latest list
- **Format**: CSV with stock ID and company name

## 📂 Output Structure

Downloaded files are organized by data type:

```
DividendDetail/
├── DividendDetail_2330_台積電.xls
├── DividendDetail_2317_鴻海.xls
├── download_results.csv
└── ...

BasicInfo/
├── BasicInfo_0050_元大台灣50.xls
├── BasicInfo_2454_聯發科.xls
├── download_results.csv
└── ...

StockDetail/
├── StockDetail_2330_台積電.xls
├── StockDetail_2382_廣達.xls
├── download_results.csv
└── ...

StockBzPerformance/
├── StockBzPerformance_2330_台積電.xls
├── StockBzPerformance_2454_聯發科.xls
├── download_results.csv
└── ...

ShowSaleMonChart/
├── ShowSaleMonChart_2330_台積電.xls
├── ShowSaleMonChart_2317_鴻海.xls
├── download_results.csv
└── ...

EquityDistribution/
├── EquityDistribution_2330_台積電.xls
├── EquityDistribution_2317_鴻海.xls
├── download_results.csv
└── ...

StockBzPerformance1/
├── StockBzPerformance1_2330_台積電_quarter.xls
├── StockBzPerformance1_2454_聯發科_quarter.xls
├── download_results.csv
└── ...

ShowK_ChartFlow/
├── ShowK_ChartFlow_2330_台積電.xls
├── ShowK_ChartFlow_2454_聯發科.xls
├── download_results.csv
└── ...

StockHisAnaQuar/
├── StockHisAnaQuar_2330_台積電.xls
├── StockHisAnaQuar_2454_聯發科.xls
├── download_results.csv
└── ...

EquityDistributionClassHis/
├── EquityDistributionClassHis_2330_台積電.xls
├── EquityDistributionClassHis_2454_聯發科.xls
├── download_results.csv
└── ...
```

## 🤖 GitHub Actions Automation

### Complete 7-Day Weekly + Daily Automation Schedule (v1.8.0)

The repository includes an intelligent GitHub Actions workflow with **complete 7-day weekly + daily scheduling**:

#### Automated Schedule (Server-Friendly)
- **Monday 8 AM UTC (4 PM Taiwan)**: Type 1 - Dividend Policy (Weekly)
- **Tuesday 8 AM UTC (4 PM Taiwan)**: Type 4 - Business Performance (Weekly)
- **Wednesday 8 AM UTC (4 PM Taiwan)**: Type 6 - Equity Distribution (Weekly)
- **Thursday 8 AM UTC (4 PM Taiwan)**: Type 7 - Quarterly Performance (Weekly)
- **Friday 8 AM UTC (4 PM Taiwan)**: Type 8 - EPS x PER Weekly (Weekly)
- **Saturday 8 AM UTC (4 PM Taiwan)**: Type 9 - Quarterly Analysis (Weekly)
- **Sunday 8 AM UTC (4 PM Taiwan)**: Type 10 - Equity Class Weekly (Weekly) 🆕
- **Daily 12 PM UTC (8 PM Taiwan)**: Type 5 - Monthly Revenue (Daily)

### Manual Triggers

You can trigger downloads manually for any data type (1-10):
1. Go to the "Actions" tab in your GitHub repository
2. Click "Download GoodInfo Data"
3. Click "Run workflow"
4. Select desired data type (1-10) and test mode if needed

### Smart Automation Features

- ✅ **Complete 7-Day Weekly Schedule** - Major data types updated weekly with perfect timing across all 7 days
- ✅ **Daily Revenue Tracking** - Time-sensitive revenue data updated daily
- ✅ **Complete Manual Support** - All 10 data types available on-demand
- ✅ **Server-Friendly Operation** - Perfect distribution prevents server overload
- ✅ Automated stock list updates before each run
- ✅ Batch processing of all stocks in observation list
- ✅ Automated Chrome setup for headless execution
- ✅ Comprehensive file organization and commits
- ✅ Error handling with detailed progress tracking
- ✅ Advanced special workflow support for Types 5, 7, 8, and 10

### Automation Strategy (v1.8.0)

**Complete 7-Day Weekly + Daily Philosophy:**
- **Weekly Updates**: Non-urgent data (Types 1,4,6,7,8,9,10) updated weekly for server efficiency
- **Daily Updates**: Time-sensitive revenue data (Type 5) updated daily
- **Optimal Timing**: All automated runs at 4 PM Taiwan time (end of business day)
- **Complete Coverage**: All 10 data types with perfect 7-day automation distribution
- **Perfect Load Balancing**: Distributed across full week for optimal performance

**Why This Complete Schedule Works:**
- 📊 **Complete coverage** - All 10 data types with perfect automation across full week
- 🌍 **Server-friendly** - Optimal load distribution with full 7-day spread
- ⚡ **Efficient resource usage** - Weekly pattern allows for retry mechanisms
- 🛡️ **Reduced failure risk** - Full week distribution improves reliability
- 📈 **Complete data coverage** - All major GoodInfo.tw data sources included
- ⏰ **Time-sensitive priority** - Revenue data gets daily attention

### Complete Schedule Summary

| Day | Time (UTC) | Time (Taiwan) | Data Type | Description | Update Frequency |
|-----|-----------|---------------|-----------|-------------|------------------|
| Monday | 8:00 AM | 4:00 PM | Type 1 | Dividend Policy | Weekly |
| Tuesday | 8:00 AM | 4:00 PM | Type 4 | Business Performance | Weekly |
| Wednesday | 8:00 AM | 4:00 PM | Type 6 | Equity Distribution | Weekly |
| Thursday | 8:00 AM | 4:00 PM | Type 7 | Quarterly Performance | Weekly |
| Friday | 8:00 AM | 4:00 PM | Type 8 | EPS x PER Weekly | Weekly |
| Saturday | 8:00 AM | 4:00 PM | Type 9 | Quarterly Analysis | Weekly |
| Sunday | 8:00 AM | 4:00 PM | Type 10 | Equity Class Weekly | Weekly 🆕 |
| Daily | 12:00 PM | 8:00 PM | Type 5 | Monthly Revenue | Daily |
| Manual | On-demand | On-demand | Type 2 | Basic Info | Manual only |
| Manual | On-demand | On-demand | Type 3 | Stock Details | Manual only |

## 🔧 Technical Details

### Dependencies

- **selenium**: Browser automation
- **webdriver-manager**: Chrome driver management
- **pandas**: CSV file handling
- **beautifulsoup4**: HTML parsing
- **undetected-chromedriver**: Anti-bot detection bypass
- **requests**: HTTP requests for stock list downloads

### Browser Configuration

- Headless Chrome execution
- Anti-detection measures
- Custom download directories
- Traditional Chinese language support

### Enhanced Error Handling (v1.8.0)

- Graceful fallbacks for missing stock IDs
- Progress tracking for batch operations
- Debug file generation for troubleshooting
- Network timeout protection
- Automatic encoding detection
- Advanced special workflow handling for Types 5, 7, 8, and 10
- Enhanced XLS element detection with 4-tier search methods

### Special Workflow Features

- **Type 5 (Monthly Revenue)**: Automated "查20年" button detection and clicking
- **Type 7 (Quarterly Performance)**: Special URL parameters + "查60年" button workflow
- **Type 8 (EPS x PER Weekly)**: Special URL parameters + "查5年" button workflow
- **Type 9 (Quarterly Analysis)**: Standard XLS download workflow
- **Type 10 (Equity Class Weekly)**: "查5年" button + XLS download workflow 🆕
- **Enhanced Element Detection**: 4-tier search system for maximum compatibility
- **Debug Screenshots**: Automatic screenshot capture for failed downloads

### Batch Processing Features

- **Progress tracking**: Shows [current/total] progress
- **Error recovery**: Continues processing even if individual stocks fail
- **Summary reporting**: Success/failure statistics
- **Rate limiting**: 1-second delay between requests (2 seconds for special workflows)
- **Test mode**: Process only first 3 stocks for testing
- **Smart automation**: Complete 7-day weekly + daily runs with perfect scheduling

## 🛠 Troubleshooting

### Common Issues

1. **CSV file not found**
   - Run: `python Get觀察名單.py` to download stock list
   - Check internet connection

2. **No XLS download elements found**
   - Page structure may have changed
   - Check debug files: `debug_page_{stock_id}.html`
   - Check debug screenshots: `debug_screenshot_{stock_id}.png`
   - Verify stock ID exists on GoodInfo.tw

3. **Module not found errors**
   - Run: `pip install -r requirements.txt`
   - Ensure all dependencies are installed

4. **Batch processing failures**
   - Use `--debug` flag to see detailed errors
   - Use `--test` flag to test with 3 stocks first
   - Check individual stock with `GetGoodInfo.py`

5. **Monthly revenue data issues (DATA_TYPE=5)**
   - Script automatically looks for "查20年" button
   - If button not found, check debug output for available elements
   - Some stocks may not have 20-year data available

6. **Quarterly performance data issues (DATA_TYPE=7)**
   - Uses special URL with quarterly parameters
   - Script automatically looks for "查60年" button
   - Debug output shows available buttons if not found
   - Some stocks may not have 60-year quarterly data

7. **EPS x PER weekly data issues (DATA_TYPE=8)**
   - Uses special URL with RPT_CAT=PER parameters
   - Script automatically looks for "查5年" button
   - Debug output shows available buttons if not found
   - Some stocks may not have 5-year EPS/PER weekly data

8. **Quarterly analysis data issues (DATA_TYPE=9)**
   - Uses standard XLS download workflow
   - Standard XLS element detection patterns
   - Some stocks may not have quarterly analysis data
   - Check debug output if download fails

9. **Equity class weekly data issues (DATA_TYPE=10) - NEW!**
   - Uses special workflow with "查5年" button
   - Script automatically looks for "查5年" button followed by XLS download
   - Debug output shows available buttons if not found
   - Some stocks may not have 5-year equity class weekly data

## 📈 Version History

- **v1.8.0** - Complete 10 Data Types with Full 7-Day Weekly Automation (CURRENT)
  - ✅ **10 Complete Data Types** - Added Equity Distribution Class Weekly (Type 10) for comprehensive weekly shareholder analysis
  - ✅ **Sunday Automation** - Extended smart weekly scheduling to include Sunday for complete 7-day coverage
  - ✅ **Perfect Weekly Coverage** - All major GoodInfo.tw data sources now covered across full week
  - ✅ **Enhanced Documentation** - Complete usage examples and troubleshooting for all 10 data types
  - ✅ **Perfect Load Distribution** - Balanced weekly distribution across 7 days with daily revenue tracking
  - ✅ Updated GetGoodInfo.py to v1.8.0.0 with full 10-type support and complete automation

## 🚀 Quick Start Guide

1. **Setup**
   ```bash
   git clone <repository>
   cd Python-Actions.GoodInfo
   pip install -r requirements.txt
   ```

2. **Download stock list**
   ```bash
   python Get觀察名單.py
   ```

3. **Test all data types**
   ```bash
   python GetAll.py 1 --test    # Dividend data
   python GetAll.py 5 --test    # Monthly revenue (daily automation)
   python GetAll.py 6 --test    # Equity distribution  
   python GetAll.py 7 --test    # Quarterly performance
   python GetAll.py 8 --test    # EPS x PER weekly
   python GetAll.py 9 --test    # Quarterly analysis
   python GetAll.py 10 --test   # Equity class weekly (NEW!)
   ```

4. **Try individual downloads**
   ```bash
   python GetGoodInfo.py 2330 6    # TSMC equity distribution
   python GetGoodInfo.py 2330 7    # TSMC quarterly performance
   python GetGoodInfo.py 2330 8    # TSMC EPS x PER weekly
   python GetGoodInfo.py 2330 9    # TSMC quarterly analysis
   python GetGoodInfo.py 2330 10   # TSMC equity class weekly (NEW!)
   ```

5. **Download complete dataset**
   ```bash
   python GetAll.py 1    # All dividend data (Monday automation)
   python GetAll.py 5    # All revenue data (daily automation)
   python GetAll.py 8    # All EPS x PER weekly data (Friday automation)
   python GetAll.py 9    # All quarterly analysis data (Saturday automation)
   python GetAll.py 10   # All equity class weekly data (Sunday automation) (NEW!)
   ```

## 📊 Complete Data Type Details (v1.8.0)

### 1. Dividend Policy (殖利率政策)
- **URL**: `StockDividendPolicy.asp?STOCK_ID={stock_id}`
- **Folder**: DividendDetail/
- **Content**: Historical dividend distributions, yield rates, payout ratios
- **Workflow**: Standard XLS download
- **Update**: Weekly (Monday 8 AM UTC automation)

### 2. Basic Info (基本資料)
- **URL**: `BasicInfo.asp?STOCK_ID={stock_id}`
- **Folder**: BasicInfo/
- **Content**: Company fundamentals, industry classification, listing information
- **Workflow**: Standard XLS download
- **Update**: Manual only (rarely changes)

### 3. Stock Details (個股市況)
- **URL**: `StockDetail.asp?STOCK_ID={stock_id}`
- **Folder**: StockDetail/
- **Content**: Trading data, price movements, volume analysis
- **Workflow**: Standard XLS download
- **Update**: Manual only (real-time data)

### 4. Business Performance (經營績效)
- **URL**: `StockBzPerformance.asp?STOCK_ID={stock_id}`
- **Folder**: StockBzPerformance/
- **Content**: Financial performance metrics, profitability ratios, operational efficiency
- **Workflow**: Standard XLS download
- **Update**: Weekly (Tuesday 8 AM UTC automation)

### 5. Monthly Revenue (每月營收)
- **URL**: `ShowSaleMonChart.asp?STOCK_ID={stock_id}`
- **Folder**: ShowSaleMonChart/
- **Content**: 20-year monthly revenue data, sales trends, growth patterns
- **Workflow**: Special - Click "查20年" → Wait 2 seconds → XLS download
- **Update**: Daily (12 PM UTC automation) - Most time-sensitive

### 6. Equity Distribution (股權結構)
- **URL**: `EquityDistributionCatHis.asp?STOCK_ID={stock_id}`
- **Folder**: EquityDistribution/
- **Content**: Shareholder structure, institutional holdings, ownership distribution
- **Workflow**: Standard XLS download
- **Update**: Weekly (Wednesday 8 AM UTC automation)

### 7. Quarterly Business Performance (每季經營績效)
- **URL**: `StockBzPerformance.asp?STOCK_ID={stock_id}&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR`
- **Folder**: StockBzPerformance1/
- **Content**: Quarterly financial data, seasonal trends, YoY comparisons
- **Workflow**: Special URL → Click "查60年" → Wait 2 seconds → XLS download
- **Update**: Weekly (Thursday 8 AM UTC automation)

### 8. EPS x PER Weekly (每週EPS本益比)
- **URL**: `ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID={stock_id}`
- **Folder**: ShowK_ChartFlow/
- **Content**: Weekly EPS and P/E ratio data for 5-year period, technical analysis data
- **Workflow**: Special URL → Click "查5年" → Wait 2 seconds → XLS download
- **Update**: Weekly (Friday 8 AM UTC automation)

### 9. Quarterly Analysis (各季詳細統計資料)
- **URL**: `StockHisAnaQuar.asp?STOCK_ID={stock_id}`
- **Folder**: StockHisAnaQuar/
- **Content**: 4-quarter detailed statistical data, stock price movements, trading volumes, seasonal patterns
- **Workflow**: Standard XLS download (click XLS button)
- **Update**: Weekly (Saturday 8 AM UTC automation)

### 10. Equity Class Weekly (股東持股分級週) 🆕
- **URL**: `EquityDistributionClassHis.asp?STOCK_ID={stock_id}`
- **Folder**: EquityDistributionClassHis/
- **Content**: Weekly equity distribution class histogram data for 5-year period, shareholder classification trends
- **Workflow**: Special - Click "查5年" → Wait 2 seconds → XLS download
- **Update**: Weekly (Sunday 8 AM UTC automation) 🆕

## ⚖️ Legal Notice

This tool is for educational and research purposes only. Please:
- Respect GoodInfo.tw's terms of service
- Use reasonable request intervals (built-in 1-second delay)
- Don't overload their servers
- Consider subscribing to their premium services for heavy usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test with `--test` flag first
4. Make your changes
5. Test thoroughly with all 10 data types
6. Submit a pull request

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: Use GitHub Discussions for questions
- **Updates**: Watch the repository for new releases

## 🎯 Roadmap

- [ ] Support for additional GoodInfo.tw data pages
- [ ] Enhanced data validation and quality checks
- [ ] Export to multiple formats (CSV, JSON)
- [ ] Real-time data monitoring capabilities
- [ ] Performance optimization for large-scale downloads
- [ ] Advanced filtering and sorting options

## 🏆 Success Tips

### Leveraging Complete 7-Day Automation (v1.8.0):
- 📅 **Perfect Scheduling**: 7-day weekly distribution covers all major data types
- 📊 **Complete Coverage**: All 10 data types available with optimal automation
- 🕐 **Predictable Timing**: All runs at 4 PM Taiwan time (end of business day)
- 📱 **Manual Access**: All 10 data types available 24/7 via manual triggers

### For New Data Type 10 (Equity Class Weekly):
- 📈 **Type 10**: Best for weekly equity distribution class analysis and shareholder trends (Sunday automation)
- 📊 **Complete Coverage**: 5-year weekly equity class histogram for comprehensive analysis
- 🕘 Special workflow - includes "查5年" button handling
- 📝 Check debug output if special workflow fails

### For All Data Types:
- 🧪 Always test with `--test` flag first
- 📄 Use batch processing for multiple stocks
- 📝 Check debug files and screenshots if downloads fail
- ⏰ Respect rate limits (1-second delay built-in, 2 seconds for special workflows)
- 🤖 **Complete**: Leverage 7-day weekly automation for optimal data freshness

---

**⭐ Star this repository if it helps you with Taiwan stock data analysis!**

**🆕 New in v1.8.0: Complete 10 data types with full 7-day weekly automation!**

**📅 Perfect scheduling: Complete weekly coverage + daily revenue tracking!**

**🚀 Complete coverage of GoodInfo.tw data sources with comprehensive equity class weekly analysis support!**