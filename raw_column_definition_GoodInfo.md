---
source: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo/refs/heads/main/raw_column_definition.md
destination: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo.Analyzer/refs/heads/main/definitions/raw_column_definition_GoodInfo.md
---

# Raw CSV Column Definitions - GoodInfo.tw (Types 1-18)
## Based on Actual GoodInfo Excel File Structure Analysis

---

## raw_dividends.csv (Dividend Distribution and Yield Data)
**No:** 1
**Source:** `DividendDetail/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/StockDividendPolicy.asp?STOCK_ID={stock_id} 
**Extraction Strategy:** Handle multi-header table with merged cells

### Column Definitions:

| Column | Type | Description | Excel Source |
|--------|------|-------------|--------------|
| `股利_發放_期間` | string | Dividend payout period | Column A |
| `股利_所屬_期間` | string | Dividend fiscal period | Column B |
| `現金股利_盈餘` | float | Cash dividend from earnings | Column C |
| `現金股利_公積` | float | Cash dividend from capital surplus | Column D |
| `現金股利_合計` | float | Total cash dividend | Column E |
| `股票股利_盈餘` | float | Stock dividend from earnings | Column F |
| `股票股利_公積` | float | Stock dividend from capital surplus | Column G |
| `股票股利_合計` | float | Total stock dividend | Column H |
| `股利_合計` | float | Total dividend (cash + stock) | Column I |
| `填息_花費_日數` | int | Ex-dividend recovery days | Column K |
| `填權_花費_日數` | int | Ex-rights recovery days | Column L |
| `股價_年度` | string | Stock price reference year | Column M |
| `現金殖利率_除息前_價格` | float | Dividend yield at pre-ex-dividend price | Column N |
| `現金殖利率_除息前_利率` | float | Dividend yield percentage at pre-ex-dividend | Column O |
| `現金殖利率_年均價_價格` | float | Dividend yield at annual average price | Column P |
| `現金殖利率_年均價_利率` | float | Dividend yield percentage at annual average | Column Q |
| `現金殖利率_成交價_價格` | float | Dividend yield at trading price | Column R |
| `現金殖利率_成交價_利率` | float | Dividend yield percentage at trading price | Column S |
| `現金殖利率_最高價_價格` | float | Dividend yield at highest price | Column T |
| `現金殖利率_最高價_利率` | float | Dividend yield percentage at highest | Column U |
| `現金殖利率_最低價_價格` | float | Dividend yield at lowest price | Column V |
| `現金殖利率_最低價_利率` | float | Dividend yield percentage at lowest | Column W |

---

## raw_performance.csv (Annual Financial Performance)
**No:** 4
**Source:** `StockBzPerformance/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}

### Column Definitions:

| Column | Type | Description | Excel Source |
|--------|------|-------------|--------------|
| `年度` | string | Financial year/quarter | Column A |
| `股本_億` | float | Share capital (hundred million NT$) | Column B |
| `財報_評分` | int | Financial report score | Column C |
| `年度股價_元_收盤` | float | Year-end closing price | Column D |
| `年度股價_元_平均` | float | Average stock price | Column E |
| `年度股價_元_漲跌` | float | Stock price change (NT$) | Column F |
| `年度股價_元_漲跌_pct` | float | Stock price change (%) | Column G |
| `獲利金額_億_營業_收入` | float | Operating revenue (hundred million NT$) | Column H |
| `獲利金額_億_營業_毛利` | float | Gross profit (hundred million NT$) | Column I |
| `獲利金額_億_營業_利益` | float | Operating profit (hundred million NT$) | Column J |
| `獲利金額_億_業外_損益` | float | Non-operating income (hundred million NT$) | Column K |
| `獲利金額_億_稅後_淨利` | float | Net income after tax (hundred million NT$) | Column L |
| `獲利率_pct_營業_毛利` | float | Gross margin (%) | Column M |
| `獲利率_pct_營業_利益` | float | Operating margin (%) | Column N |
| `獲利率_pct_業外_損益` | float | Non-operating margin (%) | Column O |
| `獲利率_pct_稅後_淨利` | float | Net margin (%) | Column P |
| `roe_pct` | float | Return on equity (%) | Column Q |
| `roa_pct` | float | Return on assets (%) | Column R |
| `eps_元_稅後_eps` | float | Earnings per share (NT$) | Column S |
| `eps_元_年增_元` | float | EPS change from previous year | Column T |
| `bps_元` | float | Book value per share (NT$) | Column U |

---

