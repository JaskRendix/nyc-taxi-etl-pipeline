import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

# -----------------------------
# Config
# -----------------------------

DEFAULT_DB_URI = "postgresql://postgres:postgres@localhost:5432/taxi"
DEFAULT_TABLE = "yellowcab_cleaned"

DB_URI = os.getenv("DB_URI", DEFAULT_DB_URI)
TABLE_NAME = os.getenv("TABLE_NAME", DEFAULT_TABLE)


@st.cache_data(show_spinner=True)
def load_data(limit: int | None = None) -> pd.DataFrame:
    engine = create_engine(DB_URI)
    query = f"SELECT * FROM {TABLE_NAME}"
    if limit is not None:
        query += f" LIMIT {limit}"
    return pd.read_sql(query, engine)


# -----------------------------
# Layout
# -----------------------------

st.set_page_config(page_title="NYC Taxi ETL Dashboard", layout="wide")

st.title("🚕 NYC Taxi ETL Dashboard")
st.caption("Backed by Dockerized PostgreSQL and a Python ETL pipeline.")

# Controls
with st.sidebar:
    st.header("Settings")
    sample_size = st.selectbox(
        "Sample size",
        options=[10_000, 50_000, 100_000, None],
        format_func=lambda x: "All rows" if x is None else f"{x:,}",
        index=0,
    )

    show_anomalies_only = st.checkbox("Show anomalies only", value=False)

# Load data
df = load_data(limit=sample_size)

if df.empty:
    st.warning("No data found in the table. Run the ETL pipeline first.")
    st.stop()

# Basic info
st.subheader("Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Rows loaded", f"{len(df):,}")
if "trip_distance" in df.columns:
    col2.metric("Avg distance (mi)", f"{df['trip_distance'].mean():.2f}")
if "fare_amount" in df.columns:
    col3.metric("Avg fare ($)", f"{df['fare_amount'].mean():.2f}")

# Filter anomalies if flags exist
anomaly_cols = [
    c for c in df.columns if c.startswith("is_") and df[c].dtype == bool
]

if show_anomalies_only and anomaly_cols:
    mask = False
    for c in anomaly_cols:
        mask = mask | df[c]
    df_view = df[mask].copy()
else:
    df_view = df.copy()

# Time-based analysis
if "tpep_pickup_datetime" in df_view.columns:
    st.subheader("Trips by pickup hour")
    df_view["pickup_hour"] = pd.to_datetime(
        df_view["tpep_pickup_datetime"]
    ).dt.hour
    hourly_counts = df_view.groupby("pickup_hour").size().reset_index(name="count")
    st.bar_chart(hourly_counts.set_index("pickup_hour"))

# Fare distribution
if "fare_amount" in df_view.columns:
    st.subheader("Fare distribution")

    import altair as alt

    chart = (
        alt.Chart(df_view)
        .mark_bar()
        .encode(
            x=alt.X("fare_amount:Q", bin=alt.Bin(maxbins=50)),
            y="count()",
        )
        .properties(height=300)
    )

    st.altair_chart(chart, width="stretch")



# Anomaly breakdown
if anomaly_cols:
    st.subheader("Anomaly flags")
    counts = {
        col: int(df_view[col].sum())
        for col in anomaly_cols
    }
    st.write(counts)

# Raw data preview
st.subheader("Sample data")
st.dataframe(df_view.head(100))
