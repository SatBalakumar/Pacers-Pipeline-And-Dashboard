"""
Pacers Analytics Dashboard

A Streamlit dashboard for exploring Indiana Pacers analytics data
from the Bronze→Silver→Gold ETL pipeline.
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Page configuration
st.set_page_config(
    page_title="Pacers Analytics Dashboard",
    page_icon="🏀",
    layout="wide"
)

# Database connection
@st.cache_resource
def get_database_connection():
    """Get SQLite database connection"""
    db_path = Path("/Users/sathyabalakumar/MyProjects/myPacersDashboard/db/pacers_analytics.db")
    if not db_path.exists():
        st.error(f"Database not found at {db_path}. Please run the ETL pipeline first.")
        return None
    return sqlite3.connect(str(db_path))

# Clear cache button for development
if st.sidebar.button("Clear Cache"):
    st.cache_resource.clear()
    st.cache_data.clear()
    st.rerun()

# Pacers color theme CSS
st.markdown("""
<style>
    /* Hide sidebar completely */
    .css-1d391kg, .css-1rs6os, .css-17eq0hr {
        display: none !important;
    }
    
    /* Hide sidebar toggle button */
    button[kind="header"] {
        display: none !important;
    }
    
    /* Hide sidebar expansion/collapse arrow completely */
    .css-1dp5vir, .css-18ni7ap, .css-vk3wp9, .css-1kyxreq {
        display: none !important;
    }
    
    /* Hide any remaining sidebar controls */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Hide the hamburger menu button */
    .css-14xtw13, .css-r698ls, .css-1y4p8pa {
        display: none !important;
    }
    
    /* Hide any sidebar toggle elements */
    button[title="Open sidebar"], button[title="Close sidebar"] {
        display: none !important;
    }
    
    /* Expand main content to full width */
    .css-18e3th9, .css-1d391kg {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: none !important;
    }
    
    /* Remove any sidebar spacing */
    .css-1lcbmhc, .css-1outpf7 {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }

    /* Pacers Color Variables */
    :root {
        --pacers-blue: rgb(0, 45, 98);
        --pacers-yellow: rgb(253, 187, 48);
        --pacers-silver: rgb(190, 192, 194);
        --pacers-white: rgb(255, 255, 255);
    }
    
    /* Main app background */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Sticky navigation container */
    .sticky-nav {
        position: sticky;
        top: 0;
        z-index: 999;
        background: linear-gradient(135deg, var(--pacers-yellow) 0%, rgb(255, 205, 80) 100%);
        padding: 1rem 2rem;
        margin: -1rem -2rem 2rem -2rem;
        box-shadow: 0 2px 8px rgba(0, 45, 98, 0.3);
        border-bottom: 3px solid var(--pacers-blue);
    }
    
    /* Title styling */
    .dashboard-title {
        color: var(--pacers-blue);
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.3);
    }
    
    /* Clear cache button styling */
    .clear-cache-btn {
        position: absolute;
        top: 1rem;
        left: 1rem;
        z-index: 1000;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        justify-content: center;
        margin-top: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: var(--pacers-white);
        color: var(--pacers-blue);
        border: 2px solid var(--pacers-silver);
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--pacers-yellow);
        color: var(--pacers-blue);
        border-color: var(--pacers-yellow);
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--pacers-yellow);
        color: var(--pacers-blue);
        border-color: var(--pacers-yellow);
        box-shadow: 0 4px 8px rgba(253, 187, 48, 0.3);
    }
    
    /* Content area styling */
    .tab-content {
        background-color: var(--pacers-white);
        border-radius: 15px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 4px 20px rgba(0, 45, 98, 0.1);
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, var(--pacers-white) 0%, rgb(248, 249, 250) 100%);
        border: 1px solid var(--pacers-silver);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 45, 98, 0.1);
    }
    
    /* Info box styling */
    .stInfo {
        background-color: rgba(253, 187, 48, 0.1);
        border-left: 4px solid var(--pacers-yellow);
    }
    
    /* DataFrame styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 45, 98, 0.1);
    }
    
    /* Subheader styling */
    .main h2, .main h3 {
        color: var(--pacers-blue);
        border-bottom: 2px solid var(--pacers-yellow);
        padding-bottom: 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--pacers-white) 0%, rgb(248, 249, 250) 100%);
        color: var(--pacers-blue);
        border: 2px solid var(--pacers-blue);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--pacers-yellow) 0%, rgb(255, 205, 80) 100%);
        color: var(--pacers-blue);
        border-color: var(--pacers-yellow);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(253, 187, 48, 0.3);
    }
