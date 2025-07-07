# Python-Actions.GoodInfo - GoodInfo.tw XLS Downloader

🚀 Automated XLS file downloader for Taiwan stock data from GoodInfo.tw using Selenium

## 📋 Features

- **No Login Required** - Downloads XLS files directly from export buttons
- **Auto-Updated Stock List** - Downloads latest observation list from GitHub
- **Batch Processing** - Process all stocks automatically with GetAll.py
- **7 Data Types** - Complete coverage of GoodInfo.tw data sources
- **Enhanced GitHub Actions** - 5 automated runs with intelligent scheduling
- **Anti-Bot Detection** - Uses undetected-chromedriver for reliability
- **Special Workflows** - Advanced handling for complex data types

## 📁 Repository Structure

```
├── GetGoodInfo.py                   # Main downloader script (v1.5.0.0)
├── GetAll.py                        # Batch processing script
├── Get觀察名單.py                    # Stock list downloader
├── StockID_TWSE_TPEX.csv            # Stock ID and name mappings (auto-updated)
├── requirements.txt                 # Python dependencies
├── .github/workflows/Actions.yml    # GitHub Actions workflow (enhanced)
├── instructions.md                  # Development instructions (NEW)
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
  - `2` = Basic Info (基本資料) - https://goodinfo.tw/tw/BasicInfo.asp?STOCK_ID=xxxx - Get 公司基本資料 table
  - `3` = Stock Details (個股市況) - https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID=xxxx - Get stock market data
  - `4` = Business Performance (經營績效) - https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID=xxxx - Click "XLS" button to get CSV file named as `StockBzPerformance_{stock_id}_{stock_company}.xls`
  - `5` = Monthly Revenue (每月營收) - https://goodinfo.tw/tw/ShowSaleMonChart.asp?STOCK_ID=xxxx - Click "查20年" button and 2 seconds later click "XLS" button to get CSV file named as `ShowSaleMonChart_{stock_id}_{stock_company}.xls`
  - `6` = Equity Distribution (股東結構) - https://goodinfo.tw/tw/EquityDistributionCatHis.asp?STOCK_ID=xxxx - Click "XLS" button to get CSV file named as `EquityDistribution_{stock_id}_{stock_company}.xls`
  - `7` = Quarterly Business Performance (每季經營績效) - https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID=xxxx&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR - Click "查60年" button and 2 seconds later click "XLS" button to get CSV file named as `StockBzPerformance1_{stock_id}_{stock_company}_quarter.xls`

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

# Download TSMC equity distribution data (NEW!)
python GetGoodInfo.py 2330 6

# Download TSMC quarterly business performance (NEW!)
python GetGoodInfo.py 2330 7
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

# Download equity distribution for all stocks (NEW!)
python GetAll.py 6

# Download quarterly performance for all stocks (NEW!)
python GetAll.py 7
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
└── ...

BasicInfo/
├── BasicInfo_0050_元大台灣50.xls
├── BasicInfo_2454_聯發科.xls
└── ...

StockDetail/
├── StockDetail_2330_台積電.xls
├── StockDetail_2382_廣達.xls
└── ...

StockBzPerformance/
├── StockBzPerformance_2330_台積電.xls
├── StockBzPerformance_2454_聯發科.xls
└── ...

ShowSaleMonChart/
├── ShowSaleMonChart_2330_台積電.xls
├── ShowSaleMonChart_2317_鴻海.xls
└── ...

EquityDistribution/
├── EquityDistribution_2330_台積電.xls
├── EquityDistribution_2317_鴻海.xls
└── ...

StockBzPerformance1/
├── StockBzPerformance1_2330_台積電_quarter.xls
├── StockBzPerformance1_2454_聯發科_quarter.xls
└── ...
```

## 🤖 GitHub Actions Automation

### Enhanced Automated Scheduling (v1.5.0)

The repository includes an enhanced GitHub Actions workflow that runs **5 times daily with 1-hour intervals**:

