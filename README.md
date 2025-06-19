# Python-Actions.GoodInfo - GoodInfo.tw XLS Downloader

🚀 Automated XLS file downloader for Taiwan stock data from GoodInfo.tw using Selenium

## 📋 Features

- **No Login Required** - Downloads XLS files directly from export buttons
- **Auto-Updated Stock List** - Downloads latest observation list from GitHub
- **Batch Processing** - Process all stocks automatically with GetAll.py
- **5 Data Types** - Dividend policy, basic info, stock details, business performance, and monthly revenue
- **GitHub Actions Integration** - Automated daily downloads with 1-hour intervals (3 runs daily)
- **Anti-Bot Detection** - Uses undetected-chromedriver for reliability

## 📁 Repository Structure

```
├── GetGoodInfo.py                   # Main downloader script
├── GetAll.py                        # Batch processing script (NEW)
├── Get觀察名單.py                    # Stock list downloader (NEW)
├── StockID_TWSE_TPEX.csv            # Stock ID and name mappings (auto-updated)
├── requirements.txt                 # Python dependencies
├── .github/workflows/Actions.yml    # GitHub Actions workflow
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

### Batch Processing (NEW)

```bash
python GetAll.py DATA_TYPE [OPTIONS]
```

### Stock List Management (NEW)

```bash
python Get觀察名單.py
```

### Parameters

- **STOCK_ID**: Taiwan stock code (e.g., 2330, 0050, 2454)
- **DATA_TYPE**: Type of data to download
  - `1` = Dividend Policy (殖利率政策)  https://goodinfo.tw/tw/StockDividendPolicy.asp?STOCK_ID=xxxx click on "XLS" button
  - `2` = Basic Info (基本資料)  https://goodinfo.tw/tw/BasicInfo.asp?STOCK_ID=xxxx 
  - `3` = Stock Details (個股市況) https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID=xxxx
  - `4` = Business Performance (經營績效) https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID=xxxx click on "XLS" button
  - `5` = Show Sale Mon Chart (每月營收) https://goodinfo.tw/tw/ShowSaleMonChart.asp?STOCK_ID=xxxx click on "查20年" button and 2 second to click on "XLS" button to get CSV file

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
```

## 🤖 GitHub Actions Automation

### Automated Daily Downloads

The repository includes a GitHub Actions workflow that runs **3 times daily** with 1-hour intervals:
- **8 AM UTC (4 PM Taiwan)**: Dividend Policy data (Type 1) for all stocks
- **9 AM UTC (5 PM Taiwan)**: Business Performance data (Type 4) for all stocks  
- **10 AM UTC (6 PM Taiwan)**: Monthly Revenue data (Type 5) for all stocks
- Updates stock list automatically before each run
- Commits results back to the repository with detailed logs

### Manual Triggers

You can also trigger downloads manually for any data type:
1. Go to the "Actions" tab in your GitHub repository
2. Click "Download GoodInfo Data"
3. Click "Run workflow"
4. Select desired data type (1-5) and test mode if needed

### Workflow Features

- ✅ **3 Daily Automated Runs** - Types 1, 4, and 5 with 1-hour intervals
- ✅ **Manual Support for All Types** - Types 1, 2, 3, 4, 5 available on-demand
- ✅ Automated stock list updates before each run
- ✅ Batch processing of all stocks in observation list
- ✅ Automated Chrome setup for headless execution
- ✅ Comprehensive file organization and commits
- ✅ Error handling with detailed progress tracking
- ✅ Special workflow support for Type 5 (Monthly Revenue)

### Automation Strategy

**Why These 3 Data Types?**
- **Type 1 (Dividend)**: Most frequently accessed data for investment decisions
- **Type 4 (Business Performance)**: Critical financial metrics for analysis
- **Type 5 (Monthly Revenue)**: Time-sensitive data for trend analysis

**Why 1-Hour Intervals?**
- ⚡ **Efficient server usage** - Spreads load across 3 hours
- 📊 **Fresh data availability** - Updated data every hour during peak times
- 🔄 **Predictable timing** - Users know exactly when data updates
- 🛡️ **Reduced failure risk** - Shorter gaps between retries if needed

**Manual Access for Other Types:**
- **Type 2 (Basic Info)**: Changes infrequently, manual access sufficient
- **Type 3 (Stock Details)**: Real-time data best accessed on-demand
- **All Types**: Available 24/7 via manual workflow triggers

### Daily Schedule Summary

| Time (UTC) | Time (Taiwan) | Frequency | Data Type | Description |
|------------|---------------|-----------|-----------|-------------|
| 8:00 AM | 4:00 PM | Daily | Type 1 | Dividend Policy |
| 9:00 AM | 5:00 PM | Daily | Type 4 | Business Performance |
| 10:00 AM | 6:00 PM | Daily | Type 5 | Monthly Revenue |
| Manual | Manual | On-demand | Type 2 | Basic Info |
| Manual | Manual | On-demand | Type 3 | Stock Details |

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

### Error Handling

- Graceful fallbacks for missing stock IDs
- Progress tracking for batch operations
- Debug file generation for troubleshooting
- Network timeout protection
- Automatic encoding detection
- Special workflow handling for monthly revenue data

### Batch Processing Features

