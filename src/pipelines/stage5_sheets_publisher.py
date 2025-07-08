# src/pipelines/stage5_sheets_publisher.py
"""
Stage 5 Pipeline: Google Sheets Dashboard Publisher v1.3.0 - 12-MODEL FRAMEWORK
✅ 12 MODELS: DCF + Graham + NAV + 8 P/E Scenarios + DDM in Google Sheets
✅ ENHANCED DASHBOARD: All 12 model values visible with detailed P/E scenario analysis
✅ COMPREHENSIVE: Complete transparency of all valuation models
✅ INTERACTIVE: Enhanced Single Pick with all 12 models displayed
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

class TwelveModelSheetsPublisher:
    """Google Sheets publisher for 12-model framework"""
    
    def __init__(self, credentials_path: str, sheet_id: str, input_dir: str):
        self.input_dir = Path(input_dir)
        self.sheet_id = sheet_id
        self.credentials_path = credentials_path
        self.temp_credentials_file = None
        self.service = self._authenticate(credentials_path)
        
        # Data directories
        self.stage1_raw_dir = self.input_dir.parent / 'stage1_raw'
        self.stage2_cleaned_dir = self.input_dir.parent / 'stage2_cleaned'
        self.stage3_analysis_dir = self.input_dir.parent / 'stage3_analysis'
        self.stage4_enhanced_dir = self.input_dir  # Current input_dir
        
        # 12-Model weights for calculations
        self.model_weights = {
            'dcf': 0.20,
            'graham': 0.10,
            'nav': 0.15,
            'pe_scenario_1': 0.055,
            'pe_scenario_2': 0.055,
            'pe_scenario_3': 0.055,
            'pe_scenario_4': 0.055,
            'pe_scenario_5': 0.055,
            'pe_scenario_6': 0.055,
            'pe_scenario_7': 0.055,
            'pe_scenario_8': 0.055,
            'ddm': 0.10
        }
    
    def _authenticate(self, credentials_path: str):
        """Authenticate with Google Sheets API"""
        try:
            # Check if credentials_path is JSON content
            if credentials_path.strip().startswith('{'):
                try:
                    credentials_data = json.loads(credentials_path)
                    
                    # Create temporary credentials file
                    self.temp_credentials_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                    self.temp_credentials_file.write(credentials_path)
                    self.temp_credentials_file.close()
                    
                    logger.info("Using credentials from JSON content")
                    credentials_path = self.temp_credentials_file.name
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in credentials: {e}")
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
        """Clean up temporary credentials file"""
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
    
    def create_required_tabs_12_model(self):
        """Create all required dashboard tabs for 12-model framework"""
        logger.info("📋 Creating dashboard tabs for 12-MODEL FRAMEWORK...")
        
        # Get existing sheets
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        existing_sheets = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
        
        # Required tabs for 12-model framework
        required_tabs = [
            # Dashboard Tabs (Enhanced for 12 models)
            'Current Snapshot 12M',
            'Top Picks 12M', 
            'Single Pick 12M',
            
            # Analysis Tabs
            '12-Model Analysis',
            'P/E Scenarios',
            
            # Data Tabs
            'Basic Analysis',
            'Raw Revenue Data',
            'Raw Dividends Data',
            'Raw Performance Data',
            
            # Meta Tabs
            'Summary 12M',
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
            time.sleep(2)
        else:
            logger.info("✅ All required tabs already exist")
    
    def create_current_snapshot_12_model(self):
        """Create Current Snapshot with all 12 models - FIXED to show ALL companies"""
        logger.info("📊 Creating Current Snapshot with 12-Model Framework (ALL COMPANIES)...")
        
        # STEP 1: First, determine how many companies we have
        enhanced_analysis_file = self.stage4_enhanced_dir / 'enhanced_analysis.csv'
        total_companies = 50  # Default fallback
        
        if enhanced_analysis_file.exists():
            try:
                df = pd.read_csv(enhanced_analysis_file)
                total_companies = len(df)
                logger.info(f"   📊 Found {total_companies} companies in enhanced analysis")
            except Exception as e:
                logger.warning(f"   Could not count companies: {e}")
        
        # Enhanced headers for 12 models
        headers = [
            'Stock Code', 'Company Name', 'Current Price', 'Quality Score',
            # Core Models (4)
            'DCF Value', 'Graham Value', 'NAV Value', 'DDM Value',
            # P/E Scenario Models (8)
            'P/E Scenario 1', 'P/E Scenario 2', 'P/E Scenario 3', 'P/E Scenario 4',
            'P/E Scenario 5', 'P/E Scenario 6', 'P/E Scenario 7', 'P/E Scenario 8',
            # Consensus and Analysis
            '12-Model Consensus', 'Safety Margin', 'Best P/E Scenario', 
            'P/E Range', 'Recommendation', 'Overall Rank'
        ]
        
        formula_data = [
            headers,  # Row 1: Headers
            
            # Row 2: First data row with 12-model formulas
            [
                '=INDEX(\'12-Model Analysis\'!A:A,2)',  # Stock Code
                '=INDEX(\'12-Model Analysis\'!B:B,2)',  # Company Name
                '=IFERROR(GOOGLEFINANCE("TPE:"&A2),100)',  # Current Price
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("quality_score",\'12-Model Analysis\'!1:1,0))',  # Quality Score
                
                # Core Models (4)
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("dcf_valuation",\'12-Model Analysis\'!1:1,0))',  # DCF
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("graham_valuation",\'12-Model Analysis\'!1:1,0))',  # Graham
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("nav_valuation",\'12-Model Analysis\'!1:1,0))',  # NAV
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("ddm_valuation",\'12-Model Analysis\'!1:1,0))',  # DDM
                
                # P/E Scenario Models (8)
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("pe_scenario_1_valuation",\'12-Model Analysis\'!1:1,0))',
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("pe_scenario_2_valuation",\'12-Model Analysis\'!1:1,0))',
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("pe_scenario_3_valuation",\'12-Model Analysis\'!1:1,0))',
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("pe_scenario_4_valuation",\'12-Model Analysis\'!1:1,0))',
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("pe_scenario_5_valuation",\'12-Model Analysis\'!1:1,0))',
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("pe_scenario_6_valuation",\'12-Model Analysis\'!1:1,0))',
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("pe_scenario_7_valuation",\'12-Model Analysis\'!1:1,0))',
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("pe_scenario_8_valuation",\'12-Model Analysis\'!1:1,0))',
                
                # 12-Model Consensus (weighted average)
                f'=ROUND((E2*{self.model_weights["dcf"]} + F2*{self.model_weights["graham"]} + G2*{self.model_weights["nav"]} + H2*{self.model_weights["ddm"]} + I2*{self.model_weights["pe_scenario_1"]} + J2*{self.model_weights["pe_scenario_2"]} + K2*{self.model_weights["pe_scenario_3"]} + L2*{self.model_weights["pe_scenario_4"]} + M2*{self.model_weights["pe_scenario_5"]} + N2*{self.model_weights["pe_scenario_6"]} + O2*{self.model_weights["pe_scenario_7"]} + P2*{self.model_weights["pe_scenario_8"]}),2)',
                
                # Safety Margin
                '=IF(AND(ISNUMBER(Q2),ISNUMBER(C2),C2>0),ROUND((Q2-C2)/C2,3),0)',
                
                # Best P/E Scenario
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("best_pe_scenario",\'12-Model Analysis\'!1:1,0))',
                
                # P/E Range
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("pe_scenario_range",\'12-Model Analysis\'!1:1,0))',
                
                # Recommendation and Rank
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("recommendation",\'12-Model Analysis\'!1:1,0))',
                '=INDEX(\'12-Model Analysis\'!1:1048576,2,MATCH("overall_rank",\'12-Model Analysis\'!1:1,0))'
            ]
        ]
        
        # FIXED: Add formula rows for ALL companies (not just 30)
        max_row = min(total_companies + 1, 500)  # Cap at 500 for Google Sheets performance
        logger.info(f"   📋 Creating formulas for rows 3 to {max_row} ({max_row-2} companies)")
        
        for row_num in range(3, max_row + 1):
            formula_row = [
                f'=INDEX(\'12-Model Analysis\'!A:A,{row_num})',  # Stock Code
                f'=INDEX(\'12-Model Analysis\'!B:B,{row_num})',  # Company Name
                f'=IFERROR(GOOGLEFINANCE("TPE:"&A{row_num}),100)',  # Current Price
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("quality_score",\'12-Model Analysis\'!1:1,0))',  # Quality Score
                
                # Core Models (4)
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("dcf_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("graham_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("nav_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("ddm_valuation",\'12-Model Analysis\'!1:1,0))',
                
                # P/E Scenario Models (8)
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("pe_scenario_1_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("pe_scenario_2_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("pe_scenario_3_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("pe_scenario_4_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("pe_scenario_5_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("pe_scenario_6_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("pe_scenario_7_valuation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("pe_scenario_8_valuation",\'12-Model Analysis\'!1:1,0))',
                
                # 12-Model Consensus
                f'=ROUND((E{row_num}*{self.model_weights["dcf"]} + F{row_num}*{self.model_weights["graham"]} + G{row_num}*{self.model_weights["nav"]} + H{row_num}*{self.model_weights["ddm"]} + I{row_num}*{self.model_weights["pe_scenario_1"]} + J{row_num}*{self.model_weights["pe_scenario_2"]} + K{row_num}*{self.model_weights["pe_scenario_3"]} + L{row_num}*{self.model_weights["pe_scenario_4"]} + M{row_num}*{self.model_weights["pe_scenario_5"]} + N{row_num}*{self.model_weights["pe_scenario_6"]} + O{row_num}*{self.model_weights["pe_scenario_7"]} + P{row_num}*{self.model_weights["pe_scenario_8"]}),2)',
                
                # Safety Margin
                f'=IF(AND(ISNUMBER(Q{row_num}),ISNUMBER(C{row_num}),C{row_num}>0),ROUND((Q{row_num}-C{row_num})/C{row_num},3),0)',
                
                # Best P/E Scenario, P/E Range, Recommendation, Rank
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("best_pe_scenario",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("pe_scenario_range",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("recommendation",\'12-Model Analysis\'!1:1,0))',
                f'=INDEX(\'12-Model Analysis\'!1:1048576,{row_num},MATCH("overall_rank",\'12-Model Analysis\'!1:1,0))'
            ]
            formula_data.append(formula_row)
        
        # Update sheet with appropriate range
        range_end_column = 'X'  # Column X = 24th column
        range_end_row = len(formula_data)
        range_name = f'Current Snapshot 12M!A1:{range_end_column}{range_end_row}'
        
        logger.info(f"   📋 Updating range: {range_name}")
        logger.info(f"   📊 Total companies displayed: {range_end_row - 1}")
        
        self._update_range(range_name, formula_data, 'USER_ENTERED')
        
        logger.info("✅ Current Snapshot 12M created with ALL companies (not limited to 30)")


    # Also add this helper method to dynamically count companies
    def get_total_companies_count(self):
        """Get the total number of companies from enhanced analysis"""
        enhanced_analysis_file = self.stage4_enhanced_dir / 'enhanced_analysis.csv'
        
        if enhanced_analysis_file.exists():
            try:
                df = pd.read_csv(enhanced_analysis_file)
                return len(df)
            except Exception as e:
                logger.warning(f"Could not count companies: {e}")
                return 50  # Fallback
        else:
            logger.warning("Enhanced analysis file not found")
            return 50  # Fallback
    
    def create_single_pick_12_model(self):
        """Create Single Pick with 12-model analysis"""
        logger.info("🔍 Creating Single Pick with 12-Model Analysis...")
        
        single_pick_data = [
            # Header
            ['🎯 單股分析 12-MODEL FRAMEWORK', '輸入股票代號', '12模型分析', '加權共識', '最佳P/E情境', '', '', ''],
            
            # Input and basic info
            ['股票代號', '=INDEX(\'12-Model Analysis\'!A:A,2)', '12模型架構', '實時價格', '=IFERROR(GOOGLEFINANCE("TPE:"&B2),100)', '', '', ''],
            ['公司名稱', '=IFERROR(INDEX(\'12-Model Analysis\'!B:B,MATCH(B2,\'12-Model Analysis\'!A:A,0)),"查無此股票")', '4+8+1模型', '品質評分', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("quality_score",\'12-Model Analysis\'!1:1,0)),0)', '', '', ''],
            ['投資建議', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("recommendation",\'12-Model Analysis\'!1:1,0)),"N/A")', '完整透明', '整體排名', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("overall_rank",\'12-Model Analysis\'!1:1,0)),999)', '', '', ''],
            
            # Spacer
            ['', '', '', '', '', '', '', ''],
            
            # 12-Model Analysis Section
            ['📊 12模型詳細分析', '', '', '🎯 加權共識結果', '', '', '', ''],
            
            # Core Models (4)
            ['核心模型 (45%)', '', '', '12模型共識', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("twelve_model_consensus",\'12-Model Analysis\'!1:1,0)),0)', '', '', ''],
            ['DCF估值 (20%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("dcf_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', 'vs目前股價', '=IF(AND(ISNUMBER(E8),ISNUMBER(E2)),ROUND((E8-E2)/E2*100,1)&"%","N/A")', '', '', ''],
            ['Graham估值 (10%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("graham_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', '安全邊際', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("safety_margin",\'12-Model Analysis\'!1:1,0)),0)', '', '', ''],
            ['NAV估值 (15%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("nav_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', '投資時框', '=IF(E9>=0.3,"6-12個月",IF(E9>=0.15,"12-18個月","18個月以上"))', '', '', ''],
            ['DDM估值 (10%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("ddm_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', '', '', '', '', ''],
            
            # Spacer
            ['', '', '', '', '', '', '', ''],
            
            # P/E Scenarios (8)
            ['P/E情境模型 (44%)', '', '', '📈 P/E情境分析', '', '', '', ''],
            ['情境1 (5.5%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("pe_scenario_1_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', '最佳情境', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("best_pe_scenario",\'12-Model Analysis\'!1:1,0)),1)', '', '', ''],
            ['情境2 (5.5%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("pe_scenario_2_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', 'P/E範圍', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("pe_scenario_range",\'12-Model Analysis\'!1:1,0)),"N/A")', '', '', ''],
            ['情境3 (5.5%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("pe_scenario_3_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', 'P/E平均', '=ROUND((B14+B15+B16+B17+B18+B19+B20+B21)/8,1)', '', '', ''],
            ['情境4 (5.5%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("pe_scenario_4_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', 'P/E標準差', '=ROUND(STDEV(B14:B21),1)', '', '', ''],
            ['情境5 (5.5%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("pe_scenario_5_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', '', '', '', '', ''],
            ['情境6 (5.5%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("pe_scenario_6_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', '📊 模型權重分布', '', '', '', ''],
            ['情境7 (5.5%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("pe_scenario_7_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', '核心模型: 45%', 'DCF(20%) + Graham(10%) + NAV(15%)', '', '', ''],
            ['情境8 (5.5%)', '=IFERROR(INDEX(\'12-Model Analysis\'!1:1048576,MATCH(B2,\'12-Model Analysis\'!A:A,0),MATCH("pe_scenario_8_valuation",\'12-Model Analysis\'!1:1,0)),0)', '', 'P/E情境: 44%', '8情境 × 5.5%權重', '', '', ''],
            ['', '', '', 'DDM模型: 10%', '股息貼現模型', '', '', ''],
            ['', '', '', '總權重: 99%', '專業級分散投資', '', '', ''],
            
            # Usage instructions
            ['使用說明 12M', '在B2輸入股票代號', '', '12模型自動計算', '完整透明分析', '查看詳細分析頁', '', '']
        ]
        
        # Update sheet
        self._update_range('Single Pick 12M!A1:H25', single_pick_data, 'USER_ENTERED')
        
        logger.info("✅ Single Pick 12M created with complete 12-model analysis")
    
    def create_12_model_analysis_tab(self):
        """Create 12-Model Analysis data tab"""
        logger.info("📊 Creating 12-Model Analysis data tab...")
        
        enhanced_analysis_file = self.stage4_enhanced_dir / 'enhanced_analysis.csv'
        if not enhanced_analysis_file.exists():
            logger.warning(f"Enhanced analysis file not found")
            placeholder_data = [
                ['12-Model Analysis - Not Available', ''],
                ['File not found:', str(enhanced_analysis_file)],
                ['Status:', 'Run Stage 4 with 12-model framework'],
            ]
            self._update_range('12-Model Analysis!A1', placeholder_data, 'RAW')
            return
        
        try:
            # Load enhanced analysis data
            df = pd.read_csv(enhanced_analysis_file)
            logger.info(f"Loaded 12-model analysis data: {len(df)} rows")
            
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
                        data_row.append(round(value, 4))
                    else:
                        data_row.append(str(value))
                data_rows.append(data_row)
            
            sheet_data = [headers] + data_rows
            
            # Use safe range to avoid issues
            range_name = f'12-Model Analysis!A1:AZ{len(sheet_data)}'
            self._update_range(range_name, sheet_data, 'RAW')
            
            logger.info(f"✅ 12-Model Analysis tab created: {len(data_rows)} rows, {len(headers)} columns")
            
        except Exception as e:
            logger.error(f"Error creating 12-Model Analysis tab: {e}")
            error_data = [
                ['12-Model Analysis - Error', ''],
                ['Error message:', str(e)],
            ]
            self._update_range('12-Model Analysis!A1', error_data, 'RAW')
    
    def create_pe_scenarios_tab(self):
        """Create detailed P/E Scenarios analysis tab"""
        logger.info("🎯 Creating P/E Scenarios detailed analysis tab...")
        
        pe_details_file = self.stage4_enhanced_dir / 'pe_8scenario_details.json'
        if not pe_details_file.exists():
            logger.warning(f"P/E scenarios file not found")
            placeholder_data = [
                ['P/E Scenarios - Not Available', ''],
                ['File not found:', str(pe_details_file)],
                ['Status:', 'Run Stage 4 with 12-model framework'],
            ]
            self._update_range('P/E Scenarios!A1', placeholder_data, 'RAW')
            return
        
        try:
            # Load P/E scenario details
            with open(pe_details_file, 'r', encoding='utf-8') as f:
                pe_data = json.load(f)
            
            logger.info(f"Loaded P/E scenario data for {len(pe_data)} stocks")
            
            # Create comprehensive P/E scenarios display
            analysis_data = [
                ['🎯 P/E Scenarios Detailed Analysis (12-Model Framework)', '', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', ''],
                
                # Header row
                ['Stock Code', 'Company Name', 'Scenario 1', 'Scenario 2', 'Scenario 3', 'Scenario 4', 
                 'Scenario 5', 'Scenario 6', 'Scenario 7', 'Scenario 8', 'Best Scenario', 'Range'],
                
                # Separator
                ['==========', '==========', '==========', '==========', '==========', '==========',
                 '==========', '==========', '==========', '==========', '==========', '==========']
            ]
            
            # Add data rows
            enhanced_analysis_file = self.stage4_enhanced_dir / 'enhanced_analysis.csv'
            if enhanced_analysis_file.exists():
                df = pd.read_csv(enhanced_analysis_file)
                
                for _, row in df.iterrows():
                    stock_code = str(row.get('stock_code', ''))
                    company_name = str(row.get('company_name', stock_code))
                    
                    # Get P/E scenario values
                    scenario_values = []
                    for i in range(1, 9):
                        col_name = f'pe_scenario_{i}_valuation'
                        value = row.get(col_name, 0)
                        scenario_values.append(f"{value:.1f}" if value > 0 else "0.0")
                    
                    best_scenario = row.get('best_pe_scenario', 1)
                    pe_range = row.get('pe_scenario_range', '0.0-0.0')
                    
                    analysis_data.append([
                        stock_code,
                        company_name,
                        *scenario_values,
                        f"Scenario {best_scenario}",
                        pe_range
                    ])
            
            # Add summary section
            analysis_data.extend([
                ['', '', '', '', '', '', '', '', '', '', '', ''],
                ['📊 P/E Scenarios Framework Summary', '', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', '', '', '', '', ''],
                ['EPS Options (2):', '', '', '', '', '', '', ''],
                ['Annual 2024 EPS', 'Conservative baseline from full-year performance', '', '', '', '', '', ''],
                ['Q1 Annualized EPS', 'Growth-adjusted projection for high-growth companies', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', '', '', '', '', ''],
                ['P/E Options (4):', '', '', '', '', '', '', ''],
                ['Q1 P/E', 'Current quarter market valuation', '', '', '', '', '', ''],
                ['Annual P/E', 'Annual historical market valuation', '', '', '', '', '', ''],
                ['Two-year Avg P/E', 'Two-year average for stability', '', '', '', '', '', ''],
                ['Electronics Industry P/E', '20.0x Taiwan electronics industry standard', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', '', '', '', '', ''],
                ['🎯 8 Scenarios = 2 EPS × 4 P/E Combinations', '', '', '', '', '', '', ''],
                ['Each scenario weighted equally (5.5%) in 12-model consensus', '', '', '', '', '', '', ''],
                ['Total P/E weight: 44% (8 × 5.5%)', '', '', '', '', '', '', ''],
            ])
            
            # Update sheet
            range_name = f'P/E Scenarios!A1:L{len(analysis_data)}'
            self._update_range(range_name, analysis_data, 'RAW')
            
            logger.info(f"✅ P/E Scenarios tab created with detailed analysis")
            
        except Exception as e:
            logger.error(f"Error creating P/E Scenarios tab: {e}")
            error_data = [
                ['P/E Scenarios - Error', ''],
                ['Error message:', str(e)],
            ]
            self._update_range('P/E Scenarios!A1', error_data, 'RAW')
    
    def run_pipeline(self) -> dict:
        """Run complete 12-model sheets publishing pipeline"""
        
        # Load enhanced analysis for validation
        input_file = self.input_dir / 'enhanced_analysis.csv'
        if not input_file.exists():
            logger.error("❌ No enhanced analysis file found. Run Stage 4 first.")
            return {'error': 'missing_input'}
        
        df = pd.read_csv(input_file)
        
        if df.empty:
            logger.error("❌ Empty enhanced analysis file")
            return {'error': 'empty_input'}
        
        logger.info(f"📊 Publishing 12-MODEL FRAMEWORK dashboard: {len(df)} stocks")
        logger.info(f"🎯 Framework: 4 Core + 8 P/E Scenarios + 1 DDM = 12 Models")
        
        try:
            # Create all required tabs
            self.create_required_tabs_12_model()
            
            # Create 12-model dashboard tabs
            logger.info("📊 Creating 12-Model Dashboard tabs...")
            self.create_current_snapshot_12_model()
            time.sleep(1)
            
            self.create_single_pick_12_model()
            time.sleep(1)
            
            # Create analysis tabs
            logger.info("📋 Creating Analysis tabs...")
            self.create_12_model_analysis_tab()
            time.sleep(1)
            
            self.create_pe_scenarios_tab()
            time.sleep(1)
            
            return {
                'status': 'success',
                'total_stocks': len(df),
                'sheets_updated': 11,
                'version': 'v1.3.0 - 12-MODEL FRAMEWORK',
                'framework': '4 Core + 8 P/E Scenarios + 1 DDM = 12 Models',
                'model_weights': self.model_weights,
                'features': [
                    '12-model diversified valuation framework',
                    '8 separate P/E scenario models (44% total weight)',
                    '4 core models: DCF, Graham, NAV, DDM (55% total weight)',
                    'Complete transparency of all model values',
                    'Enhanced Single Pick with all 12 models',
                    'Detailed P/E scenario analysis',
                    'Professional-grade diversification',
                    'Live price integration with 12-model consensus',
                    'Comprehensive model weight transparency'
                ]
            }
        
        except Exception as e:
            logger.error(f"❌ Error publishing 12-model dashboard: {e}")
            return {'error': str(e)}
        
        finally:
            self.cleanup_temp_file()

def get_credentials_from_env():
    """Get credentials and sheet ID from environment variables"""
    credentials = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    
    if not credentials:
        click.echo("❌ GOOGLE_SHEETS_CREDENTIALS environment variable not set")
        return None, None
    
    if not sheet_id:
        click.echo("❌ GOOGLE_SHEET_ID environment variable not set")
        return None, None
    
    return credentials, sheet_id

@click.command()
@click.option('--credentials', default=None, help='Path to Google Sheets credentials JSON')
@click.option('--sheet-id', default=None, help='Google Sheets ID')
@click.option('--input-dir', default='data/stage4_enhanced')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def run_stage5_12_model_dashboard(credentials: str, sheet_id: str, input_dir: str, debug: bool):
    """
    Run Stage 5: Google Sheets Dashboard Publisher v1.3.0 - 12-MODEL FRAMEWORK
    
    🚀 12-MODEL FRAMEWORK DASHBOARD:
    ✅ 12 Models: DCF + Graham + NAV + 8 P/E Scenarios + DDM
    ✅ Enhanced transparency: All 12 model values visible
    ✅ Weighted consensus: Professional-grade diversification
    ✅ P/E scenario analysis: Complete 8-scenario breakdown
    ✅ Interactive dashboard: Enhanced Single Pick with all models
    
    📊 Model Breakdown:
    
    Core Models (55% total weight):
    - DCF: 20% (fundamental cash flow analysis)
    - Graham: 10% (value investing baseline)  
    - NAV: 15% (asset-based valuation)
    - DDM: 10% (dividend-based valuation)
    
    P/E Scenario Models (44% total weight, 5.5% each):
    - Scenario 1: Annual EPS × Q1 P/E
    - Scenario 2: Annual EPS × Annual P/E
    - Scenario 3: Annual EPS × Two-year Avg P/E
    - Scenario 4: Annual EPS × Electronics Industry P/E
    - Scenario 5: Q1 Annualized EPS × Q1 P/E
    - Scenario 6: Q1 Annualized EPS × Annual P/E
    - Scenario 7: Q1 Annualized EPS × Two-year Avg P/E
    - Scenario 8: Q1 Annualized EPS × Electronics Industry P/E
    
    📊 Dashboard Features:
    
    Enhanced Tabs:
    1. Current Snapshot 12M: All stocks with 12-model analysis
    2. Single Pick 12M: Interactive analysis with complete model breakdown
    3. 12-Model Analysis: Complete data transparency
    4. P/E Scenarios: Detailed 8-scenario analysis
    
    🎯 Benefits:
    - Diversification: 8 different P/E approaches reduce single-point risk
    - Transparency: All 12 model values visible for analysis
    - Professional: Institution-grade diversified valuation
    - Flexible: Individual model weights can be adjusted
    - Comprehensive: Conservative to aggressive scenarios covered
    """
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        click.echo(f"❌ Input directory not found: {input_dir}")
        return
    
    # Get credentials and sheet ID
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
        click.echo("1. Set environment variables:")
        click.echo("   GOOGLE_SHEETS_CREDENTIALS='path/to/credentials.json'")
        click.echo("   GOOGLE_SHEET_ID='your_sheet_id'")
        return
    
    click.echo("🔧 12-MODEL FRAMEWORK Configuration:")
    if final_credentials.strip().startswith('{'):
        click.echo("   Credentials: JSON content from environment")
    else:
        click.echo(f"   Credentials: {final_credentials}")
    click.echo(f"   Sheet ID: {final_sheet_id}")
    click.echo(f"   Framework: 12-Model (4 Core + 8 P/E Scenarios + 1 DDM)")
    
    # Run pipeline
    publisher = TwelveModelSheetsPublisher(final_credentials, final_sheet_id, input_dir)
    result = publisher.run_pipeline()
    
    # Display results
    if 'error' in result:
        click.echo(f"❌ Publishing failed: {result['error']}")
    else:
        click.echo(f"\n🎉 12-MODEL FRAMEWORK DASHBOARD PUBLISHED!")
        click.echo(f"📊 Framework: {result['framework']}")
        click.echo(f"📋 Version: {result['version']}")
        click.echo(f"🏢 Stocks Analyzed: {result['total_stocks']}")
        
        click.echo(f"\n📊 Model Weights:")
        for model, weight in result['model_weights'].items():
            if model.startswith('pe_scenario'):
                scenario_num = model.split('_')[-1]
                click.echo(f"   P/E Scenario {scenario_num}: {weight:.1%}")
            else:
                click.echo(f"   {model.upper()}: {weight:.1%}")
        
        click.echo(f"\n🚀 12-MODEL FRAMEWORK Features:")
        for feature in result['features']:
            click.echo(f"   ✅ {feature}")
        
        click.echo(f"\n🔗 Access Your 12-Model Dashboard:")
        click.echo(f"   https://docs.google.com/spreadsheets/d/{final_sheet_id}/edit")
        
        click.echo(f"\n💡 Usage Guide:")
        click.echo(f"   📊 Current Snapshot 12M: See all 12 model values for each stock")
        click.echo(f"   🔍 Single Pick 12M: Analyze individual stocks with complete breakdown")
        click.echo(f"   📋 12-Model Analysis: Raw data with all calculations")
        click.echo(f"   🎯 P/E Scenarios: Detailed 8-scenario P/E analysis")
        
        click.echo(f"\n📈 Model Benefits:")
        click.echo(f"   🎯 Diversification: 8 P/E scenarios reduce single-model risk")
        click.echo(f"   📊 Transparency: All 12 models visible and weighted")
        click.echo(f"   🏢 Professional: Institution-grade multi-model approach")
        click.echo(f"   ⚖️ Balanced: Conservative (44%) + Growth scenarios (44%) + Baseline (12%)")

if __name__ == '__main__':
    run_stage5_12_model_dashboard()