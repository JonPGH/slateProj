import streamlit as st
import pandas as pd
import os
import requests
import numpy as np
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(page_title="MLB DW Slate Analysis Tool", layout="wide")

# Custom CSS for styling
st.markdown(
    """
    <style>
    /* Base styling */
    .stApp {
        background-color: #F5F6F5; /* Light gray background for a clean look */
        font-family: 'Roboto', sans-serif; /* Modern font */
    }
    h1, h2, h3, h4 {
        color: #003087; /* Navy blue for headers, MLB-inspired */
        font-weight: 700;
    }
    .sidebar .sidebar-content {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    /* Card styling for player profiles */
    .player-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    /* Table styling */
    .dataframe {
        border-collapse: collapse;
        width: 100%;
    }
    .dataframe th, .dataframe td {
        padding: 10px;
        text-align: left;
        border-bottom: 1px solid #E0E0E0;
    }
    .dataframe tr:nth-child(even) {
        background-color: #F9F9F9; /* Alternating row colors */
    }
    /* Button and selectbox styling */
    .stSelectbox, .stRadio > div {
        background-color: #FFFFFF;
        border-radius: 5px;
        padding: 5px;
        border: 1px solid #E0E0E0;
    }
    /* Responsive design */
    @media (max-width: 768px) {
        .player-card {
            padding: 10px;
        }
        h1 {
            font-size: 24px;
        }
        h2 {
            font-size: 20px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load data (unchanged)
@st.cache_data
def load_data():
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, 'Data')
    hitterproj = pd.read_csv(f'{file_path}/hitter_proj_withids.csv')
    pitcherproj = pd.read_csv(f'{file_path}/Tableau_DailyPitcherProj.csv')
    propsdf = pd.read_csv(f'{file_path}/betValues.csv')
    hitter_stats = pd.read_csv(f'{file_path}/hitterData.csv')
    hitter_stats = hitter_stats.drop_duplicates(subset=['ID'])
    lineup_stats = pd.read_csv(f'{file_path}/lineupData.csv')
    pitcher_stats = pd.read_csv(f'{file_path}/pitcherStats.csv')
    umpire_data = pd.read_csv(f'{file_path}/umpData.csv')
    weather_data = pd.read_csv(f'{file_path}/weatherReport.csv')
    h_vs_avg = pd.read_csv(f'{file_path}/vsAvg_Hit.csv')
    p_vs_avg = pd.read_csv(f'{file_path}/vsAvg_Pitch.csv')
    h_vs_sim = pd.read_csv(f'{file_path}/hitters_vs_sim_data.csv')
    logo = "{}/Logo.jpeg".format(file_path)
    gameinfo = pd.read_csv(f'{file_path}/gameinfo.csv')
    return logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, propsdf, gameinfo,h_vs_sim

color1='#FFBABA'
color2='#FFCC99'
color3='#FFFF99'
color4='#CCFF99'
color5='#99FF99'

def applyColor_HitMatchups(val, column):
    if column == 'xwOBA':
        if val >= .35:
            return f'background-color: {color5}'
        elif val >= .325:
            return f'background-color: {color4}'
        elif val >= .3:
            return f'background-color: {color3}'
        elif val >= .275:
            return f'background-color: {color2}'
        elif val < .275:
            return f'background-color: {color1}'
    if column == 'xwOBA Con':
        if val >= .5:
            return f'background-color: {color5}'
        elif val >= .425:
            return f'background-color: {color4}'
        elif val >= .375:
            return f'background-color: {color3}'
        elif val >= .35:
            return f'background-color: {color2}'
        elif val < .35:
            return f'background-color: {color1}'
    if column == 'SwStr%':
        if val >= .15:
            return f'background-color: {color1}'
        elif val >= .13:
            return f'background-color: {color2}'
        elif val >= .11:
            return f'background-color: {color3}'
        elif val >= .09:
            return f'background-color: {color4}'
        elif val < .09:
            return f'background-color: {color5}'      
    if column == 'Brl%':
        if val >= .15:
            return f'background-color: {color5}'
        elif val >= .1:
            return f'background-color: {color4}'
        elif val >= .07:
            return f'background-color: {color3}'
        elif val >= .05:
            return f'background-color: {color2}'
        elif val < .05:
            return f'background-color: {color1}'
    if column == 'FB%':
        if val >= .35:
            return f'background-color: {color5}'
        elif val >= .30:
            return f'background-color: {color4}'
        elif val >= .25:
            return f'background-color: {color3}'
        elif val >= .2:
            return f'background-color: {color2}'
        elif val < .2:
            return f'background-color: {color1}'  
    if column == 'Hard%':
        if val >= .6:
            return f'background-color: {color5}'
        elif val >= .5:
            return f'background-color: {color4}'
        elif val >= .45:
            return f'background-color: {color3}'
        elif val >= .3:
            return f'background-color: {color2}'
        elif val < .3:
            return f'background-color: {color1}'  
def applyColor_HitStat(val, column):
    if column == 'K%':
        if val >= .3:
            return f'background-color: {color1}'
        elif val >= .26:
            return f'background-color: {color2}'
        elif val >= .23:
            return f'background-color: {color3}'
        elif val >= .2:
            return f'background-color: {color4}'
        elif val < .2:
            return f'background-color: {color5}'

    if column == 'xwOBA':
        if val >= .37:
            return f'background-color: {color5}'
        elif val >= .35:
            return f'background-color: {color4}'
        elif val >= .33:
            return f'background-color: {color3}'
        elif val >= .31:
            return f'background-color: {color2}'
        elif val < .31:
            return f'background-color: {color1}'
    
    if column == 'BB%':
        if val >= .11:
            return f'background-color: {color5}'
        elif val >= .09:
            return f'background-color: {color4}'
        elif val >= .07:
            return f'background-color: {color3}'
        elif val >= .05:
            return f'background-color: {color2}'
        elif val < .05:
            return f'background-color: {color1}'
    
    if column == 'Brl%':
        if val >= .15:
            return f'background-color: {color5}'
        elif val >= .10:
            return f'background-color: {color4}'
        elif val >= .07:
            return f'background-color: {color3}'
        elif val >= .05:
            return f'background-color: {color2}'
        elif val < .05:
            return f'background-color: {color1}'      
    if column == 'FB%':
        if val >= .35:
            return f'background-color: {color5}'
        elif val >= .30:
            return f'background-color: {color4}'
        elif val >= .25:
            return f'background-color: {color3}'
        elif val >= .2:
            return f'background-color: {color2}'
        elif val < .2:
            return f'background-color: {color1}'      
def applyColor_PitchStat(val, column):
    if column == 'K%':
        if val >= .3:
            return 'background-color: #FFBABA'
        elif val >= .26:
            return 'background-color: #FFCC99'
        elif val >= .23:
            return 'background-color: #FFFF99'
        elif val >= .2:
            return 'background-color: #CCFF99'
        elif val < .2:
            return 'background-color: #99FF99'
    if column == 'BB%':
        if val >= .11:
            return f'background-color: {color1}'
        elif val >= .09:
            return f'background-color: {color2}'
        elif val >= .07:
            return f'background-color: {color3}'
        elif val >= .05:
            return f'background-color: {color4}'
        elif val < .05:
            return f'background-color: {color5}'
    if column == 'SwStr%':
        if val >= .15:
            return f'background-color: {color5}'
        elif val >= .13:
            return f'background-color: {color4}'
        elif val >= .115:
            return f'background-color: {color3}'
        elif val >= .1:
            return f'background-color: {color2}'
        elif val < .1:
            return f'background-color: {color1}'
    if column == 'Ball%':
        if val >= .4:
            return f'background-color: {color1}'
        elif val >= .38:
            return f'background-color: {color2}'
        elif val >= .35:
            return f'background-color: {color3}'
        elif val >= .32:
            return f'background-color: {color4}'
        elif val < .32:
            return f'background-color: {color5}'
    if column == 'xwOBA':
        if val >= .37:
            return f'background-color: {color1}'
        elif val >= .35:
            return f'background-color: {color2}'
        elif val >= .33:
            return f'background-color: {color3}'
        elif val >= .31:
            return f'background-color: {color4}'
        elif val < .31:
            return f'background-color: {color5}'
def applyColor_PitchProj(val, column):
    if column == 'Sal':
        if val >= 10000:
            return f'background-color: {color1}'
        elif val >= 9000:
            return f'background-color: {color2}'
        elif val >= 8000:
            return f'background-color: {color3}'
        elif val >= 7000:
            return f'background-color: {color4}'
        elif val < 7000:
            return f'background-color: {color5}'
    if column == 'PC':
        if val >= 95:
            return f'background-color: {color5}'
        elif val >= 90:
            return f'background-color: {color4}'
        elif val >= 80:
            return f'background-color: {color3}'
        elif val >= 75:
            return f'background-color: {color2}'
        elif val < 75:
            return f'background-color: {color1}'
    if column == 'DKPts':
        if val >= 22:
            return f'background-color: {color5}'
        elif val >= 19:
            return f'background-color: {color4}'
        elif val >= 16:
            return f'background-color: {color3}'
        elif val >= 13:
            return f'background-color: {color2}'
        elif val < 13:
            return f'background-color: {color1}'
    if column == 'Val':
        if val >= 2.2:
            return f'background-color: {color5}'
        elif val >= 2:
            return f'background-color: {color4}'
        elif val >= 1.8:
            return f'background-color: {color3}'
        elif val >= 1.6:
            return f'background-color: {color2}'
        elif val < 1.6:
            return f'background-color: {color1}'
    if column == 'IP':
        if val >= 6.25:
            return f'background-color: {color5}'
        elif val >= 5.75:
            return f'background-color: {color4}'
        elif val >= 5.25:
            return f'background-color: {color3}'
        elif val >= 4.75:
            return f'background-color: {color2}'
        elif val < 4.75:
            return f'background-color: {color1}'
    if column == 'H':
        if val >= 5.25:
            return f'background-color: {color1}'
        elif val >= 5:
            return f'background-color: {color2}'
        elif val >= 4.75:
            return f'background-color: {color3}'
        elif val >= 4.5:
            return f'background-color: {color4}'
        elif val < 4.5:
            return f'background-color: {color5}'
    if column == 'ER':
        if val >= 2.8:
            return f'background-color: {color1}'
        elif val >= 2.65:
            return f'background-color: {color2}'
        elif val >= 2.5:
            return f'background-color: {color3}'
        elif val >= 2.35:
            return f'background-color: {color4}'
        elif val < 2.35:
            return f'background-color: {color5}'
    if column == 'SO':
        if val >= 8:
            return f'background-color: {color5}'
        elif val >= 6.5:
            return f'background-color: {color4}'
        elif val >= 5:
            return f'background-color: {color3}'
        elif val >= 3.5:
            return f'background-color: {color2}'
        elif val < 3.5:
            return f'background-color: {color1}'
    if column == 'BB':
        if val >= 2:
            return f'background-color: {color1}'
        elif val >= 1.75:
            return f'background-color: {color2}'
        elif val >= 1.5:
            return f'background-color: {color3}'
        elif val >= 1.25:
            return f'background-color: {color4}'
        elif val < 1.25:
            return f'background-color: {color5}'
    if column == 'W':
        if val >= .35:
            return f'background-color: {color1}'
        elif val >= .3:
            return f'background-color: {color2}'
        elif val >= .25:
            return f'background-color: {color3}'
        elif val >= .2:
            return f'background-color: {color4}'
        elif val < .2:
            return f'background-color: {color5}'
    if column == 'Own%':
        if val >= 40:
            return f'background-color: {color1}'
        elif val >= 30:
            return f'background-color: {color2}'
        elif val >= 20:
            return f'background-color: {color3}'
        elif val >= 10:
            return f'background-color: {color4}'
        elif val < 10:
            return f'background-color: {color5}'
    if column == 'Ceil':
        if val >= 40:
            return f'background-color: {color5}'
        elif val >= 35:
            return f'background-color: {color4}'
        elif val >= 30:
            return f'background-color: {color3}'
        elif val >= 25:
            return f'background-color: {color2}'
        elif val < 25:
            return f'background-color: {color1}'
def applyColor_HitProj(val, column):
    if column == 'Sal':
        if val >= 5500:
            return f'background-color: {color1}'
        elif val >= 4500:
            return f'background-color: {color2}'
        elif val >= 3500:
            return f'background-color: {color3}'
        elif val >= 2500:
            return f'background-color: {color4}'
        elif val < 2500:
            return f'background-color: {color5}'
    if column == 'DKPts':
        if val >= 12:
            return f'background-color: {color5}'
        elif val >= 10:
            return f'background-color: {color4}'
        elif val >= 7.5:
            return f'background-color: {color3}'
        elif val >= 6:
            return f'background-color: {color2}'
        elif val < 6:
            return f'background-color: {color1}'
    if column == 'Value':
        if val >= 3.2:
            return f'background-color: {color5}'
        elif val >= 2.9:
            return f'background-color: {color4}'
        elif val >= 2.6:
            return f'background-color: {color3}'
        elif val >= 2.3:
            return f'background-color: {color2}'
        elif val < 2:
            return f'background-color: {color1}'
    if column == 'HR':
        if val >= .25:
            return f'background-color: {color5}'
        elif val >= .2:
            return f'background-color: {color4}'
        elif val >= .1:
            return f'background-color: {color3}'
        elif val >= .05:
            return f'background-color: {color2}'
        elif val < .05:
            return f'background-color: {color1}'
    if column == 'SB':
        if val >= .25:
            return f'background-color: {color5}'
        elif val >= .2:
            return f'background-color: {color4}'
        elif val >= .1:
            return f'background-color: {color3}'
        elif val >= .05:
            return f'background-color: {color2}'
        elif val < .05:
            return f'background-color: {color1}'

def color_cells_PitchProj(df_subset):
    return [applyColor_PitchProj(val, col) for val, col in zip(df_subset, df_subset.index)]

def color_cells_HitProj(df_subset):
    return [applyColor_HitProj(val, col) for val, col in zip(df_subset, df_subset.index)]

def color_cells_PitchStat(df_subset):
    return [applyColor_PitchStat(val, col) for val, col in zip(df_subset, df_subset.index)]

def color_cells_HitStat(df_subset):
    return [applyColor_HitStat(val, col) for val, col in zip(df_subset, df_subset.index)]

def color_cells_HitMatchups(df_subset):
    return [applyColor_HitMatchups(val, col) for val, col in zip(df_subset, df_subset.index)]

# Load data
logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, props_df, gameinfo, h_vs_sim = load_data()

logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, props_df, gameinfo, h_vs_sim = load_data()


# Compile game list (unchanged)
games_df = pitcherproj[['Team', 'Opponent', 'HomeTeam']].drop_duplicates()
games_df['RoadTeam'] = np.where(games_df['Team'] == games_df['HomeTeam'], games_df['Opponent'], games_df['Team'])
games_df['GameString'] = games_df['RoadTeam'] + '@' + games_df['HomeTeam']
games_df = games_df[['RoadTeam', 'HomeTeam', 'GameString']].drop_duplicates()
hitterproj['RoadTeam'] = np.where(hitterproj['Team'] == 'HomeTeam', 'Opp', hitterproj['Team'])
hitterproj['GameString'] = hitterproj['RoadTeam'] + '@' + hitterproj['Park']
pitcherproj['RoadTeam'] = np.where(pitcherproj['Team'] == pitcherproj['HomeTeam'], pitcherproj['Opponent'], pitcherproj['Team'])
pitcherproj['GameString'] = pitcherproj['RoadTeam'] + '@' + pitcherproj['HomeTeam']

def get_player_image(player_id):
    return f'https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_426,q_auto:best/v1/people/{player_id}/headshot/67/current'

# Sidebar navigation
st.sidebar.image(logo, width=150)  # Added logo to sidebar
st.sidebar.title("MLB Projections")
tab = st.sidebar.radio("Select View", ["Game Previews", "Pitcher Projections", "Hitter Projections"], help="Choose a view to analyze games or player projections.")
if "reload" not in st.session_state:
    st.session_state.reload = False

if st.sidebar.button("Reload Data"):
    st.session_state.reload = True
    st.cache_data.clear()  # Clear cache to force reload

# Main content
st.markdown(f"<center><h1>⚾ MLB DW Slate Analysis Tool ⚾</h1></center>", unsafe_allow_html=True)

if tab == "Game Previews":
    game_selection = list(games_df['GameString'])
    selected_game = st.selectbox('Select a Game', game_selection, help="Select a game to view detailed projections and stats.")

    selected_home_team = selected_game.split('@')[1]
    selected_road_team = selected_game.split('@')[0]


    these_sim = h_vs_sim[h_vs_sim['Team'].isin([selected_home_team,selected_road_team])]

    this_game_ump = umpire_data[umpire_data['HomeTeam'] == selected_home_team]
    known_ump = 'Y' if len(this_game_ump) > 0 else 'N'

    these_pitcherproj = pitcherproj[pitcherproj['GameString'] == selected_game]
    this_weather = weather_data[weather_data['HomeTeam'] == selected_home_team]
    game_name = this_weather['Game'].iloc[0]
    this_gameinfo = gameinfo[gameinfo['Park']==selected_home_team]
    this_gameinfo['Favorite'] = np.where(this_gameinfo['moneyline']<-100,1,0)
    this_favorite = this_gameinfo[this_gameinfo['Favorite']==1]['team'].iloc[0]
    this_favorite_odds = this_gameinfo[this_gameinfo['Favorite']==1]['moneyline'].iloc[0]
    this_over_under = this_gameinfo['overunder'].iloc[0]
    #st.write(this_gameinfo)

    # Get pitcher matchups
    road_sp_pid = str(these_pitcherproj[these_pitcherproj['Team'] == these_pitcherproj['RoadTeam']]['ID'].iloc[0]).replace('.0', '')
    road_sp_name = these_pitcherproj[these_pitcherproj['Team'] == these_pitcherproj['RoadTeam']]['Pitcher'].iloc[0]
    home_sp_pid = str(these_pitcherproj[these_pitcherproj['Team'] == these_pitcherproj['HomeTeam']]['ID'].iloc[0]).replace('.0', '')
    home_sp_name = these_pitcherproj[these_pitcherproj['Team'] == these_pitcherproj['HomeTeam']]['Pitcher'].iloc[0]

    p_proj_cols = ['Sal', 'DKPts', 'Val', 'IP', 'H', 'ER', 'SO', 'BB', 'W', 'Ownership']
    road_sp_projection = these_pitcherproj[these_pitcherproj['Pitcher'] == road_sp_name]
    home_sp_projection = these_pitcherproj[these_pitcherproj['Pitcher'] == home_sp_name]
    p_stats_cols = ['IP', 'K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA']
    road_sp_stats = pitcher_stats[pitcher_stats['Pitcher'] == road_sp_name]
    home_sp_stats = pitcher_stats[pitcher_stats['Pitcher'] == home_sp_name]

    # Player profiles in cards
    col1, col2, col3 = st.columns([2, 4, 2])
    with col1:
        st.markdown(
            f"""
            <div class="player-card">
                <img src="{get_player_image(road_sp_pid)}" width="150" style="border-radius: 10px;">
                <h4>{road_sp_name}</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(f"<center><h2>{game_name}</h2></center>", unsafe_allow_html=True)
        st.markdown(f"<center><h4>{road_sp_name} vs. {home_sp_name}</h4></center>", unsafe_allow_html=True)
        st.markdown(f"<center><h5>{this_favorite} ({this_favorite_odds}), O/U: {this_over_under}</h5></center>",unsafe_allow_html=True)
        
        weather_cond = this_weather['Conditions'].iloc[0]
        weather_temp = this_weather['Temp'].iloc[0]
        try:
            weather_winds = this_weather['Winds'].iloc[0] + ' ' + this_weather['Wind Dir'].iloc[0]
        except:
            weather_winds = this_weather.get('Winds', ['No Weather Data Found']).iloc[0]
        st.markdown(f"<center><b>Weather: {weather_cond}, {weather_temp}F<br>Winds: {weather_winds}</b></center>", unsafe_allow_html=True)
        if known_ump == 'Y':
            umpname = this_game_ump['Umpire'].iloc[0]
            k_boost = (this_game_ump['K Boost'].iloc[0] - 1) * 100
            k_symbol = '+' if k_boost > 0 else '' if k_boost == 0 else ''
            bb_boost = (this_game_ump['BB Boost'].iloc[0] - 1) * 100
            bb_symbol = '+' if bb_boost > 0 else '' if bb_boost == 0 else ''
            st.markdown(f"<center><b>Umpire: {umpname}<br>{k_symbol}{int(k_boost)}% K, {bb_symbol}{int(bb_boost)}% BB</b></center>", unsafe_allow_html=True)
    with col3:
        st.markdown(
            f"""
            <div class="player-card">
                <img src="{get_player_image(home_sp_pid)}" width="150" style="border-radius: 10px;">
                <h4>{home_sp_name}</h4>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Pitcher projections
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<h4>{road_sp_name} Projection</h4>", unsafe_allow_html=True)
        filtered_pproj = road_sp_projection[p_proj_cols].rename({'Ownership': 'Own%'}, axis=1)
        styled_df = filtered_pproj.style.apply(
            color_cells_PitchProj, subset=['DKPts', 'Sal', 'Val','IP','H','ER','SO','BB','W','Own%'], axis=1
        ).format({
            'Own%': '{:.0f}', 'Sal': '${:,.0f}', 'W': '{:.2f}', 'BB': '{:.2f}',
            'SO': '{:.2f}', 'ER': '{:.2f}', 'H': '{:.2f}', 'IP': '{:.1f}',
            'DKPts': '{:.2f}', 'Val': '{:.2f}'
        })
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
        st.markdown("<h4>2024-2025 Stats</h4>", unsafe_allow_html=True)
        show_all_df = road_sp_stats[p_stats_cols].assign(vs='All')
        vs_r_df = road_sp_stats[['IP RHB', 'K% RHB', 'BB% RHB', 'SwStr% RHB', 'Ball% RHB', 'xwOBA RHB']].assign(vs='RHB')
        vs_r_df.columns = ['IP', 'K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA', 'vs']
        vs_l_df = road_sp_stats[['IP LHB', 'K% LHB', 'BB% LHB', 'SwStr% LHB', 'Ball% LHB', 'xwOBA LHB']].assign(vs='LHB')
        vs_l_df.columns = ['IP', 'K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA', 'vs']
        stats_build = pd.concat([show_all_df, vs_r_df, vs_l_df]).reset_index(drop=True)[['vs', 'IP', 'K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA']]
        styled_df = stats_build.style.apply(
            color_cells_PitchStat, subset=['K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA'], axis=1
        ).format({
            'K%': '{:.1%}', 'BB%': '{:.1%}', 'SwStr%': '{:.1%}', 'Ball%': '{:.1%}', 'xwOBA': '{:.3f}', 'IP': '{:.1f}'
        })
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

    with col2:
        st.markdown(f"<h4>{home_sp_name} Projection</h4>", unsafe_allow_html=True)
        filtered_pproj = home_sp_projection[p_proj_cols].rename({'Ownership': 'Own%'}, axis=1)
        styled_df = filtered_pproj.style.apply(
            color_cells_PitchProj, subset=['DKPts', 'Sal', 'Val','IP','H','ER','SO','BB','W','Own%'], axis=1
        ).format({
            'Own%': '{:.0f}', 'Sal': '${:,.0f}', 'W': '{:.2f}', 'BB': '{:.2f}',
            'SO': '{:.2f}', 'ER': '{:.2f}', 'H': '{:.2f}', 'IP': '{:.1f}',
            'DKPts': '{:.2f}', 'Val': '{:.2f}'
        })
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
        st.markdown("<h4>2024-2025 Stats</h4>", unsafe_allow_html=True)
        show_all_df = home_sp_stats[p_stats_cols].assign(vs='All')
        vs_r_df = home_sp_stats[['IP RHB', 'K% RHB', 'BB% RHB', 'SwStr% RHB', 'Ball% RHB', 'xwOBA RHB']].assign(vs='RHB')
        vs_r_df.columns = ['IP', 'K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA', 'vs']
        vs_l_df = home_sp_stats[['IP LHB', 'K% LHB', 'BB% LHB', 'SwStr% LHB', 'Ball% LHB', 'xwOBA LHB']].assign(vs='LHB')
        vs_l_df.columns = ['IP', 'K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA', 'vs']
        stats_build = pd.concat([show_all_df, vs_r_df, vs_l_df]).reset_index(drop=True)[['vs', 'IP', 'K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA']]
        styled_df = stats_build.style.apply(
            color_cells_PitchStat, subset=['K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA'], axis=1
        ).format({
            'K%': '{:.1%}', 'BB%': '{:.1%}', 'SwStr%': '{:.1%}', 'Ball%': '{:.1%}', 'xwOBA': '{:.3f}', 'IP': '{:.1f}'
        })
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

    # Hitter projections/stats
    col1, col2 = st.columns([1, 5])
    with col1:
        option = st.selectbox(
            label="View Options",
            options=["Projections", "Stats", "Splits", "Matchups", "Best Matchups"],
            index=0,
            help="Choose to view hitter projections, stats, or splits."
        )
    if option == 'Projections':
        col1, col2 = st.columns(2)
        hitter_proj_cols = ['Hitter', 'Pos', 'LU', 'Sal', 'DKPts', 'Value', 'HR', 'SB']
        with col1:
            st.markdown(f"<h4>{selected_road_team} Lineup</h4>", unsafe_allow_html=True)
            road_projection_data = hitterproj[hitterproj['Team'] == selected_road_team][hitter_proj_cols]
            styled_df = road_projection_data.style.apply(
                color_cells_HitProj, subset=['DKPts', 'Value', 'Sal', 'HR', 'SB'], axis=1
            ).format({
                'DKPts': '{:.2f}', 'Value': '{:.2f}', 'Sal': '${:,.0f}',
                'PA': '{:.1f}', 'R': '{:.2f}', 'HR': '{:.2f}', 'RBI': '{:.2f}', 'SB': '{:.2f}'
            })
            st.dataframe(styled_df, hide_index=True, use_container_width=True)
        with col2:
            st.markdown(f"<h4>{selected_home_team} Lineup</h4>", unsafe_allow_html=True)
            home_projection_data = hitterproj[hitterproj['Team'] == selected_home_team][hitter_proj_cols]
            styled_df = home_projection_data.style.apply(
                color_cells_HitProj, subset=['DKPts', 'Value', 'Sal', 'HR', 'SB'], axis=1
            ).format({
                'DKPts': '{:.2f}', 'Value': '{:.2f}', 'Sal': '${:,.0f}',
                'PA': '{:.1f}', 'R': '{:.2f}', 'HR': '{:.2f}', 'RBI': '{:.2f}', 'SB': '{:.2f}'
            })
            st.dataframe(styled_df, hide_index=True, use_container_width=True)
    elif option in ['Stats', 'Splits']:
        road_hitter_stats = hitter_stats[hitter_stats['Team'] == selected_road_team]
        home_hitter_stats = hitter_stats[hitter_stats['Team'] == selected_home_team]
        if option == 'Stats':
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<h4>{selected_road_team} Stats</h4>", unsafe_allow_html=True)
                road_hitter_stats = road_hitter_stats[['Hitter', 'PA', 'K%', 'BB%', 'Brl%', 'xwOBA', 'FB%']]
                styled_df = road_hitter_stats.style.apply(
                    color_cells_HitStat, subset=['Brl%', 'FB%', 'K%', 'BB%', 'xwOBA'], axis=1
                ).format({
                    'K%': '{:.1%}', 'BB%': '{:.1%}', 'FB%': '{:.1%}', 'PA': '{:.0f}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}'
                })
                st.dataframe(styled_df, hide_index=True, use_container_width=True)
            with col2:
                st.markdown(f"<h4>{selected_home_team} Stats</h4>", unsafe_allow_html=True)
                home_hitter_stats = home_hitter_stats[['Hitter', 'PA', 'K%', 'BB%', 'Brl%', 'xwOBA', 'FB%']]
                styled_df = home_hitter_stats.style.apply(
                    color_cells_HitStat, subset=['Brl%', 'FB%', 'K%', 'BB%', 'xwOBA'], axis=1
                ).format({
                    'K%': '{:.1%}', 'BB%': '{:.1%}', 'FB%': '{:.1%}', 'PA': '{:.0f}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}'
                })
                st.dataframe(styled_df, hide_index=True, use_container_width=True)
        elif option == 'Splits':
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<h4>{selected_road_team} Splits</h4>", unsafe_allow_html=True)
                road_hitter_splits = road_hitter_stats[['Hitter', 'Split PA', 'Split K%', 'Split BB%', 'Split Brl%', 'Split xwOBA', 'Split FB%']]
                road_hitter_splits.columns = ['Hitter', 'PA', 'K%', 'BB%', 'Brl%', 'xwOBA', 'FB%']
                styled_df = road_hitter_splits.style.apply(
                    color_cells_HitStat, subset=['Brl%', 'FB%', 'K%', 'BB%', 'xwOBA'], axis=1
                ).format({
                    'K%': '{:.1%}', 'BB%': '{:.1%}', 'FB%': '{:.1%}', 'PA': '{:.0f}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}'
                })
                st.dataframe(styled_df, hide_index=True, use_container_width=True)
            with col2:
                st.markdown(f"<h4>{selected_home_team} Splits</h4>", unsafe_allow_html=True)
                home_hitter_splits = home_hitter_stats[['Hitter', 'Split PA', 'Split K%', 'Split BB%', 'Split Brl%', 'Split xwOBA', 'Split FB%']]
                home_hitter_splits.columns = ['Hitter', 'PA', 'K%', 'BB%', 'Brl%', 'xwOBA', 'FB%']
                styled_df = home_hitter_splits.style.apply(
                    color_cells_HitStat, subset=['Brl%', 'FB%', 'K%', 'BB%', 'xwOBA'], axis=1
                ).format({
                    'K%': '{:.1%}', 'BB%': '{:.1%}', 'FB%': '{:.1%}', 'PA': '{:.0f}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}'
                })
                st.dataframe(styled_df, hide_index=True, use_container_width=True)
    elif option == "Matchups":
        col1, col2 = st.columns([1,1])
        with col1:
            road_sim = these_sim[these_sim['Team']==selected_road_team]
            #road_sim = road_sim[(road_sim['xwOBA Con']>=.375)&(road_sim['SwStr%']<.11)]
            road_sim = road_sim[['Hitter','PC','xwOBA','xwOBA Con','SwStr%','Brl%','FB%','Hard%']]
            styled_df = road_sim.style.apply(color_cells_HitMatchups, subset=['xwOBA','xwOBA Con',
                                                                              'SwStr%','Brl%','FB%',
                                                                              'Hard%'], axis=1).format({'xwOBA': '{:.3f}',
                                                                                                        'xwOBA Con': '{:.3f}',
                                                                                                        'SwStr%': '{:.1%}',
                                                                                                        'Brl%': '{:.1%}',
                                                                                                        'FB%': '{:.1%}',
                                                                                                        'Hard%': '{:.1%}',})
            st.dataframe(styled_df, hide_index=True, use_container_width=True)
            #st.dataframe(road_sim)
        with col2:
            home_sim = these_sim[these_sim['Team']==selected_home_team]
            #home_sim = home_sim[(home_sim['xwOBA Con']>=.375)&(home_sim['SwStr%']<.11)]
            home_sim = home_sim[['Hitter','PC','xwOBA','xwOBA Con','SwStr%','Brl%','FB%','Hard%']]
            styled_df = home_sim.style.apply(color_cells_HitMatchups, subset=['xwOBA','xwOBA Con',
                                                                              'SwStr%','Brl%','FB%',
                                                                              'Hard%'], axis=1).format({'xwOBA': '{:.3f}',
                                                                                                        'xwOBA Con': '{:.3f}',
                                                                                                        'SwStr%': '{:.1%}',
                                                                                                        'Brl%': '{:.1%}',
                                                                                                        'FB%': '{:.1%}',
                                                                                                        'Hard%': '{:.1%}',})
            st.dataframe(styled_df, hide_index=True, use_container_width=True)

    elif option == "Best Matchups":
        col1, col2 = st.columns([1,1])
        with col1:
            road_sim = these_sim[these_sim['Team']==selected_road_team]
            road_sim = road_sim[(road_sim['xwOBA Con']>=.375)&(road_sim['SwStr%']<.11)]
            road_sim = road_sim[['Hitter','PC','xwOBA','xwOBA Con','SwStr%','Brl%','FB%','Hard%']]
            styled_df = road_sim.style.apply(color_cells_HitMatchups, subset=['xwOBA','xwOBA Con',
                                                                              'SwStr%','Brl%','FB%',
                                                                              'Hard%'], axis=1).format({'xwOBA': '{:.3f}',
                                                                                                        'xwOBA Con': '{:.3f}',
                                                                                                        'SwStr%': '{:.1%}',
                                                                                                        'Brl%': '{:.1%}',
                                                                                                        'FB%': '{:.1%}',
                                                                                                        'Hard%': '{:.1%}',})
            st.dataframe(styled_df, hide_index=True, use_container_width=True)
            #st.dataframe(road_sim)
        with col2:
            home_sim = these_sim[these_sim['Team']==selected_home_team]
            home_sim = home_sim[(home_sim['xwOBA Con']>=.375)&(home_sim['SwStr%']<.11)]
            home_sim = home_sim[['Hitter','PC','xwOBA','xwOBA Con','SwStr%','Brl%','FB%','Hard%']]
            styled_df = home_sim.style.apply(color_cells_HitMatchups, subset=['xwOBA','xwOBA Con',
                                                                              'SwStr%','Brl%','FB%',
                                                                              'Hard%'], axis=1).format({'xwOBA': '{:.3f}',
                                                                                                        'xwOBA Con': '{:.3f}',
                                                                                                        'SwStr%': '{:.1%}',
                                                                                                        'Brl%': '{:.1%}',
                                                                                                        'FB%': '{:.1%}',
                                                                                                        'Hard%': '{:.1%}',})
            st.dataframe(styled_df, hide_index=True, use_container_width=True)

st.markdown("""
    <style>
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        overflow: hidden;
    }
    .dataframe {
        width: 100%;
        font-size: 14px;
    }
    .dataframe th {
        background-color: #f4f4f4;
        color: #333;
        font-weight: bold;
        padding: 10px;
        text-align: left;
        border-bottom: 2px solid #ddd;
    }
    .dataframe td {
        padding: 8px;
        border-bottom: 1px solid #eee;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .dataframe tr:hover {
        background-color: #f1f1f1;
    }
    .stSelectbox, .stTextInput, .stRadio > div {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 5px;
    }
    h3 {
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .stMarkdown p {
        color: #666;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)





# Custom CSS for DataFrame and widget styling
st.markdown("""
    <style>
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        overflow: hidden;
    }
    .dataframe {
        width: 100%;
        font-size: 14px;
    }
    .dataframe th {
        background-color: #f4f4f4;
        color: #333;
        font-weight: bold;
        padding: 10px;
        text-align: left;
        border-bottom: 2px solid #ddd;
    }
    .dataframe td {
        padding: 8px;
        border-bottom: 1px solid #eee;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .dataframe tr:hover {
        background-color: #f1f1f1;
    }
    .stSelectbox, .stTextInput, .stRadio > div {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 5px;
    }
    h3 {
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .stMarkdown p {
        color: #666;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

if tab == "Pitcher Projections":
    st.markdown("<h3>Pitcher Projections</h3>", unsafe_allow_html=True)
    st.markdown("Explore projected pitcher performance for MLB games. Filter by slate, team, or opponent to customize your view.", unsafe_allow_html=True)
    
    # Create three columns for filters
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Radio button for slate selection
        option = st.selectbox(
            label="Slate",
            options=["Show All", "Main Slate Only"],
            index=0,
            help="Choose to view all games or only the main slate.",
            key="slate_filter_pitcher"
        )
    
    with col2:
        # Dropdown for team selection
        teams = ['All Teams'] + sorted(pitcherproj['Team'].dropna().unique().tolist())
        team_filter = st.selectbox(
            label="Filter by Team",
            options=teams,
            index=0,
            help="Select a team to filter pitchers.",
            key="team_filter_pitcher"
        )
    
    with col3:
        # Text input for filtering by opponent
        opp_filter = st.text_input(
            label="Filter by Opponent",
            placeholder="Enter opponent team (e.g., TOR, NYY)",
            help="Type an opponent team to filter pitchers (case-insensitive).",
            key="opp_filter_pitcher"
        )
    
    # Filter DataFrame based on slate selection
    if option == "Main Slate Only":
        show_pproj = pitcherproj[pitcherproj['MainSlate'] == 'Main']
    else:
        show_pproj = pitcherproj.copy()
    
    # Apply team filter if not 'All Teams'
    if team_filter != 'All Teams':
        show_pproj = show_pproj[show_pproj['Team'] == team_filter]
    
    # Apply opponent filter if input is provided
    if opp_filter:
        show_pproj = show_pproj[show_pproj['Opponent'].str.contains(opp_filter, case=False, na=False)]
    
    # Rename and select columns
    show_pproj = show_pproj.rename({'Ownership': 'Own%'}, axis=1)
    show_pproj = show_pproj[['Pitcher','Team','Opponent','HomeTeam','Sal','DKPts','Val', 'PC','IP','SO','BB','W','Ceil','Own%']]
    
    # Apply styling and formatting
    styled_df = show_pproj.style.apply(
        color_cells_PitchProj, subset=['DKPts','Val','Sal','SO','W','Ceil','Own%','BB','PC','IP'], axis=1
    ).format({
        'DKPts': '{:.2f}','FDPts': '{:.2f}', 
        'Val': '{:.2f}', 'Sal': '${:,.0f}', 
        'PC': '{:.0f}', 'IP': '{:.2f}', 
        'SO': '{:.2f}', 'BB': '{:.2f}', 
        'W': '{:.2f}', 'Floor': '{:.2f}', 
        'Ceil': '{:.2f}', 'Own%': '{:.0f}'
    }).set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'left'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('text-align', 'left')]}
    ])
    
    # Display the styled DataFrame
    st.dataframe(styled_df, use_container_width=True, height=800, hide_index=True)



if tab == "Hitter Projections":
    hitterproj['Value'] = round(hitterproj['DKPts']/(hitterproj['Sal']/1000),2)
    st.markdown("<h3>Hitter Projections</h3>", unsafe_allow_html=True)
    st.markdown("Explore projected hitter performance for MLB games. Filter by slate, team, or position to customize your view.", unsafe_allow_html=True)
    
    # Create three columns for filters
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Radio button for slate selection
        option = st.selectbox(
            label="Slate",
            options=["Show All", "Main Slate Only"],
            index=0,
            help="Choose to view all games or only the main slate.",
            key="slate_filter"
        )
    
    with col2:
        # Dropdown for team selection
        teams = ['All Teams'] + sorted(hitterproj['Team'].dropna().unique().tolist())
        team_filter = st.selectbox(
            label="Filter by Team",
            options=teams,
            index=0,
            help="Select a team to filter players.",
            key="team_filter"
        )
    
    with col3:
        # Text input for filtering by position
        pos_filter = st.text_input(
            label="Filter by Position",
            placeholder="Enter position (e.g., OF, SS)",
            help="Type a position to filter players (case-insensitive).",
            key="pos_filter"
        )
    
    # Filter DataFrame based on slate selection
    if option == "Main Slate Only":
        show_hproj = hitterproj[hitterproj['MainSlate'] == 'Main']
    else:
        show_hproj = hitterproj.copy()
    
    # Apply team filter if not 'All Teams'
    if team_filter != 'All Teams':
        show_hproj = show_hproj[show_hproj['Team'] == team_filter]
    
    # Apply position filter if input is provided
    if pos_filter:
        show_hproj = show_hproj[show_hproj['Pos'].str.contains(pos_filter, case=False, na=False)]
    
    # Rename and select columns
    show_hproj = show_hproj.rename({'Ownership': 'Own%'}, axis=1)
    show_hproj = show_hproj[['Hitter', 'Pos', 'Team', 'Sal', 'Opp', 'Park', 'OppSP', 'LU', 'DKPts', 'Value', 'HR', 'SB', 'Floor', 'Ceil', 'Own%']]
    
    # Apply styling and formatting
    styled_df = show_hproj.style.apply(
        color_cells_HitProj, subset=['DKPts', 'Value', 'Sal', 'HR', 'SB'], axis=1
    ).format({
        'DKPts': '{:.2f}', 
        'Value': '{:.2f}', 
        'Sal': '${:,.0f}', 
        'Floor': '{:.2f}', 
        'Ceil': '{:.2f}', 
        'PA': '{:.1f}', 
        'R': '{:.2f}', 
        'HR': '{:.2f}', 
        'RBI': '{:.2f}', 
        'SB': '{:.2f}', 
        'Own%': '{:.0f}'
    }).set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'left'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('text-align', 'left')]}
    ])
    
    # Display the styled DataFrame
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=600)