- **Progress tracking**: Shows [current/total] progress
- **Error recovery**: Continues processing even if individual stocks fail
- **Summary reporting**: Success/failure statistics
- **Rate limiting**: 1-second delay between requests
- **Test mode**: Process only first 3 stocks for testing
- **Special handling**: Automated "查20年" button clicking for DATA_TYPE=5
- **Optimized automation**: 3 daily runs with 1-hour intervals for efficient data coverage

## 🐛 Troubleshooting

### Common Issues

1. **CSV file not found**
   - Run: `python Get觀察名單.py` to download stock list
   - Check internet connection

2. **No XLS download elements found**
   - Page structure may have changed
   - Check debug files: `debug_page_{stock_id}.html`
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

### Debug Mode

When no download elements are found, the script automatically:
- 📄 Saves page HTML to `debug_page_{stock_id}.html`
- 📸 Takes screenshot to `debug_screenshot_{stock_id}.png`
- 📝 Lists all clickable elements for analysis
- 🔍 Shows available buttons and input elements (for DATA_TYPE=5)

### Batch Debug Options

- `--test` = Test with first 3 stocks only
- `--debug` = Show complete error messages
- `--direct` = Test GetGoodInfo.py compatibility

## 📈 Version History

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
- **v1.4.1.0** - CSV-based stock mapping, enhanced element detection
  - ✅ StockID_TWSE_TPEX.csv integration
  - ✅ Improved XLS element detection algorithms
  - ✅ Debug file generation (HTML + screenshots)
  - ✅ Better error handling and user feedback
- **v1.4.0.0** - Selenium implementation with anti-bot features
  - ✅ Selenium WebDriver automation
  - ✅ Anti-bot detection bypass
  - ✅ Automatic Chrome driver management
  - ✅ Enhanced download directory handling
- **v1.3.x.x** - Requests-based implementation
  - ✅ HTTP requests for data extraction
  - ✅ Session management
  - ✅ Basic XLS file handling
- **v1.2.x.x** - Basic authentication support
  - ✅ Login credential handling
  - ✅ Cookie session management
  - ✅ Basic error handling

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

3. **Test with 3 stocks**
   ```bash
   python GetAll.py 1 --test
   ```

4. **Download all dividend data**
   ```bash
   python GetAll.py 1
   ```

5. **Try business performance data**
   ```bash
   python GetGoodInfo.py 2330 4
   ```

6. **Try monthly revenue data (NEW!)**
   ```bash
   python GetGoodInfo.py 2330 5
   ```

## 📊 Data Type Details

### 1. Dividend Policy (殖利率政策)
- **Page**: StockDividendPolicy.asp
- **Folder**: DividendDetail/
- **Content**: Historical dividend distributions, yield rates, payout ratios
- **Workflow**: Standard XLS download

### 2. Basic Info (基本資料)
- **Page**: BasicInfo.asp
- **Folder**: BasicInfo/
- **Content**: Company fundamentals, industry classification, listing information
- **Workflow**: Standard XLS download

### 3. Stock Details (個股市況)
- **Page**: StockDetail.asp
- **Folder**: StockDetail/
- **Content**: Trading data, price movements, volume analysis
- **Workflow**: Standard XLS download

### 4. Business Performance (經營績效)
- **Page**: StockBzPerformance.asp
- **Folder**: StockBzPerformance/
- **Content**: Financial performance metrics, profitability ratios, operational efficiency
- **Workflow**: Standard XLS download

### 5. Monthly Revenue (每月營收) - NEW!
- **Page**: ShowSaleMonChart.asp
- **Folder**: ShowSaleMonChart/
- **Content**: 20-year monthly revenue data, sales trends, growth patterns
- **Workflow**: Special - Click "查20年" → Wait 2 seconds → XLS download
- **File Format**: CSV data (despite .xls extension)

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
5. Test thoroughly with all 5 data types
6. Submit a pull request

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: Use GitHub Discussions for questions
- **Updates**: Watch the repository for new releases

## 🎯 Roadmap

- [ ] Support for additional GoodInfo.tw data pages
- [ ] Enhanced error recovery mechanisms for complex workflows
- [ ] Data validation and quality checks
- [ ] Export to multiple formats (CSV, JSON)
- [ ] Real-time data monitoring capabilities
- [ ] Automated retry mechanisms for failed downloads

## 🏆 Success Tips

### Leveraging Automation:
- 📅 **Check commit history** after 4 PM Taiwan time for fresh dividend data
- 📊 **Latest business performance** available after 5 PM Taiwan time
- 💰 **Monthly revenue updates** ready after 6 PM Taiwan time
- 🔄 **Manual triggers** available 24/7 for immediate needs

### For Monthly Revenue Data (DATA_TYPE=5):
- 📊 Best used for long-term trend analysis
- 🕐 Allow extra time due to special workflow requirements
- 📈 Data spans up to 20 years when available
- 🔍 Check debug output if "查20年" button not found

### For All Data Types:
- 🧪 Always test with `--test` flag first
- 🔄 Use batch processing for multiple stocks
- 📝 Check debug files if downloads fail
- ⏰ Respect rate limits (1-second delay built-in)
- 🤖 **NEW**: Leverage automated daily updates for Types 1, 4, 5

---

**⭐ Star this repository if it helps you with Taiwan stock data analysis!**

**🆕 New in v2.1.1.0: Optimized automation with 1-hour intervals - 3 daily runs!**

**🤖 Fully automated daily updates for Dividend, Business Performance, and Monthly Revenue data!**

**📈 Now supporting 5 complete data types with smart automation scheduling!**