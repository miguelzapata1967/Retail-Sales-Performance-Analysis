# Retail Sales Performance Analysis

**Data Engineering Academy project | Project creator: Miguel Zapata | Documentation updated: October 10, 2026**

## Project overview

This project analyzes historical retail sales to identify the highest-revenue products, regional differences, monthly trends, and relationships between units sold and revenue. It demonstrates an end-to-end data engineering and analytics workflow: CSV source → AWS S3 → Snowflake → Snowpark Python → interactive Streamlit dashboard.

The goal is to turn transaction-level sales records into evidence-based inventory, marketing and regional planning insights. The analysis is descriptive: it does not establish profitability, seasonality, or causal drivers.
## Live Interactive Dashboard

**[Launch Retail Sales Performance Dashboard](https://retail-sales-performance-analysis-3ljqj9bbnadj5akwzpma2j.streamlit.app/)**

This interactive dashboard was developed using **Snowflake, Snowpark Python, Streamlit, and Altair**.

The application provides:

- Sales KPIs, including total revenue, units sold, and revenue per unit.
- Product sales performance and revenue distribution.
- Monthly revenue trends.
- Regional sales performance and product mix.
- Live Snowflake data integration.
- **Snowpark Python code displayed alongside each corresponding visualization**, allowing users to examine the calculations behind the results.

**Technical architecture:** Snowflake → Snowpark Python → Streamlit → Interactive Dashboard.

*Developed as part of the Data Engineering Academy portfolio.*

## Project requirements and delivery (Steps 1–7)

| Step | Assignment requirement | Implementation/evidence |
|---|---|---|
| 1 | Explain source data and structure | Six fields documented below; source `sales.csv` |
| 2 | Inspect data for gaps, nulls and invalid formats | Snowflake SQL and Snowpark checks; 100 rows, no missing values or exact duplicates in verified tests |
| 3 | Define process and technology | AWS S3, Snowflake stage/integration, Snowpark Python, Streamlit; details in technical README |
| 4 | Build extraction/transformation/visualization pipeline | S3 raw CSV, Snowflake `SALES_RAW`, Snowpark derived revenue and groupings, Streamlit charts |
| 5 | Define and calculate five metrics | All five calculated in Snowpark; results below and in analysis README |
| 6 | Build Streamlit dashboard | Live Snowflake dashboard with KPI cards and product chart screenshot; project creator reports app complete |
| 7 | Submit documented deliverables, explain stack, include short video/presentation | Code, graphics, CSV outputs and READMEs packaged; video/presentation remains to be recorded |


## Project documentation

This `README.md` introduces the project, its purpose, architecture, deliverables and technology choices. The detailed work is intentionally separated into two supporting documents rather than repeated here:

- **[readme_analysis.md](readme_analysis.md)** — the five Step 5 questions, Snowpark-calculated metrics, verified results, charts, interpretation, and analytical limitations.
- **[readme_tech.md](readme_tech.md)** — the Step 1–4 data workflow, data-quality validation, AWS/Snowflake setup, Snowpark transformations, Streamlit implementation, configurations, troubleshooting, and supporting technical screenshots.

Supporting evidence and data exports are included in the `graph/` directory and CSV files in the project package. The [Streamlit dashboard](https://app.snowflake.com/sicldcg/ml41894/#/streamlit-apps/RETAIL_SALES_PERFORMANCE_ANALISIS.PUBLIC.DWN5JH4NDSTXJ4X8) is hosted in Snowflake and may require authorized sign-in.

## Why this technology stack? — Step 7.2

**AWS S3 — source-data storage.** S3 provides a durable, separate landing location for the original `sales.csv`, so raw input is retained independently of the transformations and dashboard. This follows the assignment's storage → transformation → visualization architecture.

**AWS IAM role and Snowflake storage integration — controlled access.** A narrowly scoped IAM role permits Snowflake to read the project's S3 location without embedding permanent AWS credentials in application code. The Snowflake external stage connects that location to the ingestion workflow.

**Snowflake — central data and compute platform.** Snowflake stores `SALES_RAW` and supports SQL-based inspection and quality checks. Keeping the dataset near the transformation engine avoids maintaining another analytical database.

**Snowpark Python — calculations executed in Snowflake.** Snowpark is the core analytical layer: Python expressions create calculated revenue (`UNITS_SOLD × UNIT_PRICE`), group sales by product, region, and month, and aggregate units and revenue. Unlike pulling the full raw dataset into a local Python script, Snowpark expresses the operations for execution by Snowflake. It also demonstrates the assignment's requirement to implement transformation logic in Python.

**Streamlit in Snowflake — interactive presentation.** Streamlit provides the dashboard, KPIs, chart selections, and interactive views directly in the Snowflake environment. It satisfies the assignment's requirement to avoid a separate BI dashboard tool. **Altair** supplies flexible chart types, while **pandas** is used only for formatting small aggregated results for display, not as the primary transformation engine.

### Snowpark Code Inspector — transparency and verifiability

A distinctive feature of this project is the **Snowpark Code Inspector** inside the Streamlit dashboard. When an evaluator selects a supported KPI, metric, or chart, the inspector displays the corresponding **Snowpark Python calculation code** and a short explanation of what it computes. This is important because a dashboard normally shows the result but hides the underlying analytical method.

The inspector helps a professor or reviewer:

- Trace displayed revenue, product rankings, monthly trends, and regional comparisons to the Snowpark transformations behind them.
- Distinguish **Snowpark calculation logic** from **Streamlit/Altair visualization code**.
- Review the methodology without having to navigate the notebook or GitHub repository for every calculation.

The inspector is an **explanation and code-transparency feature**, not an independent proof of execution. The underlying Snowpark queries and their displayed results remain the primary evidence. Technical implementation details are documented in [readme_tech.md](readme_tech.md).

**Git/GitHub — reproducible project delivery.** Version control keeps the Python source, documentation, and non-sensitive project artifacts organized for review and future updates. The raw data's sharing permissions should be reviewed before publication.

## Step 7 submission note

The project package contains the documentation, dashboard source, graphics, screenshots and CSV outputs. The assignment also requests a **short walkthrough video or presentation**, which must be recorded separately. A useful sequence is: architecture → data validation → Snowpark metrics → dashboard → Code Inspector → findings and limitations.

## AI assistance disclosure

AI assistance was used for code suggestions, debugging, documentation, and visualization preparation. The project creator, **Miguel Zapata**, executed and reviewed the Snowflake/Snowpark work and is responsible for the final project submission.
