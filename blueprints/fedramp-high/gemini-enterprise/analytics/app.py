import streamlit as st
import plotly.express as px
from google.cloud import bigquery
import datetime
import os

# ==========================================
# CONFIGURATION & SETUP
# ==========================================
st.set_page_config(page_title="G4G Usage Analytics", layout="wide")

# Initialize BigQuery Client (Authentication inherited from GCP Compute/Run service account)
PROJECT_ID = os.environ.get("PROJECT_ID", "your-gcp-project-id")
DATASET_ID = os.environ.get("DATASET_ID", "your_dataset_id")
client = bigquery.Client(project=PROJECT_ID)

# ==========================================
# DATA LOADING & CACHING
# ==========================================
@st.cache_data(ttl=3600) # Cache for 1 hour to reduce BQ costs
def load_user_activity(start_date, end_date):
    query = f"""
    SELECT * 
    FROM `{PROJECT_ID}.{DATASET_ID}.vw_discovery_engine_user_activity`
    WHERE activity_date BETWEEN @start_date AND @end_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )
    return client.query(query, job_config=job_config).to_dataframe()

@st.cache_data(ttl=3600)
def load_session_activity(start_date, end_date):
    query = f"""
    SELECT * 
    FROM `{PROJECT_ID}.{DATASET_ID}.vw_discovery_engine_sessions`
    WHERE session_date BETWEEN @start_date AND @end_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )
    return client.query(query, job_config=job_config).to_dataframe()

@st.cache_data(ttl=3600)
def load_agent_activity(start_date, end_date):
    query = f"""
    SELECT * 
    FROM `{PROJECT_ID}.{DATASET_ID}.vw_discovery_engine_agent_activity`
    WHERE activity_date BETWEEN @start_date AND @end_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )
    df = client.query(query, job_config=job_config).to_dataframe()
    if not df.empty:
        df['agent_id'] = df['agent_id'].astype(str)
    return df

# ==========================================
# UI: SIDEBAR FILTERS
# ==========================================
st.sidebar.title("Filters")
today = datetime.date.today()
default_start = today - datetime.timedelta(days=30)

start_date = st.sidebar.date_input("Start Date", default_start)
end_date = st.sidebar.date_input("End Date", today)

# Load Data
df_users = load_user_activity(start_date, end_date)
df_sessions = load_session_activity(start_date, end_date)
df_agents = load_agent_activity(start_date, end_date)

# ==========================================
# UI: MAIN DASHBOARD LAYOUT
# ==========================================
st.title("Gemini for Government: Usage Analytics")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "User Activity & Retention", "Sessions", "Agent Activity"])

# --- TAB 1: OVERVIEW ---
with tab1:
    st.header("High-Level Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_users = df_users['principal'].nunique() if not df_users.empty else 0
    total_sessions = df_sessions['session_id'].nunique() if not df_sessions.empty else 0
    
    search_count = len(df_users[df_users['interaction_type'] == 'Search'])
    answer_count = df_users[df_users['interaction_type'] == 'Assistant']['operation_id'].nunique()
    
    col1.metric("Total Unique Users", f"{total_users:,}")
    col2.metric("Total Sessions", f"{total_sessions:,}")
    col3.metric("Search Count", f"{search_count:,}")
    col4.metric("Answer Count", f"{answer_count:,}")

    st.markdown("---")
    st.subheader("Interaction Breakdown (Search vs Answer)")
    if not df_users.empty:
        interaction_trend = df_users.groupby(['activity_date', 'interaction_type']).size().reset_index(name='count')
        fig = px.line(interaction_trend, x='activity_date', y='count', color='interaction_type', title="Daily Interactions")
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: USER ACTIVITY & RETENTION ---
with tab2:
    st.header("User Activity")
    col1, col2, col3 = st.columns(3)
    
    if not df_users.empty:
        # Calculate DAU, WAU, MAU averages for the period
        dau = df_users.groupby('activity_date')['principal'].nunique().mean()
        wau = df_users.groupby('activity_week')['principal'].nunique().mean()
        mau = df_users.groupby('activity_month')['principal'].nunique().mean()
        
        col1.metric("Avg Daily Active Users (DAU)", f"{dau:,.1f}")
        col2.metric("Avg Weekly Active Users (WAU)", f"{wau:,.1f}")
        col3.metric("Avg Monthly Active Users (MAU)", f"{mau:,.1f}")

        st.subheader("Daily Active Users Trend")
        dau_trend = df_users.groupby('activity_date')['principal'].nunique().reset_index(name='DAU')
        st.plotly_chart(px.bar(dau_trend, x='activity_date', y='DAU'), use_container_width=True)
        
        st.subheader("Growth & Retention (7d / 28d)")
        st.info("Retention and Churn metrics require historical comparative data (T-7 / T-28). In production, these should be materialized as daily snapshots in BigQuery rather than calculated on the fly in Pandas to ensure performance across millions of rows.")
    else:
        st.warning("No user data available for this date range.")

# --- TAB 3: SESSIONS ---
with tab3:
    st.header("Session Activity")
    
    if not df_sessions.empty:
        daily_sessions = df_sessions.groupby('session_date')['session_id'].nunique().mean()
        weekly_sessions = df_sessions.groupby('session_week')['session_id'].nunique().mean()
        
        col1, col2 = st.columns(2)
        col1.metric("Avg Daily Sessions", f"{daily_sessions:,.1f}")
        col2.metric("Avg Weekly Sessions", f"{weekly_sessions:,.1f}")
        
        st.subheader("Daily Sessions Trend")
        session_trend = df_sessions.groupby('session_date')['session_id'].nunique().reset_index(name='Sessions')
        st.plotly_chart(px.area(session_trend, x='session_date', y='Sessions'), use_container_width=True)
    else:
        st.warning("No session data available for this date range.")

# --- TAB 4: AGENT ACTIVITY ---
with tab4:
    st.header("Agent Usage Analytics")
    
    if not df_agents.empty:
        monthly_agents_used = df_agents['agent_id'].nunique()
        monthly_active_agent_users = df_agents['principal'].nunique()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Agents Used", f"{monthly_agents_used:,}")
        col2.metric("Active Agent Users", f"{monthly_active_agent_users:,}")
        
        st.subheader("Agent Popularity")
        agent_counts = df_agents.groupby('agent_id')['principal'].nunique().reset_index(name='Unique Users')
        agent_counts = agent_counts.sort_values(by='Unique Users', ascending=False)
        fig = px.bar(agent_counts, x='agent_id', y='Unique Users', title="Users per Agent")
        fig.update_layout(xaxis_type='category')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No agent data available for this date range.")