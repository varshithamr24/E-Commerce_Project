# app.py
"""
E-Commerce Sales Analytics  —  Streamlit Frontend
==================================================
Entry point:  streamlit run app.py

Architecture
------------
  data_loader.py – read CSV, structural inspection helpers
  cleaning.py    – clean raw frame, engineer features
  analytics.py   – all groupby / summary functions
  app.py         – UI only (no business logic here)
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import streamlit as st

import cleaning     as cl
import analytics    as an
import data_loader  as dl

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Visual theme ──────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid")
plt.rcParams.update({"figure.dpi": 110, "font.size": 10})

ACCENT   = "#2563EB"   # blue
PURPLE   = "#7C3AED"   # purple
GREEN    = "#16A34A"   # green
RED      = "#DC2626"   # red
AMBER    = "#D97706"   # amber
GRAY     = "#6B7280"   # muted

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* sidebar */
[data-testid="stSidebar"]          { background:#0F172A; }
[data-testid="stSidebar"] *        { color:#CBD5E1 !important; }
[data-testid="stSidebar"] hr       { border-color:#334155; }

/* metric cards */
[data-testid="metric-container"] {
    background:#F8FAFC; border:1px solid #E2E8F0;
    border-radius:10px; padding:14px 18px;
}
[data-testid="metric-container"] label
    { color:#64748B !important; font-size:.76rem !important; font-weight:600; }
[data-testid="metric-container"] [data-testid="stMetricValue"]
    { color:#0F172A !important; font-size:1.4rem !important; font-weight:800; }

/* section headings */
.sec { font-size:1rem; font-weight:700; color:#1E293B;
       border-left:4px solid #2563EB; padding-left:10px;
       margin:28px 0 10px; }

/* insight cards */
.insight-card {
    background:#FFFFFF; border:1px solid #E2E8F0;
    border-radius:12px; padding:18px 22px; margin-bottom:14px;
}
.insight-title { font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:6px; }
.insight-find  { font-size:.88rem; color:#374151; margin-bottom:8px; }
.insight-rec   { font-size:.84rem; color:#1D4ED8;
                 background:#EFF6FF; border-radius:6px; padding:8px 12px; }

/* tab text */
button[data-baseweb="tab"] { font-weight:600; font-size:.88rem; }

/* dataframe */
[data-testid="stDataFrame"] { border-radius:8px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA  (cached – runs once per session)
# ═══════════════════════════════════════════════════════════════════════════════
FILE = "realistic_e_commerce_sales_data.csv"

@st.cache_data(show_spinner="⏳  Loading and cleaning data …")
def get_data(path: str):
    return cl.load_and_clean(path)

try:
    df_raw, df, clean_log = get_data(FILE)
except FileNotFoundError:
    st.error(f"❌  `{FILE}` not found. Place the CSV next to `app.py`.")
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🛒 E-Commerce Analytics")
    st.markdown("---")

    st.markdown("### 🔍 Filters")
    regions    = ["All"] + sorted(df["Region"].unique())
    categories = ["All"] + sorted(df["Category"].unique())
    genders    = ["All"] + sorted(df["Gender"].unique())

    sel_region   = st.selectbox("Region",   regions,    index=0)
    sel_category = st.selectbox("Category", categories, index=0)
    sel_gender   = st.selectbox("Gender",   genders,    index=0)

    d_min = df["Order Date"].min().date()
    d_max = df["Order Date"].max().date()
    date_range = st.date_input("Order Date Range",
                               value=(d_min, d_max),
                               min_value=d_min, max_value=d_max)
    st.markdown("---")

    st.markdown("### 📌 Pages")
    page = st.radio("Navigation", [
        "🏠  Overview",
        "📄  Data Loading",
        "🧹  Data Cleaning",
        "⚙️  Feature Engineering",
        "📊  EDA",
        "📈  Visualizations",
        "💡  Business Insights",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.caption(f"Dataset: `{FILE}`")
    st.caption(f"Records: {len(df):,}  |  Cols: {df.shape[1]}")


# ─── Apply filters ────────────────────────────────────────────────────────────
dff = df.copy()
if sel_region   != "All": dff = dff[dff["Region"]   == sel_region]
if sel_category != "All": dff = dff[dff["Category"] == sel_category]
if sel_gender   != "All": dff = dff[dff["Gender"]   == sel_gender]
if len(date_range) == 2:
    dff = dff[(dff["Order Date"].dt.date >= date_range[0]) &
              (dff["Order Date"].dt.date <= date_range[1])]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def inr(v):     return f"₹{v:,.0f}"
def inr2(v):    return f"₹{v:,.2f}"
def pct(v):     return f"{v:.1f}%"
def sec(t):     st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)
def fmt_k(x,_): return f"₹{x/1000:.0f}K"

def bar_labels(ax, fmt_str="₹{:,.0f}", fontsize=8, horiz=False):
    for p in ax.patches:
        val = p.get_width() if horiz else p.get_height()
        if val <= 0:
            continue
        if horiz:
            ax.text(val + ax.get_xlim()[1] * 0.01,
                    p.get_y() + p.get_height() / 2,
                    fmt_str.format(val), va="center", fontsize=fontsize)
        else:
            ax.text(p.get_x() + p.get_width() / 2,
                    val + ax.get_ylim()[1] * 0.01,
                    fmt_str.format(val), ha="center", fontsize=fontsize)

SHIP_COLOR = {"Delivered": GREEN, "In Transit": ACCENT,
              "Returned": RED, "Unknown": GRAY}


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Overview":
    st.title("🛒 E-Commerce Sales Analytics Dashboard")
    st.markdown(
        "A full end-to-end analytics project on e-commerce transaction data. "
        "Use the **sidebar filters** to drill into any region, category, gender, or date range."
    )

    # ── Problem statement ─────────────────────────────────────────────────────
    with st.expander("📋  Problem Statement", expanded=True):
        st.markdown("""
