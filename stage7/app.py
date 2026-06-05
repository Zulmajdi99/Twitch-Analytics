"""
app.py — Twitch Viewer Analytics Dashboard
Stage 7: Streamlit Dashboard Assembly

Run locally:
    streamlit run app.py

Data files required in ./data/ folder:
    df_engineered.csv       (required)
    df_daily.csv            (required)
    df_video_play_clean.csv (optional — V8 and V9 depend on it)
"""

import os
import streamlit as st
import pandas as pd
import numpy as np

from charts import (
    build_v1_lifecycle, build_v2_engagement_timeline,
    build_v3_loyalty_heatmap, build_v4_channel_sunburst,
    build_v5_esports_calendar, build_v6_genre_treemap,
    build_v7_platform_divergence, build_v8_hourday_heatmap,
    build_v9_discovery_funnel, build_v10_binge_calendar,
    build_v11_yoy_waterfall, build_v12_monthly_heatmap,
    BG, BG2, TEAL, GOLD, PURPLE, RED, ORANGE, TEXT, TEXT_DIM,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Twitch Viewer Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  /* Background */
  [data-testid="stAppViewContainer"] > .main {{ background-color: {BG}; }}
  [data-testid="stHeader"] {{ background-color: {BG}; }}
  [data-testid="stSidebar"] {{ background-color: {BG2}; }}

  /* KPI cards */
  .kpi-card {{
      background: {BG2};
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 10px;
      padding: 18px 14px 14px;
      text-align: center;
      height: 110px;
      display: flex;
      flex-direction: column;
      justify-content: center;
  }}
  .kpi-icon  {{ font-size: 20px; line-height: 1; margin-bottom: 4px; }}
  .kpi-val   {{ font-size: 24px; font-weight: 700; color: {TEXT}; font-family: monospace; line-height: 1.1; }}
  .kpi-lbl   {{ font-size: 10px; color: {TEXT_DIM}; margin-top: 5px;
                text-transform: uppercase; letter-spacing: 0.06em; }}
  .kpi-delta {{ font-size: 10px; margin-top: 3px; }}

  /* Section headers */
  .section-header {{
      font-size: 13px;
      color: {TEXT_DIM};
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 0px;
      padding-bottom: 6px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
  }}

  /* Tabs */
  [data-baseweb="tab-list"] {{ background-color: {BG2}; border-radius: 8px; padding: 4px; }}
  [data-baseweb="tab"] {{ color: {TEXT_DIM} !important; }}
  [aria-selected="true"] {{ background-color: rgba(155,89,182,0.25) !important; border-radius: 6px; }}

  /* Table */
  [data-testid="stDataFrame"] {{ background-color: {BG2}; }}

  /* Hide streamlit default elements */
  #MainMenu {{ visibility: hidden; }}
  footer    {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


# ── Data paths ─────────────────────────────────────────────────────────────────
_HERE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(_HERE, 'Data')
PATH_ENG  = os.path.join(DATA_DIR, 'df_engineered.csv')
PATH_DAY  = os.path.join(DATA_DIR, 'df_daily.csv')
PATH_VP   = os.path.join(DATA_DIR, 'df_video_play_clean.csv')


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # df_engineered
    df = pd.read_csv(PATH_ENG, low_memory=False)
    df['day'] = pd.to_datetime(df['day'], errors='coerce')
    for c in ['is_lol', 'is_esports', 'is_top10_channel', 'is_binge_day']:
        if c in df.columns:
            df[c] = df[c].astype(bool)
    if 'hours_watched' not in df.columns:
        df['hours_watched'] = df['minutes_watched_unadjusted'] / 60
    df['year']  = df['year'].astype(int)
    df['month'] = df['month'].astype(int)

    # df_daily
    df_daily = pd.read_csv(PATH_DAY, low_memory=False)
    df_daily['date'] = pd.to_datetime(df_daily['date'], errors='coerce')
    df_daily['year'] = df_daily['year'].astype(int)
    if 'is_binge' not in df_daily.columns:
        df_daily['is_binge'] = df_daily['total_hours'] >= 3

    # df_video_play (optional)
    df_vp = None
    if os.path.exists(PATH_VP):
        df_vp = pd.read_csv(PATH_VP, low_memory=False)
        # Date column
        if 'date' in df_vp.columns:
            df_vp['date'] = pd.to_datetime(df_vp['date'], errors='coerce')
            df_vp['day']  = df_vp['date']
        elif 'time' in df_vp.columns:
            df_vp['time'] = pd.to_datetime(df_vp['time'], errors='coerce')
            df_vp['day']  = df_vp['time'].dt.normalize()
        # Hour column
        if 'hour' not in df_vp.columns and 'time' in df_vp.columns:
            df_vp['hour'] = df_vp['time'].dt.hour.astype('Int8')
        # day_of_week — ensure it exists as int (0=Mon)
        if 'day_of_week' not in df_vp.columns and 'day' in df_vp.columns:
            df_vp['day_of_week'] = df_vp['day'].dt.dayofweek

    return df, df_daily, df_vp


df, df_daily, df_vp = load_data()


# ── KPI computations ───────────────────────────────────────────────────────────
total_hours     = df['hours_watched'].sum()
caedrel_hours   = df.loc[df['channel_name'] == 'caedrel', 'hours_watched'].sum()
caedrel_pct     = caedrel_hours / total_hours * 100
lol_pct         = df['is_lol'].mean() * 100
binge_rate      = df_daily['is_binge'].mean() * 100
peak_year       = int(df.groupby('year')['hours_watched'].sum().idxmax())
peak_year_h     = df.groupby('year')['hours_watched'].sum().max()
total_channels  = df['channel_name'].nunique()
avg_session_min = df['minutes_watched_unadjusted'].mean()
span_start      = df['day'].min().strftime('%b %Y')
span_end        = df['day'].max().strftime('%b %Y')
total_sessions  = len(df)


# ── Cached chart builders ──────────────────────────────────────────────────────
@st.cache_data
def _v1(_df):        return build_v1_lifecycle(_df)

@st.cache_data
def _v2(_df_daily):  return build_v2_engagement_timeline(_df_daily)

@st.cache_data
def _v3(_df):        return build_v3_loyalty_heatmap(_df)

@st.cache_data
def _v4(_df):        return build_v4_channel_sunburst(_df)

@st.cache_data
def _v5(_df):        return build_v5_esports_calendar(_df)

@st.cache_data
def _v6(_df):        return build_v6_genre_treemap(_df)

@st.cache_data
def _v7(_df):        return build_v7_platform_divergence(_df)

@st.cache_data
def _v8(_df_vp):     return build_v8_hourday_heatmap(_df_vp)

@st.cache_data
def _v9(_df_vp):     return build_v9_discovery_funnel(_df_vp)

@st.cache_data
def _v10(_df_daily, year): return build_v10_binge_calendar(_df_daily, year=year)

@st.cache_data
def _v11(_df):       return build_v11_yoy_waterfall(_df)

@st.cache_data
def _v12(_df):       return build_v12_monthly_heatmap(_df)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Twitch Analytics")
    st.caption("Personal viewer behavior dashboard")
    st.divider()

    st.markdown("**📅 Dataset span**")
    st.markdown(f"{span_start} → {span_end}")

    st.markdown("**📁 Records**")
    st.markdown(f"{total_sessions:,} sessions  ·  {total_channels:,} channels")

    st.divider()
    st.markdown("**Data files**")
    for path, label in [(PATH_ENG, 'df_engineered.csv'),
                        (PATH_DAY, 'df_daily.csv'),
                        (PATH_VP,  'df_video_play_clean.csv')]:
        icon = '✅' if os.path.exists(path) else '⚠️'
        st.markdown(f"{icon} `{label}`")

    st.divider()
    st.caption("Stage 7 — Streamlit Dashboard")
    st.caption("Twitch Viewer Analytics Portfolio")


# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("# 📊 Twitch Viewer Analytics")
st.markdown(
    f"*{span_start} → {span_end}  ·  "
    f"{total_hours:,.0f}h across {total_channels:,} channels  ·  "
    f"{total_sessions:,} sessions recorded*"
)
st.divider()


# ── KPI cards row ──────────────────────────────────────────────────────────────
def kpi(icon, label, value, delta="", delta_color=TEAL):
    delta_html = (f'<div class="kpi-delta" style="color:{delta_color}">{delta}</div>'
                  if delta else '')
    st.markdown(
        f'<div class="kpi-card">'
        f'  <div class="kpi-icon">{icon}</div>'
        f'  <div class="kpi-val">{value}</div>'
        f'  <div class="kpi-lbl">{label}</div>'
        f'  {delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:  kpi("⏱️", "Total Hours",   f"{total_hours:,.0f}h")
with c2:  kpi("👑", "Top Channel",   "caedrel",    f"{caedrel_pct:.1f}% of all time", GOLD)
with c3:  kpi("🎮", "LoL Content",   f"{lol_pct:.1f}%", "of all sessions")
with c4:  kpi("🔥", "Binge Rate",    f"{binge_rate:.0f}%", "of days ≥ 3h", RED)
with c5:  kpi("📅", "Peak Year",     str(peak_year), f"{peak_year_h:,.0f}h that year", TEAL)
with c6:  kpi("⚡", "Avg Session",   f"{avg_session_min:.1f} min", f"{total_channels:,} channels")

st.divider()


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_ov, tab_loy, tab_con, tab_plt, tab_disc, tab_bin = st.tabs([
    "📈  Overview",
    "🎯  Loyalty",
    "🎮  Content",
    "📱  Platform",
    "🔍  Discovery",
    "🔥  Binge",
])


# ── Tab 0: Overview ────────────────────────────────────────────────────────────
with tab_ov:
    st.markdown('<p class="section-header">Viewer Lifecycle &amp; Longitudinal Engagement</p>',
                unsafe_allow_html=True)
    st.plotly_chart(_v1(df), use_container_width=True)
    st.divider()
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(_v2(df_daily), use_container_width=True)
    with col_right:
        st.plotly_chart(_v11(df), use_container_width=True)


# ── Tab 1: Loyalty ─────────────────────────────────────────────────────────────
with tab_loy:
    st.markdown('<p class="section-header">Channel Loyalty &amp; Portfolio Architecture</p>',
                unsafe_allow_html=True)
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(_v3(df), use_container_width=True)
    with col_right:
        st.plotly_chart(_v4(df), use_container_width=True)

    st.divider()
    st.markdown("#### 🏆 Top 20 Channels by Hours Watched")
    top_ch = (df.groupby('channel_name')
                .agg(hours=('hours_watched', 'sum'),
                     sessions=('hours_watched', 'count'),
                     avg_session_min=('minutes_watched_unadjusted', 'mean'))
                .round(1)
                .sort_values('hours', ascending=False)
                .head(20)
                .reset_index())
    top_ch.columns = ['Channel', 'Hours', 'Sessions', 'Avg Session (min)']
    top_ch['Hours'] = top_ch['Hours'].round(1)
    st.dataframe(top_ch, use_container_width=True, hide_index=True,
                 column_config={
                     'Hours': st.column_config.NumberColumn(format="%.1f h"),
                     'Avg Session (min)': st.column_config.NumberColumn(format="%.1f min"),
                 })


# ── Tab 2: Content ─────────────────────────────────────────────────────────────
with tab_con:
    st.markdown('<p class="section-header">Content &amp; LoL Esports Calendar</p>',
                unsafe_allow_html=True)
    st.plotly_chart(_v5(df), use_container_width=True)
    st.divider()
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(_v6(df), use_container_width=True)
    with col_right:
        st.plotly_chart(_v12(df), use_container_width=True)


# ── Tab 3: Platform ────────────────────────────────────────────────────────────
with tab_plt:
    st.markdown('<p class="section-header">Platform Behaviour &amp; Viewing Patterns</p>',
                unsafe_allow_html=True)
    if df_vp is not None and 'hour' in df_vp.columns:
        col_left, col_right = st.columns(2)
        with col_left:
            st.plotly_chart(_v7(df), use_container_width=True)
        with col_right:
            st.plotly_chart(_v8(df_vp), use_container_width=True)
    else:
        st.plotly_chart(_v7(df), use_container_width=True)
        st.info("ℹ️  **V8 Hour × Day heatmap** requires `df_video_play_clean.csv` with an `hour` column.")

    st.divider()
    st.markdown("#### 📊 Platform Session Stats")
    plat_stats = (df[df['platform'].isin(['web', 'android'])]
                  .groupby('platform')
                  .agg(sessions=('hours_watched', 'count'),
                       total_hours=('hours_watched', 'sum'),
                       avg_session_min=('minutes_watched_unadjusted', 'mean'))
                  .round(1).reset_index())
    plat_stats.columns = ['Platform', 'Sessions', 'Total Hours', 'Avg Session (min)']
    st.dataframe(plat_stats, use_container_width=True, hide_index=True)


# ── Tab 4: Discovery ───────────────────────────────────────────────────────────
with tab_disc:
    st.markdown('<p class="section-header">Stream Discovery — How You Find Streams</p>',
                unsafe_allow_html=True)
    if df_vp is not None:
        med_col = next((c for c in ['medium_simplified', 'medium'] if c in df_vp.columns), None)
        if med_col:
            st.plotly_chart(_v9(df_vp), use_container_width=True)
            st.divider()
            st.markdown("#### 🔍 Discovery Source Breakdown")
            disc_tbl = (df_vp[med_col].value_counts()
                        .reset_index()
                        .rename(columns={med_col: 'Source', 'count': 'Sessions'}))
            disc_tbl.columns = ['Source', 'Sessions']
            disc_tbl['Share %'] = (disc_tbl['Sessions'] / disc_tbl['Sessions'].sum() * 100).round(1)
            st.dataframe(disc_tbl, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️  No `medium_simplified` or `medium` column found in `df_video_play_clean.csv`.")
    else:
        st.info("ℹ️  **V9 Discovery funnel** requires `df_video_play_clean.csv`.")


# ── Tab 5: Binge ───────────────────────────────────────────────────────────────
with tab_bin:
    st.markdown('<p class="section-header">Binge Day Architecture</p>', unsafe_allow_html=True)

    years_avail = sorted(df_daily['year'].unique(), reverse=True)
    sel_year = st.selectbox("Select year to view", years_avail, key='binge_year_sel',
                            help="Switch year to explore binge patterns")

    st.plotly_chart(_v10(df_daily, sel_year), use_container_width=True)

    st.divider()
    col_stats, col_table = st.columns([1, 2])

    yr_data = df_daily[df_daily['year'] == sel_year]
    with col_stats:
        st.markdown(f"#### 📊 {sel_year} Summary")
        active  = (yr_data['total_hours'] > 0).sum()
        binge_n = yr_data['is_binge'].sum()
        max_day = yr_data.loc[yr_data['total_hours'].idxmax()]
        st.metric("Active days",     f"{active}")
        st.metric("Binge days (≥3h)", f"{binge_n}  ({binge_n/active*100:.0f}%)")
        st.metric("Peak day",
                  f"{max_day['total_hours']:.1f}h",
                  max_day['date'].strftime('%b %d'))

    with col_table:
        st.markdown(f"#### 🔥 Binge Days in {sel_year}")
        binge_tbl = (yr_data[yr_data['is_binge'] == True][['date', 'total_hours']]
                     .sort_values('total_hours', ascending=False)
                     .reset_index(drop=True))
        binge_tbl['date']        = binge_tbl['date'].dt.strftime('%Y-%m-%d')
        binge_tbl['total_hours'] = binge_tbl['total_hours'].round(1)
        binge_tbl.columns        = ['Date', 'Hours']
        st.dataframe(binge_tbl, use_container_width=True, hide_index=True,
                     column_config={'Hours': st.column_config.NumberColumn(format="%.1f h")})