</style>
""", unsafe_allow_html=True)

def highlight_stat_leaders(df):
    """Apply green highlighting to stat leaders in boxscore dataframe"""
    # Define columns that should be highlighted for maximum values
    max_stat_cols = ['Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', '+/-', 'Minutes']
    
    # Define columns that should be highlighted for minimum values (negative stats)
    min_stat_cols = ['Turnovers']
    
    # Convert percentage columns to numeric for comparison
    pct_cols = ['FG%', '3P%', 'FT%']
    
    def apply_highlighting(s):
        if s.name in max_stat_cols:
            # Highlight maximum values in green
            is_max = s == s.max()
            return ['background-color: #90EE90' if v else '' for v in is_max]
        elif s.name in min_stat_cols:
            # Highlight minimum values in green (best for turnovers)
            is_min = s == s.min()
            return ['background-color: #90EE90' if v else '' for v in is_min]
        elif s.name in pct_cols:
            # For percentage columns, convert to numeric and highlight max
            numeric_vals = pd.to_numeric(s.str.replace('%', '').str.replace('N/A', 'NaN'), errors='coerce')
            if not numeric_vals.isna().all():
                is_max = numeric_vals == numeric_vals.max()
                return ['background-color: #90EE90' if v else '' for v in is_max]
            else:
                return ['' for _ in s]
        else:
            return ['' for _ in s]
    
    return df.style.apply(apply_highlighting, axis=0)

@st.cache_data
def load_data(query: str, ttl: int = 3600):
    """Load data with caching"""
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def main():
    """Main dashboard application"""
    
    # Sticky navigation header with Pacers theme
    st.markdown("""
    <div class="sticky-nav">
        <div class="clear-cache-btn">
        </div>
        <h1 class="dashboard-title">Indiana Pacers Analytics Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Clear cache button in top left
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("Clear Cache", key="clear_cache_top"):
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()
    
    # Horizontal tab navigation with sticky positioning
    tab1, tab2, tab3, tab4 = st.tabs(["Home", "Game Summary", "Boxscore Browser", "Player Lookup"])
    
    with tab1:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        show_home_page()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        show_game_summary()
    
    with tab3:
        show_boxscore_browser()
    
    with tab4:
        show_player_lookup()

