# Python-Actions.GoodInfo - GoodInfo.tw XLS Downloader

🚀 Automated XLS file downloader for Taiwan stock data from GoodInfo.tw using Selenium

## 📋 Features

- **No Login Required** - Downloads XLS files directly from export buttons
- **Auto-Updated Stock List** - Downloads latest observation list from GitHub
- **Batch Processing** - Process all stocks automatically with GetAll.py
- **8 Data Types** - Complete coverage of GoodInfo.tw data sources
- **Smart Weekly + Daily Automation** - Optimized scheduling with server-friendly approach
- **Anti-Bot Detection** - Uses undetected-chromedriver for reliability
- **Advanced Special Workflows** - Enhanced handling for complex data types
- **Intelligent Progress Tracking** - CSV-based status monitoring with smart processing

## 📁 Repository Structure

```
├── GetGoodInfo.py                   # Main downloader script (v1.6.0.0)
├── GetAll.py                        # Batch processing script
├── Get觀察名單.py                    # Stock list downloader
├── StockID_TWSE_TPEX.csv            # Stock ID and name mappings (auto-updated)
├── requirements.txt                 # Python dependencies
├── .github/workflows/Actions.yml    # GitHub Actions workflow (Weekly + Daily v1.6.0)
├── instructions-GoodInfoDownloader.md # Development instructions (v1.6.0)
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
  - `6` = Equity Distribution (股權結構) - https://goodinfo.tw/tw/EquityDistributionCatHis.asp?STOCK_ID=xxxx - Click "XLS" button to get CSV file named as `EquityDistribution_{stock_id}_{stock_company}.xls`
  - `7` = Quarterly Business Performance (每季經營績效) - https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID=xxxx&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR - Click "查60年" button and 2 seconds later click "XLS" button to get CSV file named as `StockBzPerformance1_{stock_id}_{stock_company}_quarter.xls`
  - `8` = EPS x PER Weekly (每週EPS本益比) - https://goodinfo.tw/tw/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID=xxxx - Click "查5年" button and 2 seconds later click "XLS" button to get CSV file named as `ShowK_ChartFlow_{stock_id}_{stock_company}.xls`

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

# Download TSMC EPS x PER weekly data (NEW!)
python GetGoodInfo.py 2330 8
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

# Download EPS x PER weekly for all stocks (NEW!)
python GetAll.py 8
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
```

## 🤖 GitHub Actions Automation

### Enhanced Weekly + Daily Automation Schedule (v1.6.0)

The repository includes an intelligent GitHub Actions workflow with **smart weekly + daily scheduling**:

#### Automated Schedule (Server-Friendly)
- **Monday 8 AM UTC (4 PM Taiwan)**: Type 1 - Dividend Policy (Weekly)
- **Tuesday 8 AM UTC (4 PM Taiwan)**: Type 4 - Business Performance (Weekly)
- **Wednesday 8 AM UTC (4 PM Taiwan)**: Type 6 - Equity Distribution (Weekly)
- **Thursday 8 AM UTC (4 PM Taiwan)**: Type 7 - Quarterly Performance (Weekly)
- **Friday 8 AM UTC (4 PM Taiwan)**: Type 8 - EPS x PER Weekly (Weekly) 🆕
- **Daily 12 PM UTC (8 PM Taiwan)**: Type 5 - Monthly Revenue (Daily)

### Manual Triggers

You can trigger downloads manually for any data type (1-8):
1. Go to the "Actions" tab in your GitHub repository
2. Click "Download GoodInfo Data"
3. Click "Run workflow"
4. Select desired data type (1-8) and test mode if needed

### Smart Automation Features

- ✅ **Smart Weekly Schedule** - Major data types updated weekly with optimized timing
- ✅ **Daily Revenue Tracking** - Time-sensitive revenue data updated daily
- ✅ **Complete Manual Support** - All 8 data types available on-demand
- ✅ **Server-Friendly Operation** - Distributed timing prevents server overload
- ✅ Automated stock list updates before each run
- ✅ Batch processing of all stocks in observation list
- ✅ Automated Chrome setup for headless execution
- ✅ Comprehensive file organization and commits
- ✅ Error handling with detailed progress tracking
- ✅ Advanced special workflow support for Types 5, 7, and 8

### Automation Strategy (v1.6.0)

**Smart Weekly + Daily Philosophy:**
- **Weekly Updates**: Non-urgent data (Types 1,4,6,7,8) updated weekly for server efficiency
- **Daily Updates**: Time-sensitive revenue data (Type 5) updated daily
- **Optimal Timing**: All automated runs at 4 PM Taiwan time (end of business day)
- **Manual Access**: All 8 data types available 24/7 via manual triggers
- **Load Balancing**: Distributed across weekdays for optimal performance

