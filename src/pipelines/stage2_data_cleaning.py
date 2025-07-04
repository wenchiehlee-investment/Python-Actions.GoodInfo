# src/pipelines/stage2_data_cleaning.py
"""
Stage 2 Pipeline: Data Cleaning and Standardization - UNICODE SAFE VERSION
Cleans raw CSV data and prepares for analysis
"""
import pandas as pd
import numpy as np
import click
from pathlib import Path
import logging
import warnings
from typing import Dict, List, Optional
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

def safe_echo(message: str):
    """Safe echo that handles Unicode encoding issues on Windows"""
    try:
        click.echo(message)
    except UnicodeEncodeError:
        # Remove emoji and special Unicode characters
        import re
        # Remove emoji and other special Unicode characters
        clean_message = re.sub(r'[^\x00-\x7F]+', '', message)
        click.echo(clean_message)

class DataCleaningPipeline:
    """Pipeline to clean and standardize raw CSV data"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'files_processed': 0,
            'total_rows_input': 0,
            'total_rows_output': 0,
            'rows_removed': 0,
            'columns_cleaned': 0
        }
    
    def clean_date_columns(self, df: pd.DataFrame, date_patterns: List[str]) -> pd.DataFrame:
        """Clean date columns with improved parsing"""
        
        for col in df.columns:
            if any(pattern in str(col) for pattern in date_patterns):
                logger.info(f"    Cleaning date column: {col}")
                
                # Try common date formats first
                date_formats = [
                    '%Y/%m/%d',    # 2025/05/01
                    '%Y-%m-%d',    # 2025-05-01
                    '%Y/%m',       # 2025/05
                    '%Y-%m',       # 2025-05
                    '%m/%d/%Y',    # 05/01/2025
                    '%d/%m/%Y',    # 01/05/2025
                ]
                
                original_values = df[col].dropna().astype(str)
                if len(original_values) == 0:
                    continue
                
                # Try each format
                for fmt in date_formats:
                    try:
                        df[col] = pd.to_datetime(df[col], format=fmt, errors='coerce')
                        success_rate = df[col].notna().sum() / len(df[col])
                        if success_rate > 0.8:  # If >80% successfully parsed
                            logger.info(f"      Success with format: {fmt}")
                            break
                    except:
                        continue
                else:
                    # Fallback to flexible parsing (with warning suppression)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        logger.info(f"      Used flexible parsing for: {col}")
                
                # Report parsing results
                parsed_count = df[col].notna().sum()
                total_count = len(df[col])
                logger.info(f"      Parsed {parsed_count}/{total_count} dates successfully")
        
        return df
    
    def clean_numeric_columns(self, df: pd.DataFrame, numeric_patterns: List[str]) -> pd.DataFrame:
        """Clean numeric columns"""
        
        for col in df.columns:
            if any(pattern in str(col) for pattern in numeric_patterns):
                logger.info(f"    Cleaning numeric column: {col}")
                
                if df[col].dtype == 'object':
                    # Clean common formatting issues
                    df[col] = df[col].astype(str)
                    df[col] = df[col].str.replace('%', '', regex=False)
                    df[col] = df[col].str.replace(',', '', regex=False)
                    df[col] = df[col].str.replace('元', '', regex=False)
                    df[col] = df[col].str.replace('億', '', regex=False)
                    df[col] = df[col].str.replace('$', '', regex=False)
                    df[col] = df[col].str.replace('(', '-', regex=False)  # Handle negative values
                    df[col] = df[col].str.replace(')', '', regex=False)
                    df[col] = df[col].str.replace(' ', '', regex=False)
                    df[col] = df[col].str.replace('--', '', regex=False)
                    df[col] = df[col].str.replace('N/A', '', regex=False)
                    df[col] = df[col].str.replace('nan', '', regex=False)
                    df[col] = df[col].str.replace('None', '', regex=False)
                    
                    # Convert to numeric
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Report conversion results
                    numeric_count = df[col].notna().sum()
                    total_count = len(df[col])
                    logger.info(f"      Converted {numeric_count}/{total_count} values to numeric")
        
        return df
    
    def clean_dividend_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean dividend detail data"""
        logger.info("  Cleaning dividend data...")
        
        original_rows = len(df)
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Clean date columns
        date_patterns = ['除息日', '發放日', '股利發放期間', 'date', '日期']
        df = self.clean_date_columns(df, date_patterns)
        
        # Clean numeric columns
        numeric_patterns = ['股利', '殖利率', 'dividend', 'yield', '率', '金額']
        df = self.clean_numeric_columns(df, numeric_patterns)
        
        # Add data quality indicators
        df['data_quality_score'] = self.calculate_data_quality_score(df)
        df['cleaned_date'] = pd.Timestamp.now()
        
        cleaned_rows = len(df)
        self.stats['rows_removed'] += (original_rows - cleaned_rows)
        
        logger.info(f"    Rows: {original_rows} -> {cleaned_rows} (removed {original_rows - cleaned_rows})")
        
        return df
    
    def clean_performance_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean business performance data"""
        logger.info("  Cleaning performance data...")
        
        original_rows = len(df)
        
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Clean year/period columns
        year_patterns = ['年度', 'year', '期間', '季度']
        for col in df.columns:
            if any(pattern in str(col) for pattern in year_patterns):
                logger.info(f"    Cleaning year column: {col}")
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean financial amounts
        financial_patterns = [
            '營業收入', '收入', '毛利', '利益', '淨利', 'revenue', 'profit', 'income',
            '資產', '負債', '權益', 'assets', 'liabilities', 'equity'
        ]
        df = self.clean_numeric_columns(df, financial_patterns)
        
        # Clean percentage columns (ROE, margins, etc.)
        percentage_patterns = ['roe', 'roa', '率', 'margin', '%', 'ratio']
        df = self.clean_numeric_columns(df, percentage_patterns)
        
        # Clean EPS column specifically
        eps_patterns = ['eps', 'EPS', '每股盈餘']
        df = self.clean_numeric_columns(df, eps_patterns)
        
        # Add quality indicators
        df['data_quality_score'] = self.calculate_data_quality_score(df)
        df['cleaned_date'] = pd.Timestamp.now()
        
        cleaned_rows = len(df)
        self.stats['rows_removed'] += (original_rows - cleaned_rows)
        
        logger.info(f"    Rows: {original_rows} -> {cleaned_rows} (removed {original_rows - cleaned_rows})")
        
        return df
    
    def clean_revenue_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean monthly revenue data"""
        logger.info("  Cleaning revenue data...")
        
        original_rows = len(df)
        
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Clean date columns
        date_patterns = ['月別', 'month', '期間', '年月']
        df = self.clean_date_columns(df, date_patterns)
        
        # Clean revenue amounts
        revenue_patterns = ['營業收入', '營收', 'revenue', '收入', '銷售額']
        df = self.clean_numeric_columns(df, revenue_patterns)
        
        # Clean growth percentages
        growth_patterns = ['增', 'growth', '成長', 'yoy', 'mom', '變動']
        df = self.clean_numeric_columns(df, growth_patterns)
        
        # Add quality indicators
        df['data_quality_score'] = self.calculate_data_quality_score(df)
        df['cleaned_date'] = pd.Timestamp.now()
        
        cleaned_rows = len(df)
        self.stats['rows_removed'] += (original_rows - cleaned_rows)
        
        logger.info(f"    Rows: {original_rows} -> {cleaned_rows} (removed {original_rows - cleaned_rows})")
        
        return df
    
    def calculate_data_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate data quality score for each row (0-10 scale)"""
        
        # Exclude metadata columns from quality calculation
        metadata_cols = ['stock_code', 'company_name', 'file_type', 'source_file', 'processing_date']
        analysis_cols = [col for col in df.columns if col not in metadata_cols]
        
        if not analysis_cols:
            return pd.Series([10.0] * len(df), index=df.index)
        
        # Calculate percentage of non-null values per row for analysis columns
        analysis_df = df[analysis_cols]
        non_null_ratio = analysis_df.notna().sum(axis=1) / len(analysis_cols)
        
        # Convert to 0-10 scale
        quality_score = (non_null_ratio * 10).round(1)
        
        return quality_score
    
    def generate_cleaning_summary(self, file_name: str, input_rows: int, output_rows: int) -> Dict:
        """Generate summary for individual file cleaning"""
        
        return {
            'file': file_name,
            'input_rows': input_rows,
            'output_rows': output_rows,
            'rows_removed': input_rows - output_rows,
            'retention_rate': f"{(output_rows / input_rows * 100):.1f}%" if input_rows > 0 else "0%"
        }
    
    def run_pipeline(self) -> Dict:
        """Run the complete Stage 2 data cleaning pipeline"""
        logger.info("Starting Stage 2: Data Cleaning Pipeline")
        
        # File mappings with cleaning functions
        file_mappings = {
            'raw_dividends.csv': ('cleaned_dividends.csv', self.clean_dividend_data),
            'raw_performance.csv': ('cleaned_performance.csv', self.clean_performance_data),
            'raw_revenue.csv': ('cleaned_revenue.csv', self.clean_revenue_data)
        }
        
        cleaning_summaries = []
        
        for input_file, (output_file, cleaning_func) in file_mappings.items():
            input_path = self.input_dir / input_file
            output_path = self.output_dir / output_file
            
            if not input_path.exists():
                logger.warning(f"Input file not found: {input_path}")
                continue
            
            try:
                logger.info(f"\nProcessing: {input_file}")
                
                # Load raw data
                df = pd.read_csv(input_path)
                original_rows = len(df)
                self.stats['total_rows_input'] += original_rows
                
                logger.info(f"  Loaded: {original_rows} rows, {len(df.columns)} columns")
                
                # Clean data
                cleaned_df = cleaning_func(df)
                cleaned_rows = len(cleaned_df)
                self.stats['total_rows_output'] += cleaned_rows
                
                # Save cleaned data
                cleaned_df.to_csv(output_path, index=False, encoding='utf-8')
                logger.info(f"  Saved: {output_file}")
                
                # Generate summary
                summary = self.generate_cleaning_summary(input_file, original_rows, cleaned_rows)
                cleaning_summaries.append(summary)
                
                self.stats['files_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing {input_file}: {e}")
        
        # Generate overall summary
        self._save_cleaning_summary(cleaning_summaries)
        
        logger.info("Stage 2 pipeline completed")
        return self.stats
    
    def _save_cleaning_summary(self, summaries: List[Dict]):
        """Save cleaning summary to CSV"""
        
        if summaries:
            summary_df = pd.DataFrame(summaries)
            summary_file = self.output_dir / 'stage2_cleaning_summary.csv'
            summary_df.to_csv(summary_file, index=False)
            
            logger.info(f"\nCleaning Summary:")
            for summary in summaries:
                logger.info(f"  {summary['file']}: {summary['retention_rate']} retention")
        
        # Save overall stats
        overall_stats = {
            'metric': [
                'files_processed', 'total_rows_input', 'total_rows_output', 
                'rows_removed', 'data_retention_rate'
            ],
            'value': [
                self.stats['files_processed'],
                self.stats['total_rows_input'],
                self.stats['total_rows_output'],
                self.stats['rows_removed'],
                f"{(self.stats['total_rows_output'] / self.stats['total_rows_input'] * 100):.1f}%" 
                if self.stats['total_rows_input'] > 0 else "0%"
            ]
        }
        
        overall_file = self.output_dir / 'stage2_overall_stats.csv'
        pd.DataFrame(overall_stats).to_csv(overall_file, index=False)

@click.command()
@click.option('--input-dir', default='data/stage1_raw', help='Input directory with raw CSV files')
@click.option('--output-dir', default='data/stage2_cleaned', help='Output directory for cleaned CSV files')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def run_stage2(input_dir: str, output_dir: str, debug: bool):
    """
    Run Stage 2: Data Cleaning and Standardization
    
    Cleans raw CSV data from Stage 1 and prepares it for analysis.
    Handles date parsing, numeric conversion, and data quality scoring.
    """
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        safe_echo(f"ERROR: Input directory not found: {input_dir}")
        return
    
    # Run pipeline
    pipeline = DataCleaningPipeline(input_dir, output_dir)
    stats = pipeline.run_pipeline()
    
    # Display results (using safe_echo for Unicode compatibility)
    safe_echo(f"\n=== Stage 2 Cleaning Results ===")
    safe_echo(f"Input directory: {input_dir}")
    safe_echo(f"Output directory: {output_dir}")
    safe_echo(f"")
    safe_echo(f"Processing Statistics:")
    safe_echo(f"   Files processed: {stats['files_processed']}")
    safe_echo(f"   Input rows: {stats['total_rows_input']:,}")
    safe_echo(f"   Output rows: {stats['total_rows_output']:,}")
    safe_echo(f"   Rows removed: {stats['rows_removed']:,}")
    
    if stats['total_rows_input'] > 0:
        retention_rate = stats['total_rows_output'] / stats['total_rows_input'] * 100
        safe_echo(f"   Data retention: {retention_rate:.1f}%")
    
    safe_echo(f"")
    if stats['files_processed'] > 0:
        safe_echo(f"SUCCESS: Stage 2 completed successfully!")
        safe_echo(f"Next steps:")
        safe_echo(f"   1. Check cleaned files in: {output_dir}")
        safe_echo(f"   2. Run Stage 3: python -m src.pipelines.stage3_basic_analysis")
    else:
        safe_echo(f"ERROR: No files were processed!")

if __name__ == '__main__':
    run_stage2()