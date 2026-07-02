# POC Scenario: TrailPeak Outfitters Monthly P&L and Profit Drivers

All company names, people, numbers, and events in this dataset are fictional and synthetically generated (`generate_data.py`, seeded, reproducible). Nothing here derives from any client engagement.

## The company

**TrailPeak Outfitters** is a specialty outdoor gear retailer: 12 stores across 4 US regions (Mountain, Pacific, Southwest, Midwest), in three formats (3 Flagship, 6 Standard, 3 Compact). Revenue comes from in-store retail, online orders fulfilled by stores, and a service and repairs desk. The business is strongly seasonal: summer camping season and the December holiday peak.

## The business problem

The CFO, **Maria Chen** (fictional), closes the books monthly. Leadership currently receives the P&L as an emailed Excel file about 10 days after close: no design, no interactivity, no drill. Store managers never see their own P&L at all. Finance wants one designed, self-serve Power BI report that answers three questions:

1. **How did we do?** A properly formatted P&L statement: indented line items, Actual, Budget, Variance, Variance %, with Gross Profit, EBITDA, and Operating Profit subtotal rows. Finance must be able to pull the numbers to Excel.
2. **How are we trending?** Period analysis: month over month, year over year, YTD vs budget, with the current closed month (June 2026) as the anchor.
3. **What drives the result?** Pareto analysis: which products carry revenue (the 80/20 question), which stores concentrate profit, and which cost lines concentrate spend.

## Why this scenario fits the code-first workflow

| Report element | Workflow role |
|---|---|
| P&L statement table (indented lines, subtotals, variance columns) | The classic "native visuals cannot do this nicely" visual. HTML+DAX prototype first, then the Deneb rebuild. Finance's Excel-export requirement is the migration trigger. |
| Pareto chart (ranked bars + cumulative % line + 80% threshold) | Native Power BI has no good Pareto visual. Flagship Deneb rebuild; cumulative % computed in DAX per the aggregate-in-DAX rule. |
| KPI strip (Revenue, GP %, EBITDA, Operating Profit vs budget) | SVG DAX measures in native card visuals: the chrome layer. |
| Trend visuals (revenue and profit by month, actual vs budget vs prior year) | Deneb (cross-filtering with the rest of the page). |
| Canvas background (header band, zone containers, branding) | Agent-generated HTML/SVG rendered to a 1280x720 PNG. |
| Slicers (month, region, store) | Native slicers. Native-first rule applies. |

## Planted anomalies (actuals only; the budget stays clean)

These make variance analysis and screenshots interesting. Each should be findable in the report.

| ID | What | Where it surfaces |
|---|---|---|
| A1 | Denver Flagship rent +28% from Feb 2026 (lease renewal, not budgeted) | Occupancy variance, Denver operating margin dip |
| A2 | Pacific region digital advertising +40% in Apr to Jun 2026 (campaign overspend) | Marketing variance in Q2 2026, Pacific region filter |
| A3 | Boise revenue run-rate x0.88 through 2026 (underperforming store) | Persistent unfavorable revenue variance for Boise in 2026 |
| A4 | Portland inventory shrinkage x4.5 in Nov 2025 (count incident) | One-month COGS spike, GP% dip for Portland |

## Headline facts (from generation validation)

- Actuals: Jan 2024 to Jun 2026 (30 closed months). Budget: full 36 months through Dec 2026.
- Jun 2026 company month: revenue $4.64M, GP 48.7%, EBITDA 14.2%, operating profit 12.7%.
- FY2024 revenue $43.1M, FY2025 $46.6M (+8.0% YoY).
- Pareto concentration: the top 24 of 120 SKUs (20%) carry 77.2% of product revenue.
- Product sales reconcile to the P&L revenue and product cost lines to the cent, so the Pareto page and the P&L page always agree.

## Report page plan (wireframe input for Step 1)

**Page 1: P&L Statement.** Header band; KPI strip (4 cards); the P&L statement table (main zone); month/region/store slicers (sidebar); footer with data-refreshed timestamp.

**Page 2: Drivers.** Header band; Pareto chart of product revenue (main zone, with category cross-filter); store profit contribution bar; period trend (revenue and operating profit by month, actual vs budget vs PY); same slicer sidebar.