**Why This Smart Schedule Works:**
- 📊 **Practical frequency** - Most financial data doesn't need daily updates
- 🌍 **Server-friendly** - Reduced load with intelligent scheduling
- ⚡ **Efficient resource usage** - Weekly pattern allows for retry mechanisms
- 🛡️ **Reduced failure risk** - Distributed schedule improves reliability
- 📈 **Complete coverage** - All 8 data types with optimal automation
- ⏰ **Time-sensitive priority** - Revenue data gets daily attention

### Smart Schedule Summary

| Day | Time (UTC) | Time (Taiwan) | Data Type | Description | Update Frequency |
|-----|-----------|---------------|-----------|-------------|------------------|
| Monday | 8:00 AM | 4:00 PM | Type 1 | Dividend Policy | Weekly |
| Tuesday | 8:00 AM | 4:00 PM | Type 4 | Business Performance | Weekly |
| Wednesday | 8:00 AM | 4:00 PM | Type 6 | Equity Distribution | Weekly |
| Thursday | 8:00 AM | 4:00 PM | Type 7 | Quarterly Performance | Weekly |
| Friday | 8:00 AM | 4:00 PM | Type 8 | EPS x PER Weekly 🆕 | Weekly |
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

### Enhanced Error Handling (v1.6.0)

- Graceful fallbacks for missing stock IDs
- Progress tracking for batch operations
- Debug file generation for troubleshooting
- Network timeout protection
- Automatic encoding detection
- Advanced special workflow handling for Types 5, 7, and 8
- Enhanced XLS element detection with 4-tier search methods

### Special Workflow Features

- **Type 5 (Monthly Revenue)**: Automated "查20年" button detection and clicking
- **Type 7 (Quarterly Performance)**: Special URL parameters + "查60年" button workflow
- **Type 8 (EPS x PER Weekly)**: Special URL parameters + "查5年" button workflow 🆕
- **Enhanced Element Detection**: 4-tier search system for maximum compatibility
- **Debug Screenshots**: Automatic screenshot capture for failed downloads

### Batch Processing Features

- **Progress tracking**: Shows [current/total] progress
- **Error recovery**: Continues processing even if individual stocks fail
- **Summary reporting**: Success/failure statistics
- **Rate limiting**: 1-second delay between requests (2 seconds for special workflows)
- **Test mode**: Process only first 3 stocks for testing
- **Smart automation**: Weekly + daily runs with optimized scheduling

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

**GitHub Actions Integration:**
- CSV files are automatically committed after each run
- Progress visible in repository file history
- Manual trigger uses existing CSV for smart processing

The download_results.csv system transforms simple batch downloading into an intelligent, resilient data collection process that maximizes efficiency while ensuring comprehensive coverage across all 8 GoodInfo.tw data types.

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

7. **Equity distribution data issues (DATA_TYPE=6)**
   - Standard XLS download workflow
   - Some stocks may not have shareholder distribution data
   - Check debug output if download fails

8. **EPS x PER weekly data issues (DATA_TYPE=8) - NEW!**
   - Uses special URL with RPT_CAT=PER parameters
   - Script automatically looks for "查5年" button
   - Debug output shows available buttons if not found
   - Some stocks may not have 5-year EPS/PER weekly data

### Debug Mode

When no download elements are found, the script automatically:
- 📄 Saves page HTML to `debug_page_{stock_id}.html`
- 📸 Takes screenshot to `debug_screenshot_{stock_id}.png`
- 📋 Lists all clickable elements for analysis
- 🔍 Shows available buttons and input elements (for DATA_TYPES 5, 7, 8)

### Enhanced Debug Options (v1.6.0)

- `--test` = Test with first 3 stocks only
- `--debug` = Show complete error messages
- `--direct` = Test GetGoodInfo.py compatibility
- **4-Tier Element Detection** = Maximum compatibility with GoodInfo.tw changes
- **Advanced Special Workflows** = Enhanced handling for Types 5, 7, and 8

## 📈 Version History