E-commerce businesses generate millions of transactions per year.
Without structured analysis, opportunities and risks remain hidden.

This project analyses transaction data to surface actionable insights across:

| Dimension | Scope |
|-----------|-------|
| **Sales** | Revenue, volumes, average order value |
| **Products** | Best/worst sellers by revenue and quantity |
| **Categories** | Contribution %, average order value |
| **Customers** | Demographics, loyalty, spending |
| **Regions** | Geographic performance |
| **Gender** | Revenue and order split |
| **Age Groups** | Life-stage spending patterns |
| **Shipping** | Delivered / In-Transit / Returned |
| **Trends** | Daily, monthly, quarterly patterns |
| **Returns** | Return rate and revenue impact |
        """)

    # ── Objectives ────────────────────────────────────────────────────────────
    with st.expander("🎯  Business Objectives", expanded=False):
        for i, obj in enumerate([
            "Identify the highest-selling products",
            "Find the most profitable categories",
            "Analyse regional sales performance",
            "Analyse customer demographics (gender, age)",
            "Identify the most popular products by order frequency",
            "Analyse shipping & delivery status",
            "Study monthly and quarterly trends",
            "Analyse quantity sold across all dimensions",
            "Calculate and compare average order values",
            "Identify returned orders and their revenue impact",
            "Generate data-driven business recommendations",
        ], 1):
            st.markdown(f"**{i}.** {obj}")

    # ── KPI strip ─────────────────────────────────────────────────────────────
    st.markdown("---")
    sec("📌 Key Metrics  *(filtered)*")
    kpis = an.overall_kpis(dff)

    c = st.columns(6)
    c[0].metric("💰 Total Revenue",    inr(kpis["total_revenue"]))
    c[1].metric("📦 Orders",           f"{kpis['num_orders']:,}")
    c[2].metric("🔢 Units Sold",       f"{kpis['total_quantity']:,}")
    c[3].metric("📊 Avg Order Value",  inr(kpis["avg_order_value"]))
    c[4].metric("👥 Customers",        f"{kpis['unique_customers']:,}")
    c[5].metric("↩️ Return Rate",      pct(kpis["return_rate"]))

    c2 = st.columns(6)
    c2[0].metric("💳 Total Amount",    inr(kpis["total_amount"]))
    c2[1].metric("🔁 Repeat Customers",f"{kpis['repeat_customers']:,}")
    c2[2].metric("✅ Delivery Rate",   pct(kpis["delivery_rate"]))
    c2[3].metric("🏷️ Avg Unit Price",  inr(kpis["avg_unit_price"]))
    c2[4].metric("🚢 Avg Ship Fee",    inr2(kpis["avg_shipping_fee"]))
    c2[5].metric("📅 Date Range",
                 f"{kpis['date_min'].date()} → {kpis['date_max'].date()}"
                 if kpis['date_min'] is not pd.NaT else "—")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DATA LOADING  (powered by data_loader.py)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📄  Data Loading":
    st.title("📄 Data Loading")
    st.markdown(
        "Raw CSV read by **`data_loader.load_csv()`** — zero modifications applied. "
        "All helpers below call `data_loader` functions directly."
    )

    # ── File info ─────────────────────────────────────────────────────────────
    info = dl.dataset_info(df_raw)
    sec("1.1  File & Shape Summary")
    c = st.columns(4)
    c[0].metric("📄 File",         FILE)
    c[1].metric("🔢 Rows",         f"{info['rows']:,}")
    c[2].metric("📋 Columns",      info["columns"])
    c[3].metric("💾 Memory",       f"{info['memory_bytes'] / 1024:.1f} KB")

    c2 = st.columns(2)
    c2[0].metric("🔢 Numeric Columns",     len(info["numeric_cols"]))
    c2[1].metric("🔤 Categorical Columns", len(info["categorical_cols"]))

    # ── Sample records ────────────────────────────────────────────────────────
    head_df, tail_df = dl.sample_records(df_raw, 5)

    sec("1.2  First 5 Records")
    st.dataframe(head_df, width="stretch")

    sec("1.3  Last 5 Records")
    st.dataframe(tail_df, width="stretch")

    # ── Column names ──────────────────────────────────────────────────────────
    sec("1.4  Column Names")
    cols_display = pd.DataFrame({
        "No.":    range(1, info["columns"] + 1),
        "Column": info["column_names"],
        "Type":   [info["dtypes"][c] for c in info["column_names"]],
    })
    st.dataframe(cols_display, width="stretch", hide_index=True)

    # ── Data types + nulls ────────────────────────────────────────────────────
    sec("1.5  Data Types, Null Counts & Sample Values")
    st.dataframe(dl.dtype_table(df_raw), width="stretch", hide_index=True)

    # ── Missing value report ──────────────────────────────────────────────────
    sec("1.6  Missing Value Report")
    mv_report = dl.missing_value_report(df_raw)
    mv_with_nulls = mv_report[mv_report["Missing Count"] > 0]
    if mv_with_nulls.empty:
        st.success("✅  No missing values found in the raw dataset.")
    else:
        st.warning(f"⚠️  {len(mv_with_nulls)} column(s) contain missing values.")
        st.dataframe(mv_with_nulls, width="stretch", hide_index=True)

    # ── Missing value heatmap ─────────────────────────────────────────────────
    import matplotlib.pyplot as plt
    import seaborn as sns
    fig, ax = plt.subplots(figsize=(12, 2.8))
    sns.heatmap(df_raw.isnull().T, cbar=False, cmap="Reds",
                yticklabels=df_raw.columns, ax=ax, linewidths=0.3)
    ax.set_title("Missing Value Heatmap  (Red = Missing)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Row index")
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── Descriptive statistics ────────────────────────────────────────────────
    sec("1.7  Descriptive Statistics")
    st.dataframe(dl.descriptive_stats(df_raw), width="stretch", hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DATA CLEANING
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧹  Data Cleaning":
    st.title("🧹 Data Cleaning")
    st.markdown(
        "All cleaning is performed on a **copy** of the raw dataframe — the original "
        "is always preserved. Each step is documented below."
    )

    sec("2.1  Cleaning Steps Log")
    for entry in clean_log:
        icon = "✅"
        with st.expander(f"{icon}  {entry['step']}", expanded=False):
            st.markdown(f"```\n{entry['detail']}\n```")
            if entry.get("before") is not None:
                c1, c2 = st.columns(2)
                c1.metric("Before", entry["before"])
                c2.metric("After",  entry["after"])

    sec("2.2  Missing Values Heatmap  *(raw data)*")
    fig, ax = plt.subplots(figsize=(12, 2.8))
    sns.heatmap(df_raw.isnull().T, cbar=False, cmap="Reds",
                yticklabels=df_raw.columns, ax=ax, linewidths=0.3)
    ax.set_title("Missing Value Map  (Red = Missing)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Row index")
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    sec("2.3  Missing Value Table  *(raw data)*")
    mv = df_raw.isnull().sum().reset_index()
    mv.columns = ["Column", "Missing Count"]
    mv["Missing %"] = (mv["Missing Count"] / len(df_raw) * 100).round(2)
    st.dataframe(mv, width="stretch", hide_index=True)

    sec("2.4  Before vs After")
    c1, c2, c3 = st.columns(3)
    c1.metric("Raw Rows",     f"{df_raw.shape[0]:,}")
    c2.metric("Clean Rows",   f"{df.shape[0]:,}")
    c3.metric("Rows Removed", f"{df_raw.shape[0] - df.shape[0]:,}")

    sec("2.5  Cleaned Data Preview  *(first 10 rows)*")
    st.dataframe(df.head(10), width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️  Feature Engineering":
    st.title("⚙️ Feature Engineering")
    st.markdown("New columns derived from existing data to power deeper analysis.")

    sec("3.1  Engineered Columns")
    feat_df = pd.DataFrame([
        ("Revenue",         "= Total Price  (Unit Price × Qty, corrected)",    "Core per-order income metric"),
        ("Total Amount",    "= Revenue + Shipping Fee",                         "Total paid by customer"),
        ("Quarter",         "Derived from Order Date  →  Q1–Q4",               "Quarterly trend analysis"),
        ("Order Day",       "Day name from Order Date  →  Mon–Sun",            "Day-of-week patterns"),
        ("Age Group",       "pd.cut on Age  →  18-25 / 26-35 / 36-45 / 46-55 / 56+", "Life-stage segmentation"),
        ("Revenue per Qty", "= Revenue / Quantity",                            "Effective unit revenue"),
        ("Return Flag",     "1 if Shipping Status = 'Returned' else 0",        "Binary return indicator"),
        ("Delivered Flag",  "1 if Shipping Status = 'Delivered' else 0",       "Binary delivery indicator"),
        ("Year",            "Order Date year",                                 "Year-level grouping"),
        ("Month",           "Order Date month number  (1–12)",                 "Month sorting"),
        ("Month Name",      "Order Date month abbreviation  (Jan–Dec)",        "Month-name grouping"),
        ("Day",             "Order Date day-of-month",                         "Day-level grouping"),
    ], columns=["Column", "Formula / Source", "Purpose"])
    st.dataframe(feat_df, width="stretch", hide_index=True)

    sec("3.2  Age Group Distribution")
    age_dist = df["Age Group"].value_counts().sort_index().reset_index()
    age_dist.columns = ["Age Group", "Count"]
    age_dist["Age Group"] = age_dist["Age Group"].astype(str)

    fig, ax = plt.subplots(figsize=(9, 4))
    pal = sns.color_palette("coolwarm", len(age_dist))
    bars = ax.bar(age_dist["Age Group"], age_dist["Count"],
                  color=pal, edgecolor="white", width=0.55)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 1,
                str(int(h)), ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_title("Customer Count by Age Group", fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Age Group")
    ax.set_ylabel("Number of Customers")
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    sec("3.3  Enriched Dataset Sample  *(first 10 rows)*")
    cols = ["Customer ID", "Order Date", "Revenue", "Total Amount",
            "Quarter", "Order Day", "Age Group",
            "Revenue per Qty", "Return Flag", "Delivered Flag"]
    st.dataframe(df[cols].head(10), width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: EDA
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊  EDA":
    st.title("📊 Exploratory Data Analysis")

    tabs = st.tabs([
        "A – Overall", "B – Products", "C – Categories",
        "D – Regions",  "E – Customers", "F – Gender",
        "G – Age",      "H – Shipping",  "I – Time-Series",
    ])

    # A — Overall ─────────────────────────────────────────────────────────────
    with tabs[0]:
        sec("A.  Overall Sales Summary")
        k = an.overall_kpis(dff)
        c = st.columns(3)
        c[0].metric("Total Revenue",       inr(k["total_revenue"]))
        c[1].metric("Total Quantity Sold",  f"{k['total_quantity']:,}")
        c[2].metric("Number of Orders",     f"{k['num_orders']:,}")
        c = st.columns(3)
        c[0].metric("Avg Order Value",      inr(k["avg_order_value"]))
        c[1].metric("Avg Unit Price",       inr(k["avg_unit_price"]))
        c[2].metric("Avg Shipping Fee",     inr2(k["avg_shipping_fee"]))

    # B — Products ────────────────────────────────────────────────────────────
    with tabs[1]:
        sec("B.  Product Analysis")
        prod = an.product_summary(dff)
        if not prod.empty:
            c = st.columns(2)
            c[0].metric("🏆 Top Revenue Product",  prod.iloc[0]["Product"],
                        inr(prod.iloc[0]["Revenue"]))
            c[1].metric("📉 Lowest Revenue Product", prod.iloc[-1]["Product"],
                        inr(prod.iloc[-1]["Revenue"]))
            c = st.columns(2)
            c[0].metric("📦 Most Ordered",
                        prod.sort_values("Orders", ascending=False).iloc[0]["Product"],
                        f"{prod.sort_values('Orders',ascending=False).iloc[0]['Orders']:,} orders")
            c[1].metric("🔢 Highest Quantity",
                        prod.sort_values("Quantity", ascending=False).iloc[0]["Product"],
                        f"{prod.sort_values('Quantity',ascending=False).iloc[0]['Quantity']:,} units")
        sec("Product-wise Summary Table")
        display = prod.copy()
        for col in ["Revenue", "Avg Order Value", "Avg Unit Price"]:
            display[col] = display[col].map(inr)
        display["Return Rate %"] = display["Return Rate %"].map(lambda x: f"{x:.1f}%")
        st.dataframe(display, width="stretch", hide_index=True)

    # C — Categories ──────────────────────────────────────────────────────────
    with tabs[2]:
        sec("C.  Category Analysis")
        cat = an.category_summary(dff)
        if not cat.empty:
            c = st.columns(2)
            c[0].metric("🏆 Top Category",   cat.iloc[0]["Category"],
                        inr(cat.iloc[0]["Revenue"]))
            c[1].metric("📊 Top Contribution", cat.iloc[0]["Category"],
                        pct(cat.iloc[0]["Contribution %"]))
        sec("Category Summary Table")
        disp = cat.copy()
        for col in ["Revenue", "Avg Order Value"]:
            disp[col] = disp[col].map(inr)
        disp["Contribution %"] = disp["Contribution %"].map(lambda x: f"{x:.1f}%")
        st.dataframe(disp, width="stretch", hide_index=True)

    # D — Regions ─────────────────────────────────────────────────────────────
    with tabs[3]:
        sec("D.  Regional Analysis")
        reg = an.region_summary(dff)
        if not reg.empty:
            c = st.columns(2)
            c[0].metric("🏆 Highest-Revenue Region", reg.iloc[0]["Region"],
                        inr(reg.iloc[0]["Revenue"]))
            c[1].metric("📉 Lowest-Revenue Region",  reg.iloc[-1]["Region"],
                        inr(reg.iloc[-1]["Revenue"]))
        sec("Region Summary Table")
        disp = reg.copy()
        for col in ["Revenue", "Avg Order Value"]:
            disp[col] = disp[col].map(inr)
        disp["Return Rate %"] = disp["Return Rate %"].map(lambda x: f"{x:.1f}%")
        st.dataframe(disp, width="stretch", hide_index=True)

    # E — Customers ───────────────────────────────────────────────────────────
    with tabs[4]:
        sec("E.  Customer Analysis")
        ov, top_s, top_o = an.customer_summary(dff)
        c = st.columns(3)
        c[0].metric("Unique Customers",   f"{ov['unique']:,}")
        c[1].metric("Repeat Customers",   f"{ov['repeat']:,}")
        c[2].metric("Avg Spend/Customer", inr(ov["avg_spend"]))
        c2 = st.columns(2)
        with c2[0]:
            sec("Top 10 Customers – Spending")
            d = top_s.copy()
            d["Total Spending"] = d["Total Spending"].map(inr)
            st.dataframe(d, width="stretch", hide_index=True)
        with c2[1]:
            sec("Top 10 Customers – Orders")
            st.dataframe(top_o, width="stretch", hide_index=True)

    # F — Gender ──────────────────────────────────────────────────────────────
    with tabs[5]:
        sec("F.  Gender Analysis")
        gen = an.gender_summary(dff)
        disp = gen.copy()
        for col in ["Revenue", "Avg Spending"]:
            disp[col] = disp[col].map(inr)
        disp["Return Rate %"] = disp["Return Rate %"].map(lambda x: f"{x:.1f}%")
        st.dataframe(disp, width="stretch", hide_index=True)

    # G — Age ─────────────────────────────────────────────────────────────────
    with tabs[6]:
        sec("G.  Age Group Analysis")
        age = an.age_summary(dff)
        disp = age.copy()
        for col in ["Revenue", "Avg Spending"]:
            disp[col] = disp[col].map(inr)
        st.dataframe(disp, width="stretch", hide_index=True)

    # H — Shipping ────────────────────────────────────────────────────────────
    with tabs[7]:
        sec("H.  Shipping Analysis")
        ship = an.shipping_summary(dff)
        deliv = ship.loc[ship["Shipping Status"] == "Delivered"]
        ret   = ship.loc[ship["Shipping Status"] == "Returned"]
        tran  = ship.loc[ship["Shipping Status"] == "In Transit"]
        c = st.columns(3)
        c[0].metric("✅ Delivered",  f"{int(deliv['Orders'].sum()):,}")
        c[1].metric("🚚 In Transit", f"{int(tran['Orders'].sum()):,}")
        c[2].metric("↩️ Returned",   f"{int(ret['Orders'].sum()):,}")
        disp = ship.copy()
        disp["Revenue"]  = disp["Revenue"].map(inr)
        disp["Share %"]  = disp["Share %"].map(lambda x: f"{x:.1f}%")
        st.dataframe(disp, width="stretch", hide_index=True)

    # I — Time-Series ─────────────────────────────────────────────────────────
    with tabs[8]:
        sec("I.  Monthly Trend")
        mt = an.monthly_trend(dff)
        disp = mt.copy()
        disp["Revenue"]  = disp["Revenue"].map(inr)
        st.dataframe(disp, width="stretch", hide_index=True)
        sec("Quarterly Trend")
        qt = an.quarterly_trend(dff)
        disp2 = qt.copy()
        disp2["Revenue"] = disp2["Revenue"].map(inr)
        st.dataframe(disp2, width="stretch", hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: VISUALIZATIONS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈  Visualizations":
    st.title("📈 Visualizations")
    st.markdown("All charts use the **filtered** dataset. Adjust sidebar filters to update.")

    # Pre-compute all series
    prod    = an.product_summary(dff)
    cat     = an.category_summary(dff)
    reg     = an.region_summary(dff)
    gen     = an.gender_summary(dff)
    age     = an.age_summary(dff)
    ship    = an.shipping_summary(dff)
    cust_s  = an.top_customers(dff, 10)
    mt      = an.monthly_trend(dff)

    # ── 1. Sales by Product ───────────────────────────────────────────────────
    sec("Chart 1 — Sales Revenue by Product")
    fig, ax = plt.subplots(figsize=(10, 5))
    prod_s = prod.sort_values("Revenue")
    colors = sns.color_palette("Set2", len(prod_s))
    bars = ax.barh(prod_s["Product"], prod_s["Revenue"], color=colors)
    for b, v in zip(bars, prod_s["Revenue"]):
        ax.text(v + max(prod_s["Revenue"]) * 0.01,
                b.get_y() + b.get_height() / 2,
                inr(v), va="center", fontsize=8.5, fontweight="bold")
    ax.set_title("Sales Revenue by Product", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Total Revenue (₹)")
    ax.set_ylabel("Product")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 2. Sales by Category ──────────────────────────────────────────────────
    sec("Chart 2 — Sales Revenue by Category")
    fig, ax = plt.subplots(figsize=(8, 5))
    pal = sns.color_palette("Set2", len(cat))
    bars = ax.bar(cat["Category"], cat["Revenue"], color=pal, edgecolor="white", width=0.55)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + max(cat["Revenue"]) * 0.01,
                inr(h), ha="center", fontsize=8.5, fontweight="bold")
    ax.set_title("Sales Revenue by Category", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Category")
    ax.set_ylabel("Total Revenue (₹)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 3. Sales by Region ────────────────────────────────────────────────────
    sec("Chart 3 — Sales Revenue by Region")
    fig, ax = plt.subplots(figsize=(8, 5))
    pal = sns.color_palette("pastel", len(reg))
    bars = ax.bar(reg["Region"], reg["Revenue"], color=pal, edgecolor="#CBD5E1", width=0.5)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + max(reg["Revenue"]) * 0.01,
                inr(h), ha="center", fontsize=8.5, fontweight="bold")
    ax.set_title("Sales Revenue by Region", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Region")
    ax.set_ylabel("Total Revenue (₹)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 4. Monthly Sales Trend ────────────────────────────────────────────────
    sec("Chart 4 — Monthly Sales Trend")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(mt["Month"], mt["Revenue"],
            marker="o", linewidth=2.4, color=ACCENT, markersize=7, label="Revenue")
    ax.fill_between(mt["Month"], mt["Revenue"], alpha=0.10, color=ACCENT)
    for x, y in zip(mt["Month"], mt["Revenue"]):
        ax.annotate(f"₹{y/1000:.1f}K", (x, y),
                    textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=7.5, color=ACCENT, fontweight="bold")
    ax.set_title("Monthly Sales Trend", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Revenue (₹)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 5. Quantity Sold by Product ───────────────────────────────────────────
    sec("Chart 5 — Quantity Sold by Product")
    fig, ax = plt.subplots(figsize=(10, 5))
    pq = prod.sort_values("Quantity", ascending=False)
    bars = ax.bar(pq["Product"], pq["Quantity"],
                  color=sns.color_palette("Set3", len(pq)), edgecolor="#D1D5DB", width=0.55)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + max(pq["Quantity"]) * 0.01,
                str(int(h)), ha="center", fontsize=9, fontweight="bold")
    ax.set_title("Quantity Sold by Product", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Product")
    ax.set_ylabel("Total Quantity Sold")
    ax.tick_params(axis="x", rotation=20)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 6. Gender Sales ───────────────────────────────────────────────────────
    sec("Chart 6 — Gender-wise Sales")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    g_colors = [ACCENT, AMBER]
    axes[0].bar(gen["Gender"], gen["Revenue"],
                color=g_colors[:len(gen)], edgecolor="white", width=0.45)
    for i, row in gen.iterrows():
        axes[0].text(i, row["Revenue"] + max(gen["Revenue"]) * 0.01,
                     inr(row["Revenue"]), ha="center", fontsize=9, fontweight="bold")
    axes[0].set_title("Revenue by Gender", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Gender")
    axes[0].set_ylabel("Total Revenue (₹)")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    axes[0].spines["top"].set_visible(False)
    axes[0].spines["right"].set_visible(False)
    axes[1].pie(gen["Orders"], labels=gen["Gender"],
                autopct="%1.1f%%", colors=g_colors[:len(gen)],
                startangle=140, wedgeprops={"edgecolor": "white"})
    axes[1].set_title("Order Share by Gender", fontsize=13, fontweight="bold")
    plt.suptitle("Gender-wise Sales Analysis", fontsize=15, fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 7. Age Group Sales ────────────────────────────────────────────────────
    sec("Chart 7 — Sales Revenue by Age Group")
    fig, ax = plt.subplots(figsize=(9, 5))
    pal = sns.color_palette("coolwarm", len(age))
    bars = ax.bar(age["Age Group"], age["Revenue"],
                  color=pal, edgecolor="white", width=0.55)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + max(age["Revenue"]) * 0.01,
                inr(h), ha="center", fontsize=8.5, fontweight="bold")
    ax.set_title("Sales Revenue by Age Group", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Age Group")
    ax.set_ylabel("Total Revenue (₹)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 8. Shipping Status ────────────────────────────────────────────────────
    sec("Chart 8 — Shipping Status Distribution")
    colors_ordered = [SHIP_COLOR.get(s, GRAY) for s in ship["Shipping Status"]]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].pie(ship["Orders"], labels=ship["Shipping Status"],
                autopct="%1.1f%%", colors=colors_ordered,
                startangle=90, wedgeprops={"edgecolor": "white"})
    axes[0].set_title("Shipping Status Share", fontsize=13, fontweight="bold")
    axes[1].bar(ship["Shipping Status"], ship["Revenue"],
                color=colors_ordered, edgecolor="white")
    for i, row in ship.iterrows():
        axes[1].text(i, row["Revenue"] + max(ship["Revenue"]) * 0.01,
                     f"₹{row['Revenue']/1000:.1f}K",
                     ha="center", fontsize=9, fontweight="bold")
    axes[1].set_title("Revenue by Shipping Status", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Shipping Status")
    axes[1].set_ylabel("Total Revenue (₹)")
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    axes[1].spines["top"].set_visible(False)
    axes[1].spines["right"].set_visible(False)
    plt.suptitle("Shipping Analysis", fontsize=15, fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 9. Top 10 Customers ───────────────────────────────────────────────────
    sec("Chart 9 — Top 10 Customers by Spending")
    fig, ax = plt.subplots(figsize=(10, 6))
    pal = sns.color_palette("Blues_d", len(cust_s))
    bars = ax.barh(cust_s["Customer"], cust_s["Revenue"], color=pal)
    for b, v in zip(bars, cust_s["Revenue"]):
        ax.text(v + max(cust_s["Revenue"]) * 0.01,
                b.get_y() + b.get_height() / 2,
                inr(v), va="center", fontsize=8.5, fontweight="bold")
    ax.set_title("Top 10 Customers by Total Spending", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Total Spending (₹)")
    ax.set_ylabel("Customer ID")
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 10. Category Contribution Pie ─────────────────────────────────────────
    sec("Chart 10 — Category Revenue Contribution")
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        cat["Revenue"], labels=cat["Category"],
        autopct="%1.1f%%",
        colors=sns.color_palette("Set2", len(cat)),
        startangle=140,
        wedgeprops={"edgecolor": "white"},
        pctdistance=0.82,
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight("bold")
    ax.set_title("Category-wise Revenue Contribution", fontsize=14, fontweight="bold", pad=10)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 11. Monthly Order Count ───────────────────────────────────────────────
    sec("Chart 11 — Monthly Order Count")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(mt["Month"], mt["Orders"],
            marker="s", linewidth=2.4, color=PURPLE, markersize=7, label="Orders")
    ax.fill_between(mt["Month"], mt["Orders"], alpha=0.10, color=PURPLE)
    for x, y in zip(mt["Month"], mt["Orders"]):
        ax.annotate(str(int(y)), (x, y),
                    textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=7.5, color=PURPLE, fontweight="bold")
    ax.set_title("Monthly Order Count", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of Orders")
    ax.tick_params(axis="x", rotation=30)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()

    # ── 12. Avg Order Value by Region ─────────────────────────────────────────
    sec("Chart 12 — Average Order Value by Region")
    fig, ax = plt.subplots(figsize=(8, 5))
    reg_s = reg.sort_values("Avg Order Value", ascending=False)
    pal = sns.color_palette("muted", len(reg_s))
    bars = ax.bar(reg_s["Region"], reg_s["Avg Order Value"],
                  color=pal, edgecolor="white", width=0.5)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + max(reg_s["Avg Order Value"]) * 0.01,
                inr(h), ha="center", fontsize=9, fontweight="bold")
    ax.set_title("Average Order Value by Region", fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Region")
    ax.set_ylabel("Avg Order Value (₹)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: BUSINESS INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💡  Business Insights":
    st.title("💡 Business Insights & Recommendations")
    st.markdown(
        "Insights are **dynamically computed** from the filtered dataset. "
        "Each card shows a data-backed finding and an actionable recommendation."
    )

    # ── KPI recap ─────────────────────────────────────────────────────────────
    sec("📌 Filtered KPI Snapshot")
    k = an.overall_kpis(dff)
    c = st.columns(5)
    c[0].metric("Revenue",        inr(k["total_revenue"]))
    c[1].metric("Orders",         f"{k['num_orders']:,}")
    c[2].metric("Return Rate",    pct(k["return_rate"]))
    c[3].metric("Delivery Rate",  pct(k["delivery_rate"]))
    c[4].metric("Avg Order Value",inr(k["avg_order_value"]))

    # ── Insight cards ─────────────────────────────────────────────────────────
    sec("🔍 Data-Driven Insights")
    insights = an.business_insights(dff)

    for ins in insights:
        st.markdown(f"""
