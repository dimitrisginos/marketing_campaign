# =============================================================
#  Marketing Campaign Performance — Streamlit Dashboard
#  File    : dashboard.py
#  Run     : streamlit run dashboard.py
# =============================================================

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import gdown
import os

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Marketing Campaign Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Colors ────────────────────────────────────────────────────
GREEN = "#2ecc71"
RED   = "#e74c3c"
GRAY  = "#95a5a6"
NAVY  = "#2c3e50"
BLUE  = "#3498db"

# ── Data loading & cleaning ───────────────────────────────────
@st.cache_data
def load_data():
    file_path = "marketing_campaign_dataset.csv"
    if not os.path.exists(file_path):
        gdown.download(
            "https://drive.google.com/uc?id=1m9KxNp6GBdGX9oN0Qfr5IWtTs-4kklG-",
            file_path,
            quiet=False,
        )

    df = pd.read_csv(file_path)

    if df["Acquisition_Cost"].dtype == object:
        df["Acquisition_Cost"] = (
            df["Acquisition_Cost"]
            .str.replace(r"[\$,]", "", regex=True)
            .astype(float)
        )

    df["Date"]           = pd.to_datetime(df["Date"])
    df["CTR"]            = (df["Clicks"] / df["Impressions"]).round(4)
    df["Cost_per_Click"] = (
        df["Acquisition_Cost"] / df["Clicks"].replace(0, np.nan)
    ).round(2)

    if "Duration_Days" not in df.columns:
        df["Duration_Days"] = df["Duration"].str.extract(r"(\d+)").astype(int)
    else:
        df["Duration_Days"] = df["Duration_Days"].astype(int)

    df["Month_num"] = df["Date"].dt.month
    return df

df = load_data()

# ── Sidebar filters ───────────────────────────────────────────
st.sidebar.title("🔍 Filters")

sel_channels  = st.sidebar.multiselect("Channel",          sorted(df["Channel_Used"].unique()),     default=sorted(df["Channel_Used"].unique()))
sel_campaigns = st.sidebar.multiselect("Campaign Type",    sorted(df["Campaign_Type"].unique()),    default=sorted(df["Campaign_Type"].unique()))
sel_locations = st.sidebar.multiselect("Location",         sorted(df["Location"].unique()),         default=sorted(df["Location"].unique()))
sel_segments  = st.sidebar.multiselect("Customer Segment", sorted(df["Customer_Segment"].unique()), default=sorted(df["Customer_Segment"].unique()))

