# E-Commerce Sales Analytics

A complete end-to-end data analytics project for e-commerce transaction data, built with Python and Streamlit.

---

## Project Structure

```
archive/
├── realistic_e_commerce_sales_data.csv   ← Dataset (1,000 orders)
├── data_loader.py                        ← Data loading & structural inspection
├── cleaning.py                           ← Data cleaning & feature engineering
├── analytics.py                          ← Groupby summaries & business insights
├── app.py                                ← Streamlit dashboard (7 pages, 12 charts)
├── ecommerce_analysis_complete.py        ← Single standalone script (no Streamlit)
├── ecommerce_Project_Report.pptx         ← 20-slide project report
├── requirements.txt                      ← Python dependencies
└── README.md                             ← This file
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Streamlit dashboard
```bash
streamlit run app.py
# OR (if streamlit is not on PATH)
python -m streamlit run app.py
```
Opens at **http://localhost:8501**

### 3. Run the standalone analysis script
```bash
python ecommerce_analysis_complete.py
```
Prints all EDA results to the console and saves 12 PNG charts.

---

## Dataset

| Field | Details |
|---|---|
| File | `realistic_e_commerce_sales_data.csv` |
| Rows | 1,000 |
| Columns | 12 |
| Date Range | 2023-01-01 → 2024-01-03 |

**Columns:** Customer ID, Gender, Region, Age, Product Name, Category, Unit Price, Quantity, Total Price, Shipping Fee, Shipping Status, Order Date

**Missing values (raw):** Age (10%), Region (5%), Shipping Status (5%)

---

## Module Architecture

```
CSV File
   │
   ▼
data_loader.py       load_csv() · dataset_info() · missing_value_report()
   │                 sample_records() · dtype_table() · descriptive_stats()
   ▼
cleaning.py          load_and_clean() → (df_raw, df_clean, log)
   │                 12 cleaning steps + 8 engineered columns
   ▼
analytics.py         overall_kpis() · product_summary() · category_summary()
   │                 region_summary() · customer_summary() · gender_summary()
   │                 age_summary() · shipping_summary() · monthly_trend()
   │                 quarterly_trend() · daily_trend() · business_insights()
   ▼
app.py               Streamlit UI — 7 pages, live filters, 12 charts
```

---

## Streamlit Dashboard Pages

| Page | Content |
|---|---|
| 🏠 Overview | Problem statement, objectives, 12 KPI metric cards |
| 📄 Data Loading | File info, first/last 5 rows, dtypes, missing value heatmap, stats |
| 🧹 Data Cleaning | 13 step-by-step cleaning logs with before/after counts |
| ⚙️ Feature Engineering | 12 engineered columns table, age group chart, enriched data sample |
| 📊 EDA | 9 tabs: Overall, Products, Categories, Regions, Customers, Gender, Age, Shipping, Time-Series |
| 📈 Visualizations | 12 Matplotlib/Seaborn charts with value labels and ₹ formatting |
| 💡 Business Insights | 9 data-driven insight cards + summary snapshot table |

### Sidebar Filters (live — update all pages)
- Region (All / North / South / East / West)
- Category (All / Electronics / Wearables / Accessories)
- Gender (All / Male / Female)
- Order Date Range (date picker)

---

## Data Cleaning Steps

1. Dataset loaded via `data_loader.load_csv()`
2. Missing value audit
3. Age → median fill (100 nulls → 0)
4. Region → mode fill (50 nulls → 0)
5. Shipping Status → 'Unknown' fill (50 nulls → 0)
6. Duplicate rows removed
7. Invalid / non-positive numeric rows removed
8. Categorical columns standardised (strip + title-case)
9. Order Date parsed to datetime
10. Year / Month / Month Name / Day extracted
11. Total Price verified (Unit Price × Quantity)
12. Feature engineering (8 new columns)

---

## Feature Engineering

| Column | Formula | Purpose |
|---|---|---|
| Revenue | = Total Price | Core per-order income |
| Total Amount | = Revenue + Shipping Fee | Full amount paid |
| Quarter | From Order Date | Quarterly trend analysis |
| Order Day | Day name from Order Date | Day-of-week patterns |
| Age Group | pd.cut (18-25 / 26-35 / 36-45 / 46-55 / 56+) | Life-stage segmentation |
| Revenue per Qty | = Revenue / Quantity | Effective unit revenue |
| Return Flag | 1 if Returned else 0 | Binary return indicator |
| Delivered Flag | 1 if Delivered else 0 | Binary delivery indicator |

---

## Key Results

| Metric | Value |
|---|---|
| Total Revenue | ₹13,78,791 |
| Total Orders | 1,000 |
| Units Sold | 3,008 |
| Avg Order Value | ₹1,379 |
| Unique Customers | 292 |
| Repeat Customers | 251 (86.0%) |
| Return Rate | 30.8% |
| Delivery Rate | 31.3% |
| Top Product | Laptop (₹7,15,315 — 51.9%) |
| Top Category | Electronics (89.3%) |
| Top Region | West (₹4,05,964) |
| Peak Month | January |
| Best Quarter | Q4 |

---

## Visualizations (12 Charts)

1. Sales Revenue by Product — Horizontal Bar
2. Sales Revenue by Category — Bar
3. Sales Revenue by Region — Bar
4. Monthly Sales Trend — Line + Fill
5. Quantity Sold by Product — Bar
6. Gender-wise Sales — Bar + Pie
7. Sales by Age Group — Bar
8. Shipping Status Distribution — Pie + Bar
9. Top 10 Customers by Spending — Horizontal Bar
10. Category Revenue Contribution — Pie
11. Monthly Order Count — Line + Fill
12. Average Order Value by Region — Bar

---

## Business Insights

1. **Top Product:** Laptop drives 51.9% of revenue → invest in inventory & bundles
2. **Category Risk:** Electronics = 89.3% → diversify product range
3. **Regional Gap:** West leads, South lags by ₹1,02,241 → replicate West strategy
4. **Return Alert:** 30.8% return rate → fix product descriptions & quality
5. **Delivery Rate:** Only 31.3% confirmed delivered → add tracking & notifications
6. **Loyalty:** 86% repeat rate → launch tiered loyalty programme
7. **Age Target:** 46-55 is top-spending segment → personalise campaigns
8. **Seasonality:** January & Q4 peak → pre-stock and trough promotions
9. **AOV Uplift:** ₹1,379 avg → bundles, free shipping thresholds, volume discounts

---

## Requirements

```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
streamlit>=1.32.0
```

Install: `pip install -r requirements.txt`

---

## Files Reference

| File | Role |
|---|---|
| `data_loader.py` | CSV reading + structural inspection (6 public functions) |
| `cleaning.py` | 12-step cleaning pipeline + feature engineering |
| `analytics.py` | 13 analytics functions (KPIs, summaries, insights) |
| `app.py` | Streamlit UI — 7 pages, sidebar filters, 12 charts |
| `ecommerce_analysis_complete.py` | Standalone script — no Streamlit required |
| `ecommerce_Project_Report.pptx` | 20-slide project presentation |
| `requirements.txt` | Python package dependencies |

---

*Dataset: realistic_e_commerce_sales_data.csv | Python 3.10+ | Streamlit 1.32+ | python-pptx 0.6.21+*
