# src/pipelines/stage5_sheets_publisher.py
"""
Stage 5 Pipeline: Google Sheets Dashboard Publisher - ENVIRONMENT VARIABLE VERSION
✅ SUPPORTS: Environment variables and .env files
✅ COMPATIBLE: With new run_pipeline.py script
✅ FEATURES: Enhanced credential handling and validation
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
    """Google Sheets publisher with environment variable support"""
    
    def __init__(self, credentials_path: str, sheet_id: str, input_dir: str):
        self.input_dir = Path(input_dir)
        self.sheet_id = sheet_id
        self.credentials_path = credentials_path
        self.temp_credentials_file = None
        self.service = self._authenticate(credentials_path)
    
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
            self.input_dir.parent / 'stage1_raw' / 'raw_dividends.csv',
            self.input_dir.parent / 'stage1_raw' / 'raw_performance.csv', 
            self.input_dir.parent / 'stage1_raw' / 'raw_revenue.csv'
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
        """Create all required dashboard tabs"""
        logger.info("📋 Creating dashboard tabs...")
        
        # Get existing sheets
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        existing_sheets = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
        
        required_tabs = [
            'Current Snapshot',
            'Top Picks', 
            'Single Pick',
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
            logger.info("✅ All required tabs already exist")
    
    def create_current_snapshot_tab(self, df: pd.DataFrame):
        """Create Current Snapshot with consistent stock code format"""
        logger.info("📊 Creating Current Snapshot tab with consistent formatting...")
        
        # Ensure stock codes are numeric for consistent matching
        df['stock_code'] = pd.to_numeric(df['stock_code'], errors='coerce').fillna(0).astype(int)
        
        # Prepare headers - exact order for formulas (Added Current Price after Company Name)
        headers = [
            'Stock Code', 'Company Name', 'Current Price', 'Quality Score', 
            'DCF Value', 'Graham Value', 'NAV Value', 'PE Value', 'DDM Value',
            'Five Model Consensus', 'Original Consensus', 'Safety Margin', 'Recommendation',
            'Quality Rank', 'Overall Rank', 'ROE', 'ROA', 'EPS', 'Dividend Yield'
        ]
        
        # Prepare data rows with numeric stock codes
        data_rows = []
        for _, row in df.iterrows():
            data_row = [
                int(row.get('stock_code', 0)),  # Integer for consistent lookup
                str(row.get('company_name', '')),
                '=IFERROR(GOOGLEFINANCE("TPE:"&A' + str(len(data_rows) + 2) + '),IFERROR(IMPORTXML("https://tw.stock.yahoo.com/quote/"&A' + str(len(data_rows) + 2) + '&".TW/dividend", "/html/body/div[1]/div/div/div/div/div[4]/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/span[1]"),"無法取得"))',  # Current Price formula
                round(float(row.get('quality_score', 0)), 2),
                round(float(row.get('dcf_valuation', 0)), 2),
                round(float(row.get('graham_valuation', 0)), 2),
                round(float(row.get('nav_valuation', 0)), 2),
                round(float(row.get('pe_valuation', 0)), 2),
                round(float(row.get('ddm_valuation', 0)), 2),
                round(float(row.get('five_model_consensus', 0)), 2),
                round(float(row.get('original_consensus', 0)), 2),
                round(float(row.get('safety_margin', 0)), 4),
                str(row.get('recommendation', '')),
                int(row.get('quality_rank', 0)),
                int(row.get('overall_rank', 0)),
                round(float(row.get('avg_roe', 0)), 2),
                round(float(row.get('avg_roa', 0)), 2),
                round(float(row.get('avg_eps', 0)), 2),
                round(float(row.get('avg_dividend_yield', 0)), 2)
            ]
            data_rows.append(data_row)
        
        # Combine headers and data
        sheet_data = [headers] + data_rows
        
        # Update sheet with USER_ENTERED to execute current price formulas
        self._update_range('Current Snapshot!A1', sheet_data, 'USER_ENTERED')
        
        logger.info(f"✅ Current Snapshot: {len(data_rows)} stocks with numeric stock codes + real-time prices")
        logger.info(f"📊 Column Map: A=Stock(int), B=Company, C=Current Price, D=Quality, E=DCF, F=Graham...")
        
        # Show sample for verification
        if len(data_rows) > 0:
            sample = data_rows[0]
            logger.info(f"📋 Sample: Stock={sample[0]} (type={type(sample[0])}), Company='{sample[1]}'")

    def create_single_pick_tab(self, df: pd.DataFrame):
        """Create Single Pick with dropdown weight selection"""
        logger.info("🔍 Creating Single Pick with dropdown weight selection...")
        
        # Get top stock as default (ensure it's integer)
        top_stock = int(df.nsmallest(1, 'overall_rank').iloc[0]['stock_code'])
        
        # Create data with new layout structure
        single_pick_data = [
            # Row 1: Main headers with colored sections
            ['🔍 單股分析 (五模型)', '輸入股票代號', '輸入建議權重', '估值模型權重調整', '🚀 成長股建議權重', '💎 價值股建議權重', '💰 配息股建議權重', '⚖️ 平衡股建議權重', '🔄 配置股建議權重', '🎯 平衡股建議權重'],
            
            # Row 2: Stock input, strategy selector, and weight headers
            ['股票代號', top_stock, '成長股建議權重', 'DCF權重(%)', '50%', '20%', '15%', '30%', '15%', '30%'],
            
            # Row 3: Company Name lookup
            ['公司名稱', '=IFERROR(INDEX(\'Current Snapshot\'!B:B,MATCH(B2,\'Current Snapshot\'!A:A,0)),"查無此股票代號")', '', 'Graham權重(%)', '5%', '25%', '15%', '15%', '15%', '15%'],
            
            # Row 4: Current Price lookup
            ['現價', '=IFERROR(INDEX(\'Current Snapshot\'!C:C,MATCH(B2,\'Current Snapshot\'!A:A,0)),"無法取得")', '', 'NAV權重(%)', '10%', '30%', '20%', '20%', '20%', '20%'],
            
            # Row 5: Investment Recommendation
            ['投資建議', '=IFERROR(INDEX(\'Current Snapshot\'!M:M,MATCH(B2,\'Current Snapshot\'!A:A,0)),"N/A")', '', 'P/E權重(%)', '30%', '20%', '25%', '25%', '25%', '25%'],
            
            # Row 6: Quality Score
            ['品質評分', '=IFERROR(INDEX(\'Current Snapshot\'!D:D,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', 'DDM權重(%)', '5%', '5%', '25%', '10%', '25%', '10%'],
            
            # Row 7: Overall Rank and Weight Total
            ['整體排名', '=IFERROR(INDEX(\'Current Snapshot\'!O:O,MATCH(B2,\'Current Snapshot\'!A:A,0)),999)', '', '權重總計', '100%', '100%', '100%', '100%', '100%', '100%'],
            
            # Row 8: Section headers
            ['🔥 五模型估值結果', '', '', '🎯 調整後估值', '', '', '', '', '', ''],
            
            # Row 9: DCF Valuation with dynamic weight selection
            ['DCF估值', '=IFERROR(INDEX(\'Current Snapshot\'!E:E,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', '調整後共識', 
            '=IF(C2="成長股建議權重",ROUND((B9*VALUE(SUBSTITUTE(E2,"%",""))/100+B10*VALUE(SUBSTITUTE(E3,"%",""))/100+B11*VALUE(SUBSTITUTE(E4,"%",""))/100+B12*VALUE(SUBSTITUTE(E5,"%",""))/100+B13*VALUE(SUBSTITUTE(E6,"%",""))/100),1),IF(C2="價值股建議權重",ROUND((B9*VALUE(SUBSTITUTE(F2,"%",""))/100+B10*VALUE(SUBSTITUTE(F3,"%",""))/100+B11*VALUE(SUBSTITUTE(F4,"%",""))/100+B12*VALUE(SUBSTITUTE(F5,"%",""))/100+B13*VALUE(SUBSTITUTE(F6,"%",""))/100),1),IF(C2="配息股建議權重",ROUND((B9*VALUE(SUBSTITUTE(G2,"%",""))/100+B10*VALUE(SUBSTITUTE(G3,"%",""))/100+B11*VALUE(SUBSTITUTE(G4,"%",""))/100+B12*VALUE(SUBSTITUTE(G5,"%",""))/100+B13*VALUE(SUBSTITUTE(G6,"%",""))/100),1),ROUND((B9*VALUE(SUBSTITUTE(H2,"%",""))/100+B10*VALUE(SUBSTITUTE(H3,"%",""))/100+B11*VALUE(SUBSTITUTE(H4,"%",""))/100+B12*VALUE(SUBSTITUTE(H5,"%",""))/100+B13*VALUE(SUBSTITUTE(H6,"%",""))/100),1))))',
            '', '', '', '', ''],
            
            # Row 10: Graham Valuation
            ['Graham估值', '=IFERROR(INDEX(\'Current Snapshot\'!F:F,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', 'vs五模型共識', '=IF(AND(ISNUMBER(E9),ISNUMBER(B14)),ROUND((E9-B14)/B14*100,1)&"%","N/A")', '', '', '', '', ''],
            
            # Row 11: NAV Valuation  
            ['NAV估值', '=IFERROR(INDEX(\'Current Snapshot\'!G:G,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', 'vs原始共識', '=IF(AND(ISNUMBER(E9),ISNUMBER(B15)),ROUND((E9-B15)/B15*100,1)&"%","N/A")', '', '', '', '', ''],
            
            # Row 12: P/E Valuation
            ['P/E估值', '=IFERROR(INDEX(\'Current Snapshot\'!H:H,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', 'vs DCF差異', '=IF(AND(ISNUMBER(E9),ISNUMBER(B9)),ROUND((E9-B9)/B9*100,1)&"%","N/A")', '', '', '', '', ''],
            
            # Row 13: DDM Valuation
            ['DDM估值', '=IFERROR(INDEX(\'Current Snapshot\'!I:I,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', 'vs Graham差異', '=IF(AND(ISNUMBER(E9),ISNUMBER(B10)),ROUND((E9-B10)/B10*100,1)&"%","N/A")', '', '', '', '', ''],
            
            # Row 14: Five Model Consensus
            ['五模型共識', '=IFERROR(INDEX(\'Current Snapshot\'!J:J,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', '📈 財務指標', '', '', '', '', '', ''],
            
            # Row 15: Original Consensus and ROE
            ['原始共識(DCF+Graham)', '=IFERROR(INDEX(\'Current Snapshot\'!K:K,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', 'ROE(%)', '=IFERROR(INDEX(\'Current Snapshot\'!P:P,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', '', '', '', ''],
            
            # Row 16: Safety Margin and ROA
            ['安全邊際', '=IFERROR(INDEX(\'Current Snapshot\'!L:L,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', 'ROA(%)', '=IFERROR(INDEX(\'Current Snapshot\'!Q:Q,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', '', '', '', ''],
            
            # Row 17: EPS and Dividend Yield
            ['EPS(元)', '=IFERROR(INDEX(\'Current Snapshot\'!R:R,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', '股息殖利率(%)', '=IFERROR(INDEX(\'Current Snapshot\'!S:S,MATCH(B2,\'Current Snapshot\'!A:A,0)),0)', '', '', '', '', ''],
            
            # Row 18: Stock Characteristics and Investment Decision
            ['股票特性', '=IF(B6>7,"高品質股票",IF(B6>5,"中等品質","需謹慎評估"))', '', '💡 投資決策建議', '', '', '', '', '', ''],
            
            # Row 19: Usage Instructions and Risk Rating
            ['📝 使用說明', '1. 在B2輸入4位數股票代號', '', '風險評級', '=IF(B5="Strong Buy","低風險",IF(B5="Buy","中等風險",IF(B5="Hold","中高風險","高風險")))', '', '', '', '', ''],
            
            # Row 20: Additional Instructions and Allocation Recommendation
            ['', '2. 調整E2-E6權重(總和=100%)', '', '建議配置', '=IF(B5="Strong Buy","5-10%",IF(B5="Buy","3-7%",IF(B5="Hold","1-3%","避免投資"))', '', '', '', '', '3. 查看E9自定義估值結果']
        ]
        
        # Write data with USER_ENTERED to execute formulas
        logger.info("📝 Writing Single Pick with dropdown weight selection...")
        self._update_range('Single Pick!A1:J20', single_pick_data, 'USER_ENTERED')
        time.sleep(1)
        
        # Create dropdown for C2 using data validation
        logger.info("🎛️ Adding dropdown validation for strategy selection...")
        dropdown_request = {
            "requests": [{
                "setDataValidation": {
                    "range": {
                        "sheetId": 0,  # Will need to get actual sheet ID
                        "startRowIndex": 1,  # Row 2 (0-indexed)
                        "endRowIndex": 2,    # Row 2 (0-indexed)
                        "startColumnIndex": 2, # Column C (0-indexed)
                        "endColumnIndex": 3    # Column C (0-indexed)
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": "成長股建議權重"},
                                {"userEnteredValue": "價值股建議權重"},
                                {"userEnteredValue": "配息股建議權重"},
                                {"userEnteredValue": "平衡股建議權重"}
                            ]
                        },
                        "showCustomUi": True,
                        "strict": True
                    }
                }
            }]
        }
        
        try:
            # Get sheet ID for Single Pick tab
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            single_pick_sheet_id = None
            for sheet in sheet_metadata['sheets']:
                if sheet['properties']['title'] == 'Single Pick':
                    single_pick_sheet_id = sheet['properties']['sheetId']
                    break
            
            if single_pick_sheet_id is not None:
                dropdown_request['requests'][0]['setDataValidation']['range']['sheetId'] = single_pick_sheet_id
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body=dropdown_request
                ).execute()
                logger.info("✅ Dropdown validation added to C2")
            else:
                logger.warning("⚠️ Could not find Single Pick sheet ID for dropdown")
        except Exception as e:
            logger.warning(f"⚠️ Could not add dropdown validation: {e}")
        
        logger.info("✅ Single Pick with dropdown selection created")
        logger.info(f"📋 Default stock: {top_stock} with strategy selector in C2")
        logger.info("🎯 Features: Dynamic weight selection + Real-time calculations + Strategy comparison")
    def create_top_picks_tab(self, df: pd.DataFrame):
        """Create/update top picks tab"""
        logger.info("⭐ Creating Top Picks tab...")
        
        # Filter top picks
        hold_and_above = df[df['recommendation'].isin(['Strong Buy', 'Buy', 'Hold'])].copy()
        if len(hold_and_above) < 10:
            top_picks = df.nsmallest(20, 'overall_rank')
        else:
            top_picks = hold_and_above.sort_values('overall_rank').head(20)
        
        headers = [
            'Rank', 'Stock Code', 'Company Name', 'Current Price', 'Recommendation', 'Quality Score', 
            'Safety Margin', 'Five Model Consensus', 'Key Strengths'
        ]
        
        data_rows = []
        for i, (_, row) in enumerate(top_picks.iterrows(), 1):
            # Generate key strengths
            strengths = []
            if row.get('quality_score', 0) >= 3:
                strengths.append('Above Average Quality')
            if row.get('safety_margin', 0) >= 0:
                strengths.append('Positive Safety Margin')
            if row.get('avg_roe', 0) >= 5:
                strengths.append('Good ROE')
            if row.get('dividend_consistency', 0) >= 0.5:
                strengths.append('Dividend History')
            
            data_row = [
                i,
                int(row.get('stock_code', 0)),
                str(row.get('company_name', '')),
                f'=IFERROR(GOOGLEFINANCE("TPE:"&B{i+1}),IFERROR(IMPORTXML("https://tw.stock.yahoo.com/quote/"&B{i+1}&".TW/dividend", "/html/body/div[1]/div/div/div/div/div[4]/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/span[1]"),"無法取得"))',  # Current Price
                row.get('recommendation', ''),
                row.get('quality_score', 0),
                f"{row.get('safety_margin', 0):.1%}",
                row.get('five_model_consensus', 0),
                ', '.join(strengths[:3]) if strengths else 'Review Needed'
            ]
            data_rows.append(data_row)
        
        sheet_data = [headers] + data_rows
        self._update_range('Top Picks!A1', sheet_data, 'USER_ENTERED')
        
        logger.info(f"✅ Updated Top Picks with {len(data_rows)} stocks + real-time prices")

    def create_summary_tab(self, df: pd.DataFrame):
        """Create/update summary dashboard tab"""
        logger.info("📈 Creating Summary tab...")
        
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
            ['Analysis Overview', ''],
            ['Total Stocks Analyzed', total_stocks],
            ['Average Quality Score', f"{avg_quality:.1f}/10"],
            ['', ''],
            ['Recommendation Breakdown', ''],
            ['Strong Buy Recommendations', strong_buy],
            ['Buy Recommendations', buy],
            ['Hold Recommendations', hold],
            ['Avoid Recommendations', total_stocks - strong_buy - buy - hold],
            ['', ''],
            ['Top 5 Stocks by Overall Ranking', ''],
            ['Rank', 'Stock Code', 'Company Name'],
        ]
        
        # Add top 5 stocks with company names
        top_5 = df.nsmallest(5, 'overall_rank')
        for i, (_, row) in enumerate(top_5.iterrows(), 1):
            summary_data.append([i, int(row['stock_code']), str(row.get('company_name', ''))])
        
        self._update_range('Summary!A1', summary_data, 'RAW')
        logger.info(f"✅ Updated Summary dashboard")
    
    def create_last_updated_tab(self):
        """Create/update last updated tab"""
        logger.info("🕐 Creating Last Updated tab...")
        
        timestamp_data = [
            ['Stock Analysis System - Status', ''],
            ['', ''],
            ['Last Analysis Run', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['System Version', '2.3.0 - ENVIRONMENT VARIABLES + REAL-TIME PRICES'],
            ['Data Source', 'GoodInfo.tw + Real-time Price Feeds'],
            ['Analysis Pipeline', '5-Stage Processing'],
            ['Valuation Models', '5 Models (DCF, Graham, NAV, P/E, DDM)'],
            ['Company Names', 'Included in all tabs'],
            ['Real-time Prices', 'GOOGLEFINANCE + Yahoo Finance fallback'],
            ['Configuration', 'Environment Variables + .env support'],
            ['', ''],
            ['Pipeline Stages Completed:', ''],
            ['✅ Stage 1: Excel to CSV', 'Completed'],
            ['✅ Stage 2: Data Cleaning', 'Completed'],
            ['✅ Stage 3: Basic Analysis', 'Completed'],
            ['✅ Stage 4: Enhanced Analysis (5 Models)', 'Completed'],
            ['✅ Stage 5: Dashboard with Environment Config', 'Completed'],
            ['', ''],
            ['Environment Configuration:', ''],
            ['📊 Environment Variables', 'Active'],
            ['🔐 Secure Credential Handling', 'Active'],
            ['⚙️ .env File Support', 'Active'],
            ['🔄 JSON Content Support', 'Active'],
            ['🧹 Automatic Cleanup', 'Active'],
            ['', ''],
            ['Dashboard Features:', ''],
            ['📊 Numeric Stock Code Matching', 'Active'],
            ['🔍 Working Lookup Formulas', 'Active'],
            ['⭐ Quality Scoring System', 'Active'],
            ['💰 Five Valuation Models', 'DCF + Graham + NAV + P/E + DDM'],
            ['📈 Investment Recommendations', 'Active'],
            ['🎯 Five-Model Consensus', 'Active'],
            ['🛠️ USER_ENTERED Formula Execution', 'Active'],
            ['💹 Real-time Current Prices', 'GOOGLEFINANCE + Yahoo fallback'],
            ['📱 Live Price Updates', 'Automatic refresh in Google Sheets'],
            ['', ''],
            ['Price Data Sources:', ''],
            ['Primary: GOOGLEFINANCE("TPE:stock_code")', 'Taiwan Stock Exchange'],
            ['Fallback: Yahoo Finance IMPORTXML', 'Backup price source'],
            ['Update Frequency', 'Real-time during market hours'],
            ['', ''],
            ['Configuration Sources:', ''],
            ['Environment Variables', 'GOOGLE_SHEETS_CREDENTIALS, GOOGLE_SHEET_ID'],
            ['.env File Support', 'Local development configuration'],
            ['GitHub Secrets', 'CI/CD deployment'],
            ['Temporary File Management', 'Automatic JSON credential handling'],
            ['', ''],
            ['Next Scheduled Update', 'Manual trigger or GitHub Actions'],
            ['Dashboard URL', f'https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit']
        ]
        
        self._update_range('Last Updated!A1', timestamp_data, 'RAW')
        logger.info(f"✅ Updated Last Updated tab")
    
    def run_pipeline(self) -> dict:
        """Run complete sheets publishing pipeline"""
        
        # Load enhanced analysis
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
        
        logger.info(f"📊 Publishing {len(df)} stocks with environment variable configuration...")
        
        try:
            # Create all required tabs
            self.create_required_tabs()
            
            # Create/update all tabs
            self.create_current_snapshot_tab(df)
            time.sleep(1)
            
            self.create_top_picks_tab(df)
            time.sleep(1)
            
            self.create_single_pick_tab(df)  # WORKING formulas
            time.sleep(1)
            
            self.create_summary_tab(df)
            time.sleep(1)
            
            self.create_last_updated_tab()
            
            return {
                'status': 'success',
                'total_stocks': len(df),
                'sheets_updated': 5,
                'version': 'ENVIRONMENT 2.3.0',
                'features': [
                    'Environment variable configuration',
                    'Secure credential handling',
                    '.env file support',
                    'JSON content support',
                    'Automatic cleanup',
                    'Real-time current prices',
                    'Working lookup formulas',
                    'Five valuation models'
                ]
            }
        
        except Exception as e:
            logger.error(f"❌ Error publishing to sheets: {e}")
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
def run_stage5_env(credentials: str, sheet_id: str, input_dir: str, debug: bool):
    """
    Run Stage 5: Google Sheets Dashboard Publisher with Environment Variables
    
    ENVIRONMENT VARIABLE FEATURES:
    ✅ Reads GOOGLE_SHEETS_CREDENTIALS and GOOGLE_SHEET_ID from environment
    ✅ Supports both credential file paths and JSON content
    ✅ Automatic temporary file management for JSON credentials
    ✅ .env file support with python-dotenv
    ✅ Secure credential cleanup
    ✅ Backward compatible with --credentials and --sheet-id flags
    
    Usage:
    1. Set environment variables (recommended):
       python -m src.pipelines.stage5_sheets_publisher
    
    2. Use command line flags (legacy):
       python -m src.pipelines.stage5_sheets_publisher --credentials google_key.json --sheet-id YOUR_SHEET_ID
    
    3. Mix environment and flags:
       GOOGLE_SHEET_ID=your_id python -m src.pipelines.stage5_sheets_publisher --credentials google_key.json
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
        click.echo("3. See instructions-ENV.md for detailed setup")
        return
    
    # Validate credentials (if it's a file path)
    if not final_credentials.strip().startswith('{') and not Path(final_credentials).exists():
        click.echo(f"❌ Credentials file not found: {final_credentials}")
        return
    
    click.echo("🔧 Configuration:")
    if final_credentials.strip().startswith('{'):
        click.echo("   Credentials: JSON content from environment")
    else:
        click.echo(f"   Credentials: {final_credentials}")
    click.echo(f"   Sheet ID: {final_sheet_id}")
    
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
        click.echo(f"\n🎉 ENVIRONMENT VARIABLE Dashboard Published Successfully!")
        click.echo(f"📊 Dashboard Features:")
        click.echo(f"   📋 Current Snapshot: All {result['total_stocks']} stocks with 5 models + real-time prices")
        click.echo(f"   ⭐ Top Picks: Best opportunities with company names + current prices")
        click.echo(f"   🔍 Single Pick: WORKING interactive lookup + real-time price display")
        click.echo(f"   📈 Summary: Overview dashboard")
        click.echo(f"   🕐 Last Updated: Environment configuration tracking")
        
        click.echo(f"\n⚙️ ENVIRONMENT VARIABLE FEATURES:")
        for feature in result['features']:
            click.echo(f"   ✅ {feature}")
        
        click.echo(f"\n🔗 View Your Dashboard:")
        click.echo(f"   https://docs.google.com/spreadsheets/d/{final_sheet_id}/edit")
        
        click.echo(f"\n💡 Next Time:")
        click.echo(f"   Just run: python scripts/run_pipeline.py")
        click.echo(f"   (Environment variables will be used automatically)")

if __name__ == '__main__':
    run_stage5_env()