# src/pipelines/stage5_sheets_publisher.py
"""
Stage 5 Pipeline: Google Sheets Dashboard Publisher v1.3.0 - HYBRID FORMULA DASHBOARD
✅ NEW v1.3.0: Hybrid approach with real-time formulas for 3 models (Graham, NAV, P/E)
✅ DATA FLOW: Raw Data (6,7,8) → Analysis (4,5) → Dashboard (1,2,3) with live calculations
✅ REAL-TIME: Graham, NAV, P/E calculated live from Basic Analysis + Raw Performance
✅ PRE-CALCULATED: DCF, DDM from Advanced Analysis (too complex for formulas)
✅ LIVE CONSENSUS: Five-model consensus calculated in real-time with proper weights
"""
import pandas as pd
import click
from pathlib import Path
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import time
import logging
import os
import json
import tempfile

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, continue without it

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SheetsPublisher:
    """Google Sheets publisher with hybrid formula dashboard and real-time model calculations"""
    
    def __init__(self, credentials_path: str, sheet_id: str, input_dir: str):
        self.input_dir = Path(input_dir)
        self.sheet_id = sheet_id
        self.credentials_path = credentials_path
        self.temp_credentials_file = None
        self.service = self._authenticate(credentials_path)
        
        # Data directories for v1.3.0
        self.stage1_raw_dir = self.input_dir.parent / 'stage1_raw'
        self.stage2_cleaned_dir = self.input_dir.parent / 'stage2_cleaned'
        self.stage3_analysis_dir = self.input_dir.parent / 'stage3_analysis'
        self.stage4_enhanced_dir = self.input_dir  # Current input_dir is stage4_enhanced
        
        # Model calculation weights for v1.3.0 hybrid approach
        self.model_weights = {
            'dcf': 0.30,      # Pre-calculated (complex)
            'graham': 0.15,   # Real-time formula (simple)
            'nav': 0.20,      # Real-time formula (moderate)
            'pe': 0.25,       # Real-time formula (moderate)
            'ddm': 0.10       # Pre-calculated (complex)
        }
    
    def _authenticate(self, credentials_path: str):
        """Authenticate with Google Sheets API - handles both file paths and JSON content"""
        try:
            # Check if credentials_path is actually JSON content
            if credentials_path.strip().startswith('{'):
                # It's JSON content - create temporary file
                try:
                    # Validate JSON
                    credentials_data = json.loads(credentials_path)
                    
                    # Create temporary credentials file
                    self.temp_credentials_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                    self.temp_credentials_file.write(credentials_path)
                    self.temp_credentials_file.close()
                    
                    logger.info("Using credentials from JSON content (temporary file created)")
                    credentials_path = self.temp_credentials_file.name
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in credentials: {e}")
                    raise
                except Exception as e:
                    logger.error(f"Could not create temporary credentials file: {e}")
                    raise
            
            # Authenticate using file path
            credentials = Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            logger.info(f"Successfully authenticated with Google Sheets API")
            return build('sheets', 'v4', credentials=credentials)
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def cleanup_temp_file(self):
        """Clean up temporary credentials file if it was created"""
        if self.temp_credentials_file:
            try:
                os.unlink(self.temp_credentials_file.name)
                logger.debug("Cleaned up temporary credentials file")
            except:
                pass
    
    def _update_range(self, range_name: str, values: list, value_input_option: str = 'RAW'):
        """Update a range in the spreadsheet"""
        body = {'values': values}
        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body
        ).execute()
        return result
    
    def load_company_name_lookup(self):
        """Create a lookup table for stock_code -> company_name from raw data"""
        lookup = {}
        
        # Try to get company names from raw data files
        raw_files = [
            self.stage1_raw_dir / 'raw_dividends.csv',
            self.stage1_raw_dir / 'raw_performance.csv', 
            self.stage1_raw_dir / 'raw_revenue.csv'
        ]
        
        for raw_file in raw_files:
            if raw_file.exists():
                try:
                    df = pd.read_csv(raw_file)
                    if 'stock_code' in df.columns and 'company_name' in df.columns:
                        # Create lookup from this file
                        file_lookup = df[['stock_code', 'company_name']].drop_duplicates()
                        for _, row in file_lookup.iterrows():
                            if pd.notna(row['company_name']) and str(row['company_name']).strip():
                                lookup[str(row['stock_code'])] = str(row['company_name'])
                except Exception as e:
                    logger.warning(f"Could not load company names from {raw_file}: {e}")
        
        logger.info(f"Loaded {len(lookup)} company name mappings from raw data")
        return lookup
    
    def ensure_company_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all rows have company names, using lookup if needed"""
        
        # Check if company_name column exists and has data
        if 'company_name' not in df.columns:
            logger.info("Adding missing company_name column...")
            df['company_name'] = ''
        
        # Count missing company names
        missing_count = df['company_name'].isna().sum() + (df['company_name'] == '').sum()
        
        if missing_count > 0:
            logger.info(f"Found {missing_count} rows with missing company names, attempting lookup...")
            
            # Load company name lookup
            lookup = self.load_company_name_lookup()
            
            # Fill missing company names
            for idx, row in df.iterrows():
                if pd.isna(row['company_name']) or str(row['company_name']).strip() == '':
                    stock_code = str(row['stock_code'])
                    if stock_code in lookup:
                        df.at[idx, 'company_name'] = lookup[stock_code]
                        logger.debug(f"Filled company name for {stock_code}: {lookup[stock_code]}")
                    else:
                        # Fallback to stock code
                        df.at[idx, 'company_name'] = stock_code
        
        # Final check
        final_missing = df['company_name'].isna().sum() + (df['company_name'] == '').sum()
        if final_missing > 0:
            logger.warning(f"Still have {final_missing} rows with missing company names after lookup")
        else:
            logger.info("✅ All rows now have company names")
        
        return df
    
    def create_required_tabs(self):
        """Create all required dashboard tabs for v1.3.0 (10 tabs total)"""
        logger.info("📋 Creating dashboard tabs for v1.3.0 (10 tabs total with hybrid formulas)...")
        
        # Get existing sheets
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        existing_sheets = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
        
        # v1.3.0 - All 10 required tabs in dependency order
        required_tabs = [
            # Raw Data Tabs (6, 7, 8) - No dependencies
            'Raw Revenue Data',
            'Raw Dividends Data',
            'Raw Performance Data',
            
            # Analysis Tabs (4, 5) - Depend on raw data
            'Basic Analysis',
            'Advanced Analysis',
            
            # Dashboard Tabs (1, 2, 3) - Hybrid formulas from analysis + raw data
            'Current Snapshot',
            'Top Picks', 
            'Single Pick',
            
            # Meta Tabs
            'Summary',
            'Last Updated'
        ]
        
        requests = []
        for tab_name in required_tabs:
            if tab_name not in existing_sheets:
                requests.append({
                    'addSheet': {
                        'properties': {
                            'title': tab_name
                        }
                    }
                })
                logger.info(f"   ➕ Will create: {tab_name}")
        
        if requests:
            body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()
            logger.info(f"✅ Created {len(requests)} new tabs")
            time.sleep(2)  # Wait for tab creation
        else:
            logger.info("✅ All 10 required tabs already exist")
    
    # =============================================
    # RAW DATA TABS (6, 7, 8) - CSV UPLOADS (unchanged)
    # =============================================
    
    def create_raw_revenue_tab(self):
        """Tab 6: Create Raw Revenue Data tab from Stage 1 output"""
        logger.info("📊 Creating Tab 6: Raw Revenue Data (CSV upload)...")
        
        raw_revenue_file = self.stage1_raw_dir / 'raw_revenue.csv'
        if not raw_revenue_file.exists():
            logger.warning(f"Raw revenue file not found: {raw_revenue_file}")
            placeholder_data = [
                ['Raw Revenue Data - Not Available', ''],
                ['', ''],
                ['File not found:', str(raw_revenue_file)],
                ['Status:', 'Run Stage 1 to generate raw revenue data'],
                ['Expected columns:', '22 columns including monthly revenue data from GoodInfo'],
                ['Data source:', 'ShowSaleMonChart Excel files']
            ]
            self._update_range('Raw Revenue Data!A1', placeholder_data, 'RAW')
            return
        
        try:
            # Load raw revenue data
            df = pd.read_csv(raw_revenue_file)
            logger.info(f"Loaded raw revenue data: {len(df)} rows, {len(df.columns)} columns")
            
            # Prepare data for sheets (headers + data)
            headers = list(df.columns)
            data_rows = []
            
            # Convert DataFrame to list of lists
            for _, row in df.iterrows():
                data_row = []
                for col in headers:
                    value = row[col]
                    if pd.isna(value):
                        data_row.append('')
                    else:
                        data_row.append(str(value))
                data_rows.append(data_row)
            
            # Combine headers and data
            sheet_data = [headers] + data_rows
            
            # Update sheet
            self._update_range('Raw Revenue Data!A1', sheet_data, 'RAW')
            
            logger.info(f"✅ Tab 6: Raw Revenue Data created: {len(data_rows)} rows, {len(headers)} columns")
            
        except Exception as e:
            logger.error(f"Error creating Raw Revenue Data tab: {e}")
            # Create error placeholder
            error_data = [
                ['Raw Revenue Data - Error', ''],
                ['', ''],
                ['Error loading file:', str(raw_revenue_file)],
                ['Error message:', str(e)],
                ['Status:', 'Check Stage 1 output and file format']
            ]
            self._update_range('Raw Revenue Data!A1', error_data, 'RAW')
    
    def create_raw_dividends_tab(self):
        """Tab 7: Create Raw Dividends Data tab from Stage 1 output"""
        logger.info("💰 Creating Tab 7: Raw Dividends Data (CSV upload)...")
        
        raw_dividends_file = self.stage1_raw_dir / 'raw_dividends.csv'
        if not raw_dividends_file.exists():
            logger.warning(f"Raw dividends file not found: {raw_dividends_file}")
            placeholder_data = [
                ['Raw Dividends Data - Not Available', ''],
                ['', ''],
                ['File not found:', str(raw_dividends_file)],
                ['Status:', 'Run Stage 1 to generate raw dividends data'],
                ['Expected columns:', '25 columns including dividend history from GoodInfo'],
                ['Data source:', 'DividendDetail Excel files'],
                ['Note:', 'Quarterly L-rows filtered out in processing']
            ]
            self._update_range('Raw Dividends Data!A1', placeholder_data, 'RAW')
            return
        
        try:
            # Load raw dividends data
            df = pd.read_csv(raw_dividends_file)
            logger.info(f"Loaded raw dividends data: {len(df)} rows, {len(df.columns)} columns")
            
            # Prepare data for sheets
            headers = list(df.columns)
            data_rows = []
            
            for _, row in df.iterrows():
                data_row = []
                for col in headers:
                    value = row[col]
                    if pd.isna(value):
                        data_row.append('')
                    else:
                        data_row.append(str(value))
                data_rows.append(data_row)
            
            sheet_data = [headers] + data_rows
            self._update_range('Raw Dividends Data!A1', sheet_data, 'RAW')
            
            logger.info(f"✅ Tab 7: Raw Dividends Data created: {len(data_rows)} rows, {len(headers)} columns")
            
        except Exception as e:
            logger.error(f"Error creating Raw Dividends Data tab: {e}")
            error_data = [
                ['Raw Dividends Data - Error', ''],
                ['', ''],
                ['Error loading file:', str(raw_dividends_file)],
                ['Error message:', str(e)],
                ['Status:', 'Check Stage 1 output and file format']
            ]
            self._update_range('Raw Dividends Data!A1', error_data, 'RAW')
    
    def create_raw_performance_tab(self):
        """Tab 8: Create Raw Performance Data tab from Stage 1 output"""
        logger.info("📈 Creating Tab 8: Raw Performance Data (CSV upload)...")
        
        raw_performance_file = self.stage1_raw_dir / 'raw_performance.csv'
        if not raw_performance_file.exists():
            logger.warning(f"Raw performance file not found: {raw_performance_file}")
            placeholder_data = [
                ['Raw Performance Data - Not Available', ''],
                ['', ''],
                ['File not found:', str(raw_performance_file)],
                ['Status:', 'Run Stage 1 to generate raw performance data'],
                ['Expected columns:', '24 columns including financial performance from GoodInfo'],
                ['Data source:', 'StockBzPerformance Excel files'],
                ['Key data:', 'ROE, ROA, EPS, BPS for NAV calculations']
            ]
            self._update_range('Raw Performance Data!A1', placeholder_data, 'RAW')
            return
        
        try:
            # Load raw performance data
            df = pd.read_csv(raw_performance_file)
            logger.info(f"Loaded raw performance data: {len(df)} rows, {len(df.columns)} columns")
            
            # Prepare data for sheets
            headers = list(df.columns)
            data_rows = []
            
            for _, row in df.iterrows():
                data_row = []
                for col in headers:
                    value = row[col]
                    if pd.isna(value):
                        data_row.append('')
                    else:
                        data_row.append(str(value))
                data_rows.append(data_row)
            
            sheet_data = [headers] + data_rows
            self._update_range('Raw Performance Data!A1', sheet_data, 'RAW')
            
            logger.info(f"✅ Tab 8: Raw Performance Data created: {len(data_rows)} rows, {len(headers)} columns")
            
        except Exception as e:
            logger.error(f"Error creating Raw Performance Data tab: {e}")
            error_data = [
                ['Raw Performance Data - Error', ''],
                ['', ''],
                ['Error loading file:', str(raw_performance_file)],
                ['Error message:', str(e)],
                ['Status:', 'Check Stage 1 output and file format']
            ]
            self._update_range('Raw Performance Data!A1', error_data, 'RAW')
    
    # =============================================
    # ANALYSIS TABS (4, 5) - CSV UPLOADS (unchanged)
    # =============================================
    
    def create_basic_analysis_tab(self):
        """Tab 4: Create Basic Analysis tab from Stage 3 output"""
        logger.info("🔍 Creating Tab 4: Basic Analysis (CSV upload - feeds hybrid formulas)...")
        
        basic_analysis_file = self.stage3_analysis_dir / 'stock_analysis.csv'
        if not basic_analysis_file.exists():
            logger.warning(f"Basic analysis file not found: {basic_analysis_file}")
            placeholder_data = [
                ['Basic Analysis - Not Available', ''],
                ['', ''],
                ['File not found:', str(basic_analysis_file)],
                ['Status:', 'Run Stage 3 to generate basic analysis results'],
                ['Data flow:', 'Feeds real-time formulas for Graham, NAV, P/E calculations'],
                ['Expected data:', 'avg_eps, avg_roe, avg_roa, revenue_growth for live valuations'],
                ['Hybrid features:', 'This data feeds live formulas in dashboard tabs']
            ]
            self._update_range('Basic Analysis!A1', placeholder_data, 'RAW')
            return
        
        try:
            # Load basic analysis data
            df = pd.read_csv(basic_analysis_file)
            logger.info(f"Loaded basic analysis data: {len(df)} rows, {len(df.columns)} columns")
            
            # Ensure company names are present
            df = self.ensure_company_names(df)
            
            # Prepare data for sheets
            headers = list(df.columns)
            data_rows = []
            
            for _, row in df.iterrows():
                data_row = []
                for col in headers:
                    value = row[col]
                    if pd.isna(value):
                        data_row.append('')
                    elif isinstance(value, float):
                        data_row.append(round(value, 4))  # Preserve precision for analysis
                    else:
                        data_row.append(str(value))
                data_rows.append(data_row)
            
            sheet_data = [headers] + data_rows
            self._update_range('Basic Analysis!A1', sheet_data, 'RAW')
            
            logger.info(f"✅ Tab 4: Basic Analysis created: {len(data_rows)} rows, {len(headers)} columns")
            logger.info(f"    🔄 Feeds real-time formulas: Graham (EPS+Growth), NAV (ROE+ROA), P/E (EPS+Growth+ROE)")
            
        except Exception as e:
            logger.error(f"Error creating Basic Analysis tab: {e}")
            error_data = [
                ['Basic Analysis - Error', ''],
                ['', ''],
                ['Error loading file:', str(basic_analysis_file)],
                ['Error message:', str(e)],
                ['Status:', 'Check Stage 3 output and file format']
            ]
            self._update_range('Basic Analysis!A1', error_data, 'RAW')
    
    def number_to_column_letter(n):
        """Convert number to Excel-style column letter (1=A, 2=B, ..., 27=AA, etc.)"""
        result = ""
        while n > 0:
            n -= 1  # Make it 0-based
            result = chr(65 + (n % 26)) + result
            n //= 26
        return result
    
    def create_advanced_analysis_tab(self):
        """Tab 5: Create Advanced Analysis tab - ULTRA SIMPLE fix"""
        logger.info("🎯 Creating Tab 5: Advanced Analysis (CSV upload - no formulas)...")
        
        advanced_analysis_file = self.stage4_enhanced_dir / 'enhanced_analysis.csv'
        if not advanced_analysis_file.exists():
            logger.warning(f"Advanced analysis file not found: {advanced_analysis_file}")
            placeholder_data = [
                ['Advanced Analysis - Not Available', ''],
                ['File not found:', str(advanced_analysis_file)],
                ['Status:', 'Run Stage 4 to generate advanced analysis results'],
                ['Note:', 'Live Graham/NAV/P/E calculations available in Dashboard tabs 1,2,3'],
            ]
            self._update_range('Advanced Analysis!A1', placeholder_data, 'RAW')
            return
        
        try:
            # Load advanced analysis data
            df = pd.read_csv(advanced_analysis_file)
            logger.info(f"Loaded advanced analysis data: {len(df)} rows, {len(df.columns)} columns")
            
            # Ensure company names are present
            df = self.ensure_company_names(df)
            
            # Prepare data for sheets - just upload first 20 columns to avoid range issues
            headers = list(df.columns[:20])  # Take first 20 columns only
            headers.append('Live_Formulas_Location')
            
            data_rows = []
            
            for _, row in df.iterrows():
                data_row = []
                # Only take first 20 columns to avoid column range issues
                for col in df.columns[:20]:
                    value = row[col]
                    if pd.isna(value):
                        data_row.append('')
                    elif isinstance(value, float):
                        data_row.append(round(value, 4))
                    else:
                        data_row.append(str(value))
                
                # Add note about where to find live calculations
                data_row.append('See Dashboard Tabs 1,2,3 for LIVE Graham/NAV/P/E')
                
                data_rows.append(data_row)
            
            sheet_data = [headers] + data_rows
            
            # Use simple range - A1:U with enough columns
            range_name = f'Advanced Analysis!A1:U{len(sheet_data)}'
            
            logger.info(f"Updating range: {range_name}")
            
            # Update sheet with RAW data (safe approach)
            self._update_range(range_name, sheet_data, 'RAW')
            
            logger.info(f"✅ Tab 5: Advanced Analysis created: {len(data_rows)} rows, {len(headers)} columns")
            logger.info(f"    📊 Static data from Stage 4 processing (first 20 columns)")
            logger.info(f"    🔄 LIVE formulas available in Dashboard tabs 1,2,3")
            logger.info(f"    💡 Use Tab 1 for complete analysis with live valuations")
            
        except Exception as e:
            logger.error(f"Error creating Advanced Analysis tab: {e}")
            error_data = [
                ['Advanced Analysis - Error', ''],
                ['Error message:', str(e)],
                ['Status:', 'Dashboard tabs 1,2,3 still work with live formulas!']
            ]
            self._update_range('Advanced Analysis!A1', error_data, 'RAW')

    # =============================================
    # DASHBOARD TABS (1, 2, 3) - HYBRID FORMULAS
    # =============================================
    
    def create_current_snapshot_tab_hybrid_formulas(self):
        """Tab 1: Create Current Snapshot with hybrid real-time formulas"""
        logger.info("📊 Creating Tab 1: Current Snapshot (HYBRID: Live Graham+NAV+P/E, Pre-calc DCF+DDM)...")
        
        # Updated headers to indicate which are live calculations
        headers = [
            'Stock Code', 'Company Name', 'Current Price', 'Quality Score', 
            'DCF Value', 'Graham Value (Live)', 'NAV Value (Live)', 'PE Value (Live)', 'DDM Value',
            'Live Five Model Consensus', 'Original Consensus', 'Live Safety Margin', 'Recommendation',
            'Quality Rank', 'Overall Rank', 'ROE', 'ROA', 'EPS', 'Dividend Yield'
        ]
        
        formula_data = [
            headers,  # Row 1: Headers
            
            # Row 2: First data row with hybrid formulas
            [
                '=INDEX(\'Advanced Analysis\'!A:A,2)',  # Stock Code
                '=INDEX(\'Advanced Analysis\'!B:B,2)',  # Company Name
                '=IFERROR(GOOGLEFINANCE("TPE:"&A2),IFERROR(IMPORTXML("https://tw.stock.yahoo.com/quote/"&A2&".TW/dividend", "/html/body/div[1]/div/div/div/div/div[4]/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/span[1]"),"無法取得"))',  # Current Price
                '=INDEX(\'Advanced Analysis\'!1:1048576,2,MATCH("quality_score",\'Advanced Analysis\'!1:1,0))',  # Quality Score
                '=INDEX(\'Advanced Analysis\'!1:1048576,2,MATCH("dcf_valuation",\'Advanced Analysis\'!1:1,0))',  # DCF Value (pre-calculated)
                
                # Graham Value - REAL-TIME FORMULA: EPS * (8.5 + 2 * growth_rate)
                '=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * (8.5 + 2 * MIN(MAX(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0)),5),25))',
                
                # NAV Value - REAL-TIME FORMULA: BPS * ROE_quality_multiplier * ROA_efficiency_multiplier
                '=INDEX(\'Raw Performance Data\'!1:1048576,MATCH(A2,\'Raw Performance Data\'!A:A,0),MATCH("BPS(元)",\'Raw Performance Data\'!1:1,0)) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.4,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=15,1.3,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=10,1.1,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=5,1.0,0.8)))) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roa",\'Basic Analysis\'!1:1,0))>=8,1.1,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roa",\'Basic Analysis\'!1:1,0))>=5,1.0,0.95))',
                
                # P/E Value - REAL-TIME FORMULA: EPS * 15 * growth_multiplier * quality_multiplier * risk_multiplier
                '=MAX(MIN(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * 15 * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=25,1.6,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=15,1.4,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=10,1.2,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=5,1.1,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=0,1.0,0.8))))) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=25,1.4,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.3,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=15,1.2,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=10,1.0,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=5,0.9,0.7))))) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("revenue_volatility",\'Basic Analysis\'!1:1,0))<=5,1.1,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("revenue_volatility",\'Basic Analysis\'!1:1,0))<=15,1.0,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("revenue_volatility",\'Basic Analysis\'!1:1,0))<=25,0.95,0.9))),INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0))*40),INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0))*6)',
                
                '=INDEX(\'Advanced Analysis\'!1:1048576,2,MATCH("ddm_valuation",\'Advanced Analysis\'!1:1,0))',  # DDM Value (pre-calculated)
                
                # Live Five Model Consensus - REAL-TIME FORMULA with proper weights
                f'=ROUND((E2*{self.model_weights["dcf"]} + F2*{self.model_weights["graham"]} + G2*{self.model_weights["nav"]} + H2*{self.model_weights["pe"]} + I2*{self.model_weights["ddm"]}),2)',
                
                '=INDEX(\'Advanced Analysis\'!1:1048576,2,MATCH("original_consensus",\'Advanced Analysis\'!1:1,0))',  # Original Consensus
                
                # Live Safety Margin - REAL-TIME FORMULA
                '=IF(AND(ISNUMBER(J2),ISNUMBER(C2),C2>0),ROUND((J2-C2)/C2,3),0)',
                
                '=INDEX(\'Advanced Analysis\'!1:1048576,2,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))',  # Recommendation
                '=INDEX(\'Advanced Analysis\'!1:1048576,2,MATCH("quality_rank",\'Advanced Analysis\'!1:1,0))',  # Quality Rank
                '=INDEX(\'Advanced Analysis\'!1:1048576,2,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0))',  # Overall Rank
                '=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))',  # ROE
                '=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_roa",\'Basic Analysis\'!1:1,0))',  # ROA
                '=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0))',  # EPS
                '=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A2,\'Basic Analysis\'!A:A,0),MATCH("avg_dividend_yield",\'Basic Analysis\'!1:1,0))'  # Dividend Yield
            ]
        ]
        
        # Add formula rows for additional stocks (up to 30 stocks)
        for row_num in range(3, 32):  # Rows 3-31 (29 more stocks)
            formula_row = [
                f'=INDEX(\'Advanced Analysis\'!A:A,{row_num})',  # Stock Code
                f'=INDEX(\'Advanced Analysis\'!B:B,{row_num})',  # Company Name  
                f'=IFERROR(GOOGLEFINANCE("TPE:"&A{row_num}),IFERROR(IMPORTXML("https://tw.stock.yahoo.com/quote/"&A{row_num}&".TW/dividend", "/html/body/div[1]/div/div/div/div/div[4]/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/span[1]"),"無法取得"))',  # Current Price
                f'=INDEX(\'Advanced Analysis\'!1:1048576,{row_num},MATCH("quality_score",\'Advanced Analysis\'!1:1,0))',  # Quality Score
                f'=INDEX(\'Advanced Analysis\'!1:1048576,{row_num},MATCH("dcf_valuation",\'Advanced Analysis\'!1:1,0))',  # DCF Value
                
                # Graham Value - REAL-TIME FORMULA
                f'=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * (8.5 + 2 * MIN(MAX(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0)),5),25))',
                
                # NAV Value - REAL-TIME FORMULA (simplified for readability)
                f'=INDEX(\'Raw Performance Data\'!1:1048576,MATCH(A{row_num},\'Raw Performance Data\'!A:A,0),MATCH("BPS(元)",\'Raw Performance Data\'!1:1,0)) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.4,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=15,1.3,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=10,1.1,1.0)))',
                
                # P/E Value - REAL-TIME FORMULA (simplified)
                f'=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * 15 * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=15,1.4,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=10,1.2,1.0)) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.3,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=15,1.2,1.0))',
                
                f'=INDEX(\'Advanced Analysis\'!1:1048576,{row_num},MATCH("ddm_valuation",\'Advanced Analysis\'!1:1,0))',  # DDM Value
                
                # Live Five Model Consensus
                f'=ROUND((E{row_num}*{self.model_weights["dcf"]} + F{row_num}*{self.model_weights["graham"]} + G{row_num}*{self.model_weights["nav"]} + H{row_num}*{self.model_weights["pe"]} + I{row_num}*{self.model_weights["ddm"]}),2)',
                
                f'=INDEX(\'Advanced Analysis\'!1:1048576,{row_num},MATCH("original_consensus",\'Advanced Analysis\'!1:1,0))',  # Original Consensus
                
                # Live Safety Margin
                f'=IF(AND(ISNUMBER(J{row_num}),ISNUMBER(C{row_num}),C{row_num}>0),ROUND((J{row_num}-C{row_num})/C{row_num},3),0)',
                
                f'=INDEX(\'Advanced Analysis\'!1:1048576,{row_num},MATCH("recommendation",\'Advanced Analysis\'!1:1,0))',  # Recommendation
                f'=INDEX(\'Advanced Analysis\'!1:1048576,{row_num},MATCH("quality_rank",\'Advanced Analysis\'!1:1,0))',  # Quality Rank
                f'=INDEX(\'Advanced Analysis\'!1:1048576,{row_num},MATCH("overall_rank",\'Advanced Analysis\'!1:1,0))',  # Overall Rank
                f'=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))',  # ROE
                f'=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_roa",\'Basic Analysis\'!1:1,0))',  # ROA
                f'=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0))',  # EPS
                f'=INDEX(\'Basic Analysis\'!1:1048576,MATCH(A{row_num},\'Basic Analysis\'!A:A,0),MATCH("avg_dividend_yield",\'Basic Analysis\'!1:1,0))'  # Dividend Yield
            ]
            formula_data.append(formula_row)
        
        # Update sheet with hybrid formulas
        range_end = f'S{len(formula_data)}'
        self._update_range(f'Current Snapshot!A1:{range_end}', formula_data, 'USER_ENTERED')
        
        logger.info("✅ Tab 1: Current Snapshot created with HYBRID FORMULAS")
        logger.info("    📊 REAL-TIME: Graham, NAV, P/E values calculated live from Basic Analysis")
        logger.info("    📋 PRE-CALCULATED: DCF, DDM values from Advanced Analysis")
        logger.info("    💹 LIVE: Five Model Consensus + Safety Margin update automatically")
        logger.info("    🔄 Auto-updates when Basic Analysis or Raw Performance data changes")
    
    def create_top_picks_tab_hybrid_formulas(self):
        """Tab 2: Create Top Picks with hybrid real-time formulas"""
        logger.info("⭐ Creating Tab 2: Top Picks (HYBRID: Live valuations with real-time ranking)...")
        
        headers = [
            'Rank', 'Stock Code', 'Company Name', 'Current Price', 'Recommendation', 'Quality Score', 
            'Live Safety Margin', 'Live Five Model Consensus', 'Graham (Live)', 'NAV (Live)', 'PE (Live)', 'Key Strengths'
        ]
        
        formula_data = [
            headers,  # Row 1: Clean headers
            
            # Row 2: Top ranked stock with hybrid formulas
            ['1',  # Rank
             '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),1,1)',  # Stock Code (sorted by overall_rank)
             '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),1,2)',  # Company Name
             '=IFERROR(GOOGLEFINANCE("TPE:"&B2),IFERROR(IMPORTXML("https://tw.stock.yahoo.com/quote/"&B2&".TW/dividend", "/html/body/div[1]/div/div/div/div/div[4]/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/span[1]"),"無法取得"))',  # Current Price
             '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),1,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))',  # Recommendation
             '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),1,MATCH("quality_score",\'Advanced Analysis\'!1:1,0))',  # Quality Score
             
             # Live Safety Margin - calculated from live consensus and current price
             '=IF(AND(ISNUMBER(H2),ISNUMBER(D2),D2>0),ROUND((H2-D2)/D2,3),0)',
             
             # Live Five Model Consensus - real-time calculation
             f'=ROUND((INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),1,MATCH("dcf_valuation",\'Advanced Analysis\'!1:1,0))*{self.model_weights["dcf"]} + I2*{self.model_weights["graham"]} + J2*{self.model_weights["nav"]} + K2*{self.model_weights["pe"]} + INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),1,MATCH("ddm_valuation",\'Advanced Analysis\'!1:1,0))*{self.model_weights["ddm"]}),2)',
             
             # Graham Value - REAL-TIME FORMULA
             '=INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * (8.5 + 2 * MIN(MAX(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0)),5),25))',
             
             # NAV Value - REAL-TIME FORMULA  
             '=INDEX(\'Raw Performance Data\'!1:1048576,MATCH(B2,\'Raw Performance Data\'!A:A,0),MATCH("BPS(元)",\'Raw Performance Data\'!1:1,0)) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.4,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=15,1.3,1.0))',
             
             # P/E Value - REAL-TIME FORMULA
             '=INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * 15 * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=15,1.4,1.0) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.3,1.0)',
             
             '=IF(F2>=7,"High Quality + Live Models",IF(F2>=5,"Good Quality + Live Models","Review + Live Models"))'  # Key Strengths
            ]
        ]
        
        # Add more rows for top 20 picks with hybrid formulas
        for i in range(2, 21):  # Ranks 2-20
            formula_data.append([
                str(i),  # Rank
                f'=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),{i},1)',  # Stock Code
                f'=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),{i},2)',  # Company Name
                f'=IFERROR(GOOGLEFINANCE("TPE:"&B{i+1}),IFERROR(IMPORTXML("https://tw.stock.yahoo.com/quote/"&B{i+1}&".TW/dividend", "/html/body/div[1]/div/div/div/div/div[4]/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/span[1]"),"無法取得"))',  # Current Price
                f'=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),{i},MATCH("recommendation",\'Advanced Analysis\'!1:1,0))',  # Recommendation
                f'=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),{i},MATCH("quality_score",\'Advanced Analysis\'!1:1,0))',  # Quality Score
                
                # Live Safety Margin
                f'=IF(AND(ISNUMBER(H{i+1}),ISNUMBER(D{i+1}),D{i+1}>0),ROUND((H{i+1}-D{i+1})/D{i+1},3),0)',
                
                # Live Five Model Consensus
                f'=ROUND((INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),{i},MATCH("dcf_valuation",\'Advanced Analysis\'!1:1,0))*{self.model_weights["dcf"]} + I{i+1}*{self.model_weights["graham"]} + J{i+1}*{self.model_weights["nav"]} + K{i+1}*{self.model_weights["pe"]} + INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),{i},MATCH("ddm_valuation",\'Advanced Analysis\'!1:1,0))*{self.model_weights["ddm"]}),2)',
                
                # Graham Value - REAL-TIME
                f'=INDEX(\'Basic Analysis\'!1:1048576,MATCH(B{i+1},\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * (8.5 + 2 * MIN(MAX(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B{i+1},\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0)),5),25))',
                
                # NAV Value - REAL-TIME
                f'=INDEX(\'Raw Performance Data\'!1:1048576,MATCH(B{i+1},\'Raw Performance Data\'!A:A,0),MATCH("BPS(元)",\'Raw Performance Data\'!1:1,0)) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B{i+1},\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.4,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B{i+1},\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=15,1.3,1.0))',
                
                # P/E Value - REAL-TIME
                f'=INDEX(\'Basic Analysis\'!1:1048576,MATCH(B{i+1},\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * 15 * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B{i+1},\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=15,1.4,1.0) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B{i+1},\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.3,1.0)',
                
                f'=IF(F{i+1}>=7,"High Quality + Live Models",IF(F{i+1}>=5,"Good Quality + Live Models","Review + Live Models"))'  # Key Strengths
            ])
        
        # Update sheet with hybrid formulas
        range_end = f'L{len(formula_data)}'
        self._update_range(f'Top Picks!A1:{range_end}', formula_data, 'USER_ENTERED')
        
        logger.info("✅ Tab 2: Top Picks created with HYBRID FORMULAS")
        logger.info("    🏆 REAL-TIME: Graham, NAV, P/E values + Live Consensus + Live Safety Margin")
        logger.info("    📊 PRE-CALCULATED: DCF, DDM from Advanced Analysis")
        logger.info("    🔄 Live updates when Basic Analysis data changes")
    
    def create_single_pick_tab_hybrid_formulas(self):
        """Tab 3: Create Single Pick with hybrid formulas and interactive weight adjustment"""
        logger.info("🔍 Creating Tab 3: Single Pick (HYBRID: Interactive live calculations + custom weights)...")
        
        # Enhanced single pick layout with hybrid calculations and interactive weights
        single_pick_data = [
            # Row 1: Main headers
            ['🔍 單股分析 v1.3.0 HYBRID', '輸入股票代號', '五模型即時計算', '自訂權重調整', '成長股策略', '價值股策略', '配息股策略', '平衡股策略'],
            
            # Row 2: Input and weight headers
            ['股票代號', '=INDEX(\'Advanced Analysis\'!A:A,2)', '即時計算模型', 'DCF權重(%)', '50%', '20%', '15%', '30%'],
            
            # Row 3: Company name and strategy selection
            ['公司名稱', '=IFERROR(INDEX(\'Advanced Analysis\'!B:B,MATCH(B2,\'Advanced Analysis\'!A:A,0)),"查無此股票")', '即時計算模型', 'Graham權重(%)', '5%', '25%', '15%', '15%'],
            
            # Row 4: Current price (real-time)
            ['現價', '=IFERROR(GOOGLEFINANCE("TPE:"&B2),IFERROR(IMPORTXML("https://tw.stock.yahoo.com/quote/"&B2&".TW/dividend", "/html/body/div[1]/div/div/div/div/div[4]/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/span[1]"),"無法取得"))', '即時計算模型', 'NAV權重(%)', '10%', '30%', '20%', '20%'],
            
            # Row 5: Investment recommendation
            ['投資建議', '=IFERROR(INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("recommendation",\'Advanced Analysis\'!1:1,0)),"N/A")', '即時計算模型', 'P/E權重(%)', '30%', '20%', '25%', '25%'],
            
            # Row 6: Quality score
            ['品質評分', '=IFERROR(INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("quality_score",\'Advanced Analysis\'!1:1,0)),0)', '預設權重', 'DDM權重(%)', '5%', '5%', '25%', '10%'],
            
            # Row 7: Overall rank
            ['整體排名', '=IFERROR(INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("overall_rank",\'Advanced Analysis\'!1:1,0)),999)', '', '權重總計', '=E2+E3+E4+E5+E6', '=F2+F3+F4+F5+F6', '=G2+G3+G4+G5+G6', '=H2+H3+H4+H5+H6'],
            
            # Row 8: Space
            ['', '', '', '', '', '', '', ''],
            
            # Row 9: Model valuations section
            ['📊 五模型估值 (混合)', '', '', '🎯 即時調整後估值', '', '', '', ''],
            
            # Row 10-14: Model valuations with hybrid approach
            ['DCF估值 (預算)', '=IFERROR(INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("dcf_valuation",\'Advanced Analysis\'!1:1,0)),0)', '', '自訂權重共識', '=ROUND((B10*VALUE(SUBSTITUTE(E2,"%",""))/100+B11*VALUE(SUBSTITUTE(E3,"%",""))/100+B12*VALUE(SUBSTITUTE(E4,"%",""))/100+B13*VALUE(SUBSTITUTE(E5,"%",""))/100+B14*VALUE(SUBSTITUTE(E6,"%",""))/100),1)', '', '', ''],
            
            ['Graham估值 (即時)', '=INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * (8.5 + 2 * MIN(MAX(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0)),5),25))', '', 'vs預設五模型', '=IF(AND(ISNUMBER(E10),ISNUMBER(INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("five_model_consensus",\'Advanced Analysis\'!1:1,0)))),ROUND((E10-INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("five_model_consensus",\'Advanced Analysis\'!1:1,0)))/INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("five_model_consensus",\'Advanced Analysis\'!1:1,0))*100,1)&"%","N/A")', '', '', ''],
            
            ['NAV估值 (即時)', '=INDEX(\'Raw Performance Data\'!1:1048576,MATCH(B2,\'Raw Performance Data\'!A:A,0),MATCH("BPS(元)",\'Raw Performance Data\'!1:1,0)) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.4,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=15,1.3,IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=10,1.1,1.0)))', '', 'vs現價差異', '=IF(AND(ISNUMBER(E10),ISNUMBER(B4),B4>0),ROUND((E10-B4)/B4*100,1)&"%","N/A")', '', '', ''],
            
            ['P/E估值 (即時)', '=INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)) * 15 * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0))>=15,1.4,1.0) * IF(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0))>=20,1.3,1.0)', '', '安全邊際', '=IF(AND(ISNUMBER(E10),ISNUMBER(B4),B4>0),ROUND((E10-B4)/B4,3),"N/A")', '', '', ''],
            
            ['DDM估值 (預算)', '=IFERROR(INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("ddm_valuation",\'Advanced Analysis\'!1:1,0)),0)', '', '投資風險', '=IF(B5="Strong Buy","低風險 (即時計算)",IF(B5="Buy","中等風險 (即時計算)","高風險 (即時計算)"))', '', '', ''],
            
            # Row 15-19: Consensus and financial metrics
            ['預設五模型共識', '=IFERROR(INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("five_model_consensus",\'Advanced Analysis\'!1:1,0)),0)', '', '📈 即時財務指標', '', '', '', ''],
            
            ['原始共識', '=IFERROR(INDEX(\'Advanced Analysis\'!1:1048576,MATCH(B2,\'Advanced Analysis\'!A:A,0),MATCH("original_consensus",\'Advanced Analysis\'!1:1,0)),0)', '', 'ROE(%) 即時', '=IFERROR(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_roe",\'Basic Analysis\'!1:1,0)),0)', '', '', ''],
            
            ['EPS(元) 即時', '=IFERROR(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_eps",\'Basic Analysis\'!1:1,0)),0)', '', 'ROA(%) 即時', '=IFERROR(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_roa",\'Basic Analysis\'!1:1,0)),0)', '', '', ''],
            
            ['股息殖利率(%) 即時', '=IFERROR(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("avg_dividend_yield",\'Basic Analysis\'!1:1,0)),0)', '', '營收成長(%) 即時', '=IFERROR(INDEX(\'Basic Analysis\'!1:1048576,MATCH(B2,\'Basic Analysis\'!A:A,0),MATCH("revenue_growth",\'Basic Analysis\'!1:1,0)),0)', '', '', ''],
            
            # Row 19: Stock characteristics and recommendation  
            ['股票特性', '=IF(B6>7,"高品質股票 (即時計算)",IF(B6>5,"中等品質 (即時計算)","需謹慎評估 (即時計算)"))', '', '建議配置', '=IF(B5="Strong Buy","5-10% (即時建議)",IF(B5="Buy","3-7% (即時建議)",IF(B5="Hold","1-3% (即時建議)","避免投資 (即時建議)")))', '', '', ''],
            
            # Row 20: Usage note
            ['使用說明 v1.3.0', '在B2輸入股票代號', '', '調整E2-E6權重看即時變化', '即時計算: Graham, NAV, P/E', '預算計算: DCF, DDM', '', '']
        ]
        
        # Write data with USER_ENTERED to execute formulas
        self._update_range('Single Pick!A1:H20', single_pick_data, 'USER_ENTERED')
        
        logger.info("✅ Tab 3: Single Pick created with HYBRID INTERACTIVE FORMULAS")
        logger.info("    🔍 REAL-TIME: Graham, NAV, P/E calculated live from Basic Analysis")
        logger.info("    📊 PRE-CALCULATED: DCF, DDM from Advanced Analysis")
        logger.info("    🎯 INTERACTIVE: Custom weight adjustment in E2-E6 with instant updates")
        logger.info("    💹 LIVE: Current price + instant consensus updates + safety margins")
        logger.info("    🔄 Complete hybrid integration with strategy weight presets")
    
    # =============================================
    # META TABS (SUMMARY & LAST UPDATED) - Updated for v1.3.0
    # =============================================
    
    def create_summary_tab_hybrid_formulas(self):
        """Create Summary tab with hybrid formula information"""
        logger.info("📈 Creating Summary tab (hybrid formula approach for v1.3.0)...")
        
        # Enhanced summary with hybrid model information
        summary_data = [
            ['Investment Summary Dashboard v1.3.0 HYBRID', ''],
            ['', ''],
            ['📊 Analysis Overview', ''],
            ['Total Stocks Analyzed', '=COUNTA(\'Advanced Analysis\'!A:A)-1'],  # Count rows minus header
            ['Average Quality Score', '=ROUND(AVERAGE(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("quality_score",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("quality_score",\'Advanced Analysis\'!1:1,0)))),1)'],
            ['Average Hybrid Consensus', '=ROUND(AVERAGE(\'Current Snapshot\'!J:J),1)'],  # Live consensus from Current Snapshot
            ['', ''],
            ['📈 Recommendation Breakdown', ''],
            ['Strong Buy', '=COUNTIF(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))),"Strong Buy")'],
            ['Buy', '=COUNTIF(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))),"Buy")'],
            ['Hold', '=COUNTIF(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))),"Hold")'],
            ['Weak Hold', '=COUNTIF(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))),"Weak Hold")'],
            ['Avoid', '=COUNTIF(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("recommendation",\'Advanced Analysis\'!1:1,0))),"Avoid")'],
            ['', ''],
            ['🏆 Top 5 Stocks (Live Rankings)', ''],
            ['Rank', 'Stock Code', 'Company Name', 'Hybrid Consensus'],
            ['1', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),1,1)', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),1,2)', '=INDEX(\'Current Snapshot\'!J:J,2)'],
            ['2', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),2,1)', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),2,2)', '=INDEX(\'Current Snapshot\'!J:J,3)'],
            ['3', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),3,1)', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),3,2)', '=INDEX(\'Current Snapshot\'!J:J,4)'],
            ['4', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),4,1)', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),4,2)', '=INDEX(\'Current Snapshot\'!J:J,5)'],
            ['5', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),5,1)', '=INDEX(SORT(\'Advanced Analysis\'!A:ZZ,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0),TRUE),5,2)', '=INDEX(\'Current Snapshot\'!J:J,6)'],
            ['', ''],
            ['📊 Hybrid Model Valuations (Live + Pre-calc)', ''],
            ['DCF Average (Pre-calculated)', '=ROUND(AVERAGE(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("dcf_valuation",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("dcf_valuation",\'Advanced Analysis\'!1:1,0)))),1)'],
            ['Graham Average (LIVE)', '=ROUND(AVERAGE(\'Current Snapshot\'!F:F),1)'],  # Live Graham values
            ['NAV Average (LIVE)', '=ROUND(AVERAGE(\'Current Snapshot\'!G:G),1)'],      # Live NAV values
            ['P/E Average (LIVE)', '=ROUND(AVERAGE(\'Current Snapshot\'!H:H),1)'],       # Live P/E values
            ['DDM Average (Pre-calculated)', '=ROUND(AVERAGE(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("ddm_valuation",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("ddm_valuation",\'Advanced Analysis\'!1:1,0)))),1)'],
            ['Hybrid Consensus Average (LIVE)', '=ROUND(AVERAGE(\'Current Snapshot\'!J:J),1)'],  # Live consensus
            ['', ''],
            ['💰 Live Financial Metrics', ''],
            ['Average Live Safety Margin', '=ROUND(AVERAGE(\'Current Snapshot\'!L:L),3)'],  # Live safety margins
            ['Average Quality Rank', '=ROUND(AVERAGE(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("quality_rank",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("quality_rank",\'Advanced Analysis\'!1:1,0)))),1)'],
            ['Average Overall Rank', '=ROUND(AVERAGE(INDIRECT("\'Advanced Analysis\'!"&ADDRESS(2,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0))&":"&ADDRESS(1000,MATCH("overall_rank",\'Advanced Analysis\'!1:1,0)))),1)'],
            ['', ''],
            ['🔄 v1.3.0 Hybrid Features', ''],
            ['Real-time Models', 'Graham, NAV, P/E (calculated live from Basic Analysis)'],
            ['Pre-calculated Models', 'DCF, DDM (complex calculations from Advanced Analysis)'],
            ['Live Consensus', 'Five-model weighted average updates automatically'],
            ['Interactive Weights', 'Custom model weights in Single Pick tab'],
            ['Live Price Integration', 'GOOGLEFINANCE + Yahoo Finance fallback'],
            ['Data Transparency', 'Raw data + analysis stages visible in tabs 4-8'],
        ]
        
        self._update_range('Summary!A1', summary_data, 'USER_ENTERED')
        logger.info(f"✅ Summary tab created with hybrid formula information")
        logger.info(f"    🔄 Shows live averages from hybrid calculations")
        logger.info(f"    📊 Distinguishes between real-time and pre-calculated models")
    
    def create_last_updated_tab(self):
        """Create Last Updated tab with v1.3.0 hybrid system status"""
        logger.info("🕐 Creating Last Updated tab for v1.3.0 HYBRID...")
        
        timestamp_data = [
            ['Stock Analysis System - Status v1.3.0 HYBRID FORMULA DASHBOARD', ''],
            ['', ''],
            ['Last Analysis Run', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['System Version', '1.3.0 - HYBRID FORMULA DASHBOARD'],
            ['Dashboard Type', 'Hybrid: Live formulas + Pre-calculated complex models'],
            ['Data Source', 'GoodInfo.tw + Real-time Price Feeds'],
            ['Analysis Pipeline', '5-Stage Processing with Hybrid Formula Integration'],
            ['Valuation Models', '5 Models: 3 Live (Graham, NAV, P/E) + 2 Pre-calc (DCF, DDM)'],
            ['Dashboard Tabs', '10 Tabs Total with Hybrid Formula Dependencies'],
            ['', ''],
            ['📊 v1.3.0 HYBRID APPROACH:', ''],
            ['Real-time Models (3)', 'Graham, NAV, P/E - calculated live from Basic Analysis'],
            ['├─ Graham Formula', 'EPS * (8.5 + 2 * growth_rate) - live calculation'],
            ['├─ NAV Formula', 'BPS * ROE_quality * ROA_efficiency - live calculation'],
            ['└─ P/E Formula', 'EPS * 15 * growth * quality * risk - live calculation'],
            ['', ''],
            ['Pre-calculated Models (2)', 'DCF, DDM - complex Python calculations'],
            ['├─ DCF Model', '5-year projection + terminal value (too complex for formulas)'],
            ['└─ DDM Model', 'Gordon Growth + sustainability analysis (too complex)'],
            ['', ''],
            ['Live Calculations', 'Real-time updates when source data changes'],
            ['├─ Five Model Consensus', 'Weighted average: DCF(30%) + Graham(15%) + NAV(20%) + PE(25%) + DDM(10%)'],
            ['├─ Safety Margin', '(Consensus - Current Price) / Current Price'],
            ['├─ Current Prices', 'GOOGLEFINANCE + Yahoo Finance fallback'],
            ['└─ Interactive Weights', 'Custom model weights in Single Pick tab'],
            ['', ''],
            ['🔄 Data Flow Architecture v1.3.0:', ''],
            ['Raw Data Tabs (6, 7, 8)', 'CSV uploads from GoodInfo processing'],
            ['├─ Tab 6: Raw Revenue Data', 'Monthly revenue feeds Basic Analysis'],
            ['├─ Tab 7: Raw Dividends Data', 'Dividend history feeds Basic Analysis'],
            ['└─ Tab 8: Raw Performance Data', 'Financial metrics (BPS, ROE, ROA) feed NAV formulas'],
            ['', ''],
            ['Analysis Tabs (4, 5)', 'Calculated analysis results'],
            ['├─ Tab 4: Basic Analysis', 'Feeds live formulas: avg_eps→Graham, avg_roe→NAV, revenue_growth→P/E'],
            ['└─ Tab 5: Advanced Analysis', 'Provides DCF + DDM + quality scores'],
            ['', ''],
            ['Dashboard Tabs (1, 2, 3)', 'Hybrid formulas: live + pre-calculated'],
            ['├─ Tab 1: Current Snapshot', 'All stocks with hybrid valuations + live consensus'],
            ['├─ Tab 2: Top Picks', 'Top 20 with live rankings + hybrid models'],
            ['└─ Tab 3: Single Pick', 'Interactive analysis with custom weight adjustment'],
            ['', ''],
            ['Meta Tabs (Summary, Last Updated)', ''],
            ['├─ Summary', 'Live statistics from hybrid calculations'],
            ['└─ Last Updated', 'System status (this tab)'],
            ['', ''],
            ['🔄 Hybrid Formula Benefits:', ''],
            ['Real-time Updates', 'Graham, NAV, P/E update when Basic Analysis changes'],
            ['Accurate Complex Models', 'DCF, DDM maintain Python calculation accuracy'],
            ['Interactive Consensus', 'Five-model consensus updates with live calculations'],
            ['Live Price Integration', 'Current prices feed live safety margin calculations'],
            ['Custom Weight Support', 'Single Pick tab allows interactive model weighting'],
            ['Data Transparency', 'Formula calculations visible and auditable'],
            ['Performance Optimized', 'Simple formulas for real-time, complex Python for accuracy'],
            ['', ''],
            ['✅ v1.3.0 HYBRID Features Active:', ''],
            ['🗂️ Complete Data Pipeline Visibility', 'Raw → Clean → Basic → Advanced → Hybrid Dashboard'],
            ['🔗 Hybrid Formula Integration', '3 live models + 2 pre-calculated models'],
            ['📊 Raw Data Access', 'Original GoodInfo data in tabs 6,7,8'],
            ['🧮 Analysis Transparency', 'Basic (tab 4) feeds live formulas, Advanced (tab 5) provides complex models'],
            ['📈 Real-time Dashboard', 'Tabs 1,2,3 auto-update via hybrid formulas'],
            ['💹 Live Price Integration', 'GOOGLEFINANCE + Yahoo fallback in all major tabs'],
            ['🎯 Five Valuation Models', '3 Live: Graham, NAV, P/E | 2 Pre-calc: DCF, DDM'],
            ['🔧 Interactive Weight Adjustment', 'Custom model weights in Single Pick tab'],
            ['🔄 Live Consensus Updates', 'Five-model consensus recalculates automatically'],
            ['📊 Live Safety Margins', 'Auto-update with current prices and consensus'],
            ['🚀 Performance Optimized', 'Fast formulas for simple models, Python for complex'],
            ['', ''],
            ['Dashboard URL', f'https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit']
        ]
        
        self._update_range('Last Updated!A1', timestamp_data, 'RAW')
        logger.info(f"✅ Last Updated tab created for v1.3.0 HYBRID formula dashboard")
    
    def run_pipeline(self) -> dict:
        """Run complete hybrid formula sheets publishing pipeline for v1.3.0"""
        
        # Load enhanced analysis for validation
        input_file = self.input_dir / 'enhanced_analysis.csv'
        if not input_file.exists():
            logger.error("❌ No enhanced analysis file found. Run Stage 4 first.")
            return {'error': 'missing_input'}
        
        df = pd.read_csv(input_file)
        
        if df.empty:
            logger.error("❌ Empty enhanced analysis file")
            return {'error': 'empty_input'}
        
        # Ensure all stocks have company names
        df = self.ensure_company_names(df)
        
        logger.info(f"📊 Publishing v1.3.0 HYBRID FORMULA dashboard: {len(df)} stocks with live calculations...")
        logger.info(f"🔗 Hybrid Flow: Raw Data (6,7,8) → Analysis (4,5) → Hybrid Dashboard (1,2,3)")
        logger.info(f"⚡ Live Models: Graham, NAV, P/E | Pre-calc Models: DCF, DDM")
        
        try:
            # Create all required tabs (10 tabs for v1.3.0)
            self.create_required_tabs()
            
            # Create tabs in dependency order
            
            # Step 1: Raw Data Tabs (6, 7, 8) - CSV uploads (no dependencies)
            logger.info("📊 Step 1: Creating Raw Data tabs (6,7,8) - Feed hybrid formulas...")
            self.create_raw_revenue_tab()      # Tab 6
            time.sleep(1)
            
            self.create_raw_dividends_tab()    # Tab 7  
            time.sleep(1)
            
            self.create_raw_performance_tab()  # Tab 8 - Feeds NAV formulas with BPS
            time.sleep(1)
            
            # Step 2: Analysis Tabs (4, 5) - CSV uploads (feed hybrid formulas)
            logger.info("📋 Step 2: Creating Analysis tabs (4,5) - Feed hybrid formulas...")
            self.create_basic_analysis_tab()   # Tab 4: Feeds Graham, NAV, P/E live formulas
            time.sleep(1)
            
            self.create_advanced_analysis_tab() # Tab 5: Provides DCF, DDM for hybrid
            time.sleep(1)
            
            # Step 3: Dashboard Tabs (1, 2, 3) - Hybrid formulas (live + pre-calculated)
            logger.info("🎯 Step 3: Creating Hybrid Dashboard tabs (1,2,3) - Live + Pre-calc...")
            self.create_current_snapshot_tab_hybrid_formulas()  # Tab 1: Hybrid formulas
            time.sleep(1)
            
            self.create_top_picks_tab_hybrid_formulas()         # Tab 2: Hybrid formulas
            time.sleep(1)
            
            self.create_single_pick_tab_hybrid_formulas()       # Tab 3: Interactive hybrid
            time.sleep(1)
            
            # Step 4: Meta Tabs (updated for hybrid)
            logger.info("📈 Step 4: Creating Meta tabs (hybrid-aware)...")
            self.create_summary_tab_hybrid_formulas()  # Summary: hybrid model info
            time.sleep(1)
            
            self.create_last_updated_tab()             # Last Updated: v1.3.0 status
            
            return {
                'status': 'success',
                'total_stocks': len(df),
                'sheets_updated': 10,  # v1.3.0 - 10 tabs total
                'version': 'v1.3.0 - HYBRID FORMULA DASHBOARD',
                'data_flow': 'Raw Data (6,7,8) → Analysis (4,5) → Hybrid Dashboard (1,2,3)',
                'hybrid_approach': 'Live formulas: Graham, NAV, P/E | Pre-calculated: DCF, DDM',
                'model_weights': self.model_weights,
                'live_models': 3,       # Graham, NAV, P/E
                'precalc_models': 2,    # DCF, DDM
                'raw_data_tabs': 3,     # Tabs 6,7,8
                'analysis_tabs': 2,     # Tabs 4,5  
                'dashboard_tabs': 3,    # Tabs 1,2,3
                'meta_tabs': 2,         # Summary, Last Updated
                'features': [
                    'Hybrid formula dashboard with live calculations',
                    'Real-time Graham, NAV, P/E valuations from Basic Analysis',
                    'Pre-calculated DCF, DDM for complex financial modeling', 
                    'Live five-model consensus with automatic updates',
                    'Interactive weight adjustment in Single Pick tab',
                    'Real-time safety margins with current market prices',
                    'Complete data pipeline transparency',
                    'Raw CSV data access (tabs 6,7,8)',
                    'Analysis results access (tabs 4,5)',
                    'Hybrid interactive dashboard (tabs 1,2,3)',
                    'Live price integration with GOOGLEFINANCE + Yahoo fallback',
                    'Environment variable configuration',
                    'No google_key.json dependencies',
                    'Performance optimized: fast formulas + accurate Python calculations',
                    'Formula transparency and auditability'
                ]
            }
        
        except Exception as e:
            logger.error(f"❌ Error publishing v1.3.0 hybrid formula dashboard: {e}")
            return {'error': str(e)}
        
        finally:
            # Always clean up temporary credentials file
            self.cleanup_temp_file()

def get_credentials_from_env():
    """Get credentials and sheet ID from environment variables"""
    
    credentials = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    
    if not credentials:
        click.echo("❌ GOOGLE_SHEETS_CREDENTIALS environment variable not set")
        click.echo("Set it to either:")
        click.echo("  1. Path to JSON file: GOOGLE_SHEETS_CREDENTIALS=/path/to/google_key.json")
        click.echo("  2. JSON content: GOOGLE_SHEETS_CREDENTIALS='{\"type\":\"service_account\",...}'")
        return None, None
    
    if not sheet_id:
        click.echo("❌ GOOGLE_SHEET_ID environment variable not set")
        click.echo("Set it to your Google Sheets ID:")
        click.echo("  GOOGLE_SHEET_ID=1ufQ2BrG_lmUiM7c1agL3kCNs1L4AhZgoNlB4TKgBy0I")
        return None, None
    
    return credentials, sheet_id

@click.command()
@click.option('--credentials', default=None, help='Path to Google Sheets credentials JSON (optional if using env vars)')
@click.option('--sheet-id', default=None, help='Google Sheets ID (optional if using env vars)')
@click.option('--input-dir', default='data/stage4_enhanced')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def run_stage5_hybrid_formulas(credentials: str, sheet_id: str, input_dir: str, debug: bool):
    """
    Run Stage 5: Google Sheets Dashboard Publisher v1.3.0 - HYBRID FORMULA DASHBOARD
    
    🔄 NEW v1.3.0 HYBRID APPROACH:
    ✅ Real-time Models: Graham, NAV, P/E calculated live from Basic Analysis
    ✅ Pre-calculated Models: DCF, DDM from Advanced Analysis (too complex for formulas)
    ✅ Live Consensus: Five-model weighted average updates automatically
    ✅ Interactive Weights: Custom model weights in Single Pick tab
    ✅ Live Safety Margins: Auto-update with current prices and consensus
    
    📊 Model Implementation:
    Live Formulas (3 models):
    - Graham: EPS * (8.5 + 2 * growth_rate) - Weight: 15%
    - NAV: BPS * ROE_quality * ROA_efficiency - Weight: 20%  
    - P/E: EPS * 15 * growth * quality * risk - Weight: 25%
    
    Pre-calculated (2 models):
    - DCF: 5-year projection + terminal value - Weight: 30%
    - DDM: Gordon Growth + sustainability - Weight: 10%
    
    🎯 Benefits:
    - Real-time updates for simple models
    - Accurate complex financial modeling
    - Interactive consensus calculation
    - Live price integration
    - Formula transparency
    - Performance optimized
    
    Usage:
    1. Set environment variables:
       export GOOGLE_SHEETS_CREDENTIALS='...'
       export GOOGLE_SHEET_ID='...'
    
    2. Run: python -m src.pipelines.stage5_sheets_publisher
    """
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        click.echo(f"❌ Input directory not found: {input_dir}")
        return
    
    # Get credentials and sheet ID - prioritize command line, then environment
    final_credentials = credentials
    final_sheet_id = sheet_id
    
    if not final_credentials or not final_sheet_id:
        env_credentials, env_sheet_id = get_credentials_from_env()
        
        if not final_credentials:
            final_credentials = env_credentials
        if not final_sheet_id:
            final_sheet_id = env_sheet_id
    
    if not final_credentials or not final_sheet_id:
        click.echo("\n💡 Setup Help:")
        click.echo("1. Create .env file with:")
        click.echo("   GOOGLE_SHEETS_CREDENTIALS=./google_key.json")
        click.echo("   GOOGLE_SHEET_ID=your_sheet_id")
        click.echo("2. Or use command line flags")
        click.echo("3. See instructions-SAS.md v1.3.0 for detailed setup")
        return
    
    # Validate credentials (if it's a file path)
    if not final_credentials.strip().startswith('{') and not Path(final_credentials).exists():
        click.echo(f"❌ Credentials file not found: {final_credentials}")
        return
    
    click.echo("🔧 v1.3.0 HYBRID FORMULA Configuration:")
    if final_credentials.strip().startswith('{'):
        click.echo("   Credentials: JSON content from environment")
    else:
        click.echo(f"   Credentials: {final_credentials}")
    click.echo(f"   Sheet ID: {final_sheet_id}")
    click.echo(f"   Dashboard Type: Hybrid formulas (3 live + 2 pre-calculated models)")
    
    # Run pipeline
    publisher = SheetsPublisher(final_credentials, final_sheet_id, input_dir)
    result = publisher.run_pipeline()
    
    # Display results
    if 'error' in result:
        click.echo(f"❌ Publishing failed: {result['error']}")
        
        if "403" in str(result['error']):
            click.echo(f"\n🔑 Permission Fix Needed:")
            click.echo(f"1. Open your Google Sheet")
            click.echo(f"2. Click 'Share' button")
            click.echo(f"3. Add this email with Editor permission:")
            click.echo(f"   (check your credentials file for client_email)")
            
    else:
        click.echo(f"\n🎉 v1.3.0 HYBRID FORMULA DASHBOARD PUBLISHED!")
        click.echo(f"📊 Dashboard Type: {result['version']}")
        click.echo(f"🔗 Data Flow: {result['data_flow']}")
        click.echo(f"⚡ Hybrid Approach: {result['hybrid_approach']}")
        click.echo(f"📋 Total Tabs: {result['sheets_updated']}")
        click.echo(f"🏢 Stocks Analyzed: {result['total_stocks']}")
        
        click.echo(f"\n📊 Model Breakdown:")
        click.echo(f"   ⚡ LIVE Models ({result['live_models']}): Graham, NAV, P/E")
        click.echo(f"     - Graham: EPS * (8.5 + 2 * growth) - Weight: {result['model_weights']['graham']*100}%")
        click.echo(f"     - NAV: BPS * ROE_quality * ROA_efficiency - Weight: {result['model_weights']['nav']*100}%")
        click.echo(f"     - P/E: EPS * 15 * adjustments - Weight: {result['model_weights']['pe']*100}%")
        
        click.echo(f"   📊 PRE-CALC Models ({result['precalc_models']}): DCF, DDM")
        click.echo(f"     - DCF: 5-year projection + terminal value - Weight: {result['model_weights']['dcf']*100}%")
        click.echo(f"     - DDM: Gordon Growth + sustainability - Weight: {result['model_weights']['ddm']*100}%")
        
        click.echo(f"\n📊 Tab Breakdown:")
        click.echo(f"   📁 Raw Data Tabs: {result['raw_data_tabs']} (CSV uploads)")
        click.echo(f"     - Tab 6: Raw Revenue Data")
        click.echo(f"     - Tab 7: Raw Dividends Data") 
        click.echo(f"     - Tab 8: Raw Performance Data (feeds NAV formulas)")
        
        click.echo(f"   🧮 Analysis Tabs: {result['analysis_tabs']} (CSV uploads)")
        click.echo(f"     - Tab 4: Basic Analysis (feeds live Graham, NAV, P/E formulas)")
        click.echo(f"     - Tab 5: Advanced Analysis (provides DCF, DDM for hybrid)")
        
        click.echo(f"   🎯 Dashboard Tabs: {result['dashboard_tabs']} (HYBRID FORMULAS)")
        click.echo(f"     - Tab 1: Current Snapshot (hybrid: live + pre-calc models)")
        click.echo(f"     - Tab 2: Top Picks (hybrid: live rankings + models)")
        click.echo(f"     - Tab 3: Single Pick (interactive: custom weights + live updates)")
        
        click.echo(f"   📈 Meta Tabs: {result['meta_tabs']}")
        click.echo(f"     - Summary (live statistics from hybrid calculations)")
        click.echo(f"     - Last Updated (v1.3.0 hybrid system info)")
        
        click.echo(f"\n🚀 v1.3.0 HYBRID FEATURES:")
        for feature in result['features']:
            click.echo(f"   ✅ {feature}")
        
        click.echo(f"\n🔗 Access Your Hybrid Formula Dashboard:")
        click.echo(f"   https://docs.google.com/spreadsheets/d/{final_sheet_id}/edit")
        
        click.echo(f"\n💡 Hybrid Formula Benefits:")
        click.echo(f"   ⚡ Real-time updates: Graham, NAV, P/E recalculate when Basic Analysis changes")
        click.echo(f"   🎯 Interactive consensus: Five-model weighted average updates automatically") 
        click.echo(f"   📊 Accurate complex models: DCF, DDM maintain Python calculation precision")
        click.echo(f"   🔗 Live price integration: Current prices feed live safety margin calculations")
        click.echo(f"   🎛️ Custom weights: Single Pick tab allows interactive model weighting")
        click.echo(f"   👁️ Formula transparency: All calculations visible and auditable")
        click.echo(f"   ⚡ Performance optimized: Fast formulas for real-time, Python for accuracy")
        
        click.echo(f"\n🚀 Next Steps:")
        click.echo(f"   1. Test hybrid formulas by modifying Basic Analysis data")
        click.echo(f"   2. Use Single Pick tab for interactive weight adjustment")
        click.echo(f"   3. Monitor live consensus updates during data changes")
        click.echo(f"   4. Compare live vs pre-calculated model values")
        click.echo(f"   5. Re-run pipeline to update underlying CSV data")

if __name__ == '__main__':
    run_stage5_hybrid_formulas()