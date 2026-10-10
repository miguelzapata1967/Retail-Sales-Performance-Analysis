"""Retail Sales Performance Dashboard | Snowflake Streamlit + Snowpark.
Deploy by replacing the contents of streamlit_app.py in Snowflake Streamlit.
"""
import streamlit as st
import altair as alt
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col, sum as sf_sum, date_trunc, to_date

st.set_page_config(page_title="Retail Sales Performance", layout="wide")
st.title("Retail Sales Performance Dashboard")
st.caption("DEA Project | Snowpark Python calculations • Streamlit/Altair visualization")

# Each snippet below is EXECUTED, and the same exact source is shown in the inspector.
CODE = {
    "Load and calculate sales": '''sales_df = session.table("RETAIL_SALES_PERFORMANCE_ANALISIS.PUBLIC.SALES_RAW").with_column(
    "CALCULATED_SALES", col("UNITS_SOLD") * col("UNIT_PRICE")
)''',
    "Revenue, units and assignment AOV": '''totals = sales_df.agg(
    sf_sum("CALCULATED_SALES").alias("TOTAL_REVENUE"),
    sf_sum("UNITS_SOLD").alias("TOTAL_UNITS")
).collect()[0]
revenue = float(totals["TOTAL_REVENUE"])
units = int(totals["TOTAL_UNITS"])
per_unit = revenue / units if units else 0.0''',
    "Product sales performance": '''product_sf = sales_df.group_by("PRODUCT").agg(
    sf_sum("CALCULATED_SALES").alias("REVENUE"),
    sf_sum("UNITS_SOLD").alias("UNITS_SOLD")
).sort(col("REVENUE").desc())''',
    "Monthly revenue trends": '''monthly_sf = sales_df.with_column(
    "SALE_MONTH", date_trunc("MONTH", to_date(col("DATE")))
).group_by("SALE_MONTH").agg(
    sf_sum("CALCULATED_SALES").alias("REVENUE")
).sort("SALE_MONTH")''',
    "Regional revenue": '''regional_sf = sales_df.group_by("REGION").agg(
    sf_sum("CALCULATED_SALES").alias("REVENUE")
).sort(col("REVENUE").desc())''',
    "Regional product mix": '''regional_product_sf = sales_df.group_by("REGION", "PRODUCT").agg(
    sf_sum("CALCULATED_SALES").alias("REVENUE")
)''',
}
EXPLAIN = {
    "Load and calculate sales": "Reads the Snowflake SALES_RAW table and calculates revenue as units sold × unit price.",
    "Revenue, units and assignment AOV": "Snowpark totals revenue and units; Python divides them to produce the assignment's AOV (revenue per unit).",
    "Product sales performance": "Snowpark groups sales by product and aggregates both revenue and units sold. Powers the product bar and pie charts.",
    "Monthly revenue trends": "Snowpark converts dates to month starts and sums revenue by month. Powers the line and area charts.",
    "Regional revenue": "Snowpark groups by region and ranks regions by revenue. Powers the horizontal bar chart.",
    "Regional product mix": "Snowpark groups by region and product to produce the stacked regional chart.",
}

try:
    session = get_active_session()
    scope = {"session": session, "col": col, "sf_sum": sf_sum,
             "date_trunc": date_trunc, "to_date": to_date}
    for snippet in CODE.values():
        exec(snippet, {}, scope)
    revenue, units, per_unit = (scope[k] for k in ("revenue", "units", "per_unit"))
    product = scope["product_sf"].to_pandas()
    monthly = scope["monthly_sf"].to_pandas()
    regional = scope["regional_sf"].to_pandas()
    regional_product = scope["regional_product_sf"].to_pandas()
except Exception as exc:
    st.error("Unable to load retail sales data from Snowflake. Check the database/table and permissions.")
    st.exception(exc)
    st.stop()

monthly["SALE_MONTH"] = pd.to_datetime(monthly["SALE_MONTH"])
monthly["MONTH"] = monthly["SALE_MONTH"].dt.strftime("%Y-%m")
product = product.sort_values("REVENUE", ascending=False)
regional = regional.sort_values("REVENUE", ascending=False)
monthly = monthly.sort_values("SALE_MONTH")

# Two-column design: live dashboard on left; Snowpark code on right.
dashboard, inspector = st.columns([3, 2], gap="large")
with inspector:
    st.subheader("Snowpark Code Inspector")
    st.caption("Select any calculation below to inspect the actual executed Snowpark/Python code.")
    selected = st.selectbox("Inspect a KPI or chart calculation", list(CODE.keys()), index=1)
    st.code(CODE[selected], language="python")
    st.info(EXPLAIN[selected])
    st.caption("Calculation runs in Snowpark; visualization is rendered separately in Streamlit/Altair.")

with dashboard:
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Revenue", f"${revenue:,.2f}")
    k2.metric("Units Sold", f"{units:,}")
    k3.metric("Assignment AOV", f"${per_unit:,.2f}")
    st.caption("Assignment AOV = total revenue ÷ units sold; this is revenue per unit, not order-level AOV.")

    st.header("1. Product Sales Performance")
    st.caption("Inspector: select ‘Product sales performance’ to see the code behind both charts.")
    st.subheader("Revenue by Product")
    st.bar_chart(product.set_index("PRODUCT")["REVENUE"], x_label="Product", y_label="Revenue ($)")
    st.subheader("Product Revenue Share")
    pie = alt.Chart(product).mark_arc().encode(
        theta=alt.Theta("REVENUE:Q"), color=alt.Color("PRODUCT:N"),
        tooltip=["PRODUCT:N", alt.Tooltip("REVENUE:Q", format=",.2f")]
    )
    st.altair_chart(pie, use_container_width=True)

    st.header("2. Monthly Trends")
    st.caption("Inspector: select ‘Monthly revenue trends’ for the Snowpark grouping code.")
    st.subheader("Monthly Revenue — Line")
    st.line_chart(monthly.set_index("MONTH")["REVENUE"], x_label="Month", y_label="Revenue ($)")
    st.subheader("Monthly Revenue — Area")
    st.area_chart(monthly.set_index("MONTH")["REVENUE"], x_label="Month", y_label="Revenue ($)")
    st.warning("April 2023 is a partial month (through April 10); do not compare its total directly to full months.")

    st.header("3. Regional Insights")
    st.subheader("Revenue by Region")
    region_chart = alt.Chart(regional).mark_bar().encode(
        x=alt.X("REVENUE:Q", title="Revenue ($)"),
        y=alt.Y("REGION:N", sort="-x", title="Region"),
        tooltip=["REGION:N", alt.Tooltip("REVENUE:Q", format=",.2f")]
    )
    st.altair_chart(region_chart, use_container_width=True)
    st.subheader("Product Revenue by Region")
    stacked = alt.Chart(regional_product).mark_bar().encode(
        x=alt.X("REGION:N", title="Region"),
        y=alt.Y("REVENUE:Q", title="Revenue ($)", stack="zero"),
        color="PRODUCT:N",
        tooltip=["REGION:N", "PRODUCT:N", alt.Tooltip("REVENUE:Q", format=",.2f")]
    )
    st.altair_chart(stacked, use_container_width=True)

    with st.expander("View underlying aggregated results"):
        st.write("Product", product)
        st.write("Regional", regional)
        st.write("Monthly", monthly[["MONTH", "REVENUE"]])
        st.write("Regional product mix", regional_product)

st.divider()
st.caption("Source: Snowflake SALES_RAW | Snowpark calculations | Streamlit and Altair charts")
