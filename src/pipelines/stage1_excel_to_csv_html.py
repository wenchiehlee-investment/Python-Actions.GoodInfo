# src/pipelines/stage1_excel_to_csv_html.py
"""
Stage 1 Pipeline: Excel/HTML to CSV Conversion - CORRECTED COLUMN ORDERS
✅ USES: Simple row-by-row approach that works
✅ FOLLOWS: Exact column orders specified by user
✅ PROCESSES: Files directly from original directories
"""
import pandas as pd
import click
from pathlib import Path
import logging
import glob
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleRobustPipeline:
    """Simple, robust pipeline with corrected column orders"""
    
    def __init__(self, output_dir: str = 'data/stage1_raw'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # File type configurations with EXACT column orders as specified
        self.file_configs = {
            'ShowSaleMonChart': {
                'directory': 'ShowSaleMonChart',
                'output_file': 'raw_revenue.csv',
                'standard_headers': [
                    # CORRECTED: Revenue data should have revenue columns
                    'stock_code', 'company_name', '月別', '當月股價開盤', '當月股價收盤', 
                    '當月股價最高', '當月股價最低', '當月股價漲跌元', '當月股價漲跌%', 
                    '營業收入單月營收億', '營業收入單月月增%', '營業收入單月年增%', 
                    '營業收入累計營收億', '營業收入累計年增%', '合併營業收入單月營收億', 
                    '合併營業收入單月月增%', '合併營業收入單月年增%', '合併營業收入累計營收億', 
                    '合併營業收入累計年增%', 'file_type', 'source_file', 'processing_date'
                ]
            },

            'DividendDetail': {
                'directory': 'DividendDetail',
                'output_file': 'raw_dividends.csv',
                'standard_headers': [
                    # FIXED: Correct dividend column order exactly as specified by user
                    'stock_code', 'company_name', '發放期間(A)', '發放期間(B)', '所屬期間', 
                    '現金股利盈餘', '現金股利公積', '現金股利合計', '股票股利公積', 
                    '股票股利盈餘', '股票股利合計', '股利合計', '填息天數', '填權天數', 
                    '股價年度', '除息前股價', '除息前殖利率', '年均價股價', '年均價殖利率', 
                    '成交價股價', '成交價殖利率', '最高價股價', '最高價殖利率', 
                    '最低價股價', '最低價利率', 'file_type', 'source_file', 'processing_date'
                ]
            },
            'StockBzPerformance': {
                'directory': 'StockBzPerformance', 
                'output_file': 'raw_performance.csv',
                'standard_headers': [
                    # CORRECTED: Performance data should have performance columns
                    'stock_code', 'company_name', '年度', '股本(億)', '財報評分', '收盤', 
                    '年度股價平均', '年度股價漲跌', '漲跌(%)', '獲利金額(億)_營業收入', 
                    '獲利金額(億)_營業毛利', '獲利金額(億)_營業利益', '獲利金額(億)_業外損益', 
                    '獲利金額(億)_稅後淨利', '獲利金額(億)_獲利率(%)_營業毛利率', 
                    '獲利率(%)_營業利益率', '獲利率(%)_業外損益率', '獲利率(%)_稅後淨利率', 
                    'ROE(%)', 'ROA(%)', '稅後EPS', 'EPS年增', 'BPS(元)', 
                    'file_type', 'source_file', 'processing_date'
                ]
            }
        }
        
        self.stats = {
            'total_files_found': 0,
            'total_files_processed': 0,
            'total_rows_generated': 0,
            'files_by_type': {},
            'rows_by_type': {}
        }
    
    def read_file_safely(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read file using multiple approaches - same as simple_dividend_fix.py"""
        
        filename = file_path.stem
        logger.info(f"  Reading: {filename}")
        
        # Try multiple approaches to read the file
        df = None
        
        # Approach 1: pandas read_html with UTF-8
        try:
            tables = pd.read_html(str(file_path), encoding='utf-8')
            if tables:
                df = tables[0]
                logger.info(f"    ✅ Read with pandas.read_html (UTF-8): {df.shape}")
                return df
        except Exception as e:
            logger.debug(f"    pandas.read_html (UTF-8) failed: {e}")
        
        # Approach 2: pandas read_html with different encoding
        try:
            tables = pd.read_html(str(file_path), encoding='big5')
            if tables:
                df = tables[0]
                logger.info(f"    ✅ Read with pandas.read_html (big5): {df.shape}")
                return df
        except Exception as e:
            logger.debug(f"    pandas.read_html (big5) failed: {e}")
        
        # Approach 3: BeautifulSoup fallback
        try:
            from bs4 import BeautifulSoup
            
            # Try different encodings
            for encoding in ['utf-8', 'big5', 'gbk', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                    break
                except:
                    continue
            
            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find('table')
            
            if table:
                rows = []
                for tr in table.find_all('tr'):
                    row = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if row:
                        rows.append(row)
                
                if rows:
                    # Pad rows to same length
                    max_cols = max(len(row) for row in rows)
                    for row in rows:
                        while len(row) < max_cols:
                            row.append('')
                    
                    df = pd.DataFrame(rows[1:], columns=rows[0] if rows else None)
                    logger.info(f"    ✅ Read with BeautifulSoup: {df.shape}")
                    return df
        except Exception as e:
            logger.debug(f"    BeautifulSoup failed: {e}")
        
        logger.warning(f"    ❌ Could not read {filename}")
        return None
    
    def filter_rows_by_type(self, df: pd.DataFrame, file_type: str) -> List[List]:
        """Filter rows based on file type - specific rules for each type"""
        
        valid_rows = []
        skipped_counts = {'header': 0, 'empty': 0, 'footer': 0, 'quarterly_rows': 0}
        
        for idx, row in df.iterrows():
            row_values = [val for val in row.values if pd.notna(val)]
            row_str = ' '.join([str(val) for val in row_values])
            
            # Common filtering - skip obvious header/footer rows
            skip_keywords = ['說明', '備註', '注意', '資料來源']
            if any(keyword in row_str for keyword in skip_keywords):
                skipped_counts['header'] += 1
                continue
            
            # Skip rows that are mostly empty
            non_empty_count = sum(1 for val in row.values if pd.notna(val) and str(val).strip() != '')
            if non_empty_count < 3:  # Need at least 3 non-empty values
                skipped_counts['empty'] += 1
                continue
            
            # File-type specific filtering
            if file_type == 'DividendDetail':
                # Skip header rows containing these keywords
                header_keywords = ['發放期間', '股利', '填息', '股價年度']
                if any(keyword in row_str for keyword in header_keywords) and non_empty_count > 10:
                    skipped_counts['header'] += 1
                    continue  # Likely a header row
                
                # Skip "L" and "∟" rows (quarterly data in 發放期間(A) column - per user instructions)
                # In raw data, this would be the first column before we add stock_code/company_name
                first_col_value = str(row.values[0]).strip() if len(row.values) > 0 else ''
                if first_col_value in ['L', '∟']:  # Both Latin L and Unicode corner character
                    skipped_counts['quarterly_rows'] += 1
                    logger.debug(f"      Skipping L/∟ row (quarterly data): '{first_col_value}'")
                    continue
                
                # Skip footer/summary rows
                footer_keywords = ['累計', '合計', '總計', '平均']
                if any(keyword in row_str for keyword in footer_keywords):
                    skipped_counts['footer'] += 1
                    continue
            
            elif file_type == 'StockBzPerformance':
                # Skip header rows
                header_keywords = ['年度', '股本', '財報評分', '收盤', '獲利金額']
                if any(keyword in row_str for keyword in header_keywords) and non_empty_count > 10:
                    skipped_counts['header'] += 1
                    continue  # Likely a header row
                
                # Skip footer rows
                footer_keywords = ['累計', '合計', '總計', '平均', '小計']
                if any(keyword in row_str for keyword in footer_keywords):
                    skipped_counts['footer'] += 1
                    continue
            
            elif file_type == 'ShowSaleMonChart':
                # Skip header rows
                header_keywords = ['月別', '當月股價', '營業收入', '合併營業收入']
                if any(keyword in row_str for keyword in header_keywords) and non_empty_count > 10:
                    skipped_counts['header'] += 1
                    continue  # Likely a header row
                
                # Skip footer rows
                footer_keywords = ['累計', '合計', '總計', '平均', '備註']
                if any(keyword in row_str for keyword in footer_keywords):
                    skipped_counts['footer'] += 1
                    continue
            
            # If we get here, it's a valid data row
            valid_rows.append(row.values.tolist())
        
        # Log filtering summary
        total_skipped = sum(skipped_counts.values())
        if total_skipped > 0:
            logger.debug(f"      Filtered out: {total_skipped} rows total")
            for reason, count in skipped_counts.items():
                if count > 0:
                    logger.debug(f"        {reason}: {count} rows")
        
        return valid_rows
    
    def process_file_type(self, file_type: str) -> bool:
        """Process all files of a specific type"""
        
        config = self.file_configs[file_type]
        directory = config['directory']
        output_file = config['output_file']
        standard_headers = config['standard_headers']
        
        logger.info(f"\n📂 Processing {file_type} files from {directory}/")
        
        # Find all files in the directory
        file_pattern = f"{directory}/*.xls*"
        files = glob.glob(file_pattern)
        
        if not files:
            logger.warning(f"  ⚠️ No files found in {directory}/")
            return False
        
        logger.info(f"  📁 Found {len(files)} files")
        self.stats['total_files_found'] += len(files)
        
        all_rows = []
        processed_count = 0
        error_count = 0
        
        # Process each file
        for file_path in files:
            try:
                file_path = Path(file_path)
                
                # Extract stock code and company name from filename
                filename = file_path.stem
                parts = filename.split('_')
                stock_code = parts[1] if len(parts) >= 2 else 'UNKNOWN'
                company_name = parts[2] if len(parts) >= 3 else 'UNKNOWN'
                
                # Read the file
                df = self.read_file_safely(file_path)
                if df is None or df.empty:
                    error_count += 1
                    continue
                
                # Filter rows specific to this file type
                valid_rows = self.filter_rows_by_type(df, file_type)
                logger.info(f"    📊 Found {len(valid_rows)} valid data rows after filtering")
                
                # Special logging for DividendDetail L-row filtering
                if file_type == 'DividendDetail':
                    # Count L and ∟ rows in original data for verification
                    l_row_count = sum(1 for _, row in df.iterrows() 
                                    if len(row.values) > 0 and str(row.values[0]).strip() in ['L', '∟'])
                    if l_row_count > 0:
                        logger.info(f"    🔍 Filtered out {l_row_count} quarterly L/∟-rows (發放期間(A)='L' or '∟')")
                
                # Add metadata and append to all_rows
                for row_data in valid_rows:
                    # Create standardized row with EXACT column order
                    row_dict = {}
                    
                    # Fill in order of standard_headers
                    for i, header in enumerate(standard_headers):
                        if header == 'stock_code':
                            row_dict[header] = stock_code
                        elif header == 'company_name':
                            row_dict[header] = company_name
                        elif header == 'file_type':
                            row_dict[header] = file_type
                        elif header == 'source_file':
                            row_dict[header] = file_path.name
                        elif header == 'processing_date':
                            row_dict[header] = pd.Timestamp.now()
                        else:
                            # Data columns - map from row_data
                            # Skip the first 2 columns (stock_code, company_name) and last 3 (metadata)
                            data_headers = [h for h in standard_headers if h not in ['stock_code', 'company_name', 'file_type', 'source_file', 'processing_date']]
                            data_index = data_headers.index(header) if header in data_headers else -1
                            
                            if data_index >= 0 and data_index < len(row_data):
                                value = row_data[data_index]
                                row_dict[header] = str(value) if pd.notna(value) else ''
                            else:
                                row_dict[header] = ''
                    
                    all_rows.append(row_dict)
                
                processed_count += 1
                
                # Progress indicator
                if processed_count % 20 == 0:
                    logger.info(f"    ... processed {processed_count}/{len(files)} files")
                
            except Exception as e:
                logger.error(f"    ❌ Error processing {file_path}: {e}")
                error_count += 1
        
        # Create final DataFrame and save
        if all_rows:
            logger.info(f"\n  📊 Creating {output_file}...")
            logger.info(f"     Total rows collected: {len(all_rows)}")
            logger.info(f"     Files processed successfully: {processed_count}")
            logger.info(f"     Files with errors: {error_count}")
            
            # Create DataFrame with EXACT column order
            final_df = pd.DataFrame(all_rows, columns=standard_headers)
            
            # Save to CSV
            output_path = self.output_dir / output_file
            final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            logger.info(f"  ✅ SUCCESS: Created {output_path}")
            logger.info(f"     📊 Final CSV: {len(final_df)} rows, {len(final_df.columns)} columns")
            logger.info(f"     📈 Unique stocks: {final_df['stock_code'].nunique()}")
            logger.info(f"     🔢 Column order: {', '.join(standard_headers[:5])}...{', '.join(standard_headers[-3:])}")
            
            # Update stats
            self.stats['total_files_processed'] += processed_count
            self.stats['total_rows_generated'] += len(final_df)
            self.stats['files_by_type'][file_type] = processed_count
            self.stats['rows_by_type'][file_type] = len(final_df)
            
            return True
        else:
            logger.error(f"  ❌ No data was successfully processed for {file_type}")
            return False
    
    def run_pipeline(self) -> Dict:
        """Run the complete simple robust pipeline"""
        
        logger.info("🚀 Starting SIMPLE ROBUST Stage 1 Pipeline")
        logger.info("✨ Features: Row-by-row processing + Exact column orders + Reliable results")
        
        success_count = 0
        
        # Process each file type
        for file_type in self.file_configs.keys():
            if self.process_file_type(file_type):
                success_count += 1
        
        # Final summary
        logger.info(f"\n📊 === SIMPLE ROBUST Stage 1 Results ===")
        logger.info(f"✅ File types processed successfully: {success_count}/3")
        logger.info(f"📁 Total files found: {self.stats['total_files_found']}")
        logger.info(f"📁 Total files processed: {self.stats['total_files_processed']}")
        logger.info(f"📊 Total rows generated: {self.stats['total_rows_generated']}")
        
        if self.stats['files_by_type']:
            logger.info(f"\n📈 Breakdown by file type:")
            for file_type, count in self.stats['files_by_type'].items():
                rows = self.stats['rows_by_type'].get(file_type, 0)
                output_file = self.file_configs[file_type]['output_file']
                logger.info(f"   {file_type}: {count} files → {rows} rows → {output_file}")
        
        return self.stats

@click.command()
@click.option('--output-dir', default='data/stage1_raw', help='Output directory for CSV files')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def run_stage1_simple(output_dir: str, debug: bool):
    """
    Run SIMPLE ROBUST Stage 1: Excel/HTML to CSV conversion
    
    🎯 KEY FEATURES:
    ✅ Processes files directly from ShowSaleMonChart/, DividendDetail/, StockBzPerformance/
    ✅ Uses reliable row-by-row approach (no complex DataFrame concatenation) 
    ✅ Follows EXACT column orders as specified by user
    ✅ Metadata columns (file_type, source_file, processing_date) at the END
    ✅ No temporary file copying needed
    """
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if source directories exist
    required_dirs = ['ShowSaleMonChart', 'DividendDetail', 'StockBzPerformance']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        click.echo(f"❌ Missing required directories: {', '.join(missing_dirs)}")
        click.echo(f"💡 Expected directory structure:")
        for d in required_dirs:
            click.echo(f"   {d}/    (containing .xls/.xlsx files)")
        return
    
    # Run pipeline
    pipeline = SimpleRobustPipeline(output_dir)
    stats = pipeline.run_pipeline()
    
    # Display results
    click.echo(f"\n🎉 SIMPLE ROBUST Stage 1 COMPLETED!")
    click.echo(f"📊 Summary:")
    click.echo(f"   📁 Files processed: {stats['total_files_processed']}/{stats['total_files_found']}")
    click.echo(f"   📊 Total rows: {stats['total_rows_generated']:,}")
    click.echo(f"   💾 Output directory: {output_dir}")
    
    if stats['files_by_type']:
        click.echo(f"\n📈 Generated files with EXACT column orders:")
        for file_type, count in stats['files_by_type'].items():
            output_file = pipeline.file_configs[file_type]['output_file']
            rows = stats['rows_by_type'][file_type]
            headers = pipeline.file_configs[file_type]['standard_headers']
            click.echo(f"   ✅ {output_file}: {rows:,} rows, {len(headers)} columns")
            click.echo(f"      Columns: {', '.join(headers[:3])}...{', '.join(headers[-3:])}")
    
    if stats['total_files_processed'] > 0:
        click.echo(f"\n🚀 Next steps:")
        click.echo(f"   1. Check output files in: {output_dir}")
        click.echo(f"   2. Run Stage 2: python -m src.pipelines.stage2_data_cleaning")
        click.echo(f"   3. Or run complete pipeline: python scripts\\run_pipeline_test.py")
    else:
        click.echo(f"\n❌ No files were processed successfully!")
        click.echo(f"💡 Check that your directories contain Excel files:")
        for d in required_dirs:
            click.echo(f"   {d}/*.xls*")

if __name__ == '__main__':
    run_stage1_simple()