def show_home_page():
    """Display home page with overview"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Welcome to Pacers Analytics!")
        st.markdown("""
        This dashboard provides comprehensive analytics for the Indiana Pacers basketball team.
        
        **Available Features:**
        - **Game Summary**: View recent games, results, and opponent analysis
        - **Boxscore Browser**: Detailed player statistics for each game
        - **Player Lookup**: Search and analyze individual player performance
        """)
    
    with col2:
        # Quick stats
        st.subheader("Quick Stats")
        
        # Get basic counts
        games_count = load_data("SELECT COUNT(*) as count FROM gold_pacers_games")
        players_count = load_data("SELECT COUNT(*) as count FROM gold_pacers_players")
        
        if not games_count.empty:
            st.metric("Total Games", games_count.iloc[0]['count'])
        if not players_count.empty:
            st.metric("Active Players", players_count.iloc[0]['count'])
    
    # Recent games preview
    st.subheader("Recent Pacers Games")
    recent_games = load_data("""
        SELECT
            g.game_datetime_est as "Game Date",
            CASE WHEN home_team_abbreviation = 'IND' THEN away_team_abbreviation ELSE home_team_abbreviation END as opponent,
            CASE WHEN home_team_abbreviation = 'IND' THEN home_points ELSE away_points END as pacers_pts,
            CASE WHEN home_team_abbreviation = 'IND' THEN away_points ELSE home_points END as opponent_pts,
            CASE WHEN (CASE WHEN home_team_abbreviation = 'IND' THEN home_points ELSE away_points END) >
                      (CASE WHEN home_team_abbreviation = 'IND' THEN away_points ELSE home_points END)
                 THEN 'Win' ELSE 'Loss' END as result
        FROM gold_game_summary_with_status g
        WHERE home_team_abbreviation = 'IND' OR away_team_abbreviation = 'IND'
        ORDER BY g.game_datetime_est DESC
        LIMIT 5
    """)
    
    if not recent_games.empty:
        st.dataframe(recent_games, use_container_width=True)
    else:
        st.info("No game data available. Please ensure the ETL pipeline has been run.")

def show_game_summary():
    """Game Summary Viewer - Detailed individual game analysis"""
    
    st.header("Game Summary Viewer")
    
    # Game selection filters
    st.subheader("Select Game")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get available home teams
        home_teams = load_data("""
            SELECT DISTINCT home_team_abbreviation 
            FROM gold_game_summary_with_status 
            ORDER BY home_team_abbreviation
        """)
        if not home_teams.empty:
            home_team_options = ["Any"] + home_teams['home_team_abbreviation'].tolist()
            selected_home_team = st.selectbox("Home Team", home_team_options, index=1 if "IND" in home_team_options else 0)
        else:
            selected_home_team = "Any"
    
    with col2:
        # Get available away teams
        away_teams = load_data("""
            SELECT DISTINCT away_team_abbreviation 
            FROM gold_game_summary_with_status 
            ORDER BY away_team_abbreviation
        """)
        if not away_teams.empty:
            away_team_options = ["Any"] + away_teams['away_team_abbreviation'].tolist()
            selected_away_team = st.selectbox("Away Team", away_team_options, index=0)
        else:
            selected_away_team = "Any"
    
    with col3:
        # Get available dates
        dates = load_data("""
            SELECT DISTINCT DATE(game_datetime_est) as game_date
            FROM gold_game_summary_with_status 
            ORDER BY game_date DESC
        """)
        if not dates.empty:
            date_options = ["Any"] + dates['game_date'].tolist()
            selected_date = st.selectbox("Game Date", date_options, index=0)
        else:
            selected_date = "Any"
    
    # Build dynamic query based on filters
    where_conditions = ["1=1"]
    
    if selected_home_team != "Any":
        where_conditions.append(f"g.home_team_abbreviation = '{selected_home_team}'")
    
    if selected_away_team != "Any":
        where_conditions.append(f"g.away_team_abbreviation = '{selected_away_team}'")
    
    if selected_date != "Any":
        where_conditions.append(f"DATE(g.game_datetime_est) = '{selected_date}'")
    
    where_clause = " AND ".join(where_conditions)
    
    # Load filtered games
    games_query = f"""
        SELECT 
            g.game_id,
            g.game_datetime_est,
            g.home_team_abbreviation,
            g.away_team_abbreviation,
            g.home_points,
            g.away_points,
            g.status_name,
            g.home_team_abbreviation || ' vs ' || g.away_team_abbreviation || 
            ' (' || g.home_points || '-' || g.away_points || ') - ' || 
            DATE(g.game_datetime_est) as game_display
        FROM gold_game_summary_with_status g
        WHERE {where_clause}
        ORDER BY g.game_datetime_est DESC
        LIMIT 100
    """
    
    games_list = load_data(games_query)
    
    if games_list.empty:
        st.warning("No games found with the selected criteria. Try different filters.")
        return
    
    # Game selector
    selected_game_display = st.selectbox(
        f"Select from {len(games_list)} matching games:",
        options=games_list['game_display'].tolist(),
        help="Choose a game to view detailed summary"
    )
    
    if selected_game_display:
        # Get selected game data
        selected_game = games_list[games_list['game_display'] == selected_game_display].iloc[0]
        game_id = selected_game['game_id']
        
        # === GAME OVERVIEW SECTION ===
        st.markdown("---")
        st.subheader("Game Overview")
        
        # Score display with clean cards
        home_score = selected_game['home_points']
        away_score = selected_game['away_points']
        winner = "home" if home_score > away_score else "away"
        
        # Main scoreboard
        col1, col2, col3 = st.columns([3, 1, 3])
        
        with col1:
            # Home team card with Pacers theme
            home_border = "3px solid rgb(253, 187, 48)" if winner == "home" else "1px solid rgb(190, 192, 194)"
            home_bg = "linear-gradient(135deg, rgb(253, 187, 48) 0%, rgb(255, 205, 80) 100%)" if winner == "home" else "white"
            st.markdown(f"""
            <div style="
                background: {home_bg};
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border: {home_border};
                box-shadow: 0 4px 12px rgba(0, 45, 98, 0.2);
            ">
                <h3 style="margin: 0; color: rgb(0, 45, 98); font-weight: 600;">{selected_game['home_team_abbreviation']}</h3>
                <h1 style="margin: 10px 0; color: rgb(0, 45, 98); font-weight: 700; font-size: 2.5rem;">{home_score}</h1>
                <p style="margin: 0; color: rgb(0, 45, 98); font-size: 0.9rem; font-weight: 500;">HOME</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # VS separator with Pacers theme
            st.markdown("""
            <div style="text-align: center; padding: 45px 0;">
                <h3 style="color: rgb(190, 192, 194); margin: 0; font-weight: 400; font-size: 1.5rem;">vs</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Away team card with Pacers theme
            away_border = "3px solid rgb(253, 187, 48)" if winner == "away" else "1px solid rgb(190, 192, 194)"
            away_bg = "linear-gradient(135deg, rgb(253, 187, 48) 0%, rgb(255, 205, 80) 100%)" if winner == "away" else "white"
            st.markdown(f"""
            <div style="
                background: {away_bg};
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border: {away_border};
                box-shadow: 0 4px 12px rgba(0, 45, 98, 0.2);
            ">
                <h3 style="margin: 0; color: rgb(0, 45, 98); font-weight: 600;">{selected_game['away_team_abbreviation']}</h3>
                <h1 style="margin: 10px 0; color: rgb(0, 45, 98); font-weight: 700; font-size: 2.5rem;">{away_score}</h1>
                <p style="margin: 0; color: rgb(0, 45, 98); font-size: 0.9rem; font-weight: 500;">AWAY</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Game result and details with Pacers theme
        margin = abs(home_score - away_score)
        winner_team = selected_game['home_team_abbreviation'] if winner == "home" else selected_game['away_team_abbreviation']
        winner_location = "HOME" if winner == "home" else "AWAY"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgb(255, 255, 255) 0%, rgb(248, 249, 250) 100%);
            color: rgb(0, 45, 98);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
            border: 2px solid rgb(253, 187, 48);
            box-shadow: 0 4px 12px rgba(0, 45, 98, 0.2);
        ">
            <h3 style="margin: 0; color: rgb(0, 45, 98); font-size: 1.25rem;">
                <strong>{winner_team}</strong> wins by {margin} points ({winner_location})
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Game details metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Date", selected_game['game_datetime_est'].split()[0])
        
        with col2:
            st.metric("Status", selected_game['status_name'])
        
        with col3:
            st.metric("Margin of Victory", f"{margin} pts")
        
        with col4:
            total_points = home_score + away_score
            st.metric("Total Points", f"{total_points}")
        
        # === BOX SCORE SECTION ===
        st.markdown("---")
        st.subheader("Box Score")
        
        # Load player stats for this game - both teams
        boxscore_query = """
            SELECT 
                pi.full_name as "Player",
                ti.team_abbreviation as "Team",
                pb.starter_flag as "Starter",
                pb.minutes as "Minutes", 
                pb.pts as "PTS",
                pb.fgm || '/' || pb.fga as "FG",
                ROUND(pb.fg_pct * 100, 1) as "FG%",
                pb.fg3m || '/' || pb.fg3a as "3P",
                ROUND(pb.fg3_pct * 100, 1) as "3P%",
                pb.ftm || '/' || pb.fta as "FT",
                ROUND(pb.ft_pct * 100, 1) as "FT%",
                pb.reb as "REB",
                pb.ast as "AST",
                pb.stl as "STL",
                pb.blk as "BLK",
                pb.tov as "TO",
                pb.pf as "PF",
                pb.plusminus as "+/-"
            FROM gold_player_boxscore pb
            JOIN gold_player_info pi ON pb.player_id = pi.player_id
            JOIN teams_silver ti ON pb.team_id = ti.team_id
            WHERE pb.game_id = ?
            ORDER BY ti.team_abbreviation, pb.starter_flag DESC, pb.minutes DESC
        """
        
        conn = get_database_connection()
        if conn is None:
            st.error("Cannot connect to database. Please ensure the ETL pipeline has been run.")
            return
        
        try:
            boxscore_df = pd.read_sql_query(boxscore_query, conn, params=[game_id])
        except Exception as e:
            st.error(f"Error loading boxscore data: {e}")
            return
        
        if not boxscore_df.empty:
            # Show each team's stats separately
            home_team = selected_game['home_team_abbreviation']
            away_team = selected_game['away_team_abbreviation']
            
            # Home team stats
            home_df = boxscore_df[boxscore_df['Team'] == home_team].copy()
            if not home_df.empty:
                st.markdown(f"**{home_team} ({selected_game['home_points']} pts)**")
                home_df['Starter'] = home_df['Starter'].map({1: '⭐', 0: ''})
                home_display = home_df.drop(['Team', 'Starter'], axis=1)
                st.dataframe(home_display, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Away team stats  
            away_df = boxscore_df[boxscore_df['Team'] == away_team].copy()
            if not away_df.empty:
                st.markdown(f"**{away_team} ({selected_game['away_points']} pts)**")
                away_df['Starter'] = away_df['Starter'].map({1: '⭐', 0: ''})
                away_display = away_df.drop(['Team', 'Starter'], axis=1)
                st.dataframe(away_display, use_container_width=True, hide_index=True)
            
        else:
            st.info("No boxscore data available for this game.")
        
        # === PLAY-BY-PLAY SECTION ===
        st.markdown("---")
        st.subheader("Play-by-Play Recap")
        
        # Load play-by-play data
        pbp_query = """
            SELECT 
                p.period,
                p.pc_time,
                p.home_description,
                p.visitor_description,
                p.neutral_description,
                p.home_score,
                p.away_score,
                p.event_msg_type,
                CASE 
                    WHEN p.home_description IS NOT NULL THEN p.home_description
                    WHEN p.visitor_description IS NOT NULL THEN p.visitor_description 
                    ELSE p.neutral_description
                END as description
            FROM pbp_silver p
            WHERE p.game_id = ?
            ORDER BY p.period ASC, p.pc_time DESC
            LIMIT 100
        """
        
        conn = get_database_connection()
        if conn is None:
            st.error("Cannot connect to database. Please ensure the ETL pipeline has been run.")
            return
        
        try:
            pbp_df = pd.read_sql_query(pbp_query, conn, params=[game_id])
        except Exception as e:
            st.error(f"Error loading play-by-play data: {e}")
            return
        
        if not pbp_df.empty:
            # Filter controls
            col1, col2 = st.columns(2)
            with col1:
                periods = ["All"] + [f"Q{i}" for i in sorted(pbp_df['period'].unique())]
                selected_period = st.selectbox("Period", periods)
            with col2:
                show_scoring_only = st.checkbox("Show scoring plays only", value=True)
            
            # Filter the data
            filtered_pbp = pbp_df.copy()
            
            if selected_period != "All":
                period_num = int(selected_period[1:])
                filtered_pbp = filtered_pbp[filtered_pbp['period'] == period_num]
            
            if show_scoring_only:
                # Show plays where score changes (assuming event_msg_type 1 = made shot)
                filtered_pbp = filtered_pbp[
                    (filtered_pbp['home_score'].notna()) & 
                    (filtered_pbp['away_score'].notna()) &
                    (filtered_pbp['description'].str.contains('makes|MISS', case=False, na=False))
                ]
            
            # Display play-by-play
            if not filtered_pbp.empty:
                for _, play in filtered_pbp.head(20).iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([1, 6, 1])
                        with col1:
                            st.write(f"Q{play['period']} {play['pc_time']}")
                        with col2:
                            if pd.notna(play['description']):
                                st.write(play['description'])
                        with col3:
                            if pd.notna(play['home_score']) and pd.notna(play['away_score']):
                                st.write(f"{int(play['home_score'])}-{int(play['away_score'])}")
                        st.markdown("---")
            else:
                st.info("No play-by-play data matches the selected filters.")
        else:
            st.info("No play-by-play data available for this game.")

def show_boxscore_browser():
    """Boxscore Browser - Interactive boxscore viewer with flexible filtering"""
    
    st.header("Boxscore Browser")
    
    # Game selection filters (similar to Game Summary)
    st.subheader("🔍 Filter Games")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get available home teams
        home_teams = load_data("""
            SELECT DISTINCT home_team_abbreviation 
            FROM gold_game_summary_with_status 
            ORDER BY home_team_abbreviation
        """)
        if not home_teams.empty:
            home_team_options = ["Any"] + home_teams['home_team_abbreviation'].tolist()
            selected_home_team = st.selectbox("Home Team", home_team_options, key="bb_home")
        else:
            selected_home_team = "Any"
    
    with col2:
        # Get available away teams
        away_teams = load_data("""
            SELECT DISTINCT away_team_abbreviation 
            FROM gold_game_summary_with_status 
            ORDER BY away_team_abbreviation
        """)
        if not away_teams.empty:
            away_team_options = ["Any"] + away_teams['away_team_abbreviation'].tolist()
            selected_away_team = st.selectbox("Away Team", away_team_options, key="bb_away")
        else:
            selected_away_team = "Any"
    
    with col3:
        # Get available dates
        dates = load_data("""
            SELECT DISTINCT DATE(game_datetime_est) as game_date
            FROM gold_game_summary_with_status 
            ORDER BY game_date DESC
        """)
        if not dates.empty:
            date_options = ["Any"] + dates['game_date'].tolist()
            selected_date = st.selectbox("Game Date", date_options, key="bb_date")
        else:
            selected_date = "Any"
    
    # Build dynamic query based on filters
    where_conditions = ["1=1"]
    
    if selected_home_team != "Any":
        where_conditions.append(f"g.home_team_abbreviation = '{selected_home_team}'")
    
    if selected_away_team != "Any":
        where_conditions.append(f"g.away_team_abbreviation = '{selected_away_team}'")
    
    if selected_date != "Any":
        where_conditions.append(f"DATE(g.game_datetime_est) = '{selected_date}'")
    
    where_clause = " AND ".join(where_conditions)
    
    # Load filtered games
    games_query = f"""
        SELECT 
            g.game_id,
            g.game_datetime_est,
            g.home_team_abbreviation,
            g.away_team_abbreviation,
            g.home_points,
            g.away_points,
            g.status_name,
            g.home_team_abbreviation || ' vs ' || g.away_team_abbreviation || 
            ' (' || g.home_points || '-' || g.away_points || ') - ' || 
            DATE(g.game_datetime_est) as game_display
        FROM gold_game_summary_with_status g
        WHERE {where_clause}
        ORDER BY g.game_datetime_est DESC
        LIMIT 100
    """
    
    games_list = load_data(games_query)
    
    if games_list.empty:
        st.warning("No games found with the selected criteria. Try different filters.")
        return
    
    # Game selector
    selected_game_display = st.selectbox(
        f"Select from {len(games_list)} matching games:",
        options=games_list['game_display'].tolist(),
        help="Choose a game to view detailed boxscore"
    )
    
    if selected_game_display:
        # Get selected game data
        selected_game = games_list[games_list['game_display'] == selected_game_display].iloc[0]
        game_id = selected_game['game_id']
        
        st.markdown("---")
        
        # UI controls
        col1, col2 = st.columns(2)
        with col1:
            team_filter = st.selectbox(
                "Show team:",
                ["Both Teams", selected_game['home_team_abbreviation'], selected_game['away_team_abbreviation']],
                help="Filter to show specific team or both teams"
            )
        with col2:
            starters_only = st.checkbox("Show starters only", value=False)
        
        # Load boxscore data for selected game
        boxscore_query = """
            SELECT 
                pi.full_name as "Player",
                ti.team_abbreviation as "Team",
                pb.starter_flag,
                pb.minutes as "Minutes",
                pb.pts as "Points",
                pb.reb as "Rebounds",
                pb.ast as "Assists",
                pb.stl as "Steals",
                pb.blk as "Blocks",
                pb.tov as "Turnovers",
                pb.fgm || '/' || pb.fga as "FG",
                ROUND(pb.fg_pct * 100, 1) as "FG%",
                pb.fg3m || '/' || pb.fg3a as "3P",
                ROUND(pb.fg3_pct * 100, 1) as "3P%",
                pb.ftm || '/' || pb.fta as "FT", 
                ROUND(pb.ft_pct * 100, 1) as "FT%",
                pb.plusminus as "+/-"
            FROM gold_player_boxscore pb
            JOIN gold_player_info pi ON pb.player_id = pi.player_id
            JOIN teams_silver ti ON pb.team_id = ti.team_id
            WHERE pb.game_id = ?
            ORDER BY ti.team_abbreviation, pb.starter_flag DESC, pb.minutes DESC
        """
        
        conn = get_database_connection()
        if conn is None:
            st.error("Cannot connect to database. Please ensure the ETL pipeline has been run.")
            return
        
        try:
            boxscore_df = pd.read_sql_query(boxscore_query, conn, params=[game_id])
        except Exception as e:
            st.error(f"Error loading boxscore data: {e}")
            return
        
        if not boxscore_df.empty:
            # Apply filters
            filtered_df = boxscore_df.copy()
            
            # Filter by team if selected
            if team_filter != "Both Teams":
                filtered_df = filtered_df[filtered_df['Team'] == team_filter]
            
            # Filter by starters if selected
            if starters_only:
                filtered_df = filtered_df[filtered_df['starter_flag'] == 1]
            
            # Format the data for display
            if 'Minutes' in filtered_df.columns:
                filtered_df['Minutes'] = filtered_df['Minutes'].round(1)
            
            # Format percentage columns
            for pct_col in ['FG%', '3P%', 'FT%']:
                if pct_col in filtered_df.columns:
                    filtered_df[pct_col] = filtered_df[pct_col].apply(lambda v: f"{v:.1f}%" if pd.notna(v) else "N/A")
            
            # Game summary header
            st.subheader(f"Game: {selected_game_display}")
            st.info("**Stat Leaders**: Green highlighting indicates the best performance in each statistical category for this game")
            
            if team_filter == "Both Teams":
                # Show both teams separately
                home_team = selected_game['home_team_abbreviation']
                away_team = selected_game['away_team_abbreviation']
                
                # Home team
                home_df = filtered_df[filtered_df['Team'] == home_team].copy()
                if not home_df.empty:
                    st.markdown(f"### {home_team} ({selected_game['home_points']} pts)")
                    display_home = home_df.drop(['Team', 'starter_flag'], axis=1)
                    styled_home = highlight_stat_leaders(display_home)
                    st.dataframe(styled_home, use_container_width=True, hide_index=True)
                    
                    # Team totals for home
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Points", int(home_df['Points'].sum()))
                    col2.metric("Rebounds", int(home_df['Rebounds'].sum()))
                    col3.metric("Assists", int(home_df['Assists'].sum()))
                    col4.metric("Turnovers", int(home_df['Turnovers'].sum()))
                
                st.markdown("---")
                
                # Away team
                away_df = filtered_df[filtered_df['Team'] == away_team].copy()
                if not away_df.empty:
                    st.markdown(f"### {away_team} ({selected_game['away_points']} pts)")
                    display_away = away_df.drop(['Team', 'starter_flag'], axis=1)
                    styled_away = highlight_stat_leaders(display_away)
                    st.dataframe(styled_away, use_container_width=True, hide_index=True)
                    
                    # Team totals for away
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Points", int(away_df['Points'].sum()))
                    col2.metric("Rebounds", int(away_df['Rebounds'].sum()))
                    col3.metric("Assists", int(away_df['Assists'].sum()))
                    col4.metric("Turnovers", int(away_df['Turnovers'].sum()))
            
            else:
                # Show single team
                if not filtered_df.empty:
                    team_score = selected_game['home_points'] if team_filter == selected_game['home_team_abbreviation'] else selected_game['away_points']
                    venue = "HOME" if team_filter == selected_game['home_team_abbreviation'] else "AWAY"
                    
                    st.markdown(f"### {venue} {team_filter} ({team_score} pts)")
                    display_df = filtered_df.drop(['Team', 'starter_flag'], axis=1)
                    styled_df = highlight_stat_leaders(display_df)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    # Team totals
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Points", int(filtered_df['Points'].sum()))
                    col2.metric("Rebounds", int(filtered_df['Rebounds'].sum()))
                    col3.metric("Assists", int(filtered_df['Assists'].sum()))
                    col4.metric("Turnovers", int(filtered_df['Turnovers'].sum()))
            
            # Download option
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "Download CSV", 
                csv, 
                file_name=f"boxscore_{selected_game['game_datetime_est'].split()[0]}_{team_filter.replace(' ', '_')}.csv", 
                mime='text/csv'
            )
            
            # Team Statistical Comparison (if showing both teams)
            if team_filter == "Both Teams" and len(filtered_df) > 0:
                st.subheader("Team Statistical Comparison")
                
                # Calculate team totals
                home_team = selected_game['home_team_abbreviation']
                away_team = selected_game['away_team_abbreviation']
                
                home_stats = filtered_df[filtered_df['Team'] == home_team]
                away_stats = filtered_df[filtered_df['Team'] == away_team]
                
                if not home_stats.empty and not away_stats.empty:
                    # Calculate team totals for key stats
                    stats_comparison = {
                        'Statistic': ['Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'Turnovers', 'Minutes'],
                        home_team: [
                            int(home_stats['Points'].sum()),
                            int(home_stats['Rebounds'].sum()),
                            int(home_stats['Assists'].sum()),
                            int(home_stats['Steals'].sum()),
                            int(home_stats['Blocks'].sum()),
                            int(home_stats['Turnovers'].sum()),
                            round(home_stats['Minutes'].sum(), 1)
                        ],
                        away_team: [
                            int(away_stats['Points'].sum()),
                            int(away_stats['Rebounds'].sum()),
                            int(away_stats['Assists'].sum()),
                            int(away_stats['Steals'].sum()),
                            int(away_stats['Blocks'].sum()),
                            int(away_stats['Turnovers'].sum()),
                            round(away_stats['Minutes'].sum(), 1)
                        ]
                    }
                    
                    comparison_df = pd.DataFrame(stats_comparison)
                    
                    # Add difference and leader columns
                    comparison_df['Difference'] = comparison_df[home_team] - comparison_df[away_team]
                    comparison_df['Leader'] = comparison_df.apply(
                        lambda row: home_team if (row['Difference'] > 0 and row['Statistic'] != 'Turnovers') or (row['Difference'] < 0 and row['Statistic'] == 'Turnovers')
                                   else away_team if (row['Difference'] < 0 and row['Statistic'] != 'Turnovers') or (row['Difference'] > 0 and row['Statistic'] == 'Turnovers')
                                   else 'Tie', axis=1
                    )
                    
                    # Style the comparison table
                    def highlight_leader(row):
                        if row['Leader'] == home_team:
                            return ['', 'background-color: #90EE90', '', '', 'font-weight: bold']
                        elif row['Leader'] == away_team:
                            return ['', '', 'background-color: #90EE90', '', 'font-weight: bold']
                        else:
                            return ['', '', '', '', '']
                    
                    styled_comparison = comparison_df.style.apply(highlight_leader, axis=1)
                    st.dataframe(styled_comparison, use_container_width=True, hide_index=True)
                    
                    # Key insights
                    st.markdown("### Key Statistical Insights")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        winner_team = home_team if selected_game['home_points'] > selected_game['away_points'] else away_team
                        st.info(f"**Game Winner**: {winner_team}")
                        
                        # Points leader
                        points_leader = comparison_df[comparison_df['Statistic'] == 'Points']['Leader'].iloc[0]
                        if points_leader != 'Tie':
                            st.success(f"**Scoring Leader**: {points_leader}")
                        
                    with col2:
                        # Rebounds leader
                        reb_leader = comparison_df[comparison_df['Statistic'] == 'Rebounds']['Leader'].iloc[0]
                        if reb_leader != 'Tie':
                            st.success(f"**Rebounding Leader**: {reb_leader}")
                        
                        # Assists leader
                        ast_leader = comparison_df[comparison_df['Statistic'] == 'Assists']['Leader'].iloc[0]
                        if ast_leader != 'Tie':
                            st.success(f"**Playmaking Leader**: {ast_leader}")
                else:
                    st.info("Team comparison requires data from both teams")
        
        else:
            st.warning(f"No boxscore data found for {selected_game_display}")

def show_player_lookup():
    """Player Lookup Tool - Comprehensive player analysis"""
    
    st.header("Player Lookup Tool")
    
    # Load players list
    players_list = load_data("""
        SELECT DISTINCT pi.full_name, pi.player_id
        FROM gold_player_info pi 
        ORDER BY pi.full_name
    """)
    
    if players_list.empty:
        st.warning("No players available. Please run the ETL pipeline first.")
        return
    
    # Player selection
    selected_player = st.selectbox(
        "Select a player:",
        options=players_list['full_name'].tolist(),
        help="Choose a Pacers player to view detailed profile"
    )
    
    if selected_player:
        # Get player_id for queries
        player_id = players_list[players_list['full_name'] == selected_player]['player_id'].iloc[0]
        
        # === PLAYER INFORMATION SECTION ===
        st.markdown("---")
        st.subheader("Player Information")
        
        # Load comprehensive player info
        player_info = load_data(f"""
            SELECT 
                pi.full_name as "Name",
                pi.first_name,
                pi.last_name,
                pi.position_code as "Position",
                pi.height_inches as "Height",
                pi.weight as "Weight",
                pi.jersey_num as "Jersey",
                pi.draft_year as "Draft Year",
                pi.draft_round as "Draft Round",
                pi.draft_number as "Draft Pick",
                pi.country_name as "Country",
                pi.team_abbreviation_team as "Team"
            FROM gold_player_info pi 
            WHERE pi.full_name = '{selected_player}'
        """)
        
        if not player_info.empty:
            # Player name and position header
            st.markdown(f"### {player_info.iloc[0]['Name']}")
            
            # Jersey and position info
            jersey = f"#{int(player_info.iloc[0]['Jersey'])}" if pd.notna(player_info.iloc[0]['Jersey']) else ""
            position = player_info.iloc[0]['Position']
            jersey_pos = f"{jersey} • {position}" if jersey else position
            st.markdown(f"**{jersey_pos}**")
            
            st.markdown("")  # Add space
            
            # Basic info in clean columns
            col1, col2, col3, col4 = st.columns(4)
            
            # Height conversion
            height_inches = player_info.iloc[0]['Height']
            height_feet = height_inches // 12
            height_remaining_inches = height_inches % 12
            height_display = f"{height_feet}'{height_remaining_inches}\""
            
            with col1:
                st.metric("Height", height_display)
            
            with col2:
                st.metric("Weight", f"{player_info.iloc[0]['Weight']} lbs")
            
            with col3:
                st.metric("Country", player_info.iloc[0]['Country'])
            
            with col4:
                st.metric("Team", player_info.iloc[0]['Team'])
            
            st.markdown("")  # Add space
            
            # Draft information (if available)
            if pd.notna(player_info.iloc[0]['Draft Year']):
                draft_year = int(player_info.iloc[0]['Draft Year'])
                draft_round = int(player_info.iloc[0]['Draft Round'])
                draft_pick = int(player_info.iloc[0]['Draft Pick'])
                draft_text = f"{draft_year} Draft • Round {draft_round} • Pick #{draft_pick}"
                st.markdown(f"**Draft:** {draft_text}")
            else:
                st.markdown("**Draft:** Undrafted")
        
        # === RECENT GAME STATS SECTION ===
        st.markdown("---")
        st.subheader("Recent Game Stats (Last 10 Games)")
        
        # Load recent games stats
        recent_stats_query = """
            SELECT 
                g.game_datetime_est as "Date",
                CASE 
                    WHEN g.home_team_abbreviation = 'IND' THEN 'vs ' || g.away_team_abbreviation 
                    ELSE '@ ' || g.home_team_abbreviation 
                END as "Opponent",
                CASE 
                    WHEN (g.home_team_abbreviation = 'IND' AND g.home_points > g.away_points) OR
                         (g.away_team_abbreviation = 'IND' AND g.away_points > g.home_points)
                    THEN 'W' ELSE 'L' 
                END as "Result",
                pb.minutes as "MIN",
                pb.pts as "PTS",
                pb.fgm || '/' || pb.fga as "FG",
                ROUND(pb.fg_pct * 100, 1) as "FG%",
                pb.fg3m || '/' || pb.fg3a as "3P",
                ROUND(pb.fg3_pct * 100, 1) as "3P%",
                pb.reb as "REB",
                pb.ast as "AST",
                pb.stl as "STL",
                pb.blk as "BLK",
                pb.tov as "TO",
                pb.plusminus as "+/-"
            FROM gold_player_boxscore pb
            JOIN gold_game_summary_with_status g ON pb.game_id = g.game_id
            WHERE pb.player_id = ? 
            AND pb.team_id = 1610612754
            AND pb.played_flag = 1
            ORDER BY g.game_datetime_est DESC
            LIMIT 10
        """
        
        conn = get_database_connection()
        if conn is None:
            st.error("Cannot connect to database. Please ensure the ETL pipeline has been run.")
            return
        
        try:
            recent_stats_df = pd.read_sql_query(recent_stats_query, conn, params=[player_id])
        except Exception as e:
            st.error(f"Error loading recent stats data: {e}")
            return
        
        if not recent_stats_df.empty:
            # Format the dates for display
            recent_stats_df['Date'] = pd.to_datetime(recent_stats_df['Date']).dt.strftime('%m/%d')
            
            # Display recent games
            st.dataframe(recent_stats_df, use_container_width=True, hide_index=True)
            
            # Recent performance summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_pts = recent_stats_df['PTS'].mean()
                st.metric("Avg PTS (L10)", f"{avg_pts:.1f}")
            with col2:
                avg_reb = recent_stats_df['REB'].mean()
                st.metric("Avg REB (L10)", f"{avg_reb:.1f}")
            with col3:
                avg_ast = recent_stats_df['AST'].mean()
                st.metric("Avg AST (L10)", f"{avg_ast:.1f}")
            with col4:
                games_played = len(recent_stats_df)
                st.metric("Games Played", games_played)
        else:
            st.info("No recent game stats available for this player.")
        
        # === RECENT ACTIONS SECTION ===
        st.markdown("---")
        st.subheader("Recent Actions in Games")
        
        # Load recent play-by-play actions
        recent_actions_query = """
            SELECT 
                g.game_datetime_est,
                g.home_team_abbreviation || ' vs ' || g.away_team_abbreviation as matchup,
                p.period,
                p.pc_time,
                CASE 
                    WHEN p.home_description IS NOT NULL AND p.home_description LIKE ? THEN p.home_description
                    WHEN p.visitor_description IS NOT NULL AND p.visitor_description LIKE ? THEN p.visitor_description
                    WHEN p.neutral_description IS NOT NULL AND p.neutral_description LIKE ? THEN p.neutral_description
                    ELSE NULL
                END as action_description,
                p.home_score,
                p.away_score
            FROM pbp_silver p
            JOIN gold_game_summary_with_status g ON p.game_id = g.game_id
            WHERE (p.player1_id = ? OR p.player2_id = ? OR p.player3_id = ?)
            AND (p.home_description LIKE ? OR 
                 p.visitor_description LIKE ? OR 
                 p.neutral_description LIKE ?)
            ORDER BY g.game_datetime_est DESC, p.period ASC, p.pc_time DESC
            LIMIT 30
        """
        
        # Parameters: player name (3x for CASE), player_id (3x for WHERE), player name (3x for LIKE)
        player_name_pattern = f'%{selected_player}%'
        params = [
            player_name_pattern, player_name_pattern, player_name_pattern,  # CASE statements
            player_id, player_id, player_id,  # player_id WHERE conditions
            player_name_pattern, player_name_pattern, player_name_pattern   # description LIKE conditions
        ]
        
        conn = get_database_connection()
        if conn is None:
            st.error("Cannot connect to database. Please ensure the ETL pipeline has been run.")
            return
        
        try:
            recent_actions_df = pd.read_sql_query(recent_actions_query, conn, params=params)
        except Exception as e:
            st.error(f"Error loading recent actions data: {e}")
            return
        
        if not recent_actions_df.empty:
            # Action type filter
            col1, col2 = st.columns(2)
            with col1:
                action_filter = st.selectbox(
                    "Filter by action type:",
                    ["All Actions", "Scoring", "Assists", "Rebounds", "Steals", "Blocks"]
                )
            with col2:
                show_score = st.checkbox("Show game score", value=True)
            
            # Filter actions based on selection
            filtered_actions = recent_actions_df.copy()
            if action_filter != "All Actions":
                if action_filter == "Scoring":
                    filtered_actions = filtered_actions[filtered_actions['action_description'].str.contains('makes|MISS', case=False, na=False)]
                elif action_filter == "Assists":
                    filtered_actions = filtered_actions[filtered_actions['action_description'].str.contains('assist', case=False, na=False)]
                elif action_filter == "Rebounds":
                    filtered_actions = filtered_actions[filtered_actions['action_description'].str.contains('rebound', case=False, na=False)]
                elif action_filter == "Steals":
                    filtered_actions = filtered_actions[filtered_actions['action_description'].str.contains('steal', case=False, na=False)]
                elif action_filter == "Blocks":
                    filtered_actions = filtered_actions[filtered_actions['action_description'].str.contains('block', case=False, na=False)]
            
            # Display recent actions
            if not filtered_actions.empty:
                for _, action in filtered_actions.head(15).iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([2, 6, 1])
                        
                        with col1:
                            game_date = pd.to_datetime(action['game_datetime_est']).strftime('%m/%d')
                            st.write(f"**{game_date}** {action['opponent']}")
                            st.write(f"Q{action['period']} {action['pc_time']}")
                        
                        with col2:
                            if pd.notna(action['action_description']):
                                # Highlight the player's name in the description
                                description = action['action_description']
                                highlighted = description.replace(selected_player, f"**{selected_player}**")
                                st.write(highlighted)
                        
                        with col3:
                            if show_score and pd.notna(action['home_score']) and pd.notna(action['away_score']):
                                st.write(f"{int(action['home_score'])}-{int(action['away_score'])}")
                        
                        st.markdown("---")
            else:
                st.info(f"No {action_filter.lower()} actions found for {selected_player} in recent games.")
        else:
            st.info("No recent play-by-play actions available for this player.")
        
        # Season averages (condensed)
        season_avg = load_data(f"""
            SELECT 
                gp as "GP", mpg as "MPG", ppg as "PPG", rpg as "RPG", apg as "APG",
                spg as "SPG", bpg as "BPG", tpg as "TPG", fg_pct as "FG%", 
                three_pct as "3P%", ft_pct as "FT%"
            FROM gold_pacers_season_averages 
            WHERE full_name = '{selected_player}'
        """)
        
        if not season_avg.empty:
            st.markdown("---")
            st.subheader("📈 Season Averages")
            
            # Key stats in columns
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("PPG", f"{season_avg.iloc[0]['PPG']:.1f}")
            with col2:
                st.metric("RPG", f"{season_avg.iloc[0]['RPG']:.1f}")
            with col3:
                st.metric("APG", f"{season_avg.iloc[0]['APG']:.1f}")
            with col4:
                st.metric("MPG", f"{season_avg.iloc[0]['MPG']:.1f}")
            with col5:
                st.metric("FG%", f"{season_avg.iloc[0]['FG%']:.1%}" if pd.notna(season_avg.iloc[0]['FG%']) else "N/A")
            
            # Full stats expandable
            with st.expander("View All Season Stats"):
                st.dataframe(season_avg, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()