date_min, date_max = df["Date"].min(), df["Date"].max()
sel_dates = st.sidebar.date_input(
    "Date range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)

mask = (
    df["Channel_Used"].isin(sel_channels) &
    df["Campaign_Type"].isin(sel_campaigns) &
    df["Location"].isin(sel_locations) &
    df["Customer_Segment"].isin(sel_segments) &
    df["Date"].between(pd.Timestamp(sel_dates[0]), pd.Timestamp(sel_dates[1]))
)
dff = df[mask].copy()

if dff.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# ── Title & KPIs ──────────────────────────────────────────────
st.title("📊 Marketing Campaign Performance Dashboard")
st.caption(f"Showing **{len(dff):,}** of **{len(df):,}** campaigns after filters")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Avg ROI",              f"{dff['ROI'].mean():.2f}")
k2.metric("Avg Conversion Rate",  f"{dff['Conversion_Rate'].mean()*100:.1f}%")
k3.metric("Avg Acquisition Cost", f"${dff['Acquisition_Cost'].mean():,.0f}")
k4.metric("Avg CTR",              f"{dff['CTR'].mean()*100:.1f}%")
k5.metric("Avg Engagement Score", f"{dff['Engagement_Score'].mean():.1f}/10")
st.divider()

# =============================================================
#  Q1 — Campaign Type: ROI & Engagement
# =============================================================
st.subheader("Q1 — Which Campaign Type delivers the best ROI?")

q1 = (
    dff.groupby("Campaign_Type")
    .agg(Avg_ROI=("ROI", "mean"), Avg_Engagement=("Engagement_Score", "mean"))
    .round(3)
    .sort_values("Avg_ROI", ascending=False)
    .reset_index()
)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(q1, x="Campaign_Type", y="Avg_ROI",
                 color="Avg_ROI", color_continuous_scale="RdYlGn",
                 text=q1["Avg_ROI"].map("{:.2f}".format),
                 title="Avg ROI by Campaign Type")
    fig.add_hline(y=q1["Avg_ROI"].mean(), line_dash="dash", line_color=NAVY,
                  annotation_text=f"Avg: {q1['Avg_ROI'].mean():.2f}",
                  annotation_position="top right")
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Avg ROI")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    q1e = q1.sort_values("Avg_Engagement", ascending=False)
    fig2 = px.bar(q1e, x="Campaign_Type", y="Avg_Engagement",
                  color="Avg_Engagement", color_continuous_scale="RdYlGn",
                  text=q1e["Avg_Engagement"].map("{:.2f}".format),
                  title="Avg Engagement Score by Campaign Type (1–10)")
    fig2.add_hline(y=q1e["Avg_Engagement"].mean(), line_dash="dash", line_color=NAVY,
                   annotation_text=f"Avg: {q1e['Avg_Engagement'].mean():.2f}",
                   annotation_position="top right")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(coloraxis_showscale=False, xaxis_title="",
                       yaxis_title="Engagement Score", yaxis_range=[0, 11])
    st.plotly_chart(fig2, use_container_width=True)

st.info(
    f"**★ Key Finding Q1:** Best → **{q1.iloc[0]['Campaign_Type']}** "
    f"(ROI {q1.iloc[0]['Avg_ROI']:.2f}) | "
    f"Worst → **{q1.iloc[-1]['Campaign_Type']}** "
    f"(ROI {q1.iloc[-1]['Avg_ROI']:.2f}) | "
    f"Gap: **{q1.iloc[0]['Avg_ROI'] - q1.iloc[-1]['Avg_ROI']:.2f}** units"
)
st.divider()

# =============================================================
#  Q4 — Audience Segmentation
# =============================================================
st.subheader("Q4 — Which Audience Segment converts best at the lowest cost?")

q4 = (
    dff.groupby("Target_Audience")
    .agg(
        Avg_Conv_Rate  =("Conversion_Rate",  "mean"),
        Avg_Acq_Cost   =("Acquisition_Cost", "mean"),
        Avg_Engagement =("Engagement_Score", "mean"),
    )
    .round(3)
    .sort_values("Avg_Conv_Rate", ascending=False)
    .reset_index()
)

col1, col2, col3 = st.columns(3)

with col1:
    fig = px.bar(q4, x="Target_Audience", y=q4["Avg_Conv_Rate"] * 100,
                 color=q4["Avg_Conv_Rate"], color_continuous_scale="RdYlGn",
                 text=(q4["Avg_Conv_Rate"] * 100).map("{:.1f}%".format),
                 title="Avg Conversion Rate (%)")
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Conv Rate (%)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    q4c = q4.sort_values("Avg_Acq_Cost")
    fig2 = px.bar(q4c, y="Target_Audience", x="Avg_Acq_Cost", orientation="h",
                  color="Avg_Acq_Cost", color_continuous_scale="RdYlGn_r",
                  text=q4c["Avg_Acq_Cost"].map("${:,.0f}".format),
                  title="Avg Acquisition Cost ($)")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(coloraxis_showscale=False, yaxis_title="",
                       xaxis_title="Acquisition Cost ($)")
    st.plotly_chart(fig2, use_container_width=True)

with col3:
    q4e = q4.sort_values("Avg_Engagement", ascending=False)
    fig3 = px.bar(q4e, x="Target_Audience", y="Avg_Engagement",
                  color="Avg_Engagement", color_continuous_scale="RdYlGn",
                  text=q4e["Avg_Engagement"].map("{:.1f}".format),
                  title="Avg Engagement Score (1–10)")
    fig3.update_traces(textposition="outside")
    fig3.update_layout(coloraxis_showscale=False, xaxis_title="",
                       yaxis_title="Engagement Score", yaxis_range=[0, 11])
    st.plotly_chart(fig3, use_container_width=True)

st.info(
    f"**★ Key Finding Q4:** Best → **{q4.iloc[0]['Target_Audience']}** "
    f"(Conv {q4.iloc[0]['Avg_Conv_Rate']*100:.1f}%, Cost ${q4.iloc[0]['Avg_Acq_Cost']:,.0f}) | "
    f"Worst → **{q4.iloc[-1]['Target_Audience']}** "
    f"(Conv {q4.iloc[-1]['Avg_Conv_Rate']*100:.1f}%, Cost ${q4.iloc[-1]['Avg_Acq_Cost']:,.0f})"
)
st.divider()

# =============================================================
#  Q6 — Campaign Type × Audience Heatmaps
# =============================================================
st.subheader("Q6 — Which Campaign × Audience combo maximizes ROI?")

q6_roi  = dff.groupby(["Campaign_Type", "Target_Audience"])["ROI"].mean().round(2).unstack()
q6_conv = dff.groupby(["Campaign_Type", "Target_Audience"])["Conversion_Rate"].mean().round(4).unstack()

col1, col2 = st.columns(2)

with col1:
    fig = px.imshow(q6_roi, text_auto=".2f", color_continuous_scale="RdYlGn",
                    aspect="auto", title="ROI: Campaign Type × Target Audience",
                    zmin=2, zmax=8)
    fig.update_layout(xaxis_title="Target Audience", yaxis_title="Campaign Type")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = px.imshow(q6_conv * 100, text_auto=".1f", color_continuous_scale="Blues",
                     aspect="auto", title="Conversion Rate (%): Campaign × Audience",
                     zmin=0, zmax=15)
    fig2.update_layout(xaxis_title="Target Audience", yaxis_title="Campaign Type")
    st.plotly_chart(fig2, use_container_width=True)

best_combo  = q6_roi.stack().idxmax()
worst_combo = q6_roi.stack().idxmin()
st.info(
    f"**★ Key Finding Q6:** Best combo → **{best_combo[0]} + {best_combo[1]}** "
    f"(ROI {q6_roi.stack().max():.2f}) | "
    f"Worst → **{worst_combo[0]} + {worst_combo[1]}** "
    f"(ROI {q6_roi.stack().min():.2f})"
)
st.divider()

# =============================================================
#  Q7 — Geographic Performance
# =============================================================
st.subheader("Q7 — Which City performs best per Campaign Type?")

q7 = dff.groupby(["Location", "Campaign_Type"])["ROI"].mean().round(2).unstack()
q7_avg = (
    dff.groupby("Location")
    .agg(Avg_ROI=("ROI", "mean"))
    .round(3)
    .sort_values("Avg_ROI", ascending=True)
)

col1, col2 = st.columns(2)

with col1:
    fig = px.imshow(q7, text_auto=".2f", color_continuous_scale="YlOrRd",
                    aspect="auto", title="ROI Heatmap: Location × Campaign Type")
    fig.update_layout(xaxis_title="Campaign Type", yaxis_title="Location")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = px.bar(q7_avg.reset_index(), y="Location", x="Avg_ROI", orientation="h",
                  color="Avg_ROI", color_continuous_scale="RdYlGn",
                  text=q7_avg["Avg_ROI"].reset_index(drop=True).map("{:.2f}".format),
                  title="Overall Avg ROI by City")
    fig2.add_vline(x=q7_avg["Avg_ROI"].mean(), line_dash="dash", line_color=NAVY,
                   annotation_text=f"Avg: {q7_avg['Avg_ROI'].mean():.2f}",
                   annotation_position="top right")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="Avg ROI")
    st.plotly_chart(fig2, use_container_width=True)