## raw_revenue.csv (Monthly Revenue and Stock Price Data)
**No:** 5
**Source:** `ShowSaleMonChart/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/ShowSaleMonChart.asp?STOCK_ID={stock_id}

### Column Definitions:

| Column | Type | Description | Excel Source |
|--------|------|-------------|--------------|
| `月別` | string | Month period (YYYY/MM) | Column A |
| `當月股價_開盤` | float | Monthly stock price - Open | Column B |
| `當月股價_收盤` | float | Monthly stock price - Close | Column C |
| `當月股價_最高` | float | Monthly stock price - High | Column D |
| `當月股價_最低` | float | Monthly stock price - Low | Column E |
| `當月股價_漲跌_元` | float | Monthly price change (NT$) | Column F |
| `當月股價_漲跌_pct` | float | Monthly price change (%) | Column G |
| `營業收入_營收_億` | float | Operating revenue (hundred million NT$) | Column H |
| `營業收入_月增_pct` | float | Operating revenue monthly change (%) | Column I |
| `營業收入_年增_pct` | float | Operating revenue yearly change (%) | Column J |
| `營業收入_累計_億` | float | Operating revenue cumulative (hundred million NT$) | Column K |
| `營業收入_累計年增_pct` | float | Operating revenue cumulative YoY change (%) | Column L |
| `合併營業收入_營收_億` | float | Consolidated revenue (hundred million NT$) | Column M |
| `合併營業收入_月增_pct` | float | Consolidated revenue monthly change (%) | Column N |
| `合併營業收入_年增_pct` | float | Consolidated revenue yearly change (%) | Column O |
| `合併營業收入_累計_億` | float | Consolidated revenue cumulative (hundred million NT$) | Column P |
| `合併營業收入_累計年增_pct` | float | Consolidated revenue cumulative YoY change (%) | Column Q |

---

## raw_performance1.csv (Quarterly Performance Detail)
**No:** 7
**Source:** `StockBzPerformance1/*.xls*`

### Column Definitions:

| Column | Type | Description | Excel Source |
|--------|------|-------------|--------------|
| `季度` | string | Quarter period (YYYY/Q#) | Column A |
| `股本_億` | float | Share capital (hundred million NT$) | Column B |
| `財報_評分` | int | Financial report score | Column C |
| `季度股價_元_收盤` | float | Quarterly closing price | Column D |
| `季度股價_元_平均` | float | Quarterly average price | Column E |
| `季度股價_元_漲跌` | float | Quarterly price change (NT$) | Column F |
| `季度股價_元_漲跌_pct` | float | Quarterly price change (%) | Column G |
| `獲利金額_億_營業_收入` | float | Operating revenue (hundred million NT$) | Column H |
| `獲利金額_億_營業_毛利` | float | Gross profit (hundred million NT$) | Column I |
| `獲利金額_億_營業_利益` | float | Operating profit (hundred million NT$) | Column J |
| `獲利金額_億_業外_損益` | float | Non-operating income (hundred million NT$) | Column K |
| `獲利金額_億_稅後_淨利` | float | Net income after tax (hundred million NT$) | Column L |
| `獲利率_pct_營業_毛利` | float | Gross margin (%) | Column M |
| `獲利率_pct_營業_利益` | float | Operating margin (%) | Column N |
| `獲利率_pct_業外_損益` | float | Non-operating margin (%) | Column O |
| `獲利率_pct_稅後_淨利` | float | Net margin (%) | Column P |
| `單季_roe_pct` | float | Quarterly ROE (%) | Column Q |
| `eps_元_稅後_eps` | float | Earnings per share after tax (NT$) | Column U |
| `bps_元` | float | Book value per share (NT$) | Column W |

---

## raw_fin_ratio_quarter.csv (Quarterly Financial Ratio Analysis)
**No:** 16
**Source:** `StockFinDetail/*.xls*`

### Column Definitions (Partial - Most Used):

| Column | Type | Description |
|--------|------|-------------|
| `季度` | string | Quarter identifier (YYYYQn) |
| `營業毛利率` | float | Gross margin (%) |
| `營業利益率` | float | Operating margin (%) |
| `稅後淨利率` | float | After-tax net margin (%) |
| `每股稅後盈餘 (元)` | float | EPS after tax (NT$) |
| `股東權益報酬率 (當季)` | float | ROE (quarter) (%) |
| `資產報酬率 (當季)` | float | ROA (quarter) (%) |
| `負債總額 (%)` | float | Total liabilities % of total assets |
| `每股自由現金流量 (元)` | float | Free CF per share (NT$) |

---

## raw_margin_daily.csv (Daily Margin Balance Details)
**No:** 13
**Source:** `ShowMarginChart/*.xls*`

### Column Definitions:

| Column | Type | Description |
|--------|------|-------------|
| `期別` | string | Trading date (YY/MM/DD) |
| `收盤_價格_元` | float | Daily closing price |
| `融資_餘額_張` | int | Margin balance |
| `融券_餘額_張` | int | Short balance |
| `券資比_pct` | float | Short to margin ratio percentage |

*(Note: Types 8, 9, 10, 11, 12, 14, 15, 17, 18 also follow similar systematic naming rules)*
