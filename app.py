import streamlit as st
import pandas as pd
import plotly.express as px
import pylast

# 1. SETUP & CONFIG
st.set_page_config(page_title="Bands Seen Live & Listening", layout="wide")
st.title("🎸 Band Tracker & Listening Dashboard")

# Replace this with your Google Sheet URL (Ensure it ends in /export?format=csv)
# Example: https://docs.google.com/spreadsheets/d/YOUR_ID/export?format=csv
SHEET_URL = "https://docs.google.com/spreadsheets/d/14A51bdUSAA42npkHwheLjgR2VVYDGKH9SivzSOkYe8o/export?format=csv"

# Last.fm Setup (We will use Streamlit Secrets for the API Key later)
LAST_FM_USER = "Beach_Patrol"
LAST_FM_KEY = st.secrets["LASTFM_API_KEY"]

# 2. DATA LOADING
@st.cache_data(ttl=600) # Refreshes every 10 mins
def load_data():
    df = pd.read_csv(SHEET_URL)
    df['Date Seen'] = pd.to_datetime(df['Date Seen'])
    return df

try:
    df = load_data()
    
    # 3. SIDEBAR / FILTERS
    st.sidebar.header("Filters")
    selected_genre = st.sidebar.multiselect("Filter by Genre", options=df['Genre'].unique(), default=df['Genre'].unique())
    filtered_df = df[df['Genre'].isin(selected_genre)]

    # 4. KEY METRICS
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Gigs", len(filtered_df))
    col2.metric("Unique Artists", filtered_df['Artist'].nunique())
    col3.metric("Top Venue", filtered_df['Venue'].mode()[0])

    # 5. VISUALIZATIONS
    st.subheader("Gig History Over Time")
    line_chart = px.histogram(filtered_df, x="Date Seen", nbins=20, color="Genre", 
                             template="plotly_dark", labels={'count': 'Number of Shows'})
    st.plotly_chart(line_chart, use_container_width=True)

    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Top Artists Seen")
        top_artists = filtered_df['Artist'].value_counts().reset_index().head(10)
        fig_artists = px.bar(top_artists, x='count', y='Artist', orientation='h', color='count')
        st.plotly_chart(fig_artists, use_container_width=True)

    with c2:
        st.subheader("Recent Listening (Last.fm)")
        try:
            network = pylast.LastFMNetwork(api_key=LAST_FM_KEY)
            user = network.get_user(LAST_FM_USER)
            recent_tracks = user.get_recent_tracks(limit=5)
            for track in recent_tracks:
                st.write(f"🎵 **{track.track.artist}** - {track.track.title}")
        except Exception as e:
            st.info("Link your Last.fm API key in Settings to see live listening activity.")

except Exception as e:
    st.error(f"Error loading data. Check your Google Sheet URL. Details: {e}")
