# Python-Actions.GoodInfo - GoodInfo.tw XLS Downloader

🚀 Automated XLS file downloader for Taiwan stock data from GoodInfo.tw using Selenium

## 📋 Features

- **No Login Required** - Downloads XLS files directly from export buttons
- **Auto-Updated Stock List** - Downloads latest observation list from GitHub
- **Batch Processing** - Process all stocks automatically with GetAll.py
- **4 Data Types** - Dividend policy, basic info, stock details, and business performance
- **GitHub Actions Integration** - Automated daily downloads
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
  - `1` = Dividend Policy (殖利率政策)  https://goodinfo.tw/tw/StockDividendPolicy.asp?STOCK_ID=xxxx
  - `2` = Basic Info (基本資料)  https://goodinfo.tw/tw/BasicInfo.asp?STOCK_ID=xxxx 
  - `3` = Stock Details (個股市況) https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID=xxxx
  - `4` = Business Performance (經營績效) https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID=xxxx

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
```

## 🤖 GitHub Actions Automation

### Automated Daily Downloads

The repository includes a GitHub Actions workflow that:
- Updates stock list automatically
- Downloads dividend data for all observation list stocks
- Runs daily at 8 AM UTC (4 PM Taiwan time)
- Commits results back to the repository

### Manual Triggers

You can also trigger downloads manually:
1. Go to the "Actions" tab in your GitHub repository
2. Click "Download GoodInfo Data"
3. Click "Run workflow"

### Workflow Features

- ✅ Automated stock list updates
- ✅ Batch processing of all stocks
- ✅ Automated Chrome setup
- ✅ Headless browser execution
- ✅ Automatic file commits
- ✅ Error handling with progress tracking

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

### Batch Processing Features

- **Progress tracking**: Shows [current/total] progress
- **Error recovery**: Continues processing even if individual stocks fail
- **Summary reporting**: Success/failure statistics
- **Rate limiting**: 1-second delay between requests
- **Test mode**: Process only first 3 stocks for testing

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

### Debug Mode

When no download elements are found, the script automatically:
- 📄 Saves page HTML to `debug_page_{stock_id}.html`
- 📸 Takes screenshot to `debug_screenshot_{stock_id}.png`
- 📝 Lists all clickable elements for analysis

### Batch Debug Options

- `--test` = Test with first 3 stocks only
- `--debug` = Show complete error messages
- `--direct` = Test GetGoodInfo.py compatibility

## 📈 Version History

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

## 📊 Data Type Details

### 1. Dividend Policy (殖利率政策)
- **Page**: StockDividendPolicy.asp
- **Folder**: DividendDetail/
- **Content**: Historical dividend distributions, yield rates, payout ratios

### 2. Basic Info (基本資料)
- **Page**: BasicInfo.asp
- **Folder**: BasicInfo/
- **Content**: Company fundamentals, industry classification, listing information

### 3. Stock Details (個股市況)
- **Page**: StockDetail.asp
- **Folder**: StockDetail/
- **Content**: Trading data, price movements, volume analysis

### 4. Business Performance (經營績效) - NEW!
- **Page**: StockBzPerformance.asp
- **Folder**: StockBzPerformance/
- **Content**: Financial performance metrics, profitability ratios, operational efficiency

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
5. Test thoroughly with all 4 data types
6. Submit a pull request

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: Use GitHub Discussions for questions
- **Updates**: Watch the repository for new releases

## 🎯 Roadmap

- [ ] Support for additional GoodInfo.tw data pages
- [ ] Enhanced error recovery mechanisms
- [ ] Data validation and quality checks
- [ ] Export to multiple formats (CSV, JSON)
- [ ] Real-time data monitoring capabilities

---

**⭐ Star this repository if it helps you with Taiwan stock data analysis!**

**🆕 New in v2.0.1.0: Business Performance data support - try `python GetGoodInfo.py 2330 4`**