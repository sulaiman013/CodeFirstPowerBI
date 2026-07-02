# TrailPeak Outfitters POC: Star Schema Data Model

Synthetic dataset for the code-first Power BI report design blog POC. See `SCENARIO.md` for the business story. Regenerate any time with `python generate_data.py` (deterministic, seeded).

**The PBIP at `Report/` is already fully wired**: relationships, date table marking, statement layout, and all 34 measures were authored directly in TMDL and validated (pbip-validator: zero errors). Open `Report/Report.pbip` in Power BI Desktop and hit Refresh. Auto date/time is disabled and implicit measures are discouraged, deliberately.

## Files (`data/`)

| File | Grain | Rows |
|---|---|---|
| `dim_date.csv` | one row per day, 2024-01-01 to 2026-12-31 | 1,096 |
| `dim_store.csv` | one row per store | 12 |
| `dim_account.csv` | one row per P&L leaf account (the chart of accounts) | 20 |
| `dim_product.csv` | one row per SKU | 120 |
| `dim_pnl_layout.csv` | one row per P&L statement display line (details, groups, subtotals, totals) | 18 |
| `bridge_pnl_line_account.csv` | statement line to account mapping | 84 |
| `fact_pnl_actuals.csv` | month x store x account (Jan 2024 to Jun 2026) | 7,200 |
| `fact_pnl_budget.csv` | month x store x account (Jan 2024 to Dec 2026) | 8,640 |
| `fact_sales.csv` | month x store x product (Jan 2024 to Jun 2026) | 40,237 |

## Star schema

Relationships (all one-to-many, single direction, dimension filters fact):

| From (one) | To (many) | Note |
|---|---|---|
| `dim_date[Date]` | all three facts `[Date]` | facts carry first-of-month dates; dim_date is marked as date table |
| `dim_store[StoreKey]` | all three facts `[StoreKey]` | |
| `dim_account[AccountKey]` | both P&L facts `[AccountKey]` | |
| `dim_product[ProductKey]` | `fact_sales[ProductKey]` | |
| `dim_pnl_layout[LineKey]` | `bridge_pnl_line_account[LineKey]` | bridge is NOT related to dim_account; [P&L Line Value] resolves accounts via TREATAS |

Model conventions already applied in TMDL:
- Amounts in both P&L facts are **stored positive**; `dim_account[Sign]` (+1 revenue, -1 costs) applies the sign inside measures.
- Sort-by columns: `Account` by `StatementSort`, `Quarter` by `YearQuarterKey`, `MonthName`/`MonthShort` by `MonthNo`, `YearMonthLabel` by `YearMonthKey`, `WeekdayName` by `WeekdayNo`, `LineLabel` by `LineKey`.
- `dim_date[IsClosed]` flags dates up to the last closed month (Jun 2026). Budget exists through Dec 2026 on purpose.
- Auto date/time is off; no LocalDateTables. `dim_date` carries `dataCategory: Time` with `Date` as key.

## The P&L statement pieces

- **Chart of accounts:** `dim_account` (20 leaf accounts: 3 Revenue, 3 COGS, 13 OpEx across Payroll/Occupancy/Marketing/Selling/Admin, 1 Depreciation), with `Category`, `Subcategory`, `Sign`, `StatementSort`.
- **Statement layout:** `dim_pnl_layout` holds the 18 display rows of the statement (line label, RowType Detail/Group/Subtotal/Total, Indent, IsBold), including computed lines like Total Revenue, Gross Profit, EBITDA, and Operating Profit.
- **Bridge:** `bridge_pnl_line_account` maps every display line to its constituent accounts (subtotal lines map to many accounts). The `[P&L Line Value]` measure resolves the mapping with TREATAS, so one Deneb/matrix visual renders the entire indented statement by putting `LineLabel` on rows and the Line measures on values.

## Measures (already in the model, `_Measures` table)

Organized in display folders. The important design decisions, all fixes from the independent model audit:

1. **Statement subtotals are immune to cross-filtering:** `Total Revenue`, `Total COGS`, `Total OpEx`, `Operating Profit` use `REMOVEFILTERS(dim_account)`, so clicking one expense line elsewhere cannot blank the KPI strip or mislabel a lone account as EBITDA.
2. **Closed-period guard:** `Budget (Closed)` restricts budget to dates up to `[Last Closed Date]`, and `Variance` blanks for unclosed months, so Jul to Dec 2026 never shows fake unfavorable variance. Year-level growth uses `YTD YoY %` (YTD vs PYTD) for like-for-like partial-year comparison.
3. **Pareto is tie-safe and ghost-free:** `Product Rank` uses skip ranking with a ProductKey tiebreak and blanks when a product has no sales; `Cumulative Revenue` is a running total over the same tiebroken key, so the cumulative % line is monotonic in every filter context.
4. **MoM, YoY, YTD** all present (`DATEADD` for MoM so it works at any grain).
5. **Variance sign convention:** with signed amounts, positive variance is favorable for both revenue and expense lines; `Variance %` divides by `ABS(budget)`.

Folders: 1. Base, 2. Statement, 3. Variance, 4. Time Intelligence, 5. Pareto, 6. Statement Lines, 7. Chrome, 8. HTML Prototypes.

## Step 3 prototypes (`prototypes/` + folder "8. HTML Prototypes" in the model)

Two full-page HTML/SVG DAX measures, the blog's prototype stage. Both are already in the model; drop each into an **HTML Content (lite)** visual's Content field well. Both respond to date/region/store slicers and carry the design tokens (TrailPeak green #2d6a4f, amber #d97706, slate text).

- **`HTML P&L Statement`** (`prototypes/html_pnl_statement.dax`): the complete statement page. Iterates `dim_pnl_layout` so all 18 lines render with indents, bold subtotal/total rows (Gross Profit, EBITDA, Operating Profit highlighted), Actual / Budget / Variance / Var % columns, color-coded favorable/unfavorable, finance-style parentheses for negatives, dash for unclosed periods, dynamic period and scope header.
- **`HTML Pareto Analysis`** (`prototypes/html_pareto_analysis.dax`): the complete Pareto page as inline SVG. Top-20 ranked revenue bars (vital few inside the 80% band in green, rest gray), amber cumulative % line with dots and labels, dashed 80% threshold, right percent axis, rotated product labels, and a dynamic insight chip ("N of M products drive 80% of revenue"). Uses the tie-safe rank and monotonic cumulative measures.

Reviewed by the svg-reviewer agent; fixes applied for label clipping (left pad 84), truncation length, blank guards on every cell, clamped period labels, and quoted font-family. Reminder per the blog's decision rule: these prototypes are design artifacts; the production rebuilds ship in Deneb.

## Planted anomalies (verified detectable by independent audit)

| ID | What | Measured vs budget |
|---|---|---|
| A1 | Denver Flagship rent, lease renewal Feb 2026 | exactly +28% Feb to Jun 2026 |
| A2 | Pacific digital advertising campaign overspend | +40.7% in Q2 2026 |
| A3 | Boise underperformance in 2026 | -11.4% revenue H1 2026 |
| A4 | Portland shrinkage count incident | 4.24x in Nov 2025 |

## Notes

- CSV paths in the M partitions are absolute to this machine (`...\POC\data\`). If the folder moves, update the paths in `Report.SemanticModel/definition/tables/*.tmdl`.
- If Power BI Desktop is open on this PBIP while files are edited on disk, close and reopen it; Desktop can overwrite disk edits on save.
- Recommended `.gitignore` if this goes in a repo: `**/.pbi/localSettings.json` and `**/.pbi/cache.abf`.
