import streamlit as st
import pandas as pd, math
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
        background-color: white; /* #F5F6F5; Light gray background for a clean look */
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
    hitterproj2 = pd.read_csv(f'{file_path}/Tableau_DailyHitterProj.csv')
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
    bpreport = pd.read_csv(f'{file_path}/BullpenReport.csv')
    rpstats = pd.read_csv(f'{file_path}/relieverstats.csv')
    return logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, propsdf, gameinfo,h_vs_sim, bpreport, rpstats, hitterproj2

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
            return f'background-color:{color5}'
        elif val >= .26:
            return f'background-color:{color4}'
        elif val >= .23:
            return f'background-color:{color3}'
        elif val >= .2:
            return f'background-color:{color2}'
        elif val < .2:
            return f'background-color:{color1}'
    if column == 'K-BB%':
        if val >= .2:
            return f'background-color:{color5}'
        elif val >= .18:
            return f'background-color:{color4}'
        elif val >= .16:
            return f'background-color:{color3}'
        elif val >= .13:
            return f'background-color:{color2}'
        elif val < .13:
            return f'background-color:{color1}'
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
    if column == 'xERA':
        if val >= .37*13.4:
            return f'background-color: {color1}'
        elif val >= .35*13.4:
            return f'background-color: {color2}'
        elif val >= .33*13.4:
            return f'background-color: {color3}'
        elif val >= .31*13.4:
            return f'background-color: {color4}'
        elif val < .31*13.4:
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
def applyColor_Props(val, column):
    if column == 'BetValue':
        if val >= .2:
            return f'background-color: {color1}'
        elif val >= .15:
            return f'background-color: {color2}'
        elif val >= .1:
            return f'background-color: {color3}'
        elif val < .1:
            return f'background-color: {color5}'

    if column == 'Price':
        if val >= 150:
            return f'background-color: {color5}'
        elif val >= 100:
            return f'background-color: {color4}'
        elif val >= -150:
            return f'background-color: {color3}'
        elif val >= -200:
            return f'background-color: {color2}'
        elif val < -200:
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
def color_cells_Props(df_subset):
    return [applyColor_Props(val, col) for val, col in zip(df_subset, df_subset.index)]

# Load data
logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, props_df, gameinfo, h_vs_sim,bpreport, rpstats, hitterproj2 = load_data()
games_df = pitcherproj[['Team', 'Opponent', 'HomeTeam']].drop_duplicates()
games_df['RoadTeam'] = np.where(games_df['Team'] == games_df['HomeTeam'], games_df['Opponent'], games_df['Team'])
games_df['GameString'] = games_df['RoadTeam'] + '@' + games_df['HomeTeam']
games_df = games_df[['RoadTeam', 'HomeTeam', 'GameString']].drop_duplicates()
hitterproj['RoadTeam'] = np.where(hitterproj['Team'] == 'HomeTeam', 'Opp', hitterproj['Team'])
hitterproj['GameString'] = hitterproj['RoadTeam'] + '@' + hitterproj['Park']
pitcherproj['RoadTeam'] = np.where(pitcherproj['Team'] == pitcherproj['HomeTeam'], pitcherproj['Opponent'], pitcherproj['Team'])
pitcherproj['GameString'] = pitcherproj['RoadTeam'] + '@' + pitcherproj['HomeTeam']
bpreport['BP Rank'] = bpreport['xERA'].rank()
bpreport = bpreport.sort_values(by='BP Rank')
bpreport['BP Rank'] = range(1,len(bpreport)+1)
bpcount = len(bpreport)
bpreport['Rank'] = bpreport['BP Rank'].astype(str) + ' / ' + str(bpcount)
bpreport['K%'] = bpreport['K%']/100
bpreport['BB%'] = bpreport['BB%']/100
bpreport['K-BB%'] = bpreport['K-BB%']/100
bpreport['SwStr%'] = bpreport['SwStr%']/100
# add hitter emojis
hot_hitters = list(hitter_stats[hitter_stats['IsHot']=='Y']['ID'])
cold_hitters = list(hitter_stats[hitter_stats['IsCold']=='Y']['ID'])
hitterproj['Hitter'] = np.where(hitterproj['ID'].isin(hot_hitters), hitterproj['Hitter'] + ' 🔥' ,hitterproj['Hitter'])
hitterproj['Hitter'] = np.where(hitterproj['ID'].isin(cold_hitters), hitterproj['Hitter'] + ' 🥶' ,hitterproj['Hitter'])

