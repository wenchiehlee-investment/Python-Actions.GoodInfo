# src/pipelines/stage4_advanced_analysis.py
"""
Stage 4 Pipeline: Advanced Analysis - ENHANCED WITH 5 VALUATION MODELS
✅ DCF, Graham, NAV, P/E, DDM - Complete implementation using GoodInfo CSV data
"""
import pandas as pd
import numpy as np
import click
from pathlib import Path
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedAnalysisPipeline:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_dcf_valuation(self, row: pd.Series) -> float:
        """DCF calculation - existing implementation"""
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
        """Graham formula - existing implementation"""
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
    
    def calculate_nav_valuation(self, row: pd.Series) -> float:
        """NAV (Net Asset Value) calculation using GoodInfo data"""
        try:
            # Get BPS from performance data (已實作於raw_performance.csv)
            bps = row.get('BPS(元)', 0)  # 每股淨值 from GoodInfo
            roe = row.get('avg_roe', 0)  # ROE for quality adjustment
            
            if bps <= 0:
                return 0
            
            # ROE-based quality multiplier
            if roe >= 20:
                quality_multiple = 1.4  # Excellent ROE
            elif roe >= 15:
                quality_multiple = 1.3  # High ROE
            elif roe >= 10:
                quality_multiple = 1.1  # Good ROE
            elif roe >= 5:
                quality_multiple = 1.0  # Fair ROE
            else:
                quality_multiple = 0.8  # Poor ROE
            
            # Asset efficiency adjustment based on ROA
            roa = row.get('avg_roa', 0)
            if roa >= 8:
                efficiency_multiple = 1.1
            elif roa >= 5:
                efficiency_multiple = 1.0
            else:
                efficiency_multiple = 0.95
            
            nav_value = bps * quality_multiple * efficiency_multiple
            return round(nav_value, 2)
        
        except:
            return 0
    
    def calculate_pe_valuation(self, row: pd.Series) -> float:
        """P/E ratio valuation using growth and quality adjustments"""
        try:
            eps = row.get('avg_eps', 0)
            growth_rate = row.get('revenue_growth', 0)
            roe = row.get('avg_roe', 0)
            revenue_volatility = row.get('revenue_volatility', 10)
            
            if eps <= 0:
                return 0
            
            # Base P/E determination (Taiwan market average)
            base_pe = 15  # Taiwan market historical average
            
            # Growth adjustment
            if growth_rate >= 25:
                growth_multiple = 1.6
            elif growth_rate >= 15:
                growth_multiple = 1.4
            elif growth_rate >= 10:
                growth_multiple = 1.2
            elif growth_rate >= 5:
                growth_multiple = 1.1
            elif growth_rate >= 0:
                growth_multiple = 1.0
            else:
                growth_multiple = 0.8
            
            # Quality adjustment based on ROE
            if roe >= 25:
                quality_multiple = 1.4
            elif roe >= 20:
                quality_multiple = 1.3
            elif roe >= 15:
                quality_multiple = 1.2
            elif roe >= 10:
                quality_multiple = 1.0
            elif roe >= 5:
                quality_multiple = 0.9
            else:
                quality_multiple = 0.7
            
            # Risk adjustment (volatility-based)
            if revenue_volatility <= 5:
                risk_multiple = 1.1  # Low volatility premium
            elif revenue_volatility <= 15:
                risk_multiple = 1.0  # Normal
            elif revenue_volatility <= 25:
                risk_multiple = 0.95  # Moderate risk discount
            else:
                risk_multiple = 0.9  # High volatility discount
            
            # Calculate adjusted P/E
            adjusted_pe = base_pe * growth_multiple * quality_multiple * risk_multiple
            
            # Cap P/E to reasonable ranges (Taiwan market context)
            adjusted_pe = max(6, min(adjusted_pe, 40))
            
            pe_value = eps * adjusted_pe
            return round(pe_value, 2)
        
        except:
            return 0
    
    def calculate_ddm_valuation(self, row: pd.Series) -> float:
        """DDM (Dividend Discount Model) using GoodInfo dividend data"""
        try:
            # Get dividend data from GoodInfo
            dividend = row.get('avg_dividend', 0)  # 現金股利合計
            eps = row.get('avg_eps', 0)
            roe = row.get('avg_roe', 0) / 100 if row.get('avg_roe', 0) > 0 else 0
            
            required_return = 0.08  # 8% required return for dividends
            
            # Handle non-dividend paying stocks
            if dividend <= 0 or eps <= 0:
                # Estimate potential dividend based on payout policy
                if eps > 0:
                    # Assume conservative 30% payout for non-dividend stocks
                    estimated_dividend = eps * 0.3
                    dividend = max(dividend, estimated_dividend)
                else:
                    return 0
            
            # Calculate payout ratio
            payout_ratio = min(dividend / eps, 1.0) if eps > 0 else 0.3
            
            # Calculate sustainable dividend growth rate
            # Growth = ROE × Retention Ratio
            retention_ratio = 1 - payout_ratio
            sustainable_growth = roe * retention_ratio
            
            # Cap growth rate to be conservative
            dividend_growth = min(sustainable_growth, 0.10)  # Max 10% dividend growth
            
            # Ensure growth rate is less than required return
            if dividend_growth >= required_return:
                dividend_growth = required_return * 0.8  # Conservative adjustment
            
            # DDM calculation based on growth profile
            if dividend_growth <= 0.02:  # Low/no growth - use simple DDM
                ddm_value = dividend / required_return
            else:
                # Gordon Growth Model: P = D1 / (r - g)
                next_year_dividend = dividend * (1 + dividend_growth)
                ddm_value = next_year_dividend / (required_return - dividend_growth)
            
            # Apply quality discount/premium based on dividend consistency
            dividend_consistency = row.get('dividend_consistency', 0.5)
            if dividend_consistency >= 0.9:
                consistency_multiple = 1.1  # Highly consistent
            elif dividend_consistency >= 0.7:
                consistency_multiple = 1.0  # Good consistency
            elif dividend_consistency >= 0.5:
                consistency_multiple = 0.95  # Fair consistency
            else:
                consistency_multiple = 0.9  # Poor consistency
            
            final_ddm_value = ddm_value * consistency_multiple
            return round(final_ddm_value, 2)
        
        except Exception as e:
            logger.debug(f"DDM calculation error: {e}")
            return 0
    
    def calculate_quality_score(self, row: pd.Series) -> float:
        """Calculate overall quality score (0-10) - existing implementation"""
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
        """Calculate safety margin - existing implementation"""
        if current_price <= 0 or intrinsic_value <= 0:
            return 0
        
        margin = (intrinsic_value - current_price) / current_price
        return round(margin, 3)
    
    def load_additional_data_from_raw_files(self, df: pd.DataFrame) -> pd.DataFrame:
        """Load additional data needed for NAV and DDM from raw files"""
        logger.info("📊 Loading additional data from raw CSV files...")
        
        # Try to load raw performance data for BPS
        raw_performance_file = self.input_dir.parent / 'stage1_raw' / 'raw_performance.csv'
        if raw_performance_file.exists():
            try:
                raw_perf = pd.read_csv(raw_performance_file)
                logger.info(f"   Loaded raw performance data: {len(raw_perf)} rows")
                
                # Get latest BPS for each stock
                bps_data = raw_perf.groupby('stock_code').agg({
                    'BPS(元)': 'last'  # Take most recent BPS value
                }).reset_index()
                
                # Merge BPS data
                df = df.merge(bps_data, on='stock_code', how='left')
                logger.info(f"   Added BPS data for {len(bps_data)} stocks")
                
            except Exception as e:
                logger.warning(f"   Could not load raw performance data: {e}")
        
        return df
    
    def run_pipeline(self) -> Dict:
        """Run enhanced pipeline with 5 valuation models"""
        
        # Load basic analysis
        input_file = self.input_dir / 'stock_analysis.csv'
        if not input_file.exists():
            click.echo("❌ No basic analysis file found. Run Stage 3 first.")
            return {'error': 'missing_input'}
        
        df = pd.read_csv(input_file)
        
        if df.empty:
            click.echo("❌ Empty analysis file")
            return {'error': 'empty_input'}
        
        logger.info(f"📊 Calculating enhanced analysis with 5 models for {len(df)} stocks...")
        
        # Load additional data for NAV and DDM
        df = self.load_additional_data_from_raw_files(df)
        
        # Ensure company_name column exists
        if 'company_name' not in df.columns:
            logger.warning("Company name column missing, using stock_code as fallback")
            df['company_name'] = df['stock_code']
        
        # Calculate all 5 valuation models
        logger.info("🧮 Calculating DCF valuations...")
        df['dcf_valuation'] = df.apply(self.calculate_dcf_valuation, axis=1)
        
        logger.info("🧮 Calculating Graham valuations...")
        df['graham_valuation'] = df.apply(self.calculate_graham_valuation, axis=1)
        
        logger.info("🧮 Calculating NAV valuations...")
        df['nav_valuation'] = df.apply(self.calculate_nav_valuation, axis=1)
        
        logger.info("🧮 Calculating P/E valuations...")
        df['pe_valuation'] = df.apply(self.calculate_pe_valuation, axis=1)
        
        logger.info("🧮 Calculating DDM valuations...")
        df['ddm_valuation'] = df.apply(self.calculate_ddm_valuation, axis=1)
        
        # Calculate five-model consensus
        logger.info("🎯 Calculating five-model consensus...")
        
        # Default weights (can be adjusted per stock type later)
        default_weights = {
            'dcf': 0.30,
            'graham': 0.15, 
            'nav': 0.20,
            'pe': 0.25,
            'ddm': 0.10
        }
        
        def calculate_weighted_consensus(row):
            values = {
                'dcf': row['dcf_valuation'],
                'graham': row['graham_valuation'],
                'nav': row['nav_valuation'],
                'pe': row['pe_valuation'],
                'ddm': row['ddm_valuation']
            }
            
            # Only include non-zero values in consensus
            valid_values = {k: v for k, v in values.items() if v > 0}
            
            if not valid_values:
                return 0
            
            # Recalculate weights for valid values only
            total_weight = sum(default_weights[k] for k in valid_values.keys())
            if total_weight == 0:
                return 0
            
            weighted_sum = sum(values[k] * default_weights[k] for k in valid_values.keys())
            return round(weighted_sum / total_weight, 2)
        
        df['five_model_consensus'] = df.apply(calculate_weighted_consensus, axis=1)
        
        # Keep original two-model consensus for comparison
        df['original_consensus'] = (df['dcf_valuation'] + df['graham_valuation']) / 2
        
        # Quality scoring
        logger.info("⭐ Calculating quality scores...")
        df['quality_score'] = df.apply(self.calculate_quality_score, axis=1)
        
        # Safety margins using five-model consensus
        logger.info("🛡️ Calculating safety margins...")
        df['safety_margin'] = df.apply(lambda row: self.calculate_safety_margin(
            row['five_model_consensus'], 100), axis=1)
        
        # Investment recommendations
        logger.info("💡 Generating recommendations...")
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
        
        # Rankings
        logger.info("📊 Calculating rankings...")
        df['quality_rank'] = df['quality_score'].rank(method='dense', ascending=False)
        df['value_rank'] = df['safety_margin'].rank(method='dense', ascending=False)
        df['overall_rank'] = ((df['quality_rank'] + df['value_rank']) / 2).rank(method='dense')
        
        # Add metadata
        df['enhanced_analysis_date'] = pd.Timestamp.now()
        df['analysis_version'] = '2.0.0'  # Updated version
        df['models_used'] = 5
        
        # Save enhanced analysis
        output_file = self.output_dir / 'enhanced_analysis.csv'
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        logger.info(f"💾 Saved enhanced analysis: {output_file}")
        
        # Generate summary statistics
        summary_stats = {
            'total_stocks': len(df),
            'strong_buy_count': len(df[df['recommendation'] == 'Strong Buy']),
            'buy_count': len(df[df['recommendation'] == 'Buy']),
            'avg_quality_score': df['quality_score'].mean(),
            'avg_safety_margin': df['safety_margin'].mean(),
            'models_implemented': 5,
            'avg_dcf_value': df['dcf_valuation'].mean(),
            'avg_graham_value': df['graham_valuation'].mean(),
            'avg_nav_value': df['nav_valuation'].mean(),
            'avg_pe_value': df['pe_valuation'].mean(),
            'avg_ddm_value': df['ddm_valuation'].mean(),
            'top_10_stocks': df.nsmallest(10, 'overall_rank')[['stock_code', 'company_name']].to_dict('records')
        }
        
        # Save summary
        summary_df = pd.DataFrame([{k: v for k, v in summary_stats.items() if k != 'top_10_stocks'}])
        summary_file = self.output_dir / 'analysis_summary.csv'
        summary_df.to_csv(summary_file, index=False)
        
        # Save top stocks
        top_stocks_df = pd.DataFrame(summary_stats['top_10_stocks'])
        top_stocks_file = self.output_dir / 'top_stocks.csv'
        top_stocks_df.to_csv(top_stocks_file, index=False)
        
        logger.info(f"📋 Five-Model Summary:")
        logger.info(f"   Strong Buy: {summary_stats['strong_buy_count']} stocks")
        logger.info(f"   Buy: {summary_stats['buy_count']} stocks") 
        logger.info(f"   Avg Quality Score: {summary_stats['avg_quality_score']:.1f}")
        logger.info(f"   Models: DCF={summary_stats['avg_dcf_value']:.1f}, Graham={summary_stats['avg_graham_value']:.1f}")
        logger.info(f"   Models: NAV={summary_stats['avg_nav_value']:.1f}, P/E={summary_stats['avg_pe_value']:.1f}, DDM={summary_stats['avg_ddm_value']:.1f}")
        
        return summary_stats

