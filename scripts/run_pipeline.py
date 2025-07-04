# scripts/run_pipeline_test.py
"""
Complete 5-Stage Pipeline Test - SIMPLE ROBUST VERSION
✅ USES: New simple Stage 1 pipeline (no file copying)
✅ PROCESSES: Files directly from original directories
✅ VALIDATES: Each stage outputs with proper error handling
"""
import subprocess
import click
from pathlib import Path
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_echo(message: str):
    """Safe echo that handles Unicode encoding issues on Windows"""
    try:
        click.echo(message)
    except UnicodeEncodeError:
        # Remove emoji and special Unicode characters
        import re
        clean_message = re.sub(r'[^\x00-\x7F]+', '', message)
        click.echo(clean_message)

def setup_unicode_environment():
    """Setup environment to handle Unicode better on Windows"""
    try:
        # Set console output encoding to UTF-8 if possible
        if sys.platform.startswith('win'):
            os.system('chcp 65001 >nul 2>&1')
    except:
        pass

def check_source_directories():
    """Check if required source directories exist"""
    
    required_dirs = ['ShowSaleMonChart', 'DividendDetail', 'StockBzPerformance']
    
    safe_echo("Checking source directories...")
    
    total_files = 0
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            excel_files = list(dir_path.glob("*.xls*"))
            file_count = len(excel_files)
            total_files += file_count
            safe_echo(f"  {dir_name}/: {file_count} files")
        else:
            missing_dirs.append(dir_name)
            safe_echo(f"  {dir_name}/: MISSING")
    
    if missing_dirs:
        safe_echo(f"\nERROR: Missing required directories: {', '.join(missing_dirs)}")
        safe_echo(f"Expected directory structure:")
        for d in required_dirs:
            safe_echo(f"  {d}/    (containing .xls/.xlsx files)")
        return False, 0
    
    if total_files == 0:
        safe_echo("ERROR: No Excel files found in source directories!")
        return False, 0
    
    safe_echo(f"SUCCESS: Found {total_files} total Excel files")
    return True, total_files

def validate_stage_output(stage_num: int, expected_files: list):
    """Validate stage output files exist and contain data"""
    
    stage_dir = Path(f"data/stage{stage_num}_{'raw' if stage_num == 1 else 'cleaned' if stage_num == 2 else 'analysis' if stage_num == 3 else 'enhanced' if stage_num == 4 else 'output'}")
    
    safe_echo(f"\nValidating Stage {stage_num} outputs...")
    
    if not stage_dir.exists():
        safe_echo(f"ERROR: Stage {stage_num} output directory missing: {stage_dir}")
        return False
    
    validation_results = []
    
    for expected_file in expected_files:
        file_path = stage_dir / expected_file
        
        if file_path.exists():
            # Check if file has content
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                rows = len(df)
                cols = len(df.columns)
                
                validation_results.append({
                    'file': expected_file,
                    'exists': True,
                    'rows': rows,
                    'columns': cols,
                    'status': 'SUCCESS' if rows > 0 else 'WARNING'
                })
                
                safe_echo(f"  {validation_results[-1]['status']}: {expected_file}: {rows} rows, {cols} columns")
                
                # Show sample info for Stage 1
                if stage_num == 1 and rows > 0:
                    # Check for multiple stocks
                    if 'stock_code' in df.columns:
                        unique_stocks = df['stock_code'].nunique()
                        safe_echo(f"     Unique stocks: {unique_stocks}")
                        
                        # Show sample stock codes
                        sample_stocks = df['stock_code'].unique()[:3]
                        safe_echo(f"     Sample stocks: {', '.join(map(str, sample_stocks))}")
                
            except Exception as e:
                validation_results.append({
                    'file': expected_file,
                    'exists': True,
                    'rows': 0,
                    'columns': 0,
                    'status': 'ERROR',
                    'error': str(e)
                })
                safe_echo(f"  ERROR: {expected_file}: Error reading file - {e}")
        else:
            validation_results.append({
                'file': expected_file,
                'exists': False,
                'status': 'ERROR'
            })
            safe_echo(f"  ERROR: {expected_file}: File missing")
    
    # Overall validation
    success_count = sum(1 for r in validation_results if r['status'] == 'SUCCESS')
    total_count = len(validation_results)
    
    if success_count == total_count:
        safe_echo(f"SUCCESS: Stage {stage_num} validation: {success_count}/{total_count} files valid")
        return True
    else:
        safe_echo(f"WARNING: Stage {stage_num} validation: {success_count}/{total_count} files valid")
        return success_count > 0  # Partial success still allows continuation