best_city  = q7_avg.index[-1]
worst_city = q7_avg.index[0]
st.info(
    f"**★ Key Finding Q7:** Best city → **{best_city}** "
    f"(ROI {q7_avg.loc[best_city, 'Avg_ROI']:.2f}) | "
    f"Worst → **{worst_city}** "
    f"(ROI {q7_avg.loc[worst_city, 'Avg_ROI']:.2f})"
)
st.divider()

# =============================================================
#  Q9 — Campaign Duration Analysis
# =============================================================
st.subheader("Q9 — What is the optimal Campaign Duration?")

q9 = (
    dff.groupby("Duration_Days")
    .agg(
        Avg_ROI   =("ROI",             "mean"),
        Avg_Cost  =("Acquisition_Cost","mean"),
        Avg_Clicks=("Clicks",          "mean"),
    )
    .round(3)
    .reset_index()
)
dur_labels     = q9["Duration_Days"].astype(str) + " days"
best_dur       = q9.loc[q9["Avg_ROI"].idxmax(),  "Duration_Days"]
worst_cost_dur = q9.loc[q9["Avg_Cost"].idxmax(), "Duration_Days"]

col1, col2, col3 = st.columns(3)

with col1:
    fig = go.Figure(go.Bar(
        x=dur_labels, y=q9["Avg_ROI"],
        marker_color=[GREEN if d == best_dur else GRAY for d in q9["Duration_Days"]],
        text=q9["Avg_ROI"].map("{:.2f}".format), textposition="outside",
    ))
    fig.add_hline(y=q9["Avg_ROI"].mean(), line_dash="dash", line_color=NAVY,
                  annotation_text=f"Avg: {q9['Avg_ROI'].mean():.2f}")
    fig.update_layout(title="Avg ROI by Duration", yaxis_title="Avg ROI",
                      yaxis_range=[0, q9["Avg_ROI"].max() * 1.2])
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = go.Figure(go.Scatter(
        x=q9["Duration_Days"], y=q9["Avg_Clicks"],
        mode="lines+markers+text",
        text=q9["Avg_Clicks"].map("{:.0f}".format), textposition="top center",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=9, color=BLUE, line=dict(color="white", width=2)),
        fill="tozeroy", fillcolor="rgba(52,152,219,0.12)",
    ))
    fig2.update_layout(title="Avg Clicks by Duration",
                       xaxis=dict(tickvals=q9["Duration_Days"]),
                       xaxis_title="Duration (days)", yaxis_title="Avg Clicks")
    st.plotly_chart(fig2, use_container_width=True)

