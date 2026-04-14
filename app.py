import streamlit as st
import pandas as pd
import plotly.express as px

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
    
    # Extract Year and Month/Year period for average calculations
    df['Year'] = df['Date Seen'].dt.year

    # 3. SIDEBAR / FILTERS
    st.sidebar.header("Filters")
    
    # Create Year Filter
    available_years = sorted(df['Year'].dropna().unique().tolist(), reverse=True)
    
    timeframe = st.sidebar.radio("Select Timeframe", options=["All Time", "Specific Year(s)"])
    
    if timeframe == "Specific Year(s)":
        selected_years = st.sidebar.multiselect("Select Year(s)", options=available_years, default=available_years[0])
        filtered_df = df[df['Year'].isin(selected_years)].copy()
    else:
        filtered_df = df.copy()

    # 4. METRICS CALCULATIONS
    total_bands = len(filtered_df)
    unique_bands = filtered_df['Artist'].nunique()
    total_gigs = filtered_df['Date Seen'].nunique()

    # Calculate Longest Gap Between Gigs
    # We sort by unique dates first, then find the difference in days between them
    sorted_dates = filtered_df['Date Seen'].drop_duplicates().sort_values()
    if len(sorted_dates) > 1:
        longest_gap = sorted_dates.diff().dt.days.max()
    else:
        longest_gap = 0

    # Calculate Averages 
    # Use nunique() to dynamically see how many distinct years/months are in the filtered data
    num_years = filtered_df['Year'].nunique()
    num_months = filtered_df['Date Seen'].dt.to_period('M').nunique()
    
    # Avoid dividing by zero if the dataset is completely empty for some reason
    num_years = num_years if num_years > 0 else 1
    num_months = num_months if num_months > 0 else 1
    
    yearly_avg_total = total_bands / num_years
    yearly_avg_unique = unique_bands / num_years
    monthly_avg_total = total_bands / num_months
    monthly_avg_unique = unique_bands / num_months

    # 5. RENDER METRICS
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Bands Seen", total_bands)
    col2.metric("Unique Bands Seen", unique_bands)
    col3.metric("Gigs Attended", total_gigs)
    col4.metric("Longest Gap (Days)", int(longest_gap))

    st.subheader("📈 Averages")
    avg1, avg2, avg3, avg4 = st.columns(4)
    avg1.metric("Yearly Avg (Total)", f"{yearly_avg_total:.1f}")
    avg2.metric("Yearly Avg (Unique)", f"{yearly_avg_unique:.1f}")
    avg3.metric("Monthly Avg (Total)", f"{monthly_avg_total:.1f}")
    avg4.metric("Monthly Avg (Unique)", f"{monthly_avg_unique:.1f}")

    st.divider()

    # 6. TOP 10 LEADERBOARDS
    st.subheader("🏆 Top 10 Leaderboards")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Top 10 Bands
        top_bands = filtered_df['Artist'].value_counts().head(10).reset_index()
        top_bands.columns = ['Artist', 'Times Seen']
        
        fig_bands = px.bar(top_bands, x='Times Seen', y='Artist', orientation='h', text='Times Seen')
        fig_bands.update_layout(yaxis={'categoryorder':'total ascending'}) # Sorts highest to top
        st.plotly_chart(fig_bands, use_container_width=True)

    with chart_col2:
        # Top 10 Venues
        top_venues = filtered_df['Venue'].value_counts().head(10).reset_index()
        top_venues.columns = ['Venue', 'Bands Seen']
        
        fig_venues = px.bar(top_venues, x='Bands Seen', y='Venue', orientation='h', text='Bands Seen')
        fig_venues.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_venues, use_container_width=True)

except Exception as e:
    st.error(f"Error loading data. Check your Google Sheet URL or columns. Details: {e}")