hitter_stats['Hitter'] = np.where(hitter_stats['ID'].isin(hot_hitters), hitter_stats['Hitter'] + ' 🔥' ,hitter_stats['Hitter'])
hitter_stats['Hitter'] = np.where(hitter_stats['ID'].isin(cold_hitters), hitter_stats['Hitter'] + ' 🥶' ,hitter_stats['Hitter'])


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
    #logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, props_df, gameinfo, h_vs_sim = load_data()

# Main content
st.markdown(f"<center><h1>⚾ MLB DW Slate Analysis Tool ⚾</h1></center>", unsafe_allow_html=True)

if tab == "Game Previews":
    game_selection = list(games_df['GameString'])
    selected_game = st.selectbox('Select a Game', game_selection, help="Select a game to view detailed projections and stats.")

    selected_home_team = selected_game.split('@')[1]
    selected_road_team = selected_game.split('@')[0]

    road_bullpen_team = bpreport[bpreport['Team']==selected_road_team]
    road_bullpen_rp = rpstats[rpstats['Team']==selected_road_team]

    home_bullpen_team = bpreport[bpreport['Team']==selected_home_team]
    home_bullpen_rp = rpstats[rpstats['Team']==selected_home_team]

    #st.write(road_bullpen_team)
    #st.write(road_bullpen_rp)

    these_sim = h_vs_sim[h_vs_sim['Team'].isin([selected_home_team,selected_road_team])]

    this_game_ump = umpire_data[umpire_data['HomeTeam'] == selected_home_team]
    known_ump = 'Y' if len(this_game_ump) > 0 else 'N'

    these_pitcherproj = pitcherproj[pitcherproj['GameString'] == selected_game]
    this_weather = weather_data[weather_data['HomeTeam'] == selected_home_team]
    game_name = this_weather['Game'].iloc[0]
    try:
        this_gameinfo = gameinfo[gameinfo['Park']==selected_home_team]
        this_gameinfo['Favorite'] = np.where(this_gameinfo['moneyline']<-100,1,0)
        this_favorite = this_gameinfo[this_gameinfo['Favorite']==1]['team'].iloc[0]
        this_favorite_odds = this_gameinfo[this_gameinfo['Favorite']==1]['moneyline'].iloc[0]
        this_over_under = this_gameinfo['overunder'].iloc[0]
        game_info_fail = 'N'
    except:
        game_info_fail = 'Y'
        this_favorite=''
        this_favorite_odds=''
        this_over_under=''
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
    road_sp_hand = road_sp_stats['Hand'].iloc[0]
    is_road_p_hot = road_sp_stats['IsHot'].iloc[0]
    is_road_p_cold = road_sp_stats['IsCold'].iloc[0]

    if is_road_p_hot == 1:
        road_p_emoji = '🔥'
    elif is_road_p_cold == 1:
        road_p_emoji = '🥶'
    else:
        road_p_emoji = ''
    
    home_sp_stats = pitcher_stats[pitcher_stats['Pitcher'] == home_sp_name]
    home_sp_hand = home_sp_stats['Hand'].iloc[0]
    is_home_p_hot = home_sp_stats['IsHot'].iloc[0]
    is_home_p_cold = home_sp_stats['IsCold'].iloc[0]
    if is_home_p_hot == 1:
        home_p_emoji = '🔥'
        st.write('home hot')
    elif is_home_p_cold == 1:
        home_p_emoji = '🥶'
    else:
        home_p_emoji = ''
    
    road_sp_show_name = road_sp_name + ' ' + road_p_emoji
    home_sp_show_name = home_sp_name + ' ' + home_p_emoji
    pitcher_props = props_df[props_df['Player'].isin([road_sp_name,home_sp_name])]
    pitcher_props = pitcher_props[pitcher_props['Type']!='pitcher_outs']
    # Player profiles in cards
    col1, col2, col3 = st.columns([2, 4, 2])
    with col1:
        st.markdown(
            f"""
            <div class="player-card">
                <img src="{get_player_image(road_sp_pid)}" width="150" style="border-radius: 10px;">
                <h4>{road_sp_show_name}</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(f"<center><h2>{game_name}</h2></center>", unsafe_allow_html=True)
        st.markdown(f"<center><h5>{road_sp_show_name} vs. {home_sp_show_name}</h5></center>", unsafe_allow_html=True)
        if game_info_fail == 'N':
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
        
        st.markdown("<br><center><font size=3>🔥 <i>= hot player</i>, 🥶 <i>= cold player</i></center></i></font>", unsafe_allow_html=True)
    
    with col3:
        st.markdown(
            f"""
            <div class="player-card">
                <img src="{get_player_image(home_sp_pid)}" width="150" style="border-radius: 10px;">
                <h4>{home_sp_show_name}</h4>
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
    
    # Bullpens
    checked = st.checkbox("Show Bullpens", value=False, key=None, help=None, on_change=None)
    if checked:
        #st.write("Checkbox is checked!")

        col1, col2 = st.columns([1,1])
        with col1:
            team_rp_list = rpstats[rpstats['Team']==selected_road_team]
            team_rp_rhp = len(team_rp_list[team_rp_list['Hand']=='R'])
            team_rp_lhp = len(team_rp_list[team_rp_list['Hand']=='L'])
            road_bp_unavail = road_bullpen_team['Unavailable'].iloc[0]
            st.markdown(f"<h4>{selected_road_team} Bullpen</h4>", unsafe_allow_html=True)
                
            show_road_bullpen = road_bullpen_team[['Rank','K%','BB%','K-BB%','SwStr%','xwOBA','xERA']]
            show_road_bullpen = road_bullpen_team[['Rank','K%','BB%','K-BB%','SwStr%','xwOBA','xERA']]
            show_road_bullpen['RHP'] = team_rp_rhp
            show_road_bullpen['LHP'] = team_rp_lhp

            styled_df = show_road_bullpen.style.apply(
                color_cells_PitchStat, subset=['K%','BB%','K-BB%','SwStr%','xwOBA','xERA'], axis=1).format({
                    'K%': '{:.1%}','BB%': '{:.1%}', 'K-BB%': '{:.1%}','SwStr%': '{:.1%}','xwOBA': '{:.3f}','xERA': '{:.2f}'})
            st.dataframe(styled_df, hide_index=True)
            try:
                if len(road_bp_unavail)>1:
                    st.write(f'Unavailable: {road_bp_unavail}')
            except:
                pass
        
            team_rp_list = team_rp_list[['Player','Hand','K%','BB%','SwStr%','estimated_woba_using_speedangle']]
            team_rp_list = team_rp_list.rename({'estimated_woba_using_speedangle': 'xwOBA'},axis=1)
            styled_df = team_rp_list.style.apply(
                color_cells_PitchStat, subset=['K%','BB%','SwStr%','xwOBA'], axis=1).format({
                    'K%': '{:.1%}','BB%': '{:.1%}', 'K-BB%': '{:.1%}','SwStr%': '{:.1%}','xwOBA': '{:.3f}','xERA': '{:.2f}'})
            st.dataframe(styled_df, hide_index=True,width=500)

        
        
        with col2:
            team_rp_list = rpstats[rpstats['Team']==selected_home_team]
            team_rp_rhp = len(team_rp_list[team_rp_list['Hand']=='R'])
            team_rp_lhp = len(team_rp_list[team_rp_list['Hand']=='L'])

            home_bp_unavail = home_bullpen_team['Unavailable'].iloc[0]
            #st.write(home_bp_unavail)
            st.markdown(f"<h4>{selected_home_team} Bullpen </h4>", unsafe_allow_html=True)

            show_home_bullpen = home_bullpen_team[['Rank','K%','BB%','K-BB%','SwStr%','xwOBA','xERA']]
            show_home_bullpen['RHP'] = team_rp_rhp
            show_home_bullpen['LHP'] = team_rp_lhp
            
            styled_df = show_home_bullpen.style.apply(
                color_cells_PitchStat, subset=['K%','BB%','K-BB%','SwStr%','xwOBA','xERA'], axis=1).format({
                    'K%': '{:.1%}','BB%': '{:.1%}', 'K-BB%': '{:.1%}','SwStr%': '{:.1%}','xwOBA': '{:.3f}','xERA': '{:.2f}'})
            st.dataframe(styled_df, hide_index=True)

            try:
                if len(home_bp_unavail)>1:
                    st.write(f'Unavailable: {home_bp_unavail}')
            except:
                pass
                
            team_rp_list = team_rp_list[['Player','Hand','K%','BB%','SwStr%','estimated_woba_using_speedangle']]
            team_rp_list = team_rp_list.rename({'estimated_woba_using_speedangle': 'xwOBA'},axis=1)
            styled_df = team_rp_list.style.apply(
                color_cells_PitchStat, subset=['K%','BB%','SwStr%','xwOBA'], axis=1).format({
                    'K%': '{:.1%}','BB%': '{:.1%}', 'K-BB%': '{:.1%}','SwStr%': '{:.1%}','xwOBA': '{:.3f}','xERA': '{:.2f}'})
            st.dataframe(styled_df, hide_index=True,width=500)



    # Hitter projections/stats
    col1, col2 = st.columns([1, 3])
    with col1:
        option = st.selectbox(
            label="View Options",
            options=["Best Matchups", "Projections", "Stats", "Splits", "Matchups", "Props"],
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
                st.markdown(f"<h4>{selected_road_team} vs. {home_sp_hand}HB</h4>", unsafe_allow_html=True)
                road_hitter_splits = road_hitter_stats[['Hitter', 'Split PA', 'Split K%', 'Split BB%', 'Split Brl%', 'Split xwOBA', 'Split FB%']]
                road_hitter_splits.columns = ['Hitter', 'PA', 'K%', 'BB%', 'Brl%', 'xwOBA', 'FB%']
                styled_df = road_hitter_splits.style.apply(
                    color_cells_HitStat, subset=['Brl%', 'FB%', 'K%', 'BB%', 'xwOBA'], axis=1
                ).format({
                    'K%': '{:.1%}', 'BB%': '{:.1%}', 'FB%': '{:.1%}', 'PA': '{:.0f}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}'
                })
                st.dataframe(styled_df, hide_index=True, use_container_width=True)
            with col2:
                st.markdown(f"<h4>{selected_home_team} vs. {road_sp_hand}HB</h4>", unsafe_allow_html=True)
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
    elif option == "Props":
        game_hitter_list = list(hitterproj[hitterproj['Team'].isin([selected_road_team,selected_home_team])]['Hitter'])
        hitter_props = props_df[props_df['Player'].isin(game_hitter_list)]
        pitcher_props = pitcher_props[pitcher_props['Type']!='pitcher_outs']
        game_props = pd.concat([hitter_props,pitcher_props])
        game_props = game_props[['Player','Book','Type','OU','Line','Price','BetValue']].sort_values(by='BetValue',ascending=False)
        game_props = game_props[game_props['BetValue']>=.1]
        if len(game_props)>0:
            styled_df = game_props.style.apply(color_cells_Props, subset=['BetValue','Price'], axis=1).format({'BetValue': '{:.1%}',
                                                                                                                'Price': '{:.0f}',
                                                                                                                'Line': '{:.1f}'})
            st.dataframe(styled_df, hide_index=True, width=750)
        else:
            st.write('No recommended props for this game')

        #pitcher_props

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
    st.markdown("<h1>Pitcher Projections</h1>", unsafe_allow_html=True)
    st.markdown("Explore projected pitcher performance for MLB games. Filter by slate, team, or opponent to customize your view.", unsafe_allow_html=True)
    pitcher_matchups = dict(zip(pitcherproj.Team,pitcherproj.Opponent))
    p_vs_avg['Opp'] = p_vs_avg['Team'].map(pitcher_matchups)
    top_five_proj = pitcherproj.sort_values(by='DKPts',ascending=False).head(5)
    
    checked = st.checkbox("Show Projection Highlights", value=False, key=None, help=None, on_change=None)
    if checked:
        #st.write("Checkbox is checked!")
        st.markdown("<h4>Top Projections</h4>", unsafe_allow_html=True)
        col1,col2,col3,col4,col5 = st.columns([1,1,1,1,1])
        with col1:
            st.image(get_player_image(top_five_proj['ID'].iloc[0]),width=120)
            pname = top_five_proj['Pitcher'].iloc[0]
            dk = str(top_five_proj['DKPts'].iloc[0])
            st.write(f'{pname}: {dk}Pts')
        with col2:
            st.image(get_player_image(top_five_proj['ID'].iloc[1]),width=120)
            pname = top_five_proj['Pitcher'].iloc[1]
            dk = str(top_five_proj['DKPts'].iloc[1])
            st.write(f'{pname}: {dk}Pts')
        with col3:
            st.image(get_player_image(top_five_proj['ID'].iloc[2]),width=120)
            pname = top_five_proj['Pitcher'].iloc[2]
            dk = str(top_five_proj['DKPts'].iloc[2])
            st.write(f'{pname}: {dk}Pts')
        with col4:
            st.image(get_player_image(top_five_proj['ID'].iloc[3]),width=120)
            pname = top_five_proj['Pitcher'].iloc[3]
            dk = str(top_five_proj['DKPts'].iloc[3])
            st.write(f'{pname}: {dk}Pts')
        with col5:
            st.image(get_player_image(top_five_proj['ID'].iloc[4]),width=120)
            pname = top_five_proj['Pitcher'].iloc[4]
            dk = str(top_five_proj['DKPts'].iloc[4])
            st.write(f'{pname}: {dk}Pts')
        
        col1, col2 = st.columns([1,1])
        with col1:
            st.markdown("<h4>Highest Projection Over Season Average</h4>", unsafe_allow_html=True)
            show_p_vs_avg = p_vs_avg[['Pitcher','Team','Opp','DKPts','Avg DK Proj','DKPts Diff']].sort_values(by='DKPts Diff',ascending=False)
            show_p_vs_avg = show_p_vs_avg.head(5)
            st.dataframe(show_p_vs_avg,hide_index=True)
        with col2:
            st.markdown("<h4>Lowest Projection Over Season Average</h4>", unsafe_allow_html=True)
            show_p_vs_avg = p_vs_avg[['Pitcher','Team','Opp','DKPts','Avg DK Proj','DKPts Diff']].sort_values(by='DKPts Diff',ascending=True)
            show_p_vs_avg = show_p_vs_avg.head(5)
            st.dataframe(show_p_vs_avg,hide_index=True)
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
    hitterproj['Hitter'] = hitterproj['Hitter'].str.replace('🔥','').str.strip()
    hitterproj['Hitter'] = hitterproj['Hitter'].str.replace('🥶','').str.strip()
    hitter_name_id_dict = dict(zip(hitterproj.Hitter,hitterproj.ID))
    hitter_matchups_dict = dict(zip(hitterproj.Team,hitterproj.Opp))
    hitter_matchups_pp_dict = dict(zip(hitterproj.Team,hitterproj.OppSP))
    hitter_park_dict = dict(zip(hitterproj.Team,hitterproj.Park))
    hitterproj['Value'] = round(hitterproj['DKPts']/(hitterproj['Sal']/1000),2)
    h_vs_avg['Opp'] = h_vs_avg['Team'].map(hitter_matchups_dict)
    h_vs_avg['OppSP'] = h_vs_avg['Team'].map(hitter_matchups_pp_dict)
    
    st.markdown("<h3>Hitter Projections</h3>", unsafe_allow_html=True)
    st.markdown("Explore projected hitter performance for MLB games. Filter by slate, team, or position to customize your view.", unsafe_allow_html=True)
    col1,col2,col3,col4 = st.columns([1,1,1,1])
    with col1:
        checked = st.checkbox("Show Projection Highlights", value=False, key=None, help=None, on_change=None)
    with col2:
        checked2 = st.checkbox("Show Team Projections", value=False, key=None, help=None, on_change=None)
    with col3:
        main_slate_check = st.checkbox("Show Main Slate Only")
    
    if checked:
        st.markdown("<hr><h3>Top HR Projections</h3>",unsafe_allow_html=True)
        top_hr = h_vs_avg.sort_values(by='HR',ascending=False).head(5)
        
        top_hr['Opp'] = top_hr['Team'].map(hitter_matchups_dict)
        top_hr['OppSP'] = top_hr['Team'].map(hitter_matchups_pp_dict)
        top_hr['Park'] = top_hr['Team'].map(hitter_park_dict)
        top_hr = top_hr[['Hitter','Team','Opp','OppSP','Park','HR']]
        top_hr['ID'] = top_hr['Hitter'].map(hitter_name_id_dict)

        id_list = list(top_hr['ID'])
        name_list = list(top_hr['Hitter'])
        hr_list = list(top_hr['HR'])
        col1,col2,col3,col4,col5 = st.columns([1,1,1,1,1])
        imgwidth=100
        with col1:
            st.image(get_player_image(id_list[0]),width=imgwidth)
            st.markdown(f'{name_list[0]}: {hr_list[0]} HR')

        with col2:
            st.image(get_player_image(id_list[1]),width=imgwidth)
            st.markdown(f'{name_list[1]}: {hr_list[1]} HR')
        with col3:
            st.image(get_player_image(id_list[2]),width=imgwidth)
            st.markdown(f'{name_list[2]}: {hr_list[2]} HR')
        with col4:
            st.image(get_player_image(id_list[3]),width=imgwidth)
            st.markdown(f'{name_list[3]}: {hr_list[3]} HR')
        with col5:
            st.image(get_player_image(id_list[4]),width=imgwidth)
            st.markdown(f'{name_list[4]}: {hr_list[4]} HR')
        
        st.markdown("<hr><h3>Top HR Projections Over Average</h3>",unsafe_allow_html=True)
        top_hr = h_vs_avg.sort_values(by='HR Diff',ascending=False).head(5)
        
        top_hr['Opp'] = top_hr['Team'].map(hitter_matchups_dict)
        top_hr['OppSP'] = top_hr['Team'].map(hitter_matchups_pp_dict)
        top_hr['Park'] = top_hr['Team'].map(hitter_park_dict)
        top_hr = top_hr[['Hitter','Team','Opp','OppSP','Park','HR Diff']]
        top_hr['ID'] = top_hr['Hitter'].map(hitter_name_id_dict)

        id_list = list(top_hr['ID'])
        name_list = list(top_hr['Hitter'])
        hr_list = list(top_hr['HR Diff'])
        col1,col2,col3,col4,col5 = st.columns([1,1,1,1,1])
        with col1:
            st.image(get_player_image(id_list[0]),width=imgwidth)
            st.markdown(f'{name_list[0]}: +{hr_list[0]} HR')

        with col2:
            st.image(get_player_image(id_list[1]),width=imgwidth)
            st.markdown(f'{name_list[1]}: +{hr_list[1]} HR')
        with col3:
            st.image(get_player_image(id_list[2]),width=imgwidth)
            st.markdown(f'{name_list[2]}: +{hr_list[2]} HR')
        with col4:
            st.image(get_player_image(id_list[3]),width=imgwidth)
            st.markdown(f'{name_list[3]}: +{hr_list[3]} HR')
        with col5:
            st.image(get_player_image(id_list[4]),width=imgwidth)
            st.markdown(f'{name_list[4]}: +{hr_list[4]} HR')

        st.markdown("<h3>Biggest Fantasy Points Projected Boost", unsafe_allow_html=True)
        
        show_leaders = h_vs_avg.sort_values(by='DKPts Diff',ascending=False)
        show_leaders['Opp'] = show_leaders['Team'].map(hitter_matchups_dict)
        show_leaders['OppSP'] = show_leaders['Team'].map(hitter_matchups_pp_dict)
        show_leaders = show_leaders[['Hitter','Team','Opp','OppSP','DKPts','Avg DK Proj','DKPts Diff']].head(10)
        st.dataframe(show_leaders,hide_index=True)

    if checked2:
        st.markdown("<hr><h3>Team Projection Data</h3>",unsafe_allow_html=True)

        col1, col2 = st.columns([1,2])
        with col1:
            if main_slate_check:
                teamproj = hitterproj[hitterproj['MainSlate']=='Main'].groupby(['Team','Opp','OppSP'],as_index=False)[['DKPts','R','HR','SB']].sum()
                teamproj = teamproj.sort_values(by='DKPts',ascending=False)
                styled_df = teamproj.style.format({'DKPts': '{:.2f}', 'R': '{:.2f}', 'HR': '{:.2f}', 'SB': '{:.2f}'})                         
                st.dataframe(styled_df,hide_index=True)
            else:
                teamproj = hitterproj.groupby(['Team','Opp','OppSP'],as_index=False)[['DKPts','R','HR','SB']].sum()
                teamproj = teamproj.sort_values(by='DKPts',ascending=False)
                styled_df = teamproj.style.format({'DKPts': '{:.2f}', 'R': '{:.2f}', 'HR': '{:.2f}', 'SB': '{:.2f}'})                         
                st.dataframe(styled_df,hide_index=True)
        with col2:
            if main_slate_check:
                mainslateteams = list(hitterproj[hitterproj['MainSlate']=='Main']['Team'])
                team_v_avg = h_vs_avg[h_vs_avg['Team'].isin(mainslateteams)].groupby(['Team','Opp','OppSP'],as_index=False)[['HR','Avg HR Proj','DKPts','Avg DK Proj']].sum()
                team_v_avg.columns=['Team','Opp','OppSP','Today HR','Season HR','Today DK','Season DK']
                team_v_avg['Today HR Boost'] = round(team_v_avg['Today HR']/team_v_avg['Season HR'],3)
                team_v_avg['Today DK Boost'] = round(team_v_avg['Today DK']/team_v_avg['Season DK'],3)
                team_v_avg = team_v_avg.sort_values(by='Today DK Boost',ascending=False)

                styled_df = team_v_avg.style.format({'DKPts': '{:.2f}', 'R': '{:.2f}', 'HR': '{:.2f}', 'SB': '{:.2f}',
                                                    'Season HR': '{:.2f}', 'Today DK': '{:.2f}', 'Season DK': '{:.2f}',
                                                    'Today HR': '{:.2f}','Today HR Boost': '{:.1%}', 'Today DK Boost': '{:.2f}',
                                                    'Season DK': '{:.2f}'})                         
                st.dataframe(styled_df,hide_index=True)
            else:
                team_v_avg = h_vs_avg.groupby(['Team','Opp','OppSP'],as_index=False)[['HR','Avg HR Proj','DKPts','Avg DK Proj']].sum()
                team_v_avg.columns=['Team','Opp','OppSP','Today HR','Season HR','Today DK','Season DK']
                team_v_avg['Today HR Boost'] = round(team_v_avg['Today HR']/team_v_avg['Season HR'],3)
                team_v_avg['Today DK Boost'] = round(team_v_avg['Today DK']/team_v_avg['Season DK'],3)
                team_v_avg = team_v_avg.sort_values(by='Today DK Boost',ascending=False)

                styled_df = team_v_avg.style.format({'DKPts': '{:.2f}', 'R': '{:.2f}', 'HR': '{:.2f}', 'SB': '{:.2f}',
                                                    'Season HR': '{:.2f}', 'Today DK': '{:.2f}', 'Season DK': '{:.2f}',
                                                    'Today HR': '{:.2f}','Today HR Boost': '{:.1%}', 'Today DK Boost': '{:.2f}',
                                                    'Season DK': '{:.2f}'})                         
                st.dataframe(styled_df,hide_index=True)

    st.markdown("<hr><h1>Full Projections</h1>",unsafe_allow_html=True)
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