@click.command()
@click.option('--input-dir', default='data/stage3_analysis')
@click.option('--output-dir', default='data/stage4_enhanced')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def run_stage4_five_models(input_dir: str, output_dir: str, debug: bool):
    """
    Run Stage 4: Enhanced Analysis with Five Valuation Models
    
    🎯 NEW FEATURES:
    ✅ DCF + Graham (existing)
    ✅ NAV (Net Asset Value) using BPS + ROE
    ✅ P/E (Price-to-Earnings) with growth adjustments  
    ✅ DDM (Dividend Discount Model) using dividend data
    ✅ Five-model weighted consensus
    ✅ Enhanced rankings and recommendations
    """
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    pipeline = AdvancedAnalysisPipeline(input_dir, output_dir)
    stats = pipeline.run_pipeline()
    
    if 'error' in stats:
        click.echo(f"❌ Pipeline failed: {stats['error']}")
        return
    
    click.echo(f"✅ Five-model enhanced analysis completed:")
    click.echo(f"   Total stocks: {stats['total_stocks']}")
    click.echo(f"   Models implemented: {stats['models_implemented']}")
    click.echo(f"   Strong Buy: {stats['strong_buy_count']}")
    click.echo(f"   Buy: {stats['buy_count']}")
    click.echo(f"   Avg quality score: {stats['avg_quality_score']:.1f}")
    
    click.echo(f"\n📊 Average valuations by model:")
    click.echo(f"   DCF: {stats['avg_dcf_value']:.1f}")
    click.echo(f"   Graham: {stats['avg_graham_value']:.1f}")
    click.echo(f"   NAV: {stats['avg_nav_value']:.1f}")
    click.echo(f"   P/E: {stats['avg_pe_value']:.1f}")
    click.echo(f"   DDM: {stats['avg_ddm_value']:.1f}")
    
    if stats['top_10_stocks']:
        click.echo(f"\n🏆 Top 5 stocks:")
        for i, stock in enumerate(stats['top_10_stocks'][:5], 1):
            click.echo(f"   {i}. {stock['stock_code']} ({stock['company_name']})")
    
    click.echo(f"\n📂 Next steps:")
    click.echo(f"   1. Check enhanced analysis: {output_dir}/enhanced_analysis.csv")
    click.echo(f"   2. Run Stage 5: python -m src.pipelines.stage5_sheets_publisher")

if __name__ == '__main__':
    run_stage4_five_models()