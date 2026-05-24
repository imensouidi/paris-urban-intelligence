# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Paris Urban Intelligence",
    page_icon="🗼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CUSTOM CSS
# =========================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #050d1a;
        color: #cdd9f0;
    }

    .stApp { background-color: #050d1a; }

    section[data-testid="stSidebar"] {
        background-color: #07111f;
        border-right: 1px solid #0e2040;
    }

    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        color: #e8f0ff !important;
        letter-spacing: -0.02em;
    }

    .page-header {
        padding: 8px 0 24px 0;
        border-bottom: 1px solid #0e2040;
        margin-bottom: 28px;
    }

    .page-title {
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #e8f0ff;
        margin: 0;
        letter-spacing: -0.03em;
    }

    .page-subtitle {
        font-size: 0.85rem;
        color: #4a6fa5;
        margin-top: 4px;
        font-weight: 300;
    }

    .kpi-card {
        background: linear-gradient(145deg, #071828 0%, #091e30 100%);
        border: 1px solid #0e2a45;
        border-radius: 10px;
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #1a5fb4, #3584e4);
    }

    .kpi-value {
        font-family: 'Syne', sans-serif;
        font-size: 1.9rem;
        font-weight: 700;
        color: #7ab3f0;
        line-height: 1;
        margin-bottom: 6px;
    }

    .kpi-label {
        font-size: 0.72rem;
        color: #4a6fa5;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 500;
    }

    .kpi-delta {
        font-size: 0.78rem;
        color: #3584e4;
        margin-top: 4px;
    }

    .section-header {
        font-family: 'Syne', sans-serif;
        font-size: 1.05rem;
        font-weight: 600;
        color: #b0c8e8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 32px 0 14px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: #0e2040;
    }

    .insight-box {
        background: #071828;
        border: 1px solid #0e2a45;
        border-left: 3px solid #3584e4;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.83rem;
        color: #7a9fc4;
        margin-bottom: 16px;
    }

    .insight-box strong { color: #a8c8f0; }

    div[data-testid="stMultiSelect"] > div {
        background: #071828 !important;
        border: 1px solid #0e2a45 !important;
        border-radius: 8px !important;
    }

    .stMultiSelect [data-baseweb="tag"] {
        background: #0e2a45 !important;
        color: #7ab3f0 !important;
    }

    .stSelectbox > div > div {
        background: #071828 !important;
        border: 1px solid #0e2a45 !important;
    }

    label[data-testid="stWidgetLabel"] p {
        color: #4a6fa5 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 500;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #071828;
        border-radius: 8px;
        padding: 4px;
        border: 1px solid #0e2040;
        gap: 2px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #4a6fa5;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        font-weight: 500;
        padding: 8px 18px;
    }

    .stTabs [aria-selected="true"] {
        background: #0e2a45 !important;
        color: #7ab3f0 !important;
    }

    footer { display: none; }
</style>
""", unsafe_allow_html=True)

# =========================
# BLUE PALETTE — shades for 6 zones
# =========================

ZONE_ORDER  = ["chatelet", "gare_du_nord", "nation", "montparnasse", "saint_michel", "paris_centre"]
ZONE_LABELS = {z: z.replace("_", " ").title() for z in ZONE_ORDER}

BLUE_SHADES = {
    "chatelet":     "#1a5fb4",
    "gare_du_nord": "#2370d4",
    "nation":       "#3584e4",
    "montparnasse": "#57a0f8",
    "saint_michel": "#85bfff",
    "paris_centre": "#b8d9ff",
}

TRAFFIC_COLORS = {
    "High Traffic":   "#1a5fb4",
    "Medium Traffic": "#3584e4",
    "Low Traffic":    "#85bfff",
}

# Base Plotly layout — dark, clean
BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#7a9fc4", size=11),
    margin=dict(l=10, r=10, t=36, b=10),
    legend=dict(
        bgcolor="rgba(7,24,40,0.8)",
        bordercolor="#0e2040",
        borderwidth=1,
        font=dict(size=10, color="#7a9fc4")
    ),
    xaxis=dict(
        gridcolor="#0a1f35",
        linecolor="#0e2040",
        tickfont=dict(size=10, color="#4a6fa5"),
        title_font=dict(size=10, color="#4a6fa5")
    ),
    yaxis=dict(
        gridcolor="#0a1f35",
        linecolor="#0e2040",
        tickfont=dict(size=10, color="#4a6fa5"),
        title_font=dict(size=10, color="#4a6fa5")
    ),
)

# =========================
# DB CONNECTION
# =========================

@st.cache_resource
def get_engine():
    url = "mysql+pymysql://{}:{}@{}:{}/{}".format(
        os.getenv("MYSQL_USER"),
        os.getenv("MYSQL_PASSWORD"),
        os.getenv("MYSQL_HOST"),
        os.getenv("MYSQL_PORT"),
        os.getenv("MYSQL_DATABASE")
    )
    return create_engine(url)

engine = get_engine()

@st.cache_data(ttl=300)
def load_data():
    pollution_df = pd.read_sql("SELECT * FROM datamart_pollution", engine)
    traffic_df   = pd.read_sql("SELECT * FROM datamart_traffic",   engine)
    tp_df        = pd.read_sql("SELECT * FROM datamart_traffic_pollution", engine)
    return pollution_df, traffic_df, tp_df

pollution_df, traffic_df, tp_df = load_data()

# =========================
# SIDEBAR — FILTERS
# =========================

with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 0 20px 0;'>
        <div style='font-family: Syne, sans-serif; font-size: 1.1rem; font-weight: 700; color: #e8f0ff;'>🗼 Paris Urban</div>
        <div style='font-size: 0.72rem; color: #4a6fa5; margin-top: 2px;'>Intelligence Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("**Zone Selection**")
    # Select All / Clear All buttons
    col_a, col_b = st.columns(2)
    select_all = col_a.button("Select All", use_container_width=True)
    clear_all  = col_b.button("Clear All",  use_container_width=True)

    if "selected_zones" not in st.session_state or select_all:
        st.session_state.selected_zones = ZONE_ORDER.copy()
    if clear_all:
        st.session_state.selected_zones = []

    selected_zones = st.multiselect(
        "Choose zones to display",
        options=ZONE_ORDER,
        default=st.session_state.selected_zones,
        format_func=lambda z: ZONE_LABELS[z],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**Hour Range**")
    hour_range = st.slider(
        "Filter hours",
        min_value=0, max_value=23,
        value=(0, 23),
        format="%dh",
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**Traffic Level**")
    traffic_levels = st.multiselect(
        "Traffic level",
        options=["Low Traffic", "Medium Traffic", "High Traffic"],
        default=["Low Traffic", "Medium Traffic", "High Traffic"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption(f"Showing {len(selected_zones)} of 6 zones · Hours {hour_range[0]}h–{hour_range[1]}h")

# Guard against empty selection
if not selected_zones:
    st.warning("Please select at least one zone in the sidebar.")
    st.stop()

# =========================
# FILTER DATA
# =========================

pol_f  = pollution_df[pollution_df["zone"].isin(selected_zones)]
tra_f  = traffic_df[
    traffic_df["zone"].isin(selected_zones) &
    traffic_df["hour"].between(hour_range[0], hour_range[1])
]
tp_f   = tp_df[
    tp_df["zone"].isin(selected_zones) &
    tp_df["hour"].between(hour_range[0], hour_range[1]) &
    tp_df["traffic_level"].isin(traffic_levels)
]

# Summaries
pol_summary = (
    pol_f.groupby("zone")
    .agg(avg_pollution=("avg_pollution","mean"), max_pollution=("max_pollution","max"), avg_aqi=("avg_aqi","mean"))
    .round(1).reset_index().sort_values("avg_pollution", ascending=False)
)

tra_by_zone = (
    tra_f.groupby("zone")
    .agg(avg_traffic=("avg_traffic","mean"), max_traffic=("max_traffic","max"))
    .round(1).reset_index().sort_values("avg_traffic", ascending=False)
)

tra_by_hour = (
    tra_f.groupby(["hour","zone"])
    .agg(avg_traffic=("avg_traffic","mean"))
    .round(1).reset_index()
)

heatmap_df = (
    tra_f.groupby(["zone","hour"])
    .agg(avg_traffic=("avg_traffic","mean"))
    .round(1).reset_index()
)

tp_summary = (
    tp_f.groupby("zone")
    .agg(avg_traffic=("avg_traffic","mean"), avg_pollution=("avg_pollution","mean"),
         avg_temperature=("avg_temperature","mean"), avg_humidity=("avg_humidity","mean"))
    .round(1).reset_index()
)

level_summary = (
    tp_f.groupby("traffic_level")
    .agg(avg_pollution=("avg_pollution","mean"), count=("avg_pollution","count"))
    .round(1).reset_index()
)

# =========================
# PAGE HEADER
# =========================

st.markdown("""
<div class="page-header">
    <div class="page-title">Paris Urban Intelligence</div>
    <div class="page-subtitle">Air Quality & Traffic Analytics · Big Data Pipeline · Spark → Hive → MySQL</div>
</div>
""", unsafe_allow_html=True)

# =========================
# KPI ROW
# =========================

k1, k2, k3, k4, k5 = st.columns(5)

most_polluted  = ZONE_LABELS[pol_summary.iloc[0]["zone"]] if len(pol_summary) else "—"
cleanest       = ZONE_LABELS[pol_summary.iloc[-1]["zone"]] if len(pol_summary) else "—"
most_congested = ZONE_LABELS[tra_by_zone.iloc[0]["zone"]] if len(tra_by_zone) else "—"
peak_hour_df   = tra_f.groupby("hour")["avg_traffic"].mean()
peak_hour      = f"{int(peak_hour_df.idxmax()):02d}h" if len(peak_hour_df) else "—"
avg_pol        = round(pol_summary["avg_pollution"].mean(), 1) if len(pol_summary) else 0

for col, val, label, delta in zip(
    [k1, k2, k3, k4, k5],
    [most_polluted, most_congested, peak_hour, f"{avg_pol}", cleanest],
    ["Most Polluted Zone", "Most Congested Zone", "Peak Traffic Hour", "Avg Pollution Index", "Cleanest Zone"],
    ["Highest air pollution index", "Highest vehicle flow", "Busiest hour of day", "Across selected zones", "Lowest pollution index"]
):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{val}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-delta">{delta}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================
# TABS
# =========================

tab1, tab2, tab3 = st.tabs(["🌫  Air Quality", "🚗  Traffic", "📊  Correlation"])

# ─────────────────────────────────────────────
# TAB 1 — AIR QUALITY
# ─────────────────────────────────────────────
with tab1:

    st.markdown('<div class="insight-box">💡 <strong>Key insight:</strong> Chatelet and Gare du Nord consistently show the highest pollution levels due to high traffic density and diesel vehicle concentration. Paris Centre benefits from pedestrian zones.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown('<div class="section-header">Pollution Index by Zone</div>', unsafe_allow_html=True)
        fig = go.Figure()
        for _, row in pol_summary.sort_values("avg_pollution").iterrows():
            color = BLUE_SHADES.get(row["zone"], "#3584e4")
            label = ZONE_LABELS[row["zone"]]
            fig.add_trace(go.Bar(
                y=[label],
                x=[row["avg_pollution"]],
                orientation="h",
                marker=dict(color=color, opacity=0.95, line=dict(width=0)),
                showlegend=False,
                hovertemplate=f"<b>{label}</b><br>Avg Pollution: %{{x:.1f}}<br>Max: {row['max_pollution']}<br>Avg AQI: {row['avg_aqi']:.0f}<extra></extra>"
            ))
        fig.update_layout(
            **BASE_LAYOUT,
            height=300,
            title=dict(text="Average Pollution Index", font=dict(size=12, color="#4a6fa5")),
            xaxis_title="Pollution Index",
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-header">Pollution Share</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Pie(
            labels=[ZONE_LABELS[z] for z in pol_summary["zone"]],
            values=pol_summary["avg_pollution"],
            hole=0.65,
            marker=dict(
                colors=[BLUE_SHADES.get(z, "#3584e4") for z in pol_summary["zone"]],
                line=dict(color="#050d1a", width=2)
            ),
            textinfo="percent",
            textfont=dict(size=10, color="#cdd9f0"),
            hovertemplate="<b>%{label}</b><br>%{value:.1f} · %{percent}<extra></extra>",
            direction="clockwise",
            sort=True
        ))
        fig2.update_layout(
            **BASE_LAYOUT,
            height=300,
            title=dict(text="Relative Pollution Share", font=dict(size=12, color="#4a6fa5")),
        )
        fig2.update_layout(
            legend_orientation="v",
            legend_x=1.02,
            legend_y=0.5,
            legend_bgcolor="rgba(0,0,0,0)",
            legend_font=dict(size=10, color="#7a9fc4")
        )
        st.plotly_chart(fig2, use_container_width=True)

    # AQI bar
    st.markdown('<div class="section-header">Air Quality Index (AQI) vs Pollution</div>', unsafe_allow_html=True)
    fig3 = go.Figure()
    zones_sorted = pol_summary.sort_values("avg_pollution", ascending=False)
    labels = [ZONE_LABELS[z] for z in zones_sorted["zone"]]
    fig3.add_trace(go.Bar(
        name="Avg Pollution",
        x=labels, y=zones_sorted["avg_pollution"],
        marker=dict(color="#1a5fb4", opacity=0.9),
        hovertemplate="<b>%{x}</b><br>Pollution: %{y:.1f}<extra></extra>"
    ))
    fig3.add_trace(go.Scatter(
        name="Avg AQI",
        x=labels, y=zones_sorted["avg_aqi"],
        mode="lines+markers",
        line=dict(color="#85bfff", width=2, dash="dot"),
        marker=dict(size=7, color="#85bfff"),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>AQI: %{y:.0f}<extra></extra>"
    ))
    fig3.update_layout(
        **BASE_LAYOUT,
        height=280,
        title=dict(text="Pollution Index vs Air Quality Index by Zone", font=dict(size=12, color="#4a6fa5")),
        xaxis_title="",
        yaxis_title="Pollution Index",
        yaxis2=dict(
            title="AQI",
            overlaying="y", side="right",
            gridcolor="#0a1f35",
            tickfont=dict(size=10, color="#4a6fa5"),
            title_font=dict(size=10, color="#4a6fa5")
        ),
    )
    fig3.update_layout(legend_orientation="h", legend_y=1.12, legend_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────────
# TAB 2 — TRAFFIC
# ─────────────────────────────────────────────
with tab2:

    st.markdown('<div class="insight-box">💡 <strong>Key insight:</strong> Chatelet dominates all hours with 800+ vehicles/h. The rush hour peak is between <strong>07h–10h</strong> and <strong>17h–19h</strong>. Night hours (01h–05h) drop below 300 vehicles/h across all zones.</div>', unsafe_allow_html=True)

    c3, c4 = st.columns([2, 3])

    with c3:
        st.markdown('<div class="section-header">Average Traffic by Zone</div>', unsafe_allow_html=True)
        fig4 = go.Figure()
        for _, row in tra_by_zone.sort_values("avg_traffic").iterrows():
            color = BLUE_SHADES.get(row["zone"], "#3584e4")
            label = ZONE_LABELS[row["zone"]]
            fig4.add_trace(go.Bar(
                y=[label], x=[row["avg_traffic"]],
                orientation="h",
                marker=dict(color=color, opacity=0.9, line=dict(width=0)),
                showlegend=False,
                hovertemplate=f"<b>{label}</b><br>Avg: %{{x:.0f}} veh/h<br>Max: {row['max_traffic']:.0f} veh/h<extra></extra>"
            ))
        fig4.update_layout(
            **BASE_LAYOUT,
            height=300,
            title=dict(text="Avg Hourly Traffic Volume", font=dict(size=12, color="#4a6fa5")),
            xaxis_title="Vehicles / Hour",
        )
        st.plotly_chart(fig4, use_container_width=True)

    with c4:
        st.markdown('<div class="section-header">Traffic Flow Throughout the Day</div>', unsafe_allow_html=True)
        fig5 = go.Figure()
        for zone in selected_zones:
            zdf = tra_by_hour[tra_by_hour["zone"] == zone].sort_values("hour")
            if zdf.empty:
                continue
            fig5.add_trace(go.Scatter(
                x=zdf["hour"], y=zdf["avg_traffic"],
                mode="lines",
                name=ZONE_LABELS[zone],
                line=dict(color=BLUE_SHADES.get(zone, "#3584e4"), width=2.5),
                fill="tozeroy",
                fillcolor=BLUE_SHADES.get(zone, "#3584e4").replace(")", ",0.04)").replace("rgb", "rgba") if "rgb" in BLUE_SHADES.get(zone,"") else "rgba(53,132,228,0.04)",
                hovertemplate=f"<b>{ZONE_LABELS[zone]}</b> · %{{x:02d}}h<br>%{{y:.0f}} veh/h<extra></extra>"
            ))
        fig5.update_layout(
            **BASE_LAYOUT,
            height=300,
            title=dict(text="Hourly Traffic by Zone", font=dict(size=12, color="#4a6fa5")),
            xaxis_title="Hour of Day",
            xaxis_dtick=2,
            yaxis_title="Vehicles / Hour",
        )
        st.plotly_chart(fig5, use_container_width=True)

    # Heatmap
    st.markdown('<div class="section-header">Traffic Heatmap — Zone × Hour</div>', unsafe_allow_html=True)
    pivot = heatmap_df.pivot(index="zone", columns="hour", values="avg_traffic").fillna(0)
    pivot = pivot.reindex([z for z in ZONE_ORDER if z in pivot.index])
    pivot.index = [ZONE_LABELS[z] for z in pivot.index]

    fig6 = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}h" for h in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[
            [0.0,  "#050d1a"],
            [0.25, "#071828"],
            [0.5,  "#1a5fb4"],
            [0.75, "#3584e4"],
            [1.0,  "#85bfff"],
        ],
        hovertemplate="<b>%{y}</b> at %{x}<br>%{z:.0f} vehicles/h<extra></extra>",
        showscale=True,
        colorbar=dict(
            tickfont=dict(color="#4a6fa5", size=10),
            outlinecolor="rgba(0,0,0,0)",
            title=dict(text="veh/h", font=dict(color="#4a6fa5", size=10))
        )
    ))
    fig6.update_layout(
        **BASE_LAYOUT,
        height=260,
        title=dict(text="Traffic Volume by Zone and Hour of Day", font=dict(size=12, color="#4a6fa5")),
        xaxis_title="",
        yaxis_title="",
    )
    st.plotly_chart(fig6, use_container_width=True)

# ─────────────────────────────────────────────
# TAB 3 — CORRELATION
# ─────────────────────────────────────────────
with tab3:

    st.markdown('<div class="insight-box">💡 <strong>Key insight:</strong> High traffic zones (Chatelet, Gare du Nord) show the strongest pollution levels. However, Paris Centre has high traffic but lower pollution — suggesting pedestrian infrastructure reduces emissions effectively.</div>', unsafe_allow_html=True)

    c5, c6 = st.columns([3, 2])

    with c5:
        st.markdown('<div class="section-header">Traffic vs Pollution by Zone</div>', unsafe_allow_html=True)
        fig7 = go.Figure()
        for _, row in tp_summary.iterrows():
            color = BLUE_SHADES.get(row["zone"], "#3584e4")
            label = ZONE_LABELS[row["zone"]]
            # bubble size based on humidity
            size = max(20, row["avg_humidity"] * 0.7)
            fig7.add_trace(go.Scatter(
                x=[row["avg_traffic"]],
                y=[row["avg_pollution"]],
                mode="markers+text",
                marker=dict(
                    size=size,
                    color=color,
                    opacity=0.75,
                    line=dict(width=1.5, color="#0e2a45")
                ),
                text=[label],
                textposition="top center",
                textfont=dict(size=10, color="#cdd9f0"),
                showlegend=False,
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    f"Traffic: %{{x:.0f}} veh/h<br>"
                    f"Pollution: %{{y:.1f}}<br>"
                    f"Temp: {row['avg_temperature']:.1f}°C<br>"
                    f"Humidity: {row['avg_humidity']:.1f}%<extra></extra>"
                )
            ))
        fig7.update_layout(
            **BASE_LAYOUT,
            height=360,
            title=dict(text="Bubble size = Avg Humidity · Each bubble = one zone", font=dict(size=11, color="#4a6fa5")),
            xaxis_title="Avg Traffic (vehicles/h)",
            yaxis_title="Avg Pollution Index",
        )
        st.plotly_chart(fig7, use_container_width=True)

    with c6:
        st.markdown('<div class="section-header">Pollution by Traffic Level</div>', unsafe_allow_html=True)
        fig8 = go.Figure(go.Bar(
            x=[l.replace(" Traffic","") for l in level_summary["traffic_level"]],
            y=level_summary["avg_pollution"],
            marker=dict(
                color=[TRAFFIC_COLORS.get(l,"#3584e4") for l in level_summary["traffic_level"]],
                opacity=0.9,
                line=dict(width=0)
            ),
            text=level_summary["avg_pollution"].round(1),
            textposition="outside",
            textfont=dict(color="#7ab3f0", size=12),
            hovertemplate="<b>%{x} Traffic</b><br>Avg Pollution: %{y:.1f}<extra></extra>"
        ))
        fig8.update_layout(
            **BASE_LAYOUT,
            height=220,
            title=dict(text="Does More Traffic Mean More Pollution?", font=dict(size=12, color="#4a6fa5")),
            xaxis_title="Traffic Level",
            yaxis_title="Avg Pollution",
            showlegend=False
        )
        st.plotly_chart(fig8, use_container_width=True)

        # Environmental conditions mini table
        st.markdown('<div class="section-header">Env. Conditions by Zone</div>', unsafe_allow_html=True)
        env_df = tp_summary[["zone","avg_temperature","avg_humidity"]].copy()
        env_df["zone"] = env_df["zone"].map(ZONE_LABELS)
        env_df.columns = ["Zone", "Temp (°C)", "Humidity (%)"]
        env_df = env_df.sort_values("Temp (°C)", ascending=False).reset_index(drop=True)
        st.dataframe(
            env_df,
            use_container_width=True,
            hide_index=True,
            height=160
        )

# =========================
# FOOTER
# =========================

st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#0e2040; font-size:0.72rem; font-family: Inter;'>"
    "Paris Urban Intelligenc"
    "</p>",
    unsafe_allow_html=True
)