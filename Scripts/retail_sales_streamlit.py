"""Retail Sales Performance | Streamlit dashboard with live Snowpark connection.

Run: python -m streamlit run Scripts/retail_sales_streamlit.py
For Streamlit Community Cloud, configure credentials in Streamlit secrets.
Never commit private keys or secrets.toml to GitHub.
"""
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
from snowflake.snowpark import Session
from streamlit.errors import StreamlitSecretNotFoundError
from snowflake.snowpark.functions import col, date_trunc, sum as sf_sum, to_date

# Snowflake object name is ANALISIS (with I), as verified in this project.
DB = "RETAIL_SALES_PERFORMANCE_ANALISIS"
TABLE = f"{DB}.PUBLIC.SALES_RAW"

st.set_page_config(page_title="Retail Sales Performance", layout="wide")
st.title("Retail Sales Performance Dashboard")
st.caption("DEA Project | Live Snowflake data • Snowpark Python calculations • Streamlit/Altair visualization")

# These snippets mirror the actual calculations in load_results().
CODE = {
    "load": '''sales_df = session.table(TABLE).with_column(
    "CALCULATED_SALES", col("UNITS_SOLD") * col("UNIT_PRICE")
)''',
    "kpis": '''totals = sales_df.agg(
    sf_sum("CALCULATED_SALES").alias("TOTAL_REVENUE"),
    sf_sum("UNITS_SOLD").alias("TOTAL_UNITS")
).collect()[0]
revenue = float(totals["TOTAL_REVENUE"] or 0)
units = int(totals["TOTAL_UNITS"] or 0)
per_unit = revenue / units if units else 0.0''',
    "product": '''product_sf = sales_df.group_by("PRODUCT").agg(
    sf_sum("CALCULATED_SALES").alias("REVENUE"),
    sf_sum("UNITS_SOLD").alias("UNITS_SOLD")
).sort(col("REVENUE").desc())''',
    "monthly": '''monthly_sf = sales_df.with_column(
    "SALE_MONTH", date_trunc("MONTH", to_date(col("DATE")))
).group_by("SALE_MONTH").agg(
    sf_sum("CALCULATED_SALES").alias("REVENUE")
).sort("SALE_MONTH")''',
    "regional": '''regional_sf = sales_df.group_by("REGION").agg(
    sf_sum("CALCULATED_SALES").alias("REVENUE")
).sort(col("REVENUE").desc())''',
    "mix": '''regional_product_sf = sales_df.group_by("REGION", "PRODUCT").agg(
    sf_sum("CALCULATED_SALES").alias("REVENUE")
)''',
}


def snowpark_code(title: str, key: str, explanation: str) -> None:
    """Show the relevant Snowpark calculation without an expander."""
    st.markdown(f"**Snowpark Python — {title}**")
    st.code(CODE[key], language="python")
    st.caption(explanation)


def get_session() -> Session:
    """Connect locally using a protected key, or in Cloud using app secrets."""
    try:
        cloud_config = dict(st.secrets["snowflake"])
    except (StreamlitSecretNotFoundError, KeyError):
        cloud_config = None

    if cloud_config is not None:
        cfg = cloud_config
        cfg.setdefault("database", DB)
        cfg.setdefault("schema", "PUBLIC")
        cfg.setdefault("role", "RETAIL_STREAMLIT_READER")
        cfg.setdefault("warehouse", "COMPUTE_WH")
        # A PEM stored in Streamlit secrets can be passed as private_key_file
        # only if it is an actual path; for inline PEM use cryptography.
        if "private_key" in cfg:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            pem = cfg.pop("private_key").replace("\\n", "\n").encode("utf-8")
            password = cfg.pop("private_key_passphrase", None)
            key = serialization.load_pem_private_key(
                pem,
                password=password.encode("utf-8") if password else None,
                backend=default_backend(),
            )
            cfg["private_key"] = key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        return Session.builder.configs(cfg).create()

    private_key_path = Path.home() / ".snowflake_keys" / "retail_streamlit_private_key.pem"
    if not private_key_path.is_file():
        raise FileNotFoundError(
            "Snowflake private key not found locally. Configure [snowflake] "
            "in Streamlit secrets for cloud deployment."
        )
    connection_parameters = {
        "account": "SICLDCG-ML41894",
        "user": "RETAIL_STREAMLIT_SERVICE",
        "private_key_file": str(private_key_path),
        "role": "RETAIL_STREAMLIT_READER",
        "warehouse": "COMPUTE_WH",
        "database": DB,
        "schema": "PUBLIC",
    }
    return Session.builder.configs(connection_parameters).create()


@st.cache_data(ttl=300, show_spinner="Loading live sales aggregates from Snowflake...")
def load_results():
    session = get_session()
    try:
        sales_df = session.table(TABLE).with_column(
            "CALCULATED_SALES", col("UNITS_SOLD") * col("UNIT_PRICE")
        )
        totals = sales_df.agg(
            sf_sum("CALCULATED_SALES").alias("TOTAL_REVENUE"),
            sf_sum("UNITS_SOLD").alias("TOTAL_UNITS")
        ).collect()[0]
        revenue = float(totals["TOTAL_REVENUE"] or 0)
        units = int(totals["TOTAL_UNITS"] or 0)
        per_unit = revenue / units if units else 0.0

        product_sf = sales_df.group_by("PRODUCT").agg(
            sf_sum("CALCULATED_SALES").alias("REVENUE"),
            sf_sum("UNITS_SOLD").alias("UNITS_SOLD")
        ).sort(col("REVENUE").desc())
        monthly_sf = sales_df.with_column(
            "SALE_MONTH", date_trunc("MONTH", to_date(col("DATE")))
        ).group_by("SALE_MONTH").agg(
            sf_sum("CALCULATED_SALES").alias("REVENUE")
        ).sort("SALE_MONTH")
        regional_sf = sales_df.group_by("REGION").agg(
            sf_sum("CALCULATED_SALES").alias("REVENUE")
        ).sort(col("REVENUE").desc())
        regional_product_sf = sales_df.group_by("REGION", "PRODUCT").agg(
            sf_sum("CALCULATED_SALES").alias("REVENUE")
        )
        return (revenue, units, per_unit, product_sf.to_pandas(),
                monthly_sf.to_pandas(), regional_sf.to_pandas(),
                regional_product_sf.to_pandas())
    finally:
        session.close()