- **v1.6.0** - Complete 8 Data Types with Smart Weekly + Daily Automation (CURRENT)
  - ✅ **8 Complete Data Types** - Added EPS x PER Weekly (Type 8) for comprehensive technical analysis
  - ✅ **Smart Weekly + Daily Automation** - Optimized scheduling with weekly updates for non-urgent data
  - ✅ **Server-Friendly Operation** - Reduced from 6 daily runs to smart weekly pattern + daily revenue
  - ✅ **Advanced Special Workflows** - Enhanced handling for Types 5, 7, and 8 with custom parameters
  - ✅ **Complete Manual Access** - All 8 data types available 24/7 via manual triggers
  - ✅ **Enhanced Error Handling** - Improved debug output and recovery mechanisms for complex workflows
  - ✅ **Comprehensive Documentation** - Complete usage examples and troubleshooting for all 8 data types
  - ✅ Updated GetGoodInfo.py to v1.6.0.0 with full 8-type support and GetAll.py with smart processing

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
   python GetAll.py 8 --test    # EPS x PER weekly (NEW!)
   ```

4. **Try individual downloads**
   ```bash
   python GetGoodInfo.py 2330 6    # TSMC equity distribution
   python GetGoodInfo.py 2330 7    # TSMC quarterly performance
   python GetGoodInfo.py 2330 8    # TSMC EPS x PER weekly (NEW!)
   ```

5. **Download complete dataset**
   ```bash
   python GetAll.py 1    # All dividend data (Monday automation)
   python GetAll.py 5    # All revenue data (daily automation)
   python GetAll.py 8    # All EPS x PER weekly data (Friday automation)
   ```

## 📊 Complete Data Type Details (v1.6.0)

### 1. Dividend Policy (殖利率政策)
- **Page**: StockDividendPolicy.asp
- **Folder**: DividendDetail/
- **Content**: Historical dividend distributions, yield rates, payout ratios
- **Workflow**: Standard XLS download
- **Update**: Weekly (Monday 8 AM UTC automation)

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
- **Update**: Weekly (Tuesday 8 AM UTC automation)

### 5. Monthly Revenue (每月營收)
- **Page**: ShowSaleMonChart.asp
- **Folder**: ShowSaleMonChart/
- **Content**: 20-year monthly revenue data, sales trends, growth patterns
- **Workflow**: Special - Click "查20年" → Wait 2 seconds → XLS download
- **Update**: Daily (12 PM UTC automation) - Most time-sensitive

### 6. Equity Distribution (股權結構)
- **Page**: EquityDistributionCatHis.asp
- **Folder**: EquityDistribution/
- **Content**: Shareholder structure, institutional holdings, ownership distribution
- **Workflow**: Standard XLS download
- **Update**: Weekly (Wednesday 8 AM UTC automation)

### 7. Quarterly Business Performance (每季經營績效)
- **Page**: StockBzPerformance.asp with special parameters
- **URL**: `?STOCK_ID={id}&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR`
- **Folder**: StockBzPerformance1/
- **Content**: Quarterly financial data, seasonal trends, YoY comparisons
- **Workflow**: Special URL → Click "查60年" → Wait 2 seconds → XLS download
- **Update**: Weekly (Thursday 8 AM UTC automation)

### 8. EPS x PER Weekly (每週EPS本益比) - NEW!
- **Page**: ShowK_ChartFlow.asp with special parameters
- **URL**: `?RPT_CAT=PER&STOCK_ID={id}`
- **Folder**: ShowK_ChartFlow/
- **Content**: Weekly EPS and P/E ratio data for 5-year period, technical analysis data
- **Workflow**: Special URL → Click "查5年" → Wait 2 seconds → XLS download
- **Update**: Weekly (Friday 8 AM UTC automation) 🆕

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
5. Test thoroughly with all 8 data types
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

### Leveraging Smart Weekly + Daily Automation (v1.6.0):
- 📅 **Smart Scheduling**: Weekly updates for major data, daily for time-sensitive revenue
- 📊 **Complete Coverage**: All 8 data types available with optimized automation
- 🕐 **Predictable Timing**: All runs at 4 PM Taiwan time (end of business day)
- 📱 **Manual Access**: All 8 data types available 24/7 via manual triggers

### For New Data Type 8 (EPS x PER Weekly):
- 📈 **Type 8**: Best for weekly technical analysis and P/E ratio trends (Friday automation)
- 📊 **5-Year Coverage**: Comprehensive weekly EPS and P/E data for technical analysis
- 🕘 Allow extra time for Type 8 due to special workflow requirements
- 🔍 Check debug output if special buttons ("查5年") not found

### For All Data Types:
- 🧪 Always test with `--test` flag first
- 📄 Use batch processing for multiple stocks
- 🔍 Check debug files and screenshots if downloads fail
- ⏰ Respect rate limits (1-second delay built-in, 2 seconds for special workflows)
- 🤖 **Smart**: Leverage weekly + daily automation for optimal data freshness

---

**⭐ Star this repository if it helps you with Taiwan stock data analysis!**

**🆕 New in v1.6.0: Complete 8 data types with smart weekly + daily automation!**

**📅 Optimized scheduling: Weekly updates for major data + daily revenue tracking!**

**🚀 Complete coverage of GoodInfo.tw data sources with enhanced technical analysis support!**