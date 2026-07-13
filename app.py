import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------
# STEP 2 — Page Config
# -----------------------------------------------------------------------
st.set_page_config(layout="wide")
st.title("Provisional Natality Data Dashboard")
st.markdown("#### Birth Analysis by State and Gender")

DATA_FILE = "Provisional_Natality_2025_CDC.csv"

REQUIRED_FIELDS = [
    "state_of_residence",
    "month",
    "month_code",
    "year_code",
    "sex_of_infant",
    "births",
]

# -----------------------------------------------------------------------
# STEP 3 — Load Data
# -----------------------------------------------------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    # Normalize column names: strip whitespace, lowercase, replace spaces
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df


df = None
load_error = None

try:
    df = load_data(DATA_FILE)
except FileNotFoundError:
    st.error("Dataset file not found in repository.")
except Exception as e:
    load_error = str(e)
    st.error(f"An error occurred while loading the dataset: {load_error}")

if df is not None:
    # Validate required logical fields are present
    missing_fields = [f for f in REQUIRED_FIELDS if f not in df.columns]

    if missing_fields:
        st.error(
            "The dataset is missing required logical fields: "
            + ", ".join(missing_fields)
        )
        st.write("Actual columns found in the dataset:")
        st.write(df.columns)
        st.stop()

    # Convert births to numeric, drop nulls
    df["births"] = pd.to_numeric(df["births"], errors="coerce")
    df = df.dropna(subset=["births"])

    # -------------------------------------------------------------------
    # STEP 4 — Sidebar Filters
    # -------------------------------------------------------------------
    st.sidebar.header("Filters")

    month_options = ["All"] + sorted(df["month"].dropna().unique().tolist())
    gender_options = ["All"] + sorted(df["sex_of_infant"].dropna().unique().tolist())
    state_options = ["All"] + sorted(df["state_of_residence"].dropna().unique().tolist())

    selected_months = st.sidebar.multiselect(
        "Month", options=month_options, default=["All"]
    )
    selected_genders = st.sidebar.multiselect(
        "Gender", options=gender_options, default=["All"]
    )
    selected_states = st.sidebar.multiselect(
        "State", options=state_options, default=["All"]
    )

    # -------------------------------------------------------------------
    # STEP 5 — Filtering Logic (does not mutate the original dataframe)
    # -------------------------------------------------------------------
    filtered_df = df.copy()

    if selected_months and "All" not in selected_months:
        filtered_df = filtered_df[filtered_df["month"].isin(selected_months)]

    if selected_genders and "All" not in selected_genders:
        filtered_df = filtered_df[filtered_df["sex_of_infant"].isin(selected_genders)]

    if selected_states and "All" not in selected_states:
        filtered_df = filtered_df[filtered_df["state_of_residence"].isin(selected_states)]

    # -------------------------------------------------------------------
    # STEP 9 — Edge Case: empty filter result
    # -------------------------------------------------------------------
    if filtered_df.empty:
        st.warning("No data available for the selected filter combination.")
    else:
        # -----------------------------------------------------------
        # STEP 6 — Aggregation
        # -----------------------------------------------------------
        agg_df = (
            filtered_df.groupby(["state_of_residence", "sex_of_infant"], as_index=False)[
                "births"
            ]
            .sum()
            .sort_values("state_of_residence")
        )

        # -----------------------------------------------------------
        # STEP 7 — Plot
        # -----------------------------------------------------------
        fig = px.bar(
            agg_df,
            x="state_of_residence",
            y="births",
            color="sex_of_infant",
            title="Total Births by State and Gender",
            labels={
                "state_of_residence": "State",
                "births": "Total Births",
                "sex_of_infant": "Gender",
            },
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend_title_text="Gender",
            xaxis_title="State",
            yaxis_title="Total Births",
            autosize=True,
        )

        st.plotly_chart(fig, use_container_width=True)

        # -----------------------------------------------------------
        # STEP 8 — Show Filtered Table
        # -----------------------------------------------------------
        st.subheader("Filtered Data")
        st.dataframe(filtered_df.reset_index(drop=True), hide_index=True, use_container_width=True)