if st.button("Refresh live Snowflake results", help="Clear the five-minute aggregate cache and rerun queries"):
    load_results.clear()

try:
    revenue, units, per_unit, product, monthly, regional, regional_product = load_results()
except Exception as exc:
    st.error("Unable to load retail sales data from Snowflake. Verify credentials, database, and role permissions.")
    st.exception(exc)
    st.stop()

monthly["SALE_MONTH"] = pd.to_datetime(monthly["SALE_MONTH"])
monthly["MONTH"] = monthly["SALE_MONTH"].dt.strftime("%Y-%m")
product = product.sort_values("REVENUE", ascending=False)
regional = regional.sort_values("REVENUE", ascending=False)
monthly = monthly.sort_values("SALE_MONTH")

st.header("Sales KPIs")
left, right = st.columns([3, 2], gap="large")
with left:
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Revenue", f"${revenue:,.2f}")
    k2.metric("Units Sold", f"{units:,}")
    k3.metric("Assignment AOV", f"${per_unit:,.2f}")
    st.caption("Assignment AOV = revenue ÷ units sold. This is revenue per unit, not order-level average order value.")
with right:
    snowpark_code("Revenue, units and assignment AOV", "kpis", "Snowpark aggregates revenue and units; Python computes revenue per unit.")

st.header("1. Product Sales Performance")
left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Revenue by Product")
    st.bar_chart(product.set_index("PRODUCT")["REVENUE"], x_label="Product", y_label="Revenue ($)")
with right:
    snowpark_code("Product revenue", "product", "Snowpark groups by product and sums calculated revenue and units sold.")
left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Product Revenue Share")
    pie = alt.Chart(product).mark_arc().encode(
        theta=alt.Theta("REVENUE:Q"), color=alt.Color("PRODUCT:N"),
        tooltip=["PRODUCT:N", alt.Tooltip("REVENUE:Q", format=",.2f")]
    )
    st.altair_chart(pie, use_container_width=True)
with right:
    snowpark_code("Product revenue share", "product", "The same Snowpark product totals feed this proportional chart; Altair handles rendering.")

st.header("2. Monthly Trends")
left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Monthly Revenue — Line")
    st.line_chart(monthly.set_index("MONTH")["REVENUE"], x_label="Month", y_label="Revenue ($)")
with right:
    snowpark_code("Monthly revenue line", "monthly", "Snowpark groups sales into calendar months and aggregates revenue.")
left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Monthly Revenue — Area")
    st.area_chart(monthly.set_index("MONTH")["REVENUE"], x_label="Month", y_label="Revenue ($)")
with right:
    snowpark_code("Monthly revenue area", "monthly", "The same Snowpark monthly aggregation feeds the area chart.")
st.warning("April 2023 may be a partial month; verify the date coverage before comparing it with full months.")

st.header("3. Regional Insights")
left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Revenue by Region")
    region_chart = alt.Chart(regional).mark_bar().encode(
        x=alt.X("REVENUE:Q", title="Revenue ($)"),
        y=alt.Y("REGION:N", sort="-x", title="Region"),
        tooltip=["REGION:N", alt.Tooltip("REVENUE:Q", format=",.2f")]
    )
    st.altair_chart(region_chart, use_container_width=True)
with right:
    snowpark_code("Regional revenue", "regional", "Snowpark groups by region and ranks regions by revenue.")
left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Product Revenue by Region")
    stacked = alt.Chart(regional_product).mark_bar().encode(
        x=alt.X("REGION:N", title="Region"),
        y=alt.Y("REVENUE:Q", title="Revenue ($)", stack="zero"),
        color="PRODUCT:N",
        tooltip=["REGION:N", "PRODUCT:N", alt.Tooltip("REVENUE:Q", format=",.2f")]
    )
    st.altair_chart(stacked, use_container_width=True)
with right:
    snowpark_code("Regional product mix", "mix", "Snowpark groups by region and product; Altair renders the stacked bars.")

# Permanent panel immediately before the aggregated-results section.
st.header("4. Snowpark Data Preparation")
left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Calculated Sales Pipeline")
    st.write("The SALES_RAW table is read directly from Snowflake. Snowpark creates CALCULATED_SALES = UNITS_SOLD × UNIT_PRICE before producing the KPIs and charts above.")
    st.caption(f"Source table: {TABLE}")
with right:
    snowpark_code("Loading and calculated sales", "load", "This is the Snowpark transformation used by every aggregation above.")

st.header("5. Aggregated Results")
with st.expander("View underlying aggregated results"):
    st.write("Product", product)
    st.write("Regional", regional)
    st.write("Monthly", monthly[["MONTH", "REVENUE"]])
    st.write("Regional product mix", regional_product)

st.divider()
st.caption("Source: Snowflake SALES_RAW | Snowpark calculations | Streamlit and Altair visualizations")
