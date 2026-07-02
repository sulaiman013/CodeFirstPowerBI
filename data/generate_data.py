"""
TrailPeak Outfitters: synthetic star-schema dataset for the code-first Power BI POC.

Generates a fully consistent P&L + product sales model:
  dims:  dim_date, dim_store, dim_account, dim_product
  facts: fact_pnl_actuals (month x store x account, Jan 2024 - Jun 2026)
         fact_pnl_budget  (month x store x account, Jan 2024 - Dec 2026)
         fact_sales       (month x store x product, Jan 2024 - Jun 2026)

Consistency guarantees:
  - fact_sales revenue == P&L accounts 4000 + 4100 per store-month (to the cent)
  - fact_sales cost    == P&L account 5000 per store-month (to the cent)
  - engineered Pareto: ~20% of SKUs carry ~75-80% of product revenue

Planted anomalies (actuals only, budget stays clean):
  A1: Denver Flagship rent +28% from Feb 2026 (lease renewal)
  A2: Pacific region digital advertising +40% in Apr-Jun 2026 (campaign overspend)
  A3: Boise revenue run-rate x0.88 through 2026 (underperforming store)
  A4: Portland inventory shrinkage x4.5 in Nov 2025 (count incident)

Deterministic: seeded RNG, safe to re-run.
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(BASE_DIR, exist_ok=True)

ACTUALS_MONTHS = [(y, m) for y in (2024, 2025, 2026) for m in range(1, 13)
                  if not (y == 2026 and m > 6)]
BUDGET_MONTHS = [(y, m) for y in (2024, 2025, 2026) for m in range(1, 13)]

# ---------------------------------------------------------------- dim_date
DATE_START = date(2024, 1, 1)
DATE_END = date(2026, 12, 31)
LAST_CLOSED = date(2026, 6, 30)  # last closed accounting month

def build_dim_date():
    rows = []
    d = DATE_START
    while d <= DATE_END:
        q = (d.month - 1) // 3 + 1
        rows.append({
            "Date": d.isoformat(),
            "Year": d.year,
            "QuarterNo": q,
            "Quarter": f"Q{q} {d.year}",
            "YearQuarterKey": d.year * 10 + q,
            "MonthNo": d.month,
            "MonthName": d.strftime("%B"),
            "MonthShort": d.strftime("%b"),
            "YearMonthKey": d.year * 100 + d.month,
            "YearMonthLabel": d.strftime("%b %Y"),
            "WeekdayNo": d.isoweekday(),
            "WeekdayName": d.strftime("%A"),
            "IsWeekend": 1 if d.isoweekday() >= 6 else 0,
            "IsClosed": 1 if d <= LAST_CLOSED else 0,
        })
        d += timedelta(days=1)
    return rows

# ---------------------------------------------------------------- dim_store
STORES = [
    # key, code, name, city, state, region, tier, sqft, open
    (1,  "DEN01", "Denver Flagship",   "Denver",        "CO", "Mountain",  "Flagship", 14500, "2018-03-15"),
    (2,  "BLD01", "Boulder",           "Boulder",       "CO", "Mountain",  "Standard",  8200, "2019-06-01"),
    (3,  "SLC01", "Salt Lake City",    "Salt Lake City","UT", "Mountain",  "Standard",  7900, "2019-09-12"),
    (4,  "BOI01", "Boise",             "Boise",         "ID", "Mountain",  "Compact",   4600, "2021-04-20"),
    (5,  "SEA01", "Seattle Flagship",  "Seattle",       "WA", "Pacific",   "Flagship", 13800, "2017-11-08"),
    (6,  "PDX01", "Portland",          "Portland",      "OR", "Pacific",   "Standard",  8500, "2018-08-22"),
    (7,  "SAC01", "Sacramento",        "Sacramento",    "CA", "Pacific",   "Compact",   4900, "2022-02-14"),
    (8,  "AUS01", "Austin",            "Austin",        "TX", "Southwest", "Standard",  8100, "2020-10-05"),
    (9,  "PHX01", "Phoenix",           "Phoenix",       "AZ", "Southwest", "Standard",  7700, "2020-03-18"),
    (10, "ABQ01", "Albuquerque",       "Albuquerque",   "NM", "Southwest", "Compact",   4400, "2022-07-11"),
    (11, "CHI01", "Chicago Flagship",  "Chicago",       "IL", "Midwest",   "Flagship", 13200, "2018-05-30"),
    (12, "MSP01", "Minneapolis",       "Minneapolis",   "MN", "Midwest",   "Standard",  8000, "2019-11-25"),
]
TIER_BASE_REV = {"Flagship": 400_000.0, "Standard": 250_000.0, "Compact": 145_000.0}
TIER_ONLINE_SHARE = {"Flagship": 0.24, "Standard": 0.21, "Compact": 0.18}
TIER_PAYROLL_BASE = {"Flagship": 52_000.0, "Standard": 34_000.0, "Compact": 21_000.0}
TIER_INSURANCE = {"Flagship": 2_800.0, "Standard": 1_900.0, "Compact": 1_200.0}
TIER_DEPRECIATION = {"Flagship": 9_500.0, "Standard": 5_200.0, "Compact": 2_800.0}
TIER_EVENT_SCALE = {"Flagship": 1.5, "Standard": 1.0, "Compact": 0.6}

# fixed per-store run-rate factors (known to budget planners, so shared)
STORE_FACTOR = {s[0]: round(random.uniform(0.94, 1.06), 4) for s in STORES}
STORE_RENT_FACTOR = {s[0]: round(random.uniform(0.90, 1.15), 4) for s in STORES}
STORE_ONLINE_NUDGE = {s[0]: round(random.uniform(-0.02, 0.02), 4) for s in STORES}

# ---------------------------------------------------------------- dim_account
ACCOUNTS = [
    # key, account, category, subcategory, sign, sort
    (4000, "Retail Sales",             "Revenue",            "Retail",    1, 10),
    (4100, "Online Sales",             "Revenue",            "Online",    1, 20),
    (4200, "Services & Repairs",       "Revenue",            "Services",  1, 30),
    (5000, "Product Cost",             "Cost of Goods Sold", "Product",  -1, 40),
    (5100, "Freight In",               "Cost of Goods Sold", "Freight",  -1, 50),
    (5200, "Inventory Shrinkage",      "Cost of Goods Sold", "Shrinkage",-1, 60),
    (6000, "Salaries & Wages",         "Operating Expenses", "Payroll",  -1, 70),
    (6010, "Payroll Taxes & Benefits", "Operating Expenses", "Payroll",  -1, 80),
    (6100, "Rent",                     "Operating Expenses", "Occupancy",-1, 90),
    (6110, "Utilities",                "Operating Expenses", "Occupancy",-1, 100),
    (6120, "Repairs & Maintenance",    "Operating Expenses", "Occupancy",-1, 110),
    (6200, "Digital Advertising",      "Operating Expenses", "Marketing",-1, 120),
    (6210, "Events & Sponsorships",    "Operating Expenses", "Marketing",-1, 130),
    (6300, "Card Processing Fees",     "Operating Expenses", "Selling",  -1, 140),
    (6310, "Packaging & Supplies",     "Operating Expenses", "Selling",  -1, 150),
    (6400, "Insurance",                "Operating Expenses", "Admin",    -1, 160),
    (6410, "Software & Subscriptions", "Operating Expenses", "Admin",    -1, 170),
    (6420, "Professional Fees",        "Operating Expenses", "Admin",    -1, 180),
    (6430, "Office & Miscellaneous",   "Operating Expenses", "Admin",    -1, 190),
    (7000, "Depreciation",             "Depreciation",       "Depreciation", -1, 200),
]

# ------------------------------------------------- P&L statement layout
# Display rows for the statement visual: details, groups, and computed
# subtotal/total lines, each mapped to its constituent accounts via the bridge.
PNL_LAYOUT = [
    # key, label, rowtype, indent, bold
    (10,  "Retail Sales",              "Detail",   1, 0),
    (20,  "Online Sales",              "Detail",   1, 0),
    (30,  "Services & Repairs",        "Detail",   1, 0),
    (40,  "Total Revenue",             "Subtotal", 0, 1),
    (50,  "Product Cost",              "Detail",   1, 0),
    (60,  "Freight In",                "Detail",   1, 0),
    (70,  "Inventory Shrinkage",       "Detail",   1, 0),
    (80,  "Total Cost of Goods Sold",  "Subtotal", 0, 1),
    (90,  "Gross Profit",              "Total",    0, 1),
    (100, "Payroll",                   "Group",    1, 0),
    (110, "Occupancy",                 "Group",    1, 0),
    (120, "Marketing",                 "Group",    1, 0),
    (130, "Selling",                   "Group",    1, 0),
    (140, "Admin",                     "Group",    1, 0),
    (150, "Total Operating Expenses",  "Subtotal", 0, 1),
    (160, "EBITDA",                    "Total",    0, 1),
    (170, "Depreciation",              "Detail",   1, 0),
    (180, "Operating Profit",          "Total",    0, 1),
]
REVENUE_ACCTS = [4000, 4100, 4200]
COGS_ACCTS = [5000, 5100, 5200]
OPEX_ACCTS = [6000, 6010, 6100, 6110, 6120, 6200, 6210, 6300, 6310, 6400, 6410, 6420, 6430]
PNL_BRIDGE = {
    10: [4000], 20: [4100], 30: [4200],
    40: REVENUE_ACCTS,
    50: [5000], 60: [5100], 70: [5200],
    80: COGS_ACCTS,
    90: REVENUE_ACCTS + COGS_ACCTS,
    100: [6000, 6010],
    110: [6100, 6110, 6120],
    120: [6200, 6210],
    130: [6300, 6310],
    140: [6400, 6410, 6420, 6430],
    150: OPEX_ACCTS,
    160: REVENUE_ACCTS + COGS_ACCTS + OPEX_ACCTS,
    170: [7000],
    180: REVENUE_ACCTS + COGS_ACCTS + OPEX_ACCTS + [7000],
}

# ---------------------------------------------------------------- dim_product
CATEGORY_SPECS = {
    # category: (count, price_lo, price_hi, subcats)
    "Apparel":          (30,  35, 220, ["Jackets", "Baselayers", "Pants", "Fleece"]),
    "Footwear":         (20,  90, 320, ["Hiking Boots", "Trail Runners", "Approach Shoes"]),
    "Camping & Hiking": (25,  25, 600, ["Tents", "Sleeping Bags", "Packs", "Stoves"]),
    "Climbing":         (15,  20, 450, ["Harnesses", "Ropes", "Protection", "Shoes"]),
    "Winter Sports":    (15, 120, 800, ["Skis", "Snowboards", "Avalanche Safety"]),
    "Accessories":      (15,  10, 120, ["Bottles", "Headlamps", "Navigation", "Socks"]),
}
ADJ = ["Summit", "Ridgeline", "Granite", "Alpine", "Basecamp", "Cascade", "Timber",
       "Boulder", "Glacier", "Canyon", "Trailhead", "Peakline", "Northwind", "Ember",
       "Switchback", "Highline", "Stonefall", "Meridian", "Compass", "Latitude",
       "Drift", "Cornice", "Tundra", "Juniper", "Falcon", "Osprey", "Cinder",
       "Quartz", "Sierra", "Vista"]
NOUN = {
    "Apparel": ["Shell Jacket", "Down Parka", "Merino Baselayer", "Hiking Pants",
                "Grid Fleece", "Rain Jacket", "Insulated Vest", "Softshell"],
    "Footwear": ["Hiking Boot", "Trail Runner", "Approach Shoe", "Winter Boot",
                 "Mid GTX Boot"],
    "Camping & Hiking": ["2P Tent", "4P Tent", "20F Sleeping Bag", "0F Sleeping Bag",
                         "45L Pack", "65L Pack", "Canister Stove", "Sleeping Pad"],
    "Climbing": ["Harness", "9.8mm Rope", "Cam Set", "Quickdraw Pack",
                 "Climbing Shoe", "Chalk Bag", "Belay Device"],
    "Winter Sports": ["All-Mountain Ski", "Touring Ski", "Snowboard", "Avalanche Beacon",
                      "Snow Shovel", "Climbing Skins"],
    "Accessories": ["Water Bottle", "Headlamp", "GPS Watch", "Trekking Poles",
                    "Wool Socks", "Dry Bag", "First Aid Kit"],
}
# category seasonality (month 1..12 multipliers)
CAT_SEASON = {
    "Apparel":          [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.05, 1.1, 1.25],
    "Footwear":         [0.9, 0.9, 1.0, 1.1, 1.1, 1.1, 1.1, 1.1, 1.05, 1.0, 0.95, 1.0],
    "Camping & Hiking": [0.7, 0.7, 0.9, 1.1, 1.35, 1.35, 1.35, 1.35, 1.1, 0.9, 0.7, 0.75],
    "Climbing":         [0.9, 0.9, 1.0, 1.1, 1.15, 1.15, 1.15, 1.15, 1.1, 1.0, 0.9, 0.9],
    "Winter Sports":    [1.8, 1.7, 1.2, 0.7, 0.4, 0.35, 0.35, 0.35, 0.6, 1.0, 1.7, 1.85],
    "Accessories":      [1.0, 1.0, 1.0, 1.0, 1.0, 1.05, 1.05, 1.0, 1.0, 1.0, 1.1, 1.5],
}
GLOBAL_SEASON = [0.82, 0.84, 0.96, 1.04, 1.14, 1.24, 1.28, 1.18, 1.02, 0.94, 1.08, 1.40]

def build_dim_product():
    products = []
    key = 100
    used_names = set()
    for cat, (count, lo, hi, subcats) in CATEGORY_SPECS.items():
        for i in range(count):
            key += 1
            while True:
                name = f"{random.choice(ADJ)} {random.choice(NOUN[cat])}"
                if name not in used_names:
                    used_names.add(name)
                    break
            price = round(random.uniform(lo, hi) / 5) * 5 - 0.01
            cost = round(price * random.uniform(0.45, 0.58), 2)
            tier = "Premium" if price > (lo + hi) * 0.6 else ("Core" if price > (lo + hi) * 0.3 else "Value")
            products.append({
                "ProductKey": key,
                "SKU": f"TP-{cat[:2].upper()}{key}",
                "ProductName": name,
                "Category": cat,
                "Subcategory": subcats[i % len(subcats)],
                "PriceTier": tier,
                "UnitPrice": price,
                "UnitCost": cost,
            })
    return products

def assign_pareto_weights(products):
    """Engineer revenue concentration: 8 heroes ~40%, 16 mid ~35%, 96 tail ~25%."""
    idx = list(range(len(products)))
    # pick heroes spread across categories for realism
    by_cat = {}
    for i, p in enumerate(products):
        by_cat.setdefault(p["Category"], []).append(i)
    hero_plan = [("Apparel", 2), ("Camping & Hiking", 2), ("Footwear", 1),
                 ("Winter Sports", 1), ("Climbing", 1), ("Accessories", 1)]
    heroes = []
    for cat, n in hero_plan:
        heroes.extend(random.sample(by_cat[cat], n))
    remaining = [i for i in idx if i not in heroes]
    mid = random.sample(remaining, 16)
    tail = [i for i in remaining if i not in mid]

    weights = [0.0] * len(products)
    hero_w = [random.uniform(0.8, 1.2) for _ in heroes]
    mid_w = [random.uniform(0.7, 1.3) for _ in mid]
    tail_w = [(r + 1) ** -0.8 * random.uniform(0.6, 1.4) for r in range(len(tail))]
    for grp, ws, share in ((heroes, hero_w, 0.40), (mid, mid_w, 0.35), (tail, tail_w, 0.25)):
        total = sum(ws)
        for i, w in zip(grp, ws):
            weights[i] = share * w / total
    return weights

# ---------------------------------------------------------------- P&L engine
def month_revenue_target(store, year, month, mode):
    """Planned product revenue for a store-month. mode: 'actual' or 'budget'."""
    key, code, name, city, state, region, tier, sqft, opened = store
    base = TIER_BASE_REV[tier] * STORE_FACTOR[key]
    if mode == "budget":
        growth = {2024: 1.00, 2025: 1.07, 2026: 1.134}[year]
        noise = 1.0
        boise = 1.0
    else:
        growth = {2024: 1.00, 2025: 1.082, 2026: 1.134}[year]
        noise = random.uniform(0.96, 1.04)
        boise = 0.88 if (key == 4 and year == 2026) else 1.0  # A3
    return base * growth * GLOBAL_SEASON[month - 1] * noise * boise

def allocate_products(products, weights, target_rev, month):
    """Split a store-month revenue target across SKUs; return rows + exact totals."""
    season_w = []
    for p, w in zip(products, weights):
        season_w.append(w * CAT_SEASON[p["Category"]][month - 1] * random.uniform(0.75, 1.25))
    total_w = sum(season_w)
    rows, rev_total, cost_total = [], 0.0, 0.0
    for p, w in zip(products, season_w):
        alloc = target_rev * w / total_w
        units = int(round(alloc / p["UnitPrice"]))
        if units <= 0:
            continue
        rev = round(units * p["UnitPrice"], 2)
        cost = round(units * p["UnitCost"], 2)
        rows.append((p["ProductKey"], units, rev, cost))
        rev_total = round(rev_total + rev, 2)
        cost_total = round(cost_total + cost, 2)
    return rows, rev_total, cost_total

def store_month_pnl(store, year, month, product_rev, product_cost, mode):
    """Return {account_key: amount>0} for one store-month."""
    key, code, name, city, state, region, tier, sqft, opened = store
    n = (lambda lo, hi: random.uniform(lo, hi)) if mode == "actual" else (lambda lo, hi: 1.0)

    online = round(product_rev * min(0.35, max(0.10, TIER_ONLINE_SHARE[tier] + STORE_ONLINE_NUDGE[key])), 2)
    retail = round(product_rev - online, 2)
    services = round(product_rev * 0.075 * n(0.93, 1.07), 2)

    freight = round(product_rev * 0.023 * n(0.95, 1.05), 2)
    shrink_rate = 0.007
    shrink_mult = 4.5 if (mode == "actual" and key == 6 and year == 2025 and month == 11) else 1.0  # A4
    shrinkage = round(product_rev * shrink_rate * shrink_mult * n(0.8, 1.2), 2)

    wages = round((TIER_PAYROLL_BASE[tier] + product_rev * 0.055) * n(0.97, 1.03), 2)
    benefits = round(wages * 0.22, 2)

    rent = sqft * 3.0 * STORE_RENT_FACTOR[key]
    if mode == "actual" and key == 1 and (year, month) >= (2026, 2):  # A1
        rent *= 1.28
    rent = round(rent, 2)
    util_season = 1.3 if month in (12, 1, 2) else (1.25 if month in (7, 8) else 1.0)
    utilities = round(sqft * 0.16 * util_season * n(0.9, 1.1), 2)
    maintenance = round(1800 * n(0.5, 2.5), 2) if mode == "actual" else 1800.0

    ads = product_rev * 0.034
    if mode == "actual" and region == "Pacific" and (year, month) in ((2026, 4), (2026, 5), (2026, 6)):  # A2
        ads *= 1.40
    ads = round(ads * n(0.95, 1.05), 2)
    events = round((2500 + (6000 if month in (3, 6, 9, 12) else 0)) * TIER_EVENT_SCALE[tier] * n(0.9, 1.1), 2)

    card_fees = round((retail + online) * 0.019, 2)
    packaging = round(product_rev * 0.006 * n(0.9, 1.1), 2)
    insurance = TIER_INSURANCE[tier]
    software = round(1450 * (1.02 ** (year - 2024)), 2)
    prof_fees = round(900 * (3.0 if month == 1 else 1.0) * n(0.8, 1.3), 2)
    office = round(700 * n(0.7, 1.4), 2)
    depreciation = TIER_DEPRECIATION[tier]

    return {
        4000: retail, 4100: online, 4200: services,
        5000: product_cost, 5100: freight, 5200: shrinkage,
        6000: wages, 6010: benefits,
        6100: rent, 6110: utilities, 6120: maintenance,
        6200: ads, 6210: events,
        6300: card_fees, 6310: packaging,
        6400: insurance, 6410: software, 6420: prof_fees, 6430: office,
        7000: depreciation,
    }

# ---------------------------------------------------------------- build all
def main():
    dim_date = build_dim_date()
    products = build_dim_product()
    weights = assign_pareto_weights(products)

    fact_sales, fact_actuals, fact_budget = [], [], []

    for store in STORES:
        for (year, month) in ACTUALS_MONTHS:
            dt = date(year, month, 1).isoformat()
            target = month_revenue_target(store, year, month, "actual")
            rows, rev_total, cost_total = allocate_products(products, weights, target, month)
            for pk, units, rev, cost in rows:
                fact_sales.append({"Date": dt, "StoreKey": store[0], "ProductKey": pk,
                                   "UnitsSold": units, "Revenue": rev, "Cost": cost})
            pnl = store_month_pnl(store, year, month, rev_total, cost_total, "actual")
            for ak, amt in pnl.items():
                fact_actuals.append({"Date": dt, "StoreKey": store[0],
                                     "AccountKey": ak, "Amount": amt})

    for store in STORES:
        for (year, month) in BUDGET_MONTHS:
            dt = date(year, month, 1).isoformat()
            target = month_revenue_target(store, year, month, "budget")
            product_rev = round(target, 2)
            product_cost = round(target * 0.525, 2)
            pnl = store_month_pnl(store, year, month, product_rev, product_cost, "budget")
            for ak, amt in pnl.items():
                fact_budget.append({"Date": dt, "StoreKey": store[0],
                                    "AccountKey": ak, "Amount": round(round(amt / 50) * 50, 2)})

    # ------------------------------------------------------------ write csvs
    def write(name, rows, fieldnames):
        path = os.path.join(BASE_DIR, name)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        print(f"  {name}: {len(rows):,} rows")

    print("Writing CSVs:")
    write("dim_date.csv", dim_date, list(dim_date[0].keys()))
    write("dim_store.csv",
          [{"StoreKey": s[0], "StoreCode": s[1], "StoreName": s[2], "City": s[3],
            "State": s[4], "Region": s[5], "StoreTier": s[6], "SquareFeet": s[7],
            "OpenDate": s[8]} for s in STORES],
          ["StoreKey", "StoreCode", "StoreName", "City", "State", "Region",
           "StoreTier", "SquareFeet", "OpenDate"])
    write("dim_account.csv",
          [{"AccountKey": a[0], "Account": a[1], "Category": a[2], "Subcategory": a[3],
            "Sign": a[4], "StatementSort": a[5]} for a in ACCOUNTS],
          ["AccountKey", "Account", "Category", "Subcategory", "Sign", "StatementSort"])
    write("dim_product.csv", products, list(products[0].keys()))
    write("dim_pnl_layout.csv",
          [{"LineKey": l[0], "LineLabel": l[1], "RowType": l[2], "Indent": l[3],
            "IsBold": l[4]} for l in PNL_LAYOUT],
          ["LineKey", "LineLabel", "RowType", "Indent", "IsBold"])
    write("bridge_pnl_line_account.csv",
          [{"LineKey": lk, "AccountKey": ak} for lk, accts in PNL_BRIDGE.items()
           for ak in accts],
          ["LineKey", "AccountKey"])
    write("fact_pnl_actuals.csv", fact_actuals, ["Date", "StoreKey", "AccountKey", "Amount"])
    write("fact_pnl_budget.csv", fact_budget, ["Date", "StoreKey", "AccountKey", "Amount"])
    write("fact_sales.csv", fact_sales, ["Date", "StoreKey", "ProductKey",
                                         "UnitsSold", "Revenue", "Cost"])

    # ------------------------------------------------------------ validation
    print("\nValidation:")
    # FK integrity
    dates = {r["Date"] for r in dim_date}
    skeys = {s[0] for s in STORES}
    akeys = {a[0] for a in ACCOUNTS}
    pkeys = {p["ProductKey"] for p in products}
    assert all(r["Date"] in dates and r["StoreKey"] in skeys and r["AccountKey"] in akeys
               for r in fact_actuals + fact_budget), "FK violation in P&L facts"
    assert all(r["Date"] in dates and r["StoreKey"] in skeys and r["ProductKey"] in pkeys
               for r in fact_sales), "FK violation in fact_sales"
    print("  FK integrity: OK (all fact keys resolve to dimensions)")

    # reconciliation: sales revenue == 4000+4100, sales cost == 5000
    from collections import defaultdict
    sales_rev, sales_cost = defaultdict(float), defaultdict(float)
    for r in fact_sales:
        k = (r["Date"], r["StoreKey"])
        sales_rev[k] = round(sales_rev[k] + r["Revenue"], 2)
        sales_cost[k] = round(sales_cost[k] + r["Cost"], 2)
    pnl_rev, pnl_cost = defaultdict(float), defaultdict(float)
    for r in fact_actuals:
        k = (r["Date"], r["StoreKey"])
        if r["AccountKey"] in (4000, 4100):
            pnl_rev[k] = round(pnl_rev[k] + r["Amount"], 2)
        if r["AccountKey"] == 5000:
            pnl_cost[k] = round(pnl_cost[k] + r["Amount"], 2)
    max_rev_diff = max(abs(sales_rev[k] - pnl_rev[k]) for k in sales_rev)
    max_cost_diff = max(abs(sales_cost[k] - pnl_cost[k]) for k in sales_cost)
    assert max_rev_diff <= 0.02 and max_cost_diff <= 0.02, \
        f"reconciliation broke: rev {max_rev_diff}, cost {max_cost_diff}"
    print(f"  Sales-to-P&L reconciliation: OK (max diff rev ${max_rev_diff:.2f}, cost ${max_cost_diff:.2f})")

    # Pareto check
    by_product = defaultdict(float)
    for r in fact_sales:
        by_product[r["ProductKey"]] += r["Revenue"]
    ranked = sorted(by_product.values(), reverse=True)
    total = sum(ranked)
    top20 = sum(ranked[: int(len(ranked) * 0.2)]) / total
    print(f"  Pareto: top 20% of SKUs = {top20:.1%} of revenue "
          f"({int(len(ranked) * 0.2)} of {len(ranked)} SKUs)")

    # company P&L for June 2026
    def company_month(year_month):
        agg = defaultdict(float)
        for r in fact_actuals:
            if r["Date"].startswith(year_month):
                agg[r["AccountKey"]] += r["Amount"]
        rev = agg[4000] + agg[4100] + agg[4200]
        cogs = agg[5000] + agg[5100] + agg[5200]
        gp = rev - cogs
        opex = sum(v for k, v in agg.items() if 6000 <= k < 7000)
        ebitda = gp - opex
        op = ebitda - agg[7000]
        return rev, gp, ebitda, op

    rev, gp, ebitda, op = company_month("2026-06")
    print(f"  Jun 2026 company P&L: revenue ${rev:,.0f}, GP {gp/rev:.1%}, "
          f"EBITDA {ebitda/rev:.1%}, operating profit {op/rev:.1%}")

    # YoY growth sanity
    def year_revenue(y):
        return sum(r["Amount"] for r in fact_actuals
                   if r["Date"].startswith(str(y)) and r["AccountKey"] in (4000, 4100, 4200))
    r24, r25 = year_revenue(2024), year_revenue(2025)
    print(f"  Revenue 2024 ${r24:,.0f} -> 2025 ${r25:,.0f} (YoY {r25/r24-1:+.1%})")

    # anomaly presence
    den_rent_jan = sum(r["Amount"] for r in fact_actuals
                       if r["Date"] == "2026-01-01" and r["StoreKey"] == 1 and r["AccountKey"] == 6100)
    den_rent_feb = sum(r["Amount"] for r in fact_actuals
                       if r["Date"] == "2026-02-01" and r["StoreKey"] == 1 and r["AccountKey"] == 6100)
    print(f"  A1 Denver rent: Jan 2026 ${den_rent_jan:,.0f} -> Feb 2026 ${den_rent_feb:,.0f} "
          f"({den_rent_feb/den_rent_jan-1:+.0%})")
    print("\nDone. CSVs in ./data/")

if __name__ == "__main__":
    main()
