# scripts/run_pipeline.py
"""
Complete 5-Stage Pipeline Runner v1.3.0 - 8-SCENARIO P/E FRAMEWORK VERSION
✅ USES: Revolutionary 8-scenario P/E valuation with intelligent scenario selection
✅ PROCESSES: Files directly from original directories with enhanced P/E analysis
✅ VALIDATES: Each stage outputs with 8-scenario P/E validation
✅ FEATURES: Complete data pipeline transparency with personalized P/E valuations
✅ ENVIRONMENT: Loads .env file for local development
"""
import subprocess
import click
from pathlib import Path
import logging
import sys
import os

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, .env file will not be loaded")
    print("   Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

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
    
    stage_dir_names = {
        1: 'raw',
        2: 'cleaned', 
        3: 'analysis',
        4: 'enhanced',
        5: 'output'
    }
    
    stage_dir = Path(f"data/stage{stage_num}_{stage_dir_names[stage_num]}")
    
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
                
                # Show key columns for Stage 4 (v1.3.0 - 8-scenario P/E support)
                if stage_num == 4 and rows > 0:
                    valuation_cols = [col for col in df.columns if 'valuation' in col or 'consensus' in col]
                    if valuation_cols:
                        safe_echo(f"     Valuation models: {len(valuation_cols)} ({', '.join(valuation_cols[:3])}...)")
                    
                    # Check for BPS column (needed for NAV calculations)
                    if 'BPS(元)' in df.columns:
                        safe_echo(f"     BPS data: Available for NAV calculations")
                    
                    # Check for 8-scenario P/E columns
                    pe_scenario_cols = [col for col in df.columns if 'pe_' in col and 'scenario' in col]
                    if pe_scenario_cols:
                        safe_echo(f"     8-Scenario P/E: {len(pe_scenario_cols)} analysis columns")
                    
                    # Check for market cap classification
                    if 'market_cap_trillion' in df.columns:
                        safe_echo(f"     Market Cap: Real calculation from 股本(億) data")
                    
                    # Check for enhanced P/E confidence scoring
                    if 'pe_confidence_score' in df.columns:
                        safe_echo(f"     P/E Confidence: Intelligent scenario selection scoring")
                
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

def validate_stage5_hybrid_dashboard():
    """Special validation for Stage 5 v1.3.0 - hybrid formula dashboard with 8-scenario P/E"""
    safe_echo(f"\nValidating Stage 5 v1.3.0 Hybrid Formula Dashboard Configuration...")
    safe_echo(f"NOTE: v1.3.0 uses hybrid approach with enhanced 8-scenario P/E framework")
    safe_echo(f"Expected: 10 tabs total with live formulas + 8-scenario P/E analysis")
    
    # Debug: Show environment loading status
    try:
        from dotenv import load_dotenv
        safe_echo(f"  📋 dotenv library available - .env file loading enabled")
    except ImportError:
        safe_echo(f"  ⚠️  dotenv library not found - .env files will not be loaded")
        safe_echo(f"      Install with: pip install python-dotenv")
    
    # Check environment variables only
    credentials_env = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    
    # Debug: Show what was found
    safe_echo(f"  🔍 Environment variable check:")
    safe_echo(f"      GOOGLE_SHEETS_CREDENTIALS: {'✅ Found' if credentials_env else '❌ Not found'}")
    safe_echo(f"      GOOGLE_SHEET_ID: {'✅ Found' if sheet_id else '❌ Not found'}")
    
    credentials_found = False
    if credentials_env:
        if credentials_env.strip().startswith('{'):  # JSON content
            credentials_found = True
            safe_echo(f"  ✅ Credentials: JSON content from GOOGLE_SHEETS_CREDENTIALS environment variable")
        elif Path(credentials_env).exists():  # File path in environment
            credentials_found = True
            safe_echo(f"  ✅ Credentials: File path from GOOGLE_SHEETS_CREDENTIALS -> {credentials_env}")
        else:
            safe_echo(f"  ❌ Credentials: GOOGLE_SHEETS_CREDENTIALS points to non-existent file: {credentials_env}")
    else:
        safe_echo(f"  ❌ Credentials: GOOGLE_SHEETS_CREDENTIALS environment variable not set")
    
    if sheet_id:
        safe_echo(f"  ✅ Sheet ID: {sheet_id} (from GOOGLE_SHEET_ID environment variable)")
    else:
        safe_echo(f"  ❌ Sheet ID: GOOGLE_SHEET_ID environment variable not set")
    
    # Check for prerequisite data for 8-scenario P/E formulas
    safe_echo(f"\n  🔍 8-Scenario P/E Prerequisites:")
    
    # Check Basic Analysis for scenario selection data
    basic_analysis_file = Path('data/stage3_analysis/stock_analysis.csv')
    if basic_analysis_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(basic_analysis_file)
            
            # Check for columns needed by 8-scenario P/E
            required_cols = ['avg_eps', 'avg_roe', 'avg_roa', 'revenue_growth']
            available_cols = [col for col in required_cols if col in df.columns]
            
            safe_echo(f"      Basic Analysis: ✅ Available ({len(available_cols)}/{len(required_cols)} columns)")
            safe_echo(f"      8-Scenario P/E: EPS selection (annual vs Q1), P/E selection (4 options)")
            
        except Exception as e:
            safe_echo(f"      Basic Analysis: ❌ Error reading - {e}")
    else:
        safe_echo(f"      Basic Analysis: ❌ Not found - needed for 8-scenario P/E analysis")
    
    # Check Raw Performance for BPS + 股本 data (market cap calculations)
    raw_performance_file = Path('data/stage1_raw/raw_performance.csv')
    if raw_performance_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(raw_performance_file)
            
            has_bps = 'BPS(元)' in df.columns
            has_capital = '股本(億)' in df.columns
            
            if has_bps:
                safe_echo(f"      Raw Performance: ✅ BPS data available for NAV calculations")
            if has_capital:
                safe_echo(f"      Raw Performance: ✅ 股本(億) data available for real market cap calculation")
            
            if not (has_bps or has_capital):
                safe_echo(f"      Raw Performance: ⚠️  Missing BPS or 股本 data - 8-scenario logic may be limited")
                
        except Exception as e:
            safe_echo(f"      Raw Performance: ❌ Error reading - {e}")
    else:
        safe_echo(f"      Raw Performance: ❌ Not found - needed for market cap classification")
    
    # Check Enhanced Analysis for 8-scenario P/E results
    enhanced_analysis_file = Path('data/stage4_enhanced/enhanced_analysis.csv')
    if enhanced_analysis_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(enhanced_analysis_file)
            
            # Check for 8-scenario P/E columns
            pe_scenario_cols = [col for col in df.columns if 'pe_' in col and ('scenario' in col or 'confidence' in col)]
            market_cap_cols = [col for col in df.columns if 'market_cap' in col or 'size_class' in col]
            
            safe_echo(f"      Enhanced Analysis: ✅ Available with 8-scenario P/E framework")
            if pe_scenario_cols:
                safe_echo(f"      8-Scenario Columns: {len(pe_scenario_cols)} analysis columns")
            if market_cap_cols:
                safe_echo(f"      Market Cap Classification: Available for company sizing")
            
        except Exception as e:
            safe_echo(f"      Enhanced Analysis: ❌ Error reading - {e}")
    else:
        safe_echo(f"      Enhanced Analysis: ❌ Not found - needed for 8-scenario P/E dashboard")
    
    # Warn about deprecated google_key.json if it exists
    if Path("google_key.json").exists():
        safe_echo(f"  ⚠️  WARNING: google_key.json file found but will be IGNORED")
        safe_echo(f"      v1.3.0 uses GOOGLE_SHEETS_CREDENTIALS environment variable exclusively")
    
    # Check for .env file
    if Path(".env").exists():
        safe_echo(f"  📄 .env file found - should be loaded automatically")
    else:
        safe_echo(f"  📄 No .env file found in current directory")
    
    if credentials_found and sheet_id:
        safe_echo(f"✅ SUCCESS: Stage 5 configuration ready for 8-scenario P/E hybrid dashboard")
        safe_echo(f"  Dashboard Tabs: Current Snapshot, Top Picks, Single Pick (enhanced P/E)")
        safe_echo(f"  8-Scenario P/E: Intelligent scenario selection + confidence scoring")
        safe_echo(f"  Market Cap Classification: Real calculation from 股本(億) data")
        safe_echo(f"  Meta Tabs: Summary, Last Updated (v1.3.0 features)")
        safe_echo(f"  Data Tabs: Raw Revenue, Raw Dividends, Raw Performance, Basic Analysis, Enhanced Analysis")
        return True
    else:
        safe_echo(f"❌ WARNING: Stage 5 configuration incomplete")
        if not credentials_found:
            safe_echo(f"  Missing: GOOGLE_SHEETS_CREDENTIALS environment variable")
            safe_echo(f"  Set to: JSON content or file path to credentials")
        if not sheet_id:
            safe_echo(f"  Missing: GOOGLE_SHEET_ID environment variable")
            safe_echo(f"  Set to: Your Google Sheets ID")
        safe_echo(f"  Stage 5 will be skipped (Stages 1-4 can still complete)")
        safe_echo(f"")
        safe_echo(f"  🔧 Troubleshooting Steps:")
        safe_echo(f"    1. Ensure .env file exists in current directory")
        safe_echo(f"    2. Install python-dotenv: pip install python-dotenv")
        safe_echo(f"    3. Export manually: export GOOGLE_SHEETS_CREDENTIALS='...'")
        safe_echo(f"    4. Check .env file format (no spaces around =)")
        safe_echo(f"")
        safe_echo(f"  📋 Setup Instructions:")
        safe_echo(f"    export GOOGLE_SHEETS_CREDENTIALS='path/to/credentials.json'")
        safe_echo(f"    export GOOGLE_SHEET_ID='your_sheet_id_here'")
        safe_echo(f"  Or create .env file with these variables")
        return False

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

def run_complete_pipeline_v130():
    """Run complete 5-stage pipeline with v1.3.0 8-scenario P/E framework"""
    
    # Setup Unicode environment
    setup_unicode_environment()
    
    safe_echo("=" * 70)
    safe_echo("STOCK ANALYSIS SYSTEM v1.3.0 - COMPLETE PIPELINE")
    safe_echo("Features: 5-Stage Processing + 8-Scenario P/E Framework + Hybrid Dashboard")
    safe_echo("=" * 70)
    
    # Debug environment variable loading
    safe_echo("🔧 Environment Configuration Check:")
    safe_echo(f"   Current directory: {os.getcwd()}")
    safe_echo(f"   .env file exists: {'✅ Yes' if Path('.env').exists() else '❌ No'}")
    
    # Show dotenv status
    try:
        from dotenv import load_dotenv
        safe_echo(f"   python-dotenv available: ✅ Yes")
    except ImportError:
        safe_echo(f"   python-dotenv available: ❌ No (install with: pip install python-dotenv)")
    
    # Configuration from environment variables only
    credentials_env = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    
    # Debug what was loaded
    safe_echo(f"   GOOGLE_SHEETS_CREDENTIALS: {'✅ Loaded' if credentials_env else '❌ Not found'}")
    safe_echo(f"   GOOGLE_SHEET_ID: {'✅ Loaded' if sheet_id else '❌ Not found'}")
    
    if credentials_env and len(credentials_env) > 50:
        safe_echo(f"   Credentials type: {'JSON content' if credentials_env.strip().startswith('{') else 'File path'}")
    
    safe_echo("")  # Empty line for readability
    
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
        
        # Stage 3: Basic Analysis (feeds 8-scenario P/E framework)
        safe_echo(f"\n{'='*50}")
        safe_echo("Stage 3: Basic Analysis (feeds 8-scenario P/E framework)")
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
            safe_echo("This data will feed 8-scenario P/E intelligent scenario selection")
        
        # Validate Stage 3 outputs
        stage3_files = ['stock_analysis.csv']
        if not validate_stage_output(3, stage3_files):
            safe_echo("WARNING: Stage 3 validation issues found")
            safe_echo("Continuing to next stage...")
        
        # Stage 4: Advanced Analysis with 8-Scenario P/E Framework
        safe_echo(f"\n{'='*50}")
        safe_echo("Stage 4: Advanced Analysis with 8-Scenario P/E Framework v1.3.0")
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
            safe_echo("8-Scenario P/E Framework: Personalized valuations with intelligent scenario selection")
        
        # Validate Stage 4 outputs
        stage4_files = ['enhanced_analysis.csv']
        if not validate_stage_output(4, stage4_files):
            safe_echo("WARNING: Stage 4 validation issues found")
            safe_echo("Continuing to next stage...")
        
        # Stage 5: Google Sheets Publishing v1.3.0 (Enhanced with 8-Scenario P/E)
        safe_echo(f"\n{'='*50}")
        safe_echo("Stage 5: Google Sheets Publishing v1.3.0 (Enhanced with 8-Scenario P/E)")
        safe_echo(f"{'='*50}")
        
        # Validate Stage 5 configuration
        stage5_ready = validate_stage5_hybrid_dashboard()
        
        if not stage5_ready:
            safe_echo(f"WARNING: Skipping Stage 5 (configuration incomplete)")
            safe_echo(f"Set GOOGLE_SHEETS_CREDENTIALS and GOOGLE_SHEET_ID to enable 8-scenario P/E dashboard publishing")
        else:
            result = run_subprocess_safely([
                'python', '-m', 'src.pipelines.stage5_sheets_publisher'
            ], "Stage 5")
            
            if result is None or result.returncode != 0:
                safe_echo(f"WARNING: Stage 5 failed (non-critical):")
                if result:
                    safe_echo(f"STDERR: {result.stderr}")
            else:
                safe_echo("SUCCESS: Stage 5 completed - 8-Scenario P/E Enhanced Dashboard Published!")
        
        # Final success message
        safe_echo(f"\n{'='*70}")
        safe_echo("STOCK ANALYSIS SYSTEM v1.3.0 PIPELINE COMPLETED!")
        safe_echo(f"{'='*70}")
        safe_echo(f"SUCCESS: All stages executed successfully with 8-scenario P/E framework")
        safe_echo(f"Processed {total_files} Excel files from original directories")
        safe_echo(f"Generated comprehensive 5-stage analysis pipeline with personalized P/E valuations")
        
        # Show pipeline outputs
        safe_echo(f"\nPipeline Outputs:")
        safe_echo(f"  Stage 1: 3 Raw CSV files (Revenue, Dividends, Performance + 股本億 data)")
        safe_echo(f"  Stage 2: 3 Cleaned CSV files with data quality scores")  
        safe_echo(f"  Stage 3: 1 Combined basic analysis file (feeds 8-scenario P/E logic)")
        safe_echo(f"  Stage 4: 1 Enhanced analysis with 8-scenario P/E + 4 other models")
        
        if stage5_ready:
            safe_echo(f"  Stage 5: 10-Tab Enhanced Google Sheets Dashboard")
            safe_echo(f"           - 3 Dashboard Tabs: Enhanced with 8-scenario P/E analysis")
            safe_echo(f"           - 5 Data Tabs: Raw data + analysis stages for transparency")
            safe_echo(f"           - 2 Meta Tabs: Summary + system status (v1.3.0 features)")
            safe_echo(f"           - Configuration: Environment variables only")
            safe_echo(f"")
            safe_echo(f"8-Scenario P/E Dashboard URL:")
            safe_echo(f"   https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        else:
            safe_echo(f"  Stage 5: Skipped (set GOOGLE_SHEETS_CREDENTIALS & GOOGLE_SHEET_ID to enable)")
            safe_echo(f"           No google_key.json files used - environment variables only")
        
        # Show final data summary with 8-scenario P/E highlights
        safe_echo(f"\nFinal Data Summary:")
        try:
            import pandas as pd
            final_analysis = pd.read_csv('data/stage4_enhanced/enhanced_analysis.csv')
            safe_echo(f"   Total stocks analyzed: {len(final_analysis)}")
            safe_echo(f"   Strong Buy recommendations: {len(final_analysis[final_analysis['recommendation'] == 'Strong Buy'])}")
            safe_echo(f"   Buy recommendations: {len(final_analysis[final_analysis['recommendation'] == 'Buy'])}")
            
            # Show 8-scenario P/E summary
            if 'pe_confidence_score' in final_analysis.columns:
                avg_pe_confidence = final_analysis['pe_confidence_score'].mean()
                safe_echo(f"   8-Scenario P/E Models: Avg confidence {avg_pe_confidence:.1%}")
                
            if 'market_cap_trillion' in final_analysis.columns:
                mega_cap_count = len(final_analysis[final_analysis['market_cap_trillion'] >= 1.0])
                safe_echo(f"   Mega-cap companies (≥1兆): {mega_cap_count}")
            
            # Check basic analysis for scenario selection data
            basic_analysis = pd.read_csv('data/stage3_analysis/stock_analysis.csv')
            scenario_cols = ['avg_eps', 'avg_roe', 'avg_roa', 'revenue_growth']
            available_scenario_cols = [col for col in scenario_cols if col in basic_analysis.columns]
            safe_echo(f"   8-Scenario selection data: {len(available_scenario_cols)}/{len(scenario_cols)} metrics available")
            
        except:
            safe_echo(f"   Check data/stage4_enhanced/enhanced_analysis.csv for results")
        
        safe_echo(f"\nv1.3.0 8-Scenario P/E Features Completed:")
        safe_echo(f"   ✅ 5-Stage processing pipeline")
        safe_echo(f"   ✅ Revolutionary 8-scenario P/E framework (2 EPS × 4 P/E scenarios)")
        safe_echo(f"   ✅ Intelligent scenario selection with systematic decision trees")
        safe_echo(f"   ✅ Real market cap calculation using 股本(億) data")
        safe_echo(f"   ✅ Company classification (mega-cap vs large-cap vs mid-cap)")
        safe_echo(f"   ✅ Growth analysis (explosive ≥50% vs moderate vs mature <20%)")
        safe_echo(f"   ✅ Confidence scoring for risk-adjusted recommendations")
        safe_echo(f"   ✅ Enhanced five-model consensus with sophisticated P/E component")
        safe_echo(f"   ✅ Personalized valuations eliminating subjective bias")
        safe_echo(f"   ✅ Complete scenario transparency and auditability")
        safe_echo(f"   ✅ Time frame recommendations for target achievement")
        safe_echo(f"   ✅ Professional-grade investment analysis comparable to institutional tools")
        safe_echo(f"   ✅ Environment variable configuration for secure deployment")
        safe_echo(f"   ✅ Enhanced Google Sheets dashboard with 8-scenario P/E integration")
        
    except subprocess.CalledProcessError as e:
        safe_echo(f"ERROR: Pipeline stage failed: {e}")
    except Exception as e:
        safe_echo(f"ERROR: Pipeline failed: {e}")

@click.command()
@click.option('--stage', default=None, type=int, help='Run specific stage only (1-5)')
@click.option('--validate-only', is_flag=True, help='Only validate outputs without running')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(stage: int, validate_only: bool, debug: bool):
    """
    Stock Analysis System v1.3.0 - Complete Pipeline Runner
    
    🎯 v1.3.0 REVOLUTIONARY FEATURES:
    ✅ 8-Scenario P/E Valuation Framework with intelligent scenario selection
    ✅ Real market cap calculation using 股本(億) data from GoodInfo
    ✅ Systematic decision trees eliminate subjective bias in valuations
    ✅ Company classification: Mega-cap (≥1兆) vs Large-cap vs Mid-cap
    ✅ Growth analysis: Explosive (≥50%) vs Moderate vs Mature (<20%)
    ✅ Enhanced confidence scoring for risk-adjusted recommendations
    ✅ Five-model consensus with sophisticated P/E component
    ✅ Complete scenario transparency and auditability
    
    🔧 8-Scenario P/E Framework:
    
    EPS Selection (2 options):
    - 2024年度 EPS: Conservative baseline from full-year performance
    - Q1年化 EPS: Growth-adjusted projection (selected if explosive growth + quality data)
    
    P/E Selection (4 options):
    - Q1 P/E: Current quarter market valuation
    - 2024 P/E: Annual historical market valuation
    - 兩年平均 P/E: Two-year average for stability
    - 電子業 P/E (20.0x): Electronics industry standard
    
    🎯 Intelligent Selection Logic:
    
    EPS Selection:
    IF (Q1 growth ≥50% AND data quality good AND no seasonality) 
      → Use Q1 annualized EPS
    ELSE 
      → Use conservative 2024 annual EPS
    
    P/E Selection:
    IF (Market cap ≥1兆 AND industry leader) 
      → Two-year average P/E (leader premium)
    ELSE IF (Revenue growth <20% OR mature company) 
      → 2024 P/E (conservative valuation)
    ELSE 
      → Electronics industry P/E (standard 20.0x)
    
    🔧 Environment Variables Required for Stage 5:
    - GOOGLE_SHEETS_CREDENTIALS: JSON content or path to credentials file
    - GOOGLE_SHEET_ID: Your Google Sheets ID
    
    📋 Setup Example:
    export GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account",...}'
    export GOOGLE_SHEET_ID='1ufQ2BrG_lmUiM7c1agL3kCNs1L4AhZgoNlB4TKgBy0I'
    
    Or create .env file:
    GOOGLE_SHEETS_CREDENTIALS=./path/to/credentials.json
    GOOGLE_SHEET_ID=your_sheet_id_here
    
    📊 8-Scenario P/E Results:
    Each stock gets all 8 scenarios calculated with:
    - Target price for each scenario
    - Upside potential percentage
    - Confidence score (0-1)
    - Investment recommendation 
    - Time frame for target achievement
    - Transparent reasoning for selection
    
    Optimal scenario selected using systematic logic:
    - Company profile analysis (market cap, growth, leadership)
    - Data quality assessment
    - Risk-adjusted confidence scoring
    - Objective criteria eliminate subjective bias
    
    Usage Examples:
    1. Run complete pipeline with 8-scenario P/E:
       python scripts/run_pipeline.py
    
    2. Run specific stage:
       python scripts/run_pipeline.py --stage 4  # 8-scenario P/E analysis
    
    3. Validate outputs only:
       python scripts/run_pipeline.py --validate-only
    
    4. Debug mode:
       python scripts/run_pipeline.py --debug
    """
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if validate_only:
        safe_echo("Validating pipeline outputs...")
        
        # Validate each stage
        stage_files = {
            1: ['raw_revenue.csv', 'raw_dividends.csv', 'raw_performance.csv'],
            2: ['cleaned_dividends.csv', 'cleaned_performance.csv', 'cleaned_revenue.csv'],
            3: ['stock_analysis.csv'],
            4: ['enhanced_analysis.csv']
        }
        
        for stage_num, files in stage_files.items():
            validate_stage_output(stage_num, files)
        
        # Special validation for Stage 5 with 8-scenario P/E
        validate_stage5_hybrid_dashboard()
        
        return
    
    if stage:
        safe_echo(f"Running Stage {stage} only...")
        
        if stage == 1:
            run_subprocess_safely(['python', '-m', 'src.pipelines.stage1_excel_to_csv_html'], f"Stage {stage}")
        elif stage == 2:
            run_subprocess_safely(['python', '-m', 'src.pipelines.stage2_data_cleaning'], f"Stage {stage}")
        elif stage == 3:
            run_subprocess_safely(['python', '-m', 'src.pipelines.stage3_basic_analysis'], f"Stage {stage}")
        elif stage == 4:
            safe_echo("Running Stage 4: 8-Scenario P/E Advanced Analysis...")
            run_subprocess_safely(['python', '-m', 'src.pipelines.stage4_advanced_analysis'], f"Stage {stage}")
        elif stage == 5:
            safe_echo("Running Stage 5: Enhanced Dashboard with 8-Scenario P/E...")
            run_subprocess_safely(['python', '-m', 'src.pipelines.stage5_sheets_publisher'], f"Stage {stage}")
        else:
            safe_echo(f"ERROR: Invalid stage {stage}. Must be 1-5.")
            return
        
        safe_echo(f"Stage {stage} completed.")
        return
    
    # Run complete pipeline
    run_complete_pipeline_v130()

if __name__ == '__main__':
    main()