#### Daily Runs (All Automated Data Types)
- **8 AM UTC (4 PM Taiwan)**: Dividend Policy data (Type 1) - Investment decisions
- **9 AM UTC (5 PM Taiwan)**: Business Performance data (Type 4) - Financial metrics  
- **10 AM UTC (6 PM Taiwan)**: Monthly Revenue data (Type 5) - Revenue trends
- **11 AM UTC (7 PM Taiwan)**: Equity Distribution data (Type 6) - Shareholder structure
- **12 PM UTC (8 PM Taiwan)**: Quarterly Business Performance data (Type 7) - Quarterly analysis

### Manual Triggers

You can trigger downloads manually for any data type (1-7):
1. Go to the "Actions" tab in your GitHub repository
2. Click "Download GoodInfo Data"
3. Click "Run workflow"
4. Select desired data type (1-7) and test mode if needed

### Enhanced Workflow Features

- ✅ **5 Daily Scheduled Runs** - All automated data types run daily with 1-hour intervals
- ✅ **Complete Manual Support** - All 7 data types available on-demand
- ✅ **Optimized Daily Schedule** - 5-hour window (8 AM - 12 PM UTC) for complete data coverage
- ✅ Automated stock list updates before each run
- ✅ Batch processing of all stocks in observation list
- ✅ Automated Chrome setup for headless execution
- ✅ Comprehensive file organization and commits
- ✅ Error handling with detailed progress tracking
- ✅ Special workflow support for Types 5 and 7

### Automation Strategy (v1.5.0)

**Enhanced Daily Scheduling Philosophy:**
- **Daily Data Types (1, 4, 5, 6, 7)**: All automated data types run daily for maximum freshness
- **5-Hour Window**: Optimized 8 AM - 12 PM UTC schedule spreads server load efficiently
- **1-Hour Intervals**: Predictable timing with adequate processing time between runs

**Why This Enhanced Schedule Works:**
- ⚡ **Maximum data freshness** - All automated data updated daily
- 📊 **Efficient resource usage** - 5-hour spread prevents server overload
- 🔄 **Predictable timing** - Users know exactly when each type updates
- 🛡️ **Reduced failure risk** - 1-hour gaps allow for retry mechanisms
- 📈 **Complete coverage** - All 7 data types available with optimal automation

### Enhanced Daily Schedule Summary

| Time (UTC) | Time (Taiwan) | Frequency | Data Type | Description | Update Reason |
|------------|---------------|-----------|-----------|-------------|---------------|
| 8:00 AM | 4:00 PM | Daily | Type 1 | Dividend Policy | Investment decisions |
| 9:00 AM | 5:00 PM | Daily | Type 4 | Business Performance | Financial metrics |
| 10:00 AM | 6:00 PM | Daily | Type 5 | Monthly Revenue | Revenue trends |
| 11:00 AM | 7:00 PM | Daily | Type 6 | Equity Distribution | Shareholder analysis |
| 12:00 PM | 8:00 PM | Daily | Type 7 | Quarterly Performance | Quarterly trends |
| Manual | Manual | On-demand | Type 2 | Basic Info | Rarely changes |
| Manual | Manual | On-demand | Type 3 | Stock Details | Real-time data |

## 🔍 Technical Details

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

### Enhanced Error Handling (v1.5.0)

- Graceful fallbacks for missing stock IDs
- Progress tracking for batch operations
- Debug file generation for troubleshooting
- Network timeout protection
- Automatic encoding detection
- Special workflow handling for Types 5 and 7 (complex workflows)
- Enhanced XLS element detection with 4 search methods

### Special Workflow Features

- **Type 5 (Monthly Revenue)**: Automated "查20年" button detection and clicking
- **Type 7 (Quarterly Performance)**: Special URL parameters + "查60年" button workflow
- **Enhanced Element Detection**: 4-tier search system for maximum compatibility
- **Debug Screenshots**: Automatic screenshot capture for failed downloads

### Batch Processing Features

