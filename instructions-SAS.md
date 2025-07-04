# Stock Analysis System - Implementation Guide v1.1.0

[![Version](https://img.shields.io/badge/Version-1.1.0-blue)](https://github.com/your-repo/stock-analysis-system)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green)](https://python.org)
[![Architecture](https://img.shields.io/badge/Architecture-Pipeline-orange)](https://github.com/your-repo/stock-analysis-system)

## 📋 Overview

This document provides comprehensive implementation guidelines for the **Modular and Pipeline Stock Analysis System** that integrates GoodInfo.tw data with Google Sheets for professional investment analysis.

### 🎯 System Objectives

- **Automated Data Processing**: Daily processing of 348+ Excel files from GoodInfo.tw
- **Intelligent Data Layering**: Smart data retention and performance optimization
- **Professional Analysis**: Five-model valuation system (DCF, Graham, NAV, P/E, DDM), quality scoring, portfolio optimization
- **Real-Time Price Integration**: Live current prices via GOOGLEFINANCE API with Yahoo Finance fallback
- **Seamless Integration**: Google Sheets presentation layer with GitHub Actions automation
- **Modular Architecture**: Easy extension for new data types and analysis models
- **Pipeline Orchestration**: Efficient data flow management with easy verification

---

## 🏗️ Architecture Overview

**Data Flow Pipeline**:
```
GoodInfo Excel Files → Raw CSV → Cleaned CSV → Analysis CSV → Enhanced CSV (5 Models) → Google Sheets + Live Prices
     Stage 1           Stage 2      Stage 3        Stage 4                    Stage 5
```

**Core Benefits**:
- ✅ **Debuggable**: Inspect CSV outputs at each stage
- ✅ **Testable**: Validate each pipeline stage independently  
- ✅ **Resumable**: Restart from any stage if needed
- ✅ **Modular**: Each stage is completely isolated
- ✅ **Multi-Model**: Five valuation approaches for robust analysis
- ✅ **Real-Time**: Live market prices integrated at presentation layer

---

## 🏗️ Project Structure

```
stock-analysis-system/
├── 📁 src/
│   ├── 📁 pipelines/           # 5-stage pipeline modules
│   │   ├── stage1_excel_to_csv_html.py     # Excel → Raw CSV
│   │   ├── stage2_data_cleaning.py    # Raw → Cleaned CSV
│   │   ├── stage3_basic_analysis.py   # Basic metrics calculation
│   │   ├── stage4_advanced_analysis.py # 5-Model valuations & quality scores
│   │   └── stage5_sheets_publisher.py  # Google Sheets integration + live prices
│   │
│   ├── 📁 models/              # Data models
│   │   ├── stock_data.py       # Stock, financial data models
│   │   └── analysis_results.py # Analysis result models
│   │
│   ├── 📁 analysis/            # Analysis engines
│   │   ├── 📁 valuation/       # DCF, Graham, NAV, P/E, DDM models
│   │   ├── 📁 quality/         # Quality scoring system
│   │   └── 📁 trends/          # Trend analysis
│   │
│   ├── 📁 integrations/        # External systems
│   │   ├── 📁 sheets/          # Google Sheets API
│   │   └── 📁 github/          # GitHub file access
│   │
│   └── 📁 utils/               # Utilities
│       ├── logging_utils.py    # Logging setup
│       ├── config_manager.py   # Configuration management
│       └── validators.py       # Data validation
│
├── 📁 data/                    # Pipeline data directories
│   ├── stage1_raw/             # Raw CSV outputs
│   ├── stage2_cleaned/         # Cleaned CSV outputs
│   ├── stage3_analysis/        # Basic analysis outputs
│   ├── stage4_enhanced/        # Five-model enhanced analysis outputs
│   └── stage5_output/          # Final outputs
│
├── 📁 scripts/
│   └── run_pipeline.py         # Complete pipeline runner
│
├── 📁 .github/workflows/
│   └── Uploader_GoogleSheet.yaml   # GitHub Actions workflow
│
├── requirements.txt
├── .env                       # Environment variables
├── instructions-SAS.md  # Implementation instructions
└── README.md
```

---

## 🚀 Quick Start Implementation

### **Phase 1: Environment Setup (30 minutes)**

```bash
# 1. Create project structure
mkdir stock-analysis-system && cd stock-analysis-system
mkdir -p data/{stage1_raw,stage2_cleaned,stage3_analysis,stage4_enhanced,stage5_output}
mkdir -p src/{pipelines,models,analysis,integrations,utils}
mkdir -p tests/{unit,integration,pipeline_tests}
mkdir -p config scripts

# 2. Setup Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
cat > requirements.txt << 'EOF'
pandas>=1.5.0
openpyxl>=3.0.0
click>=8.0.0
pyyaml>=6.0
google-api-python-client>=2.0.0
google-auth>=2.0.0
requests>=2.28.0
numpy>=1.24.0
pathlib
beautifulsoup4>=4.11.0
EOF

pip install -r requirements.txt
```

---

## 📊 Pipeline Implementation

### **Stage 1: Excel → Raw CSV (60 minutes)**

**File Structure Requirements:**
- Source files must be in directories: `ShowSaleMonChart/`, `DividendDetail/`, `StockBzPerformance/`
- Files follow naming pattern: `{FileType}_{stock_code}_{company_name}.xls`

**Output Files with EXACT Column Orders:**

#### raw_revenue.csv (from ShowSaleMonChart files)
```csv
stock_code,company_name,月別,當月股價開盤,當月股價收盤,當月股價最高,當月股價最低,當月股價漲跌元,當月股價漲跌%,營業收入單月營收億,營業收入單月月增%,營業收入單月年增%,營業收入累計營收億,營業收入累計年增%,合併營業收入單月營收億,合併營業收入單月月增%,合併營業收入單月年增%,合併營業收入累計營收億,合併營業收入累計年增%,file_type,source_file,processing_date
```

#### raw_dividends.csv (from DividendDetail files)
```csv
stock_code,company_name,發放期間(A),發放期間(B),所屬期間,現金股利公積,現金股利合計,股票股利盈餘1,股票股利盈餘2,股票股利公積,股票股利合計,股利合計,填息天數,填權天數,股價年度,除息前股價,除息前殖利率,年均價股價,年均價殖利率,成交價股價,成交價殖利率,最高價股價,最高價殖利率,最低價股價,最低價利率,file_type,source_file,processing_date
```

#### raw_performance.csv (from StockBzPerformance files)
```csv
stock_code,company_name,年度,股本(億),財報評分,收盤,年度股價平均,年度股價漲跌,漲跌(%),獲利金額(億)_營業收入,獲利金額(億)_營業毛利,獲利金額(億)_營業利益,獲利金額(億)_業外損益,獲利金額(億)_稅後淨利,獲利金額(億)_獲利率(%)_營業毛利率,獲利率(%)_營業利益率,獲利率(%)_業外損益率,獲利率(%)_稅後淨利率,ROE(%),ROA(%),稅後EPS,EPS年增,BPS(元),file_type,source_file,processing_date
```

**Data Processing Requirements:**

**ShowSaleMonChart Processing:**
- Excel structure: Header row + monthly data rows
- Header contains: 月別, 當月股價開盤, 當月股價收盤, etc.
- Body contains: 2025/05, 96.6, 101.5, etc. (one row per month)
- Extract stock_code and company_name from filename pattern
- Skip header rows and footer/summary rows

**DividendDetail Processing:**
- Excel structure: Header row + annual data rows + footer
- **CRITICAL**: Skip all rows where 發放期間(A) = "L" or "∟" (quarterly data)
- Keep only annual rows (where 發放期間(A) is a year like "2025", "2024")
- Skip footer rows containing "累計", "合計", etc.
- Header: 發放期間(A), 發放期間(B), 所屬期間, etc.

**StockBzPerformance Processing:**
- Excel structure: Header row + annual data rows
- Header: 年度, 股本(億), 財報評分, etc.
- Body: 25Q1, 8.01, 39, etc. (includes quarterly and annual data)
- Keep both quarterly (25Q1, 24Q4) and annual (2024, 2023) data
- **CRITICAL**: Preserve BPS(元) column for NAV calculations in Stage 4
- Skip header rows and footer/summary rows

**Implementation Interface:**
```python
class SimpleRobustPipeline:
    def __init__(self, output_dir: str)
    def read_file_safely(self, file_path: Path) -> Optional[pd.DataFrame]
    def filter_rows_by_type(self, df: pd.DataFrame, file_type: str) -> List[List]
    def process_file_type(self, file_type: str) -> bool
    def run_pipeline(self) -> Dict
```

**Key Methods:**
- `read_file_safely()`: Try multiple encoding approaches (UTF-8, big5, BeautifulSoup fallback)
- `filter_rows_by_type()`: File-specific row filtering (skip L-rows for dividends, etc.)
- `process_file_type()`: Process all files of one type, standardize columns, add metadata
- `run_pipeline()`: Process all three file types, generate statistics

---

### **Stage 2: Data Cleaning and Standardization**

**Input:** Raw CSV files from Stage 1
**Output:** Cleaned CSV files with standardized data types

**Interface Requirements:**
```python
class DataCleaningPipeline:
    def __init__(self, input_dir: str, output_dir: str)
    def clean_date_columns(self, df: pd.DataFrame, date_patterns: List[str]) -> pd.DataFrame
    def clean_numeric_columns(self, df: pd.DataFrame, numeric_patterns: List[str]) -> pd.DataFrame
    def clean_dividend_data(self, df: pd.DataFrame) -> pd.DataFrame
    def clean_performance_data(self, df: pd.DataFrame) -> pd.DataFrame
    def clean_revenue_data(self, df: pd.DataFrame) -> pd.DataFrame
    def calculate_data_quality_score(self, df: pd.DataFrame) -> pd.Series
    def run_pipeline(self) -> Dict
```

**Key Features:**
- **Date Parsing**: Handle multiple date formats (YYYY/MM, YYYY-MM, MM/DD/YYYY)
- **Numeric Cleaning**: Remove %, commas, currency symbols, handle negative values
- **Data Quality Scoring**: Calculate 0-10 score based on non-null ratio per row
- **File-Specific Logic**: Different cleaning rules for dividend, performance, revenue data
- **Unicode Safety**: Handle encoding issues on Windows systems
- **Metadata Addition**: Add cleaned_date, data_quality_score columns

**Output Files:**
- `cleaned_dividends.csv`
- `cleaned_performance.csv` 
- `cleaned_revenue.csv`
- `stage2_cleaning_summary.csv`
- `stage2_overall_stats.csv`

---

### **Stage 3: Basic Analysis and Metrics Calculation**

**Input:** Cleaned CSV files from Stage 2
**Output:** Combined stock analysis with basic metrics

**Interface Requirements:**
```python
class BasicAnalysisPipeline:
    def __init__(self, input_dir: str, output_dir: str)
    def find_column(self, df: pd.DataFrame, patterns: list) -> str
    def safe_numeric_conversion(self, series: pd.Series) -> pd.Series
    def calculate_dividend_metrics(self, df: pd.DataFrame) -> pd.DataFrame
    def calculate_performance_metrics(self, df: pd.DataFrame) -> pd.DataFrame
    def calculate_revenue_metrics(self, df: pd.DataFrame) -> pd.DataFrame
    def run_pipeline(self) -> dict
```

**Column Mapping Configuration:**
```python
self.column_mappings = {
    'dividend': {
        'cash_dividend': ['現金股利合計', '現金股利公積', '股利合計'],
        'dividend_yield': ['除息前殖利率', '年均價殖利率', '最高價殖利率', '最低價利率'],
        'year': ['發放期間(A)', '股價年度']
    },
    'performance': {
        'roe': ['ROE(%)', 'ROE', 'roe'],
        'roa': ['ROA(%)', 'ROA', 'roa'], 
        'eps': ['稅後EPS', 'EPS', 'eps'],
        'revenue': ['獲利金額(億)_營業收入', '營業收入', '收入'],
        'year': ['年度', 'year']
    },
    'revenue': {
        'mom_growth': ['營業收入單月月增%', '月增%', '月增', 'mom'],
        'yoy_growth': ['營業收入單月年增%', '年增%', '年增', 'yoy'], 
        'monthly_revenue': ['營業收入單月營收億', '營業收入', '營收'],
        'date': ['月別', 'month', '年月']
    }
}
```

**Key Features:**
- **Company Name Preservation**: Maintain company_name throughout all calculations
- **Exact Column Mapping**: Use exact header matching from instructions-SAS.md
- **Multi-Stock Support**: Process multiple stocks per dataset correctly
- **Data Filtering**: Remove invalid years, summary rows, handle quarterly vs annual data
- **Metric Calculations**: 
  - Dividend: avg_dividend, avg_dividend_yield, dividend_consistency
  - Performance: avg_roe, avg_roa, avg_eps, revenue_growth (annualized)
  - Revenue: avg_mom_growth, avg_yoy_growth, revenue_volatility
- **Robust Merging**: Combine metrics on stock_code while preserving company names

**Output:** `stock_analysis.csv` with combined basic metrics for all stocks

---

### **Stage 4: Five-Model Advanced Analysis and Valuations**

**Input:** Basic analysis from Stage 3
**Output:** Enhanced analysis with five valuation models and recommendations

**Interface Requirements:**
```python
class AdvancedAnalysisPipeline:
    def __init__(self, input_dir: str, output_dir: str)
    def calculate_dcf_valuation(self, row: pd.Series) -> float
    def calculate_graham_valuation(self, row: pd.Series) -> float
    def calculate_nav_valuation(self, row: pd.Series) -> float
    def calculate_pe_valuation(self, row: pd.Series) -> float
    def calculate_ddm_valuation(self, row: pd.Series) -> float
    def calculate_quality_score(self, row: pd.Series) -> float
    def calculate_safety_margin(self, intrinsic_value: float, current_price: float) -> float
    def load_additional_data_from_raw_files(self, df: pd.DataFrame) -> pd.DataFrame
    def run_pipeline(self) -> Dict
```

**Five Valuation Models Implementation:**

#### **1. DCF (Discounted Cash Flow) - Weight: 30%**
- **Method**: 5-year EPS projection with declining growth rates
- **Parameters**: 10% discount rate, 2.5% terminal growth
- **Formula**: PV = Σ(Future_EPS / (1+r)^n) + Terminal_Value
- **Growth Decay**: Each year growth rate = previous_rate × 0.8
- **Cap**: Maximum 20% growth rate

#### **2. Graham Formula - Weight: 15%**
- **Method**: Benjamin Graham value formula
- **Formula**: V = EPS × (8.5 + 2g) where g = growth rate
- **Parameters**: Minimum 5% growth assumption, maximum 25% growth cap
- **Conservative**: Designed for value investing approach

#### **3. NAV (Net Asset Value) - Weight: 20%**
- **Method**: Book value adjusted for quality and efficiency
- **Data Source**: BPS(元) from raw_performance.csv
- **Formula**: NAV = BPS × ROE_Quality_Multiplier × ROA_Efficiency_Multiplier
- **Quality Adjustments**:
  - Excellent ROE (≥20%): 1.4x multiplier
  - High ROE (≥15%): 1.3x multiplier
  - Good ROE (≥10%): 1.1x multiplier
  - Fair ROE (≥5%): 1.0x multiplier
  - Poor ROE (<5%): 0.8x multiplier

#### **4. P/E Valuation - Weight: 25%**
- **Method**: Adjusted P/E ratio based on growth and quality
- **Base P/E**: 15 (Taiwan market historical average)
- **Formula**: Value = EPS × Adjusted_PE
- **Adjustments**:
  - Growth multiplier (0.8x to 1.6x based on revenue growth)
  - Quality multiplier (0.7x to 1.4x based on ROE)
  - Risk multiplier (0.9x to 1.1x based on revenue volatility)
- **P/E Range**: Capped between 6 and 40

#### **5. DDM (Dividend Discount Model) - Weight: 10%**
- **Method**: Gordon Growth Model with sustainability analysis
- **Data Source**: avg_dividend from cleaned dividend data
- **Formula**: 
  - Simple DDM: P = D / r (for low/no growth)
  - Gordon Growth: P = D₁ / (r - g) (for growing dividends)
- **Growth Calculation**: g = ROE × Retention_Ratio
- **Parameters**: 8% required return, max 10% dividend growth
- **Adjustments**: Consistency multiplier based on dividend payment history

**Five-Model Consensus Calculation:**
```python
default_weights = {
    'dcf': 0.30,      # 30% - Primary valuation method
    'graham': 0.15,   # 15% - Conservative value approach
    'nav': 0.20,      # 20% - Asset-based valuation
    'pe': 0.25,       # 25% - Market-based approach
    'ddm': 0.10       # 10% - Income-based approach
}

# Weighted consensus only includes models with valid (>0) results
# Weights are recalculated proportionally for valid models only
```

**Quality Scoring (0-10 scale):**
- **Financial Health (30%)**: Based on ROE + ROA performance
- **Growth Consistency (25%)**: Based on revenue growth patterns
- **Profitability (25%)**: Based on EPS trends
- **Dividend Consistency (20%)**: Based on dividend payment history

**Investment Recommendations:**
- **Strong Buy**: Quality ≥ 7 AND Safety Margin ≥ 30%
- **Buy**: Quality ≥ 6 AND Safety Margin ≥ 20%
- **Hold**: Quality ≥ 5 AND Safety Margin ≥ 10%
- **Weak Hold**: Quality ≥ 4
- **Avoid**: Quality < 4

**Rankings:**
- **Quality Rank**: Based on quality_score (descending)
- **Value Rank**: Based on safety_margin (descending)
- **Overall Rank**: Average of Quality + Value ranks

**Additional Data Loading:**
- **BPS Data**: Loads BPS(元) from raw_performance.csv for NAV calculations
- **Latest Values**: Uses most recent BPS value per stock
- **Error Handling**: Graceful fallback if raw data unavailable

**Output Files:**
- `enhanced_analysis.csv`: Complete analysis with all five models
- `analysis_summary.csv`: Summary statistics and model averages
- `top_stocks.csv`: Top 10 stocks with company names

---

### **Stage 5: Google Sheets Dashboard Publisher with Real-Time Prices**

**Input:** Enhanced analysis from Stage 4
**Output:** Professional 5-tab Google Sheets dashboard with live current prices

**Interface Requirements:**
```python
class SheetsPublisher:
    def __init__(self, credentials_path: str, sheet_id: str, input_dir: str)
    def _authenticate(self, credentials_path: str)
    def _update_range(self, range_name: str, values: list, value_input_option: str)
    def load_company_name_lookup(self)
    def ensure_company_names(self, df: pd.DataFrame) -> pd.DataFrame
    def create_required_tabs(self)
    def create_current_snapshot_tab(self, df: pd.DataFrame)
    def create_top_picks_tab(self, df: pd.DataFrame)
    def create_single_pick_tab(self, df: pd.DataFrame)
    def create_summary_tab(self, df: pd.DataFrame)
    def create_last_updated_tab(self)
    def run_pipeline(self) -> dict
```

**Real-Time Price Integration:**
- **Primary Source**: `GOOGLEFINANCE("TPE:"&stock_code)` for Taiwan Stock Exchange
- **Fallback Source**: Yahoo Finance IMPORTXML for backup price data
- **Formula**: `=IFERROR(GOOGLEFINANCE("TPE:"&A2),IFERROR(IMPORTXML("https://tw.stock.yahoo.com/quote/"&A2&".TW/dividend", "/html/body/div[1]/div/div/div/div/div[4]/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/span[1]"),"無法取得"))`
- **Update Frequency**: Real-time during market hours
- **Error Handling**: Shows "無法取得" if both sources fail

**Dashboard Tabs:**

1. **Current Snapshot**: All stocks with complete metrics + real-time prices
   - **Updated Columns**: Stock Code, Company Name, **Current Price**, Quality Score, DCF Value, Graham Value, NAV Value, PE Value, DDM Value, Five Model Consensus, Original Consensus, Safety Margin, Recommendation, Rankings, Financial Metrics
   - **Column Structure**: A=Stock Code, B=Company Name, **C=Current Price**, D=Quality Score, E=DCF Value, F=Graham Value, G=NAV Value, H=PE Value, I=DDM Value, J=Five Model Consensus, K=Original Consensus, L=Safety Margin, M=Recommendation, N=Quality Rank, O=Overall Rank, P=ROE, Q=ROA, R=EPS, S=Dividend Yield
   - Shows all analyzed stocks with company names and live market prices

2. **Top Picks**: Best investment opportunities (top 20) + current prices
   - **Updated Columns**: Rank, Stock Code, Company Name, **Current Price**, Recommendation, Quality Score, Safety Margin, Five Model Consensus, Key Strengths
   - Filters: Hold and above recommendations, or top 20 by overall rank
   - Includes live current prices for easy comparison with valuations

3. **Single Pick**: Interactive stock lookup + real-time price display
   - Input: Stock code in cell B2 (defaults to top-ranked stock)
   - **Row 4**: **現價** - Shows live current price via formula lookup
   - Output: Complete analysis via formula lookups from Current Snapshot (adjusted for new column structure)
   - Shows: Company name, current price, all five model valuations, investment summary, risk level, position sizing
   - **Updated Column References**: All formulas adjusted for Current Price insertion (C=Current Price, D=Quality, E=DCF, F=Graham, G=NAV, H=PE, I=DDM, etc.)
   - **Weight Adjustment**: Interactive E2-E6 cells for custom five-model weighting

4. **Summary**: Dashboard overview
   - Analysis statistics: Total stocks, recommendation breakdown, average quality
   - Top 5 stocks with stock codes and company names
   - Five-model average valuations summary

5. **Last Updated**: System status and metadata
   - Timestamp, system version (2.2.0), data source
   - Pipeline completion status for all 5 stages
   - **Five-Model Features**: DCF, Graham, NAV, P/E, DDM implementation status
   - **Real-time price feeds**: GOOGLEFINANCE + Yahoo fallback
   - Active features list, dashboard URL

**Key Features:**
- **Company Name Lookup**: Automatically fills missing company names from raw data
- **Real-time Price Formulas**: Live price lookups using dual fallback approach
- **Formula Execution**: Uses `USER_ENTERED` value input option for executable formulas
- **Five-Model Integration**: All valuation models displayed and interactive
- **Professional Formatting**: Clean headers, proper data types, organized layout
- **Error Handling**: IFERROR formulas prevent display issues
- **Rate Limiting**: Built-in delays between API calls
- **Live Updates**: Prices refresh automatically during market hours

---

## 🧪 Pipeline Runner

**Interface Requirements:**
```python
def setup_unicode_environment()
def check_source_directories() -> Tuple[bool, int]
def validate_stage_output(stage_num: int, expected_files: list) -> bool
def run_subprocess_safely(cmd_args, stage_name)
def run_complete_pipeline()
```

**Pipeline Features:**
- **Unicode Safety**: Handle special characters on Windows systems
- **Directory Validation**: Check source directories exist and contain Excel files
- **Stage Validation**: Verify each stage produces expected outputs with data
- **Error Handling**: Provide troubleshooting guidance for common issues
- **Progress Tracking**: Show file counts, row counts, processing status
- **Subprocess Management**: Safe execution with proper encoding

**Validation Checks:**
- **Stage 1**: Verify 3 CSV files created with correct row/column counts, multiple stocks
- **Stage 2**: Verify cleaned files with data quality metrics
- **Stage 3**: Verify combined analysis file with calculated metrics
- **Stage 4**: Verify enhanced analysis with five valuation models and recommendations
- **Stage 5**: Verify Google Sheets publication with real-time prices (if credentials available)

**Error Recovery:**
- File lock detection (Excel files open)
- Permission issues guidance
- Missing directory troubleshooting
- Unicode encoding fallbacks
- Partial success handling

---

## 🚀 GitHub Actions Workflow

```yaml
# .github/workflows/Uploader_GoogleSheet.yaml.yml
name: Daily Stock Analysis Pipeline

on:
  schedule:
    - cron: '30 10 * * *'  # 6:30 PM Taiwan Time
  workflow_dispatch:
    inputs:
      analysis_mode:
        description: 'Analysis Mode'
        required: true
        default: 'full'
        type: choice
        options: [full, test_mode, quick_update]

jobs:
  analyze:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        cache: 'pip'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Configure credentials
      env:
        GOOGLE_SHEETS_CREDENTIALS: ${{ secrets.GOOGLE_SHEETS_CREDENTIALS }}
      run: echo "$GOOGLE_SHEETS_CREDENTIALS" > credentials.json
    
    - name: Run Complete Pipeline
      env:
        GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
      run: python scripts/run_pipeline.py
    
    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: analysis-results
        path: data/
        retention-days: 7
```

---

## 📋 Quick Start Commands

```bash
# 1. Setup project
git clone <your-repo> && cd stock-analysis-system
python -m venv venv && source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Prepare source directories
# Ensure these directories exist with Excel files:
# ShowSaleMonChart/ShowSaleMonChart_*.xls
# DividendDetail/DividendDetail_*.xls
# StockBzPerformance/StockBzPerformance_*.xls

# 3. Run complete pipeline
python scripts/run_pipeline.py

# 4. Run individual stages (optional)
python -m src.pipelines.stage1_excel_to_csv_html
python -m src.pipelines.stage2_data_cleaning
python -m src.pipelines.stage3_basic_analysis
python -m src.pipelines.stage4_advanced_analysis  # Five-model enhanced
python -m src.pipelines.stage5_sheets_publisher --credentials google_key.json --sheet-id YOUR_SHEET_ID

# 5. Validate outputs at each stage
ls data/stage1_raw/      # Raw CSV files with BPS data
ls data/stage2_cleaned/  # Cleaned CSV files
ls data/stage3_analysis/ # Basic analysis
ls data/stage4_enhanced/ # Five-model enhanced analysis
```

---

## 🎯 Success Criteria

### **Stage Outputs**
- **Stage 1**: ✅ 3 Raw CSV files with exact column orders, company names, multiple stocks per file, BPS(元) preserved
- **Stage 2**: ✅ 3 Cleaned files with standardized data types, quality scores
- **Stage 3**: ✅ 1 Combined analysis file with basic metrics for all stocks
- **Stage 4**: ✅ 1 Enhanced analysis with five valuation models, quality scores, recommendations
- **Stage 5**: ✅ 5-tab Google Sheets dashboard with company names and real-time prices throughout

### **Final Dashboard Features**
1. **Current Snapshot**: All stocks with complete five-model analysis, company names, and live current prices
2. **Top Picks**: Best opportunities with company names, current prices, and five-model consensus
3. **Single Pick**: Interactive lookup showing company name, current price, and all five model valuations with custom weighting
4. **Summary**: Overview with company names in top 5 list and five-model averages
5. **Last Updated**: System status and metadata with five-model and real-time price feed information

### **Data Quality Standards**
- All stock codes have corresponding company names
- **Five valuation models** calculated for each stock: DCF, Graham, NAV, P/E, DDM
- **Real-time prices** displayed using GOOGLEFINANCE API with Yahoo Finance fallback
- Column orders exactly match specifications (with Current Price as Column C)
- **Five-model consensus** calculated with configurable weights
- Data types properly standardized (dates as datetime, numbers as float)
- No missing critical data (ROE, EPS, dividend information, BPS for NAV)
- Proper filtering applied (no quarterly L-rows in dividend data)
- Multiple encoding approaches ensure data integrity
- **Live price updates** during market hours for enhanced analysis

### **Five-Model Valuation Features (v1.1.0)**
- **DCF**: 5-year projection with declining growth rates (30% weight)
- **Graham**: Conservative value formula with growth adjustments (15% weight)
- **NAV**: Asset-based valuation using BPS + ROE quality multipliers (20% weight)
- **P/E**: Market-based approach with growth, quality, and risk adjustments (25% weight)
- **DDM**: Income-based dividend discount model with sustainability analysis (10% weight)
- **Consensus**: Weighted average of all valid models with proportional rebalancing
- **Interactive**: Custom weight adjustment in Single Pick tab
- **Comprehensive**: Original two-model consensus preserved for comparison

### **Real-Time Price Features (v1.1.0)**
- **Primary**: GOOGLEFINANCE("TPE:"&stock_code) for Taiwan stocks
- **Fallback**: Yahoo Finance IMPORTXML for backup data
- **Integration**: Current Price column (Column C) in all major tabs
- **Updates**: Automatic refresh during market hours
- **Error Handling**: Graceful fallback with "無法取得" for unavailable prices

This comprehensive implementation guide provides the exact specifications needed to recreate the enhanced Python pipeline with five-model valuation and real-time price integration, maintaining consistency with the actual codebase while documenting all advanced analysis capabilities.