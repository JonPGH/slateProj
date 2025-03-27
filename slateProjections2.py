import streamlit as st
import pandas as pd
import os

# Set page configuration
st.set_page_config(page_title="Daily MLB Projections", layout="wide")

# Load data (assuming the data is in CSV format based on your provided structure)
@st.cache_data
def load_data():
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, 'Data')
    hitters_df = pd.read_csv(f'{file_path}/Tableau_DailyHitterProj.csv')
    pitchers_df = pd.read_csv(f'{file_path}/Tableau_DailyPitcherProj.csv')
    props_df = pd.read_csv(f'{file_path}/betValues.csv')

    return pitchers_df, hitters_df, props_df

pitchers_df, hitters_df, props_df = load_data()

def reload_data():
    st.cache_data.clear()  # Clear the cache
    return load_data()     # Reload the data

# Sidebar navigation
st.sidebar.title("MLB Projections")
tab = st.sidebar.radio("Select View", ["Pitchers", "Hitters", "Betting Props"])

# Function to filter dataframe by team and player
def filter_df(df, team_col, player_col, selected_team, selected_player):
    filtered_df = df.copy()
    if selected_team != "All Teams":
        filtered_df = filtered_df[filtered_df[team_col] == selected_team]
    if selected_player != "All Players":
        filtered_df = filtered_df[filtered_df[player_col] == selected_player]
    return filtered_df

# Main content based on selected tab
if tab == "Pitchers":
    st.title("Pitcher Projections - March 27, 2025")

    # Refresh button
    if st.button("Refresh Data", key="refresh_pitchers"):
        pitchers_df, hitters_df, props_df = reload_data()

    # Team and Player Filters
    teams = ["All Teams"] + sorted(pitchers_df["Team"].unique().tolist())
    selected_team = st.sidebar.selectbox("Select Team", teams, key="pitcher_team")
    players = ["All Players"] + sorted(pitchers_df["Pitcher"].unique().tolist())
    selected_player = st.sidebar.selectbox("Select Player", players, key="pitcher_player")

    # Filter data
    filtered_pitchers = filter_df(pitchers_df, "Team", "Pitcher", selected_team, selected_player)

    # Display data
    st.subheader("Quick View")
    st.dataframe(
        filtered_pitchers[[
            "Pitcher", "Team", "Opponent", "Sal", "DKPts", "Val"
        ]].style.format({
            "Sal": "${:,.0f}", 
             "DKPts": "{:.2f}", "Val": "{:.2f}"
        }),
        use_container_width=False, hide_index=True, width=550,height=400
    )

    # Display data
    st.subheader("Full Projections")
    st.dataframe(
        filtered_pitchers[[
            "Pitcher", "Team", "Opponent", "Sal", "IP", "H", "ER", "SO", "BB", "W", "DKPts"
        ]].style.format({
            "Sal": "${:,.0f}", "IP": "{:.2f}", "H": "{:.2f}", "ER": "{:.2f}", 
            "SO": "{:.2f}", "BB": "{:.2f}", "W": "{:.2f}", "DKPts": "{:.2f}"
        }),
        use_container_width=False, hide_index=True, width=1300, height=500
    )

elif tab == "Hitters":
    st.title("Hitter Projections - March 27, 2025")
    
    # Refresh button
    if st.button("Refresh Data", key="refresh_pitchers"):
        pitchers_df, hitters_df, props_df = reload_data()

    # Team and Player Filters
    teams = ["All Teams"] + sorted(hitters_df["Team"].unique().tolist())
    selected_team = st.sidebar.selectbox("Select Team", teams, key="hitter_team")
    players = ["All Players"] + sorted(hitters_df["Hitter"].unique().tolist())
    selected_player = st.sidebar.selectbox("Select Player", players, key="hitter_player")

    # Filter data
    filtered_hitters = filter_df(hitters_df, "Team", "Hitter", selected_team, selected_player)

    # Display data
    st.subheader("Projected Stats")
    st.dataframe(
        filtered_hitters[[
            "Hitter", "Pos", "Team", "Opp", "Sal", "PA", "R", "HR", "RBI", "SB", "SO", "BB", "DKPts", "TopPlayScore"
        ]].style.format({
            "Sal": "${:,.0f}", "PA": "{:.2f}", "R": "{:.2f}", "HR": "{:.2f}", 
            "RBI": "{:.2f}", "SB": "{:.2f}", "SO": "{:.2f}", "BB": "{:.2f}", 
            "DKPts": "{:.2f}", "TopPlayScore": "{:.2f}"
        }),
        use_container_width=False, hide_index=True, width=1300, height=900
    )

elif tab == "Betting Props":
    st.title("Betting Props - March 27, 2025")
    # Refresh button
    if st.button("Refresh Data", key="refresh_pitchers"):
        pitchers_df, hitters_df, props_df = reload_data()

    # Team Filter (based on pitchers or hitters involved)
    all_teams = ["All Teams"] + sorted(
        set(pitchers_df["Team"].tolist() + hitters_df["Team"].tolist())
    )
    selected_team = st.sidebar.selectbox("Select Team", all_teams, key="prop_team")
    players = ["All Players"] + sorted(props_df["Player"].unique().tolist())
    selected_player = st.sidebar.selectbox("Select Player", players, key="prop_player")

    # Filter data (no direct team column, so we'll approximate using player names)
    props_df = props_df[props_df['BetValue']>=.05]
    filtered_props = props_df.copy()
    if selected_team != "All Teams":
        # Cross-reference with pitchers and hitters to approximate team filtering
        team_players = pd.concat([
            pitchers_df[pitchers_df["Team"] == selected_team]["Pitcher"],
            hitters_df[hitters_df["Team"] == selected_team]["Hitter"]
        ]).unique()
        filtered_props = filtered_props[filtered_props["Player"].isin(team_players)]
    if selected_player != "All Players":
        filtered_props = filtered_props[filtered_props["Player"] == selected_player]

    # Display data
    st.subheader("Betting Props")
    st.dataframe(
        filtered_props[[
            "Player", "Book", "Type", "OU", "Line", "Price", "BetValue", "Recommended"
        ]].style.format({
            "Line": "{:.1f}", "Price": "{:+.0f}", "BetValue": "{:.3f}"
        }),
        use_container_width=False, hide_index=True, width=900, height=800
    )

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Data last updated: March 27, 2025 13:56")