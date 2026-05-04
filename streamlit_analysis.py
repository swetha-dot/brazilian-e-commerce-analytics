import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Olist E-Commerce Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #F8F9FA; }
    .kpi-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #4F46E5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #1E1B4B;
        margin: 0;
    }
    .kpi-label {
        font-size: 13px;
        color: #6B7280;
        margin: 4px 0 0 0;
    }
    /* ── WHITE section headers ── */
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #FFFFFF;
        background: #4F46E5;
        padding: 8px 14px;
        border-radius: 6px;
        margin-bottom: 15px;
        letter-spacing: 0.3px;
    }
    .insight-box {
        background: #EEF2FF;
        border: 1px solid #C7D2FE;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
        font-size: 14px;
        color: #3730A3;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("dataset/olist_tableau_ready.csv")
    #df = pd.read_csv(
       # r'C:\Users\hp\Documents\GitHub\tableau\analysis\dataset\olist_tableau_ready.csv'
    #)
    date_cols = [
        'order_purchase_timestamp',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


@st.cache_data
def compute_rfm(_df):
    snapshot = _df['order_purchase_timestamp'].max()
    rfm = _df.groupby('customer_unique_id').agg(
        recency   = ('order_purchase_timestamp',
                     lambda x: (snapshot - x.max()).days),
        frequency = ('order_id', 'nunique'),
        monetary  = ('payment_value', 'sum')
    ).reset_index()

    def segment(row):
        if row['frequency'] >= 3 and row['monetary'] >= 500:
            return 'Champions'
        elif row['frequency'] >= 2:
            return 'Loyal'
        elif row['frequency'] == 1 and row['monetary'] >= 200:
            return 'At Risk'
        else:
            return 'Lost'

    rfm['Segment'] = rfm.apply(segment, axis=1)
    return rfm


# ─────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────
df  = load_data()
rfm = compute_rfm(df)


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
st.sidebar.markdown("## 📦 Olist Analytics")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")

years = sorted(df['order_year'].dropna().unique())
selected_years = st.sidebar.multiselect("Select Year", years, default=years)

categories = sorted(df['category_english'].dropna().unique())
selected_cats = st.sidebar.multiselect("Select Category", categories, default=[])

states = sorted(df['customer_state'].dropna().unique())
selected_states = st.sidebar.multiselect("Select State", states, default=[])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Navigation")
page = st.sidebar.radio("Go to", [
    "🏠 Executive Summary",
    "📈 Revenue Analysis",
    "🚚 Delivery Performance",
    "👥 Customer Segments",
    "🔬 Statistical Testing"
])

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Project:** Olist E-Commerce  
**Data:** 100K+ Orders · 9 Tables  
**Tools:** Python · Streamlit · Plotly  
""")


# ─────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────
mask = df['order_year'].astype(str).isin([str(y) for y in selected_years])
if selected_cats:
    mask &= df['category_english'].isin(selected_cats)
if selected_states:
    mask &= df['customer_state'].isin(selected_states)

filtered = df[mask].copy()
orders   = filtered.drop_duplicates('order_id')


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def kpi_card(label, value, delta=None):
    delta_html = (
        f"<p style='font-size:12px;color:#10B981;margin:2px 0 0 0'>{delta}</p>"
        if delta else ""
    )
    return f"""
    <div class='kpi-card'>
        <p class='kpi-value'>{value}</p>
        <p class='kpi-label'>{label}</p>
        {delta_html}
    </div>"""


def insight(text):
    st.markdown(f"<div class='insight-box'>💡 {text}</div>",
                unsafe_allow_html=True)


# ── Base layout — NO xaxis/yaxis keys here.
#    Axis styles are applied via fig.update_xaxes() / fig.update_yaxes()
#    to avoid "multiple values for keyword argument" errors.
CHART_LAYOUT = dict(
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(l=0, r=0, t=10, b=0),
    font=dict(color='#111827', size=12, family='Arial'),
)

# Reusable axis style dicts
X_STYLE = dict(
    tickfont=dict(color='#111827', size=11),
    title_font=dict(color='#111827', size=12),
    linecolor='#D1D5DB',
    showgrid=False,
)
X_STYLE_GRID = dict(
    tickfont=dict(color='#111827', size=11),
    title_font=dict(color='#111827', size=12),
    linecolor='#D1D5DB',
    showgrid=True,
    gridcolor='#E5E7EB',
)
Y_STYLE = dict(
    tickfont=dict(color='#111827', size=11),
    title_font=dict(color='#111827', size=12),
    gridcolor='#E5E7EB',
    linecolor='#D1D5DB',
)
Y_STYLE_NOGRID = dict(
    tickfont=dict(color='#111827', size=11),
    title_font=dict(color='#111827', size=12),
    linecolor='#D1D5DB',
    showgrid=False,
)

COLOR_MAP = {
    'Champions': '#1E3A8A',
    'Loyal':     '#0D9488',
    'At Risk':   '#F59E0B',
    'Lost':      '#9CA3AF'
}


# ─────────────────────────────────────────
# PAGE 1 — EXECUTIVE SUMMARY
# ─────────────────────────────────────────
if page == "🏠 Executive Summary":

    st.markdown("# 📦 Olist Brazilian E-Commerce Analytics")
    st.markdown("**Data Source:** Kaggle Olist Dataset · 2016–2018 · 100K+ Real Orders")
    st.markdown("---")

    total_rev  = orders['payment_value'].sum()
    total_ord  = orders['order_id'].nunique()
    aov        = total_rev / total_ord if total_ord else 0
    avg_review = filtered['review_score'].mean()
    late_pct   = orders['is_late'].mean() * 100
    avg_del    = orders['delivery_days'].mean()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(kpi_card("💰 Total Revenue",   f"R$ {total_rev:,.0f}"), unsafe_allow_html=True)
    c2.markdown(kpi_card("📦 Total Orders",    f"{total_ord:,}"),       unsafe_allow_html=True)
    c3.markdown(kpi_card("🛒 Avg Order Value", f"R$ {aov:.2f}"),        unsafe_allow_html=True)
    c4.markdown(kpi_card("⭐ Avg Review",       f"{avg_review:.2f}"),   unsafe_allow_html=True)
    c5.markdown(kpi_card("🕐 Late Delivery",   f"{late_pct:.1f}%"),     unsafe_allow_html=True)
    c6.markdown(kpi_card("📅 Avg Delivery",    f"{avg_del:.1f} days"),  unsafe_allow_html=True)

    st.markdown("---")

    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.markdown("<p class='section-header'>📈 Monthly Revenue Trend</p>",
                    unsafe_allow_html=True)
        monthly = (filtered.groupby('order_month')['payment_value']
                   .sum().reset_index().sort_values('order_month'))
        fig = px.area(monthly, x='order_month', y='payment_value',
                      labels={'payment_value': 'Revenue (R$)', 'order_month': 'Month'},
                      color_discrete_sequence=['#4F46E5'])
        fig.update_layout(height=320, **CHART_LAYOUT)
        fig.update_xaxes(**X_STYLE)
        fig.update_yaxes(**Y_STYLE)
        fig.update_traces(line_width=2.5)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("<p class='section-header'>🏆 Top 10 Categories</p>",
                    unsafe_allow_html=True)
        top_cats = (filtered.groupby('category_english')['payment_value']
                    .sum().sort_values(ascending=True).tail(10).reset_index())
        fig2 = px.bar(top_cats, x='payment_value', y='category_english',
                      orientation='h',
                      labels={'payment_value': 'Revenue', 'category_english': ''},
                      color='payment_value', color_continuous_scale='Blues')
        fig2.update_layout(height=320, **CHART_LAYOUT,
                           showlegend=False, coloraxis_showscale=False)
        fig2.update_xaxes(**X_STYLE_GRID)
        fig2.update_yaxes(**Y_STYLE_NOGRID)
        st.plotly_chart(fig2, use_container_width=True)

    if not monthly.empty:
        peak = monthly.loc[monthly['payment_value'].idxmax(), 'order_month']
        insight(f"Peak revenue occurred in **{peak}**. "
                f"Focus marketing budget on the top category for maximum ROI.")

    st.markdown("---")

    col_c, col_d = st.columns([1.5, 1])

    with col_c:
        # ── FIXED: choropleth → working horizontal bar chart ──
        st.markdown("<p class='section-header'>🗺️ Revenue by State (Top 15)</p>",
                    unsafe_allow_html=True)
        state_rev = (filtered.groupby('customer_state')['payment_value']
                     .sum().sort_values(ascending=True).tail(15).reset_index())
        state_rev.columns = ['State', 'Revenue']
        fig3 = px.bar(state_rev, x='Revenue', y='State', orientation='h',
                      color='Revenue', color_continuous_scale='Blues',
                      labels={'Revenue': 'Revenue (R$)', 'State': 'State'},
                      text='Revenue')
        fig3.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside',
                           textfont=dict(color='#111827', size=10))
        fig3.update_layout(height=420, **CHART_LAYOUT, coloraxis_showscale=False)
        fig3.update_xaxes(**X_STYLE_GRID)
        fig3.update_yaxes(**Y_STYLE_NOGRID)
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown("<p class='section-header'>👥 Customer Segments</p>",
                    unsafe_allow_html=True)
        seg = rfm['Segment'].value_counts().reset_index()
        seg.columns = ['Segment', 'Count']
        fig4 = go.Figure(go.Pie(
            labels=seg['Segment'], values=seg['Count'], hole=0.55,
            marker_colors=[COLOR_MAP.get(s, '#999') for s in seg['Segment']],
            textinfo='label+percent',
            textfont=dict(color='#111827', size=12),
            hovertemplate='%{label}<br>Count: %{value:,}<extra></extra>'
        ))
        fig4.update_layout(height=420, **CHART_LAYOUT, showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    lost_pct = (rfm['Segment'] == 'Lost').mean() * 100
    atrisk_n = (rfm['Segment'] == 'At Risk').sum()
    insight(f"**{lost_pct:.0f}%** of customers are in the Lost segment — "
            f"purchased once and never returned. "
            f"Re-engagement campaign targeting **{atrisk_n:,} At Risk customers** "
            f"could significantly improve retention.")


# ─────────────────────────────────────────
# PAGE 2 — REVENUE ANALYSIS
# ─────────────────────────────────────────
elif page == "📈 Revenue Analysis":

    st.markdown("# 📈 Revenue Deep Dive")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<p class='section-header'>Revenue by Year</p>",
                    unsafe_allow_html=True)
        yearly = (filtered.groupby('order_year')['payment_value'].sum().reset_index())
        fig = px.bar(yearly, x='order_year', y='payment_value',
                     labels={'payment_value': 'Revenue (R$)', 'order_year': 'Year'},
                     color='payment_value', color_continuous_scale='Blues',
                     text='payment_value')
        fig.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside',
                          textfont=dict(color='#111827', size=11))
        fig.update_layout(height=320, **CHART_LAYOUT, coloraxis_showscale=False)
        fig.update_xaxes(**X_STYLE)
        fig.update_yaxes(**Y_STYLE)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<p class='section-header'>Revenue by Payment Type</p>",
                    unsafe_allow_html=True)
        if 'payment_type' in filtered.columns:
            pay = (filtered.groupby('payment_type')['payment_value'].sum().reset_index())
            fig2 = px.pie(pay, names='payment_type', values='payment_value',
                          color_discrete_sequence=px.colors.qualitative.Bold, hole=0.4)
            fig2.update_traces(textfont=dict(color='#111827', size=12))
            fig2.update_layout(height=320, **CHART_LAYOUT)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    st.markdown("<p class='section-header'>Category Performance Table</p>",
                unsafe_allow_html=True)
    cat_table = (
        filtered.groupby('category_english').agg(
            Total_Revenue   = ('payment_value', 'sum'),
            Total_Orders    = ('order_id',      'nunique'),
            Avg_Order_Value = ('payment_value', 'mean'),
            Avg_Review      = ('review_score',  'mean')
        ).reset_index()
        .sort_values('Total_Revenue', ascending=False)
        .head(20)
    )
    cat_table['Total_Revenue']   = cat_table['Total_Revenue'].map('R$ {:,.0f}'.format)
    cat_table['Total_Orders']    = cat_table['Total_Orders'].map('{:,}'.format)
    cat_table['Avg_Order_Value'] = cat_table['Avg_Order_Value'].map('R$ {:.2f}'.format)
    cat_table['Avg_Review']      = cat_table['Avg_Review'].map('{:.2f}'.format)
    cat_table.columns = ['Category', 'Revenue', 'Orders', 'Avg Order Value', 'Avg Review']
    st.dataframe(cat_table, use_container_width=True, hide_index=True)

    insight("Categories with high revenue but low review scores are quality improvement "
            "opportunities — fixing them can increase repeat purchases.")

    st.markdown("---")

    st.markdown("<p class='section-header'>Revenue Heatmap — Year vs Month</p>",
                unsafe_allow_html=True)
    filtered['month_num'] = pd.to_datetime(filtered['order_purchase_timestamp']).dt.month
    heatmap_data = (filtered.groupby(['order_year', 'month_num'])['payment_value']
                    .sum().reset_index())
    heatmap_pivot = heatmap_data.pivot(
        index='order_year', columns='month_num', values='payment_value').fillna(0)
    heatmap_pivot.columns = (
        ['Jan','Feb','Mar','Apr','May','Jun',
         'Jul','Aug','Sep','Oct','Nov','Dec'][:len(heatmap_pivot.columns)]
    )
    fig3 = px.imshow(heatmap_pivot, color_continuous_scale='Blues',
                     labels=dict(color='Revenue (R$)'), text_auto='.2s')
    fig3.update_traces(textfont=dict(color='#111827', size=11))
    fig3.update_layout(height=250, **CHART_LAYOUT)
    fig3.update_xaxes(**X_STYLE)
    fig3.update_yaxes(**Y_STYLE_NOGRID)
    st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────
# PAGE 3 — DELIVERY PERFORMANCE
# ─────────────────────────────────────────
elif page == "🚚 Delivery Performance":

    st.markdown("# 🚚 Delivery Performance Analysis")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Delivery Days", f"{orders['delivery_days'].mean():.1f} days")
    col2.metric("Late Orders",       f"{orders['is_late'].sum():,}",
                f"{orders['is_late'].mean()*100:.1f}% of total")
    col3.metric("On-Time Orders",    f"{(orders['is_late'] == 0).sum():,}",
                f"{(1 - orders['is_late'].mean())*100:.1f}% on time")

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("<p class='section-header'>Delivery Days Distribution</p>",
                    unsafe_allow_html=True)
        del_data = orders[orders['delivery_days'].between(0, 60)]['delivery_days']
        fig = px.histogram(del_data, x='delivery_days', nbins=30,
                           labels={'delivery_days': 'Delivery Days',
                                   'count': 'Number of Orders'},
                           color_discrete_sequence=['#4F46E5'])
        fig.update_layout(height=320, **CHART_LAYOUT, bargap=0)
        fig.update_xaxes(**X_STYLE)
        fig.update_yaxes(**Y_STYLE)
        fig.add_vline(x=del_data.mean(), line_dash='dash', line_color='red',
                      annotation_text=f"Avg: {del_data.mean():.1f}d",
                      annotation_position='top right',
                      annotation_font=dict(color='#B91C1C', size=12))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("<p class='section-header'>Late Delivery % by State</p>",
                    unsafe_allow_html=True)
        late_state = (orders.groupby('customer_state')['is_late']
                      .mean().mul(100).sort_values(ascending=False)
                      .head(10).reset_index())
        late_state.columns = ['State', 'Late %']
        fig2 = px.bar(late_state, x='State', y='Late %',
                      color='Late %', color_continuous_scale='Reds',
                      labels={'Late %': 'Late Delivery %'}, text='Late %')
        fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside',
                           textfont=dict(color='#111827', size=11))
        fig2.update_layout(height=320, **CHART_LAYOUT, coloraxis_showscale=False)
        fig2.update_xaxes(**X_STYLE)
        fig2.update_yaxes(**Y_STYLE)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    st.markdown("<p class='section-header'>Avg Delivery Days by Category (Top 15)</p>",
                unsafe_allow_html=True)
    cat_del = (filtered.groupby('category_english')['delivery_days']
               .mean().sort_values(ascending=False).head(15).reset_index())
    fig3 = px.bar(cat_del, x='delivery_days', y='category_english', orientation='h',
                  color='delivery_days', color_continuous_scale='RdYlGn_r',
                  labels={'delivery_days': 'Avg Days', 'category_english': ''},
                  text='delivery_days')
    fig3.update_traces(texttemplate='%{text:.1f}d', textposition='outside',
                       textfont=dict(color='#111827', size=11))
    fig3.update_layout(height=450, **CHART_LAYOUT, coloraxis_showscale=False)
    fig3.update_xaxes(**X_STYLE_GRID)
    fig3.update_yaxes(**Y_STYLE_NOGRID)
    st.plotly_chart(fig3, use_container_width=True)

    insight("States with highest late delivery % likely have last-mile logistics issues — "
            "recommend partnering with regional carriers in those states.")


# ─────────────────────────────────────────
# PAGE 4 — CUSTOMER SEGMENTS
# ─────────────────────────────────────────
elif page == "👥 Customer Segments":

    st.markdown("# 👥 Customer Segmentation — RFM Analysis")
    st.markdown("---")

    seg_counts = rfm['Segment'].value_counts()
    col1, col2, col3, col4 = st.columns(4)

    for col, seg, color in zip(
        [col1, col2, col3, col4],
        ['Champions', 'Loyal', 'At Risk', 'Lost'],
        ['#1E3A8A',   '#0D9488', '#F59E0B', '#6B7280']
    ):
        count = seg_counts.get(seg, 0)
        pct   = count / len(rfm) * 100
        col.markdown(f"""
        <div style='background:white;padding:16px;border-radius:10px;
                    border-top:4px solid {color};text-align:center;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08)'>
            <p style='font-size:24px;font-weight:700;color:{color};margin:0'>{count:,}</p>
            <p style='font-size:13px;color:#374151;margin:4px 0 0 0;font-weight:600'>{seg}</p>
            <p style='font-size:12px;color:#6B7280;margin:2px 0 0 0'>{pct:.1f}%</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("<p class='section-header'>Segment Distribution</p>",
                    unsafe_allow_html=True)
        seg_df = rfm['Segment'].value_counts().reset_index()
        seg_df.columns = ['Segment', 'Count']
        fig = go.Figure(go.Pie(
            labels=seg_df['Segment'], values=seg_df['Count'], hole=0.55,
            marker_colors=[COLOR_MAP[s] for s in seg_df['Segment']],
            textinfo='label+percent',
            textfont=dict(color='#111827', size=12),
            hovertemplate='%{label}<br>%{value:,} customers<extra></extra>'
        ))
        fig.update_layout(height=360, **CHART_LAYOUT, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("<p class='section-header'>Recency vs Monetary (Sample 3000)</p>",
                    unsafe_allow_html=True)
        sample = rfm.sample(min(3000, len(rfm)), random_state=42)
        fig2 = px.scatter(sample, x='recency', y='monetary',
                          color='Segment', size='frequency',
                          color_discrete_map=COLOR_MAP,
                          labels={'recency': 'Recency (days)',
                                  'monetary': 'Total Spend (R$)',
                                  'frequency': 'Orders'},
                          opacity=0.7)
        fig2.update_layout(height=360, **CHART_LAYOUT,
                           legend=dict(font=dict(color='#111827', size=11)))
        fig2.update_xaxes(**X_STYLE_GRID)
        fig2.update_yaxes(**Y_STYLE)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    st.markdown("<p class='section-header'>Segment Summary Statistics</p>",
                unsafe_allow_html=True)
    seg_stats = (
        rfm.groupby('Segment').agg(
            Customers     = ('customer_unique_id', 'count'),
            Avg_Recency   = ('recency',   'mean'),
            Avg_Frequency = ('frequency', 'mean'),
            Avg_Monetary  = ('monetary',  'mean'),
            Total_Revenue = ('monetary',  'sum')
        ).reset_index()
    )
    seg_stats['Avg_Recency']   = seg_stats['Avg_Recency'].map('{:.0f} days'.format)
    seg_stats['Avg_Frequency'] = seg_stats['Avg_Frequency'].map('{:.1f} orders'.format)
    seg_stats['Avg_Monetary']  = seg_stats['Avg_Monetary'].map('R$ {:.2f}'.format)
    seg_stats['Total_Revenue'] = seg_stats['Total_Revenue'].map('R$ {:,.0f}'.format)
    seg_stats['Customers']     = seg_stats['Customers'].map('{:,}'.format)
    seg_stats.columns = ['Segment', 'Customers', 'Avg Recency',
                         'Avg Frequency', 'Avg Spend', 'Total Revenue']
    st.dataframe(seg_stats, use_container_width=True, hide_index=True)

    insight("Focus retention campaigns on At Risk customers — "
            "they spent well but haven't returned recently. "
            "Champions should receive loyalty rewards to maintain engagement.")


# ─────────────────────────────────────────
# PAGE 5 — STATISTICAL TESTING
# ─────────────────────────────────────────
elif page == "🔬 Statistical Testing":

    st.markdown("# 🔬 Statistical Testing")
    st.markdown("*Hypothesis testing to validate business insights with numbers*")
    st.markdown("---")

    # ── Test 1: T-Test ──
    st.markdown("<p class='section-header'>Test 1 — T-Test: Do SP customers spend more than RJ?</p>",
                unsafe_allow_html=True)

    sp = filtered[filtered['customer_state'] == 'SP']['payment_value'].dropna()
    rj = filtered[filtered['customer_state'] == 'RJ']['payment_value'].dropna()

    if len(sp) > 1 and len(rj) > 1:
        t_stat, p_val = stats.ttest_ind(sp, rj)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("SP Avg Spend", f"R$ {sp.mean():.2f}")
        col2.metric("RJ Avg Spend", f"R$ {rj.mean():.2f}")
        col3.metric("T-Statistic",  f"{t_stat:.4f}")
        col4.metric("P-Value",      f"{p_val:.4f}")

        if p_val < 0.05:
            st.success(f"✅ SIGNIFICANT (p = {p_val:.4f} < 0.05) — "
                       f"SP and RJ customers spend differently. "
                       f"SP spends R$ {sp.mean() - rj.mean():.2f} more on average.")
        else:
            st.info(f"❌ NOT SIGNIFICANT (p = {p_val:.4f} > 0.05) — "
                    f"No significant spending difference between SP and RJ.")

        fig = go.Figure()
        fig.add_trace(go.Box(y=sp.clip(upper=sp.quantile(0.95)),
                             name='São Paulo', marker_color='#4F46E5'))
        fig.add_trace(go.Box(y=rj.clip(upper=rj.quantile(0.95)),
                             name='Rio de Janeiro', marker_color='#10B981'))
        fig.update_layout(height=300, **CHART_LAYOUT, yaxis_title='Order Value (R$)',
                          legend=dict(font=dict(color='#111827', size=11)))
        fig.update_xaxes(**X_STYLE)
        fig.update_yaxes(**Y_STYLE)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Test 2: Chi-Square ──
    st.markdown("<p class='section-header'>Test 2 — Chi-Square: Is late delivery related to payment type?</p>",
                unsafe_allow_html=True)

    if 'payment_type' in filtered.columns:
        contingency = pd.crosstab(orders['payment_type'], orders['is_late'])
        chi2, p_chi, dof, _ = stats.chi2_contingency(contingency)

        col1, col2, col3 = st.columns(3)
        col1.metric("Chi2 Statistic",     f"{chi2:.4f}")
        col2.metric("P-Value",            f"{p_chi:.4f}")
        col3.metric("Degrees of Freedom", f"{dof}")

        if p_chi < 0.05:
            st.success(f"✅ SIGNIFICANT — Payment type IS associated "
                       f"with late delivery (p = {p_chi:.4f})")
        else:
            st.info(f"❌ NOT SIGNIFICANT — Payment type is NOT "
                    f"associated with late delivery (p = {p_chi:.4f})")

        fig2 = px.imshow(contingency,
                         labels=dict(x='Is Late (0=No, 1=Yes)',
                                     y='Payment Type', color='Count'),
                         color_continuous_scale='Blues', text_auto=True)
        fig2.update_traces(textfont=dict(color='#111827', size=12))
        fig2.update_layout(height=300, **CHART_LAYOUT)
        fig2.update_xaxes(**X_STYLE)
        fig2.update_yaxes(**Y_STYLE_NOGRID)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ── Test 3: ANOVA ──
    st.markdown("<p class='section-header'>Test 3 — ANOVA: Do review scores differ across top categories?</p>",
                unsafe_allow_html=True)

    top5 = (filtered.groupby('category_english')['payment_value']
            .sum().nlargest(5).index.tolist())
    groups = [filtered[filtered['category_english'] == c]['review_score'].dropna()
              for c in top5]
    groups = [g for g in groups if len(g) > 1]

    if len(groups) >= 2:
        f_stat, p_anova = stats.f_oneway(*groups)

        col1, col2 = st.columns(2)
        col1.metric("F-Statistic", f"{f_stat:.4f}")
        col2.metric("P-Value",     f"{p_anova:.4f}")

        if p_anova < 0.05:
            st.success(f"✅ SIGNIFICANT — Review scores differ across "
                       f"categories (p = {p_anova:.4f}). Category quality is NOT equal.")
        else:
            st.info(f"❌ NOT SIGNIFICANT (p = {p_anova:.4f}) — "
                    f"No significant difference in review scores.")

        plot_df = filtered[filtered['category_english'].isin(top5)
                           ][['category_english', 'review_score']].dropna()
        fig3 = px.box(plot_df, x='category_english', y='review_score',
                      color='category_english',
                      labels={'category_english': 'Category',
                               'review_score': 'Review Score'},
                      color_discrete_sequence=px.colors.qualitative.Bold)
        fig3.update_layout(height=380, **CHART_LAYOUT, showlegend=False)
        fig3.update_xaxes(**X_STYLE)
        fig3.update_yaxes(**Y_STYLE)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # ── Test 4: Z-Test ──
    st.markdown("<p class='section-header'>Test 4 — Z-Test: Is avg order value significantly above R$ 100?</p>",
                unsafe_allow_html=True)

    from statsmodels.stats.weightstats import ztest

    order_vals = orders['payment_value'].dropna()
    z_stat, p_z = ztest(order_vals, value=100)

    col1, col2, col3 = st.columns(3)
    col1.metric("Sample Mean", f"R$ {order_vals.mean():.2f}")
    col2.metric("Z-Statistic", f"{z_stat:.4f}")
    col3.metric("P-Value",     f"{p_z:.4f}")

    if p_z < 0.05:
        st.success(f"✅ SIGNIFICANT — Avg order value of R$ {order_vals.mean():.2f} "
                   f"is significantly above R$ 100 (p = {p_z:.4f})")
    else:
        st.info(f"❌ NOT SIGNIFICANT (p = {p_z:.4f})")

    insight("Statistical tests add credibility to your analysis. "
            "In interviews say: 'I didn't just observe the trend — "
            "I validated it with a t-test / chi-square / ANOVA "
            "to confirm it wasn't due to random chance.' "
            "That statement alone puts you ahead of 90% of candidates.")