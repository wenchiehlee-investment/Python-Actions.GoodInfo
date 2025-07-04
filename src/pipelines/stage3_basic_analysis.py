# src/pipelines/stage3_basic_analysis.py
"""
Stage 3 Pipeline: Basic Analysis - COMPLETE VERSION WITH COMPANY NAMES
✅ PRESERVES: Company names throughout all calculations
✅ HANDLES: Improved column detection and metric calculation
✅ PROCESSES: Multi-stock data structure correctly
"""
import pandas as pd
import numpy as np
import click
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BasicAnalysisPipeline:
    """Basic analysis pipeline with company name preservation"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # EXACT column mappings from instructions-SAS.md
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
    
    def find_column(self, df: pd.DataFrame, patterns: list) -> str:
        """Find column by matching patterns (exact first, then fuzzy)"""
        
        # First try exact matches
        for pattern in patterns:
            if pattern in df.columns:
                return pattern
        
        # Then try fuzzy matches
        for pattern in patterns:
            for col in df.columns:
                if pattern.lower() in str(col).lower():
                    return col
        return None
    
    def safe_numeric_conversion(self, series: pd.Series) -> pd.Series:
        """Safely convert series to numeric with better error handling"""
        try:
            # Handle common non-numeric values
            if series.dtype == 'object':
                # Clean common formatting issues first
                cleaned = series.astype(str)
                cleaned = cleaned.str.replace('%', '')
                cleaned = cleaned.str.replace(',', '')
                cleaned = cleaned.str.replace('億', '')
                cleaned = cleaned.str.replace('--', '')
                cleaned = cleaned.str.replace('N/A', '')
                cleaned = cleaned.str.replace('nan', '')
                cleaned = cleaned.replace('', np.nan)
                
                # Convert to numeric
                return pd.to_numeric(cleaned, errors='coerce')
            else:
                return pd.to_numeric(series, errors='coerce')
        except:
            return pd.Series([0] * len(series), index=series.index)
    
    def calculate_dividend_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate dividend-related metrics per stock with company names"""
        if df.empty:
            return pd.DataFrame()
        
        logger.info("📊 Calculating dividend metrics...")
        logger.info(f"  Available columns: {list(df.columns)[5:10]}...")  # Skip metadata
        
        # Find relevant columns using exact mappings
        mapping = self.column_mappings['dividend']
        cash_dividend_col = self.find_column(df, mapping['cash_dividend'])
        dividend_yield_col = self.find_column(df, mapping['dividend_yield'])
        year_col = self.find_column(df, mapping['year'])
        
        logger.info(f"  Cash dividend column: {cash_dividend_col}")
        logger.info(f"  Dividend yield column: {dividend_yield_col}")
        logger.info(f"  Year column: {year_col}")
        
        results = []
        
        for stock_code in df['stock_code'].unique():
            stock_data = df[df['stock_code'] == stock_code].copy()
            
            # Get company name from the first row for this stock
            company_name = stock_data['company_name'].iloc[0] if 'company_name' in stock_data.columns and not stock_data.empty else stock_code
            
            logger.debug(f"  Processing stock {stock_code} ({company_name}): {len(stock_data)} rows")
            
            # Filter out summary/total rows
            if year_col:
                # Remove rows where year is not numeric (like totals, summaries)
                year_series = self.safe_numeric_conversion(stock_data[year_col])
                stock_data = stock_data[year_series.notna() & (year_series > 1900)]
            
            if len(stock_data) == 0:
                logger.debug(f"    {stock_code}: No valid data after filtering")
                results.append({
                    'stock_code': stock_code,
                    'company_name': company_name,
                    'avg_dividend': 0,
                    'avg_dividend_yield': 0,
                    'dividend_consistency': 0
                })
                continue
            
            # Calculate dividend metrics
            avg_dividend = 0
            avg_yield = 0
            dividend_consistency = 0
            
            if cash_dividend_col and cash_dividend_col in stock_data.columns:
                dividend_series = self.safe_numeric_conversion(stock_data[cash_dividend_col])
                valid_dividends = dividend_series[dividend_series.notna()]
                
                if len(valid_dividends) > 0:
                    avg_dividend = valid_dividends.mean()
                    dividend_consistency = len(valid_dividends[valid_dividends > 0]) / len(valid_dividends)
                logger.debug(f"    {stock_code} dividend: avg={avg_dividend:.2f}, consistency={dividend_consistency:.2f}")
            
            if dividend_yield_col and dividend_yield_col in stock_data.columns:
                yield_series = self.safe_numeric_conversion(stock_data[dividend_yield_col])
                valid_yields = yield_series[yield_series.notna()]
                
                if len(valid_yields) > 0:
                    avg_yield = valid_yields.mean()
                logger.debug(f"    {stock_code} yield: avg={avg_yield:.2f}")
            
            results.append({
                'stock_code': stock_code,
                'company_name': company_name,
                'avg_dividend': round(avg_dividend, 2),
                'avg_dividend_yield': round(avg_yield, 2),
                'dividend_consistency': round(dividend_consistency, 3)
            })
        
        result_df = pd.DataFrame(results)
        logger.info(f"  ✅ Calculated dividend metrics for {len(result_df)} stocks")
        return result_df
    
    def calculate_performance_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate performance metrics with company names"""
        if df.empty:
            return pd.DataFrame()
        
        logger.info("📊 Calculating performance metrics...")
        logger.info(f"  Available columns: {list(df.columns)[5:10]}...")  # Skip metadata
        
        # Find relevant columns using exact mappings
        mapping = self.column_mappings['performance']
        roe_col = self.find_column(df, mapping['roe'])
        roa_col = self.find_column(df, mapping['roa'])
        eps_col = self.find_column(df, mapping['eps'])
        revenue_col = self.find_column(df, mapping['revenue'])
        year_col = self.find_column(df, mapping['year'])
        
        logger.info(f"  ROE column: {roe_col}")
        logger.info(f"  ROA column: {roa_col}")
        logger.info(f"  EPS column: {eps_col}")
        logger.info(f"  Revenue column: {revenue_col}")
        logger.info(f"  Year column: {year_col}")
        
        results = []
        
        for stock_code in df['stock_code'].unique():
            stock_data = df[df['stock_code'] == stock_code].copy()
            
            # Get company name from the first row for this stock
            company_name = stock_data['company_name'].iloc[0] if 'company_name' in stock_data.columns and not stock_data.empty else stock_code
            
            logger.debug(f"  Processing stock {stock_code} ({company_name}): {len(stock_data)} rows")
            
            # Filter and sort by year if available
            if year_col:
                year_series = self.safe_numeric_conversion(stock_data[year_col])
                # Keep only valid years (exclude quarters like 25Q1 for now)
                valid_year_mask = year_series.notna() & (year_series >= 2000) & (year_series <= 2030)
                stock_data = stock_data[valid_year_mask]
                
                if len(stock_data) > 0:
                    stock_data = stock_data.sort_values(by=year_col)
            
            if len(stock_data) == 0:
                logger.debug(f"    {stock_code}: No valid data after filtering")
                results.append({
                    'stock_code': stock_code,
                    'company_name': company_name,
                    'avg_roe': 0,
                    'avg_roa': 0,
                    'avg_eps': 0,
                    'revenue_growth': 0
                })
                continue
            
            # Calculate financial metrics
            avg_roe = 0
            avg_roa = 0
            avg_eps = 0
            revenue_growth = 0
            
            if roe_col:
                roe_series = self.safe_numeric_conversion(stock_data[roe_col])
                valid_roe = roe_series[roe_series.notna()]
                if len(valid_roe) > 0:
                    avg_roe = valid_roe.mean()
                logger.debug(f"    {stock_code} ROE: avg={avg_roe:.2f}")
            
            if roa_col:
                roa_series = self.safe_numeric_conversion(stock_data[roa_col])
                valid_roa = roa_series[roa_series.notna()]
                if len(valid_roa) > 0:
                    avg_roa = valid_roa.mean()
                logger.debug(f"    {stock_code} ROA: avg={avg_roa:.2f}")
            
            if eps_col:
                eps_series = self.safe_numeric_conversion(stock_data[eps_col])
                valid_eps = eps_series[eps_series.notna()]
                if len(valid_eps) > 0:
                    avg_eps = valid_eps.mean()
                logger.debug(f"    {stock_code} EPS: avg={avg_eps:.2f}")
            
            # Calculate revenue growth (first to last valid revenue)
            if revenue_col and len(stock_data) > 1:
                revenue_series = self.safe_numeric_conversion(stock_data[revenue_col])
                valid_revenues = revenue_series[revenue_series.notna() & (revenue_series > 0)]
                
                if len(valid_revenues) >= 2:
                    first_revenue = valid_revenues.iloc[0]
                    last_revenue = valid_revenues.iloc[-1]
                    years_span = len(valid_revenues)
                    
                    if first_revenue > 0 and years_span > 1:
                        # Annualized growth rate
                        revenue_growth = ((last_revenue / first_revenue) ** (1 / (years_span - 1)) - 1) * 100
                
                logger.debug(f"    {stock_code} revenue growth: {revenue_growth:.2f}%")
            
            results.append({
                'stock_code': stock_code,
                'company_name': company_name,
                'avg_roe': round(avg_roe, 2),
                'avg_roa': round(avg_roa, 2),
                'avg_eps': round(avg_eps, 2),
                'revenue_growth': round(revenue_growth, 2)
            })
        
        result_df = pd.DataFrame(results)
        logger.info(f"  ✅ Calculated performance metrics for {len(result_df)} stocks")
        return result_df
    
    def calculate_revenue_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate revenue trend metrics with company names"""
        if df.empty:
            return pd.DataFrame()
        
        logger.info("📊 Calculating revenue metrics...")
        logger.info(f"  Available columns: {list(df.columns)[5:10]}...")  # Skip metadata
        
        # Find relevant columns using exact mappings
        mapping = self.column_mappings['revenue']
        mom_col = self.find_column(df, mapping['mom_growth'])
        yoy_col = self.find_column(df, mapping['yoy_growth'])
        revenue_col = self.find_column(df, mapping['monthly_revenue'])
        date_col = self.find_column(df, mapping['date'])
        
        logger.info(f"  Month-over-month column: {mom_col}")
        logger.info(f"  Year-over-year column: {yoy_col}")
        logger.info(f"  Monthly revenue column: {revenue_col}")
        logger.info(f"  Date column: {date_col}")
        
        results = []
        
        for stock_code in df['stock_code'].unique():
            stock_data = df[df['stock_code'] == stock_code].copy()
            
            # Get company name from the first row for this stock
            company_name = stock_data['company_name'].iloc[0] if 'company_name' in stock_data.columns and not stock_data.empty else stock_code
            
            logger.debug(f"  Processing stock {stock_code} ({company_name}): {len(stock_data)} rows")
            
            # Sort by date if available
            if date_col:
                try:
                    stock_data[date_col] = pd.to_datetime(stock_data[date_col], errors='coerce')
                    stock_data = stock_data.sort_values(by=date_col)
                except:
                    pass
            
            # Calculate revenue trend metrics
            avg_mom_growth = 0
            avg_yoy_growth = 0
            revenue_volatility = 0
            
            if mom_col:
                mom_series = self.safe_numeric_conversion(stock_data[mom_col])
                valid_mom = mom_series[mom_series.notna()]
                if len(valid_mom) > 0:
                    avg_mom_growth = valid_mom.mean()
                    revenue_volatility = valid_mom.std() if len(valid_mom) > 1 else 0
                logger.debug(f"    {stock_code} MoM: avg={avg_mom_growth:.2f}, vol={revenue_volatility:.2f}")
            
            if yoy_col:
                yoy_series = self.safe_numeric_conversion(stock_data[yoy_col])
                valid_yoy = yoy_series[yoy_series.notna()]
                if len(valid_yoy) > 0:
                    avg_yoy_growth = valid_yoy.mean()
                logger.debug(f"    {stock_code} YoY: avg={avg_yoy_growth:.2f}")
            
            results.append({
                'stock_code': stock_code,
                'company_name': company_name,
                'avg_mom_growth': round(avg_mom_growth, 2),
                'avg_yoy_growth': round(avg_yoy_growth, 2),
                'revenue_volatility': round(revenue_volatility, 2)
            })
        
        result_df = pd.DataFrame(results)
        logger.info(f"  ✅ Calculated revenue metrics for {len(result_df)} stocks")
        return result_df
    
    def run_pipeline(self) -> dict:
        """Run basic analysis pipeline with company name preservation"""
        logger.info("🚀 Starting Stage 3: Basic Analysis Pipeline with Company Names")
        logger.info("✨ Features: Exact column mapping + Company name preservation + Multi-stock support")
        
        # Load cleaned data
        dividend_file = self.input_dir / 'cleaned_dividends.csv'
        performance_file = self.input_dir / 'cleaned_performance.csv'
        revenue_file = self.input_dir / 'cleaned_revenue.csv'
        
        # Load datasets with error handling
        datasets = {}
        
        if dividend_file.exists():
            try:
                datasets['dividend'] = pd.read_csv(dividend_file)
                logger.info(f"📂 Loaded dividends: {len(datasets['dividend'])} rows")
            except Exception as e:
                logger.error(f"❌ Error loading dividends: {e}")
                datasets['dividend'] = pd.DataFrame()
        else:
            logger.warning(f"⚠️ Dividend file not found: {dividend_file}")
            datasets['dividend'] = pd.DataFrame()
        
        if performance_file.exists():
            try:
                datasets['performance'] = pd.read_csv(performance_file)
                logger.info(f"📂 Loaded performance: {len(datasets['performance'])} rows")
            except Exception as e:
                logger.error(f"❌ Error loading performance: {e}")
                datasets['performance'] = pd.DataFrame()
        else:
            logger.warning(f"⚠️ Performance file not found: {performance_file}")
            datasets['performance'] = pd.DataFrame()
        
        if revenue_file.exists():
            try:
                datasets['revenue'] = pd.read_csv(revenue_file)
                logger.info(f"📂 Loaded revenue: {len(datasets['revenue'])} rows")
            except Exception as e:
                logger.error(f"❌ Error loading revenue: {e}")
                datasets['revenue'] = pd.DataFrame()
        else:
            logger.warning(f"⚠️ Revenue file not found: {revenue_file}")
            datasets['revenue'] = pd.DataFrame()
        
        # Calculate metrics for each dataset
        metrics = {}
        
        if not datasets['dividend'].empty:
            metrics['dividend'] = self.calculate_dividend_metrics(datasets['dividend'])
        else:
            metrics['dividend'] = pd.DataFrame()
        
        if not datasets['performance'].empty:
            metrics['performance'] = self.calculate_performance_metrics(datasets['performance'])
        else:
            metrics['performance'] = pd.DataFrame()
        
        if not datasets['revenue'].empty:
            metrics['revenue'] = self.calculate_revenue_metrics(datasets['revenue'])
        else:
            metrics['revenue'] = pd.DataFrame()
        
        # Combine all metrics with proper company name handling
        logger.info("🔗 Combining all metrics...")
        
        non_empty_metrics = {name: df for name, df in metrics.items() if not df.empty}
        
        if not non_empty_metrics:
            logger.error("❌ No metrics calculated - all datasets empty or failed")
            return {'stocks_analyzed': 0, 'metrics_calculated': 0}
        
        # Start with first non-empty dataset
        first_name, combined_analysis = list(non_empty_metrics.items())[0]
        logger.info(f"  Started with {first_name}: {len(combined_analysis)} stocks")
        
        # Merge remaining datasets on both stock_code and preserve company_name
        for name, df in list(non_empty_metrics.items())[1:]:
            # Merge on stock_code and keep company_name from both sides
            combined_analysis = combined_analysis.merge(df, on='stock_code', how='outer', suffixes=('', '_right'))
            
            # Handle company_name conflicts - prefer non-empty values
            if 'company_name_right' in combined_analysis.columns:
                # Fill missing company_name with values from the right dataframe
                mask = combined_analysis['company_name'].isna() | (combined_analysis['company_name'] == '')
                combined_analysis.loc[mask, 'company_name'] = combined_analysis.loc[mask, 'company_name_right']
                
                # Drop the duplicate company_name column
                combined_analysis = combined_analysis.drop(columns=['company_name_right'])
            
            logger.info(f"  Merged {name}: {len(combined_analysis)} stocks")
        
        # Fill missing values with 0 for numeric columns only
        numeric_columns = combined_analysis.select_dtypes(include=[np.number]).columns
        combined_analysis[numeric_columns] = combined_analysis[numeric_columns].fillna(0)
        
        # Ensure company_name is filled for all rows
        combined_analysis['company_name'] = combined_analysis['company_name'].fillna(combined_analysis['stock_code'])
        
        # Add analysis metadata
        combined_analysis['analysis_date'] = pd.Timestamp.now()
        combined_analysis['analysis_stage'] = 'basic_metrics'
        
        # Save combined analysis
        output_file = self.output_dir / 'stock_analysis.csv'
        combined_analysis.to_csv(output_file, index=False, encoding='utf-8')
        
        # Generate summary
        summary_stats = {
            'stocks_analyzed': len(combined_analysis),
            'metrics_calculated': len([col for col in combined_analysis.columns if col not in ['stock_code', 'company_name', 'analysis_date', 'analysis_stage']])
        }
        
        logger.info(f"💾 Saved analysis: {output_file}")
        logger.info(f"📊 Summary: {summary_stats['stocks_analyzed']} stocks, {summary_stats['metrics_calculated']} metrics")
        
        # Show sample of calculated metrics with company names
        if len(combined_analysis) > 0:
            logger.info("📋 Sample metrics from first stock:")
            sample_stock = combined_analysis.iloc[0]
            logger.info(f"  Stock: {sample_stock['stock_code']} ({sample_stock['company_name']})")
            sample_metrics = ['avg_roe', 'avg_roa', 'avg_eps', 'revenue_growth', 'avg_dividend', 'avg_yoy_growth']
            for metric in sample_metrics:
                if metric in combined_analysis.columns:
                    logger.info(f"  {metric}: {sample_stock[metric]}")
        
        logger.info("✅ Stage 3 completed successfully with company names preserved")
        return summary_stats