with col3:
    fig3 = go.Figure(go.Bar(
        x=dur_labels, y=q9["Avg_Cost"],
        marker_color=[RED if d == worst_cost_dur else GRAY for d in q9["Duration_Days"]],
        text=q9["Avg_Cost"].map("${:,.0f}".format), textposition="outside",
    ))
    fig3.update_layout(title="Avg Acquisition Cost ($) by Duration",
                       yaxis_title="Acquisition Cost ($)")
    st.plotly_chart(fig3, use_container_width=True)

best_d  = q9.loc[q9["Avg_ROI"].idxmax()]
worst_d = q9.loc[q9["Avg_ROI"].idxmin()]
st.info(
    f"**★ Key Finding Q9:** Sweet spot → **{int(best_d['Duration_Days'])} days** "
    f"(ROI {best_d['Avg_ROI']:.2f}, Cost ${best_d['Avg_Cost']:,.0f}) | "
    f"Worst → **{int(worst_d['Duration_Days'])} days** "
    f"(ROI {worst_d['Avg_ROI']:.2f})"
)
st.divider()

# =============================================================
#  Q2 — Channel ROI vs Cost Efficiency
# =============================================================
st.subheader("Q2 — Which Channel gives the best ROI at the lowest cost?")

q2 = (
    dff.groupby("Channel_Used")
    .agg(
        Avg_ROI =("ROI",             "mean"),
        Avg_Cost=("Acquisition_Cost","mean"),
        Avg_Conv=("Conversion_Rate", "mean"),
        Avg_CTR =("CTR",             "mean"),
    )
    .round(3)
    .sort_values("Avg_ROI", ascending=False)
    .reset_index()
)
q2["Efficiency"] = (q2["Avg_ROI"] / (q2["Avg_Cost"] / 1000)).round(3)

col1, col2, col3 = st.columns(3)

with col1:
    fig = px.bar(q2, x="Channel_Used", y="Avg_ROI",
                 color="Avg_ROI", color_continuous_scale="RdYlGn",
                 text=q2["Avg_ROI"].map("{:.2f}".format),
                 title="Avg ROI by Channel")
    fig.add_hline(y=q2["Avg_ROI"].mean(), line_dash="dash", line_color=NAVY,
                  annotation_text=f"Avg: {q2['Avg_ROI'].mean():.2f}",
                  annotation_position="top right")
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Avg ROI")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    q2c = q2.sort_values("Avg_Cost")
    fig2 = px.bar(q2c, y="Channel_Used", x="Avg_Cost", orientation="h",
                  color="Avg_Cost", color_continuous_scale="RdYlGn_r",
                  text=q2c["Avg_Cost"].map("${:,.0f}".format),
                  title="Avg Acquisition Cost ($) by Channel")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(coloraxis_showscale=False, yaxis_title="",
                       xaxis_title="Acquisition Cost ($)")
    st.plotly_chart(fig2, use_container_width=True)

