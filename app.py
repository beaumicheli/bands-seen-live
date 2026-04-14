import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. SETUP & CONFIG
st.set_page_config(page_title="Bands Seen Live", layout="wide")
st.title("🎸 Bands Seen Live Dashboard")

# Replace this with your Google Sheet URL (Ensure it ends in /export?format=csv)
SHEET_URL = "https://docs.google.com/spreadsheets/d/14A51bdUSAA42npkHwheLjgR2VVYDGKH9SivzSOkYe8o/export?format=csv"

# 2. DATA LOADING & CLEANING
@st.cache_data(ttl=600) # Refreshes every 10 mins
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip() # Clean header spaces
    if 'Date Seen' in df.columns:
        df['Date Seen'] = pd.to_datetime(df['Date Seen'], dayfirst=True)
    return df

try:
    df = load_data()
    
    # Extract Year 
    df['Year'] = df['Date Seen'].dt.year
    
    # Pre-calculate Event Type for the whole dataset
    df['Event Type'] = df['Festival'].apply(
        lambda x: 'Gig' if pd.isna(x) or str(x).strip() == '' else 'Festival'
    )

    # 3. SIDEBAR / FILTERS
    st.sidebar.header("Filters")
    available_years = sorted(df['Year'].dropna().unique().tolist(), reverse=True)
    timeframe = st.sidebar.radio("Select Timeframe", options=["All Time", "Specific Year(s)"])
    
    if timeframe == "Specific Year(s)":
        selected_years = st.sidebar.multiselect("Select Year(s)", options=available_years, default=available_years[0])
        filtered_df = df[df['Year'].isin(selected_years)].copy()
    else:
        filtered_df = df.copy()

    # 4. METRICS & ADVANCED CALCULATIONS
    total_bands = len(filtered_df)
    unique_bands = filtered_df['Artist'].nunique()
    total_gigs = filtered_df['Date Seen'].nunique()

    # Longest Gap
    sorted_dates = filtered_df['Date Seen'].drop_duplicates().sort_values()
    longest_gap = sorted_dates.diff().dt.days.max() if len(sorted_dates) > 1 else 0

    # Averages
    num_years = max(filtered_df['Year'].nunique(), 1)
    num_months = max(filtered_df['Date Seen'].dt.to_period('M').nunique(), 1)
    
    yearly_avg_total, yearly_avg_unique = total_bands / num_years, unique_bands / num_years
    monthly_avg_total, monthly_avg_unique = total_bands / num_months, unique_bands / num_months

    # MULTI-DAY FESTIVAL LOGIC
    fest_df = filtered_df[filtered_df['Event Type'] == 'Festival'].copy()
    
    if not fest_df.empty:
        fest_df = fest_df.sort_values(by=['Festival', 'Date Seen'])
        fest_df['Prev_Date'] = fest_df.groupby('Festival')['Date Seen'].shift(1)
        fest_df['Days_Diff'] = (fest_df['Date Seen'] - fest_df['Prev_Date']).dt.days
        fest_df['New_Instance'] = (fest_df['Days_Diff'].isna()) | (fest_df['Days_Diff'] > 1)
        total_festivals = fest_df['New_Instance'].sum()
    else:
        total_festivals = 0

    # 5. RENDER TOP METRICS
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Bands Seen", total_bands)
    col2.metric("Unique Bands Seen", unique_bands)
    col3.metric("Gigs Attended", total_gigs)
    col4.metric("Festivals Attended", int(total_festivals))
    col5.metric("Longest Gap (Days)", int(longest_gap))

    st.subheader("📈 Averages")
    avg1, avg2, avg3, avg4 = st.columns(4)
    avg1.metric("Yearly Avg (Total)", f"{yearly_avg_total:.1f}")
    avg2.metric("Yearly Avg (Unique)", f"{yearly_avg_unique:.1f}")
    avg3.metric("Monthly Avg (Total)", f"{monthly_avg_total:.1f}")
    avg4.metric("Monthly Avg (Unique)", f"{monthly_avg_unique:.1f}")

    st.divider()

    # 6. YEARLY TRENDS
    st.subheader("📅 Yearly Trends")
    
    # Pre-calculate yearly stats for both the line chart and the bar chart
    yearly_stats = filtered_df.groupby('Year').agg(
        Total_Bands=('Artist', 'count'),
        Unique_Bands=('Artist', 'nunique')
    ).reset_index()

    # --- TOP ROW (FULL WIDTH LINE CHART) ---
    fig_line = px.line(yearly_stats, x='Year', y='Total_Bands', markers=True,
                       title="Total Bands Seen Live Over Time")
    fig_line.update_layout(xaxis=dict(tickmode='linear', dtick=1), yaxis_title="Count")
    st.plotly_chart(fig_line, use_container_width=True)
    
    # --- ROW 1 ---
    trend_r1_col1, trend_r1_col2 = st.columns(2)

    with trend_r1_col1:
        yearly_melted = yearly_stats.melt(id_vars='Year', value_vars=['Total_Bands', 'Unique_Bands'], 
                                          var_name='Type', value_name='Count')
        yearly_melted['Type'] = yearly_melted['Type'].str.replace('_', ' ')
        
        fig_yearly = px.bar(yearly_melted, x='Year', y='Count', color='Type', barmode='group',
                            title="Total vs Unique Bands per Year")
        fig_yearly.update_layout(xaxis=dict(tickmode='linear', dtick=1)) 
        st.plotly_chart(fig_yearly, use_container_width=True)

    with trend_r1_col2:
        genre_year = filtered_df.groupby(['Year', 'Genre']).size().reset_index(name='Count')
        fig_genre_year = px.bar(genre_year, x='Year', y='Count', color='Genre', 
                                title="Bands by Genre over Time (100% Stacked)")
        fig_genre_year.update_layout(barmode='stack', barnorm='percent', xaxis=dict(tickmode='linear', dtick=1), yaxis_title="% of Total")
        st.plotly_chart(fig_genre_year, use_container_width=True)

    # --- ROW 2 ---
    trend_r2_col1, trend_r2_col2 = st.columns(2)

    with trend_r2_col1:
        if not fest_df.empty:
            fest_year = fest_df.groupby(['Year', 'Festival']).size().reset_index(name='Count')
            fig_fest_year = px.bar(fest_year, x='Year', y='Count', color='Festival', 
                                    title="Bands Seen at Festivals by Year (100% Stacked)")
            fig_fest_year.update_layout(barmode='stack', barnorm='percent', xaxis=dict(tickmode='linear', dtick=1), yaxis_title="% of Total")
            st.plotly_chart(fig_fest_year, use_container_width=True)
        else:
            st.info("No festival data available to generate this chart.")

    with trend_r2_col2:
        event_year = filtered_df.groupby(['Year', 'Event Type']).size().reset_index(name='Count')
        fig_event_year = px.bar(event_year, x='Year', y='Count', color='Event Type', 
                                title="Festivals vs Gigs by Year (100% Stacked)",
                                color_discrete_map={'Gig': '#636EFA', 'Festival': '#EF553B'})
        fig_event_year.update_layout(barmode='stack', barnorm='percent', xaxis=dict(tickmode='linear', dtick=1), yaxis_title="% of Total")
        st.plotly_chart(fig_event_year, use_container_width=True)

    st.divider()

    # 7. GENRES & FORMATS
    st.subheader("🎵 Genres & Event Types")
    pie_col1, pie_col2 = st.columns(2)

    with pie_col1:
        genre_counts = filtered_df['Genre'].value_counts().reset_index()
        genre_counts.columns = ['Genre', 'Count']
        fig_pie_genre = px.pie(genre_counts, names='Genre', values='Count', title="All Band Genres (Total Seen)", hole=0.3)
        fig_pie_genre.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie_genre, use_container_width=True)

    with pie_col2:
        event_counts = filtered_df['Event Type'].value_counts().reset_index()
        event_counts.columns = ['Event Type', 'Count']
        fig_pie_events = px.pie(event_counts, names='Event Type', values='Count', title="Festivals vs Gigs (All Time)", hole=0.3)
        fig_pie_events.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie_events, use_container_width=True)

    st.divider()

    # 8. TOP 10 LEADERBOARDS 
    st.subheader("🏆 Top 10 Leaderboards")
    chart_col1, chart_col2, chart_col3 = st.columns(3)

    with chart_col1:
        top_bands = filtered_df['Artist'].value_counts().head(10).reset_index()
        top_bands.columns = ['Artist', 'Times Seen']
        fig_bands = px.bar(top_bands, x='Times Seen', y='Artist', orientation='h', text='Times Seen', title="Top Artists")
        fig_bands.update_layout(yaxis={'categoryorder':'total ascending'}) 
        st.plotly_chart(fig_bands, use_container_width=True)

    with chart_col2:
        top_venues = filtered_df['Venue'].value_counts().head(10).reset_index()
        top_venues.columns = ['Venue', 'Bands Seen']
        fig_venues = px.bar(top_venues, x='Bands Seen', y='Venue', orientation='h', text='Bands Seen', title="Top Venues")
        fig_venues.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_venues, use_container_width=True)
        
    with chart_col3:
        if not fest_df.empty:
            top_fests = fest_df[fest_df['New_Instance']].groupby('Festival').size().reset_index(name='Times Attended')
            top_fests = top_fests.sort_values('Times Attended', ascending=False).head(10)
            fig_fests = px.bar(top_fests, x='Times Attended', y='Festival', orientation='h', text='Times Attended', title="Top Festivals")
            fig_fests.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_fests, use_container_width=True)
        else:
            st.info("No festival data to display.")

except Exception as e:
    st.error(f"Error loading data. Check your Google Sheet URL or columns. Details: {e}")