<div class="insight-card">
  <div class="insight-title">{ins['icon']}&nbsp;&nbsp;{ins['title']}</div>
  <div class="insight-find">📌 <strong>Finding:</strong> {ins['finding']}</div>
  <div class="insight-rec">💡 <strong>Recommendation:</strong> {ins['recommendation']}</div>
</div>
""", unsafe_allow_html=True)

    # ── Summary table ─────────────────────────────────────────────────────────
    sec("📋 Summary Snapshot Table")
    prod = an.product_summary(dff)
    cat  = an.category_summary(dff)
    reg  = an.region_summary(dff)
    age  = an.age_summary(dff).sort_values("Revenue", ascending=False)

    summary_rows = [
        ("Top Product",        prod.iloc[0]["Product"]   if not prod.empty else "—",
                               inr(prod.iloc[0]["Revenue"]) if not prod.empty else "—"),
        ("Weakest Product",    prod.iloc[-1]["Product"]  if not prod.empty else "—",
                               inr(prod.iloc[-1]["Revenue"]) if not prod.empty else "—"),
        ("Top Category",       cat.iloc[0]["Category"]   if not cat.empty else "—",
                               pct(cat.iloc[0]["Contribution %"]) if not cat.empty else "—"),
        ("Top Region",         reg.iloc[0]["Region"]     if not reg.empty else "—",
                               inr(reg.iloc[0]["Revenue"]) if not reg.empty else "—"),
        ("Weakest Region",     reg.iloc[-1]["Region"]    if not reg.empty else "—",
                               inr(reg.iloc[-1]["Revenue"]) if not reg.empty else "—"),
        ("Top Age Group",      str(age.iloc[0]["Age Group"]) if not age.empty else "—",
                               inr(age.iloc[0]["Revenue"]) if not age.empty else "—"),
        ("Return Rate",        "All products",            pct(k["return_rate"])),
        ("Delivery Rate",      "All products",            pct(k["delivery_rate"])),
        ("Avg Order Value",    "All orders",              inr(k["avg_order_value"])),
        ("Repeat Customers",   f"{k['repeat_customers']:,} of {k['unique_customers']:,}",
                               pct(k["repeat_customers"] / max(k["unique_customers"],1) * 100)),
    ]
    summary_df = pd.DataFrame(summary_rows, columns=["Metric", "Segment / Item", "Value"])
    st.dataframe(summary_df, width="stretch", hide_index=True)