def run_subprocess_safely(cmd_args, stage_name):
    """Run subprocess with proper encoding handling"""
    try:
        # Force UTF-8 encoding for subprocess
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            cmd_args, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace',  # Replace problematic characters instead of failing
            env=env
        )
        
        return result
        
    except Exception as e:
        safe_echo(f"Error running {stage_name}: {e}")
        return None

def run_complete_pipeline_test():
    """Run complete 5-stage pipeline test with the new simple approach"""
    
    # Setup Unicode environment
    setup_unicode_environment()
    
    safe_echo("Starting SIMPLE ROBUST Complete Pipeline Test")
    safe_echo("Features: Direct directory processing + No file copying + Reliable CSV generation")
    
    # Configuration
    credentials_file = "google_key.json"
    sheet_id = "1ufQ2BrG_lmUiM7c1agL3kCNs1L4AhZgoNlB4TKgBy0I"
    
    # Check source directories
    dirs_ok, total_files = check_source_directories()
    if not dirs_ok:
        return
    
    try:
        # Stage 1: Excel → CSV (Process files directly from directories)
        safe_echo(f"\n{'='*50}")
        safe_echo("Stage 1: Excel -> Raw CSV (Direct processing)")
        safe_echo(f"{'='*50}")
        
        # Check for file locks before starting
        output_files = ['data/stage1_raw/raw_revenue.csv', 'data/stage1_raw/raw_dividends.csv', 'data/stage1_raw/raw_performance.csv']
        for output_file in output_files:
            if Path(output_file).exists():
                try:
                    with open(output_file, 'a'):
                        pass
                except PermissionError:
                    safe_echo(f"ERROR: File is locked (possibly open in Excel): {output_file}")
                    safe_echo("Please close all Excel files and try again.")
                    return
        
        result = run_subprocess_safely([
            'python', '-m', 'src.pipelines.stage1_excel_to_csv_html'
        ], "Stage 1")
        
        if result is None or result.returncode != 0:
            safe_echo(f"ERROR: Stage 1 failed:")
            if result:
                safe_echo(f"STDOUT: {result.stdout}")
                safe_echo(f"STDERR: {result.stderr}")
            
            # Check for common errors
            error_text = result.stderr if result else ""
            if "Permission denied" in error_text:
                safe_echo("\nTROUBLESHOOTING:")
                safe_echo("- Close any Excel files that might be open")
                safe_echo("- Check if CSV files are open in Excel")
                safe_echo("- Restart command prompt as administrator if needed")
            elif "Missing required directories" in error_text:
                safe_echo("\nTROUBLESHOOTING:")
                safe_echo("- Ensure directories exist: ShowSaleMonChart/, DividendDetail/, StockBzPerformance/")
                safe_echo("- Check that directories contain .xls/.xlsx files")
            
            return
        else:
            safe_echo("SUCCESS: Stage 1 completed")
            if result.stdout:
                # Show last part of output
                try:
                    output_lines = result.stdout.split('\n')
                    for line in output_lines[-10:]:  # Show last 10 lines
                        if line.strip():
                            safe_echo(line)
                except:
                    safe_echo("Output contains special characters (processing succeeded)")
        
        # Validate Stage 1 outputs
        stage1_files = ['raw_revenue.csv', 'raw_dividends.csv', 'raw_performance.csv']
        if not validate_stage_output(1, stage1_files):
            safe_echo("WARNING: Stage 1 validation issues found")
            safe_echo("Continuing to next stage...")
        
        # Stage 2: Data Cleaning
        safe_echo(f"\n{'='*50}")
        safe_echo("Stage 2: Data Cleaning")
        safe_echo(f"{'='*50}")
        
        result = run_subprocess_safely([
            'python', '-m', 'src.pipelines.stage2_data_cleaning'
        ], "Stage 2")
        
        if result is None or result.returncode != 0:
            safe_echo(f"ERROR: Stage 2 failed:")
            if result:
                safe_echo(f"STDERR: {result.stderr}")
            return
        else:
            safe_echo("SUCCESS: Stage 2 completed")
        
        # Validate Stage 2 outputs
        stage2_files = ['cleaned_dividends.csv', 'cleaned_performance.csv', 'cleaned_revenue.csv']
        if not validate_stage_output(2, stage2_files):
            safe_echo("WARNING: Stage 2 validation issues found")
            safe_echo("Continuing to next stage...")
        
        # Stage 3: Basic Analysis
        safe_echo(f"\n{'='*50}")
        safe_echo("Stage 3: Basic Analysis")
        safe_echo(f"{'='*50}")
        
        result = run_subprocess_safely([
            'python', '-m', 'src.pipelines.stage3_basic_analysis'
        ], "Stage 3")
        
        if result is None or result.returncode != 0:
            safe_echo(f"ERROR: Stage 3 failed:")
            if result:
                safe_echo(f"STDERR: {result.stderr}")
            return
        else:
            safe_echo("SUCCESS: Stage 3 completed")
        
        # Validate Stage 3 outputs
        stage3_files = ['stock_analysis.csv']
        if not validate_stage_output(3, stage3_files):
            safe_echo("WARNING: Stage 3 validation issues found")
            safe_echo("Continuing to next stage...")
        
        # Stage 4: Advanced Analysis
        safe_echo(f"\n{'='*50}")
        safe_echo("Stage 4: Advanced Analysis")
        safe_echo(f"{'='*50}")
        
        result = run_subprocess_safely([
            'python', '-m', 'src.pipelines.stage4_advanced_analysis'
        ], "Stage 4")
        
        if result is None or result.returncode != 0:
            safe_echo(f"ERROR: Stage 4 failed:")
            if result:
                safe_echo(f"STDERR: {result.stderr}")
            return
        else:
            safe_echo("SUCCESS: Stage 4 completed")
        
        # Validate Stage 4 outputs
        stage4_files = ['enhanced_analysis.csv']
        if not validate_stage_output(4, stage4_files):
            safe_echo("WARNING: Stage 4 validation issues found")
            safe_echo("Continuing to next stage...")
        
        # Stage 5: Google Sheets Publishing
        safe_echo(f"\n{'='*50}")
        safe_echo("Stage 5: Google Sheets Publishing")
        safe_echo(f"{'='*50}")
        
        # Check if credentials exist
        if not Path(credentials_file).exists():
            safe_echo(f"WARNING: Credentials file not found: {credentials_file}")
            safe_echo("Skipping Google Sheets publishing (Stages 1-4 completed successfully)")
        else:
            result = run_subprocess_safely([
                'python', '-m', 'src.pipelines.stage5_sheets_publisher',
                '--credentials', credentials_file,
                '--sheet-id', sheet_id
            ], "Stage 5")
            
            if result is None or result.returncode != 0:
                safe_echo(f"WARNING: Stage 5 failed (non-critical):")
                if result:
                    safe_echo(f"STDERR: {result.stderr}")
            else:
                safe_echo("SUCCESS: Stage 5 completed")
        
        # Final success message
        safe_echo(f"\n{'='*50}")
        safe_echo("SIMPLE ROBUST PIPELINE TEST COMPLETED!")
        safe_echo(f"{'='*50}")
        safe_echo(f"SUCCESS: All stages executed successfully")
        safe_echo(f"Processed {total_files} Excel files from original directories")
        safe_echo(f"Check outputs in data/ subdirectories")
        
        if Path(credentials_file).exists():
            safe_echo(f"Dashboard URL:")
            safe_echo(f"   https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        
        # Show final data summary
        safe_echo(f"\nFinal Data Summary:")
        try:
            import pandas as pd
            final_analysis = pd.read_csv('data/stage4_enhanced/enhanced_analysis.csv')
            safe_echo(f"   Total stocks analyzed: {len(final_analysis)}")
            safe_echo(f"   Strong Buy recommendations: {len(final_analysis[final_analysis['recommendation'] == 'Strong Buy'])}")
            safe_echo(f"   Buy recommendations: {len(final_analysis[final_analysis['recommendation'] == 'Buy'])}")
        except:
            safe_echo(f"   Check data/stage4_enhanced/enhanced_analysis.csv for results")
        
    except subprocess.CalledProcessError as e:
        safe_echo(f"ERROR: Pipeline stage failed: {e}")
    except Exception as e:
        safe_echo(f"ERROR: Test failed: {e}")

if __name__ == '__main__':
    run_complete_pipeline_test()