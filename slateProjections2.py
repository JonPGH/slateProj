import streamlit as st
import pandas as pd, math
import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go


# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Define the correct password (replace with your desired password)
#st.markdown("<h1>Enter Password to Access Slate Analysis Tool",unsafe_allow_html=True)
CORRECT_PASSWORD = "hafner"
CORRECT_PASSWORD2 = '1'

# Function to check password
def check_password():
    def password_entered():
        if (st.session_state["password"] == CORRECT_PASSWORD) or (st.session_state["password"] == CORRECT_PASSWORD2):
            st.session_state.authenticated = True
            del st.session_state["password"]  # Clear password from session state
        else:
            st.error("Incorrect password. Please try again.")
    
    if not st.session_state.authenticated:
        st.text_input("Enter Password (new password in resource glossary 7/18/2025)", type="password", key="password", on_change=password_entered)
        return False
    return True

# Main app content (only displayed if authenticated)
if check_password():

    # Set page configuration
    st.set_page_config(page_title="MLB DW Slate Analysis Tool", layout="wide")

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
        ownershipdf = pd.read_csv(f'{file_path}/PlayerOwnershipReport.csv')
        allbets = pd.read_csv(f'{file_path}/AllBetValues.csv')
        alllines = pd.read_csv(f'{file_path}/AllBooksLines.csv')
        hitdb = pd.read_csv(f'{file_path}/hitdb2025.csv')
        pitdb = pd.read_csv(f'{file_path}/pitdb2025.csv')
        bat_hitters = pd.read_csv(f'{file_path}/bat_hitters.csv')
        bat_pitchers = pd.read_csv(f'{file_path}/bat_pitchers.csv')
        bet_tracker = pd.read_csv(f'{file_path}/bet_tracker.csv')
        base_sched = pd.read_csv(f'{file_path}/upcoming_schedule.csv')
        upcoming_proj = pd.read_csv(f'{file_path}/next10projections.csv')
        upcoming_p_scores = pd.read_csv(f'{file_path}/upcoming_p_schedule_scores.csv')
        mlbplayerinfo = pd.read_csv(f'{file_path}/mlbplayerinfo.csv')
        airpulldata = pd.read_csv(f'{file_path}/airpulldata.csv')
        trend_h = pd.read_csv(f'{file_path}/hot_hit_oe_data.csv')
        trend_p = pd.read_csv(f'{file_path}/hot_pit_ja_era.csv')
        upcoming_start_grades = pd.read_csv(f'{file_path}/upcoming_start_grades.csv')

        return logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, propsdf, gameinfo,h_vs_sim, bpreport, rpstats, hitterproj2,ownershipdf,allbets,alllines,hitdb,pitdb,bat_hitters,bat_pitchers,bet_tracker, base_sched, upcoming_proj, upcoming_p_scores, mlbplayerinfo, airpulldata, trend_p, trend_h, upcoming_start_grades

    color1='#FFBABA'
    color2='#FFCC99'
    color3='#FFFF99'
    color4='#CCFF99'
    color5='#99FF99'

    def applyColor_PitMatchups(val, column):
        if column == 'JA ERA':
            if val >= 4.5:
                return f'background-color: {color1}'
            elif val >= 3.75:
                return f'background-color: {color2}'
            elif val >= 3.25:
                return f'background-color: {color3}'
            elif val >= 2.5:
                return f'background-color: {color4}'
            elif val < 2.5:
                return f'background-color: {color5}'
        if column == 'JA ERA L20':
            if val >= 4.5:
                return f'background-color: {color1}'
            elif val >= 3.75:
                return f'background-color: {color2}'
            elif val >= 3.25:
                return f'background-color: {color3}'
            elif val >= 2.5:
                return f'background-color: {color4}'
            elif val < 2.5:
                return f'background-color: {color5}'
        if column == 'Hot Score':
            if val >= 1.25:
                return f'background-color: {color5}'
            elif val >= 1:
                return f'background-color: {color4}'
            elif val >= .5:
                return f'background-color: {color3}'
            elif val >= -.5:
                return f'background-color: {color2}'
            elif val < -.5:
                return f'background-color: {color1}'
    
    def applyColor_HitMatchups(val, column):
        if column == 'xwOBA OE':
            if val >= .05:
                return f'background-color: {color5}'
            elif val >= .025:
                return f'background-color: {color4}'
            elif val >= -.025:
                return f'background-color: {color3}'
            elif val >= -.05:
                return f'background-color: {color2}'
            elif val < -.05:
                return f'background-color: {color1}'
        if column == 'xwOBA OE L15':
            if val >= .05:
                return f'background-color: {color5}'
            elif val >= .025:
                return f'background-color: {color4}'
            elif val >= -.025:
                return f'background-color: {color3}'
            elif val >= -.05:
                return f'background-color: {color2}'
            elif val < -.05:
                return f'background-color: {color1}'
        if column == 'Hot Score':
            if val >= .1:
                return f'background-color: {color5}'
            elif val >= .05:
                return f'background-color: {color4}'
            elif val >= -.05:
                return f'background-color: {color3}'
            elif val >= -.1:
                return f'background-color: {color2}'
            elif val < -.1:
                return f'background-color: {color1}'
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
        if column == 'AVG':
            if val >= .3:
                return f'background-color: {color5}'
            elif val >= .28:
                return f'background-color: {color4}'
            elif val >= .26:
                return f'background-color: {color3}'
            elif val >= .24:
                return f'background-color: {color2}'
            elif val < .24:
                return f'background-color: {color1}'
        if column == 'SLG':
            if val >= .525:
                return f'background-color: {color5}'
            elif val >= .475:
                return f'background-color: {color4}'
            elif val >= .425:
                return f'background-color: {color3}'
            elif val >= .4:
                return f'background-color: {color2}'
            elif val < .4:
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
        if column == 'Hitter Air Pull / PA':
            if val >= .14:
                return f'background-color: {color5}'
            elif val >= .11:
                return f'background-color: {color4}'
            elif val >= .08:
                return f'background-color: {color3}'
            elif val >= .05:
                return f'background-color: {color2}'
            elif val < .05:
                return f'background-color: {color1}'
        
        if column == 'Pitcher Air Pull / PA':
            if val >= .14:
                return f'background-color: {color5}'
            elif val >= .11:
                return f'background-color: {color4}'
            elif val >= .08:
                return f'background-color: {color3}'
            elif val >= .05:
                return f'background-color: {color2}'
            elif val < .05:
                return f'background-color: {color1}'   
        if column == 'Average Air Pull':
            if val >= .14:
                return f'background-color: {color5}'
            elif val >= .11:
                return f'background-color: {color4}'
            elif val >= .08:
                return f'background-color: {color3}'
            elif val >= .05:
                return f'background-color: {color2}'
            elif val < .05:
                return f'background-color: {color1}'        
        if column == 'Hitter Air Pull / BIP':
            if val >= .2:
                return f'background-color: {color5}'
            elif val >= .17:
                return f'background-color: {color4}'
            elif val >= .13:
                return f'background-color: {color3}'
            elif val >= .1:
                return f'background-color: {color2}'
            elif val < .1:
                return f'background-color: {color1}'     
        if column == 'Pitcher Air Pull / BIP':
            if val >= .2:
                return f'background-color: {color5}'
            elif val >= .17:
                return f'background-color: {color4}'
            elif val >= .13:
                return f'background-color: {color3}'
            elif val >= .1:
                return f'background-color: {color2}'
            elif val < .1:
                return f'background-color: {color1}'        
        if column == 'PPA':
            if val >= 4:
                return f'background-color: {color1}'
            elif val >= 3.9:
                return f'background-color: {color2}'
            elif val >= 3.85:
                return f'background-color: {color3}'
            elif val >= 3.75:
                return f'background-color: {color4}'
            elif val < 3.75:
                return f'background-color: {color5}'
        
        if column == 'GB%':
            if val >= .55:
                return f'background-color: {color5}'
            elif val >= .5:
                return f'background-color: {color5}'
            elif val >= .45:
                return f'background-color: {color3}'
            elif val >= .4:
                return f'background-color: {color2}'
            elif val < .4:
                return f'background-color: {color1}'
        
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
    def applyColor_weatherumps(val, column):
        if column == 'Rain%':
            if val >= 75:
                return f'background-color:{color1}'
            elif val >= 50:
                return f'background-color:{color2}'
            elif val >= 30:
                return f'background-color:{color3}'
            elif val >= 10:
                return f'background-color:{color4}'
            elif val < 10:
                return f'background-color:{color5}'
        if column == 'K Boost':
            if val >= 1.05:
                return f'background-color:{color5}'
            elif val >= 1.02:
                return f'background-color:{color4}'
            elif val >= .98:
                return f'background-color:{color3}'
            elif val >= .96:
                return f'background-color:{color2}'
            elif val < .96:
                return f'background-color:{color1}'
        if column == 'BB Boost':
            if val >= 1.05:
                return f'background-color:{color5}'
            elif val >= 1.02:
                return f'background-color:{color4}'
            elif val >= .98:
                return f'background-color:{color3}'
            elif val >= .96:
                return f'background-color:{color2}'
            elif val < .96:
                return f'background-color:{color1}'
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
                return f'background-color: {color5}'
            elif val >= .3:
                return f'background-color: {color4}'
            elif val >= .25:
                return f'background-color: {color3}'
            elif val >= .2:
                return f'background-color: {color2}'
            elif val < .2:
                return f'background-color: {color1}'
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
            if val >= 11:
                return f'background-color: {color5}'
            elif val >= 9.5:
                return f'background-color: {color4}'
            elif val >= 7.5:
                return f'background-color: {color3}'
            elif val >= 6:
                return f'background-color: {color2}'
            elif val < 6:
                return f'background-color: {color1}'
        if column == 'Avg DK Proj':
            if val >= 11:
                return f'background-color: {color5}'
            elif val >= 9.5:
                return f'background-color: {color4}'
            elif val >= 7.5:
                return f'background-color: {color3}'
            elif val >= 6:
                return f'background-color: {color2}'
            elif val < 6:
                return f'background-color: {color1}'
        if column == 'HR Diff':
            if val >= .05:
                return f'background-color: {color5}'
            elif val >= .03:
                return f'background-color: {color4}'
            elif val >= 0.01:
                return f'background-color: {color3}'
            elif val >= -.03:
                return f'background-color: {color2}'
            elif val < -.03:
                return f'background-color: {color1}'
        if column == 'DKPts Diff':
            if val >= 1.5:
                return f'background-color: {color5}'
            elif val >= 1:
                return f'background-color: {color4}'
            elif val >= .5:
                return f'background-color: {color3}'
            elif val >= 0:
                return f'background-color: {color2}'
            elif val < 0:
                return f'background-color: {color1}'
        if column == 'Boost':
            if val >= 1.5:
                return f'background-color: {color5}'
            elif val >= 1:
                return f'background-color: {color4}'
            elif val >= .5:
                return f'background-color: {color3}'
            elif val >= 0:
                return f'background-color: {color2}'
            elif val < 0:
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
        if column == 'Avg HR Proj':
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
                return f'background-color: {color5}'
            elif val >= .15:
                return f'background-color: {color4}'
            elif val >= .1:
                return f'background-color: {color3}'
            elif val < .1:
                return f'background-color: {color2}'

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
    def color_cells_weatherumps(df_subset):
        return [applyColor_weatherumps(val, col) for val, col in zip(df_subset, df_subset.index)]
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
    def color_cells_PitMatchups(df_subset):
        return [applyColor_PitMatchups(val, col) for val, col in zip(df_subset, df_subset.index)]
    def color_cells_Props(df_subset):
        return [applyColor_Props(val, col) for val, col in zip(df_subset, df_subset.index)]

    # Load data
    logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, props_df, gameinfo, h_vs_sim,bpreport, rpstats, hitterproj2, ownershipdf,allbets,alllines,hitdb,pitdb,bat_hitters,bat_pitchers,bet_tracker, base_sched, upcoming_proj, upcoming_p_scores, mlbplayerinfo, airpulldata, trend_p, trend_h, upcoming_start_grades = load_data()

    hitdb = hitdb[(hitdb['level']=='MLB')&(hitdb['game_type']=='R')]
    pitdb = pitdb[(pitdb['level']=='MLB')&(pitdb['game_type']=='R')]
    if len(weather_data)<1:
        weather_data = pd.DataFrame()

    confirmed_lus = list(hitterproj2[hitterproj2['Confirmed LU']=='Y']['Team'].unique())

    last_update = pitcherproj['LastUpdate'].iloc[0]
    gameinfo['RoadTeam'] = np.where(gameinfo['team'] == gameinfo['Park'], gameinfo['opponent'], gameinfo['team'])
    gameinfo['GameString'] = gameinfo['RoadTeam']+'@'+gameinfo['Park']

    team_vs_sim = h_vs_sim[h_vs_sim['PC']>49].groupby('Team',as_index=False)[['xwOBA','SwStr%','AVG','SLG','Brl%','FB%']].mean()
    team_vs_sim['RawRank'] = len(team_vs_sim)-team_vs_sim['xwOBA'].rank()+1

    team_vs_sim['Rank'] = team_vs_sim['RawRank'].astype(int).astype(str) + '/' + str(len(team_vs_sim))

    games_df = pitcherproj[['Team', 'Opponent', 'HomeTeam']].drop_duplicates()
    games_df['RoadTeam'] = np.where(games_df['Team'] == games_df['HomeTeam'], games_df['Opponent'], games_df['Team'])
    games_df['GameString'] = games_df['RoadTeam'] + '@' + games_df['HomeTeam']
    games_df = games_df[['RoadTeam', 'HomeTeam', 'GameString']].drop_duplicates()
    hitterproj['RoadTeam'] = np.where(hitterproj['Team'] == 'HomeTeam', 'Opp', hitterproj['Team'])
    hitterproj['GameString'] = hitterproj['RoadTeam'] + '@' + hitterproj['Park']
    pitcherproj['RoadTeam'] = np.where(pitcherproj['Team'] == pitcherproj['HomeTeam'], pitcherproj['Opponent'], pitcherproj['Team'])
    pitcherproj['GameString'] = pitcherproj['RoadTeam'] + '@' + pitcherproj['HomeTeam']
    mainslateteams = list(hitterproj[hitterproj['MainSlate']=='Main']['Team'])
    main_slate_gamelist = list(pitcherproj[pitcherproj['MainSlate']=='Main']['GameString'])
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
    homer_boosts = list(h_vs_avg[(h_vs_avg['HR Diff']>=.03)&(h_vs_avg['HR']>=.1)]['Hitter'])

    #hitterproj['Hitter'] = np.where(hitterproj['ID'].isin(hot_hitters), hitterproj['Hitter'] + ' 🔥' ,hitterproj['Hitter'])
    #hitterproj['Hitter'] = np.where(hitterproj['ID'].isin(cold_hitters), hitterproj['Hitter'] + ' 🥶' ,hitterproj['Hitter'])
    hitterproj['Hot'] = np.where(hitterproj['ID'].isin(hot_hitters),'🔥','')
    hitterproj['Cold'] = np.where(hitterproj['ID'].isin(cold_hitters),'🥶','')
    hitterproj['HR Boost'] = np.where(hitterproj['Hitter'].isin(homer_boosts),'🚀','')
    hitterproj['Batter'] = hitterproj['Hitter'] + ' ' + hitterproj['Hot'] +' ' +  hitterproj['Cold'] + ' ' + hitterproj['HR Boost']
    #st.dataframe(hitterproj)

    #hitter_stats['Hitter'] = np.where(hitter_stats['ID'].isin(hot_hitters), hitter_stats['Hitter'] + ' 🔥' ,hitter_stats['Hitter'])
    #hitter_stats['Hitter'] = np.where(hitter_stats['ID'].isin(cold_hitters), hitter_stats['Hitter'] + ' 🥶' ,hitter_stats['Hitter'])
    hitter_stats['Hot'] = np.where(hitter_stats['ID'].isin(hot_hitters),'🔥','')
    hitter_stats['Cold'] = np.where(hitter_stats['ID'].isin(cold_hitters),'🥶','')
    hitter_stats['HR Boost'] = np.where(hitter_stats['Hitter'].isin(homer_boosts),'🚀','')
    hitter_stats['Batter'] = hitter_stats['Hitter'] + ' ' + hitter_stats['Hot'] +' ' +  hitter_stats['Cold'] + ' ' + hitter_stats['HR Boost']
    
    def get_player_image(player_id):
        return f'https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_426,q_auto:best/v1/people/{player_id}/headshot/67/current'

    # Sidebar navigation
    st.sidebar.image(logo, width=150)  # Added logo to sidebar
    st.sidebar.title("MLB Projections")
    tab = st.sidebar.radio("Select View", ["Game Previews", "Pitcher Projections", "Hitter Projections", "Matchups", "Player Trends","Air Pull Matchups", "Weather & Umps", "Streamers","Tableau", "DFS Optimizer","Prop Bets", "SP Planner"], help="Choose a view to analyze games or player projections.")
    if "reload" not in st.session_state:
        st.session_state.reload = False

    if st.sidebar.button("Reload Data"):
        st.session_state.reload = True
        st.cache_data.clear()  # Clear cache to force reload
        #logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, props_df, gameinfo, h_vs_sim = load_data()

    # Main content
    st.markdown(f"<center><h1>⚾ MLB DW Slate Analysis Tool ⚾</h1></center>", unsafe_allow_html=True)
    st.markdown(f"<center><i>Last projection update time: {last_update}est</center></i>",unsafe_allow_html=True)
    if tab == "Game Previews":
        #game_selection = list(games_df['GameString'])
        game_selection = list(gameinfo['GameString'].unique())
        selected_game = st.selectbox('Select a Game', game_selection, help="Select a game to view detailed projections and stats.")

        selected_home_team = selected_game.split('@')[1]
        selected_road_team = selected_game.split('@')[0]

        road_bullpen_team = bpreport[bpreport['Team']==selected_road_team]
        road_bullpen_rp = rpstats[rpstats['Team']==selected_road_team]

        home_bullpen_team = bpreport[bpreport['Team']==selected_home_team]
        home_bullpen_rp = rpstats[rpstats['Team']==selected_home_team]

        home_lineup_stats = lineup_stats[lineup_stats['Opp']==selected_home_team]
        road_lineup_stats = lineup_stats[lineup_stats['Opp']==selected_road_team]

        these_sim = h_vs_sim[h_vs_sim['Team'].isin([selected_home_team,selected_road_team])]

        this_game_ump = umpire_data[umpire_data['HomeTeam'] == selected_home_team]
        known_ump = 'Y' if len(this_game_ump) > 0 else 'N'

        these_pitcherproj = pitcherproj[pitcherproj['GameString'] == selected_game]
        try:
            this_weather = weather_data[weather_data['HomeTeam'] == selected_home_team]
            this_winds = this_weather['Winds'].iloc[0]
            this_winds = this_winds.replace(' mph','')
            this_winds = float(this_winds)
        except:
            this_winds = ''
        
        try:
            if this_weather['Rain%'].iloc[0]>25:
                rain_emoji = '🌧️'
            else:
                rain_emoji = ''
            if this_winds > 10:
                winds_emoji = '💨'
            else:
                winds_emoji = ''
        except:
            winds_emoji = ''
            rain_emoji = ''
        
        weather_emoji = rain_emoji + ' ' + winds_emoji
        try:
            game_name = this_weather['Game'].iloc[0]
        except:
            game_name = selected_game
        try:
            this_gameinfo = gameinfo[gameinfo['Park']==selected_home_team]
            this_gametime = this_gameinfo['game_time'].iloc[0]
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

        p_proj_cols = ['Sal', 'DKPts', 'Val', 'PC','IP', 'H', 'ER', 'SO', 'BB', 'W', 'Ownership']
        road_sp_projection = these_pitcherproj[these_pitcherproj['Pitcher'] == road_sp_name]
        home_sp_projection = these_pitcherproj[these_pitcherproj['Pitcher'] == home_sp_name]
        p_stats_cols = ['IP', 'K%', 'BB%', 'SwStr%', 'Ball%', 'xwOBA']
        road_sp_stats = pitcher_stats[pitcher_stats['Pitcher'] == road_sp_name]
        
        if len(road_sp_stats)>0:
            road_sp_hand = road_sp_stats['Hand'].iloc[0]
            is_road_p_hot = road_sp_stats['IsHot'].iloc[0]
            is_road_p_cold = road_sp_stats['IsCold'].iloc[0]
        else:
            road_sp_hand = 'R'
            is_road_p_hot = 0
            is_road_p_cold = 0
        if is_road_p_hot == 1:
            road_p_emoji = '🔥'
        elif is_road_p_cold == 1:
            road_p_emoji = '🥶'
        else:
            road_p_emoji = ''
        
        home_sp_stats = pitcher_stats[pitcher_stats['Pitcher'] == home_sp_name]
        
        if len(home_sp_stats)>0:
            home_sp_hand = home_sp_stats['Hand'].iloc[0]
            is_home_p_hot = home_sp_stats['IsHot'].iloc[0]
            is_home_p_cold = home_sp_stats['IsCold'].iloc[0]
        else:
            home_sp_hand = 'R'
            is_home_p_hot = 0
            is_home_p_cold = 0
        
        if is_home_p_hot == 1:
            home_p_emoji = '🔥'
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
            st.markdown(f"<center><h2>{game_name} {rain_emoji} </h2></center>", unsafe_allow_html=True)
            st.markdown(f"<center><h5>{road_sp_show_name} vs. {home_sp_show_name}</h5></center>", unsafe_allow_html=True)
            st.markdown(f"<center><h6><i>{this_gametime}</i></h6></center>", unsafe_allow_html=True)

            if game_info_fail == 'N':
                st.markdown(f"<center><h5>{this_favorite} ({this_favorite_odds}), O/U: {this_over_under}</h5></center>",unsafe_allow_html=True)
            
            try:
                weather_cond = this_weather['Conditions'].iloc[0]
                weather_temp = this_weather['Temp'].iloc[0]
            except:
                weather_cond = ''
                weather_temp = ''
            
            try:
                try:
                    weather_winds = this_weather['Winds'].iloc[0] + ' ' + this_weather['Wind Dir'].iloc[0]
                except:
                    weather_winds = this_weather.get('Winds', ['No Weather Data Found']).iloc[0]
            except:
                weather_winds = ''
            st.markdown(f"<center><b>{weather_emoji} Weather: {weather_cond}, {weather_temp}F<br>Winds: {weather_winds}</b></center>", unsafe_allow_html=True)
            if known_ump == 'Y':
                umpname = this_game_ump['Umpire'].iloc[0]
                k_boost = (this_game_ump['K Boost'].iloc[0] - 1) * 100
                k_symbol = '+' if k_boost > 0 else '' if k_boost == 0 else ''
                bb_boost = (this_game_ump['BB Boost'].iloc[0] - 1) * 100
                bb_symbol = '+' if bb_boost > 0 else '' if bb_boost == 0 else ''
                st.markdown(f"<center><b>Umpire: {umpname}<br>{k_symbol}{int(k_boost)}% K, {bb_symbol}{int(bb_boost)}% BB</b></center>", unsafe_allow_html=True)
            
            st.markdown("<br><center><font size=3>🔥 <i>= hot player</i>, 🥶 <i>= cold player</i>, 🚀 elevated HR proj</center></i></font>", unsafe_allow_html=True)
        
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
        col1, col2, col3 = st.columns([1,1,5])
        with col1:
            bp_checked = st.checkbox("Show Bullpens", value=False, key=None, help=None, on_change=None)
        with col2:
            lu_checked = st.checkbox("Show Lineup Stats", value=False, key=None, help=None, on_change=None)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<h4>{road_sp_name} Projection</h4>", unsafe_allow_html=True)
            filtered_pproj = road_sp_projection[p_proj_cols].rename({'Ownership': 'Own%'}, axis=1)
            styled_df = filtered_pproj.style.apply(
                color_cells_PitchProj, subset=['DKPts', 'Sal', 'Val','IP','H','ER','PC','SO','BB','W','Own%'], axis=1
            ).format({
                'Own%': '{:.0f}', 'Sal': '${:,.0f}', 'W': '{:.2f}', 'BB': '{:.2f}', 'PC': '{:.1f}',
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

            #lu_checked = st.checkbox("Show Lineup Stats", value=False, key=None, help=None, on_change=None)
            if lu_checked:
                ### lineup stuff
                home_lineup_stats = home_lineup_stats[['K%','BB%','Brl%','GB%','FB%','xwOBA','PPA']]
                st.markdown(f"<h4>{selected_home_team} Lineup Stats</h4>", unsafe_allow_html=True)
                styled_df = home_lineup_stats.style.apply(
                    color_cells_HitStat, subset=['K%', 'BB%', 'Brl%', 'GB%', 'FB%','PPA','xwOBA'], axis=1
                ).format({
                    'K%': '{:.1%}', 'BB%': '{:.1%}', 'GB%': '{:.1%}', 'FB%': '{:.1%}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}', 'PPA': '{:.3f}', 'IP': '{:.1f}'
                })
                st.dataframe(styled_df,hide_index=True,width=450)

        with col2:
            st.markdown(f"<h4>{home_sp_name} Projection</h4>", unsafe_allow_html=True)
            filtered_pproj = home_sp_projection[p_proj_cols].rename({'Ownership': 'Own%'}, axis=1)
            styled_df = filtered_pproj.style.apply(
                color_cells_PitchProj, subset=['DKPts', 'Sal','PC', 'Val','IP','H','ER','SO','BB','W','Own%'], axis=1
            ).format({
                'Own%': '{:.0f}', 'Sal': '${:,.0f}', 'W': '{:.2f}', 'BB': '{:.2f}', 'PC': '{:.0f}',
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

            if lu_checked:
                road_lineup_stats = road_lineup_stats[['K%','BB%','Brl%','GB%','FB%','xwOBA','PPA']]
                st.markdown(f"<h4>{selected_road_team} Lineup Stats</h4>", unsafe_allow_html=True)
                styled_df = road_lineup_stats.style.apply(
                    color_cells_HitStat, subset=['K%', 'BB%', 'Brl%', 'GB%', 'FB%','PPA','xwOBA'], axis=1
                ).format({
                    'K%': '{:.1%}', 'BB%': '{:.1%}', 'GB%': '{:.1%}', 'FB%': '{:.1%}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}', 'PPA': '{:.3f}', 'IP': '{:.1f}'
                })
                st.dataframe(styled_df,hide_index=True,width=450)

        
        # Bullpens
        #checked = st.checkbox("Show Bullpens", value=False, key=None, help=None, on_change=None)
        if bp_checked:
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
                options=["Team Matchup", "Best Matchups", "Projections","Projection vs. Avg", "Stats", "Splits", "Matchups", "Props"],
                index=0,
                help="Choose to view hitter projections, stats, or splits."
            )
        if option == "Team Matchup":
            col1, col2 = st.columns(2)
            with col1:
                road_team_matchups = team_vs_sim[team_vs_sim['Team']==selected_home_team]
                road_team_matchups = road_team_matchups[['Team','Rank','xwOBA','SwStr%','AVG','SLG','Brl%','FB%']]
                styled_df = road_team_matchups.style.apply(color_cells_HitMatchups, subset=['AVG','SLG','xwOBA','SwStr%','Brl%','FB%'], axis=1).format({'xwOBA': '{:.3f}',
                                                                                                            'xwOBA Con': '{:.3f}',
                                                                                                            'SwStr%': '{:.1%}', 'AVG':  '{:.3f}',
                                                                                                            'Brl%': '{:.1%}','SLG':  '{:.3f}',
                                                                                                            'FB%': '{:.1%}',
                                                                                                            'Hard%': '{:.1%}',})
                st.dataframe(styled_df, hide_index=True, use_container_width=True)
            
            with col2:
                home_team_matchups = team_vs_sim[team_vs_sim['Team']==selected_road_team]
                home_team_matchups = home_team_matchups[['Team','Rank','xwOBA','SwStr%','AVG','SLG','Brl%','FB%']]
                styled_df = home_team_matchups.style.apply(color_cells_HitMatchups, subset=['AVG','SLG','xwOBA','SwStr%','Brl%','FB%'], axis=1).format({'xwOBA': '{:.3f}',
                                                                                                            'xwOBA Con': '{:.3f}',
                                                                                                            'SwStr%': '{:.1%}', 'AVG':  '{:.3f}',
                                                                                                            'Brl%': '{:.1%}','SLG':  '{:.3f}',
                                                                                                            'FB%': '{:.1%}',
                                                                                                            'Hard%': '{:.1%}',})
                st.dataframe(styled_df, hide_index=True, use_container_width=True)

        if option == "Projection vs. Avg":
            luspotdict = dict(zip(hitterproj.Hitter,hitterproj.LU))
            h_vs_avg = h_vs_avg.drop(['Unnamed: 0'],axis=1)
            col1, col2 = st.columns(2)
            with col1:
                if selected_road_team in confirmed_lus:
                    lu_confirmation_string = 'Confirmed'
                else:
                    lu_confirmation_string = 'Not Confirmed'
                st.markdown(f"<h4>{selected_road_team} Lineup ({lu_confirmation_string})</h4>", unsafe_allow_html=True)
                road_projection_oa = h_vs_avg[h_vs_avg['Team'] == selected_road_team]
                road_projection_oa['Spot'] = road_projection_oa['Hitter'].map(luspotdict)
                road_projection_oa['Boost'] = road_projection_oa['DKPts']/road_projection_oa['Avg DK Proj']
                road_projection_oa = road_projection_oa[['Hitter','Spot','DKPts','Avg DK Proj','DKPts Diff','Boost']].sort_values(by='Spot')
                road_projection_oa = road_projection_oa.round(2)
                styled_df = road_projection_oa.style.apply(color_cells_HitProj, subset=['DKPts','Avg DK Proj','Boost'], axis=1).format({'DKPts': '{:.2f}', 'Avg DK Proj': '{:.2f}', 'DKPts Diff': '{:.2f}', 'Boost': '{:.2f}'})                         
                st.dataframe(styled_df,hide_index=True)
            with col2:
                if selected_home_team in confirmed_lus:
                    lu_confirmation_string = 'Confirmed'
                else:
                    lu_confirmation_string = 'Not Confirmed'
                st.markdown(f"<h4>{selected_home_team} Lineup ({lu_confirmation_string})</h4>", unsafe_allow_html=True)
                home_projection_oa = h_vs_avg[h_vs_avg['Team'] == selected_home_team]
                home_projection_oa['Spot'] = home_projection_oa['Hitter'].map(luspotdict)
                home_projection_oa['Boost'] = home_projection_oa['DKPts']/home_projection_oa['Avg DK Proj']
                home_projection_oa = home_projection_oa[['Hitter','Spot','DKPts','Avg DK Proj','DKPts Diff','Boost']].sort_values(by='Spot')
                home_projection_oa = home_projection_oa.round(2)
                styled_df = home_projection_oa.style.apply(color_cells_HitProj, subset=['DKPts','Avg DK Proj','Boost'], axis=1).format({'DKPts': '{:.2f}', 'Avg DK Proj': '{:.2f}', 'DKPts Diff': '{:.2f}', 'Boost': '{:.2f}'})                         
                st.dataframe(styled_df,hide_index=True)
                


        if option == 'Projections':
            avg_merge = h_vs_avg[['Hitter','DKPts Diff']]
            avg_merge.columns=['Batter','ProjOA']
            oa_look = dict(zip(avg_merge.Batter,avg_merge.ProjOA))
            col1, col2 = st.columns(2)
            hitter_proj_cols = ['Batter', 'Pos', 'LU', 'Sal', 'DKPts', 'HR', 'SB']
            with col1:
                if selected_road_team in confirmed_lus:
                    lu_confirmation_string = 'Confirmed'
                else:
                    lu_confirmation_string = 'Not Confirmed'
                st.markdown(f"<h4>{selected_road_team} Lineup ({lu_confirmation_string})</h4>", unsafe_allow_html=True)
                road_projection_data = hitterproj[hitterproj['Team'] == selected_road_team][hitter_proj_cols]
                styled_df = road_projection_data.style.apply(
                    color_cells_HitProj, subset=['DKPts', 'Sal', 'HR', 'SB'], axis=1
                ).format({
                    'DKPts': '{:.2f}', 'Value': '{:.2f}', 'Sal': '${:,.0f}',
                    'PA': '{:.1f}', 'R': '{:.2f}', 'HR': '{:.2f}', 'RBI': '{:.2f}', 'SB': '{:.2f}'
                })
                st.dataframe(styled_df, hide_index=True, use_container_width=True)
            with col2:
                if selected_road_team in confirmed_lus:
                    lu_confirmation_string = 'Confirmed'
                else:
                    lu_confirmation_string = 'Not Confirmed'
                st.markdown(f"<h4>{selected_home_team} Lineup ({lu_confirmation_string})</h4>", unsafe_allow_html=True)
                home_projection_data = hitterproj[hitterproj['Team'] == selected_home_team][hitter_proj_cols]
                styled_df = home_projection_data.style.apply(
                    color_cells_HitProj, subset=['DKPts',  'Sal', 'HR', 'SB'], axis=1
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
                    road_hitter_stats = road_hitter_stats[['Batter', 'PA', 'K%', 'BB%', 'Brl%', 'xwOBA', 'FB%']]
                    styled_df = road_hitter_stats.style.apply(
                        color_cells_HitStat, subset=['Brl%', 'FB%', 'K%', 'BB%', 'xwOBA'], axis=1
                    ).format({
                        'K%': '{:.1%}', 'BB%': '{:.1%}', 'FB%': '{:.1%}', 'PA': '{:.0f}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}'
                    })
                    st.dataframe(styled_df, hide_index=True, use_container_width=True)
                with col2:
                    st.markdown(f"<h4>{selected_home_team} Stats</h4>", unsafe_allow_html=True)
                    home_hitter_stats = home_hitter_stats[['Batter', 'PA', 'K%', 'BB%', 'Brl%', 'xwOBA', 'FB%']]
                    styled_df = home_hitter_stats.style.apply(
                        color_cells_HitStat, subset=['Brl%', 'FB%', 'K%', 'BB%', 'xwOBA'], axis=1
                    ).format({
                        'K%': '{:.1%}', 'BB%': '{:.1%}', 'FB%': '{:.1%}', 'PA': '{:.0f}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}'
                    })
                    st.dataframe(styled_df, hide_index=True, use_container_width=True)
            elif option == 'Splits':
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<h4>{selected_road_team} vs. {home_sp_hand}HP</h4>", unsafe_allow_html=True)
                    road_hitter_splits = road_hitter_stats[['Batter', 'Split PA', 'Split K%', 'Split BB%', 'Split Brl%', 'Split xwOBA', 'Split FB%']]
                    road_hitter_splits.columns = ['Hitter', 'PA', 'K%', 'BB%', 'Brl%', 'xwOBA', 'FB%']
                    styled_df = road_hitter_splits.style.apply(
                        color_cells_HitStat, subset=['Brl%', 'FB%', 'K%', 'BB%', 'xwOBA'], axis=1
                    ).format({
                        'K%': '{:.1%}', 'BB%': '{:.1%}', 'FB%': '{:.1%}', 'PA': '{:.0f}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}'
                    })
                    st.dataframe(styled_df, hide_index=True, use_container_width=True)
                with col2:
                    st.markdown(f"<h4>{selected_home_team} vs. {road_sp_hand}HP</h4>", unsafe_allow_html=True)
                    home_hitter_splits = home_hitter_stats[['Batter', 'Split PA', 'Split K%', 'Split BB%', 'Split Brl%', 'Split xwOBA', 'Split FB%']]
                    home_hitter_splits.columns = ['Hitter', 'PA', 'K%', 'BB%', 'Brl%', 'xwOBA', 'FB%']
                    styled_df = home_hitter_splits.style.apply(
                        color_cells_HitStat, subset=['Brl%', 'FB%', 'K%', 'BB%', 'xwOBA'], axis=1
                    ).format({
                        'K%': '{:.1%}', 'BB%': '{:.1%}', 'FB%': '{:.1%}', 'PA': '{:.0f}', 'Brl%': '{:.1%}', 'xwOBA': '{:.3f}'
                    })
                    st.dataframe(styled_df, hide_index=True, use_container_width=True)
        elif option == "Matchups":
            st.markdown(f"<b><i>Matchups is an algorithm that finds hitter stats against similar pitch movements as the ones they will see in this matchup</b></i>", unsafe_allow_html=True)
            col1, col2 = st.columns([1,1])
            with col1:
                road_sim = these_sim[these_sim['Team']==selected_road_team]
                #avg_matchup = road_sim[road_sim['PC']>99][['xwOBA','xwOBA Con','Brl%','FB%']].mean()
                #st.write(avg_matchup)
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
                road_sim = road_sim[(road_sim['xwOBA Con']>=.375)&(road_sim['SwStr%']<.11)&(road_sim['PC']>=50)]
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
                home_sim = home_sim[(home_sim['xwOBA Con']>=.375)&(home_sim['SwStr%']<.11)&(home_sim['PC']>=50)]
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
            game_props = game_props[(game_props['BetValue']>=.1)|((game_props['Type']=='batter_home_runs')&(game_props['BetValue']>=.05))]
            if len(game_props)>0:
                styled_df = game_props.style.apply(color_cells_Props, subset=['BetValue','Price'], axis=1).format({'BetValue': '{:.1%}',
                                                                                                                    'Price': '{:.0f}',
                                                                                                                    'Line': '{:.1f}'})
                st.dataframe(styled_df, hide_index=True, width=750)
            else:
                st.write('No recommended props for this game')

            #pitcher_props

    if tab == "Pitcher Projections":
        st.markdown("<h1><center>Pitcher Projections</center></h1>", unsafe_allow_html=True)
        #st.markdown(f"<center><i>Last projection update time: {last_update}est</center></i>",unsafe_allow_html=True)

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
                st.markdown(f'{name_list[0]}: +{round(hr_list[0],2)} HR')

            with col2:
                st.image(get_player_image(id_list[1]),width=imgwidth)
                st.markdown(f'{name_list[1]}: +{round(hr_list[1],2)} HR')
            with col3:
                st.image(get_player_image(id_list[2]),width=imgwidth)
                st.markdown(f'{name_list[2]}: +{round(hr_list[2],2)} HR')
            with col4:
                st.image(get_player_image(id_list[3]),width=imgwidth)
                st.markdown(f'{name_list[3]}: +{round(hr_list[3],2)} HR')
            with col5:
                st.image(get_player_image(id_list[4]),width=imgwidth)
                st.markdown(f'{name_list[4]}: +{round(hr_list[4],2)} HR')

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
                                                        'Today HR': '{:.2f}','Today HR Boost': '{:.1%}', 'Today DK Boost': '{:.1%}',
                                                        'Season DK': '{:.2f}'})                         
                    st.dataframe(styled_df,hide_index=True)

        st.markdown("<hr><h1>Full Projections</h1>",unsafe_allow_html=True)
        
        col1, col2 = st.columns([1,3])
        with col1:
            hproj_option = st.selectbox(
                label="What Type To Show",
                options=["Todays Projections", "Today vs. Season Avg"],
                index=0,
                help="Choose to view all games or only the main slate.",
                key="projtype")
                    
        if hproj_option == 'Todays Projections':
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
            show_hproj = show_hproj[['Batter', 'Pos', 'Team', 'Sal', 'Opp', 'Park', 'OppSP', 'LU', 'DKPts', 'Value', 'HR', 'SB', 'Floor', 'Ceil', 'Own%']]
            
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
        
        elif hproj_option == "Today vs. Season Avg":
            needed_proj_data = hitterproj[['Hitter','Sal','Pos']]
            h_vs_avg = pd.merge(h_vs_avg,needed_proj_data,on=['Hitter'])

            if main_slate_check:
                h_vs_avg = h_vs_avg[h_vs_avg['Team'].isin(mainslateteams)]
            else:
                pass
            team_options = ['All'] + list(h_vs_avg['Team'].unique())
            col1, col2, col3= st.columns([1,1,2])
            with col1:
                selected_team = st.selectbox('Select a Team', team_options)
            with col2:
                pos_filter = st.text_input(
                    label="Filter by Position",
                    placeholder="Enter position (e.g., OF, SS)",
                    help="Type a position to filter players (case-insensitive).",
                    key="pos_filter"
                )
            
            st.markdown("<h2>Fantasy Point Projection</h2>", unsafe_allow_html=True)
            if selected_team == 'All':
                filtered_havg = h_vs_avg.copy()
            else:
                filtered_havg = h_vs_avg[h_vs_avg['Team']==selected_team]
            
            if pos_filter:
                filtered_havg = filtered_havg[filtered_havg['Pos'].str.contains(pos_filter, case=False, na=False)]

            show_proj_df = filtered_havg[['Hitter','Team','Sal','Pos','Opp','OppSP','DKPts','Avg DK Proj','DKPts Diff']]
            styled_df = show_proj_df.style.apply(
                color_cells_HitProj, subset=['DKPts', 'Sal', 'Avg DK Proj','DKPts Diff'], axis=1).format({
                    'DKPts': '{:.2f}', 'Sal': '${:,.0f}',
                    'Avg DK Proj': '{:.2f}', 'DKPts Diff': '{:.2f}', })
            
            if len(show_proj_df)>20:
                st.dataframe(styled_df,hide_index=True,width=850,height=600)
            else:
                st.dataframe(styled_df,hide_index=True,width=850)
            
            show_proj_df_hr = filtered_havg[['Hitter','Team','Pos','Opp','OppSP','HR','Avg HR Proj','HR Diff']]
            show_proj_df_hr = show_proj_df_hr.sort_values(by='HR Diff',ascending=False)
            styled_df_hr = show_proj_df_hr.style.apply(
                color_cells_HitProj, subset=['HR', 'Avg HR Proj','HR Diff'], axis=1).format({
                    'HR': '{:.2f}',
                    'Avg HR Proj': '{:.2f}', 'HR Diff': '{:.2f}', })
            
            st.markdown("<h2>Home Run Projection</h2>", unsafe_allow_html=True)
            if len(show_proj_df)>20:
                st.dataframe(styled_df_hr,hide_index=True,width=850,height=600)
            else:
                st.dataframe(styled_df_hr,hide_index=True,width=850)

    if tab == "Matchups":

        st.markdown("<h2><center><br>Matchups Model</h2></center>", unsafe_allow_html=True)

        if st.checkbox("Show Team Ranks"):
            
            st.markdown("<h2>Team Matchups</h2>", unsafe_allow_html=True)

            if st.checkbox("Main Slate Only"):
                show_team_vs_sim = team_vs_sim[team_vs_sim['Team'].isin(mainslateteams)].sort_values(by='RawRank')
                show_team_vs_sim = show_team_vs_sim.drop(['Rank'],axis=1)

                show_team_vs_sim = show_team_vs_sim.rename({'RawRank': 'Rank'},axis=1)

                team_styled_df = show_team_vs_sim.style.apply(color_cells_HitMatchups, subset=['xwOBA', 'AVG', 'SLG',
                                                                                'SwStr%','Brl%','FB%'], axis=1).format({
                    'xwOBA': '{:.3f}', 'xwOBA Con': '{:.3f}','AVG': '{:.3f}',
                    'SwStr%': '{:.1%}', 'Brl%': '{:.1%}', 'SLG': '{:.3f}',
                    'FB%': '{:.1%}', 'Hard%': '{:.1%}', 'Rank': '{:.0f}'
                })
                st.dataframe(team_styled_df, hide_index=True, width=600, height=560)
            else:       
                show_team_vs_sim = team_vs_sim.sort_values(by='RawRank')
                show_team_vs_sim = show_team_vs_sim.drop(['Rank'],axis=1)

                show_team_vs_sim = show_team_vs_sim.rename({'RawRank': 'Rank'},axis=1)

                team_styled_df = show_team_vs_sim.style.apply(color_cells_HitMatchups, subset=['xwOBA', 'AVG', 'SLG',
                                                                                'SwStr%','Brl%','FB%'], axis=1).format({
                    'xwOBA': '{:.3f}', 'xwOBA Con': '{:.3f}','AVG': '{:.3f}',
                    'SwStr%': '{:.1%}', 'Brl%': '{:.1%}', 'SLG': '{:.3f}',
                    'FB%': '{:.1%}', 'Hard%': '{:.1%}', 'Rank': '{:.0f}'
                })
                st.dataframe(team_styled_df, hide_index=True, width=600, height=560)
            
        
        team_options = ['All'] + list(h_vs_sim['Team'].unique())
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_team = st.selectbox('Filter by Team', team_options)

        # Create a single row for sliders
        col_pc, col_xwoba, col_swstr, col_brl = st.columns(4)
        with col_pc:
            pc_min = int(h_vs_sim['PC'].min())
            pc_max = int(h_vs_sim['PC'].max())
            pc_range = st.slider('PC Range', pc_min, pc_max, (pc_min, pc_max))
        with col_xwoba:
            xwoba_min = float(h_vs_sim['xwOBA'].min())
            xwoba_max = float(h_vs_sim['xwOBA'].max())
            xwoba_range = st.slider('xwOBA Range', xwoba_min, xwoba_max, (xwoba_min, xwoba_max), step=0.001)
        with col_swstr:
            swstr_min = float(h_vs_sim['SwStr%'].min())
            swstr_max = float(h_vs_sim['SwStr%'].max())
            swstr_range = st.slider('SwStr% Range', swstr_min, swstr_max, (swstr_min, swstr_max), step=0.001)
        with col_brl:
            brl_min = float(h_vs_sim['Brl%'].min())
            brl_max = float(h_vs_sim['Brl%'].max())
            brl_range = st.slider('Brl% Range', brl_min, brl_max, (brl_min, brl_max), step=0.001)

        # Filter data based on team and slider values
        if selected_team == 'All':
            show_hsim = h_vs_sim[
                (h_vs_sim['PC'].between(pc_range[0], pc_range[1])) &
                (h_vs_sim['xwOBA'].between(xwoba_range[0], xwoba_range[1])) &
                (h_vs_sim['SwStr%'].between(swstr_range[0], swstr_range[1])) &
                (h_vs_sim['Brl%'].between(brl_range[0], brl_range[1]))
            ][['Hitter','Team','OppSP','PC','BIP','xwOBA','xwOBA Con','SwStr%','Brl%','FB%','Hard%']]
        else:
            show_hsim = h_vs_sim[
                (h_vs_sim['Team'] == selected_team) &
                (h_vs_sim['PC'].between(pc_range[0], pc_range[1])) &
                (h_vs_sim['xwOBA'].between(xwoba_range[0], xwoba_range[1])) &
                (h_vs_sim['SwStr%'].between(swstr_range[0], swstr_range[1])) &
                (h_vs_sim['Brl%'].between(brl_range[0], brl_range[1]))
            ][['Hitter','Team','OppSP','PC','BIP','xwOBA','xwOBA Con','SwStr%','Brl%','FB%','Hard%']]

        styled_df = show_hsim.style.apply(color_cells_HitMatchups, subset=['xwOBA','xwOBA Con',
                                                                        'SwStr%','Brl%','FB%',
                                                                        'Hard%'], axis=1).format({
            'xwOBA': '{:.3f}', 'xwOBA Con': '{:.3f}',
            'SwStr%': '{:.1%}', 'Brl%': '{:.1%}',
            'FB%': '{:.1%}', 'Hard%': '{:.1%}'
        })

        if len(show_hsim) > 9:
            st.dataframe(styled_df, hide_index=True, use_container_width=True, height=900)
        else:
            st.dataframe(styled_df, hide_index=True, use_container_width=True)
  
    if tab == "Player Trends":
        st.markdown("<h1><center>Player Trends</center></h1>", unsafe_allow_html=True)

        col1,col2,col3 = st.columns([3,1,3])
        with col2:
            h_p_selection = st.selectbox('Select',['Hitters','Pitchers'])
        
        if h_p_selection == 'Hitters':

            st.markdown('<b><center><i>Determined by comparing xwOBA over expectation from the last 15 days with what each hitter did before these last 15 days', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<h3><center>🔥 Hottest Hitters 🔥</center></h3>", unsafe_allow_html=True)

                hot_five_ids = trend_h.sort_values(by='Hot Score',ascending=False).head(5)['batter'].unique()
                xcol1,xcol2,xcol3 = st.columns(3)
                picture_width = 105
                with xcol1:
                    st.image(get_player_image(hot_five_ids[0]), width=picture_width)
                with xcol2:
                    st.image(get_player_image(hot_five_ids[1]), width=picture_width)
                with xcol3:
                    st.image(get_player_image(hot_five_ids[2]), width=picture_width)

                hot_five_h = trend_h.sort_values(by='Hot Score',ascending=False).head(10)[['BatterName','xwOBA OE','xwOBA OE L15','Hot Score']]
                styled_hot_five = hot_five_h.style.apply(color_cells_HitMatchups, subset=['xwOBA OE','xwOBA OE L15','Hot Score'], axis=1).format({'xwOBA OE': '{:.3f}', 'xwOBA OE L15': '{:.3f}', 'Hot Score': '{:.3f}'})
                st.dataframe(styled_hot_five, hide_index=True, width=600)
            with col2:
                st.markdown("<h3><center>🧊 Coldest Hitters 🧊</center></h3>", unsafe_allow_html=True)

                cold_five_ids = trend_h.sort_values(by='Hot Score',ascending=True).head(5)['batter'].unique()
                zcol1,zcol2,zcol3 = st.columns(3)
                
                with zcol1:
                    st.image(get_player_image(cold_five_ids[0]), width=picture_width)
                with zcol2:
                    st.image(get_player_image(cold_five_ids[1]), width=picture_width)
                with zcol3:
                    st.image(get_player_image(cold_five_ids[2]), width=picture_width)
                
                col_five_h = trend_h.sort_values(by='Hot Score',ascending=True).head(10)[['BatterName','xwOBA OE','xwOBA OE L15','Hot Score']]
                styled_cold_five = col_five_h.style.apply(color_cells_HitMatchups, subset=['xwOBA OE','xwOBA OE L15','Hot Score'], axis=1).format({'xwOBA OE': '{:.3f}', 'xwOBA OE L15': '{:.3f}', 'Hot Score': '{:.3f}'})
                st.dataframe(styled_cold_five, hide_index=True, width=600)

            st.markdown("<h3><center>Full Table</center></h3>", unsafe_allow_html=True)
            
            bcol1,bcol2,bcol3 = st.columns([1,3,1])
            with bcol2:
                all_trend_h = trend_h.sort_values(by='Hot Score',ascending=False)[['BatterName','xwOBA OE','xwOBA OE L15','Hot Score']]
                styled_all_trend_h = all_trend_h.style.apply(color_cells_HitMatchups, subset=['xwOBA OE','xwOBA OE L15','Hot Score'], axis=1).format({'xwOBA OE': '{:.3f}', 'xwOBA OE L15': '{:.3f}', 'Hot Score': '{:.3f}'})
                st.dataframe(styled_all_trend_h, hide_index=True, width=700,height=900)


        elif h_p_selection == 'Pitchers':
            st.markdown('<b><center><i>Determined by comparing JA ERA the last 20 days with what each pitcher did before these last 20 days', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<h3><center>🔥 Hottest Pitchers 🔥</center></h3>", unsafe_allow_html=True)

                hot_five_ids = trend_p.sort_values(by='Hot Score',ascending=False).head(5)['pitcher'].unique()

                xcol1,xcol2,xcol3 = st.columns(3)
                picture_width = 105
                with xcol1:
                    st.image(get_player_image(hot_five_ids[0]), width=picture_width)
                with xcol2:
                    st.image(get_player_image(hot_five_ids[1]), width=picture_width)
                with xcol3:
                    st.image(get_player_image(hot_five_ids[2]), width=picture_width)
                
                hot_five_p = trend_p.sort_values(by='Hot Score',ascending=False).head(10)[['player_name','JA ERA','JA ERA L20','Hot Score']]
                styled_hot_five = hot_five_p.style.apply(color_cells_PitMatchups, subset=['JA ERA','JA ERA L20','Hot Score'], axis=1).format({'JA ERA': '{:.2f}', 'JA ERA L20': '{:.2f}', 'Hot Score': '{:.2f}'})
                st.dataframe(styled_hot_five, hide_index=True, width=600)
        
            with col2:
                st.markdown("<h3><center>🧊 Coldest Pitchers 🧊</center></h3>", unsafe_allow_html=True)

                cold_five_ids = trend_p.sort_values(by='Hot Score',ascending=True).head(5)['pitcher'].unique()

                xcol1,xcol2,xcol3 = st.columns(3)
                picture_width = 105
                with xcol1:
                    st.image(get_player_image(cold_five_ids[0]), width=picture_width)
                with xcol2:
                    st.image(get_player_image(cold_five_ids[1]), width=picture_width)
                with xcol3:
                    st.image(get_player_image(cold_five_ids[2]), width=picture_width)
                
                cold_five_p = trend_p.sort_values(by='Hot Score',ascending=True).head(10)[['player_name','JA ERA','JA ERA L20','Hot Score']]
                styled_cold_five = cold_five_p.style.apply(color_cells_PitMatchups, subset=['JA ERA','JA ERA L20','Hot Score'], axis=1).format({'JA ERA': '{:.2f}', 'JA ERA L20': '{:.2f}', 'Hot Score': '{:.2f}'})
                st.dataframe(styled_cold_five, hide_index=True, width=600)

            st.markdown("<h3><center>Full Table</center></h3>", unsafe_allow_html=True)

            todays_pitchers = list(pitcherproj['Pitcher'])
            today_box = st.checkbox('Show Only Today SP?')
            if today_box:                
                ccol1,ccol2,ccol3 = st.columns([1,3,1])
                with ccol2:
                    all_trend_p = trend_p[trend_p['player_name'].isin(todays_pitchers)].sort_values(by='Hot Score',ascending=False)[['player_name','JA ERA','JA ERA L20','Hot Score']]
                    styled_all_trend_p = all_trend_p.style.apply(color_cells_HitMatchups, subset=['JA ERA','JA ERA L20','Hot Score'], axis=1).format({'JA ERA': '{:.2f}', 'JA ERA L20': '{:.2f}', 'Hot Score': '{:.2f}'})
                    st.dataframe(styled_all_trend_p, hide_index=True, width=700,height=810)
            else:
                bcol1,bcol2,bcol3 = st.columns([1,3,1])
                with bcol2:
                    all_trend_p = trend_p.sort_values(by='Hot Score',ascending=False)[['player_name','JA ERA','JA ERA L20','Hot Score']]
                    styled_all_trend_p = all_trend_p.style.apply(color_cells_HitMatchups, subset=['JA ERA','JA ERA L20','Hot Score'], axis=1).format({'JA ERA': '{:.2f}', 'JA ERA L20': '{:.2f}', 'Hot Score': '{:.2f}'})
                    st.dataframe(styled_all_trend_p, hide_index=True, width=700,height=900)

    if tab == "Air Pull Matchups":

        st.markdown("<h2><center><br>Air Pull Matchups</h2></center>", unsafe_allow_html=True)

        #st.write(airpulldata)
        hitters_ap = airpulldata[airpulldata['Sample']=='Hitters'][['BatterName','PA_flag','IsBIP','Air Pull / PA', 'Air Pull / BIP']]
        hitters_ap = hitters_ap.rename({'PA_flag':'Hitter PA', 'BatterName':'Hitter', 'IsBIP': 'Hitter BIP', 'Air Pull / PA': 'Hitter Air Pull / PA', 'Air Pull / BIP': 'Hitter Air Pull / BIP'},axis=1)
        
        pitchers_ap = airpulldata[airpulldata['Sample']=='Pitchers'][['player_name','IsBIP', 'PA_flag','Air Pull / PA', 'Air Pull / BIP']]
        pitchers_ap = pitchers_ap.rename({'PA_flag':'Pitcher PA', 'player_name':'Pitcher',  'IsBIP': 'Pitcher BIP','Air Pull / PA': 'Pitcher Air Pull / PA', 'Air Pull / BIP': 'Pitcher Air Pull / BIP'},axis=1)
        
        todays_matchups = hitterproj2[['Hitter','OppSP']]
        todays_matchups.columns=['Hitter','Pitcher']

        merge1 = pd.merge(todays_matchups,hitters_ap, how='left', on='Hitter')
        merge2 = pd.merge(merge1,pitchers_ap, how='left', on='Pitcher')

        col1, col2 = st.columns([1,5])
        with col1:
            option = st.radio('Select Stat Type', options=['Per PA','Per BIP'], horizontal=True)
        
        if option == 'Per PA':
            show_data = merge2[['Hitter','Pitcher','Hitter PA','Pitcher PA','Hitter Air Pull / PA','Pitcher Air Pull / PA']]

            show_data['Average Air Pull'] = (show_data['Hitter Air Pull / PA'] + show_data['Pitcher Air Pull / PA'])/2
            min_pa = 10
            max_h_pa = int(show_data['Hitter PA'].max()) if not show_data['Hitter PA'].empty else min_pa
            max_p_pa = int(show_data['Pitcher PA'].max()) if not show_data['Pitcher PA'].empty else min_pa
            max_pa = max(max_h_pa, max_p_pa)

            col1, col2 = st.columns([1,3])
            with col1:
               pa_filter = st.slider("Filter by Plate Appearances (PA):",min_value=min_pa,max_value=max_pa,value=(min_pa, max_pa), step=1)

            filtered_df = show_data[(show_data['Hitter PA']>pa_filter[0])&(show_data['Pitcher PA']>pa_filter[0])].sort_values(by='Average Air Pull',ascending=False)

            styled_df = filtered_df.style.apply(
                    color_cells_HitStat, subset=['Hitter Air Pull / PA','Pitcher Air Pull / PA','Average Air Pull'], axis=1
                ).format({'Hitter Air Pull / PA': '{:.1%}','Pitcher Air Pull / PA': '{:.1%}','Average Air Pull': '{:.1%}',
                'Hitter PA': '{:.0f}','Pitcher PA': '{:.0f}'})

            st.dataframe(styled_df, hide_index=True, width=850,height=750)
        
        elif option == 'Per BIP':
            show_data = merge2[['Hitter','Pitcher','Hitter BIP','Pitcher BIP','Hitter Air Pull / BIP','Pitcher Air Pull / BIP']]
            show_data['Average Air Pull'] = (show_data['Hitter Air Pull / BIP'] + show_data['Pitcher Air Pull / BIP'])/2

            min_bip = 50
            max_h_bip = int(show_data['Hitter BIP'].max()) if not show_data['Hitter BIP'].empty else min_pa
            max_p_bip = int(show_data['Pitcher BIP'].max()) if not show_data['Pitcher BIP'].empty else min_pa
            max_bip = max(max_h_bip, max_p_bip)

            col1, col2 = st.columns([1,3])
            with col1:
               bip_filter = st.slider("Filter by Balls In Play (BIP):",min_value=min_bip,max_value=max_bip,value=(min_bip, max_bip), step=1)
            
            filtered_df = show_data[(show_data['Hitter BIP']>bip_filter[0])&(show_data['Pitcher BIP']>bip_filter[0])].sort_values(by='Average Air Pull',ascending=False)

            styled_df = filtered_df.style.apply(
                    color_cells_HitStat, subset=['Hitter Air Pull / BIP','Pitcher Air Pull / BIP','Average Air Pull'], axis=1
                ).format({'Hitter Air Pull / BIP': '{:.1%}','Pitcher Air Pull / BIP': '{:.1%}','Average Air Pull': '{:.1%}',
                'Hitter BIP': '{:.0f}','Pitcher BIP': '{:.0f}'})

            st.dataframe(styled_df, hide_index=True,height=750)
    
    if tab == "Weather & Umps":
        weather_show = weather_data[['HomeTeam','Game','Conditions','Temp','Winds','Wind Dir','Rain%']].sort_values(by='Rain%',ascending=False)
        weather_show = pd.merge(weather_show,umpire_data, how='left', on='HomeTeam')
        weather_show = weather_show[['Game','Conditions','Temp','Winds','Wind Dir','Rain%','Umpire','K Boost','BB Boost']]
        styled_df = weather_show.style.apply(
                color_cells_weatherumps, subset=['Rain%','K Boost','BB Boost'], axis=1).format({'K Boost': '{:.2f}','BB Boost': '{:.2f}'}) 
        st.dataframe(styled_df,hide_index=True,width=900,height=700)
    
    if tab == "Streamers":
        ownershipdict = dict(zip(ownershipdf.Player, ownershipdf.Yahoo))

        # hitters or pitchers select
        h_or_p = st.selectbox(options=['Pitchers','Hitters'],label='Select Hitters or Pitchers')
        pitcherproj['Ownership'] = pitcherproj['Pitcher'].map(ownershipdict)

        hitterproj['Hitter'] = hitterproj['Hitter'].str.replace('🔥','').str.strip()
        hitterproj['Hitter'] = hitterproj['Hitter'].str.replace('🥶','').str.strip()
        hitterproj['Ownership'] = hitterproj['Hitter'].map(ownershipdict)

        if h_or_p == 'Hitters':
            show_hitters = hitterproj.copy()
            show_hitters['H'] = show_hitters['1B']+show_hitters['2B']+show_hitters['3B']+show_hitters['HR']
            show_hitters = show_hitters[['Hitter','Pos','Team','Opp','OppSP','Park','Ownership','LU','DKPts','PA','H','R','HR','RBI','SB','1B','2B','3B']]
            
            # Add a slider for Ownership percentage
            col1, col2 = st.columns([1,7])
            with col1:
                ownership_filter = st.slider("Filter by Ownership %", min_value=0, max_value=100, value=(0, 100))
            
            with col2:
                # Filter DataFrame based on slider values
                show_hitters = show_hitters[
                    (show_hitters['Ownership'] >= ownership_filter[0]) & 
                    (show_hitters['Ownership'] <= ownership_filter[1])
                ]
                
                show_hitters = show_hitters.sort_values(by='DKPts', ascending=False)
                #st.dataframe(show_pitchers, hide_index=True, width=850, height=600)

                styled_df = show_hitters.style.apply(
                        color_cells_HitProj, subset=['DKPts','HR','SB'], axis=1
                    ).format({
                        'DKPts': '{:.2f}','PA': '{:.2f}', 
                        'R': '{:.2f}', 'Sal': '${:,.0f}', 
                        'PC': '{:.0f}', 'HR': '{:.2f}', 
                        'H': '{:.2f}', 'RBI': '{:.2f}', 
                        'Ownership': '{:.0f}',
                        'SB': '{:.2f}', 'BB': '{:.2f}', 
                        '1B': '{:.2f}', '2B': '{:.2f}', 
                        '3B': '{:.2f}'
                    }).set_table_styles([
                        {'selector': 'th', 'props': [('text-align', 'left'), ('font-weight', 'bold')]},
                        {'selector': 'td', 'props': [('text-align', 'left')]}
                    ])
                st.dataframe(styled_df, hide_index=True, height=600)
        elif h_or_p == 'Pitchers':
            show_pitchers = pitcherproj.copy()
            show_pitchers = show_pitchers[['Pitcher','Team','Opponent','HomeTeam','Ownership','DKPts','PC','IP','H','ER','SO','BB','W']]
            
            # Add a slider for Ownership percentage
            col1, col2 = st.columns([1,6])
            with col1:
                ownership_filter = st.slider("Filter by Ownership %", min_value=0, max_value=100, value=(0, 100))
            
            with col2:
                # Filter DataFrame based on slider values
                show_pitchers = show_pitchers[
                    (show_pitchers['Ownership'] >= ownership_filter[0]) & 
                    (show_pitchers['Ownership'] <= ownership_filter[1])
                ]
                
                show_pitchers = show_pitchers.sort_values(by='DKPts', ascending=False)
                #st.dataframe(show_pitchers, hide_index=True, width=850, height=600)

                styled_df = show_pitchers.style.apply(
                        color_cells_PitchProj, subset=['DKPts','SO','W','Ownership','BB','PC','IP'], axis=1
                    ).format({
                        'DKPts': '{:.2f}','FDPts': '{:.2f}', 
                        'Val': '{:.2f}', 'Sal': '${:,.0f}', 
                        'PC': '{:.0f}', 'IP': '{:.2f}', 
                        'H': '{:.2f}', 'ER': '{:.2f}', 
                        'Ownership': '{:.0f}',
                        'SO': '{:.2f}', 'BB': '{:.2f}', 
                        'W': '{:.2f}', 'Floor': '{:.2f}', 
                        'Ceil': '{:.2f}', 'Own%': '{:.0f}'
                    }).set_table_styles([
                        {'selector': 'th', 'props': [('text-align', 'left'), ('font-weight', 'bold')]},
                        {'selector': 'td', 'props': [('text-align', 'left')]}
                    ])
                st.dataframe(styled_df, hide_index=True, width=950, height=600)
    
    if tab == "Tableau":
        tableau_choice = st.selectbox(options=['Main','MLB & MiLB Stats'],label='Choose dashboard to display')
        if tableau_choice == 'Main':
            #st.markdown("<h2><center>Main MLB Dashboard</center></h2>", unsafe_allow_html=True)
            st.markdown("<i><center><a href='https://public.tableau.com/app/profile/jon.anderson4212/viz/JonPGHMLB2025Dashboard/Hitters'>Click here to visit full thing</i></a></center>", unsafe_allow_html=True)
            tableau_code_pitchers = """
            <div class='tableauPlaceholder' id='viz1745234354780' style='position: relative'><noscript><a href='#'><img alt=' ' src='https:&#47;&#47;public.tableau.com&#47;static&#47;images&#47;Jo&#47;JonPGHMLB2025Dashboard&#47;Pitchers&#47;1_rss.png' style='border: none' /></a></noscript><object class='tableauViz'  style='display:none;'><param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' /> <param name='embed_code_version' value='3' /> <param name='site_root' value='' /><param name='name' value='JonPGHMLB2025Dashboard&#47;Pitchers' /><param name='tabs' value='yes' /><param name='toolbar' value='yes' /><param name='static_image' value='https:&#47;&#47;public.tableau.com&#47;static&#47;images&#47;Jo&#47;JonPGHMLB2025Dashboard&#47;Pitchers&#47;1.png' /> <param name='animate_transition' value='yes' /><param name='display_static_image' value='yes' /><param name='display_spinner' value='yes' /><param name='display_overlay' value='yes' /><param name='display_count' value='yes' /><param name='language' value='en-US' /></object></div>                <script type='text/javascript'>                    var divElement = document.getElementById('viz1745234354780');                    var vizElement = divElement.getElementsByTagName('object')[0];                    if ( divElement.offsetWidth > 800 ) { vizElement.style.width='1400px';vizElement.style.height='1250px';} else if ( divElement.offsetWidth > 500 ) { vizElement.style.width='1400px';vizElement.style.height='1250px';} else { vizElement.style.width='100%';vizElement.style.height='2350px';}                     var scriptElement = document.createElement('script');                    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';                    vizElement.parentNode.insertBefore(scriptElement, vizElement);                </script>    
            """ 
            components.html(tableau_code_pitchers, height=750, scrolling=True)
        elif tableau_choice == 'MLB & MiLB Stats':
            #st.markdown("<h2><center>Main MLB Dashboard</center></h2>", unsafe_allow_html=True)
            st.markdown("<i><center><a href='https://public.tableau.com/app/profile/jon.anderson4212/viz/MLBMiLBStatsDashboardv3/Hitters-Main#1'>Click here to visit full thing</i></a></center>", unsafe_allow_html=True)
            tableau_code_pitchers = """
            <div class='tableauPlaceholder' id='viz1745237361320' style='position: relative'><noscript><a href='#'><img alt=' ' src='https:&#47;&#47;public.tableau.com&#47;static&#47;images&#47;ML&#47;MLBMiLBStatsDashboardv3&#47;Hitters-Main&#47;1_rss.png' style='border: none' /></a></noscript><object class='tableauViz'  style='display:none;'><param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' /> <param name='embed_code_version' value='3' /> <param name='site_root' value='' /><param name='name' value='MLBMiLBStatsDashboardv3&#47;Hitters-Main' /><param name='tabs' value='yes' /><param name='toolbar' value='yes' /><param name='static_image' value='https:&#47;&#47;public.tableau.com&#47;static&#47;images&#47;ML&#47;MLBMiLBStatsDashboardv3&#47;Hitters-Main&#47;1.png' /> <param name='animate_transition' value='yes' /><param name='display_static_image' value='yes' /><param name='display_spinner' value='yes' /><param name='display_overlay' value='yes' /><param name='display_count' value='yes' /><param name='language' value='en-US' /></object></div>                <script type='text/javascript'>                    var divElement = document.getElementById('viz1745237361320');                    var vizElement = divElement.getElementsByTagName('object')[0];                    if ( divElement.offsetWidth > 800 ) { vizElement.style.width='1400px';vizElement.style.height='850px';} else if ( divElement.offsetWidth > 500 ) { vizElement.style.width='1400px';vizElement.style.height='850px';} else { vizElement.style.width='100%';vizElement.style.height='1800px';}                     var scriptElement = document.createElement('script');                    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';                    vizElement.parentNode.insertBefore(scriptElement, vizElement);                </script>
            """ 
            components.html(tableau_code_pitchers, height=750, scrolling=True)

    if tab == "DFS Optimizer":

        import pulp
        import warnings
        warnings.filterwarnings("ignore")

        # Streamlit app
        st.title("DraftKings MLB DFS Optimizer")
        st.markdown("""
                    There is nothing special about this optimizer, and it doesn't
                    let you export the lineups so they can be used, but it will at 
                    least give you a feel for what kind of lineup the model likes.<hr>
                    """, unsafe_allow_html=True)

        # Read data
        try:
            hitters = hitterproj.copy()
            pitchers = pitcherproj.copy()
        except FileNotFoundError:
            st.error("CSV files not found. Please ensure 'Tableau_DailyHitterProj.csv' and 'Tableau_DailyPitcherProj.csv' are in the same directory as the script.")
            st.stop()

        # main slate filter
        hitters = hitters[hitters['MainSlate']=='Main']
        pitchers = pitchers[pitchers['MainSlate']=='Main']
        
        # Handle multi-position eligibility for hitters
        hitters['Pos'] = hitters['Pos'].str.split('/')
        hitters = hitters.explode('Pos')

        # Combine hitters and pitchers
        hitters['Type'] = 'Hitter'
        pitchers['Type'] = 'Pitcher'

        # Rename columns for consistency
        hitters = hitters.rename(columns={'Hitter': 'Name', 'Sal': 'Salary', 'DKPts': 'Points', 'Team': 'Team'})
        pitchers = pitchers.rename(columns={'Pitcher': 'Name', 'Sal': 'Salary', 'DKPts': 'Points', 'Team': 'Team'})

        # Select relevant columns
        hitters = hitters[['Name', 'Pos', 'Team', 'Salary', 'Points', 'Type']]
        pitchers = pitchers[['Name', 'Team', 'Salary', 'Points', 'Type']]

        # Assign pitcher position
        pitchers['Pos'] = 'P'

        # Combine data
        players = pd.concat([hitters, pitchers], ignore_index=True)

        # Clean data
        players = players.dropna(subset=['Name', 'Pos', 'Team', 'Salary', 'Points'])
        players['Salary'] = players['Salary'].astype(float)
        players['Points'] = players['Points'].astype(float)

        # DraftKings MLB DFS rules
        SALARY_CAP = 50000
        ROSTER_SIZE = 10
        POSITIONS = {
            'P': 2,
            'C': 1,
            '1B': 1,
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'OF': 3
        }

        # Define display order for positions
        POSITION_ORDER = ['P', 'P', 'C', '1B', '2B', 'SS', '3B', 'OF', 'OF', 'OF']
        POSITION_INDEX = {pos: i for i, pos in enumerate(['P', 'C', '1B', '2B', 'SS', '3B', 'OF'])}

        # Streamlit inputs
        col1,col2,col3 = st.columns([1,1,1])
        with col1:
            projection_variance = st.slider("Projection Variance (%)", min_value=0, max_value=50, value=10, step=5) / 100
        with col2:
            num_lineups = st.number_input("Number of Lineups to Generate", min_value=1, max_value=20, value=5, step=1)
        with col3:
            max_exposure = st.slider("Maximum Player Exposure (%)", min_value=10, max_value=100, value=50, step=10) / 100

        # Optimizer function
        def optimize_lineup(players, player_usage, max_usage, used_lineups):
            # Initialize PuLP problem
            prob = pulp.LpProblem("DFS_Optimizer", pulp.LpMaximize)

            # Decision variables
            player_vars = pulp.LpVariable.dicts("Player", players.index, cat='Binary')

            # Objective: Maximize projected points
            prob += pulp.lpSum([players.loc[i, 'Points'] * player_vars[i] for i in players.index])

            # Constraints
            # 1. Salary cap
            prob += pulp.lpSum([players.loc[i, 'Salary'] * player_vars[i] for i in players.index]) <= SALARY_CAP

            # 2. Roster size
            prob += pulp.lpSum([player_vars[i] for i in players.index]) == ROSTER_SIZE

            # 3. Positional constraints
            for pos, count in POSITIONS.items():
                prob += pulp.lpSum([player_vars[i] for i in players.index if players.loc[i, 'Pos'] == pos]) == count

            # 4. Max exposure constraint
            for idx in players.index:
                player_name = players.loc[idx, 'Name']
                if player_name in player_usage and player_usage[player_name] >= max_usage:
                    prob += player_vars[idx] == 0

            # 5. Exclude previously used lineups
            for lineup_indices in used_lineups:
                # Prevent the exact same combination of players
                prob += pulp.lpSum([player_vars[i] for i in lineup_indices]) <= ROSTER_SIZE - 1

            # Solve
            prob.solve()

            # Extract results
            lineup = []
            if pulp.LpStatus[prob.status] == 'Optimal':
                for i in players.index:
                    if player_vars[i].varValue == 1:
                        lineup.append(players.loc[i])
                lineup_df = pd.DataFrame(lineup)
                total_points = sum(players.loc[i, 'Points'] for i in players.index if player_vars[i].varValue == 1)
                total_salary = sum(players.loc[i, 'Salary'] for i in players.index if player_vars[i].varValue == 1)
                selected_indices = [i for i in players.index if player_vars[i].varValue == 1]
                return lineup_df, total_points, total_salary, selected_indices
            else:
                return None, 0, 0, []

        # Function to sort lineup by position order
        def sort_lineup(lineup_df):
            # Create a sorting key based on POSITION_ORDER
            def get_sort_key(row):
                pos = row['Pos']
                if pos == 'P':
                    # Assign first or second P based on order
                    p_count = sum(1 for r in lineup_df['Pos'][:row.name] if r == 'P')
                    return POSITION_ORDER.index('P') + p_count / 10
                elif pos == 'OF':
                    # Assign OF positions based on order
                    of_count = sum(1 for r in lineup_df['Pos'][:row.name] if r == 'OF')
                    return POSITION_ORDER.index('OF') + of_count / 10
                else:
                    return POSITION_ORDER.index(pos)
            
            lineup_df = lineup_df.copy()
            lineup_df['SortKey'] = lineup_df.apply(get_sort_key, axis=1)
            sorted_lineup = lineup_df.sort_values('SortKey').drop(columns=['SortKey'])
            return sorted_lineup

        # Generate multiple lineups
        if st.button("Generate Lineups"):
            all_lineups = []
            player_usage = {}  # Track how many times each player has been used
            used_lineups = []  # Track indices of players in each lineup
            max_usage = max_exposure * num_lineups  # Convert percentage to number of lineups

            for lineup_num in range(int(num_lineups)):
                # Apply random variance to projections
                players['Points'] = players['Points'] * np.random.uniform(1 - projection_variance, 1 + projection_variance, size=len(players))

                # Optimize lineup with max exposure and unique lineup constraints
                lineup_df, total_points, total_salary, selected_indices = optimize_lineup(players, player_usage, max_usage, used_lineups)

                if lineup_df is not None:
                    # Sort lineup by position order
                    lineup_df = sort_lineup(lineup_df)
                    all_lineups.append({
                        'Lineup Number': lineup_num + 1,
                        'Lineup': lineup_df[['Name', 'Pos', 'Team', 'Salary', 'Points']],
                        'Total Points': total_points,
                        'Total Salary': total_salary,
                        'Teams': lineup_df['Team'].nunique()
                    })
                    # Update player usage and used lineups
                    for idx in selected_indices:
                        player_name = players.loc[idx, 'Name']
                        player_usage[player_name] = player_usage.get(player_name, 0) + 1
                    used_lineups.append(selected_indices)
                else:
                    st.warning(f"Could not generate lineup {lineup_num + 1}. Check constraints or data.")
                    break

            # Display lineups side-by-side
            if all_lineups:
                st.subheader("Generated Lineups")
                # Create columns for lineups (up to num_lineups)
                cols = st.columns(len(all_lineups))
                for idx, lineup_info in enumerate(all_lineups):
                    with cols[idx]:
                        st.write(f"**Lineup {lineup_info['Lineup Number']}**")
                        st.dataframe(lineup_info['Lineup'], hide_index=True)
                        st.write(f"**Total Projected Points**: {lineup_info['Total Points']:.2f}")
                        st.write(f"**Total Salary**: ${lineup_info['Total Salary']:,.2f}")
                        st.write(f"**Teams Represented**: {lineup_info['Teams']}")

                # Player ownership report
                st.subheader("Player Ownership Report")
                ownership_data = []
                for player_name, count in player_usage.items():
                    ownership_pct = (count / len(all_lineups)) * 100
                    player_info = players[players['Name'] == player_name].iloc[0]
                    ownership_data.append({
                        'Name': player_name,
                        'Position': player_info['Pos'],
                        'Team': player_info['Team'],
                        'Ownership (%)': ownership_pct
                    })
                ownership_df = pd.DataFrame(ownership_data).sort_values(by='Ownership (%)', ascending=False)
                st.dataframe(ownership_df, hide_index=True)

        # Display raw data (optional)
        if st.checkbox("Show Raw Player Data"):
            st.subheader("Player Projections")
            st.dataframe(players, hide_index=True)

    ## move this later
    def create_speed_gauge(value, min_value=0.05, max_value=0.30):
        fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={'projection': 'polar'})

        # Normalize value to angle (0 to 180 degrees for gauge)
        range_value = max_value - min_value
        normalized_value = (value - min_value) / range_value
        angle = normalized_value * 180
        angle_rad = np.deg2rad(180 - angle)  # Convert to radians, adjust for gauge orientation

        # Create background arc
        theta = np.linspace(np.pi, 0, 100)  # 180-degree arc
        ax.fill_between(theta, 0, range_value, color='lightgray', alpha=0.3)

        # Create colored gauge arc based on value
        gauge_theta = np.linspace(np.pi, np.pi - angle_rad, 50)
        ax.fill_between(gauge_theta, 0, range_value, color='limegreen', alpha=0.7)

        # Plot needle
        needle_length = range_value * 0.9
        ax.plot([np.pi - angle_rad, np.pi - angle_rad], [0, needle_length], color='red', lw=3)

        # Customize gauge
        ax.set_ylim(0, range_value * 1.1)  # Extend slightly beyond max for aesthetics
        ax.set_xticks([])  # Hide angular ticks
        ax.set_yticks([])  # Hide radial ticks
        ax.spines['polar'].set_visible(False)  # Hide polar spine
        ax.grid(False)  # Hide grid

        # Add value label at the bottom
        ax.text(np.pi / 2, -range_value * 0.2, f'{value:.2f}', fontsize=20, ha='center', va='center', color='black')

        # Style
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        return fig


    def plot_bet_value_compare(bet_projodds, bet_lineodds, title="Implied Odds Comparison"):
        labels = ['JA Model', 'Betting Line']
        values = [bet_projodds, bet_lineodds]

        # Create horizontal bar chart
        fig = go.Figure(
            data=[
                go.Bar(
                    y=labels,
                    x=values,
                    orientation='h',
                    marker=dict(color=['#e74c3c', '#3498db']),  # Red, Blue, Green
                    text=[f"{v:.2f}" for v in values],  # Display values on bars
                    textposition='auto',
                )
            ]
        )

        # Customize layout
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=18, family="Arial", color="#2c3e50"),
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="Value",
            yaxis_title="",
            height=300,
            margin=dict(l=10, r=10, t=50, b=10),
            showlegend=False,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(family="Arial", size=12, color="#2c3e50"),
            yaxis=dict(automargin=True),
            xaxis=dict(gridcolor="#ecf0f1"),
        )

        # Display the chart in Streamlit
        #st.plotly_chart(fig, use_container_width=True)
        return(fig)

    def plot_bet_projections(bet_line, bet_proj, bat_proj, title="Bet and Projection Comparison"):
        # Data for the bar chart
        labels = ['Bet Line', 'JA Model Projection', 'The Bat X Projection']
        values = [bet_line, bet_proj, bat_proj]

        # Create horizontal bar chart
        fig = go.Figure(
            data=[
                go.Bar(
                    y=labels,
                    x=values,
                    orientation='h',
                    marker=dict(color=['#e74c3c', '#3498db', '#2ecc71']),  # Red, Blue, Green
                    text=[f"{v:.2f}" for v in values],  # Display values on bars
                    textposition='auto',
                )
            ]
        )

        # Customize layout
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=18, family="Arial", color="#2c3e50"),
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="Value",
            yaxis_title="",
            height=300,
            margin=dict(l=10, r=10, t=50, b=10),
            showlegend=False,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(family="Arial", size=12, color="#2c3e50"),
            yaxis=dict(automargin=True),
            xaxis=dict(gridcolor="#ecf0f1"),
        )

        # Display the chart in Streamlit
        #st.plotly_chart(fig, use_container_width=True)
        return(fig)
    
    def plotWalks(df,line):
        playername = df['Player'].iloc[0]
        df["Date"] = pd.to_datetime(df["Date"])

        # Create a line graph using Plotly
        fig = px.line(
            df,
            x="Date",
            y="BB",
            title=f"Walks by Start for {playername}",
            markers=True,  # Add markers for each data point
            text="BB",  # Show opponent labels on the points
        )
        
            # Add horizontal line using the 'line' variable
        fig.add_hline(
            y=line,
            line_dash="solid",
            line_color="red",
            line_width=2,
            annotation_text=f"{line}",
            annotation_position="top right"
            )
        
        # Customize the layout for a nicer look
        fig.update_traces(
            line=dict(color="#1f77b4", width=2.5),  # Blue line with a decent thickness
            marker=dict(size=10),  # Larger markers
            textposition="top center",  # Position opponent labels above the points
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Walks",
            xaxis=dict(
                tickformat="%b %d",  # Format dates as "Mar 31", "Apr 06", etc.
                tickangle=45,  # Rotate x-axis labels for better readability
            ),
            yaxis=dict(
                range=[-0.5, 5],  # Set y-axis range with a little padding
                dtick=1,  # Step of 1 for y-axis ticks
            ),
            title=dict(
                x=0.5,  # Center the title
                font=dict(size=20),
            ),
            showlegend=False,  # No legend needed for a single line
            plot_bgcolor="white",  # White background for the plot
            paper_bgcolor="white",  # White background for the entire figure
            font=dict(size=12),
        )

        return(fig)
    
    def plotStrikeouts(df,line):
        playername = df['Player'].iloc[0]
        df["Date"] = pd.to_datetime(df["Date"])

        df_max = np.max(df['SO']) + 2

        # Create a line graph using Plotly
        fig = px.line(
            df,
            x="Date",
            y="SO",
            title=f"Strikeouts by Start for {playername}",
            markers=True,  # Add markers for each data point
            text="SO",  # Show opponent labels on the points
        )
        
            # Add horizontal line using the 'line' variable
        fig.add_hline(
            y=line,
            line_dash="solid",
            line_color="red",
            line_width=2,
            annotation_text=f"{line}",
            annotation_position="top right"
            )
        
        # Customize the layout for a nicer look
        fig.update_traces(
            line=dict(color="#1f77b4", width=2.5),  # Blue line with a decent thickness
            marker=dict(size=10),  # Larger markers
            textposition="top center",  # Position opponent labels above the points
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Strikeouts",
            xaxis=dict(
                tickformat="%b %d",  # Format dates as "Mar 31", "Apr 06", etc.
                tickangle=45,  # Rotate x-axis labels for better readability
            ),
            yaxis=dict(
                range=[-0.5, df_max],  # Set y-axis range with a little padding
                dtick=1,  # Step of 1 for y-axis ticks
            ),
            title=dict(
                x=0.5,  # Center the title
                font=dict(size=20),
            ),
            showlegend=False,  # No legend needed for a single line
            plot_bgcolor="white",  # White background for the plot
            paper_bgcolor="white",  # White background for the entire figure
            font=dict(size=12),
        )

        return(fig)

    if tab == "Prop Bets":
        st.markdown("<hr><h4>This page is still a work in progress</h4><hr>",unsafe_allow_html=True)


        rec_bets = allbets.head(10)#[allbets['Recommended']=='Y']

        #st.dataframe(rec_bets)
        rec_bets['BetFullName'] = rec_bets['Player'] + ' :: ' + rec_bets['Type'] + ' :: ' + rec_bets['OU'].astype(str) + ' ' + rec_bets['Line'].astype(str)

        col1, col2 = st.columns([1,4])
        with col1:
            bet_select = list(rec_bets['BetFullName'].unique())
        
            selected_bet = st.selectbox('Select a Bet', bet_select, help="Select a bet to view details.")
        
        show_bet_details = rec_bets[rec_bets['BetFullName']==selected_bet]

        bet_player = show_bet_details['Player'].iloc[0]
        bet_market = show_bet_details['Type'].iloc[0]
        if bet_market == 'pitcher_strikeouts':
            bet_market_show = 'Strikeouts'
        elif bet_market == 'pitcher_walks':
            bet_market_show = 'Walks'
        elif bet_market == 'batter_walks':
            bet_market_show = 'Walks'
        elif bet_market == 'pitcher_outs':
            bet_market_show = 'Outs Recorded'
        elif bet_market == 'batter_hits':
            bet_market_show = 'Hits'
        bet_line = show_bet_details['Line'].iloc[0]
        bet_book = show_bet_details['Book'].iloc[0]
        bet_price = show_bet_details['Price'].iloc[0]
        bet_proj = show_bet_details['Projection'].iloc[0]
        bet_ou = show_bet_details['OU'].iloc[0]
        bet_lineodds = show_bet_details['LineOdds'].iloc[0]
        bet_projodds = show_bet_details['ProjOdds'].iloc[0]
        bet_value = show_bet_details['BetValue'].iloc[0]
        bet_value = round(bet_value,3)
        bet_value_show = round(show_bet_details['BetValue'].iloc[0]*100,3)

        with col2:
            st.markdown(f"<h2><center>{bet_player} {bet_ou} {bet_line} {bet_market_show} ({bet_price} on {bet_book})</center>", unsafe_allow_html=True)
        
        if bet_market == 'pitcher_walks':
            show_db = pitdb[pitdb['Player']==bet_player][['Player','team_abbrev','game_date','opp_abbrev','GS','IP','BFP','BB']]
            show_db['BB%'] = round(show_db['BB']/show_db['BFP'],3)
            show_db.columns=['Player','Team','Date','Opp','GS','IP','TBF','BB','BB%']
            show_db = show_db.sort_values(by='Date',ascending=False)

            ## hit rate ##
            start_count = np.sum(show_db['GS'])
            if bet_ou == 'Over':
                bet_hit_count = (len(show_db[(show_db['BB']>bet_line)&(show_db['GS']==1)]))
                print_ou = 'over'
            if bet_ou == 'Under':
                bet_hit_count = (len(show_db[(show_db['BB']<bet_line)&(show_db['GS']==1)]))
                print_ou = 'under'
            bet_hit_rate = round(bet_hit_count/start_count,3)*100


            bat_proj = bat_pitchers[bat_pitchers['PLAYER']==bet_player]['BB'].iloc[0]

            last_three_dates = show_db['Date'].unique()[0:3]
            last3db = show_db[show_db['Date'].isin(last_three_dates)]

            col1, col2, col3 = st.columns([1,3,3])
            
            with col1:
                st.markdown(f"""<div style="text-align: center; font-family: 'Impact', sans-serif;">
                        <span style="font-size: 25px; color: black; text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">Bet Value</span>
                        <span style="font-size: 25px; color: black;">&nbsp;</span>
                        <span style="font-size: 75px; color: #e74c3c; text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">{bet_value_show}%</span>
                    </div>
                    <div style="text-align: center; font-family: 'Impact', sans-serif;">
                        <span style="font-size: 25px; color: black; text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">Bet Hit Rate</span>
                        <span style="font-size: 25px; color: black;">&nbsp;</span>
                        <span style="font-size: 75px; color: #e74c3c; text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">{round(bet_hit_rate,3)}%</span>
                    </div>
                """, unsafe_allow_html=True)
                
            
            with col2:
                
                fig1 = plot_bet_projections(bet_line, bet_proj, bat_proj, title="Bet and Projection Comparison")
                st.plotly_chart(fig1, use_container_width=True)

            with col3:
                fig2 = plot_bet_value_compare(bet_projodds, bet_lineodds, title="Implied Odds Comparison")
                st.plotly_chart(fig2, use_container_width=True)
            st.markdown(f"<br><br>",unsafe_allow_html=True)

            line_plot = plotWalks(show_db,bet_line)        
            col1, col2 = st.columns([1,4])
                
            with col1:
                similar_bets = bet_tracker[(bet_tracker['Bet Type']=='Walks')&(bet_tracker['Bet']==bet_ou)&(bet_tracker['Bet Value']>bet_value-.035)&(bet_tracker['Bet Value']<bet_value+.035)]
                similar_bet_count = len(similar_bets)
                similar_bet_winners = np.sum(similar_bets['Winner?'])
                similar_bet_profit = round(np.sum(similar_bets['Profit']),2)
                similar_bet_roi = round(similar_bet_profit/similar_bet_count,3)*100
                similar_bet_roi = round(similar_bet_roi,1) - 100
                st.markdown(f"""
                    <div style="text-align: center; font-family: 'Impact', sans-serif; padding: 20px;">
                        <div style="margin-bottom: 5px;">
                            <span style="font-size: 30px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">Similar Bets Analysis</span>
                            <span style="font-size: 20px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">Bets Recommended</span>
                            <span style="font-size: 20px; color: black;">&nbsp;</span>
                            <span style="font-size: 40px; color: #e74c3c; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{similar_bet_count}</span>
                        </div>
                        <div style="margin-bottom: 5px;">
                            <span style="font-size: 20px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">Winners</span>
                            <span style="font-size: 2px; color: black;">&nbsp;</span>
                            <span style="font-size: 40px; color: #e74c3c; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{similar_bet_winners}</span>
                        </div>
                        <div style="margin-bottom: 5px;">
                            <span style="font-size: 20px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">Unit Profit</span>
                            <span style="font-size: 20px; color: black;">&nbsp;</span>
                            <span style="font-size: 40px; color: #e74c3c; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{similar_bet_profit}</span>
                        </div>
                        <div>
                            <span style="font-size: 25px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">ROI</span>
                            <span style="font-size: 25px; color: black;">&nbsp;</span>
                            <span style="font-size: 50px; color: #e74c3c; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{similar_bet_roi}%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                #st.dataframe(similar_bets, hide_index=True) 
            with col2:
                st.markdown(f"""
                    <div style="text-align: center; font-family: 'Arial', sans-serif; font-size: 25px; color:rgb(0, 0, 0); text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">
                    {bet_player} has gone {print_ou} {bet_line} walks in {bet_hit_count} of {start_count} starts
                    </div>
                    """, unsafe_allow_html=True)
                st.plotly_chart(line_plot, use_container_width=False,width=50)
        
        if bet_market == 'pitcher_strikeouts':
            show_db = pitdb[pitdb['Player']==bet_player][['Player','team_abbrev','game_date','opp_abbrev','GS','IP','BFP','SO']]
            show_db['K%'] = round(show_db['SO']/show_db['BFP'],3)
            show_db.columns=['Player','Team','Date','Opp','GS','IP','TBF','SO','K%']
            show_db = show_db.sort_values(by='Date',ascending=False)

            ## hit rate ##
            start_count = np.sum(show_db['GS'])
            if bet_ou == 'Over':
                bet_hit_count = (len(show_db[(show_db['SO']>bet_line)&(show_db['GS']==1)]))
                print_ou = 'over'
            if bet_ou == 'Under':
                bet_hit_count = (len(show_db[(show_db['SO']<bet_line)&(show_db['GS']==1)]))
                print_ou = 'under'
            bet_hit_rate = round(bet_hit_count/start_count,3)*100

            bat_proj = bat_pitchers[bat_pitchers['PLAYER']==bet_player]['K'].iloc[0]

            last_three_dates = show_db['Date'].unique()[0:3]
            last3db = show_db[show_db['Date'].isin(last_three_dates)]

            col1, col2, col3 = st.columns([1,3,3])
            
            with col1:
                st.markdown(f"""<div style="text-align: center; font-family: 'Impact', sans-serif;">
                        <span style="font-size: 25px; color: black; text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">Bet Value</span>
                        <span style="font-size: 25px; color: black;">&nbsp;</span>
                        <span style="font-size: 75px; color: #e74c3c; text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">{bet_value_show}%</span>
                    </div>
                    <div style="text-align: center; font-family: 'Impact', sans-serif;">
                        <span style="font-size: 25px; color: black; text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">Bet Hit Rate</span>
                        <span style="font-size: 25px; color: black;">&nbsp;</span>
                        <span style="font-size: 75px; color: #e74c3c; text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">{round(bet_hit_rate,3)}%</span>
                    </div>
                """, unsafe_allow_html=True)
                
            
            with col2:
                
                fig1 = plot_bet_projections(bet_line, bet_proj, bat_proj, title="Bet and Projection Comparison")
                st.plotly_chart(fig1, use_container_width=True)

            with col3:
                fig2 = plot_bet_value_compare(bet_projodds, bet_lineodds, title="Implied Odds Comparison")
                st.plotly_chart(fig2, use_container_width=True)
            st.markdown(f"<br><br>",unsafe_allow_html=True)

            line_plot = plotStrikeouts(show_db,bet_line)       
            col1, col2 = st.columns([1,4])
                
            with col1:
                similar_bets = bet_tracker[(bet_tracker['Bet Type']=='Strikeouts')&(bet_tracker['Bet']==bet_ou)&(bet_tracker['Bet Value']>bet_value-.035)&(bet_tracker['Bet Value']<bet_value+.035)]
                similar_bet_count = len(similar_bets)
                similar_bet_winners = np.sum(similar_bets['Winner?'])
                similar_bet_profit = round(np.sum(similar_bets['Profit']),2)
                similar_bet_roi = round(similar_bet_profit/similar_bet_count,3)*100
                similar_bet_roi = round(similar_bet_roi,1) - 100
                st.markdown(f"""
                    <div style="text-align: center; font-family: 'Impact', sans-serif; padding: 20px;">
                        <div style="margin-bottom: 5px;">
                            <span style="font-size: 30px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">Similar Bets Analysis</span>
                            <span style="font-size: 20px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">Bets Recommended</span>
                            <span style="font-size: 20px; color: black;">&nbsp;</span>
                            <span style="font-size: 40px; color: #e74c3c; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{similar_bet_count}</span>
                        </div>
                        <div style="margin-bottom: 5px;">
                            <span style="font-size: 20px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">Winners</span>
                            <span style="font-size: 2px; color: black;">&nbsp;</span>
                            <span style="font-size: 40px; color: #e74c3c; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{similar_bet_winners}</span>
                        </div>
                        <div style="margin-bottom: 5px;">
                            <span style="font-size: 20px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">Unit Profit</span>
                            <span style="font-size: 20px; color: black;">&nbsp;</span>
                            <span style="font-size: 40px; color: #e74c3c; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{similar_bet_profit}</span>
                        </div>
                        <div>
                            <span style="font-size: 25px; color: black; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">ROI</span>
                            <span style="font-size: 25px; color: black;">&nbsp;</span>
                            <span style="font-size: 50px; color: #e74c3c; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{round(similar_bet_roi,1)}%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                #st.dataframe(similar_bets, hide_index=True) 
            with col2:
                st.markdown(f"""
                    <div style="text-align: center; font-family: 'Arial', sans-serif; font-size: 25px; color:rgb(0, 0, 0); text-shadow: 3px 3px 5px rgba(0,0,0,0.3);">
                    {bet_player} has gone {print_ou} {bet_line} strikeouts in {bet_hit_count} of {start_count} starts
                    </div>
                    """, unsafe_allow_html=True)
                st.plotly_chart(line_plot, use_container_width=False,width=50)

    def sp_grade_color_score(val):
        try:
            score = float(val)
            if score > 100:
                intensity = min((score - 100) / 40, 1)  # Normalize to 0-1 scale, cap at 50 points above 100
                color = f'rgba(144, 238, 144, {0.3 + 0.7 * intensity})'  # Light green with varying opacity
            elif score < 90:
                intensity = min((100 - score) / 50, 1)  # Normalize to 0-1 scale, cap at 50 points below 100
                color = f'rgba(255, 182, 193, {0.3 + 0.7 * intensity})'  # Light pink/red with varying opacity
            else:
                color = 'rgba(245, 245, 245, 1)'  # Neutral light gray for 100
            
            return f'background-color: {color}; color: black;'
        except:
            return ''  # Return empty string for non-numeric values

    if tab == "SP Planner":
        st.markdown("&nbsp;<h1><center>Upcoming Strength of Schedule Analysis</h1></center>&nbsp;",unsafe_allow_html=True)

        dpcheck = st.checkbox('Show Daily Planner?')
        if dpcheck:
            st.markdown("<h3><center>Upcoming Starting Pitcher Matchup Grades</h3></center>",unsafe_allow_html=True)
            #sgcol1, sgcol2, sgcol3 = st.columns([1,5,1])
            #with sgcol2:
            upcoming_start_grades['Date'] = upcoming_start_grades['Date'] + '-2025'
            upcoming_start_grades['Date'] = pd.to_datetime(upcoming_start_grades['Date'])
            upcoming_start_grades['Date'] =upcoming_start_grades['Date'].dt.date
            upcoming_start_grades['Own%'] = round(upcoming_start_grades['Own%'],0)
            upcoming_start_grades = upcoming_start_grades[['Date','Pitcher','Team','Own%','Opp','Home','Start Grade','Day Rank']]
            dates = upcoming_start_grades['Date'].unique()
            ownerships = upcoming_start_grades['Own%'].unique()

            col1, col2 = st.columns([1,4])

            with col1:
                # Sliders
                date_range = st.slider("Select a Date Range", min_value=min(dates), max_value=max(dates), value=(min(dates), max(dates)), format="YYYY-MM-DD")
                own_range = st.slider("Select an Ownership Range", min_value=min(ownerships), max_value=max(ownerships), value=(min(ownerships), max(ownerships)))
            
            with col2:
                sg_filtered_df = upcoming_start_grades[(upcoming_start_grades['Date'] >= date_range[0]) & (upcoming_start_grades['Date'] <= date_range[1])]
                sg_filtered_df = sg_filtered_df[(upcoming_start_grades['Own%'] >= own_range[0]) & (upcoming_start_grades['Own%'] <= own_range[1])]

                sg_display = sg_filtered_df.style.applymap(sp_grade_color_score, subset=['Start Grade']).format({'Start Grade': '{:.0f}','Own%': '{:.0f}'})
                #st.markdown("&nbsp;&nbsp;&nbsp;", unsafe_allow_html=True)
                st.dataframe(sg_display, width=900,height=500, hide_index=True)
        
        col1, col2 = st.columns([1,1])
        with col1:
            st.markdown("<h3>Softest Upcoming Schedules</h3>",unsafe_allow_html=True)
            top_hits = upcoming_p_scores[upcoming_p_scores['Score']>=110][['Pitcher','Team','GS','Score','Matchups']]
            top_hits['Score'] = top_hits['Score'].astype(float).astype(int)
            styled_top_hits = top_hits.style.applymap(sp_grade_color_score, subset=['Score'])

            st.dataframe(styled_top_hits, hide_index=True, height=400, width=900)

        with col2:
            st.markdown("<h3>Toughest Upcoming Schedules</h3>",unsafe_allow_html=True)
            bot_hits = upcoming_p_scores[upcoming_p_scores['Score']<=90][['Pitcher','Team','GS','Score','Matchups']].sort_values(by='Score')
            bot_hits['Score'] = bot_hits['Score'].astype(float).astype(int)
            styled_bot_hits = bot_hits.style.applymap(sp_grade_color_score, subset=['Score'])
            st.dataframe(styled_bot_hits, hide_index=True, height=400, width=900)

        col1, col2 = st.columns([1,1])
        with col1:
            st.markdown("<h3>Search for a Pitcher</h3>", unsafe_allow_html=True)
            pitcher_name = st.text_input("Enter Pitcher Name:")
            if pitcher_name:
                # Case-insensitive search for pitcher name
                search_result = upcoming_p_scores[upcoming_p_scores['Pitcher'].str.contains(pitcher_name, case=False, na=False)][['Pitcher','Team','GS','Score','Matchups']]
                if not search_result.empty:
                    search_result['Score'] = search_result['Score'].astype(float).astype(int)
                    styled_search_result = search_result.style.applymap(sp_grade_color_score, subset=['Score'])
                    st.dataframe(styled_search_result, hide_index=True, width=900)
                else:
                    st.write("No matching pitcher found.")
        with col2:

            p_hand_dict = dict(zip(mlbplayerinfo.Player, mlbplayerinfo.PitchSide))
            st.markdown("<h3>Filter by Opponent</h3>", unsafe_allow_html=True)
            # Get unique OPP values and sort them for better UX
            opp_options = sorted(base_sched['OPP'].unique())
            # Create a dropdown for selecting an OPP
            selected_opp = st.selectbox("Select Opponent:", opp_options)
            # Filter base_sched based on selected OPP
            base_sched['Hand'] = base_sched['Pitcher'].map(p_hand_dict)
            filtered_sched = base_sched[base_sched['OPP'] == selected_opp][['DATE','GAME','TIME','Pitcher','Hand','TEAM','OPP']]
            # Display the filtered dataframe
            st.dataframe(filtered_sched, hide_index=True, width=900)

