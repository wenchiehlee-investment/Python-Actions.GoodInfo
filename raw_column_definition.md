---
source: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo/refs/heads/main/raw_column_definition.md
destination: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo.Analyzer/refs/heads/main/raw_column_definition.md
---

# Raw CSV Column Definitions - Python-Actions.GoodInfo
## GoodInfo.tw Excel Data Source (Types 1-18)

This repository is the **primary source** for GoodInfo.tw Excel files that get processed by Python-Actions.GoodInfo.Analyzer.

### Data Source Folders:

| Type | Folder | Description |
|------|--------|-------------|
| 1 | `DividendDetail/` | Dividend distribution and yield data |
| 4 | `StockBzPerformance/` | Annual financial performance |
| 5 | `ShowSaleMonChart/` | Monthly revenue and stock price |
| 6 | `EquityDistribution/` | Shareholding structure distribution |
| 7 | `StockBzPerformance1/` | Quarterly performance detail |
| 8 | `ShowK_ChartFlow/` | Weekly P/E flow analysis |
| 9 | `StockHisAnaQuar/` | Quarterly historical analysis |
| 10 | `EquityDistributionClassHis/` | Weekly equity distribution |
| 11 | `WeeklyTradingData/` | Weekly institutional flow & margin |
| 12 | `ShowMonthlyK_ChartFlow/` | Monthly P/E long-term valuation |
| 13 | `ShowMarginChart/` | Daily margin balance |
| 14 | `ShowMarginChartWeek/` | Weekly margin balance |
| 15 | `ShowMarginChartMonth/` | Monthly margin balance |
| 16 | `StockFinDetail/` | Quarterly financial ratio analysis |
| 17 | `ShowWeeklyK_ChartFlow/` | Weekly K-Line Chart Flow |
| 18 | `ShowDailyK_ChartFlow/` | Daily K-Line Chart Flow |

### Column Definitions:

For detailed column definitions of each type, see the consolidated documentation at:
- **Destination:** [Python-Actions.GoodInfo.Analyzer/raw_column_definition.md](https://github.com/wenchiehlee-investment/Python-Actions.GoodInfo.Analyzer/blob/main/raw_column_definition.md)

### Processing Pipeline:

```
Python-Actions.GoodInfo (Excel files)
    ↓ Stage 1: Excel to CSV extraction
Python-Actions.GoodInfo.Analyzer (raw_*.csv)
    ↓ Stage 2: Data cleaning
Python-Actions.GoodInfo.Analyzer (cleaned_*.csv)
```
