# file: bid_dashboard.py

import streamlit as st
import pandas as pd
import re

EXCEL_FILE = "gem_bid_analysis.xlsx"
SHEET_NAME = "Target_Keyword_Bids"

st.set_page_config(
    layout="wide",
    page_title="GeM Bid Intelligence Dashboard"
)

# ─────────────────────────────
# Keyword group definitions
# ─────────────────────────────
KEYWORD_GROUPS = {
    "Lead Acid / Planté": [
        "plante",
        "lead acid",
        "1652",
    ],
    "Traction Batteries": [
        "traction",
        "traction batter",
        "5154",
    ],
    "Diesel Loco": [
        "diesel loco",
        "7624",
    ],
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower())


def classify_keyword_group(items: str) -> str:
    text = normalize(items)
    for group, keywords in KEYWORD_GROUPS.items():
        if any(k in text for k in keywords):
            return group
    return "Other"


@st.cache_data
def load_data():
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    # Assign keyword group
    df["Keyword Group"] = df["Items"].apply(classify_keyword_group)

    # Safety: keep only defined groups
    df = df[df["Keyword Group"] != "Other"]

    return df


df = load_data()

# ─────────────────────────────
# Header
# ─────────────────────────────
st.title("📊 GeM Bid Intelligence Dashboard")
st.caption(
    "Keyword-based bid analysis: Lead Acid / Planté | Traction Batteries | Diesel Loco"
)

# ─────────────────────────────
# Summary Cards (by keyword group)
# ─────────────────────────────
st.subheader("📌 Summary by Keyword Group")

cols = st.columns(3)

for col, group in zip(cols, KEYWORD_GROUPS.keys()):
    subset = df[df["Keyword Group"] == group]
    with col:
        st.metric(
            label=group,
            value=len(subset)
        )

st.divider()

# ─────────────────────────────
# Drill-down Controls
# ─────────────────────────────
st.subheader("🔍 Drill-down Analysis")

group_filter = st.selectbox(
    "Select Keyword Group",
    options=["All"] + list(KEYWORD_GROUPS.keys())
)

if group_filter != "All":
    df_view = df[df["Keyword Group"] == group_filter]
else:
    df_view = df

# ─────────────────────────────
# Data Table
# ─────────────────────────────
st.dataframe(
    df_view[
        [
            "Keyword Group",
            "Bid No",
            "Items",
            "Quantity",
            "Department Name And Address",
            "Start Date",
            "End Date",
        ]
    ],
    use_container_width=True,
    height=520,
)

st.divider()

# ─────────────────────────────
# Export
# ─────────────────────────────
st.download_button(
    label="⬇ Download Filtered Data (CSV)",
    data=df_view.to_csv(index=False),
    file_name="keyword_group_filtered_bids.csv",
    mime="text/csv",
)