- **Progress tracking**: Shows [current/total] progress
- **Error recovery**: Continues processing even if individual stocks fail
- **Summary reporting**: Success/failure statistics
- **Rate limiting**: 1-second delay between requests
- **Test mode**: Process only first 3 stocks for testing
- **Enhanced automation**: 5 intelligent runs with frequency-based scheduling

## 🐛 Troubleshooting

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

6. **Quarterly performance data issues (DATA_TYPE=7) - NEW!**
   - Uses special URL with quarterly parameters
   - Script automatically looks for "查60年" button
   - Debug output shows available buttons if not found
   - Some stocks may not have 60-year quarterly data

7. **Equity distribution data issues (DATA_TYPE=6) - NEW!**
   - Standard XLS download workflow
   - Some stocks may not have shareholder distribution data
   - Check debug output if download fails

### Debug Mode

When no download elements are found, the script automatically:
- 📄 Saves page HTML to `debug_page_{stock_id}.html`
- 📸 Takes screenshot to `debug_screenshot_{stock_id}.png`
- 📝 Lists all clickable elements for analysis
- 🔍 Shows available buttons and input elements (for DATA_TYPES 5, 7)

### Enhanced Debug Options (v1.5.0)

- `--test` = Test with first 3 stocks only
- `--debug` = Show complete error messages
- `--direct` = Test GetGoodInfo.py compatibility
- **4-Tier Element Detection** = Maximum compatibility with GoodInfo.tw changes

## 📈 Version History

- **v1.5.0.0** - Complete 7 Data Types with Enhanced Automation
  - ✅ **7 Complete Data Types** - Added Equity Distribution (Type 6) and Quarterly Business Performance (Type 7)
  - ✅ **Enhanced GitHub Actions** - 5 intelligent scheduled runs (Daily/Weekly/Monthly)
  - ✅ **Special Workflows** - Advanced handling for quarterly data with URL parameters
  - ✅ **Smart Scheduling** - Frequency-based automation matching data update patterns
  - ✅ **Enhanced Error Handling** - 4-tier element detection and improved debug output
  - ✅ **Complete Documentation** - Comprehensive coverage of all 7 data types
  - ✅ Updated GetGoodInfo.py to v1.5.0.0 with full 7-type support
- **v2.1.1.0** - Enhanced GitHub Actions automation with 1-hour intervals
  - ✅ **3 Daily Automated Runs** - Types 1, 4, 5 with optimized timing
  - ✅ **1-Hour Interval Schedule** - 8 AM, 9 AM, 10 AM UTC daily
  - ✅ **Complete Manual Support** - All 5 types available on-demand
  - ✅ Enhanced file management for ShowSaleMonChart folder
  - ✅ Improved automation efficiency and server load distribution
- **v2.1.0.0** - Added DATA_TYPE=5 support (Monthly Revenue / 每月營收)
  - ✅ Support for ShowSaleMonChart.asp page
  - ✅ New folder: ShowSaleMonChart/
  - ✅ Special workflow: "查20年" button → wait 2 seconds → XLS download
  - ✅ Updated GetGoodInfo.py to v1.4.3.0
  - ✅ Enhanced error handling and debug output
  - ✅ Updated documentation for all 5 data types
- **v2.0.1.0** - Added DATA_TYPE=4 support (Business Performance / 經營績效)
  - ✅ Support for StockBzPerformance.asp page
  - ✅ New folder: StockBzPerformance/
  - ✅ Updated GetGoodInfo.py to v1.4.2.0
  - ✅ Enhanced usage examples and documentation