@click.command()
@click.option('--input-dir', default='data/stage2_cleaned')
@click.option('--output-dir', default='data/stage3_analysis')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def run_stage3_with_companies(input_dir: str, output_dir: str, debug: bool):
    """
    Run Stage 3: Basic Analysis with Company Name Preservation
    
    🎯 KEY FEATURES:
    ✅ Exact column headers from instructions-SAS.md
    ✅ Company names preserved throughout all calculations
    ✅ Improved column detection and mapping
    ✅ Better data filtering and validation
    ✅ Multi-stock data structure support
    ✅ Comprehensive error handling
    """
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        click.echo(f"❌ Input directory not found: {input_dir}")
        return
    
    # Run pipeline
    pipeline = BasicAnalysisPipeline(input_dir, output_dir)
    stats = pipeline.run_pipeline()
    
    # Display results
    click.echo(f"\n📊 === Stage 3 Results ===")
    click.echo(f"📁 Input directory: {input_dir}")
    click.echo(f"💾 Output directory: {output_dir}")
    click.echo(f"")
    click.echo(f"📈 Analysis Results:")
    click.echo(f"   📊 Stocks analyzed: {stats['stocks_analyzed']}")
    click.echo(f"   📋 Metrics calculated: {stats['metrics_calculated']}")
    
    if stats['stocks_analyzed'] > 0:
        click.echo(f"\n🎉 Stage 3 SUCCESS!")
        click.echo(f"✨ Features implemented:")
        click.echo(f"   📋 Exact column mapping from instructions-SAS.md")
        click.echo(f"   🏢 Company names preserved for all stocks")
        click.echo(f"   🗑️ Improved data filtering and validation")
        click.echo(f"   📊 Multi-stock data structure support")
        click.echo(f"   🔗 Robust metric combination with company names")
        
        click.echo(f"\n📂 Next steps:")
        click.echo(f"   1. Check analysis file: {output_dir}/stock_analysis.csv")
        click.echo(f"   2. Run Stage 4: python -m src.pipelines.stage4_advanced_analysis")
    else:
        click.echo(f"❌ No stocks analyzed - check input data and column mappings")

if __name__ == '__main__':
    run_stage3_with_companies()