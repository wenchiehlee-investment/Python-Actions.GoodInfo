# Python-Actions.GoodInfo- GoodInfo.tw XLS Downloader

🚀 Automated XLS file downloader for Taiwan stock data from GoodInfo.tw using Selenium

## 📋 Features

- **No Login Required** - Downloads XLS files directly from export buttons
- **777 Stocks Supported** - Reads stock mappings from CSV file
- **3 Data Types** - Dividend policy, basic info, and stock details
- **GitHub Actions Integration** - Automated daily downloads
- **Anti-Bot Detection** - Uses undetected-chromedriver for reliability

## 📁 Repository Structure

```
├── GetGoodInfo.py                   # Main script
├── StockID_TWSE_TPEX.csv            # Stock ID and name mappings (777 stocks)
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

3. **Verify Chrome installation** (for Selenium)
   - Chrome browser will be automatically managed by webdriver-manager

## 🎯 Usage

### Command Line Interface

```bash
python GetGoodInfo.py STOCK_ID DATA_TYPE
```

### Parameters

- **STOCK_ID**: Taiwan stock code (e.g., 2330, 0050, 2454)
- **DATA_TYPE**: Type of data to download
  - `1` = Dividend Policy (殖利率政策)
  - `2` = Basic Info (基本資料)  
  - `3` = Stock Details (個股市況)

### Examples

```bash
# Download TSMC dividend data
python GetGoodInfo.py 2330 1

# Download 0050 ETF basic info
python GetGoodInfo.py 0050 2

# Download MediaTek stock details
python GetGoodInfo.py 2454 3

# Download Quanta dividend data
python GetGoodInfo.py 2382 2
```

## 📊 Supported Stocks

The script supports **777 Taiwan stocks** from TWSE and TPEx markets. Stock mappings are automatically loaded from `StockID_TWSE_TPEX.csv`.

### Popular Examples:
- `2330` - 台積電 (TSMC)
- `0050` - 元大台灣50
- `2454` - 聯發科 (MediaTek)
- `2317` - 鴻海 (Foxconn)
- `2382` - 廣達 (Quanta)

## 📂 Output Structure

Downloaded files are organized by data type:

```
DividendDetail/
├── DividendDetail_2330_台積電.xls

BasicInfo/
├── BasicInfo_0050_元大台灣50.xls

StockDetail/
├── StockDetail_2454_聯發科.xls
```

## 🤖 GitHub Actions Automation

### Automated Daily Downloads

The repository includes a GitHub Actions workflow that:
- Runs daily at 8 AM UTC (4 PM Taiwan time)
- Downloads TSMC dividend data automatically
- Commits results back to the repository

### Manual Triggers

You can also trigger downloads manually:
1. Go to the "Actions" tab in your GitHub repository
2. Click "Download GoodInfo Data"
3. Click "Run workflow"

### Workflow Features

- ✅ Automated Chrome setup
- ✅ Headless browser execution
- ✅ Automatic file commits
- ✅ Error handling with fallbacks

## 🔍 Technical Details

### Dependencies

- **selenium**: Browser automation
- **webdriver-manager**: Chrome driver management
- **pandas**: CSV file handling
- **beautifulsoup4**: HTML parsing
- **undetected-chromedriver**: Anti-bot detection bypass

### Browser Configuration

- Headless Chrome execution
- Anti-detection measures
- Custom download directories
- Traditional Chinese language support

### Error Handling

- Graceful fallbacks for missing stock IDs
- Debug file generation for troubleshooting
- Network timeout protection
- Missing CSV file recovery

## 🐛 Troubleshooting

### Common Issues

1. **No XLS download elements found**
   - Page structure may have changed
   - Check debug files: `debug_page_{stock_id}.html`
   - Verify stock ID exists on GoodInfo.tw

2. **Module not found errors**
   - Run: `pip install -r requirements.txt`
   - Ensure all dependencies are installed

3. **Chrome/Selenium issues**
   - Update Chrome browser
   - Clear Chrome cache
   - Check internet connection

### Debug Mode

When no download elements are found, the script automatically:
- 📄 Saves page HTML to `debug_page_{stock_id}.html`
- 📸 Takes screenshot to `debug_screenshot_{stock_id}.png`
- 📝 Lists all clickable elements for analysis

## 📈 Version History

- **v1.4.1.0** - CSV-based stock mapping, enhanced element detection
- **v1.4.0.0** - Selenium implementation with anti-bot features
- **v1.3.x.x** - Requests-based implementation
- **v1.2.x.x** - Basic authentication support

## ⚖️ Legal Notice

This tool is for educational and research purposes only. Please:
- Respect GoodInfo.tw's terms of service
- Use reasonable request intervals
- Don't overload their servers
- Consider subscribing to their premium services for heavy usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: Use GitHub Discussions for questions
- **Updates**: Watch the repository for new releases

---

**⭐ Star this repository if it helps you with Taiwan stock data analysis!**