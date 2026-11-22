from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Sellers Dashboard", page_icon="📊", layout="wide")

DATA_FILE = Path(__file__).parent / "sellers.xlsx"

@st.cache_data
def load_data(path):
    df = pd.read_excel(path)
    df["FULL NAME"] = df["NAME"] + " " + df["LASTNAME"]
    return df

df = load_data(DATA_FILE)

st.title("📊 Sellers Dashboard")
st.caption("Sales performance of sellers by region")

st.sidebar.header("Filters")

regions = sorted(df["REGION"].unique())

selected_regions = st.sidebar.multiselect("Region", options=regions, default=regions)

if st.sidebar.button("Show all regions"):
    selected_regions = regions

min_units = st.sidebar.slider(
    "Minimum units sold",
    min_value=int(df["SOLD UNITS"].min()),
    max_value=int(df["SOLD UNITS"].max()),
    value=int(df["SOLD UNITS"].min()),
)

filtered = df[df["REGION"].isin(selected_regions) & (df["SOLD UNITS"] >= min_units)]

if filtered.empty:
    st.warning("No sellers match the selected filters.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Sellers", len(filtered))
k2.metric("Units sold", f"{filtered['SOLD UNITS'].sum():,}")
k3.metric("Total sales", f"${filtered['TOTAL SALES'].sum():,}")
k4.metric("Avg. sales average", f"{filtered['SALES AVERAGE'].mean():.2%}")

tab_table, tab_charts, tab_vendor = st.tabs(["📋 Table", "📈 Charts", "👤 Vendor"])

with tab_table:
    st.subheader("Sellers table")
    st.write(f"Showing **{len(filtered)}** of {len(df)} sellers — regions: {', '.join(selected_regions)}")

    st.dataframe(
        filtered.drop(columns=["FULL NAME"]),
        width="stretch",
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(format="%d"),
            "INCOME": st.column_config.NumberColumn(format="$%d"),
            "TOTAL SALES": st.column_config.NumberColumn(format="$%d"),
            "SALES AVERAGE": st.column_config.NumberColumn(format="%.4f"),
        },
    )

    st.download_button(
        "⬇️ Download filtered data (CSV)",
        data=filtered.drop(columns=["FULL NAME"]).to_csv(index=False).encode("utf-8"),
        file_name="sellers_filtered.csv",
        mime="text/csv",
    )

with tab_charts:
    with st.container(border=True):
        st.subheader("Summary by region")

        by_region = (
            filtered.groupby("REGION", as_index=False)
            .agg({"SOLD UNITS": "sum", "TOTAL SALES": "sum", "SALES AVERAGE": "mean"})
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            fig = px.bar(by_region, x="REGION", y="SOLD UNITS", title="Units Sold")
            st.plotly_chart(fig, width="stretch")
        with c2:
            fig = px.bar(by_region, x="REGION", y="TOTAL SALES", title="Total Sales")
            st.plotly_chart(fig, width="stretch")
        with c3:
            fig = px.bar(by_region, x="REGION", y="SALES AVERAGE", title="Average Sales (mean)")
            st.plotly_chart(fig, width="stretch")

    with st.container(border=True):
        st.subheader("Detail by seller")

        metric = st.radio(
            "Metric",
            ["SOLD UNITS", "TOTAL SALES", "SALES AVERAGE"],
            format_func=lambda m: {"SOLD UNITS": "Units Sold",
                                   "TOTAL SALES": "Total Sales",
                                   "SALES AVERAGE": "Average Sales"}[m],
            horizontal=True,
        )

        sorted_df = filtered.sort_values(metric)
        fig = px.bar(
            sorted_df, x=metric, y="FULL NAME", color="REGION", orientation="h",
            height=max(400, 22 * len(sorted_df)),
        )
        fig.update_layout(yaxis_title=None)
        st.plotly_chart(fig, width="stretch")

        fig = px.scatter(
            filtered, x="SOLD UNITS", y="TOTAL SALES", color="REGION",
            hover_name="FULL NAME", title="Units Sold vs Total Sales",
        )
        st.plotly_chart(fig, width="stretch")

with tab_vendor:
    st.subheader("Vendor details")

    vendor_name = st.selectbox("Select a vendor", sorted(filtered["FULL NAME"]))

    if st.button("Show vendor data", type="primary"):
        vendor = filtered[filtered["FULL NAME"] == vendor_name].iloc[0]

        with st.container(border=True):
            st.markdown(f"### {vendor['FULL NAME']}")
            st.write(f"**ID:** {vendor['ID']}  |  **Region:** {vendor['REGION']}")

            region_df = df[df["REGION"] == vendor["REGION"]]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Income", f"${vendor['INCOME']:,}")
            m2.metric("Units sold", f"{vendor['SOLD UNITS']:,}",
                      delta=f"{vendor['SOLD UNITS'] - region_df['SOLD UNITS'].mean():,.0f} vs region avg")
            m3.metric("Total sales", f"${vendor['TOTAL SALES']:,}",
                      delta=f"{vendor['TOTAL SALES'] - region_df['TOTAL SALES'].mean():,.0f} vs region avg")
            m4.metric("Sales average", f"{vendor['SALES AVERAGE']:.4f}",
                      delta=f"{vendor['SALES AVERAGE'] - region_df['SALES AVERAGE'].mean():.4f} vs region avg")

            compare = pd.DataFrame({
                "Who": [vendor["FULL NAME"], f"Avg. {vendor['REGION']}"],
                "SOLD UNITS": [vendor["SOLD UNITS"], region_df["SOLD UNITS"].mean()],
                "TOTAL SALES": [vendor["TOTAL SALES"], region_df["TOTAL SALES"].mean()],
            })
            v1, v2 = st.columns(2)
            with v1:
                st.plotly_chart(px.bar(compare, x="Who", y="SOLD UNITS", title="Units Sold vs region"),
                                width="stretch")
            with v2:
                st.plotly_chart(px.bar(compare, x="Who", y="TOTAL SALES", title="Total Sales vs region"),
                                width="stretch")
    else:
        st.info("Choose a vendor and press **Show vendor data**.")
