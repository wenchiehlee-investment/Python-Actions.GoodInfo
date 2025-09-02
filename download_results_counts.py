#!/usr/bin/env python3
"""
Download Results Count Analyzer for GoodInfo Data Downloader

Scans download_results.csv files across all 9 data type folders and generates
comprehensive status reports with download statistics and timing information.

Usage:
    python download_results_counts.py [options]

Options:
    --output FILE     Save output to specific file (default: stdout)
    --format FORMAT   Output format: table|json (default: table)
    --detailed        Include additional metrics and timestamps
    --update-readme   Update README.md status section
    --help           Show this help message
"""

import os
import csv
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Data type to folder mapping based on GoodInfo project structure
FOLDER_MAPPING = {
    1: "DividendDetail",
    2: "BasicInfo",
    3: "StockDetail", 
    4: "StockBzPerformance",
    5: "ShowSaleMonChart",
    6: "EquityDistribution",
    7: "StockBzPerformance1",
    8: "ShowK_ChartFlow",
    9: "StockHisAnaQuar"
}

class DownloadStatsAnalyzer:
    """Analyzes download results across all GoodInfo data types."""
    
    def __init__(self):
        self.current_time = datetime.now()
    
    def safe_parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string with fallback for special values."""
        if not date_string or date_string.strip() in ['NOT_PROCESSED', 'NEVER', '']:
            return None
        
        try:
            # Handle various date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S']:
                try:
                    return datetime.strptime(date_string.strip(), fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def format_time_ago(self, time_diff: timedelta) -> str:
        """Convert timedelta to human-readable 'ago' format."""
        if time_diff.total_seconds() < 0:
            return "Future"
        
        days = time_diff.days
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60
        
        if days > 0:
            if hours > 0:
                return f"{days} days {hours} hours ago"
            else:
                return f"{days} days ago"
        elif hours > 0:
            if minutes > 0:
                return f"{hours} hours {minutes} minutes ago"
            else:
                return f"{hours} hours ago"
        elif minutes > 0:
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    def format_duration(self, time_diff: timedelta) -> str:
        """Convert timedelta to duration format."""
        if time_diff.total_seconds() <= 0:
            return "N/A"
        
        days = time_diff.days
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60
        
        if days > 0:
            if hours > 0:
                return f"{days} days {hours} hours"
            else:
                return f"{days} days"
        elif hours > 0:
            if minutes > 0:
                return f"{hours} hours {minutes} minutes"
            else:
                return f"{hours} hours"
        elif minutes > 0:
            return f"{minutes} minutes"
        else:
            return "< 1 minute"
    
    def analyze_csv(self, csv_path: str) -> Dict:
        """Analyze a single download_results.csv file."""
        default_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'updated_from_now': 'Never',
            'duration': 'N/A',
            'error': None
        }
        
        if not os.path.exists(csv_path):
            default_stats['error'] = 'File not found'
            return default_stats
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Required columns
                required_cols = ['filename', 'last_update_time', 'success', 'process_time']
                if not all(col in reader.fieldnames for col in required_cols):
                    default_stats['error'] = 'Invalid CSV format'
                    return default_stats
                
                rows = list(reader)
                
                if not rows:
                    return default_stats
                
                # Calculate basic statistics
                stats = {
                    'total': len(rows),
                    'success': sum(1 for row in rows if row['success'].lower() == 'true'),
                    'failed': sum(1 for row in rows if row['success'].lower() == 'false'),
                    'error': None
                }
                
                # Calculate time-based metrics
                process_times = []
                for row in rows:
                    time_parsed = self.safe_parse_date(row['process_time'])
                    if time_parsed:
                        process_times.append(time_parsed)
                
                if process_times:
                    # Updated from now (last processed time)
                    last_time = max(process_times)
                    time_diff = self.current_time - last_time
                    stats['updated_from_now'] = self.format_time_ago(time_diff)
                    
                    # Duration (time span from first to last processing)
                    if len(process_times) > 1:
                        first_time = min(process_times)
                        duration_diff = last_time - first_time
                        stats['duration'] = self.format_duration(duration_diff)
                    else:
                        stats['duration'] = "Single batch"
                else:
                    stats['updated_from_now'] = 'Never'
                    stats['duration'] = 'N/A'
                
                return stats
                
        except Exception as e:
            default_stats['error'] = f"Error reading file: {str(e)}"
            return default_stats
    
    def scan_all_folders(self) -> Dict[int, Dict]:
        """Scan all data type folders and analyze their CSV files."""
        results = {}
        
        for data_type, folder_name in FOLDER_MAPPING.items():
            csv_path = os.path.join(folder_name, 'download_results.csv')
            folder_exists = os.path.exists(folder_name)
            
            if not folder_exists:
                results[data_type] = {
                    'folder': folder_name,
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'updated_from_now': 'N/A',
                    'duration': 'N/A',
                    'error': 'Folder not found'
                }
            else:
                stats = self.analyze_csv(csv_path)
                stats['folder'] = folder_name
                results[data_type] = stats
        
        return results
    
    def generate_markdown_table(self, results: Dict[int, Dict]) -> str:
        """Generate markdown table from analysis results."""
        lines = [
            "|No| Folder |Total|Success| Failed|Updated from now|Duration|",
            "|--| -- |--|--|--|--|--|"
        ]
        
        for data_type in sorted(results.keys()):
            stats = results[data_type]
            
            # Handle error cases
            if stats.get('error'):
                total = success = failed = 0
                updated = 'N/A'
                duration = 'N/A'
            else:
                total = stats['total']
                success = stats['success']
                failed = stats['failed']
                updated = stats['updated_from_now']
                duration = stats['duration']
            
            line = f"|{data_type}| {stats['folder']} |{total}|{success}|{failed}|{updated}|{duration}|"
            lines.append(line)
        
        return "\n".join(lines)
    
    def generate_detailed_report(self, results: Dict[int, Dict]) -> str:
        """Generate detailed analysis report."""
        total_files = sum(r['total'] for r in results.values())
        total_success = sum(r['success'] for r in results.values())
        total_failed = sum(r['failed'] for r in results.values())
        
        success_rate = (total_success / total_files * 100) if total_files > 0 else 0
        
        report = [
            "# GoodInfo Download Status Report",
            f"*Generated: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}*\n",
            "## Summary",
            f"- **Total Files**: {total_files:,}",
            f"- **Successful**: {total_success:,} ({success_rate:.1f}%)",
            f"- **Failed**: {total_failed:,}",
            f"- **Data Types**: {len(results)} configured\n",
            "## Status by Data Type",
            self.generate_markdown_table(results),
            "\n## Notes",
            "- **Updated from now**: Time since last processing attempt",
            "- **Duration**: Time span from first to last processing in batch",
            "- **N/A**: No processing data available",
            "- **Never**: No successful processing attempts"
        ]
        
        # Add error summary if any
        errors = [(k, v['error']) for k, v in results.items() if v.get('error')]
        if errors:
            report.extend([
                "\n## Errors Detected",
                *[f"- **Type {k} ({FOLDER_MAPPING[k]})**: {error}" for k, error in errors]
            ])
        
        return "\n".join(report)
    
    def export_json(self, results: Dict[int, Dict]) -> str:
        """Export results as JSON."""
        export_data = {
            'generated_at': self.current_time.isoformat(),
            'summary': {
                'total_files': sum(r['total'] for r in results.values()),
                'total_success': sum(r['success'] for r in results.values()),
                'total_failed': sum(r['failed'] for r in results.values()),
                'data_types_configured': len(results)
            },
            'data_types': results
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze GoodInfo download results across all data types',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--output', '-o', 
                       help='Save output to file (default: stdout)')
    parser.add_argument('--format', '-f', 
                       choices=['table', 'json'], 
                       default='table',
                       help='Output format (default: table)')
    parser.add_argument('--detailed', '-d',
                       action='store_true',
                       help='Generate detailed report with summary')
    parser.add_argument('--update-readme',
                       action='store_true', 
                       help='Update README.md status section')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = DownloadStatsAnalyzer()
    
    print("Scanning download results across all data types...")
    results = analyzer.scan_all_folders()
    
    # Generate output based on format
    if args.format == 'json':
        output = analyzer.export_json(results)
    elif args.detailed:
        output = analyzer.generate_detailed_report(results)
    else:
        output = analyzer.generate_markdown_table(results)
    
    # Handle output destination
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Results saved to: {args.output}")
        except Exception as e:
            print(f"Error saving to file: {e}")
            print("\nOutput:")
            print(output)
    else:
        print(output)
    
    # Update README.md if requested
    if args.update_readme:
        try:
            update_readme_status(analyzer.generate_markdown_table(results))
            print("README.md status section updated successfully")
        except Exception as e:
            print(f"Error updating README.md: {e}")


def update_readme_status(table_content: str):
    """Update the status table in README.md."""
    readme_path = 'README.md'
    
    if not os.path.exists(readme_path):
        raise FileNotFoundError("README.md not found in current directory")
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the status table section
    status_start = content.find('## Status\n')
    if status_start == -1:
        raise ValueError("Status section not found in README.md")
    
    # Find the end of the status table
    next_section = content.find('\n## ', status_start + 1)
    if next_section == -1:
        next_section = len(content)
    
    # Generate current timestamp
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Replace the status section with timestamp
    new_content = (
        content[:status_start] +
        "## Status\n" +
        f"Update time: {current_time}\n\n" +
        table_content +
        "\n\n" +
        content[next_section:]
    )
    
    # Write back to file
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


if __name__ == '__main__':
    main()