with col3:
    med_cost = q2["Avg_Cost"].median()
    med_roi  = q2["Avg_ROI"].median()
    pt_colors = [
        GREEN if (r["Avg_Cost"] < med_cost and r["Avg_ROI"] > med_roi)
        else RED if (r["Avg_Cost"] > med_cost and r["Avg_ROI"] < med_roi)
        else BLUE
        for _, r in q2.iterrows()
    ]
    fig3 = go.Figure()
    fig3.add_vline(x=med_cost, line_dash="dash", line_color="gray", opacity=0.5)
    fig3.add_hline(y=med_roi,  line_dash="dash", line_color="gray", opacity=0.5)
    fig3.add_trace(go.Scatter(
        x=q2["Avg_Cost"], y=q2["Avg_ROI"],
        mode="markers+text",
        text=q2["Channel_Used"], textposition="top right",
        marker=dict(
            size=q2["Avg_Conv"] * 400,
            color=pt_colors,
            line=dict(color="white", width=2),
            opacity=0.85,
        ),
    ))
    fig3.add_annotation(x=q2["Avg_Cost"].min(), y=q2["Avg_ROI"].max(),
                        text="✅ Best zone", showarrow=False,
                        font=dict(color=GREEN, size=10), xanchor="left")
    fig3.add_annotation(x=q2["Avg_Cost"].max(), y=q2["Avg_ROI"].min(),
                        text="❌ Worst zone", showarrow=False,
                        font=dict(color=RED, size=10), xanchor="right")
    fig3.update_layout(title="ROI vs Cost  (bubble size = Conversion Rate)",
                       xaxis_title="Avg Acquisition Cost ($)",
                       yaxis_title="Avg ROI", showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

best_ch  = q2.iloc[0]
worst_ch = q2.iloc[-1]
best_eff = q2.loc[q2["Efficiency"].idxmax()]
st.info(
    f"**★ Key Finding Q2:** Best ROI → **{best_ch['Channel_Used']}** "
    f"(ROI {best_ch['Avg_ROI']:.2f}, Cost ${best_ch['Avg_Cost']:,.0f}) | "
    f"Worst → **{worst_ch['Channel_Used']}** (ROI {worst_ch['Avg_ROI']:.2f}) | "
    f"Best value → **{best_eff['Channel_Used']}** "
    f"(Efficiency: {best_eff['Efficiency']:.3f} ROI/$1K)"
)
st.divider()

# =============================================================
#  Final Summary
# =============================================================
st.subheader("📋 Final Business Recommendations")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
**1. Campaign Type** → Use **{q1.iloc[0]['Campaign_Type']}**
ROI {q1.iloc[0]['Avg_ROI']:.2f} vs avg {q1['Avg_ROI'].mean():.2f}

**2. Target Audience** → Focus on **{q4.iloc[0]['Target_Audience']}**
Conv Rate {q4.iloc[0]['Avg_Conv_Rate']*100:.1f}% — highest segment
""")

with col2:
    st.markdown(f"""
**3. Best Combo** → **{best_combo[0]}** + **{best_combo[1]}**
ROI {q6_roi.stack().max():.2f} — top Campaign × Audience

**4. Top City** → **{best_city}**
ROI {q7_avg.loc[best_city, 'Avg_ROI']:.2f} — best geographic market
""")

with col3:
    st.markdown(f"""
**5. Duration** → **{int(best_d['Duration_Days'])} days** is the sweet spot
ROI {best_d['Avg_ROI']:.2f} — beyond this returns diminish

**6. Best Channel** → **{best_ch['Channel_Used']}**
ROI {best_ch['Avg_ROI']:.2f} at ${best_ch['Avg_Cost']:,.0f} avg cost
""")