- **v2.0.0.0** - Added batch processing and auto-updating stock list
  - ✅ New GetAll.py for batch processing all stocks
  - ✅ New Get觀察名單.py for auto-updating stock list
  - ✅ CSV-based stock ID mapping
  - ✅ Progress tracking and error recovery
  - ✅ Test mode and debug options

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
   python GetAll.py 6 --test    # Equity distribution (NEW!)
   python GetAll.py 7 --test    # Quarterly performance (NEW!)
   ```

4. **Try individual downloads**
   ```bash
   python GetGoodInfo.py 2330 6    # TSMC equity distribution
   python GetGoodInfo.py 2330 7    # TSMC quarterly performance
   ```

5. **Download complete dataset**
   ```bash
   python GetAll.py 1    # All dividend data
   python GetAll.py 6    # All equity data
   python GetAll.py 7    # All quarterly data
   ```

## 📊 Complete Data Type Details (v1.5.0)

### 1. Dividend Policy (殖利率政策)
- **Page**: StockDividendPolicy.asp
- **Folder**: DividendDetail/
- **Content**: Historical dividend distributions, yield rates, payout ratios
- **Workflow**: Standard XLS download
- **Update**: Daily (automated)

### 2. Basic Info (基本資料)
- **Page**: BasicInfo.asp
- **Folder**: BasicInfo/
- **Content**: Company fundamentals, industry classification, listing information
- **Workflow**: Standard XLS download
- **Update**: Manual only (rarely changes)

### 3. Stock Details (個股市況)
- **Page**: StockDetail.asp
- **Folder**: StockDetail/
- **Content**: Trading data, price movements, volume analysis
- **Workflow**: Standard XLS download
- **Update**: Manual only (real-time data)

### 4. Business Performance (經營績效)
- **Page**: StockBzPerformance.asp
- **Folder**: StockBzPerformance/
- **Content**: Financial performance metrics, profitability ratios, operational efficiency
- **Workflow**: Standard XLS download
- **Update**: Daily (automated)

### 5. Monthly Revenue (每月營收)
- **Page**: ShowSaleMonChart.asp
- **Folder**: ShowSaleMonChart/
- **Content**: 20-year monthly revenue data, sales trends, growth patterns
- **Workflow**: Special - Click "查20年" → Wait 2 seconds → XLS download
- **Update**: Daily (automated)

### 6. Equity Distribution (股東結構) - NEW!
- **Page**: EquityDistributionCatHis.asp
- **Folder**: EquityDistribution/
- **Content**: Shareholder structure, institutional holdings, ownership distribution
- **Workflow**: Standard XLS download
- **Update**: Daily (automated)

### 7. Quarterly Business Performance (每季經營績效) - NEW!
- **Page**: StockBzPerformance.asp with special parameters
- **URL**: `?STOCK_ID={id}&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR`
- **Folder**: StockBzPerformance1/
- **Content**: Quarterly financial data, seasonal trends, YoY comparisons
- **Workflow**: Special URL → Click "查60年" → Wait 2 seconds → XLS download
- **Update**: Daily (automated)

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
5. Test thoroughly with all 7 data types
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

### Leveraging Enhanced Automation (v1.5.0):
- 📅 **Daily Updates**: Check commits after 4-8 PM Taiwan time for all automated data
- 📊 **Complete Coverage**: All 5 automated data types updated daily
- 🕐 **Predictable Schedule**: 8 AM - 12 PM UTC (4-8 PM Taiwan) daily automation window
- 🔄 **Manual Access**: All 7 data types available 24/7 via manual triggers

### For New Data Types (6 & 7):
- 📈 **Type 6 (Equity)**: Best for tracking institutional investment changes
- 📊 **Type 7 (Quarterly)**: Essential for seasonal business pattern analysis
- 🕐 Allow extra time for Type 7 due to special workflow requirements
- 🔍 Check debug output if special buttons ("查60年") not found

### For All Data Types:
- 🧪 Always test with `--test` flag first
- 🔄 Use batch processing for multiple stocks
- 📝 Check debug files and screenshots if downloads fail
- ⏰ Respect rate limits (1-second delay built-in)
- 🤖 **NEW**: Leverage intelligent automation for optimal data freshness

---

**⭐ Star this repository if it helps you with Taiwan stock data analysis!**

**🆕 New in v1.5.0: Complete 7 data types with 5 daily automated runs!**

**📈 Enhanced automation with daily 8-12 PM UTC schedule - Maximum data freshness!**

**🚀 Full coverage of GoodInfo.tw data sources with optimized daily workflows!**