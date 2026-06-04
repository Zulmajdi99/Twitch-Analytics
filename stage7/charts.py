"""
charts.py — Stage 6 visualization library
All 12 build_* functions for the Twitch Viewer Analytics dashboard.
Import this module in app.py.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

pio.templates.default = "plotly_dark"

# ── Design system ─────────────────────────────────────────────────────────────
BG       = '#0f0f1a'
BG2      = '#141428'
GRID     = 'rgba(255,255,255,0.05)'
TEXT     = '#e0e0e0'
TEXT_DIM = '#8899aa'
PURPLE   = '#9b59b6'
GOLD     = '#f1c40f'
ORANGE   = '#e67e22'
TEAL     = '#1abc9c'
RED      = '#e74c3c'
BLUE     = '#3498db'
GREEN    = '#2ecc71'
GREY     = '#95a5a6'

TIER_COLORS   = {'S': GOLD, 'A': ORANGE, 'B': PURPLE, 'C': BLUE, 'D': GREY}
PERIOD_COLORS = {'Spring Split': PURPLE, 'Summer Split': ORANGE,
                 'Worlds': GOLD, 'Off-season': GREY}
SEASON_COLORS = {'Spring': GREEN, 'Summer': ORANGE, 'Fall': RED, 'Winter': BLUE}
SESSION_ORDER = ['Quick', 'Short', 'Medium', 'Long', 'Marathon']


def _base(title: str, height: int = 460, t=80, b=60, l=70, r=40) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=15)),
        height=height,
        plot_bgcolor=BG, paper_bgcolor=BG,
        font=dict(color=TEXT, family='system-ui, sans-serif'),
        margin=dict(t=t, b=b, l=l, r=r),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  V1 — Viewer Lifecycle Bubble Chart
# ═══════════════════════════════════════════════════════════════════════════════
def build_v1_lifecycle(df: pd.DataFrame) -> go.Figure:
    annual = df.groupby('year').agg(
        total_hours=('hours_watched', 'sum'),
        unique_channels=('channel_name', 'nunique'),
        avg_session_min=('minutes_watched_unadjusted', 'mean'),
        lol_pct=('is_lol', 'mean'),
        sessions=('channel_name', 'count'),
    ).reset_index()
    annual['lol_100'] = (annual['lol_pct'] * 100).round(1)
    xm = annual['unique_channels'].median()
    ym = annual['total_hours'].median()

    fig = go.Figure()
    for (x0, x1, y0, y1) in [
        (0, xm, ym, annual['total_hours'].max() * 1.2),
        (xm, annual['unique_channels'].max() * 1.2, ym, annual['total_hours'].max() * 1.2),
        (0, xm, 0, ym),
        (xm, annual['unique_channels'].max() * 1.2, 0, ym),
    ]:
        fig.add_shape(type='rect', x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor='rgba(255,255,255,0.018)',
                      line=dict(color='rgba(255,255,255,0.07)', width=0.6))

    for qx, qy, qlabel, qa in [
        (xm * 0.04, annual['total_hours'].max() * 1.08, 'LOYALIST', 'left'),
        (xm * 1.04, annual['total_hours'].max() * 1.08, 'PEAK EXPLORER', 'left'),
        (xm * 0.04, ym * 0.06, 'QUIET', 'left'),
        (xm * 1.04, ym * 0.06, 'CASUAL EXPLORER', 'left'),
    ]:
        fig.add_annotation(x=qx, y=qy, text=qlabel, showarrow=False,
                           font=dict(size=9, color='rgba(255,255,255,0.18)'),
                           xanchor=qa, yanchor='top')

    fig.add_vline(x=xm, line=dict(color='rgba(255,255,255,0.13)', width=1, dash='dot'))
    fig.add_hline(y=ym, line=dict(color='rgba(255,255,255,0.13)', width=1, dash='dot'))

    fig.add_trace(go.Scatter(
        x=annual['unique_channels'], y=annual['total_hours'],
        mode='markers',
        marker=dict(
            size=annual['avg_session_min'] * 2.8,
            sizemode='area',
            sizeref=2. * annual['avg_session_min'].max() / (50. ** 2),
            color=annual['lol_100'],
            colorscale=[[0, BLUE], [0.35, PURPLE], [0.7, TEAL], [1, GREEN]],
            colorbar=dict(title=dict(text='LoL %', font=dict(size=11)),
                          ticksuffix='%', len=0.55, thickness=12, x=1.02),
            line=dict(color='white', width=1.5), opacity=0.87,
        ),
        customdata=annual[['lol_100', 'avg_session_min', 'sessions', 'total_hours']].values,
        hovertemplate=(
            '<b>%{customdata[3]:.0f}h · %{x} channels</b><br>'
            'LoL: %{customdata[0]:.1f}%<br>'
            'Avg session: %{customdata[1]:.1f} min<br>'
            'Sessions: %{customdata[2]:,}<extra></extra>'
        ),
        showlegend=False,
    ))

    for _, row in annual.iterrows():
        xv, yv = float(row['unique_channels']), float(row['total_hours'])
        h_rank = float((annual['total_hours'] < yv).sum()) / len(annual)
        c_rank = float((annual['unique_channels'] < xv).sum()) / len(annual)
        ysh = -22 if h_rank >= 0.55 else 20
        xsh = -12 if c_rank >= 0.65 else 12
        xanch = 'right' if c_rank >= 0.65 else 'left'
        fig.add_annotation(x=xv, y=yv, text=f'<b>{int(row["year"])}</b>',
                           showarrow=False,
                           font=dict(size=10, color='white', family='monospace'),
                           xshift=xsh, yshift=ysh, xanchor=xanch, yanchor='middle',
                           bgcolor='rgba(10,10,20,0.80)', borderpad=2)

    r21 = annual[annual['year'] == 2021]
    r22 = annual[annual['year'] == 2022]
    if len(r21) and len(r22):
        x21, y21 = float(r21['unique_channels'].iloc[0]), float(r21['total_hours'].iloc[0])
        x22, y22 = float(r22['unique_channels'].iloc[0]), float(r22['total_hours'].iloc[0])
        fig.add_shape(type='line', x0=x21, y0=y21, x1=x22, y1=y22,
                      xref='x', yref='y',
                      line=dict(color=RED, width=2, dash='dot'), layer='below')
        fig.add_trace(go.Scatter(x=[x22], y=[y22], mode='markers',
                                 marker=dict(symbol='triangle-down', size=14, color=RED,
                                             opacity=0.9, line=dict(color=RED, width=1)),
                                 hoverinfo='skip', showlegend=False))
    fig.add_annotation(xref='paper', yref='paper', x=0.06, y=0.86,
                       text='Explorer \u2192 Loyalist pivot (2021\u21922022)<br>channels \u221238% \u00b7 avg session +11%',
                       font=dict(size=8, color=RED), showarrow=False,
                       xanchor='left', yanchor='middle',
                       bgcolor='rgba(10,10,20,0.88)', borderpad=3,
                       bordercolor=RED, borderwidth=0.5)

    pk = annual.loc[annual['total_hours'].idxmax()]
    fig.add_annotation(x=float(pk['unique_channels']), y=float(pk['total_hours']),
                       ax=55, ay=-45, text=f"Peak: {float(pk['total_hours']):.0f}h",
                       font=dict(size=9, color=GOLD), showarrow=True,
                       arrowcolor=GOLD, arrowhead=2, arrowwidth=1.5,
                       bgcolor='rgba(10,10,20,0.82)', borderpad=2)

    fig.update_layout(**_base('\U0001fab7 V1 \u2014 Viewer Lifecycle (bubble = avg session depth)',
                              height=530, t=80, b=65, l=75, r=120))
    fig.update_xaxes(title_text='Unique Channels Watched / Year', showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title_text='Total Hours Watched / Year', showgrid=True, gridcolor=GRID, zeroline=False)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V2 — Rolling Engagement Timeline
# ═══════════════════════════════════════════════════════════════════════════════
def build_v2_engagement_timeline(df_daily: pd.DataFrame) -> go.Figure:
    d = df_daily.copy().sort_values('date')
    d['date'] = pd.to_datetime(d['date'])
    r30_max = d['rolling_30d'].max()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d['date'], y=d['rolling_30d'], mode='lines',
                             name='Rolling 30d', fill='tozeroy',
                             fillcolor='rgba(155,89,182,0.18)',
                             line=dict(color=PURPLE, width=1.8),
                             hovertemplate='%{x|%b %Y}<br>30d: %{y:.1f}h<extra></extra>'))
    fig.add_trace(go.Scatter(x=d['date'], y=d['rolling_7d'], mode='lines',
                             name='Rolling 7d', line=dict(color=TEAL, width=1.1, dash='dot'),
                             opacity=0.5,
                             hovertemplate='%{x|%b %d %Y}<br>7d: %{y:.1f}h<extra></extra>'))
    binge = d[d['is_binge'] == True]
    fig.add_trace(go.Scatter(x=binge['date'], y=binge['total_hours'], mode='markers',
                             name='Binge day (\u22653h)',
                             marker=dict(color=RED, size=3.5, opacity=0.45),
                             hovertemplate='%{x|%b %d %Y}<br>%{y:.1f}h \U0001f525<extra></extra>'))

    for yr in range(int(d['year'].min()) + 1, int(d['year'].max()) + 1):
        fig.add_vline(x=f'{yr}-01-01',
                      line=dict(color='rgba(255,255,255,0.12)', width=1, dash='dot'))
        fig.add_annotation(x=f'{yr}-01-01', y=r30_max * 1.07, text=str(yr),
                           showarrow=False, font=dict(size=9, color=TEXT_DIM), yanchor='bottom')

    key_events = [
        ('2021-03-07', 'jankos + LEC peak\n(Spring Split)', ORANGE, 22, -56),
        ('2022-01-24', 'caedrel era begins', GOLD, -20, -52),
        ('2022-09-11', '2022: \u221252% year-on-year', RED, -18, -70),
        ('2024-02-22', 'Peak day 24.1h', TEAL, 22, -52),
    ]
    for date_str, label, color, ax_px, ay_px in key_events:
        target = pd.to_datetime(date_str)
        idx = (d['date'] - target).abs().idxmin()
        actual_y = float(d.loc[idx, 'rolling_30d'])
        fig.add_annotation(x=date_str, y=actual_y, ax=ax_px, ay=ay_px, text=label,
                           font=dict(size=9, color=color), showarrow=True,
                           arrowhead=2, arrowcolor=color, arrowwidth=1.5,
                           bgcolor='rgba(10,10,20,0.82)', borderpad=3, standoff=3)

    fig.update_layout(**_base('\U0001f4c8 V2 \u2014 8-Year Engagement Timeline',
                              height=460, t=80, b=60, l=75, r=30))
    fig.update_xaxes(showgrid=False, title_text='Date', tickformat='%Y')
    fig.update_yaxes(title_text='Hours (Rolling Window)', showgrid=True, gridcolor=GRID,
                     zeroline=False, rangemode='tozero')
    fig.update_layout(legend=dict(orientation='h', y=1.09, x=0,
                                  bgcolor='rgba(0,0,0,0)', font=dict(size=11)))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V3 — Channel Loyalty Heatmap
# ═══════════════════════════════════════════════════════════════════════════════
def build_v3_loyalty_heatmap(df: pd.DataFrame) -> go.Figure:
    tier_order = ['S', 'A', 'B', 'C', 'D']
    sess_order = ['Quick', 'Short', 'Medium', 'Long', 'Marathon']
    pivot = (df.groupby(['channel_tier', 'session_type'], observed=True)
               ['minutes_watched_unadjusted'].mean()
               .unstack(fill_value=0)
               .reindex(index=tier_order, columns=sess_order, fill_value=0))
    cnt = (df.groupby(['channel_tier', 'session_type'], observed=True).size()
             .unstack(fill_value=0)
             .reindex(index=tier_order, columns=sess_order, fill_value=0))
    z = pivot.values
    fig = go.Figure(go.Heatmap(
        z=z, x=sess_order, y=tier_order,
        text=[[f"{v:.1f}" for v in row] for row in z],
        texttemplate='%{text}', textfont=dict(size=12, color='white'),
        colorscale=[[0, '#12122a'], [0.15, '#1e3a5f'], [0.40, '#9b59b6'],
                    [0.70, '#e67e22'], [1.0, '#f1c40f']],
        colorbar=dict(title=dict(text='Avg min', font=dict(size=11)),
                      ticksuffix=' min', len=0.7, thickness=12),
        customdata=cnt.values,
        hovertemplate='Tier <b>%{y}</b> × <b>%{x}</b><br>'
                      'Avg session: %{z:.1f} min<br>'
                      'Sessions: %{customdata:,}<extra></extra>',
    ))
    tier_hrs = df.groupby('channel_tier', observed=True)['hours_watched'].sum()
    ytick = [f"<b>{t}</b>  <span style='color:#8899aa;font-size:10px'>"
             f"{tier_hrs.get(t, 0):,.0f}h</span>" for t in tier_order]
    fig.update_layout(**_base('\U0001f3af V3 \u2014 Channel Loyalty Matrix: Avg Session (min)',
                              height=390, t=80, b=60, l=80, r=110))
    fig.update_yaxes(tickvals=list(range(5)), ticktext=ytick, title_text='Channel Tier')
    fig.update_xaxes(title_text='Session Type')
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V4 — Channel Portfolio Sunburst
# ═══════════════════════════════════════════════════════════════════════════════
def build_v4_channel_sunburst(df: pd.DataFrame, min_hours: float = 5.0) -> go.Figure:
    ch = (df.groupby(['channel_tier', 'channel_name'], observed=True)['hours_watched']
            .sum().reset_index())
    ch = ch[ch['hours_watched'] >= min_hours].copy()
    ids, labels, parents, values, colors = [], [], [], [], []
    ids.append('root'); labels.append('All Channels'); parents.append('')
    values.append(ch['hours_watched'].sum()); colors.append('#1a1a2e')
    for tier in ['S', 'A', 'B', 'C', 'D']:
        sub = ch[ch['channel_tier'] == tier]
        if sub.empty:
            continue
        ids.append(f'tier_{tier}')
        labels.append(f'Tier {tier}  {sub["hours_watched"].sum():.0f}h')
        parents.append('root'); values.append(sub['hours_watched'].sum())
        colors.append(TIER_COLORS.get(tier, GREY))
        for _, row in sub.sort_values('hours_watched', ascending=False).iterrows():
            ids.append(f'{tier}_{row["channel_name"]}')
            labels.append(f'{row["channel_name"]}  {row["hours_watched"]:.0f}h')
            parents.append(f'tier_{tier}'); values.append(row['hours_watched'])
            colors.append(GOLD if row['channel_name'] == 'caedrel'
                          else TIER_COLORS.get(tier, GREY) + 'aa')
    fig = go.Figure(go.Sunburst(ids=ids, labels=labels, parents=parents, values=values,
                                marker=dict(colors=colors), branchvalues='total', maxdepth=3,
                                insidetextorientation='radial',
                                hovertemplate='<b>%{label}</b><br>%{value:.1f}h (%{percentRoot:.1%})<extra></extra>'))
    fig.update_layout(**_base(f'\U0001f31e V4 \u2014 Channel Portfolio Sunburst (\u2265{min_hours:.0f}h)',
                              height=560, t=70, b=30, l=30, r=30))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V5 — LoL Esports Calendar Overlay
# ═══════════════════════════════════════════════════════════════════════════════
def build_v5_esports_calendar(df: pd.DataFrame) -> go.Figure:
    period_map = {1: 'Spring Split', 2: 'Spring Split', 3: 'Spring Split', 4: 'Spring Split',
                  5: 'Summer Split', 6: 'Summer Split', 7: 'Summer Split', 8: 'Summer Split',
                  9: 'Off-season', 10: 'Worlds', 11: 'Worlds', 12: 'Off-season'}
    lol = df[df['is_lol'] == True].copy()
    monthly = (lol.groupby(['year', 'month'])['hours_watched'].sum().reset_index())
    monthly['date'] = pd.to_datetime(
        monthly['year'].astype(str) + '-' + monthly['month'].astype(str).str.zfill(2) + '-01')
    monthly = monthly.sort_values('date')
    monthly['period'] = monthly['month'].map(period_map)
    monthly['bar_color'] = monthly['period'].map(PERIOD_COLORS)
    y0, y1 = int(monthly['year'].min()), int(monthly['year'].max())
    fig = go.Figure()
    for yr in range(y0, y1 + 2):
        for sm, em, fc in [(1, 4, 'rgba(155,89,182,0.09)'), (5, 8, 'rgba(230,126,34,0.09)'),
                           (10, 11, 'rgba(241,196,15,0.09)')]:
            fig.add_vrect(x0=f'{yr}-{sm:02d}-01', x1=f'{yr}-{em:02d}-28',
                          fillcolor=fc, line_width=0, layer='below')
    fig.add_trace(go.Bar(x=monthly['date'], y=monthly['hours_watched'],
                         marker=dict(color=monthly['bar_color'], opacity=0.87),
                         name='LoL hours',
                         hovertemplate='<b>%{x|%b %Y}</b><br>LoL: %{y:.1f}h<extra></extra>'))
    for period, color in PERIOD_COLORS.items():
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
                                 marker=dict(size=10, color=color, symbol='square'),
                                 name=period, showlegend=True))
    for yr in range(y0 + 1, y1 + 2):
        fig.add_vline(x=f'{yr}-01-01',
                      line=dict(color='rgba(255,255,255,0.14)', width=1, dash='dot'))
    fig.update_layout(**_base('\U0001f3c6 V5 \u2014 Monthly LoL Viewing vs Esports Calendar',
                              height=470, t=80, b=70, l=75, r=30))
    fig.update_xaxes(title_text='Month', showgrid=False, tickformat='%b %Y', tickangle=-30)
    fig.update_yaxes(title_text='LoL Hours Watched', showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_layout(bargap=0.06,
                      legend=dict(orientation='h', y=1.09, x=0, bgcolor='rgba(0,0,0,0)', font=dict(size=11)))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V6 — Game Genre Treemap
# ═══════════════════════════════════════════════════════════════════════════════
def build_v6_genre_treemap(df: pd.DataFrame) -> go.Figure:
    g = (df.groupby(['game_genre', 'game_name'], observed=True)['hours_watched']
           .sum().reset_index())
    g.columns = ['genre', 'game', 'hours']
    g = g[g['hours'] >= 0.5].copy()
    fig = px.treemap(g, path=[px.Constant('All Genres'), 'genre', 'game'],
                     values='hours', color='hours',
                     color_continuous_scale=[[0, '#0d0d1a'], [0.05, '#1f1f3a'],
                                              [0.15, '#1e3a5f'], [0.35, '#9b59b6'],
                                              [0.65, '#1abc9c'], [1.0, '#f1c40f']],
                     title='\U0001f333 V6 \u2014 Content Genre Treemap')
    fig.update_traces(textinfo='label+percent parent', textfont_size=12,
                      hovertemplate='<b>%{label}</b><br>%{value:.1f}h<br>%{percentParent:.1%} of genre<extra></extra>',
                      marker_line_width=0.6, marker_line_color=BG)
    fig.update_layout(height=550, paper_bgcolor=BG, font=dict(color=TEXT, size=11),
                      margin=dict(t=70, b=10, l=10, r=10),
                      coloraxis_colorbar=dict(title=dict(text='Hours'), len=0.6, thickness=12))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V7 — Platform Divergence
# ═══════════════════════════════════════════════════════════════════════════════
def build_v7_platform_divergence(df: pd.DataFrame) -> go.Figure:
    plat = (df[df['platform'].isin(['web', 'android'])]
            .groupby(['year', 'platform'], observed=True)['minutes_watched_unadjusted']
            .mean().reset_index())
    plat.columns = ['year', 'platform', 'avg_min']
    web_s = plat[plat['platform'] == 'web'].set_index('year')['avg_min']
    and_s = plat[plat['platform'] == 'android'].set_index('year')['avg_min']
    years = sorted(set(web_s.index) & set(and_s.index))
    wy = [float(web_s[y]) for y in years]
    ay = [float(and_s[y]) for y in years]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years + years[::-1], y=wy + ay[::-1],
                             fill='toself', fillcolor='rgba(26,188,156,0.10)',
                             line=dict(color='rgba(0,0,0,0)'),
                             name='Divergence zone', hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=years, y=wy, mode='lines+markers+text', name='Web',
                             line=dict(color=TEAL, width=3),
                             marker=dict(size=9, color=TEAL, line=dict(color='white', width=1.5)),
                             text=[f"{v:.1f}" for v in wy], textposition='top center',
                             textfont=dict(size=9, color=TEAL),
                             hovertemplate='Web %{x}<br>%{y:.1f} min<extra></extra>'))
    fig.add_trace(go.Scatter(x=years, y=ay, mode='lines+markers+text', name='Android',
                             line=dict(color=ORANGE, width=3, dash='dash'),
                             marker=dict(size=9, color=ORANGE, symbol='diamond',
                                         line=dict(color='white', width=1.5)),
                             text=[f"{v:.1f}" for v in ay], textposition='bottom center',
                             textfont=dict(size=9, color=ORANGE),
                             hovertemplate='Android %{x}<br>%{y:.1f} min<extra></extra>'))
    if 2022 in web_s.index:
        fig.add_vline(x=2022, line=dict(color='rgba(255,255,255,0.2)', width=1.5, dash='dot'))
        fig.add_annotation(x=2022, y=max(wy) * 0.92, text='Web dominant from 2022',
                           font=dict(size=9, color=TEXT_DIM), showarrow=False,
                           xanchor='left', xshift=8)
    fig.update_layout(**_base('\U0001f4f1 V7 \u2014 Platform Divergence: Web vs Android Avg Session',
                              height=450, t=80, b=65, l=75, r=30))
    fig.update_xaxes(title_text='Year', dtick=1, showgrid=False)
    fig.update_yaxes(title_text='Avg Session Length (min)', showgrid=True, gridcolor=GRID,
                     zeroline=False, rangemode='tozero')
    fig.update_layout(legend=dict(orientation='h', y=1.09, bgcolor='rgba(0,0,0,0)', font=dict(size=11)))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V8 — Hour × Day Heatmap (requires df_video_play_clean)
# ═══════════════════════════════════════════════════════════════════════════════
def build_v8_hourday_heatmap(df_vp: pd.DataFrame) -> go.Figure:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    _dow_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    _vp = df_vp.copy()
    if _vp['day_of_week'].dtype != object:
        _vp['dow_name'] = _vp['day_of_week'].map(_dow_map)
    else:
        _long = {'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday', 'Thu': 'Thursday',
                 'Fri': 'Friday', 'Sat': 'Saturday', 'Sun': 'Sunday'}
        _vp['dow_name'] = _vp['day_of_week'].map(lambda x: _long.get(str(x), str(x)))
    hourday = (_vp.groupby(['dow_name', 'hour']).size().reset_index(name='count'))
    hourday.columns = ['day_of_week', 'hour', 'count']
    pivot = (hourday.pivot(index='day_of_week', columns='hour', values='count')
             .reindex(day_order, fill_value=0).fillna(0).astype(int))
    for h in range(24):
        if h not in pivot.columns:
            pivot[h] = 0
    pivot = pivot[sorted(pivot.columns)]
    z = pivot.values
    fig = go.Figure(go.Heatmap(
        z=z, x=list(pivot.columns), y=day_order,
        colorscale=[[0, '#0d0d1a'], [0.04, '#1a0533'], [0.20, '#4a0572'],
                    [0.50, '#9b59b6'], [0.78, '#e67e22'], [1.0, '#f1c40f']],
        colorbar=dict(title=dict(text='Play Events', font=dict(size=11)), len=0.7, thickness=12),
        text=[[str(v) if v > 0 else '' for v in row] for row in z],
        texttemplate='%{text}', textfont=dict(size=8, color='rgba(255,255,255,0.65)'),
        hovertemplate='<b>%{y}</b> %{x}:00<br>Events: %{z}<extra></extra>',
        xgap=1.5, ygap=1.5,
    ))
    fig.add_shape(type='rect', x0=19.5, x1=23.5, y0=-0.5, y1=6.5,
                  line=dict(color=GOLD, width=1.5, dash='dash'), fillcolor='rgba(0,0,0,0)')
    fig.add_annotation(x=21.5, y=-0.85, text='Prime-time 20:00\u201323:00',
                       font=dict(size=9, color=GOLD), showarrow=False, yanchor='top')
    fig.update_layout(**_base('\U0001f550 V8 \u2014 When You Watch: Play Events by Hour \u00d7 Day',
                              height=370, t=80, b=85, l=100, r=30))
    fig.update_xaxes(title_text='Hour of Day',
                     tickvals=list(range(0, 24, 2)),
                     ticktext=[f"{h}:00" for h in range(0, 24, 2)], showgrid=False)
    fig.update_yaxes(title_text='Day of Week', showgrid=False)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V9 — Stream Discovery Funnel (requires df_video_play_clean)
# ═══════════════════════════════════════════════════════════════════════════════
def build_v9_discovery_funnel(df_vp: pd.DataFrame) -> go.Figure:
    med_col = next((c for c in ['medium_simplified', 'medium'] if c in df_vp.columns), None)
    if med_col is None:
        raise ValueError("No medium column in df_video_play_clean")
    funnel = df_vp[med_col].value_counts().reset_index()
    funnel.columns = ['medium', 'count']
    funnel = funnel.sort_values('count', ascending=True).reset_index(drop=True)
    funnel['pct'] = (funnel['count'] / funnel['count'].sum() * 100).round(1)
    n = len(funnel)
    bar_colors = [GOLD if i == n - 1 else TEAL if i == n - 2 else PURPLE if i >= n - 4 else GREY
                  for i in range(n)]
    fig = go.Figure(go.Bar(
        y=funnel['medium'], x=funnel['count'], orientation='h',
        marker=dict(color=bar_colors, opacity=0.88),
        text=[f"{p:.1f}%" for p in funnel['pct']], textposition='outside',
        textfont=dict(size=10, color='white'),
        customdata=funnel[['pct']].values,
        hovertemplate='<b>%{y}</b><br>Sessions: %{x:,}<br>Share: %{customdata[0]:.1f}%<extra></extra>',
    ))
    fig.update_layout(**_base('\U0001f50d V9 \u2014 Stream Discovery Funnel',
                              height=430, t=80, b=60, l=150, r=90))
    fig.update_xaxes(title_text='Number of Play Events', showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title_text='Discovery Source', showgrid=False)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V10 — Binge Calendar Heatmap
# ═══════════════════════════════════════════════════════════════════════════════
def build_v10_binge_calendar(df_daily: pd.DataFrame, year: int = None) -> go.Figure:
    if year is None:
        year = int(df_daily.groupby('year')['total_hours'].sum().idxmax())
    all_days = pd.DataFrame({'date': pd.date_range(f'{year}-01-01', f'{year}-12-31')})
    d = all_days.merge(df_daily[['date', 'total_hours', 'is_binge']].copy(),
                       on='date', how='left').fillna({'total_hours': 0, 'is_binge': False})
    d['dow'] = d['date'].dt.dayofweek
    year_start = pd.Timestamp(f'{year}-01-01')
    first_monday = year_start - pd.Timedelta(days=year_start.dayofweek)
    d['col'] = ((d['date'] - first_monday).dt.days // 7).clip(0, 52)
    Z = np.zeros((7, 53))
    Hover = [['' for _ in range(53)] for _ in range(7)]
    Binge = np.zeros((7, 53))
    for _, row in d.iterrows():
        dw, wk, hrs = int(row['dow']), int(row['col']), float(row['total_hours'])
        Z[dw, wk] = hrs
        Binge[dw, wk] = 1 if hrs >= 3 else 0
        Hover[dw][wk] = (f"<b>{row['date'].strftime('%a %b %d %Y')}</b><br>"
                         f"{'🔥 BINGE  ' if hrs >= 3 else ''}{hrs:.1f}h")
    day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    mticks, mnames = [], []
    for m in range(1, 13):
        rows = d[d['date'].dt.month == m]
        if len(rows):
            mticks.append(int(rows['col'].min()))
            mnames.append(rows['date'].dt.strftime('%b').iloc[0])
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=Z, x=list(range(53)), y=day_labels,
        colorscale=[[0, '#0d0d1a'], [0.001, '#14122a'], [0.04, '#1a0d3d'],
                    [0.15, '#4a1f72'], [0.35, '#9b59b6'], [0.60, '#e74c3c'],
                    [0.82, '#e67e22'], [1.0, '#f1c40f']],
        zmin=0, zmax=max(d['total_hours'].max(), 3),
        colorbar=dict(title=dict(text='Hours', font=dict(size=11)), ticksuffix='h', len=0.65, thickness=12),
        text=Hover, hovertemplate='%{text}<extra></extra>',
        showscale=True, xgap=2, ygap=2,
    ))
    bx, by = [], []
    for dw in range(7):
        for wk in range(53):
            if Binge[dw, wk]:
                bx.append(wk); by.append(day_labels[dw])
    if bx:
        fig.add_trace(go.Scatter(x=bx, y=by, mode='markers',
                                 marker=dict(symbol='square', size=13, color='rgba(0,0,0,0)',
                                             line=dict(color=GOLD, width=1.5), opacity=0.65),
                                 name='Binge (\u22653h)', hoverinfo='skip', showlegend=True))
    for wk, mname in zip(mticks, mnames):
        fig.add_annotation(x=wk, y=7.4, text=mname, showarrow=False,
                           font=dict(size=10, color=TEXT_DIM), xref='x', yref='y')
    fig.update_layout(**_base(f'\U0001f4c5 V10 \u2014 {year} Viewing Calendar (Binge Heatmap)',
                              height=320, t=80, b=70, l=55, r=110))
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False, autorange='reversed', tickfont=dict(size=10))
    fig.update_layout(legend=dict(orientation='h', y=-0.18, font=dict(size=10), bgcolor='rgba(0,0,0,0)'))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V11 — Year-over-Year Change
# ═══════════════════════════════════════════════════════════════════════════════
def build_v11_yoy_waterfall(df: pd.DataFrame) -> go.Figure:
    annual = (df.groupby('year')['hours_watched'].sum().reset_index().sort_values('year'))
    annual['year'] = annual['year'].astype(int)
    annual['yoy'] = annual['hours_watched'].diff()
    annual['pct'] = (annual['yoy'] / annual['hours_watched'].shift(1) * 100).round(1)
    chg = annual.dropna(subset=['yoy']).copy()
    prev_hrs = annual['hours_watched'].shift(1).dropna().values
    bar_colors = ['rgba(26,188,156,0.88)' if v >= 0 else 'rgba(231,76,60,0.88)'
                  for v in chg['yoy']]
    texts = []
    for v, p, prev in zip(chg['yoy'], chg['pct'], prev_hrs):
        prefix = '+' if v >= 0 else ''
        if abs(prev) < 20:
            texts.append(f"{prefix}{v:.0f}h")
        else:
            texts.append(f"{prefix}{v:.0f}h  ({prefix}{p:.0f}%)")
    fig = go.Figure(go.Bar(
        x=list(chg['year']), y=list(chg['yoy']),
        name='YoY Change',
        marker_color=bar_colors,
        marker_line=dict(color='rgba(255,255,255,0.15)', width=0.5),
        text=texts, textposition='outside', textfont=dict(size=9, color='white'),
        cliponaxis=False,
        hovertemplate='<b>%{x}</b><br>%{y:+.0f}h vs prior year<extra></extra>',
    ))
    fig.add_hline(y=0, line=dict(color='rgba(255,255,255,0.28)', width=1.5))
    fig.add_trace(go.Scatter(
        x=list(annual['year']), y=list(annual['hours_watched']),
        mode='lines+markers', name='Annual total (h)',
        line=dict(color=PURPLE, width=1.5, dash='dot'),
        marker=dict(size=5, color=PURPLE), yaxis='y2',
        hovertemplate='%{x} total: %{y:.0f}h<extra></extra>',
    ))
    no_nan = annual.dropna(subset=['yoy'])
    worst = no_nan.loc[no_nan['yoy'].idxmin()]
    best = no_nan.loc[no_nan['yoy'].idxmax()]
    fig.add_annotation(xref='paper', yref='paper', x=0.01, y=0.01,
                       text=(f"Biggest drop  : {int(worst['year'])}  {worst['yoy']:+.0f}h  ({worst['pct']:.0f}%)<br>"
                             f"Biggest surge : {int(best['year'])}   {best['yoy']:+.0f}h  ({best['pct']:+.0f}%)"),
                       font=dict(size=9, color=TEXT_DIM), showarrow=False,
                       xanchor='left', yanchor='bottom',
                       bgcolor='rgba(10,10,20,0.75)', borderpad=4, align='left')
    fig.update_layout(**_base('\U0001f4c9 V11 \u2014 Year-over-Year Viewing Change',
                              height=490, t=90, b=70, l=75, r=80))
    fig.update_layout(
        xaxis=dict(title='Year', tickmode='linear', dtick=1, tickformat='d',
                   showgrid=False, range=[chg['year'].min() - 0.6, chg['year'].max() + 0.6]),
        yaxis=dict(title='Hours Changed vs Prior Year', showgrid=True, gridcolor=GRID,
                   zeroline=True, zerolinecolor='rgba(255,255,255,0.28)', zerolinewidth=1.5),
        yaxis2=dict(title='Annual Total (h)', overlaying='y', side='right',
                    showgrid=False, tickfont=dict(color=PURPLE, size=9)),
        legend=dict(orientation='h', y=1.09, bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  V12 — Monthly Engagement Heatmap
# ═══════════════════════════════════════════════════════════════════════════════
def build_v12_monthly_heatmap(df: pd.DataFrame) -> go.Figure:
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly = (df.groupby(['year', 'month_name'])['hours_watched'].sum().reset_index())
    monthly.columns = ['year', 'month', 'hours']
    monthly['month'] = pd.Categorical(monthly['month'], categories=month_order, ordered=True)
    monthly = monthly.sort_values(['year', 'month'])
    pivot = (monthly.pivot(index='year', columns='month', values='hours')
             .reindex(columns=month_order).fillna(0))
    z = pivot.values
    yrs = [str(y) for y in pivot.index]
    text = [[f"{v:.0f}h" if v >= 1 else '' for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=month_order, y=yrs,
        colorscale=[[0, '#0d0d1a'], [0.05, '#1a0533'], [0.20, '#4a1572'],
                    [0.45, '#9b59b6'], [0.70, '#1abc9c'], [1.0, '#f1c40f']],
        colorbar=dict(title=dict(text='Hours', font=dict(size=11)), ticksuffix='h', len=0.7, thickness=12),
        text=text, texttemplate='%{text}', textfont=dict(size=9, color='rgba(255,255,255,0.7)'),
        hovertemplate='<b>%{y} %{x}</b><br>Hours: %{z:.1f}h<extra></extra>',
        xgap=2, ygap=2,
    ))
    fig.add_shape(type='rect', x0=8.5, x1=10.5, y0=-0.5, y1=len(yrs) - 0.5,
                  line=dict(color=GOLD, width=1.5, dash='dash'), fillcolor='rgba(0,0,0,0)')
    fig.add_annotation(x=9.5, y=len(yrs) - 0.35, text='Worlds', showarrow=False,
                       font=dict(size=8, color=GOLD), yanchor='bottom')
    fig.add_shape(type='rect', x0=-0.5, x1=3.5, y0=-0.5, y1=len(yrs) - 0.5,
                  line=dict(color=PURPLE, width=1.5, dash='dash'), fillcolor='rgba(0,0,0,0)')
    fig.add_annotation(x=1.5, y=len(yrs) - 0.35, text='Spring Split', showarrow=False,
                       font=dict(size=8, color=PURPLE), yanchor='bottom')
    fig.update_layout(**_base('\U0001f5d3\ufe0f V12 \u2014 Monthly Engagement Heatmap (All Years \u00d7 All Months)',
                              height=420, t=90, b=60, l=65, r=100))
    fig.update_xaxes(title_text='Month', showgrid=False, side='bottom')
    fig.update_yaxes(title_text='Year', showgrid=False, autorange='reversed')
    return fig
