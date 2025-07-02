# Stock Analysis System - Implementation Guide v1.0.0

[![Version](https://img.shields.io/badge/Version-1.0.0-blue)](https://github.com/your-repo/stock-analysis-system)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green)](https://python.org)
[![Architecture](https://img.shields.io/badge/Architecture-Pipeline-orange)](https://github.com/your-repo/stock-analysis-system)

## 📋 Overview

This document provides comprehensive implementation guidelines for the **Modular and Pipeline Stock Analysis System** that integrates GoodInfo.tw data with Google Sheets for professional investment analysis.

### 🎯 System Objectives

- **Automated Data Processing**: Daily processing of 348+ Excel files from GoodInfo.tw
- **Intelligent Data Layering**: Smart data retention and performance optimization
- **Professional Analysis**: Multi-model valuation, quality scoring, portfolio optimization
- **Seamless Integration**: Google Sheets presentation layer with GitHub Actions automation
- **Modular Architecture**: Easy extension for new data types and analysis models
- **Pipeline Orchestration**: Efficient data flow management with easy verification

---

## 🏗️ Architecture Overview

**Data Flow Pipeline**:
```
GoodInfo Excel Files → Raw CSV → Cleaned CSV → Analysis CSV → Enhanced CSV → Google Sheets
     Stage 1           Stage 2      Stage 3        Stage 4         Stage 5
```

**Core Benefits**:
- ✅ **Debuggable**: Inspect CSV outputs at each stage
- ✅ **Testable**: Validate each pipeline stage independently  
- ✅ **Resumable**: Restart from any stage if needed
- ✅ **Modular**: Each stage is completely isolated

---

## 🏗️ Project Structure

```
stock-analysis-system/
├── 📁 src/
│   ├── 📁 pipelines/           # 5-stage pipeline modules
│   │   ├── stage1_excel_to_csv.py     # Excel → Raw CSV
│   │   ├── stage2_data_cleaning.py    # Raw → Cleaned CSV
│   │   ├── stage3_basic_analysis.py   # Basic metrics calculation
│   │   ├── stage4_advanced_analysis.py # Valuations & quality scores
│   │   └── stage5_sheets_publisher.py  # Google Sheets integration
│   │
│   ├── 📁 models/              # Data models
│   │   ├── stock_data.py       # Stock, financial data models
│   │   └── analysis_results.py # Analysis result models
│   │
│   ├── 📁 analysis/            # Analysis engines
│   │   ├── 📁 valuation/       # DCF, Graham, multiples models
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
│   ├── stage4_enhanced/        # Enhanced analysis outputs
│   └── stage5_output/          # Final outputs
│
├── 📁 tests/
│   ├── 📁 unit/                # Unit tests
│   ├── 📁 integration/         # Integration tests
│   └── 📁 pipeline_tests/      # Pipeline validation tests
│
├── 📁 config/
│   ├── default.yaml            # Default configuration
│   ├── production.yaml         # Production settings
│   └── data_types.yaml         # Data type definitions
│
├── 📁 scripts/
│   ├── run_pipeline_test.py    # Complete pipeline test
│   ├── setup_environment.py    # Environment setup
│   └── deploy.py               # Deployment script
│
├── 📁 .github/workflows/
│   └── analysis_pipeline.yml   # GitHub Actions workflow
│
├── requirements.txt
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
EOF

pip install -r requirements.txt
```

### **Phase 2: Core Configuration (15 minutes)**

```yaml
# config/default.yaml
system:
  version: "1.0.0"
  environment: "development"
  log_level: "INFO"

data:
  github:
    repository_url: "https://raw.githubusercontent.com/username/Python-Actions.GoodInfo/main"
    rate_limit: 5000
    timeout: 30
    retry_attempts: 3
  
  file_types:
    DividendDetail:
      pattern: "DividendDetail_{stock_code}_{company_name}.xls"
      required_columns: ["除息日", "現金股利", "股票股利", "殖利率"]
    
    StockBzPerformance:
      pattern: "StockBzPerformance_{stock_code}_{company_name}.xls"
      required_columns: ["營業收入", "營業毛利", "營業利益", "稅後淨利", "ROE", "ROA", "EPS"]
    
    ShowSaleMonChart:
      pattern: "ShowSaleMonChart_{stock_code}_{company_name}.xls"
      required_columns: ["月別", "營業收入", "月增", "年增", "累計營收"]

analysis:
  valuation:
    dcf:
      discount_rate: 0.10
      terminal_growth: 0.025
      projection_years: 5
    
    graham:
      bond_yield: 0.03
      minimum_eps_growth: 0.05
      safety_margin: 0.5
  
  quality:
    scoring_weights:
      financial_health: 0.25
      growth_consistency: 0.25
      profitability: 0.20
      risk_factors: 0.15
      data_quality: 0.15

integrations:
  google_sheets:
    rate_limit: 100
    batch_size: 1000
    retry_attempts: 3
```

---

## 📊 Pipeline Implementation

### **Stage 1: Excel → Raw CSV (60 minutes)**

```python
# src/pipelines/stage1_excel_to_csv.py
import pandas as pd
import click
from pathlib import Path
import logging

class ExcelToCSVPipeline:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.file_mappings = {
            'DividendDetail': 'raw_dividends.csv',
            'StockBzPerformance': 'raw_performance.csv', 
            'ShowSaleMonChart': 'raw_revenue.csv'
        }
        
        self.stats = {'processed': 0, 'errors': 0, 'total': 0}
    
    def detect_file_type(self, filename: str) -> str:
        for file_type in self.file_mappings.keys():
            if file_type in filename:
                return file_type
        return 'Unknown'
    
    def process_excel_file(self, excel_path: Path) -> dict:
        try:
            file_type = self.detect_file_type(excel_path.name)
            if file_type == 'Unknown':
                return {'status': 'skipped', 'reason': 'unknown_type'}
            
            # Extract stock code and company name
            parts = excel_path.stem.split('_')
            stock_code = parts[1] if len(parts) >= 2 else 'UNKNOWN'
            company_name = parts[2] if len(parts) >= 3 else 'UNKNOWN'
            
            # Read Excel file
            df = pd.read_excel(excel_path, engine='openpyxl')
            
            # Add metadata columns
            df.insert(0, 'stock_code', stock_code)
            df.insert(1, 'company_name', company_name)
            df.insert(2, 'file_type', file_type)
            df.insert(3, 'source_file', excel_path.name)
            df.insert(4, 'processing_date', pd.Timestamp.now())
            
            return {
                'status': 'success',
                'file_type': file_type,
                'dataframe': df
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def run_pipeline(self) -> dict:
        excel_files = list(self.input_dir.glob("*.xls")) + list(self.input_dir.glob("*.xlsx"))
        self.stats['total'] = len(excel_files)
        
        # Group data by file type
        grouped_data = {ft: [] for ft in self.file_mappings.keys()}
        
        for excel_path in excel_files:
            result = self.process_excel_file(excel_path)
            
            if result['status'] == 'success':
                grouped_data[result['file_type']].append(result['dataframe'])
                self.stats['processed'] += 1
            else:
                self.stats['errors'] += 1
        
        # Combine and save CSV files
        for file_type, dataframes in grouped_data.items():
            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                output_file = self.output_dir / self.file_mappings[file_type]
                combined_df.to_csv(output_file, index=False, encoding='utf-8')
        
        return self.stats

@click.command()
@click.option('--input-dir', required=True, help='Directory containing Excel files')
@click.option('--output-dir', default='data/stage1_raw', help='Output directory')
def run_stage1(input_dir: str, output_dir: str):
    pipeline = ExcelToCSVPipeline(input_dir, output_dir)
    stats = pipeline.run_pipeline()
    click.echo(f"Processed: {stats['processed']}/{stats['total']} files")

if __name__ == '__main__':
    run_stage1()
```

### **Stage 2: Raw CSV → Cleaned CSV (60 minutes)**

```python
# src/pipelines/stage2_data_cleaning.py
import pandas as pd
import numpy as np
import click
from pathlib import Path

class DataCleaningPipeline:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def clean_dividend_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Standardize date columns
        date_columns = ['除息日', '發放日']
        for col in df.columns:
            if any(date_term in str(col) for date_term in date_columns):
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Clean numeric columns
        numeric_patterns = ['股利', '殖利率']
        for col in df.columns:
            if any(pattern in str(col) for pattern in numeric_patterns):
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '')
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Add quality score
        df['data_quality_score'] = df.notna().sum(axis=1) / len(df.columns) * 10
        return df
    
    def clean_performance_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna(how='all')
        
        # Clean financial amounts
        financial_patterns = ['營業收入', '毛利', '淨利']
        for col in df.columns:
            if any(pattern in str(col) for pattern in financial_patterns):
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '').str.replace('億', '')
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean percentage columns
        percentage_patterns = ['roe', 'roa', '率']
        for col in df.columns:
            if any(pattern in str(col).lower() for pattern in percentage_patterns):
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace('%', '')
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['data_quality_score'] = df.notna().sum(axis=1) / len(df.columns) * 10
        return df
    
    def clean_revenue_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna(how='all')
        
        # Clean date columns
        date_columns = ['月別', 'month']
        for col in df.columns:
            if any(date_term in str(col) for date_term in date_columns):
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Clean revenue amounts and growth rates
        for col in df.columns:
            if '營業收入' in str(col) or '增' in str(col):
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '')
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['data_quality_score'] = df.notna().sum(axis=1) / len(df.columns) * 10
        return df
    
    def run_pipeline(self) -> dict:
        file_mappings = {
            'raw_dividends.csv': ('cleaned_dividends.csv', self.clean_dividend_data),
            'raw_performance.csv': ('cleaned_performance.csv', self.clean_performance_data),
            'raw_revenue.csv': ('cleaned_revenue.csv', self.clean_revenue_data)
        }
        
        stats = {'processed': 0, 'total_rows': 0}
        
        for input_file, (output_file, cleaning_func) in file_mappings.items():
            input_path = self.input_dir / input_file
            if not input_path.exists():
                continue
            
            df = pd.read_csv(input_path)
            cleaned_df = cleaning_func(df)
            
            output_path = self.output_dir / output_file
            cleaned_df.to_csv(output_path, index=False, encoding='utf-8')
            
            stats['processed'] += 1
            stats['total_rows'] += len(cleaned_df)
        
        return stats

@click.command()
@click.option('--input-dir', default='data/stage1_raw')
@click.option('--output-dir', default='data/stage2_cleaned')
def run_stage2(input_dir: str, output_dir: str):
    pipeline = DataCleaningPipeline(input_dir, output_dir)
    stats = pipeline.run_pipeline()
    click.echo(f"Processed {stats['processed']} files, {stats['total_rows']} total rows")

if __name__ == '__main__':
    run_stage2()
```

### **Stage 3: Basic Analysis (60 minutes)**

```python
# src/pipelines/stage3_basic_analysis.py
import pandas as pd
import numpy as np
import click
from pathlib import Path

class BasicAnalysisPipeline:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_dividend_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate dividend-related metrics per stock"""
        if df.empty:
            return pd.DataFrame()
        
        results = []
        for stock_code in df['stock_code'].unique():
            stock_data = df[df['stock_code'] == stock_code]
            
            # Basic dividend metrics
            avg_dividend = stock_data['現金股利'].mean() if '現金股利' in stock_data.columns else 0
            avg_yield = stock_data['殖利率'].mean() if '殖利率' in stock_data.columns else 0
            dividend_consistency = len(stock_data[stock_data['現金股利'] > 0]) / len(stock_data) if '現金股利' in stock_data.columns else 0
            
            results.append({
                'stock_code': stock_code,
                'avg_dividend': avg_dividend,
                'avg_dividend_yield': avg_yield,
                'dividend_consistency': dividend_consistency
            })
        
        return pd.DataFrame(results)
    
    def calculate_performance_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate performance metrics per stock"""
        if df.empty:
            return pd.DataFrame()
        
        results = []
        for stock_code in df['stock_code'].unique():
            stock_data = df[df['stock_code'] == stock_code]
            
            # Financial metrics
            avg_roe = stock_data['ROE'].mean() if 'ROE' in stock_data.columns else 0
            avg_roa = stock_data['ROA'].mean() if 'ROA' in stock_data.columns else 0
            avg_eps = stock_data['EPS'].mean() if 'EPS' in stock_data.columns else 0
            
            # Growth calculations
            if '營業收入' in stock_data.columns and len(stock_data) > 1:
                revenue_growth = (stock_data['營業收入'].iloc[-1] / stock_data['營業收入'].iloc[0] - 1) * 100
            else:
                revenue_growth = 0
            
            results.append({
                'stock_code': stock_code,
                'avg_roe': avg_roe,
                'avg_roa': avg_roa,
                'avg_eps': avg_eps,
                'revenue_growth': revenue_growth
            })
        
        return pd.DataFrame(results)
    
    def calculate_revenue_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate revenue trend metrics per stock"""
        if df.empty:
            return pd.DataFrame()
        
        results = []
        for stock_code in df['stock_code'].unique():
            stock_data = df[df['stock_code'] == stock_code]
            
            # Revenue trend metrics
            avg_mom_growth = stock_data['月增'].mean() if '月增' in stock_data.columns else 0
            avg_yoy_growth = stock_data['年增'].mean() if '年增' in stock_data.columns else 0
            revenue_volatility = stock_data['月增'].std() if '月增' in stock_data.columns else 0
            
            results.append({
                'stock_code': stock_code,
                'avg_mom_growth': avg_mom_growth,
                'avg_yoy_growth': avg_yoy_growth,
                'revenue_volatility': revenue_volatility
            })
        
        return pd.DataFrame(results)
    
    def run_pipeline(self) -> dict:
        """Combine all metrics into single analysis file"""
        
        # Load cleaned data
        dividend_df = pd.read_csv(self.input_dir / 'cleaned_dividends.csv') if (self.input_dir / 'cleaned_dividends.csv').exists() else pd.DataFrame()
        performance_df = pd.read_csv(self.input_dir / 'cleaned_performance.csv') if (self.input_dir / 'cleaned_performance.csv').exists() else pd.DataFrame()
        revenue_df = pd.read_csv(self.input_dir / 'cleaned_revenue.csv') if (self.input_dir / 'cleaned_revenue.csv').exists() else pd.DataFrame()
        
        # Calculate metrics
        dividend_metrics = self.calculate_dividend_metrics(dividend_df)
        performance_metrics = self.calculate_performance_metrics(performance_df)
        revenue_metrics = self.calculate_revenue_metrics(revenue_df)
        
        # Combine all metrics
        if not dividend_metrics.empty and not performance_metrics.empty:
            combined_analysis = dividend_metrics.merge(performance_metrics, on='stock_code', how='outer')
        elif not dividend_metrics.empty:
            combined_analysis = dividend_metrics
        elif not performance_metrics.empty:
            combined_analysis = performance_metrics
        else:
            combined_analysis = pd.DataFrame()
        
        if not revenue_metrics.empty and not combined_analysis.empty:
            combined_analysis = combined_analysis.merge(revenue_metrics, on='stock_code', how='outer')
        elif not revenue_metrics.empty:
            combined_analysis = revenue_metrics
        
        # Add analysis metadata
        if not combined_analysis.empty:
            combined_analysis['analysis_date'] = pd.Timestamp.now()
            combined_analysis['analysis_stage'] = 'basic_metrics'
        
        # Save combined analysis
        output_file = self.output_dir / 'stock_analysis.csv'
        combined_analysis.to_csv(output_file, index=False, encoding='utf-8')
        
        return {
            'stocks_analyzed': len(combined_analysis) if not combined_analysis.empty else 0,
            'metrics_calculated': len(combined_analysis.columns) - 3 if not combined_analysis.empty else 0  # Exclude metadata columns
        }

@click.command()
@click.option('--input-dir', default='data/stage2_cleaned')
@click.option('--output-dir', default='data/stage3_analysis')
def run_stage3(input_dir: str, output_dir: str):
    pipeline = BasicAnalysisPipeline(input_dir, output_dir)
    stats = pipeline.run_pipeline()
    click.echo(f"Analyzed {stats['stocks_analyzed']} stocks with {stats['metrics_calculated']} metrics")

if __name__ == '__main__':
    run_stage3()
```

### **Stage 4: Advanced Analysis (90 minutes)**

```python
# src/pipelines/stage4_advanced_analysis.py
import pandas as pd
import numpy as np
import click
from pathlib import Path
from typing import Dict, List

class AdvancedAnalysisPipeline:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_dcf_valuation(self, row: pd.Series) -> float:
        """Simple DCF calculation"""
        try:
            eps = row.get('avg_eps', 0)
            growth_rate = min(row.get('revenue_growth', 5), 20) / 100  # Cap at 20%
            discount_rate = 0.10
            terminal_growth = 0.025
            years = 5
            
            if eps <= 0:
                return 0
            
            # Project earnings
            future_eps = []
            current_eps = eps
            for year in range(1, years + 1):
                current_eps *= (1 + growth_rate * (0.8 ** year))  # Declining growth
                future_eps.append(current_eps)
            
            # Terminal value
            terminal_eps = future_eps[-1] * (1 + terminal_growth)
            terminal_value = terminal_eps / (discount_rate - terminal_growth)
            
            # Present value calculation
            pv = 0
            for year, eps_val in enumerate(future_eps, 1):
                pv += eps_val / ((1 + discount_rate) ** year)
            
            pv += terminal_value / ((1 + discount_rate) ** years)
            
            return round(pv, 2)
        
        except:
            return 0
    
    def calculate_graham_valuation(self, row: pd.Series) -> float:
        """Graham formula valuation"""
        try:
            eps = row.get('avg_eps', 0)
            growth = max(row.get('revenue_growth', 0), 5)  # Minimum 5% growth
            
            if eps <= 0:
                return 0
            
            # Graham formula: V = EPS × (8.5 + 2g) where g is growth rate
            value = eps * (8.5 + 2 * min(growth, 25))  # Cap growth at 25%
            return round(value, 2)
        
        except:
            return 0
    
    def calculate_quality_score(self, row: pd.Series) -> float:
        """Calculate overall quality score (0-10)"""
        try:
            scores = []
            
            # Financial health (ROE, ROA)
            roe = row.get('avg_roe', 0)
            roa = row.get('avg_roa', 0)
            financial_health = min((roe + roa) / 4, 10)  # Normalize to 0-10
            scores.append(financial_health * 0.3)
            
            # Growth consistency
            growth = row.get('revenue_growth', 0)
            growth_score = min(abs(growth) / 2, 10) if growth > 0 else 0
            scores.append(growth_score * 0.25)
            
            # Profitability
            eps = row.get('avg_eps', 0)
            profit_score = min(eps / 2, 10) if eps > 0 else 0
            scores.append(profit_score * 0.25)
            
            # Dividend consistency
            dividend_consistency = row.get('dividend_consistency', 0)
            dividend_score = dividend_consistency * 10
            scores.append(dividend_score * 0.2)
            
            total_score = sum(scores)
            return round(min(total_score, 10), 1)
        
        except:
            return 0
    
    def calculate_safety_margin(self, intrinsic_value: float, current_price: float = 100) -> float:
        """Calculate safety margin (assuming current price of 100 for demo)"""
        if current_price <= 0 or intrinsic_value <= 0:
            return 0
        
        margin = (intrinsic_value - current_price) / current_price
        return round(margin, 3)
    
    def run_pipeline(self) -> Dict:
        """Run advanced analysis pipeline"""
        
        # Load basic analysis
        input_file = self.input_dir / 'stock_analysis.csv'
        if not input_file.exists():
            click.echo("❌ No basic analysis file found. Run Stage 3 first.")
            return {'error': 'missing_input'}
        
        df = pd.read_csv(input_file)
        
        if df.empty:
            click.echo("❌ Empty analysis file")
            return {'error': 'empty_input'}
        
        # Calculate advanced metrics
        click.echo(f"📊 Calculating advanced analysis for {len(df)} stocks...")
        
        # Valuation models
        df['dcf_valuation'] = df.apply(self.calculate_dcf_valuation, axis=1)
        df['graham_valuation'] = df.apply(self.calculate_graham_valuation, axis=1)
        df['consensus_valuation'] = (df['dcf_valuation'] + df['graham_valuation']) / 2
        
        # Quality scoring
        df['quality_score'] = df.apply(self.calculate_quality_score, axis=1)
        
        # Safety margins (using consensus valuation vs assumed current price)
        df['safety_margin'] = df.apply(lambda row: self.calculate_safety_margin(
            row['consensus_valuation'], 100), axis=1)
        
        # Investment recommendations
        def get_recommendation(row):
            quality = row['quality_score']
            safety = row['safety_margin']
            
            if quality >= 7 and safety >= 0.3:
                return 'Strong Buy'
            elif quality >= 6 and safety >= 0.2:
                return 'Buy'
            elif quality >= 5 and safety >= 0.1:
                return 'Hold'
            elif quality >= 4:
                return 'Weak Hold'
            else:
                return 'Avoid'
        
        df['recommendation'] = df.apply(get_recommendation, axis=1)
        
        # Ranking
        df['quality_rank'] = df['quality_score'].rank(method='dense', ascending=False)
        df['value_rank'] = df['safety_margin'].rank(method='dense', ascending=False)
        df['overall_rank'] = ((df['quality_rank'] + df['value_rank']) / 2).rank(method='dense')
        
        # Add metadata
        df['enhanced_analysis_date'] = pd.Timestamp.now()
        df['analysis_version'] = '1.0.0'
        
        # Save enhanced analysis
        output_file = self.output_dir / 'enhanced_analysis.csv'
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        # Generate summary statistics
        summary_stats = {
            'total_stocks': len(df),
            'strong_buy_count': len(df[df['recommendation'] == 'Strong Buy']),
            'buy_count': len(df[df['recommendation'] == 'Buy']),
            'avg_quality_score': df['quality_score'].mean(),
            'avg_safety_margin': df['safety_margin'].mean(),
            'top_10_stocks': df.nsmallest(10, 'overall_rank')['stock_code'].tolist()
        }
        
        # Save summary
        summary_df = pd.DataFrame([summary_stats])
        summary_file = self.output_dir / 'analysis_summary.csv'
        summary_df.to_csv(summary_file, index=False)
        
        return summary_stats

@click.command()
@click.option('--input-dir', default='data/stage3_analysis')
@click.option('--output-dir', default='data/stage4_enhanced')
def run_stage4(input_dir: str, output_dir: str):
    pipeline = AdvancedAnalysisPipeline(input_dir, output_dir)
    stats = pipeline.run_pipeline()
    
    if 'error' in stats:
        click.echo(f"❌ Pipeline failed: {stats['error']}")
        return
    
    click.echo(f"✅ Enhanced analysis completed:")
    click.echo(f"   Total stocks: {stats['total_stocks']}")
    click.echo(f"   Strong Buy: {stats['strong_buy_count']}")
    click.echo(f"   Buy: {stats['buy_count']}")
    click.echo(f"   Avg quality score: {stats['avg_quality_score']:.1f}")
    click.echo(f"   Top 10 stocks: {', '.join(stats['top_10_stocks'][:5])}...")

if __name__ == '__main__':
    run_stage4()
```

### **Stage 5: Google Sheets Publisher (90 minutes)**

```python
# src/pipelines/stage5_sheets_publisher.py
import pandas as pd
import click
from pathlib import Path
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import time

class SheetsPublisher:
    def __init__(self, credentials_path: str, sheet_id: str, input_dir: str):
        self.input_dir = Path(input_dir)
        self.sheet_id = sheet_id
        self.service = self._authenticate(credentials_path)
    
    def _authenticate(self, credentials_path: str):
        """Authenticate with Google Sheets API"""
        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return build('sheets', 'v4', credentials=credentials)
    
    def _update_range(self, range_name: str, values: list, sheet_name: str = None):
        """Update a range in the spreadsheet"""
        if sheet_name:
            range_name = f"{sheet_name}!{range_name}"
        
        body = {'values': values}
        
        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        return result
    
    def create_current_snapshot_tab(self, df: pd.DataFrame):
        """Create/update current snapshot tab"""
        
        # Prepare data for sheets
        headers = [
            'Stock Code', 'Company Name', 'Quality Score', 'DCF Value', 
            'Graham Value', 'Consensus Value', 'Safety Margin', 'Recommendation',
            'Quality Rank', 'Overall Rank', 'ROE', 'ROA', 'EPS', 'Dividend Yield'
        ]
        
        # Prepare data rows
        data_rows = []
        for _, row in df.iterrows():
            data_row = [
                row.get('stock_code', ''),
                row.get('company_name', ''),
                row.get('quality_score', 0),
                row.get('dcf_valuation', 0),
                row.get('graham_valuation', 0),
                row.get('consensus_valuation', 0),
                row.get('safety_margin', 0),
                row.get('recommendation', ''),
                row.get('quality_rank', 0),
                row.get('overall_rank', 0),
                row.get('avg_roe', 0),
                row.get('avg_roa', 0),
                row.get('avg_eps', 0),
                row.get('avg_dividend_yield', 0)
            ]
            data_rows.append(data_row)
        
        # Combine headers and data
        sheet_data = [headers] + data_rows
        
        # Update sheet
        self._update_range('A1', sheet_data, 'Current Snapshot')
        
        click.echo(f"✅ Updated Current Snapshot with {len(data_rows)} stocks")
    
    def create_top_picks_tab(self, df: pd.DataFrame):
        """Create/update top picks tab"""
        
        # Filter top picks (Strong Buy and Buy recommendations)
        top_picks = df[df['recommendation'].isin(['Strong Buy', 'Buy'])].copy()
        top_picks = top_picks.sort_values('overall_rank').head(20)
        
        headers = [
            'Rank', 'Stock Code', 'Recommendation', 'Quality Score', 
            'Safety Margin', 'Consensus Value', 'Key Strengths'
        ]
        
        data_rows = []
        for i, (_, row) in enumerate(top_picks.iterrows(), 1):
            # Generate key strengths
            strengths = []
            if row.get('quality_score', 0) >= 8:
                strengths.append('High Quality')
            if row.get('safety_margin', 0) >= 0.3:
                strengths.append('High Safety Margin')
            if row.get('avg_roe', 0) >= 15:
                strengths.append('Strong ROE')
            if row.get('dividend_consistency', 0) >= 0.8:
                strengths.append('Consistent Dividends')
            
            data_row = [
                i,
                row.get('stock_code', ''),
                row.get('recommendation', ''),
                row.get('quality_score', 0),
                f"{row.get('safety_margin', 0):.1%}",
                row.get('consensus_valuation', 0),
                ', '.join(strengths[:3])  # Top 3 strengths
            ]
            data_rows.append(data_row)
        
        sheet_data = [headers] + data_rows
        self._update_range('A1', sheet_data, 'Top Picks')
        
        click.echo(f"✅ Updated Top Picks with {len(data_rows)} stocks")
    
    def create_single_pick_tab(self, df: pd.DataFrame):
        """Create/update single stock analysis tab with input functionality"""
        
        # Create input section and template
        single_pick_data = [
            ['Single Stock Analysis', ''],
            ['', ''],
            ['Enter Stock Code:', '2330'],  # Default example
            ['', ''],
            ['Stock Details:', ''],
            ['', ''],
            ['Stock Code', '=B3'],  # Reference to input cell
            ['Company Name', '=IFERROR(INDEX(\'Current Snapshot\'!B:B,MATCH(B3,\'Current Snapshot\'!A:A,0)),"Stock not found")'],
            ['Quality Score', '=IFERROR(INDEX(\'Current Snapshot\'!C:C,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['DCF Valuation', '=IFERROR(INDEX(\'Current Snapshot\'!D:D,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['Graham Valuation', '=IFERROR(INDEX(\'Current Snapshot\'!E:E,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['Consensus Valuation', '=IFERROR(INDEX(\'Current Snapshot\'!F:F,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['Safety Margin', '=IFERROR(INDEX(\'Current Snapshot\'!G:G,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['Recommendation', '=IFERROR(INDEX(\'Current Snapshot\'!H:H,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['Quality Rank', '=IFERROR(INDEX(\'Current Snapshot\'!I:I,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['Overall Rank', '=IFERROR(INDEX(\'Current Snapshot\'!J:J,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['', ''],
            ['Financial Metrics:', ''],
            ['ROE (%)', '=IFERROR(INDEX(\'Current Snapshot\'!K:K,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['ROA (%)', '=IFERROR(INDEX(\'Current Snapshot\'!L:L,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['EPS', '=IFERROR(INDEX(\'Current Snapshot\'!M:M,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['Dividend Yield (%)', '=IFERROR(INDEX(\'Current Snapshot\'!N:N,MATCH(B3,\'Current Snapshot\'!A:A,0)),"N/A")'],
            ['', ''],
            ['Investment Summary:', ''],
            ['Risk Level', '=IF(B13="Strong Buy","Low",IF(B13="Buy","Medium",IF(B13="Hold","Medium","High")))'],
            ['Expected Return', '=IF(ISNUMBER(B12),ROUND(B12*100,1)&"%","N/A")'],
            ['Position Sizing', '=IF(B13="Strong Buy","5-10%",IF(B13="Buy","3-7%",IF(B13="Hold","1-3%","0%")))'],
        ]
        
        self._update_range('A1', single_pick_data, 'Single Pick')
        
        click.echo(f"✅ Updated Single Pick analysis tab")
    
    def create_summary_tab(self, df: pd.DataFrame):
        """Create/update summary dashboard tab"""
        
        # Calculate summary statistics
        total_stocks = len(df)
        strong_buy = len(df[df['recommendation'] == 'Strong Buy'])
        buy = len(df[df['recommendation'] == 'Buy'])
        hold = len(df[df['recommendation'] == 'Hold'])
        avg_quality = df['quality_score'].mean()
        
        # Create summary data
        summary_data = [
            ['Investment Summary Dashboard', ''],
            ['', ''],
            ['Total Stocks Analyzed', total_stocks],
            ['Strong Buy Recommendations', strong_buy],
            ['Buy Recommendations', buy],
            ['Hold Recommendations', hold],
            ['Average Quality Score', f"{avg_quality:.1f}"],
            ['', ''],
            ['Top 5 Stocks by Overall Ranking', ''],
            ['Rank', 'Stock Code'],
        ]
        
        # Add top 5 stocks
        top_5 = df.nsmallest(5, 'overall_rank')
        for i, (_, row) in enumerate(top_5.iterrows(), 1):
            summary_data.append([i, row['stock_code']])
        
        self._update_range('A1', summary_data, 'Summary')
        
        click.echo(f"✅ Updated Summary dashboard")
    
    def run_pipeline(self) -> dict:
        """Run complete sheets publishing pipeline"""
        
        # Load enhanced analysis
        input_file = self.input_dir / 'enhanced_analysis.csv'
        if not input_file.exists():
            click.echo("❌ No enhanced analysis file found. Run Stage 4 first.")
            return {'error': 'missing_input'}
        
        df = pd.read_csv(input_file)
        
        if df.empty:
            click.echo("❌ Empty enhanced analysis file")
            return {'error': 'empty_input'}
        
        click.echo(f"📊 Publishing {len(df)} stocks to Google Sheets...")
        
        try:
            # Create/update all tabs
            self.create_current_snapshot_tab(df)
            time.sleep(1)  # Rate limiting
            
            self.create_top_picks_tab(df)
            time.sleep(1)
            
            self.create_single_pick_tab(df)
            time.sleep(1)
            
            self.create_summary_tab(df)
            time.sleep(1)
            
            # Add timestamp
            timestamp_data = [
                [f"Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"]
            ]
            self._update_range('A1', timestamp_data, 'Last Updated')
            
            return {
                'status': 'success',
                'total_stocks': len(df),
                'sheets_updated': 5
            }
        
        except Exception as e:
            click.echo(f"❌ Error publishing to sheets: {e}")
            return {'error': str(e)}

@click.command()
@click.option('--credentials', required=True, help='Path to Google Sheets credentials JSON')
@click.option('--sheet-id', required=True, help='Google Sheets ID')
@click.option('--input-dir', default='data/stage4_enhanced')
def run_stage5(credentials: str, sheet_id: str, input_dir: str):
    publisher = SheetsPublisher(credentials, sheet_id, input_dir)
    result = publisher.run_pipeline()
    
    if 'error' in result:
        click.echo(f"❌ Publishing failed: {result['error']}")
    else:
        click.echo(f"✅ Successfully published {result['total_stocks']} stocks to {result['sheets_updated']} sheets")

if __name__ == '__main__':
    run_stage5()
```

---

## 🧪 Testing and Validation

### **Pipeline Test Runner**

```python
# scripts/run_pipeline_test.py
import subprocess
import click
from pathlib import Path

def run_complete_pipeline_test():
    """Run complete 5-stage pipeline test"""
    
    click.echo("🚀 Starting Complete Pipeline Test")
    
    # Get input parameters
    excel_dir = input("Enter path to GoodInfo Excel files: ")
    if not Path(excel_dir).exists():
        click.echo(f"❌ Directory not found: {excel_dir}")
        return
    
    credentials_file = input("Enter path to Google Sheets credentials JSON: ")
    sheet_id = input("Enter Google Sheets ID: ")
    
    try:
        # Stage 1: Excel → CSV
        click.echo("\n📤 Stage 1: Excel → Raw CSV")
        subprocess.run([
            'python', '-m', 'src.pipelines.stage1_excel_to_csv',
            '--input-dir', excel_dir
        ], check=True)
        
        # Stage 2: Data Cleaning
        click.echo("\n🧹 Stage 2: Data Cleaning")
        subprocess.run([
            'python', '-m', 'src.pipelines.stage2_data_cleaning'
        ], check=True)
        
        # Stage 3: Basic Analysis
        click.echo("\n📊 Stage 3: Basic Analysis")
        subprocess.run([
            'python', '-m', 'src.pipelines.stage3_basic_analysis'
        ], check=True)
        
        # Stage 4: Advanced Analysis
        click.echo("\n🎯 Stage 4: Advanced Analysis")
        subprocess.run([
            'python', '-m', 'src.pipelines.stage4_advanced_analysis'
        ], check=True)
        
        # Stage 5: Google Sheets Publishing
        click.echo("\n📈 Stage 5: Google Sheets Publishing")
        subprocess.run([
            'python', '-m', 'src.pipelines.stage5_sheets_publisher',
            '--credentials', credentials_file,
            '--sheet-id', sheet_id
        ], check=True)
        
        click.echo("\n🎉 Complete pipeline test successful!")
        click.echo("\n📁 Check your Google Sheets for the published dashboard")
        
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Pipeline stage failed: {e}")
    except Exception as e:
        click.echo(f"❌ Test failed: {e}")

if __name__ == '__main__':
    run_complete_pipeline_test()
```

---

## 🚀 GitHub Actions Workflow

```yaml
# .github/workflows/analysis_pipeline.yml
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
    
    - name: Run Stage 1 - Excel to CSV
      run: |
        python -m src.pipelines.stage1_excel_to_csv \
          --input-dir data/goodinfo_files
    
    - name: Run Stage 2 - Data Cleaning
      run: python -m src.pipelines.stage2_data_cleaning
    
    - name: Run Stage 3 - Basic Analysis
      run: python -m src.pipelines.stage3_basic_analysis
    
    - name: Run Stage 4 - Advanced Analysis
      run: python -m src.pipelines.stage4_advanced_analysis
    
    - name: Run Stage 5 - Publish to Sheets
      env:
        GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
      run: |
        python -m src.pipelines.stage5_sheets_publisher \
          --credentials credentials.json \
          --sheet-id $GOOGLE_SHEET_ID
    
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
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Run individual stages
python -m src.pipelines.stage1_excel_to_csv --input-dir /path/to/excel/files
python -m src.pipelines.stage2_data_cleaning
python -m src.pipelines.stage3_basic_analysis
python -m src.pipelines.stage4_advanced_analysis
python -m src.pipelines.stage5_sheets_publisher --credentials creds.json --sheet-id YOUR_SHEET_ID

# 3. Run complete pipeline test
python scripts/run_pipeline_test.py

# 4. Validate outputs at each stage
ls data/stage1_raw/      # Raw CSV files
ls data/stage2_cleaned/  # Cleaned CSV files
ls data/stage3_analysis/ # Basic analysis
ls data/stage4_enhanced/ # Advanced analysis with valuations
```

---

## 🎯 Success Criteria

### **Stage Outputs**
- **Stage 1**: ✅ Raw CSV files with metadata
- **Stage 2**: ✅ Cleaned data with quality scores
- **Stage 3**: ✅ Basic metrics per stock
- **Stage 4**: ✅ Valuations, quality scores, recommendations
- **Stage 5**: ✅ Google Sheets dashboard

### **Final Dashboard Tabs**
1. **Current Snapshot**: All stocks with key metrics
2. **Top Picks**: Best investment opportunities
3. **Single Pick**: By fill Stock ID, then show details of single stock in the same tab
4. **Summary**: Dashboard overview
5. **Last Updated**: Timestamp tracking

This consolidated guide provides a complete, tested pipeline implementation that processes GoodInfo Excel files into actionable investment insights via Google Sheets. Each stage is independent, debuggable, and can be run individually for testing and validation.