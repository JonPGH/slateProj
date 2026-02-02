import streamlit as st
import pandas as pd, math
import os
import warnings, re
import gspread

warnings.filterwarnings("ignore")

import numpy as np
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Store what access they have (None / "basic" / "full" / etc.)
if "access_level" not in st.session_state:
    st.session_state.access_level = None

# Optional: store which password key they used (not the raw password)
if "auth_key" not in st.session_state:
    st.session_state.auth_key = None


# ----------------------------
# Password -> access mapping
# (use env vars / st.secrets in production; see note below)
# ----------------------------
PASSWORDS = {
    "giles":   {"access_level": "full", "auth_key": "FULL"},
    "12":      {"access_level": "full", "auth_key": "FULL"},
    "kanak": {"access_level": "full",  "auth_key": "FULL"},
}

def check_password():
    def password_entered():
        pw = st.session_state.get("password", "")
        info = PASSWORDS.get(pw)

        if info:
            st.session_state.authenticated = True
            st.session_state.access_level = info["access_level"]
            st.session_state.auth_key = info["auth_key"]
            # clear the entered password from session state
            st.session_state.pop("password", None)
        else:
            st.session_state.authenticated = False
            st.session_state.access_level = None
            st.session_state.auth_key = None
            st.error("Incorrect password. Please try again.")

    if not st.session_state.authenticated:
        st.text_input(
            "Enter Password (new password in resource glossary 1/30/2026)",
            type="password",
            key="password",
            on_change=password_entered,
        )
        return False

    return True


# ----------------------------
# Main app content
# ----------------------------
if check_password():

    # Access variables you can use anywhere later:
    access_level = st.session_state.access_level   # "basic" or "full"
    auth_key     = st.session_state.auth_key       # e.g., "FULL"

    #st.write(f"Logged in with access: {access_level}")

    # Set page configuration
    st.set_page_config(page_title="MLB DW Web App", layout="wide")

    ### count down banner 

    try:
        from zoneinfo import ZoneInfo  # py3.9+
    except ImportError:
        ZoneInfo = None

    def render_opening_day_banner():
        from datetime import datetime
        import streamlit as st

        target = datetime(2026, 3, 26)
        now = datetime.now()
        delta = target - now
        total_seconds = int(delta.total_seconds())

        if total_seconds <= 0:
            headline = "⚾ MLB Opening Day is HERE"
            sub = "Play ball."
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            headline = f"{days} Days Until Opening Day!"
            sub = f"{days} days"# {hours}h {minutes}m remaining"

        html = f"""
        <div style="
            width:100%;
            padding:16px 20px;
            margin-bottom:14px;
            border-radius:14px;
            background:#0f172a;
            color:#ffffff;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 8px 20px rgba(0,0,0,0.18);
        ">
            <div>
                <div style="font-size:22px;font-weight:800;">
                    {headline}
                </div>
            </div>

            
        </div>
        """

        st.markdown(html, unsafe_allow_html=True)

    # Call this once per page render (put it right after set_page_config / before your page content)
    render_opening_day_banner()

    #######

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
    @st.cache_data(ttl=60*60)  # 5 minutes
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
        #logo = "{}/Logo.jpeg".format(file_path)
        logo = "{}/Logo.png".format(file_path)
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
        hotzonedata = pd.read_csv(f'{file_path}/hotzonedata.csv')
        hprofiles24 = pd.read_csv(f'{file_path}/hitter_profiles_data_2024.csv')
        hprofiles25 = pd.read_csv(f'{file_path}/hitter_profiles_data_2025.csv')
        hprofiles2425 = pd.read_csv(f'{file_path}/hitter_profiles_data_2024_2025.csv')
        posdata = pd.read_csv(f'{file_path}/mlbposdata.csv')
        hitterranks = pd.read_csv(f'{file_path}/MLB DW 2026 Player Ranks - Hitters.csv')
        pitcherranks = pd.read_csv(f'{file_path}/MLB DW 2026 Player Ranks - Pitchers.csv')
        fscores_mlb_hit = pd.read_csv(f'{file_path}/All_MLB_Scores.csv')
        fscores_milb_hit = pd.read_csv(f'{file_path}/All_MiLB_Scores.csv')
        fscores_mlb_pitch = pd.read_csv(f'{file_path}/All_Pitching_Majors_MLB_Scores.csv')
        fscores_milb_pitch = pd.read_csv(f'{file_path}/All_Pitching_Minors_MLB_Scores.csv')
        ja_hit = pd.read_csv(f'{file_path}/ja_2026_hitter_proj.csv')
        ja_pitch = pd.read_csv(f'{file_path}/ja_2026_pitching_projections.csv')
        steamerhit = pd.read_csv(f'{file_path}/steamerhit.csv')
        steamerpit = pd.read_csv(f'{file_path}/steamerpitch.csv')
        bathit = pd.read_csv(f'{file_path}/thebat_h.csv')
        batpit = pd.read_csv(f'{file_path}/thebat_p.csv')
        atchit = pd.read_csv(f'{file_path}/atc_h.csv')
        atcpit = pd.read_csv(f'{file_path}/atc_p.csv')
        oopsyhit = pd.read_csv(f'{file_path}/oopsy_h.csv')
        oopsypitch = pd.read_csv(f'{file_path}/oopsy_p.csv')
        adp2026 = pd.read_csv(f'{file_path}/MasterADPTableau.csv')
        timrank_hitters = pd.read_csv(f'{file_path}/timrank_hitters.csv')
        timrank_pitchers = pd.read_csv(f'{file_path}/timrank_pitchers.csv')

        pitch_move_data = pd.read_csv(f'{file_path}/mlb_pitch_movement_clustering_data_2025.csv')

        return pitch_move_data,timrank_hitters,timrank_pitchers,adp2026,ja_hit,ja_pitch,oopsyhit,oopsypitch,steamerhit,steamerpit,bathit,batpit,atchit,atcpit,fscores_mlb_hit,fscores_milb_hit,fscores_mlb_pitch,fscores_milb_pitch,hitterranks,pitcherranks,posdata,hprofiles24,hprofiles25,hprofiles2425,logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, propsdf, gameinfo,h_vs_sim, bpreport, rpstats, hitterproj2,ownershipdf,allbets,alllines,hitdb,pitdb,bat_hitters,bat_pitchers,bet_tracker, base_sched, upcoming_proj, upcoming_p_scores, mlbplayerinfo, airpulldata, trend_p, trend_h, upcoming_start_grades, hotzonedata

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
    pitch_move_data,timrank_hitters,timrank_pitchers,adp2026,ja_hit,ja_pitch,oopsyhit,oopsypitch,steamerhit,steamerpit,bathit,batpit,atchit,atcpit,fscores_mlb_hit,fscores_milb_hit,fscores_mlb_pitch,fscores_milb_pitch,hitterranks,pitcherranks,posdata,hprofiles24,hprofiles25,hprofiles2425,logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, props_df, gameinfo, h_vs_sim,bpreport, rpstats, hitterproj2, ownershipdf,allbets,alllines,hitdb,pitdb,bat_hitters,bat_pitchers,bet_tracker, base_sched, upcoming_proj, upcoming_p_scores, mlbplayerinfo, airpulldata, trend_p, trend_h, upcoming_start_grades, hotzonedata = load_data()

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
    st.sidebar.image(logo, width=250)  # Added logo to sidebar
    st.sidebar.title("MLB Projections")
    #tab = st.sidebar.radio("Select View", ["2026 Ranks", "Game Previews", "Pitcher Projections", "Hitter Projections","Hitter Profiles","Hitter Comps", "Player Projection Details","Player Rater", "Matchups", "Player Trends","Air Pull Matchups", "Weather & Umps", "Streamers","Tableau", "DFS Optimizer","Prop Bets", "SP Planner", "Zone Matchups"], help="Choose a view to analyze games or player projections.")
    #tab = st.sidebar.radio("Select View", ["Game Previews", "Pitcher Projections", "Hitter Projections", "Matchups", "Player Trends","Air Pull Matchups", "Weather & Umps", "Streamers","Tableau", "DFS Optimizer","Prop Bets", "SP Planner", "Zone Matchups"], help="Choose a view to analyze games or player projections.")
    #tab = st.sidebar.radio("Select View", ["2026 Ranks", "Game Previews","Hitter Profiles","Hitter Comps", "Player Rater","Tableau"], help="Choose a view to analyze games or player projections.")
    #tab = st.sidebar.radio("Select View", ["2026 Ranks","Matchups", "Game Previews","Hitter Projections","Pitcher Projections","Hitter Profiles","Hitter Comps","Prospect Comps", "Player Rater","Tableau"], help="Choose a view to analyze games or player projections.")
    
    if st.session_state.access_level == "full":
        tab = st.sidebar.radio("Select View", ["2026 Ranks","2026 Projections", "Auction Value Calculator","2026 ADP","Prospect Ranks","Hitter Profiles","Hitter Comps","Prospect Comps", "Player Rater","Pitch Movement Comps"], help="Choose a view to analyze games or player projections.")
    else:
        tab = st.sidebar.radio("Select View", ["2026 Ranks","2026 Projections", "Auction Value Calculator","2026 ADP", "Player Rater","Pitch Movement Comps"], help="Choose a view to analyze games or player projections.")

    
    if "reload" not in st.session_state:
        st.session_state.reload = False

    if st.sidebar.button("Reload Data"):
        st.session_state.reload = True
        st.cache_data.clear()  # Clear cache to force reload
        #logo, hitterproj, pitcherproj, hitter_stats, lineup_stats, pitcher_stats, umpire_data, weather_data, h_vs_avg, p_vs_avg, props_df, gameinfo, h_vs_sim = load_data()

    # Main content
    st.markdown(f"""
                <center><h1>MLB DW Web App</h1></center>
                <center><b><i>On mobile, be sure to set the theme to 'light mode' (go to settings in the top right)</b></i></center></b>
                """, unsafe_allow_html=True)
    #st.markdown("<b><center>If you're on mobile, be sure you're using 'light mode' in settings (hit the three dots in the top right of the screen)</center></b>",unsafe_allow_html=True)
    #st.markdown(f"<center><i>Last projection update time: {last_update}est</center></i>",unsafe_allow_html=True)
    

    # --- HITTER PROFILES (drop-in) -------------------------------------------------
    # Requirements: streamlit, pandas, altair (add "altair" to requirements.txt)

    def _fmt_cols(df: pd.DataFrame, pct_cols=None, trip_cols=None, int_cols=None):
        """Return Streamlit column_config dict + a formatted copy of df."""
        pct_cols = pct_cols or []
        trip_cols = trip_cols or []  # 3-decimal (AVG/OBP/SLG)
        int_cols = int_cols or []

        cfg = {}
        df2 = df.copy()

        # Build configs only for columns that actually exist
        for c in df2.columns:
            if c in pct_cols:
                cfg[c] = st.column_config.NumberColumn(format="%.1f%%", help=f"{c} (percent)")
                # If values look like 0–1, convert to percent
                if df2[c].dropna().between(0, 1).all():
                    df2[c] = df2[c] * 100.0
            elif c in trip_cols:
                cfg[c] = st.column_config.NumberColumn(format="%.3f", help=f"{c} (triple-slash)")
            elif c in int_cols:
                cfg[c] = st.column_config.NumberColumn(format="%d")
            elif pd.api.types.is_float_dtype(df2[c]):
                cfg[c] = st.column_config.NumberColumn(format="%.2f")

        return df2, cfg

    def _cols_existing(df, wanted):
        return [c for c in wanted if c in df.columns]

    def _metric_or_dash(val):
        try:
            if pd.isna(val): return "—"
            if isinstance(val, (float, np.floating)): return f"{val:.3f}" if 0 <= val <= 1 else f"{val:.3f}" if "0." in f"{val}" else f"{val}"
            return f"{val}"
        except Exception:
            return "—"

    def render_hitter_profiles(hprofiles24: pd.DataFrame,
                            hprofiles25: pd.DataFrame,
                            hprofiles2425: pd.DataFrame):

        st.markdown("""
            <div style="text-align:center">
                <div style="font-size:38px; font-weight:800; line-height:1.1">Hitter Profiles ⚾</div>
                <div style="opacity:0.8; margin-top:4px">Fast, visual snapshots of each hitter’s skills and batted-ball DNA</div>
            </div>
            <hr style="margin:1rem 0 0.5rem 0; opacity:.2;">
        """, unsafe_allow_html=True)

        # ------------------------- Controls -------------------------
        colA, colB, colC = st.columns([2, 1, 2])
        with colA:
            hitter_options = sorted(hprofiles2425["BatterName"].dropna().unique().tolist())
            hitter = st.selectbox("Choose a Hitter", hitter_options, index=0)

        with colB:
            sample = st.selectbox("Choose Sample", ["2025", "2024", "2024-2025"], index=0)

        with colC:
            st.caption("Display options")
            show_tables = st.toggle("Show raw tables", value=False, help="Reveal the raw profile tables below the charts/cards")
            show_all_cols = st.toggle("Show all columns", value=False, help="If off, show the key subset for each table")

        if sample == "2025":
            data = hprofiles25.copy()
        elif sample == "2024":
            data = hprofiles24.copy()
        else:
            data = hprofiles2425.copy()

        player = data.loc[data["BatterName"] == hitter].copy()
        if player.empty:
            st.warning("No rows found for that hitter in the selected sample.")
            return

        # If there are multiple rows (e.g., team splits), pick the most recent/highest PA row as default view
        if "PA" in player.columns:
            player = player.sort_values("PA", ascending=False).head(1)
        else:
            player = player.head(1)

        # ------------------------- Top Cards -------------------------
        # Pull headline metrics safely
        def gv(col, default=None):
            return player[col].values[0] if col in player.columns else default

        PA = gv("PA", 0)
        HR = gv("HR", 0)
        SB = gv("SB", 0)
        AVG = gv("AVG", np.nan)
        OBP = gv("OBP", np.nan)
        SLG = gv("SLG", np.nan)
        xwOBA = gv("xwOBA", np.nan)
        wOBA = gv("wOBA", np.nan) if "wOBA" in player.columns else np.nan

        st.markdown("### Snapshot")
        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
        mc1.metric("PA", f"{int(PA) if pd.notna(PA) else '—'}")
        mc2.metric("HR", f"{int(HR) if pd.notna(HR) else '—'}")
        mc3.metric("SB", f"{int(SB) if pd.notna(SB) else '—'}")
        mc4.metric("AVG", _metric_or_dash(AVG))
        mc5.metric("OBP", _metric_or_dash(OBP))
        mc6.metric("SLG", _metric_or_dash(SLG))

        # ------------------------- Quick Charts -------------------------
        st.markdown("### Visuals")

        ch_left, ch_mid, ch_right = st.columns([1.2, 1.2, 1.4])

        # Slash line bar
        with ch_left:
            slash_cols = _cols_existing(player, ["AVG", "OBP", "SLG"])
            if slash_cols:
                plot_df = pd.melt(player[slash_cols], var_name="Stat", value_name="Value")
                bar = (
                    alt.Chart(plot_df)
                    .mark_bar()
                    .encode(x=alt.X("Stat:N", title="", sort=slash_cols),
                            y=alt.Y("Value:Q", title="", scale=alt.Scale(zero=False)),
                            tooltip=[alt.Tooltip("Stat:N"), alt.Tooltip("Value:Q", format=".3f")])
                    .properties(height=200)
                )
                st.altair_chart(bar, use_container_width=True)
            else:
                st.caption("Slash chart: required columns not found.")

        # Batted-ball profile horizontal bars
        with ch_mid:
            bb_cols = _cols_existing(player, ["Brl%", "AirPull%", "GB%", "LD%", "FB%", "SweetSpot%"])
            if bb_cols:
                bb_df = player[bb_cols].T.reset_index()
                bb_df.columns = ["Metric", "Value"]
                # Normalize to percent if needed
                if bb_df["Value"].dropna().between(0, 1).all():
                    bb_df["Value"] = bb_df["Value"] * 100.0
                hbar = (
                    alt.Chart(bb_df)
                    .mark_bar()
                    .encode(
                        y=alt.Y("Metric:N", sort="-x", title=""),
                        x=alt.X("Value:Q", title="", scale=alt.Scale(domain=[0, max(100, float(bb_df["Value"].max() or 0))])),
                        tooltip=[alt.Tooltip("Metric:N"), alt.Tooltip("Value:Q", format=".1f")]
                    )
                    .properties(height=220)
                )
                st.altair_chart(hbar, use_container_width=True)
            else:
                st.caption("Batted-ball chart: required columns not found.")

        # Contact/discipline scatter (x: Z-Contact%, y: Z-Swing%, size: BB%/K% diff)
        with ch_right:
            d_cols = _cols_existing(player, ["Z-Contact%", "Z-Swing%", "BB%", "K%"])
            if d_cols:
                ddf = player.copy()
                # Convert to 0–100 if in decimals
                for c in ["Z-Contact%", "Z-Swing%", "BB%", "K%"]:
                    if c in ddf.columns:
                        if ddf[c].dropna().between(0, 1).all():
                            ddf[c] = ddf[c] * 100.0
                ddf["DisciplineScore"] = (ddf.get("BB%", 0) - ddf.get("K%", 0))
                scat = (
                    alt.Chart(ddf)
                    .mark_circle()
                    .encode(
                        x=alt.X("Z-Contact%:Q", title="Z-Contact%"), 
                        y=alt.Y("Z-Swing%:Q", title="Z-Swing%"),
                        size=alt.Size("DisciplineScore:Q", title="BB% - K%"),
                        tooltip=[
                            alt.Tooltip("Z-Contact%:Q", format=".1f"),
                            alt.Tooltip("Z-Swing%:Q", format=".1f"),
                            alt.Tooltip("BB%:Q", format=".1f"),
                            alt.Tooltip("K%:Q", format=".1f")
                        ],
                    )
                    .properties(height=230)
                )
                st.altair_chart(scat, use_container_width=True)
            else:
                st.caption("Plate-discipline scatter: required columns not found.")

        # ------------------------- Detail Tabs -------------------------
        tab1, tab2, tab3, tab4 = st.tabs(["Base Stats", "Batted Ball", "Plate Discipline", "fScores"])

        # Base stats
        with tab1:
            base_cols = _cols_existing(player, ["BatterName", "PA", "AB", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "xwOBA", "wOBA"])
            if base_cols:
                df_base = player[base_cols].copy()
                df_base, cfg = _fmt_cols(
                    df_base,
                    pct_cols=[],  # slash/xwOBA are 3-decimal
                    trip_cols=_cols_existing(df_base, ["AVG", "OBP", "SLG", "xwOBA", "wOBA"]),
                    int_cols=_cols_existing(df_base, ["PA", "AB", "R", "HR", "RBI", "SB"])
                )
                st.dataframe(df_base if show_all_cols else df_base[base_cols], use_container_width=True, column_config=cfg, hide_index=True)
            else:
                st.info("No base stat columns found.")

        # Batted ball
        with tab2:
            bb_cols_full = _cols_existing(player, ["BatterName","xwOBA","xwOBACON","Brl%","AirPull%","GB%","LD%","FB%","SweetSpot%"])
            if bb_cols_full:
                df_bb = player[bb_cols_full].copy()
                df_bb, cfg = _fmt_cols(
                    df_bb,
                    pct_cols=_cols_existing(df_bb, ["Brl%","AirPull%","GB%","LD%","FB%","SweetSpot%"]),
                    trip_cols=_cols_existing(df_bb, ["xwOBA","xwOBACON"]),
                )
                st.dataframe(df_bb if show_all_cols else df_bb[bb_cols_full], use_container_width=True, column_config=cfg, hide_index=True)
            else:
                st.info("No batted-ball profile columns found.")

        # Plate discipline
        with tab3:
            disc_cols = _cols_existing(player, ["BatterName","K%","BB%","Z-Contact%","Z-Swing%","O-Swing%","O-Contact%"])
            if disc_cols:
                df_disc = player[disc_cols].copy()
                df_disc, cfg = _fmt_cols(
                    df_disc,
                    pct_cols=[c for c in disc_cols if c.endswith("%")]
                )
                st.dataframe(df_disc if show_all_cols else df_disc[disc_cols], use_container_width=True, column_config=cfg, hide_index=True)
            else:
                st.info("No plate-discipline columns found.")

        # fScores
        with tab4:
            f_cols = _cols_existing(player, ["BatterName","fHitTool","fPower","fDiscipline","fSpeed","fDurability"])
            if f_cols:
                df_f = player[f_cols].copy()
                # Horizontal bar chart for fScores
                score_cols = [c for c in f_cols if c != "BatterName"]
                if score_cols:
                    longf = pd.melt(df_f[["BatterName"] + score_cols], id_vars=["BatterName"], var_name="Trait", value_name="Score")
                    fbar = (
                        alt.Chart(longf)
                        .mark_bar()
                        .encode(
                            y=alt.Y("Trait:N", sort="-x", title=""),
                            x=alt.X("Score:Q", title="", scale=alt.Scale(zero=False)),
                            tooltip=["Trait:N", alt.Tooltip("Score:Q", format=".1f")]
                        )
                        .properties(height=220)
                    )
                    st.altair_chart(fbar, use_container_width=True)

                # Table
                df_f, cfg = _fmt_cols(df_f)
                st.dataframe(df_f if show_all_cols else df_f[f_cols], use_container_width=True, column_config=cfg, hide_index=True)
            else:
                st.info("No fScore columns found.")

        # ------------------------- Optional: Raw tables -------------------------
        if show_tables:
            st.divider()
            st.subheader("Raw tables")
            st.write("Below are your original selections as plain tables (useful for debugging).")

            # These mimic your original blocks but cleaner + resilient
            base_cols_raw = _cols_existing(data, ["BatterName","PA","AB","R","HR","RBI","SB","AVG","OBP","SLG"])
            if base_cols_raw:
                df0 = player[base_cols_raw].copy()
                df0, cfg0 = _fmt_cols(df0, trip_cols=_cols_existing(df0, ["AVG","OBP","SLG"]), int_cols=_cols_existing(df0, ["PA","AB","R","HR","RBI","SB"]))
                st.dataframe(df0, use_container_width=True, column_config=cfg0, hide_index=True)

            bb_cols_raw = _cols_existing(data, ["BatterName","xwOBA","xwOBACON","Brl%","AirPull%","GB%","LD%","FB%","SweetSpot%"])
            if bb_cols_raw:
                df1 = player[bb_cols_raw].copy()
                df1, cfg1 = _fmt_cols(df1, pct_cols=_cols_existing(df1, ["Brl%","AirPull%","GB%","LD%","FB%","SweetSpot%"]),
                                    trip_cols=_cols_existing(df1, ["xwOBA","xwOBACON"]))
                st.dataframe(df1, use_container_width=True, column_config=cfg1, hide_index=True)

            disc_cols_raw = _cols_existing(data, ["BatterName","K%","BB%","Z-Contact%","Z-Swing%"])
            if disc_cols_raw:
                df2 = player[disc_cols_raw].copy()
                df2, cfg2 = _fmt_cols(df2, pct_cols=[c for c in disc_cols_raw if c.endswith("%")])
                st.dataframe(df2, use_container_width=True, column_config=cfg2, hide_index=True)

            f_cols_raw = _cols_existing(data, ["BatterName","fHitTool","fPower","fDiscipline","fSpeed","fDurability"])
            if f_cols_raw:
                df3 = player[f_cols_raw].copy()
                df3, cfg3 = _fmt_cols(df3)
                st.dataframe(df3, use_container_width=True, column_config=cfg3, hide_index=True)

    
    def get_sheet_data_old(sheet_url, worksheet_name="Sheet1"):
        """Fetch data from a Google Sheet using gspread"""
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the sheet and get data
        sheet = client.open_by_url(sheet_url).worksheet(worksheet_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)

    # Cache the data to avoid repeated API calls
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def load_all_sheets_old(sheet_urls):
        """Load data from all sheets"""
        sheet_data = {}
        for name, url in sheet_urls.items():
            sheet_data[name] = get_sheet_data_old(url,"Hitters")
            sheet_data[name] = get_sheet_data_old(url,"Pitchers")
        return sheet_data  
    

    @st.cache_resource
    def get_gspread_client():
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        return gspread.authorize(creds)

    # 2) Cache a single worksheet → DataFrame
    @st.cache_data(show_spinner=False)  # no TTL = cache for the app session until cleared
    def get_sheet_df(sheet_url: str, worksheet_name: str) -> pd.DataFrame:
        client = get_gspread_client()
        ws = client.open_by_url(sheet_url).worksheet(worksheet_name)
        # get_all_records respects header row; fast + clean to DataFrame
        data = ws.get_all_records()
        return pd.DataFrame(data)

    # 3) Single convenience loader for both tabs (also cached)
    @st.cache_data(show_spinner=False)
    def load_ranks_data(sheet_url: str):
        hitters  = get_sheet_df(sheet_url, "Hitters")
        pitchers = get_sheet_df(sheet_url, "Pitchers")
        return {"hitters": hitters, "pitchers": pitchers}

    # 4) Optional: a manual refresh to bust the cache
    def render_refresh_button():
        col = st.empty()
        with col.container():
            if st.button("↻ Refresh data", help="Clear cache and re-load from Google Sheets"):
                load_ranks_data.clear()
                get_sheet_df.clear()
                get_gspread_client.clear()
                st.experimental_rerun()

    if tab == "Pitch Movement Comps":
        import numpy as np
        import pandas as pd
        import streamlit as st

        st.title("Pitch Movement Comps")
        st.caption("Find the most similar pitch shapes (by pitch type) across MLB, using averaged Statcast movement + release traits.")

        # -----------------------------
        # Expect: pitch_move_data is already loaded as a DataFrame
        # Required columns:
        # player_name, pitcher, p_throws, pitch_type, n_pitches,
        # release_speed, release_pos_x, release_pos_z, release_extension, pfx_x_in, pfx_z_in
        # -----------------------------
        df = pitch_move_data.copy()
        df['PitchGrade'] = round(df['PitchGrade'],0)
        df = df.rename({'PitchGrade': 'MLBDW Grade'},axis=1)

        grade_df = df[['pitcher','pitch_type','MLBDW Grade']]

        required = {
            "player_name","pitcher","p_throws","pitch_type","n_pitches",
            "release_speed","release_pos_x","release_pos_z","release_extension","pfx_x_in","pfx_z_in"
        }
        missing = sorted(list(required - set(df.columns)))
        if missing:
            st.error(f"pitch_move_data is missing required columns: {missing}")
            st.stop()

        # Ensure numeric
        num_cols = ["n_pitches","release_speed","release_pos_x","release_pos_z","release_extension","pfx_x_in","pfx_z_in"]
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df.dropna(subset=["player_name","pitcher","pitch_type","p_throws"] + num_cols).copy()
        df["pitch_type"] = df["pitch_type"].astype(str)
        df["p_throws"] = df["p_throws"].astype(str)

        # -----------------------------
        # Layout: Left = results, Right = controls (top) + filters (below)
        # -----------------------------
        left, right = st.columns([3, 1])

        with right:
            st.subheader("Select Pitcher & Pitch")

            # Pitcher search + select (in the right pane, top)
            search = st.text_input("Search pitcher", value="", placeholder="Type a name (e.g., Cade Horton)")
            all_names = np.array(sorted(df["player_name"].unique()))

            if search.strip():
                mask = np.char.find(np.char.lower(all_names), search.strip().lower()) >= 0
                filtered_names = all_names[mask]
            else:
                filtered_names = all_names

            if len(filtered_names) == 0:
                st.warning("No names match your search.")
                st.stop()

            pitcher_name = st.selectbox("Pitcher", filtered_names, index=0)

            # Identify pitcher_id (handle duplicate names by choosing largest total sample)
            sel_name = df[df["player_name"] == pitcher_name].copy()
            totals = sel_name.groupby("pitcher", as_index=False)["n_pitches"].sum().sort_values("n_pitches", ascending=False)
            pitcher_id = int(totals.iloc[0]["pitcher"])
            sel_pitcher = sel_name[sel_name["pitcher"] == pitcher_id].copy()

            # Pitch selection box (top)
            pitch_options = (
                sel_pitcher.sort_values("n_pitches", ascending=False)["pitch_type"].unique().tolist()
            )
            default_pitch = pitch_options[0] if pitch_options else None
            selected_pitch_type = st.selectbox("Pitch type", pitch_options, index=0)

            st.divider()
            st.subheader("Filters")

            k = st.slider("Comps per pitch", min_value=5, max_value=15, value=10, step=1)
            min_target_n = st.slider("Min samples for selected pitch", min_value=1, max_value=100, value=15, step=1)
            min_comp_n = st.slider("Min samples for comp pitches", min_value=10, max_value=150, value=30, step=5)

            same_hand_only = st.checkbox("Only compare to same throwing hand", value=True)

            st.divider()
            st.subheader("Bias toward bigger samples")
            st.caption("Penalizes low-sample comps so you don’t just get random 12-pitch reliever shapes.")
            sample_penalty = st.slider(
                "Penalty strength",
                min_value=0.0, max_value=10.0, value=5.0, step=0.5,
                help="Higher = more penalty for low-sample comps. 0 = no bias, pure distance."
            )

            st.divider()
            feat_mode = st.selectbox(
                "Feature set",
                ["Shape + Release (recommended)", "Movement + Velo only"],
                index=0,
                help="Shape + Release tends to produce more intuitive pitcher-to-pitcher comps."
            )

        # -----------------------------
        # Feature selection
        # -----------------------------
        if feat_mode == "Movement + Velo only":
            feat_cols = ["release_speed","pfx_x_in","pfx_z_in"]
        else:
            feat_cols = ["release_speed","release_pos_x","release_pos_z","release_extension","pfx_x_in","pfx_z_in"]

        # -----------------------------
        # Standardize features *within pitch_type* (and optionally within hand)
        # -----------------------------
        group_keys = ["pitch_type"] + (["p_throws"] if same_hand_only else [])

        for c in feat_cols:
            df[f"{c}__mu"] = df.groupby(group_keys)[c].transform("mean")
            df[f"{c}__sd"] = df.groupby(group_keys)[c].transform("std").replace(0, np.nan)
            df[f"z_{c}"] = (df[c] - df[f"{c}__mu"]) / df[f"{c}__sd"]

        z_cols = [f"z_{c}" for c in feat_cols]
        df = df.dropna(subset=z_cols).copy()

        # -----------------------------
        # Helper: compute comps for a single (pitcher, pitch_type) row
        # -----------------------------
        def get_comps_for_row(target_row: pd.Series, top_k: int) -> pd.DataFrame:
            pt = target_row["pitch_type"]
            hand = target_row["p_throws"]

            pool = df[df["pitch_type"] == pt].copy()
            if same_hand_only:
                pool = pool[pool["p_throws"] == hand].copy()

            # Exclude same pitcher
            pool = pool[pool["pitcher"] != target_row["pitcher"]].copy()

            # Filter by comp sample size
            pool = pool[pool["n_pitches"] >= min_comp_n].copy()
            if pool.empty:
                return pool

            # Vector distances in z-space
            t = target_row[z_cols].to_numpy(dtype=float)
            X = pool[z_cols].to_numpy(dtype=float)
            d = np.sqrt(((X - t) ** 2).sum(axis=1))

            # Penalize small sample comps (optional)
            n = pool["n_pitches"].to_numpy(dtype=float)
            factor = 1.0 + (sample_penalty / np.sqrt(np.maximum(n, 1.0)))
            score = d * factor

            pool = pool.assign(distance=d, score=score)

            # Rank: primarily by score, then raw distance, then larger sample
            pool = pool.sort_values(["score","distance","n_pitches"], ascending=[True, True, False]).head(top_k)

            show_cols = [
                "player_name","pitcher","p_throws","pitch_type","n_pitches",
                "release_speed","pfx_x_in","pfx_z_in","release_pos_x","release_pos_z","release_extension",
                "distance","score"
            ]
            show_cols = [c for c in show_cols if c in pool.columns]
            return pool[show_cols].reset_index(drop=True)

        # -----------------------------
        # Selected pitcher summary + selected pitch comps in left pane
        # -----------------------------
        with left:
            #df = pd.merge(df,grade_df,how='left',on=['pitcher','pitch_type'])
            sel = df[(df["player_name"] == pitcher_name) & (df["pitcher"] == pitcher_id)].copy()
            if sel.empty:
                st.error("Selected pitcher not found in the data after filtering/standardization.")
                st.stop()

            hand = sel["p_throws"].iloc[0]

            st.subheader(f"{pitcher_name}  ·  {hand}-handed")
            st.caption(f"Pitcher ID: {pitcher_id}")

            st.markdown("### Pitch Arsenal (Averages)")
            summary_cols = ["pitch_type","n_pitches","MLBDW Grade","release_speed","pfx_x_in","pfx_z_in","release_pos_x","release_pos_z","release_extension"]
            summary_cols = [c for c in summary_cols if c in sel.columns]
            arsenal = sel[summary_cols].sort_values("n_pitches", ascending=False).reset_index(drop=True)
            st.dataframe(arsenal, use_container_width=True, hide_index=True)

            st.markdown(f"### Selected Pitch: **{selected_pitch_type}**")
            target = sel[sel["pitch_type"] == selected_pitch_type].copy()
            if target.empty:
                st.warning("That pitch type wasn't found for the selected pitcher.")
                st.stop()

            trow = target.sort_values("n_pitches", ascending=False).iloc[0]
            if int(trow["n_pitches"]) < min_target_n:
                st.warning(
                    f"{pitcher_name} {selected_pitch_type} only has n={int(trow['n_pitches'])} in your table. "
                    f"Lower 'Min samples for selected pitch' or pick a different pitch."
                )
                st.stop()

            # Target metrics row
            cols = st.columns(7)
            cols[0].metric("MLBDW Grade", f"{trow['MLBDW Grade']:.0f}")
            cols[1].metric("Velo", f"{trow['release_speed']:.1f}")
            cols[2].metric("HB (in)", f"{trow['pfx_x_in']:.1f}")
            cols[3].metric("VB (in)", f"{trow['pfx_z_in']:.1f}")
            if "release_extension" in trow:
                cols[4].metric("Ext", f"{trow['release_extension']:.2f}")
            if "release_pos_x" in trow:
                cols[5].metric("Rel X", f"{trow['release_pos_x']:.2f}")
            if "release_pos_z" in trow:
                cols[6].metric("Rel Z", f"{trow['release_pos_z']:.2f}")

            st.markdown("### Most Similar Pitches (Same Pitch Type)")
            comps = get_comps_for_row(trow, top_k=k)

            if comps.empty:
                st.info("No comps found after filters (try lowering 'Min samples for comp pitches').")
            else:
                comps = pd.merge(comps, grade_df, how='left', on=['pitcher','pitch_type'])
                display = comps.copy()

                if "distance" in display.columns:
                    display["distance"] = display["distance"].round(3)
                if "score" in display.columns:
                    display["score"] = display["score"].round(3)
                for c in ["release_speed","pfx_x_in","pfx_z_in","release_extension","release_pos_x","release_pos_z"]:
                    if c in display.columns:
                        display[c] = display[c].round(2)
                
                display = display[['player_name','pitch_type','MLBDW Grade','n_pitches','release_speed','pfx_x_in','pfx_z_in','release_pos_x','release_pos_z','release_extension','distance','score']]
                display.columns=['Pitcher','Pitch','MLBDW Grade','#','Velo','X Move','V Move','Release X','Release Y','Ext','Distance','Sim Score']
                st.dataframe(display, use_container_width=True, hide_index=True)

            # Optional movement plot
            show_plot = st.checkbox("Show movement scatter (context)", value=False)
            if show_plot:
                import matplotlib.pyplot as plt

                pool = df[df["pitch_type"] == selected_pitch_type].copy()
                if same_hand_only:
                    pool = pool[pool["p_throws"] == hand].copy()

                cloud = pool[pool["n_pitches"] >= min_comp_n].copy()
                highlight_names = set(comps["player_name"].tolist()) if not comps.empty else set()
                highlight = cloud[cloud["player_name"].isin(highlight_names)].copy()

                fig, ax = plt.subplots()
                ax.scatter(cloud["pfx_x_in"], cloud["pfx_z_in"], alpha=0.15)
                if not highlight.empty:
                    ax.scatter(highlight["pfx_x_in"], highlight["pfx_z_in"], alpha=0.9)

                ax.scatter([trow["pfx_x_in"]], [trow["pfx_z_in"]], marker="X", s=120)

                ax.set_xlabel("Horizontal Break (in)  [pitcher POV]")
                ax.set_ylabel("Vertical Break (in)")
                ax.set_title(f"{pitcher_name} {selected_pitch_type} — Movement Neighborhood")
                st.pyplot(fig, clear_figure=True)

            st.divider()
            st.caption(
                "Under the hood: we z-score features within pitch type (and optionally hand), then use nearest-neighbor distance. "
                "The sample penalty biases comps toward higher-sample pitches."
            )



        if tab == "Team Talk":
            st.title("MLB Team Fan Accounts on X")

            TEAM_X_LISTS = {
                "Phillies": "https://x.com/i/lists/1998094471389429763",
                "Mets": "https://x.com/i/lists/1998094471389429763",  # fake placeholder
                "Nationals": "https://x.com/i/lists/1998098849437479020",
                "Braves": "https://x.com/i/lists/1998097122676052283",
                "Marlins": "https://x.com/i/lists/1998098786376159713",
            }

            team = st.selectbox("Select a team", list(TEAM_X_LISTS.keys()))

            if team:
                list_url = TEAM_X_LISTS[team]
                
                st.subheader(f"{team} X Fan List")

                st.markdown(
                    f"""
                    <div style="padding:20px; border-radius:12px; 
                                background:#f5f7fa; border:1px solid #dadde1;">
                        <h3 style="margin-top:0;">{team} Fan Accounts</h3>
                        <p>This will open the curated X list for {team} fans.</p>
                        <a href="{list_url}" target="_blank"
                        style="font-size:18px; font-weight:600; 
                                color:#1d9bf0; text-decoration:none;">
                            👉 Open {team} Fan List on X
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )




    if tab == "Prospect Ranks":

        ## Some functions ##
        fscores_milb_hit = fscores_milb_hit.dropna()
        fscores_milb_pitch = fscores_milb_pitch.dropna()

        def score_bg_color(val: float) -> str:
            if val < 80:
                return "#7f1d1d"      # darkest red
            elif val < 100:
                return "#dc2626"      # red
            elif val < 105:
                return "#facc15"      # yellow
            elif val < 120:
                return "#86efac"      # light green
            else:
                return "#16a34a"      # greenest

        def render_score_tile(label: str, value: float):
            bg = score_bg_color(value)

            html = f"""
            <div style="
                background:{bg};
                border-radius:14px;
                padding:12px 8px;          /* ↓ was 18px 10px */
                text-align:center;
                box-shadow:0 4px 10px rgba(0,0,0,0.12);
                min-width:110px;
            ">
                <div style="
                    font-size:30px;        /* ↓ was 38px */
                    font-weight:800;
                    color:#111827;
                    line-height:1.05;
                ">
                    {value:.0f}
                </div>
                <div style="
                    font-size:13px;        /* ↓ was 14px */
                    font-weight:600;
                    margin-top:4px;        /* ↓ was 6px */
                    color:#1f2937;
                    letter-spacing:0.04em;
                ">
                    {label.upper()}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

        import re
        # ---------- LIGHT CUSTOM STYLING ----------
        custom_css = """
        <style>
        html, body, [class*="css"]  {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stDataFrame table {
            border-collapse: collapse !important;
        }

        .stDataFrame th {
            background: #0f172a !important;  /* dark navy */
            color: #f9fafb !important;       /* near white */
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }

        .stDataFrame td {
            font-size: 0.9rem !important;
            padding: 0.35rem 0.5rem !important;
        }

        .stDataFrame tbody tr:hover {
            background-color: #e5f2ff !important;
        }
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)

        # ---------- TITLE / INTRO ----------
        st.title("Top 150 Prospect Rankings")
        #st.caption("Fantasy-focused prospect list from Tim Kanak (@fantasyaceball)")
        st.markdown("<font size=5>Fantasy-focused prospect list from Tim Kanak (@fantasyaceball)</font>", unsafe_allow_html=True)

        st.markdown(
            """
            These rankings are based on **fantasy value** (not real-life WAR), 
            with hitters generally favored over pitchers and a blend of proximity + 5-year upside.

            Tim's top 150 has been split between hitters and pitchers below. 
            """
        )

        # ---------- PLAYER TYPE TOGGLE ----------
        col_pool_left, col_pool_right = st.columns([2, 3])
        with col_pool_left:
            pool = st.radio(
                "Player type",
                ["Hitters", "Pitchers"],
                horizontal=True,
            )

        if pool == "Hitters":
            base_df = timrank_hitters.copy()
        else:
            base_df = timrank_pitchers.copy()

        base_df["rank"] = pd.to_numeric(base_df["rank"], errors="coerce")

        # ---------- SEARCH FILTERS (PLAYER + TEAM ONLY) ----------
        st.markdown("### Search")

        c1, c2 = st.columns(2)
        with c1:
            player_query = st.text_input(
                "Search by player name",
                placeholder="e.g. Walcott, Basallo, Konnor Griffin...",
            )
        with c2:
            team_query = st.text_input(
                "Search by organization",
                placeholder="e.g. Pirates, Guardians, Dodgers...",
            )

        df = base_df.copy()

        # Player search
        if player_query:
            pat = player_query.lower()
            df = df[df["player_name"].str.lower().str.contains(pat, na=False)]

        # Team search
        if team_query:
            pat = team_query.lower()
            df = df[df["organization"].str.lower().str.contains(pat, na=False)]

        df = df.sort_values("rank")

        # ---------- LAYOUT: TABLE LEFT, DETAIL RIGHT ----------
        left_col, right_col = st.columns([2,4])

        # ===== LEFT: MAIN TABLE =====
        with left_col:
            st.markdown("### Prospect List")

            display_cols = ["rank", "player_name", "organization", "eta"]
            display_cols = [c for c in display_cols if c in df.columns]

            table_df = df[display_cols].reset_index(drop=True)

            column_config = {}
            if "rank" in table_df.columns:
                column_config["rank"] = st.column_config.NumberColumn(
                    "Rank",
                    help="Overall fantasy prospect rank",
                    format="%d",
                )
            if "player_name" in table_df.columns:
                column_config["player_name"] = st.column_config.TextColumn(
                    "Player",
                    help="Prospect name",
                )
            if "organization" in table_df.columns:
                column_config["organization"] = st.column_config.TextColumn(
                    "Org",
                    help="MLB organization",
                )
            if "eta" in table_df.columns:
                column_config["eta"] = st.column_config.TextColumn(
                    "ETA",
                    help="Estimated time of arrival",
                )

            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                height=min(600, 40 + 32 * len(table_df)),
            )

        # ===== RIGHT: DETAIL / POPUP =====
        with right_col:
            st.markdown("### Player Details")

            if table_df.empty:
                st.info("No prospects match your current search.")
            else:
                # Choose a player from the currently filtered list
                selected_name = st.selectbox(
                    "Select a player",
                    options=table_df["player_name"].tolist(),
                )

                ### fscores
                ## try hitter fscores
                player_f_scores_1 = fscores_milb_hit[fscores_milb_hit['Player']==selected_name]
                player_f_scores_2 = fscores_milb_pitch[fscores_milb_pitch['player_name']==selected_name]

                if len(player_f_scores_1)>0:
                    player_f_scores = player_f_scores_1
                    f_score_cat = 'Hitter'
                elif len(player_f_scores_2)>0:
                    player_f_scores = player_f_scores_2
                    f_score_cat = 'Pitcher'
                else:
                    player_f_scores = pd.DataFrame()
                    f_score_cat = 'None'
                
                if f_score_cat == 'Hitter':
                    f_hit = player_f_scores['HitTool'].iloc[0]
                    f_power = player_f_scores['Power'].iloc[0]
                    f_dur = player_f_scores['Durability'].iloc[0]
                    f_disc = player_f_scores['Discipline'].iloc[0]
                    f_speed = player_f_scores['Speed'].iloc[0]

                    f_grade = (f_power*.3) + (f_hit*.3) + (f_disc*.2) + (f_dur*.05) + (f_speed*.15)

                    st.markdown("### 🧬 fScore Grades")

                    c1, c2, c3, c4, c5, c6 = st.columns(6)

                    with c1:
                        render_score_tile("Hit", f_hit)
                    with c2:
                        render_score_tile("Power", f_power)
                    with c3:
                        render_score_tile("Discipline", f_disc)
                    with c4:
                        render_score_tile("Speed", f_speed)
                    with c5:
                        render_score_tile("Durability", f_dur)
                    with c6:
                        render_score_tile("Overall", f_grade)

                    st.markdown("---")
                
                if f_score_cat == 'Pitcher':
                    #st.write(player_f_scores)
                    f_era = player_f_scores['fERA'].iloc[0]
                    f_stuff = player_f_scores['fStuff'].iloc[0]
                    f_dur = player_f_scores['fDurability'].iloc[0]
                    f_control = player_f_scores['fControl'].iloc[0]

                    f_grade = (f_era*.3) + (f_stuff*.3) + (f_control*.3) + (f_dur*.1)

                    st.markdown("### 🧬 fScore Grades")

                    c1, c2, c3, c4, c5 = st.columns(5)

                    with c1:
                        render_score_tile("Stuff", f_stuff)
                    with c2:
                        render_score_tile("Control", f_control)
                    with c3:
                        render_score_tile("ERA", f_era)
                    with c4:
                        render_score_tile("Durability", f_dur)
                    with c5:
                        render_score_tile("Overall", f_grade)

                    st.markdown("---")


                p = base_df[base_df["player_name"] == selected_name].iloc[0]

                # Quick summary card always visible on the right
                st.markdown(
                    f"#### {p['player_name']}"
                    f"<br><span style='font-size:0.9rem; color:#6b7280;'>"
                    f"{p.get('positions', '')} • {p.get('organization', '')}"
                    f"</span>",
                    unsafe_allow_html=True,
                )

                meta_bits = []
                if pd.notna(p.get("rank")):
                    meta_bits.append(f"**Rank:** {int(p['rank'])}")
                if pd.notna(p.get("eta")):
                    meta_bits.append(f"**ETA:** {p['eta']}")
                if pd.notna(p.get("previous_rank")):
                    meta_bits.append(f"**Previous Rank:** {p['previous_rank']}")
                if meta_bits:
                    st.markdown(" | ".join(meta_bits))

                if pd.notna(p.get("comp")) and str(p["comp"]).strip():
                    st.markdown(f"**Comp:** {p['comp']}")

                # Build grades block
                grades_text = ""
                if pool == "Hitters":
                    hit = p.get("hit_grade", None)
                    pa = p.get("plate_approach_grade", None)
                    pow_ = p.get("power_grade", None)
                    spd = p.get("speed_grade", None)
                    chunks = []
                    if pd.notna(hit):
                        chunks.append(f"**Hit:** {hit}")
                    if pd.notna(pa):
                        chunks.append(f"**Plate Approach:** {pa}")
                    if pd.notna(pow_):
                        chunks.append(f"**Power:** {pow_}")
                    if pd.notna(spd):
                        chunks.append(f"**Speed:** {spd}")
                    if chunks:
                        grades_text = " • ".join(chunks)
                else:
                    pitch_cols = [c for c in base_df.columns if c.endswith("_grade")]
                    lines = []
                    for c in pitch_cols:
                        val = p.get(c)
                        if pd.notna(val):
                            label = c.replace("_grade", "")
                            lines.append(f"- **{label}:** {val}")
                    if lines:
                        grades_text = "\n".join(lines)

                if grades_text:
                    if pool == "Hitters":
                        st.markdown("**Tool Grades**")
                        st.markdown(grades_text)
                    else:
                        st.markdown("**Arsenal / Command Grades**")
                        st.markdown(grades_text)

                # Popover "cloud" for full write-up
                with st.popover("View full scouting report ✨"):
                    if pd.notna(p.get("prime_skills")) and str(p["prime_skills"]).strip():
                        st.markdown("#### Prime Skills")
                        st.write(p["prime_skills"])

                    if pd.notna(p.get("ranking_explanation")) and str(p["ranking_explanation"]).strip():
                        st.markdown("#### Ranking Explanation")
                        st.write(p["ranking_explanation"])




    if tab == "2026 ADP":

        # ----------------------------
        # CONFIG / DATA LOADING
        # ----------------------------
        st.set_page_config(page_title="MLB DW ADP Explorer", layout="wide")
        
        adp = adp2026.copy()
        adp['Date'] = pd.to_datetime(adp['Date'])

        st.title("⚾ MLB DW ADP Explorer")

        # ----------------------------
        # SIDEBAR FILTERS
        # ----------------------------
        with st.sidebar:
            st.header("Filters")

            # Format
            all_formats = sorted(adp["Format"].dropna().unique().tolist())
            sel_formats = st.multiselect(
                "Draft Format",
                options=all_formats,
                default=all_formats
            )

            # Date range
            min_date = adp["Date"].min()
            max_date = adp["Date"].max()
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            if isinstance(date_range, tuple):
                start_date, end_date = date_range
            else:  # if user picks only one day
                start_date = end_date = date_range

            # Position filter
            pos_filter_type = st.radio(
                "Position Filter By",
                options=["Primary Pos", "Position(s)"],
                index=0
            )

            if pos_filter_type == "Primary Pos":
                all_pos = sorted(adp["Primary Pos"].dropna().unique().tolist())
            else:
                # explode all listed positions from "Position(s)" column
                temp_pos = (
                    adp["Position(s)"]
                    .dropna()
                    .str.split(",")
                    .explode()
                    .str.strip()
                    .unique()
                    .tolist()
                )
                all_pos = sorted(temp_pos)

            sel_pos = st.multiselect(
                "Positions",
                options=all_pos,
                default=[]
            )

            # Pitcher role filter
            all_roles = sorted(adp["PitcherRole"].fillna("None").unique().tolist())
            sel_roles = st.multiselect(
                "Pitcher Role",
                options=all_roles,
                default=all_roles
            )

            # Player search
            search_text = st.text_input("Search Player (contains)")

            # Minimum drafts filter
            min_drafts = st.number_input(
                "Minimum Drafts (sample size)",
                min_value=1,
                max_value=10000,
                value=5,
                step=1
            )

        # ----------------------------
        # APPLY FILTERS
        # ----------------------------
        df = adp.copy()
        df = df[df["Format"].isin(sel_formats)]
        df = df[(df["Date"] >= pd.to_datetime(start_date)) &
                (df["Date"] <= pd.to_datetime(end_date))]

        if sel_pos:
            if pos_filter_type == "Primary Pos":
                df = df[df["Primary Pos"].isin(sel_pos)]
            else:
                # "Position(s)" contains any selected position
                pos_mask = df["Position(s)"].fillna("").apply(
                    lambda x: any(p in [p2.strip() for p2 in x.split(",")] for p in sel_pos)
                )
                df = df[pos_mask]

        # PitcherRole (treat NaN as "None" to match sidebar choices)
        df = df.copy()
        df["PitcherRole_display"] = df["PitcherRole"].fillna("None")
        df = df[df["PitcherRole_display"].isin(sel_roles)]

        if search_text:
            df = df[df["Player"].str.contains(search_text, case=False, na=False)]

        # ----------------------------
        # AGGREGATED PLAYER TABLE
        # ----------------------------
        if df.empty:
            st.warning("No data with current filters.")
            st.stop()

        group_cols = ["Player", "Player ID", "Team", "Primary Pos",
                    "PitcherRole_display", "Format"]

        agg = df.groupby(group_cols).agg(
            Drafts=("DayADP", "count"),
            ADP=("DayADP", "mean"),
            MinPick=("DayMin", "min"),
            MaxPick=("DayMax", "max"),
            StdDev=("DayADP", "std"),
            FirstDate=("Date", "min"),
            LastDate=("Date", "max")
        ).reset_index()

        # remove players with too few drafts
        agg = agg[agg["Drafts"] >= min_drafts]

        # fill NaN std dev for single-draft guys
        agg["StdDev"] = agg["StdDev"].fillna(0.0)

        # ----------------------------
        # POSITIONAL RANKS
        # ----------------------------
        # Rank within Format + Primary Pos by ADP
        agg = agg.sort_values(["Format", "Primary Pos", "ADP"])
        agg["PosRank"] = (
            agg.groupby(["Format", "Primary Pos"])["ADP"]
            .rank(method="first")
            .astype(int)
        )
        agg["Pos Rank Label"] = agg["Primary Pos"] + agg["PosRank"].astype(str)

        # For SP / RP we can also use PitcherRole
        is_sp = agg["PitcherRole_display"] == "SP"
        is_rp = agg["PitcherRole_display"] == "RP"

        agg.loc[is_sp, "Role Rank Label"] = (
            "SP" + agg[is_sp].groupby(["Format"])["ADP"]
                        .rank(method="first")
                        .astype(int)
                        .astype(str)
        )
        agg.loc[is_rp, "Role Rank Label"] = (
            "RP" + agg[is_rp].groupby(["Format"])["ADP"]
                        .rank(method="first")
                        .astype(int)
                        .astype(str)
        )

        # ----------------------------
        # TREND ANALYSIS
        # ----------------------------
        # Define "early" vs "late" windows inside selected date range
        unique_dates = sorted(df["Date"].unique())
        if len(unique_dates) >= 2:
            window = max(1, len(unique_dates) // 3)
            early_dates = unique_dates[:window]
            late_dates = unique_dates[-window:]

            df_early = df[df["Date"].isin(early_dates)]
            df_late = df[df["Date"].isin(late_dates)]

            early = df_early.groupby(group_cols).agg(
                EarlyADP=("DayADP", "mean")
            ).reset_index()

            late = df_late.groupby(group_cols).agg(
                LateADP=("DayADP", "mean")
            ).reset_index()

            trends = pd.merge(early, late, how="inner", on=group_cols)
            # Positive = moving up board (ADP smaller number)
            trends["ADP Change"] = trends["EarlyADP"] - trends["LateADP"]

            agg = agg.merge(trends, how="left", on=group_cols)
        else:
            agg["EarlyADP"] = np.nan
            agg["LateADP"] = np.nan
            agg["ADP Change"] = np.nan

        # Formatting
        for c in ["ADP", "MinPick", "MaxPick", "StdDev", "EarlyADP", "LateADP", "ADP Change"]:
            agg[c] = agg[c].round(2)

        # ----------------------------
        # LAYOUT: TABS
        # ----------------------------
        tab_players, tab_trends, tab_rp = st.tabs(
            ["Player Explorer", "Trend Dashboard", "RP Competition"]
        )

        # ----------------------------
        # TAB 1: PLAYER EXPLORER
        # ----------------------------
        with tab_players:
            st.subheader("Player ADP Summary")

            # small search just within the aggregated table
            table_search = st.text_input("Filter results (player / team / position contains):", key="table_search")
            view_df = agg.copy()
            if table_search:
                mask = (
                    view_df["Player"].str.contains(table_search, case=False, na=False)
                    | view_df["Team"].str.contains(table_search, case=False, na=False)
                    | view_df["Primary Pos"].astype(str).str.contains(table_search, case=False, na=False)
                    | view_df["Pos Rank Label"].astype(str).str.contains(table_search, case=False, na=False)
                )
                view_df = view_df[mask]

            # nice default sort: by ADP
            view_df = view_df.sort_values(["Format", "ADP"])

            display_cols = [
                "Player", "Team", "Format", "Primary Pos", "PitcherRole_display",
                "Pos Rank Label", "Role Rank Label",
                "ADP", "MinPick", "MaxPick", "StdDev", "Drafts",
                "EarlyADP", "LateADP", "ADP Change"
            ]
            view_df = view_df.round(0)
            st.dataframe(
                view_df[display_cols],
                use_container_width=True,
                hide_index=True
            )

            # Player-specific chart
            st.markdown("---")
            st.subheader("Player ADP History")

            selected_players = st.multiselect(
                "Select player(s) to chart",
                options=sorted(df["Player"].unique().tolist()),
                default=[]
            )

            if selected_players:
                chart_df = df[df["Player"].isin(selected_players)]
                # average ADP per day + format
                chart_df = chart_df.groupby(["Date", "Player", "Format"]).agg(
                    DayADP=("DayADP", "mean")
                ).reset_index()

                # pivot: Date as index, Player (with format) as columns
                chart_df["PlayerLabel"] = chart_df["Player"] + " (" + chart_df["Format"] + ")"
                pivot = chart_df.pivot_table(
                    index="Date",
                    columns="PlayerLabel",
                    values="DayADP"
                ).sort_index()

                st.line_chart(pivot)

        # ----------------------------
        # TAB 2: TRENDS
        # ----------------------------
        with tab_trends:
            st.subheader("Risers & Fallers (within selected date range)")

            st.caption(
                "Trend = Early-window ADP minus Late-window ADP within your selected date range. "
                "Positive numbers = moving up the board (going earlier)."
            )

            # Only keep rows where we have both early & late ADP
            trend_df = agg.dropna(subset=["EarlyADP", "LateADP", "ADP Change"]).copy()

            st.write(trend_df)

            top_n = st.slider("How many risers/fallers to show?", min_value=5, max_value=50, value=15, step=5)

            # Top risers: biggest positive ADP Change
            risers = trend_df.sort_values("ADP Change", ascending=False).head(top_n)
            fallers = trend_df.sort_values("ADP Change", ascending=True).head(top_n)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📈 Top Risers")
                st.dataframe(
                    risers[[
                        "Player", "Team", "Format", "Primary Pos", "Pos Rank Label",
                        "ADP", "EarlyADP", "LateADP", "ADP Change", "Drafts"
                    ]],
                    use_container_width=True,
                    hide_index=True
                )

            with col2:
                st.markdown("### 📉 Top Fallers")
                st.dataframe(
                    fallers[[
                        "Player", "Team", "Format", "Primary Pos", "Pos Rank Label",
                        "ADP", "EarlyADP", "LateADP", "ADP Change", "Drafts"
                    ]],
                    use_container_width=True,
                    hide_index=True
                )

        # ----------------------------
        # TAB 3: RP COMPETITION
        # ----------------------------
        with tab_rp:
            st.subheader("Bullpen Landscape & RP Competition")

            rp = df[df["PitcherRole_display"] == "RP"].copy()
            if rp.empty:
                st.info("No RP data with current filters.")
            else:
                # Aggregate per RP per team per format
                rp_agg = rp.groupby(["Player", "Player ID", "Team", "Format"]).agg(
                    Drafts=("DayADP", "count"),
                    ADP=("DayADP", "mean"),
                    MinPick=("DayMin", "min"),
                    MaxPick=("DayMax", "max")
                ).reset_index()

                rp_agg = rp_agg[rp_agg["Drafts"] >= min_drafts]

                # Team RP ranks & ADP gaps
                rp_agg = rp_agg.sort_values(["Team", "Format", "ADP"])
                rp_agg["TeamRPIndex"] = rp_agg.groupby(["Team", "Format"]).cumcount() + 1
                rp_agg["Team Role"] = "RP" + rp_agg["TeamRPIndex"].astype(str)

                rp_agg["Next_ADP"] = rp_agg.groupby(["Team", "Format"])["ADP"].shift(-1)
                rp_agg["Picks Ahead"] = (rp_agg["Next_ADP"] - rp_agg["ADP"]).round(1)

                # Overall closer-ish rank per format
                rp_agg = rp_agg.sort_values(["Format", "ADP"])
                rp_agg["Overall RP Rank"] = (
                    rp_agg.groupby("Format")["ADP"].rank(method="first").astype(int)
                )

                for c in ["ADP", "MinPick", "MaxPick"]:
                    rp_agg[c] = rp_agg[c].round(2)

                st.caption(
                    "Picks Ahead = how many picks the current RP is going ahead of the next RP on his team "
                    "(so bigger number = more secure role)."
                )

                # Focus on competition: show only RP1s by default
                show_all_rps = st.checkbox("Show all team RPs (not just RP1)?", value=False)
                if not show_all_rps:
                    rp_view = rp_agg[rp_agg["TeamRPIndex"] == 1].copy()
                else:
                    rp_view = rp_agg.copy()

                # smaller gap = more competition
                comp_sorted = rp_view.sort_values("Picks Ahead", ascending=True)

                st.markdown("### Teams with the Tightest Bullpen Battles")
                st.dataframe(
                    comp_sorted[[
                        "Team", "Format", "Player", "Team Role", "Overall RP Rank",
                        "ADP", "MinPick", "MaxPick", "Drafts", "Picks Ahead"
                    ]],
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("---")
                st.markdown("### Raw RP Table")
                st.dataframe(
                    rp_agg[[
                        "Team", "Format", "Player", "Team Role", "Overall RP Rank",
                        "ADP", "MinPick", "MaxPick", "Drafts", "Picks Ahead"
                    ]].sort_values(["Format", "ADP"]),
                    use_container_width=True,
                    hide_index=True
                )

    if tab == "Auction Value Calculator":

        # =========================
        # RAW INPUTS (you already added these)
        # =========================
        steamer_h_raw = steamerhit.copy()
        steamer_p_raw = steamerpit.copy()

        ja_h_raw = ja_hit.copy()
        ja_p_raw = ja_pitch.copy()

        bat_h_raw = bathit.copy()
        bat_p_raw = batpit.copy()

        atc_h_raw = atchit.copy()
        atc_p_raw = atcpit.copy()

        oopsy_h_raw = oopsyhit.copy()
        oopsy_p_raw = oopsypitch.copy()

        pos_dict = dict(zip(posdata.ID,posdata.Pos))
        steamer_h_raw['Pos'] = steamer_h_raw['MLBAMID'].map(pos_dict)
        bat_h_raw['Pos'] = bat_h_raw['MLBAMID'].map(pos_dict)
        atc_h_raw['Pos'] = atc_h_raw['MLBAMID'].map(pos_dict)
        oopsy_h_raw['Pos'] = oopsy_h_raw['MLBAMID'].map(pos_dict)

        # NOTE: assumes you have these dataframes loaded elsewhere (same pattern as others):
        #   oopsy_h_raw = oopsyhit.copy()
        #   oopsy_p_raw = oopsypitch.copy()
        # If your variable names differ, just swap them below.

        # =========================
        # HELPERS
        # =========================
        def _safe_col(df, col, default=np.nan):
            return df[col] if col in df.columns else default

        def _first_present(df: pd.DataFrame, candidates: list[str]):
            for c in candidates:
                if c in df.columns:
                    return c
            return None

        def _rename_first_present(df: pd.DataFrame, candidates: list[str], to: str):
            c = _first_present(df, candidates)
            if c is not None and c != to:
                df.rename(columns={c: to}, inplace=True)

        def _coerce_numeric_cols(df: pd.DataFrame, cols: list[str]) -> None:
            for c in cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")

        def _standardize_hitters(df: pd.DataFrame, system: str) -> pd.DataFrame:
            """
            Standard output columns:
            Name, Team, Pos, PA, AB, R, HR, RBI, SB, AVG, OBP, SLG, OPS, H, BB, HBP, SF
            """
            d = df.copy()

            # --- Name / Team / Pos ---
            if system == "JA":
                _rename_first_present(d, ["Player", "Name", "NameASCII", "player_name"], "Name")
            else:
                _rename_first_present(d, ["Name", "Player", "NameASCII", "player_name", "PlayerName"], "Name")

            _rename_first_present(d, ["Team", "Tm", "team", "MLB Team"], "Team")
            _rename_first_present(d, ["Pos", "POS", "Position", "Positions", "Position(s)"], "Pos")

            if "Pos" not in d.columns:
                d["Pos"] = "UTIL"

            # --- Core counting stats ---
            # These are usually consistent across systems, but we still guard them.
            for c in ["PA", "AB", "R", "HR", "RBI", "SB", "H", "BB", "HBP", "SF"]:
                if c not in d.columns:
                    d[c] = np.nan

            # --- Rate stats ---
            for c in ["AVG", "OBP", "SLG", "OPS"]:
                if c not in d.columns:
                    d[c] = np.nan

            # Common alternates some files use
            # (Only fill if the standard col is missing/empty)
            if d["AVG"].isna().all():
                alt = _first_present(d, ["BA", "AVG_"])
                if alt:
                    d["AVG"] = pd.to_numeric(d[alt], errors="coerce")

            if d["OBP"].isna().all():
                alt = _first_present(d, ["OBP_"])
                if alt:
                    d["OBP"] = pd.to_numeric(d[alt], errors="coerce")

            if d["SLG"].isna().all():
                alt = _first_present(d, ["SLG_"])
                if alt:
                    d["SLG"] = pd.to_numeric(d[alt], errors="coerce")

            # OPS: compute if missing but OBP/SLG available
            if d["OPS"].isna().all() and (not d["OBP"].isna().all()) and (not d["SLG"].isna().all()):
                d["OPS"] = pd.to_numeric(d["OBP"], errors="coerce") + pd.to_numeric(d["SLG"], errors="coerce")

            # Build AB if still missing but PA exists (rough fallback)
            if d["AB"].isna().all() and (not d["PA"].isna().all()):
                d["AB"] = np.where(pd.to_numeric(d["PA"], errors="coerce").notna(), (pd.to_numeric(d["PA"], errors="coerce") * 0.86), np.nan)

            # --- Cleanup / types ---
            d = d.dropna(subset=["Name"]).copy()
            d["Team"] = d["Team"].fillna("")
            d["Pos"] = d["Pos"].fillna("UTIL")

            _coerce_numeric_cols(d, ["PA", "AB", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "H", "BB", "HBP", "SF"])

            d = d[d["PA"].fillna(0) > 0].copy()
            return d

        def _standardize_pitchers(df: pd.DataFrame, system: str) -> pd.DataFrame:
            """
            Standard output columns:
            Name, Team, Pos, GS, IP, W, SV, ERA, WHIP, SO, BB, K/9, BB/9
            """
            d = df.copy()

            # --- Name / Team ---
            if system == "JA":
                _rename_first_present(d, ["Pitcher", "Name", "NameASCII", "player_name"], "Name")
            else:
                _rename_first_present(d, ["Name", "Pitcher", "NameASCII", "player_name", "PlayerName"], "Name")

            _rename_first_present(d, ["Team", "Tm", "team", "MLB Team"], "Team")

            # --- Normalize SO/K and core cols ---
            # Some sets use K instead of SO
            if "SO" not in d.columns and "K" in d.columns:
                d["SO"] = d["K"]
            if "SO" not in d.columns:
                # sometimes "SO" is "SO_" etc
                alt = _first_present(d, ["SO_", "Ks", "KSO"])
                if alt:
                    d["SO"] = d[alt]
                else:
                    d["SO"] = np.nan

            # Ensure core columns exist
            for c in ["GS", "IP", "W", "SV", "ERA", "WHIP", "SO", "BB"]:
                if c not in d.columns:
                    d[c] = np.nan

            # Infer Pos (SP/RP) by GS if not provided
            if "Pos" not in d.columns:
                gs = pd.to_numeric(_safe_col(d, "GS", 0), errors="coerce").fillna(0)
                d["Pos"] = np.where(gs > 0, "SP", "RP")
            else:
                d["Pos"] = d["Pos"].fillna("P")

            # Compute K/9 and BB/9 if missing
            d["IP"] = pd.to_numeric(_safe_col(d, "IP", np.nan), errors="coerce")
            d["BB"] = pd.to_numeric(_safe_col(d, "BB", np.nan), errors="coerce")
            d["SO"] = pd.to_numeric(_safe_col(d, "SO", np.nan), errors="coerce")

            if "K/9" not in d.columns:
                d["K/9"] = np.where(d["IP"].fillna(0) > 0, (d["SO"] * 9) / d["IP"], np.nan)
            if "BB/9" not in d.columns:
                d["BB/9"] = np.where(d["IP"].fillna(0) > 0, (d["BB"] * 9) / d["IP"], np.nan)

            # Final type coercion
            d = d.dropna(subset=["Name"]).copy()
            d["Team"] = d["Team"].fillna("")
            d["Pos"] = d["Pos"].fillna("P")

            _coerce_numeric_cols(d, ["GS", "IP", "W", "SV", "ERA", "WHIP", "SO", "BB", "K/9", "BB/9"])

            d = d[d["IP"].fillna(0) > 0].copy()
            return d

        def _parse_roster_string(roster_str: str) -> list[str]:
            parts = [p.strip().upper() for p in roster_str.split(",") if p.strip()]
            return parts

        def _is_pitch_slot(slot: str) -> bool:
            slot = slot.upper().strip()
            return slot in {"SP", "RP", "P"}

        def _compute_marginal_hit_rate(df: pd.DataFrame, rate_col: str) -> pd.Series:
            """
            Convert a rate stat into a counting-like contribution using playing time.
            AVG/SLG use AB if present; OBP/OPS use PA.
            """
            rate = pd.to_numeric(df[rate_col], errors="coerce")

            if rate_col in {"AVG", "SLG"}:
                denom = pd.to_numeric(df["AB"], errors="coerce")
            else:
                denom = pd.to_numeric(df["PA"], errors="coerce")

            denom = denom.fillna(0)
            if denom.sum() > 0:
                lg_rate = np.nansum(rate * denom) / np.nansum(denom)
            else:
                lg_rate = np.nanmean(rate)

            return (rate - lg_rate) * denom

        def _compute_marginal_pitch_rate(df: pd.DataFrame, rate_col: str) -> pd.Series:
            """
            Convert a rate stat into a counting-like contribution.
            Lower-is-better for ERA/WHIP/BB9; higher-is-better for K9.
            """
            ip = pd.to_numeric(df["IP"], errors="coerce").fillna(0)
            r = pd.to_numeric(df[rate_col], errors="coerce")

            if rate_col in {"ERA", "WHIP"}:
                lg = np.nansum(r * ip) / np.nansum(ip) if ip.sum() > 0 else np.nanmean(r)
                return (lg - r) * ip  # better (lower) => positive

            if rate_col == "BB/9":
                w = ip / 9.0
                lg = np.nansum(r * w) / np.nansum(w) if w.sum() > 0 else np.nanmean(r)
                return (lg - r) * w

            if rate_col == "K/9":
                w = ip / 9.0
                lg = np.nansum(r * w) / np.nansum(w) if w.sum() > 0 else np.nanmean(r)
                return (r - lg) * w  # better (higher) => positive

            return r

        def _zscore(series: pd.Series) -> pd.Series:
            s = pd.to_numeric(series, errors="coerce")
            mu = np.nanmean(s)
            sd = np.nanstd(s)
            if not np.isfinite(sd) or sd == 0:
                sd = 1.0
            return (s - mu) / sd

        def _auction_values(
            hitters: pd.DataFrame,
            pitchers: pd.DataFrame,
            hit_cats: list[str],
            pit_cats: list[str],
            roster_slots: list[str],
            teams: int,
            budget_per_team: int,
            hitter_pct: float,
        ):
            # How many total players are expected to be drafted (starters only)
            total_slots = len(roster_slots) * teams
            n_hit = int(round(total_slots * hitter_pct))
            n_pit = total_slots - n_hit

            total_budget = teams * budget_per_team
            hit_budget = total_budget * hitter_pct
            pit_budget = total_budget - hit_budget

            # --- Build category matrices (with proper handling for rate cats) ---
            hit_df = hitters.copy()
            pit_df = pitchers.copy()

            hit_feat = {}
            for c in hit_cats:
                if c in {"AVG", "OBP", "SLG", "OPS"}:
                    hit_feat[c] = _compute_marginal_hit_rate(hit_df, c)
                else:
                    hit_feat[c] = pd.to_numeric(hit_df[c], errors="coerce") if c in hit_df.columns else np.nan

            pit_feat = {}
            for c in pit_cats:
                if c in {"ERA", "WHIP", "K/9", "BB/9"}:
                    pit_feat[c] = _compute_marginal_pitch_rate(pit_df, c)
                else:
                    pit_feat[c] = pd.to_numeric(pit_df[c], errors="coerce") if c in pit_df.columns else np.nan

            # --- First pass z-scores to identify the drafted pool ---
            for c, v in hit_feat.items():
                hit_df[f"z_{c}"] = _zscore(v)
            hit_df["z_total_pre"] = hit_df[[f"z_{c}" for c in hit_cats]].sum(axis=1)

            for c, v in pit_feat.items():
                pit_df[f"z_{c}"] = _zscore(v)
            pit_df["z_total_pre"] = pit_df[[f"z_{c}" for c in pit_cats]].sum(axis=1)

            hit_pool = hit_df.sort_values("z_total_pre", ascending=False).head(n_hit).copy()
            pit_pool = pit_df.sort_values("z_total_pre", ascending=False).head(n_pit).copy()

            # --- Second pass: recompute z within drafted pool (closer to FG behavior) ---
            for c in hit_cats:
                if c in {"AVG", "OBP", "SLG", "OPS"}:
                    vals = _compute_marginal_hit_rate(hit_pool, c)
                else:
                    vals = pd.to_numeric(hit_pool[c], errors="coerce") if c in hit_pool.columns else np.nan
                hit_pool[f"z_{c}"] = _zscore(vals)
            hit_pool["z_total"] = hit_pool[[f"z_{c}" for c in hit_cats]].sum(axis=1)

            for c in pit_cats:
                if c in {"ERA", "WHIP", "K/9", "BB/9"}:
                    vals = _compute_marginal_pitch_rate(pit_pool, c)
                else:
                    vals = pd.to_numeric(pit_pool[c], errors="coerce") if c in pit_pool.columns else np.nan
                pit_pool[f"z_{c}"] = _zscore(vals)
            pit_pool["z_total"] = pit_pool[[f"z_{c}" for c in pit_cats]].sum(axis=1)

            # Replacement baselines: last drafted at each pool
            hit_rep = hit_pool["z_total"].min()
            pit_rep = pit_pool["z_total"].min()

            hit_pool["AAR"] = (hit_pool["z_total"] - hit_rep).clip(lower=0)
            pit_pool["AAR"] = (pit_pool["z_total"] - pit_rep).clip(lower=0)

            # Dollar allocation (optionally $1 floor)
            def allocate(pool: pd.DataFrame, pool_budget: float, n: int) -> pd.DataFrame:
                out = pool.copy()
                if pool_budget >= n:
                    floor = 1.0
                    rem = pool_budget - (floor * n)
                    aar_sum = out["AAR"].sum()
                    if aar_sum > 0 and rem > 0:
                        out["$"] = floor + (out["AAR"] / aar_sum) * rem
                    else:
                        out["$"] = floor
                else:
                    aar_sum = out["AAR"].sum()
                    if aar_sum > 0:
                        out["$"] = (out["AAR"] / aar_sum) * pool_budget
                    else:
                        out["$"] = pool_budget / max(n, 1)
                out["$"] = out["$"].round(1)
                return out

            hit_vals = allocate(hit_pool, hit_budget, n_hit)
            pit_vals = allocate(pit_pool, pit_budget, n_pit)

            return hit_vals, pit_vals, {
                "teams": teams,
                "budget_per_team": budget_per_team,
                "total_budget": total_budget,
                "hitter_pct": hitter_pct,
                "hit_budget": hit_budget,
                "pit_budget": pit_budget,
                "slots_per_team": len(roster_slots),
                "total_drafted": total_slots,
                "drafted_hitters": n_hit,
                "drafted_pitchers": n_pit,
            }

        # =========================
        # UI
        # =========================
        st.subheader("Auction Value Calculator")

        left, right = st.columns([1, 1], gap="large")

        with left:
            proj_system = st.radio(
                "Projection system",
                ["JA", "Steamer", "THE BAT", "ATC", "OOPSY"],
                index=0,
                horizontal=True,
                help="Choose the projection set used to calculate auction values.",
            )

            roster_default = (
                "C, 1B, 2B, 3B, SS, 1B/3B, 2B/SS, "
                "OF, OF, OF, OF, OF, UTIL, UTIL, "
                "SP, SP, SP, SP, SP, SP, RP, RP, RP"
            )
            roster_str = st.text_area(
                "Starting lineup slots (comma-separated)",
                value=roster_default,
                height=90,
                help="Use SP/RP for pitchers. Anything else is treated as hitter/UTIL.",
            )
            roster_slots = _parse_roster_string(roster_str)

            teams = st.number_input("Teams", min_value=4, max_value=30, value=12, step=1)
            budget_per_team = st.number_input("Budget per team ($)", min_value=50, max_value=1000, value=260, step=10)

            hitter_pct = st.slider(
                "Drafted player split: % hitters",
                min_value=0.40,
                max_value=0.80,
                value=0.60,
                step=0.01,
            )
            st.caption(f"Pitchers: {int(round((1 - hitter_pct) * 100))}%")

        # =========================
        # Load & standardize per selection
        # =========================
        if proj_system == "JA":
            hitters = _standardize_hitters(ja_h_raw, "JA")
            pitchers = _standardize_pitchers(ja_p_raw, "JA")
        elif proj_system == "Steamer":
            hitters = _standardize_hitters(steamer_h_raw, "Steamer")
            pitchers = _standardize_pitchers(steamer_p_raw, "Steamer")
        elif proj_system == "THE BAT":
            hitters = _standardize_hitters(bat_h_raw, "THE BAT")
            pitchers = _standardize_pitchers(bat_p_raw, "THE BAT")
        elif proj_system == "ATC":
            hitters = _standardize_hitters(atc_h_raw, "ATC")
            pitchers = _standardize_pitchers(atc_p_raw, "ATC")
        else:  # OOPSY
            hitters = _standardize_hitters(oopsy_h_raw, "OOPSY")
            pitchers = _standardize_pitchers(oopsy_p_raw, "OOPSY")

        # =========================
        # Category pickers + preview
        # =========================
        with right:
            st.markdown("### League categories")

            hit_default = ["R", "HR", "RBI", "SB", "AVG"]  # common 5x5 hitters
            pit_default = ["W", "SV", "ERA", "WHIP", "SO"]  # common 5x5 pitchers

            hit_all = ["R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "PA"]
            pit_all = ["W", "SV", "ERA", "WHIP", "SO", "K/9", "BB/9", "IP", "GS"]

            hit_cats = st.multiselect("Hitting categories", hit_all, default=hit_default)
            pit_cats = st.multiselect("Pitching categories", pit_all, default=pit_default)

            st.markdown("### Projection table view")
            show_side = st.radio("Show", ["Hitters", "Pitchers"], index=0, horizontal=True)

            show_hit_cols = ["Name", "Team", "Pos", "PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS"]
            show_pit_cols = ["Name", "Team", "Pos", "GS", "IP", "W", "SV", "ERA", "WHIP", "SO", "K/9", "BB/9"]

            if show_side == "Hitters":
                cols = [c for c in show_hit_cols if c in hitters.columns]
                st.dataframe(hitters[cols].sort_values("PA", ascending=False), use_container_width=True, height=420)
            else:
                cols = [c for c in show_pit_cols if c in pitchers.columns]
                st.dataframe(pitchers[cols].sort_values("IP", ascending=False), use_container_width=True, height=420)

        # =========================
        # RUN CALC
        # =========================
        st.divider()
        c1, c2 = st.columns([1, 3], gap="large")

        with c1:
            run = st.button("Run Auction Values", type="primary", use_container_width=True)

        with c2:
            pit_slots = sum(_is_pitch_slot(s) for s in roster_slots)
            hit_slots = len(roster_slots) - pit_slots
            st.caption(
                f"Slots per team: **{len(roster_slots)}** "
                f"(Hit: **{hit_slots}**, Pitch: **{pit_slots}**) • "
                f"Total drafted (starters): **{len(roster_slots) * int(teams)}**"
            )

        if run:
            if len(hit_cats) == 0 or len(pit_cats) == 0:
                st.error("Please select at least one hitting category and one pitching category.")
            else:
                hit_vals, pit_vals, meta = _auction_values(
                    hitters=hitters,
                    pitchers=pitchers,
                    hit_cats=hit_cats,
                    pit_cats=pit_cats,
                    roster_slots=roster_slots,
                    teams=int(teams),
                    budget_per_team=int(budget_per_team),
                    hitter_pct=float(hitter_pct),
                )

                st.success("Auction values calculated.")

                # Summary metrics
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("Total Budget", f"${meta['total_budget']:.0f}")
                s2.metric("Hitter Budget", f"${meta['hit_budget']:.0f}")
                s3.metric("Pitcher Budget", f"${meta['pit_budget']:.0f}")
                s4.metric("Drafted Players", f"{meta['total_drafted']}")

                # Combine + display
                hit_out_cols = ["Name", "Team", "Pos", "$"] + [c for c in ["PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS"] if c in hit_vals.columns]
                pit_out_cols = ["Name", "Team", "Pos", "$"] + [c for c in ["GS", "IP", "W", "SV", "ERA", "WHIP", "SO", "K/9", "BB/9"] if c in pit_vals.columns]

                st.markdown("### Top Auction Values — Hitters")
                st.dataframe(hit_vals[hit_out_cols].sort_values("$", ascending=False).reset_index(drop=True), use_container_width=True, height=420)

                st.markdown("### Top Auction Values — Pitchers")
                st.dataframe(pit_vals[pit_out_cols].sort_values("$", ascending=False).reset_index(drop=True), use_container_width=True, height=420)

                combined = pd.concat(
                    [
                        hit_vals.assign(Side="Hitter")[["Side"] + hit_out_cols],
                        pit_vals.assign(Side="Pitcher")[["Side"] + pit_out_cols],
                    ],
                    ignore_index=True,
                ).sort_values(["Side", "$"], ascending=[True, False])

                st.download_button(
                    f"Download auction values (CSV) — {proj_system}",
                    data=combined.to_csv(index=False).encode("utf-8"),
                    file_name=f"auction_values_{proj_system.lower().replace(' ', '_')}_2026.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

                with st.expander("How this is being calculated (quick)"):
                    st.markdown(
                        """
                        - Counting categories use **z-scores** directly (higher = better).
                        - Rate categories are converted to counting-like **marginal contributions** using playing time:
                        - Hitters: `(player_rate - league_rate) * PA` (OBP/OPS) or `* AB` (AVG/SLG).
                        - Pitchers: `(league_rate - player_rate) * IP` for ERA/WHIP; K/9 and BB/9 use IP/9 weighting.
                        - We identify the drafted pool, then recompute z-scores **within the drafted pool**.
                        - Dollar values are distributed by **above-replacement** total z-score, with a **$1 floor** when possible.
                        """.strip()
                    )


    if tab == "Auction Value Calculator_Back":

        steamer_h_raw = steamerhit.copy()
        steamer_p_raw = steamerpit.copy()

        ja_h_raw = ja_hit.copy()
        ja_p_raw = ja_pitch.copy()
        
        bat_h_raw = bathit.copy()
        bat_p_raw = batpit.copy()

        atc_h_raw = atc_hitters.copy()
        atc_p_raw = atc_pitchers.copy()


        # =========================
        # HELPERS
        # =========================
        def _safe_col(df, col, default=np.nan):
            return df[col] if col in df.columns else default

        def _standardize_hitters(df: pd.DataFrame, system: str) -> pd.DataFrame:
            d = df.copy()

            if system == "JA":
                # Expected: Player, Team, Pos, PA, R, HR, RBI, SB, AVG/OBP/SLG/OPS (or can compute OPS)
                d.rename(columns={"Player": "Name"}, inplace=True)
                if "Pos" not in d.columns:
                    d["Pos"] = "UTIL"
            else:
                # Steamer: Name, Team, PA, R, HR, RBI, SB, etc. (no positions in file)
                d.rename(columns={"Name": "Name", "Team": "Team"}, inplace=True)
                if "Pos" not in d.columns:
                    d["Pos"] = "UTIL"

            # Ensure core numeric cols exist
            for c in ["PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS"]:
                if c not in d.columns:
                    d[c] = np.nan

            # If OPS missing but OBP/SLG present
            if d["OPS"].isna().all() and (not d["OBP"].isna().all()) and (not d["SLG"].isna().all()):
                d["OPS"] = d["OBP"].astype(float) + d["SLG"].astype(float)

            # Build AB if available; else approximate AB from PA (rough fallback)
            if "AB" not in d.columns:
                d["AB"] = np.where(d["PA"].notna(), (d["PA"] * 0.86), np.nan)  # loose fallback
            # For OBP components if available
            # (JA hitter file often has BB, HBP, SF; Steamer has BB, HBP, SF too)
            for c in ["H", "BB", "HBP", "SF"]:
                if c not in d.columns:
                    d[c] = np.nan

            # Basic cleanup
            d = d.dropna(subset=["Name"]).copy()
            d["Team"] = d["Team"].fillna("")
            d["Pos"] = d["Pos"].fillna("UTIL")
            d["PA"] = pd.to_numeric(d["PA"], errors="coerce")
            for c in ["R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "AB"]:
                d[c] = pd.to_numeric(d[c], errors="coerce")

            d = d[d["PA"].fillna(0) > 0].copy()
            return d

        def _standardize_pitchers(df: pd.DataFrame, system: str) -> pd.DataFrame:
            d = df.copy()

            if system == "JA":
                # Expected: Pitcher, Team, GS, IP, W, SV, ERA, WHIP, K/9, BB/9, K (or SO)
                d.rename(columns={"Pitcher": "Name"}, inplace=True)
                if "Pos" not in d.columns:
                    d["Pos"] = np.where(pd.to_numeric(_safe_col(d, "GS", 0), errors="coerce").fillna(0) > 0, "SP", "RP")
            else:
                # Steamer: Name, Team, GS, IP, W, SV, ERA, WHIP, SO, BB, etc (no positions in file)
                # We'll infer SP/RP by GS
                if "Pos" not in d.columns:
                    gs = pd.to_numeric(_safe_col(d, "GS", 0), errors="coerce").fillna(0)
                    d["Pos"] = np.where(gs > 0, "SP", "RP")

            # Normalize SO naming
            if "SO" not in d.columns and "K" in d.columns:
                d["SO"] = d["K"]
            if "SO" not in d.columns:
                d["SO"] = np.nan

            # Compute K/9 and BB/9 if missing
            d["IP"] = pd.to_numeric(_safe_col(d, "IP", np.nan), errors="coerce")
            d["BB"] = pd.to_numeric(_safe_col(d, "BB", np.nan), errors="coerce")
            d["SO"] = pd.to_numeric(_safe_col(d, "SO", np.nan), errors="coerce")

            if "K/9" not in d.columns:
                d["K/9"] = np.where(d["IP"].fillna(0) > 0, (d["SO"] * 9) / d["IP"], np.nan)
            if "BB/9" not in d.columns:
                d["BB/9"] = np.where(d["IP"].fillna(0) > 0, (d["BB"] * 9) / d["IP"], np.nan)

            # Ensure cols exist
            for c in ["GS", "IP", "W", "SV", "ERA", "WHIP", "SO", "K/9", "BB/9"]:
                if c not in d.columns:
                    d[c] = np.nan

            # Cleanup
            d = d.dropna(subset=["Name"]).copy()
            d["Team"] = d["Team"].fillna("")
            d["Pos"] = d["Pos"].fillna("P")
            for c in ["GS", "IP", "W", "SV", "ERA", "WHIP", "SO", "K/9", "BB/9"]:
                d[c] = pd.to_numeric(d[c], errors="coerce")
            d = d[d["IP"].fillna(0) > 0].copy()
            return d

        def _parse_roster_string(roster_str: str) -> list[str]:
            parts = [p.strip().upper() for p in roster_str.split(",") if p.strip()]
            return parts

        def _is_pitch_slot(slot: str) -> bool:
            slot = slot.upper().strip()
            return slot in {"SP", "RP", "P"}

        def _compute_marginal_hit_rate(df: pd.DataFrame, rate_col: str) -> pd.Series:
            """
            Convert a rate stat into a counting-like contribution using playing time.
            AVG/SLG use AB if present; OBP/OPS use PA.
            """
            rate = pd.to_numeric(df[rate_col], errors="coerce")

            if rate_col in {"AVG", "SLG"}:
                denom = pd.to_numeric(df["AB"], errors="coerce")
            else:
                denom = pd.to_numeric(df["PA"], errors="coerce")

            denom = denom.fillna(0)
            lg_rate = np.nan
            if denom.sum() > 0:
                lg_rate = np.nansum(rate * denom) / np.nansum(denom)
            else:
                lg_rate = np.nanmean(rate)

            return (rate - lg_rate) * denom

        def _compute_marginal_pitch_rate(df: pd.DataFrame, rate_col: str) -> pd.Series:
            """
            Convert a rate stat into a counting-like contribution.
            Lower-is-better for ERA/WHIP/BB9; higher-is-better for K9.
            """
            ip = pd.to_numeric(df["IP"], errors="coerce").fillna(0)
            r = pd.to_numeric(df[rate_col], errors="coerce")

            if rate_col in {"ERA", "WHIP"}:
                # Weight by IP
                lg = np.nansum(r * ip) / np.nansum(ip) if ip.sum() > 0 else np.nanmean(r)
                return (lg - r) * ip  # better (lower) => positive
            if rate_col == "BB/9":
                # Weight by IP/9
                w = ip / 9.0
                lg = np.nansum(r * w) / np.nansum(w) if w.sum() > 0 else np.nanmean(r)
                return (lg - r) * w
            if rate_col == "K/9":
                w = ip / 9.0
                lg = np.nansum(r * w) / np.nansum(w) if w.sum() > 0 else np.nanmean(r)
                return (r - lg) * w  # better (higher) => positive

            # Fallback
            return r

        def _zscore(series: pd.Series) -> pd.Series:
            s = pd.to_numeric(series, errors="coerce")
            mu = np.nanmean(s)
            sd = np.nanstd(s)
            if not np.isfinite(sd) or sd == 0:
                sd = 1.0
            return (s - mu) / sd

        def _auction_values(
            hitters: pd.DataFrame,
            pitchers: pd.DataFrame,
            hit_cats: list[str],
            pit_cats: list[str],
            roster_slots: list[str],
            teams: int,
            budget_per_team: int,
            hitter_pct: float,
        ):
            # How many total players are expected to be drafted (starters only)
            total_slots = len(roster_slots) * teams
            n_hit = int(round(total_slots * hitter_pct))
            n_pit = total_slots - n_hit

            total_budget = teams * budget_per_team
            hit_budget = total_budget * hitter_pct
            pit_budget = total_budget - hit_budget

            # --- Build category matrices (with proper handling for rate cats) ---
            hit_df = hitters.copy()
            pit_df = pitchers.copy()

            hit_feat = {}
            for c in hit_cats:
                if c in {"AVG", "OBP", "SLG", "OPS"}:
                    hit_feat[c] = _compute_marginal_hit_rate(hit_df, c)
                else:
                    hit_feat[c] = pd.to_numeric(hit_df[c], errors="coerce")

            pit_feat = {}
            for c in pit_cats:
                if c in {"ERA", "WHIP", "K/9", "BB/9"}:
                    pit_feat[c] = _compute_marginal_pitch_rate(pit_df, c)
                else:
                    pit_feat[c] = pd.to_numeric(pit_df[c], errors="coerce")

            # --- First pass z-scores to identify the drafted pool ---
            for c, v in hit_feat.items():
                hit_df[f"z_{c}"] = _zscore(v)
            hit_df["z_total_pre"] = hit_df[[f"z_{c}" for c in hit_cats]].sum(axis=1)

            for c, v in pit_feat.items():
                pit_df[f"z_{c}"] = _zscore(v)
            pit_df["z_total_pre"] = pit_df[[f"z_{c}" for c in pit_cats]].sum(axis=1)

            hit_pool = hit_df.sort_values("z_total_pre", ascending=False).head(n_hit).copy()
            pit_pool = pit_df.sort_values("z_total_pre", ascending=False).head(n_pit).copy()

            # --- Second pass: recompute z within drafted pool (closer to FG behavior) ---
            for c in hit_cats:
                if c in {"AVG", "OBP", "SLG", "OPS"}:
                    vals = _compute_marginal_hit_rate(hit_pool, c)
                else:
                    vals = pd.to_numeric(hit_pool[c], errors="coerce")
                hit_pool[f"z_{c}"] = _zscore(vals)
            hit_pool["z_total"] = hit_pool[[f"z_{c}" for c in hit_cats]].sum(axis=1)

            for c in pit_cats:
                if c in {"ERA", "WHIP", "K/9", "BB/9"}:
                    vals = _compute_marginal_pitch_rate(pit_pool, c)
                else:
                    vals = pd.to_numeric(pit_pool[c], errors="coerce")
                pit_pool[f"z_{c}"] = _zscore(vals)
            pit_pool["z_total"] = pit_pool[[f"z_{c}" for c in pit_cats]].sum(axis=1)

            # Replacement baselines: last drafted at each pool
            hit_rep = hit_pool["z_total"].min()
            pit_rep = pit_pool["z_total"].min()

            hit_pool["AAR"] = (hit_pool["z_total"] - hit_rep).clip(lower=0)
            pit_pool["AAR"] = (pit_pool["z_total"] - pit_rep).clip(lower=0)

            # Dollar allocation (optionally $1 floor)
            def allocate(pool: pd.DataFrame, pool_budget: float, n: int) -> pd.DataFrame:
                out = pool.copy()
                # $1 floor if possible
                if pool_budget >= n:
                    floor = 1.0
                    rem = pool_budget - (floor * n)
                    aar_sum = out["AAR"].sum()
                    if aar_sum > 0 and rem > 0:
                        out["$"] = floor + (out["AAR"] / aar_sum) * rem
                    else:
                        out["$"] = floor
                else:
                    # Not enough to floor everyone; distribute proportionally (or evenly if all zero)
                    aar_sum = out["AAR"].sum()
                    if aar_sum > 0:
                        out["$"] = (out["AAR"] / aar_sum) * pool_budget
                    else:
                        out["$"] = pool_budget / max(n, 1)
                out["$"] = out["$"].round(1)
                return out

            hit_vals = allocate(hit_pool, hit_budget, n_hit)
            pit_vals = allocate(pit_pool, pit_budget, n_pit)

            return hit_vals, pit_vals, {
                "teams": teams,
                "budget_per_team": budget_per_team,
                "total_budget": total_budget,
                "hitter_pct": hitter_pct,
                "hit_budget": hit_budget,
                "pit_budget": pit_budget,
                "slots_per_team": len(roster_slots),
                "total_drafted": total_slots,
                "drafted_hitters": n_hit,
                "drafted_pitchers": n_pit,
            }

        # =========================
        # UI
        # =========================
        st.subheader("Auction Value Calculator")

        left, right = st.columns([1, 1], gap="large")

        with left:
            proj_system = st.radio(
                "Projection system",
                ["JA", "Steamer"],
                index=0,
                horizontal=True,
                help="Default: JA",
            )

            roster_default = (
                "C, 1B, 2B, 3B, SS, 1B/3B, 2B/SS, "
                "OF, OF, OF, OF, OF, UTIL, UTIL, "
                "SP, SP, SP, SP, SP, SP, RP, RP, RP"
            )
            roster_str = st.text_area(
                "Starting lineup slots (comma-separated)",
                value=roster_default,
                height=90,
                help="Use SP/RP for pitchers. Anything else is treated as hitter/UTIL.",
            )
            roster_slots = _parse_roster_string(roster_str)

            teams = st.number_input("Teams", min_value=4, max_value=30, value=12, step=1)
            budget_per_team = st.number_input("Budget per team ($)", min_value=50, max_value=1000, value=260, step=10)

            hitter_pct = st.slider(
                "Drafted player split: % hitters",
                min_value=0.40,
                max_value=0.80,
                value=0.60,
                step=0.01,
            )
            st.caption(f"Pitchers: {int(round((1 - hitter_pct) * 100))}%")

        # Load and standardize per selection
        if proj_system == "JA":
            hitters = _standardize_hitters(ja_h_raw, "JA")
            pitchers = _standardize_pitchers(ja_p_raw, "JA")
        else:
            hitters = _standardize_hitters(steamer_h_raw, "Steamer")
            pitchers = _standardize_pitchers(steamer_p_raw, "Steamer")

        # Category pickers
        with right:
            st.markdown("### League categories")

            hit_default = ["R", "HR", "RBI", "SB", "AVG"]  # common 5x5 hitters
            pit_default = ["W", "SV", "ERA", "WHIP", "SO"]  # common 5x5 pitchers

            hit_all = ["R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "PA"]
            pit_all = ["W", "SV", "ERA", "WHIP", "SO", "K/9", "BB/9", "IP", "GS"]

            hit_cats = st.multiselect("Hitting categories", hit_all, default=hit_default)
            pit_cats = st.multiselect("Pitching categories", pit_all, default=pit_default)

            st.markdown("### Projection table view")
            show_side = st.radio("Show", ["Hitters", "Pitchers"], index=0, horizontal=True)

            show_hit_cols = ["Name", "Team", "Pos", "PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS"]
            show_pit_cols = ["Name", "Team", "Pos", "GS", "IP", "W", "SV", "ERA", "WHIP", "SO", "K/9", "BB/9"]

            if show_side == "Hitters":
                cols = [c for c in show_hit_cols if c in hitters.columns]
                st.dataframe(hitters[cols].sort_values("PA", ascending=False), use_container_width=True, height=420)
            else:
                cols = [c for c in show_pit_cols if c in pitchers.columns]
                st.dataframe(pitchers[cols].sort_values("IP", ascending=False), use_container_width=True, height=420)

        # =========================
        # RUN CALC
        # =========================
        st.divider()
        c1, c2 = st.columns([1, 3], gap="large")

        with c1:
            run = st.button("Run Auction Values", type="primary", use_container_width=True)

        with c2:
            # quick roster summary
            pit_slots = sum(_is_pitch_slot(s) for s in roster_slots)
            hit_slots = len(roster_slots) - pit_slots
            st.caption(
                f"Slots per team: **{len(roster_slots)}** "
                f"(Hit: **{hit_slots}**, Pitch: **{pit_slots}**) • "
                f"Total drafted (starters): **{len(roster_slots) * int(teams)}**"
            )

        if run:
            if len(hit_cats) == 0 or len(pit_cats) == 0:
                st.error("Please select at least one hitting category and one pitching category.")
            else:
                hit_vals, pit_vals, meta = _auction_values(
                    hitters=hitters,
                    pitchers=pitchers,
                    hit_cats=hit_cats,
                    pit_cats=pit_cats,
                    roster_slots=roster_slots,
                    teams=int(teams),
                    budget_per_team=int(budget_per_team),
                    hitter_pct=float(hitter_pct),
                )

                st.success("Auction values calculated.")

                # Summary metrics
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("Total Budget", f"${meta['total_budget']:.0f}")
                s2.metric("Hitter Budget", f"${meta['hit_budget']:.0f}")
                s3.metric("Pitcher Budget", f"${meta['pit_budget']:.0f}")
                s4.metric("Drafted Players", f"{meta['total_drafted']}")

                # Combine + display
                hit_out_cols = ["Name", "Team", "Pos", "$"] + [c for c in ["PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS"] if c in hit_vals.columns]
                pit_out_cols = ["Name", "Team", "Pos", "$"] + [c for c in ["GS", "IP", "W", "SV", "ERA", "WHIP", "SO", "K/9", "BB/9"] if c in pit_vals.columns]

                st.markdown("### Top Auction Values — Hitters")
                st.dataframe(hit_vals[hit_out_cols].sort_values("$", ascending=False).reset_index(drop=True), use_container_width=True, height=420)

                st.markdown("### Top Auction Values — Pitchers")
                st.dataframe(pit_vals[pit_out_cols].sort_values("$", ascending=False).reset_index(drop=True), use_container_width=True, height=420)

                combined = pd.concat(
                    [
                        hit_vals.assign(Side="Hitter")[["Side"] + hit_out_cols],
                        pit_vals.assign(Side="Pitcher")[["Side"] + pit_out_cols],
                    ],
                    ignore_index=True,
                ).sort_values(["Side", "$"], ascending=[True, False])

                st.download_button(
                    "Download auction values (CSV)",
                    data=combined.to_csv(index=False).encode("utf-8"),
                    file_name=f"auction_values_{proj_system.lower()}_2026.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

                with st.expander("How this is being calculated (quick)"):
                    st.markdown(
                        """
                        - Counting categories use **z-scores** directly (higher = better).
                        - Rate categories are converted to counting-like **marginal contributions** using playing time:
                        - Hitters: `(player_rate - league_rate) * PA` (OBP/OPS) or `* AB` (AVG/SLG).
                        - Pitchers: `(league_rate - player_rate) * IP` for ERA/WHIP; K/9 and BB/9 use IP/9 weighting.
                        - We identify the drafted pool, then recompute z-scores **within the drafted pool**.
                        - Dollar values are distributed by **above-replacement** total z-score, with a **$1 floor** when possible.
                                            """.strip()
                        )

    if tab == "2026 Projections":
        # =========================
        # ===== DEBUG (optional) ===
        # =========================
        # st.write(oopsyhit)
        # st.write(oopsypitch)

        # === POSITION DATA ===
        pos_data = adp2026[["Player", "Player ID", "Position(s)"]].drop_duplicates()

        # =========================
        # ===== SRV FUNCTIONS =====
        # =========================
        def calculateSRV_Hitters(hitdf: pd.DataFrame, merge_df: pd.DataFrame | None = None):
            df = hitdf.copy()

            count_cats = ["R", "HR", "RBI", "SB"]
            for cat in count_cats:
                std = df[cat].std(ddof=0)
                df[f"{cat}_z"] = (df[cat] - df[cat].mean()) / (std if std != 0 else 1.0)

            total_ab = df["AB"].sum()
            lg_avg = np.divide((df["AVG"] * df["AB"]).sum(), total_ab) if total_ab else df["AVG"].mean()

            df["AVG_contrib"] = (df["AVG"] - lg_avg) * df["AB"]
            std = df["AVG_contrib"].std(ddof=0)
            df["AVG_z"] = (df["AVG_contrib"] - df["AVG_contrib"].mean()) / (std if std != 0 else 1.0)

            z_cols = [f"{c}_z" for c in count_cats] + ["AVG_z"]
            df["SRV"] = df[z_cols].sum(axis=1)

            base_cols = ["Player", "Team", "SRV"] + z_cols
            if "player_id" in df.columns:
                base_cols.insert(1, "player_id")

            df_sorted = df[base_cols].sort_values("SRV", ascending=False).reset_index(drop=True)

            if merge_df is not None:
                out = merge_df.merge(
                    df_sorted[[c for c in ["Player", "Team", "SRV", "player_id"] if c in df_sorted.columns]],
                    on=[c for c in ["Player", "Team"] if c in merge_df.columns],
                    how="left",
                )
                out["SRV"] = out["SRV"].round(2)
                return out.sort_values("SRV", ascending=False)

            return df_sorted

        def calculateSRV_Pitchers(pitchdf: pd.DataFrame, merge_df: pd.DataFrame | None = None):
            df = pitchdf.copy()

            count_cats = ["W", "SV", "SO"]
            for cat in count_cats:
                std = df[cat].std(ddof=0)
                df[f"{cat}_z"] = (df[cat] - df[cat].mean()) / (std if std != 0 else 1.0)

            lg_era = np.divide((df["ERA"] * df["IP"]).sum(), df["IP"].sum()) if df["IP"].sum() else df["ERA"].mean()
            df["ERA_contrib"] = (lg_era - df["ERA"]) * df["IP"]
            std = df["ERA_contrib"].std(ddof=0)
            df["ERA_z"] = (df["ERA_contrib"] - df["ERA_contrib"].mean()) / (std if std != 0 else 1.0)

            lg_whip = np.divide((df["WHIP"] * df["IP"]).sum(), df["IP"].sum()) if df["IP"].sum() else df["WHIP"].mean()
            df["WHIP_contrib"] = (lg_whip - df["WHIP"]) * df["IP"]
            std = df["WHIP_contrib"].std(ddof=0)
            df["WHIP_z"] = (df["WHIP_contrib"] - df["WHIP_contrib"].mean()) / (std if std != 0 else 1.0)

            z_cols = [f"{c}_z" for c in count_cats] + ["ERA_z", "WHIP_z"]
            df["SRV"] = df[z_cols].sum(axis=1)

            base_cols = ["Player", "Team", "SRV"] + z_cols
            if "player_id" in df.columns:
                base_cols.insert(1, "player_id")

            df_sorted = df[base_cols].sort_values("SRV", ascending=False).reset_index(drop=True)

            if merge_df is not None:
                out = merge_df.merge(
                    df_sorted[[c for c in ["Player", "Team", "SRV", "player_id"] if c in df_sorted.columns]],
                    on=[c for c in ["Player", "Team"] if c in merge_df.columns],
                    how="left",
                )
                out["SRV"] = out["SRV"].round(2)
                return out.sort_values("SRV", ascending=False)

            return df_sorted

        # =========================
        # ===== PER-600 HELPER =====
        # =========================
        def to_per_600_pa(df: pd.DataFrame) -> pd.DataFrame:
            """
            Scales hitter counting stats to a 600 PA basis, preserving rate.
            Only touches: PA, R, HR, RBI, SB (and AB if present).
            AVG/OBP/SLG/OPS/K%/BB% remain unchanged (rates).
            """
            out = df.copy()

            if "PA" not in out.columns:
                return out

            pa = pd.to_numeric(out["PA"], errors="coerce").fillna(0.0)
            scale = np.where(pa > 0, 600.0 / pa, 0.0)

            for c in ["R", "HR", "RBI", "SB"]:
                if c in out.columns:
                    out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0) * scale

            if "AB" in out.columns:
                out["AB"] = pd.to_numeric(out["AB"], errors="coerce").fillna(0.0) * scale

            out["PA"] = 600.0
            return out

        # =========================
        # ===== POINTS HELPERS =====
        # =========================
        UNDERDOG_H = {
            "1B": 3.0,
            "2B": 6.0,
            "3B": 8.0,
            "HR": 10.0,
            "BB": 3.0,
            "HBP": 3.0,
            "RBI": 2.0,
            "R": 2.0,
            "SB": 4.0,
        }
        UNDERDOG_P = {
            "W": 5.0,
            "QS": 5.0,
            "SO": 3.0,   # Strikeout
            "IP": 3.0,
            "ER": -3.0,
        }

        DRAFTKINGS_H = {
            "1B": 3.0,
            "2B": 5.0,
            "3B": 8.0,
            "HR": 10.0,
            "RBI": 2.0,
            "R": 2.0,
            "BB": 2.0,
            "HBP": 2.0,
            "SB": 5.0,
        }
        DRAFTKINGS_P = {
            "IP": 2.25,
            "SO": 2.0,
            "W": 4.0,
            "ER": -2.0,
            "H": -0.6,      # Hit Against
            "BB": -0.6,     # Base on Balls Against
            "HBP": -0.6,    # Hits Batsman
            "CG": 2.5,
            "CGSO": 2.5,
            "NH": 5.0,      # No Hitter
        }

        def _num(s):
            return pd.to_numeric(s, errors="coerce").fillna(0.0)

        def _ensure_event_cols_hitters(df: pd.DataFrame) -> pd.DataFrame:
            """
            Make a best effort to create: 1B, 2B, 3B, HR, BB, HBP, R, RBI, SB
            using whatever exists in the projection source.
            """
            out = df.copy()

            # Normalize common column names
            rename_map = {
                "1B": "1B",
                "2B": "2B",
                "3B": "3B",
                "HR": "HR",
                "BB": "BB",
                "HBP": "HBP",
                "R": "R",
                "RBI": "RBI",
                "SB": "SB",
                "H": "H",
                "AB": "AB",
                "PA": "PA",
                "BB%": "BB%",
                "AVG": "AVG",
            }
            # (no-op, but keeps intent clear)
            out = out.rename(columns={k: v for k, v in rename_map.items() if k in out.columns})

            # BB from BB% * PA if BB missing
            if "BB" not in out.columns:
                if "BB%" in out.columns and "PA" in out.columns:
                    out["BB"] = _num(out["BB%"]) * _num(out["PA"])
                else:
                    out["BB"] = 0.0

            # HBP if missing
            if "HBP" not in out.columns:
                out["HBP"] = 0.0

            # If we have H/2B/3B/HR, derive 1B
            if "1B" not in out.columns:
                if all(c in out.columns for c in ["H", "2B", "3B", "HR"]):
                    out["1B"] = _num(out["H"]) - _num(out["2B"]) - _num(out["3B"]) - _num(out["HR"])
                # Else, if we have AVG and AB, approximate H = AVG*AB, but still no 2B/3B -> can't split -> leave 1B at 0
                else:
                    out["1B"] = 0.0

            # Ensure 2B/3B exist
            for c in ["2B", "3B", "HR", "R", "RBI", "SB"]:
                if c not in out.columns:
                    out[c] = 0.0

            # Clean negatives from derived 1B (can happen with mismatched inputs)
            out["1B"] = np.maximum(_num(out["1B"]), 0.0)

            return out

        def _ensure_event_cols_pitchers(df: pd.DataFrame) -> pd.DataFrame:
            """
            Make a best effort to create: IP, SO, W, ER, H, BB, HBP, QS, CG, CGSO, NH
            using whatever exists in the projection source.
            """
            out = df.copy()

            # SO normalization
            if "SO" not in out.columns:
                if "K" in out.columns:
                    out["SO"] = _num(out["K"])
                else:
                    out["SO"] = 0.0

            # Basic counting stats
            for c in ["IP", "W", "ER", "H"]:
                if c not in out.columns:
                    out[c] = 0.0

            # Walks against: sometimes "BB" exists, sometimes only "BB/9" (can't infer without BF), so default 0
            if "BB" not in out.columns:
                out["BB"] = 0.0

            # HBP against
            if "HBP" not in out.columns:
                out["HBP"] = 0.0

            # Bonuses / QS
            for c in ["QS", "CG", "CGSO", "NH"]:
                if c not in out.columns:
                    out[c] = 0.0

            return out

        def calc_points(df: pd.DataFrame, group: str, system: str) -> pd.Series:
            """
            Returns a float Series of fantasy points for each row in df.
            """
            if group == "Hitters":
                d = _ensure_event_cols_hitters(df)
                scoring = UNDERDOG_H if system == "Underdog" else DRAFTKINGS_H
                pts = (
                    _num(d["1B"]) * scoring["1B"]
                    + _num(d["2B"]) * scoring["2B"]
                    + _num(d["3B"]) * scoring["3B"]
                    + _num(d["HR"]) * scoring["HR"]
                    + _num(d["BB"]) * scoring["BB"]
                    + _num(d["HBP"]) * scoring["HBP"]
                    + _num(d["RBI"]) * scoring["RBI"]
                    + _num(d["R"]) * scoring["R"]
                    + _num(d["SB"]) * scoring["SB"]
                )
                return pts

            # Pitchers
            d = _ensure_event_cols_pitchers(df)
            scoring = UNDERDOG_P if system == "Underdog" else DRAFTKINGS_P

            pts = (
                _num(d["IP"]) * scoring["IP"]
                + _num(d["SO"]) * scoring["SO"]
                + _num(d["W"]) * scoring["W"]
                + _num(d["ER"]) * scoring["ER"]
            )

            # Underdog QS
            if system == "Underdog":
                pts = pts + _num(d["QS"]) * scoring["QS"]

            # DraftKings penalties/bonuses
            if system == "DraftKings":
                pts = (
                    pts
                    + _num(d["H"]) * scoring["H"]
                    + _num(d["BB"]) * scoring["BB"]
                    + _num(d["HBP"]) * scoring["HBP"]
                    + _num(d["CG"]) * scoring["CG"]
                    + _num(d["CGSO"]) * scoring["CGSO"]
                    + _num(d["NH"]) * scoring["NH"]
                )

            return pts

        # =========================
        # ===== TITLE =====
        # =========================
        st.markdown(
            """
            <h2 style='text-align:center;margin:.25rem 0 1rem;'>2026 Projections</h2>
            <p style='text-align:center;margin:0 0 1.25rem; font-size:0.85rem; color:#666;'>
                Compare MLB DW, Steamer, ATC, THE BAT, and OOPSY projections.            </p>
            """,
            unsafe_allow_html=True,
        )

        # =========================
        # ===== RAW DATA PREP =====
        # =========================
        ja_hit_local = ja_hit.copy()
        steamerhit_local = steamerhit.copy()
        bathit_local = bathit.copy()
        atchit_local = atchit.copy()
        oopsyhit_local = oopsyhit.copy()

        # --- attach positions robustly to ja_hit_local ---
        ja_hit_local = ja_hit_local.merge(
            pos_data[["Player", "Position(s)"]],
            on="Player",
            how="left",
            suffixes=("", "_pos"),
        )
        ja_pos_cols = [c for c in ja_hit_local.columns if "Position(s)" in c]
        if ja_pos_cols:
            ja_hit_local["Pos"] = ja_hit_local[ja_pos_cols[-1]]
        ja_hit_local = ja_hit_local.drop(columns=ja_pos_cols, errors="ignore")

        # ensure required hitter columns exist
        for c in ["PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%", "Team", "Pos"]:
            if c not in ja_hit_local.columns:
                ja_hit_local[c] = np.nan

        ja_hitters = ja_hit_local[
            ["Player", "Team", "Pos", "PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%","BB","HBP","1B","2B","3B"]
        ].copy()

        # --- Steamer hitters ---
        steamerhit_local = steamerhit_local.rename({"Name": "Player"}, axis=1)
        steamerhit_local = steamerhit_local.merge(
            pos_data[["Player", "Position(s)"]],
            on="Player",
            how="left",
            suffixes=("", "_pos"),
        )
        steamer_pos_cols = [c for c in steamerhit_local.columns if "Position(s)" in c]
        if steamer_pos_cols:
            steamerhit_local["Pos"] = steamerhit_local[steamer_pos_cols[-1]]
        steamerhit_local = steamerhit_local.drop(columns=steamer_pos_cols, errors="ignore")

        for c in ["PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%", "Team", "Pos"]:
            if c not in steamerhit_local.columns:
                steamerhit_local[c] = np.nan

        steamer_hitters = steamerhit_local[
            ["Player", "Team", "Pos", "PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%","BB","HBP","1B","2B","3B"]
        ].copy()

        # --- THE BAT hitters (robust rename if needed) ---
        if "Name" in bathit_local.columns and "Player" not in bathit_local.columns:
            bathit_local = bathit_local.rename({"Name": "Player"}, axis=1)

        bathit_local = bathit_local.merge(
            pos_data[["Player", "Position(s)"]],
            on="Player",
            how="left",
            suffixes=("", "_pos"),
        )
        bat_pos_cols = [c for c in bathit_local.columns if "Position(s)" in c]
        if bat_pos_cols:
            bathit_local["Pos"] = bathit_local[bat_pos_cols[-1]]
        bathit_local = bathit_local.drop(columns=bat_pos_cols, errors="ignore")

        for c in ["PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%", "Team", "Pos"]:
            if c not in bathit_local.columns:
                bathit_local[c] = np.nan

        bat_hitters = bathit_local[
            ["Player", "Team", "Pos", "PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%","BB","HBP","1B","2B","3B"]
        ].copy()

        # --- ATC hitters (robust rename if needed) ---
        if "Name" in atchit_local.columns and "Player" not in atchit_local.columns:
            atchit_local = atchit_local.rename({"Name": "Player"}, axis=1)

        atchit_local = atchit_local.merge(
            pos_data[["Player", "Position(s)"]],
            on="Player",
            how="left",
            suffixes=("", "_pos"),
        )
        atc_pos_cols = [c for c in atchit_local.columns if "Position(s)" in c]
        if atc_pos_cols:
            atchit_local["Pos"] = atchit_local[atc_pos_cols[-1]]
        atchit_local = atchit_local.drop(columns=atc_pos_cols, errors="ignore")

        for c in ["PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%", "Team", "Pos"]:
            if c not in atchit_local.columns:
                atchit_local[c] = np.nan

        atc_hitters = atchit_local[
            ["Player", "Team", "Pos", "PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%","BB","HBP","1B","2B","3B"]
        ].copy()

        # --- OOPSY hitters (robust rename if needed) ---
        if "Name" in oopsyhit_local.columns and "Player" not in oopsyhit_local.columns:
            oopsyhit_local = oopsyhit_local.rename({"Name": "Player"}, axis=1)

        oopsyhit_local = oopsyhit_local.merge(
            pos_data[["Player", "Position(s)"]],
            on="Player",
            how="left",
            suffixes=("", "_pos"),
        )
        oopsy_pos_cols = [c for c in oopsyhit_local.columns if "Position(s)" in c]
        if oopsy_pos_cols:
            oopsyhit_local["Pos"] = oopsyhit_local[oopsyhit_local.columns[oopsyhit_local.columns.str.contains("Position\\(s\\)")] ].iloc[:, -1]
            # safer: overwrite with last pos col if multiple merges happened
            oopsyhit_local["Pos"] = oopsyhit_local[oopsy_pos_cols[-1]]
        oopsyhit_local = oopsyhit_local.drop(columns=oopsy_pos_cols, errors="ignore")

        for c in ["PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%", "Team", "Pos"]:
            if c not in oopsyhit_local.columns:
                oopsyhit_local[c] = np.nan

        oopsy_hitters = oopsyhit_local[
            ["Player", "Team", "Pos", "PA", "R", "HR", "RBI", "SB", "AVG", "OBP", "SLG", "OPS", "K%", "BB%","BB","HBP","1B","2B","3B"]
        ].copy()

        # Add AB if missing (needed in SRV)
        for hdf in (ja_hitters, steamer_hitters, atc_hitters, bat_hitters, oopsy_hitters):
            if "AB" not in hdf.columns:
                hdf["AB"] = (pd.to_numeric(hdf["PA"], errors="coerce").fillna(0) * 0.9).astype(int)

        # --- Pitchers ---
        ja_pitchers = ja_pitch[
            ["Pitcher", "Team", "GS", "IP", "H", "ER", "K", "ERA", "WHIP", "K/9", "BB/9", "K%", "BB%","W","SV"]
        ].copy()
        ja_pitchers = ja_pitchers.rename({"Pitcher": "Player"}, axis=1)

        steamerpit_local = steamerpit.rename({"Name": "Player", "SO": "K"}, axis=1)
        steamer_pitchers = steamerpit_local[
            ["Player", "Team", "GS", "IP", "H", "ER", "K", "ERA", "WHIP", "K/9", "BB/9", "K%", "BB%","W","SV","QS"]
        ].copy()

        batpit_local = batpit.copy()
        if "Name" in batpit_local.columns and "Player" not in batpit_local.columns:
            batpit_local = batpit_local.rename({"Name": "Player"}, axis=1)
        if "SO" in batpit_local.columns and "K" not in batpit_local.columns:
            batpit_local = batpit_local.rename({"SO": "K"}, axis=1)

        bat_pitchers = batpit_local[
            ["Player", "Team", "GS", "IP", "H", "ER", "K", "ERA", "WHIP", "K/9", "BB/9", "K%", "BB%","W","SV","QS"]
        ].copy()

        atcpit_local = atcpit.copy()
        if "Name" in atcpit_local.columns and "Player" not in atcpit_local.columns:
            atcpit_local = atcpit_local.rename({"Name": "Player"}, axis=1)
        if "SO" in atcpit_local.columns and "K" not in atcpit_local.columns:
            atcpit_local = atcpit_local.rename({"SO": "K"}, axis=1)

        atc_pitchers = atcpit_local[
            ["Player", "Team", "GS", "IP", "H", "ER", "K", "ERA", "WHIP", "K/9", "BB/9", "K%", "BB%","W","SV","QS"]
        ].copy()

        oopsypit_local = oopsypitch.copy()
        if "Name" in oopsypit_local.columns and "Player" not in oopsypit_local.columns:
            oopsypit_local = oopsypit_local.rename({"Name": "Player"}, axis=1)
        if "SO" in oopsypit_local.columns and "K" not in oopsypit_local.columns:
            oopsypit_local = oopsypit_local.rename({"SO": "K"}, axis=1)

        # ensure required pitcher columns exist (for consistent "All" view)
        req_p = ["Player", "Team", "GS", "IP", "H", "ER", "K", "ERA", "WHIP", "K/9", "BB/9", "K%", "BB%","W","SV","QS"]
        for c in req_p:
            if c not in oopsypit_local.columns:
                oopsypit_local[c] = 0 if c in ["GS", "IP", "H", "ER", "K"] else np.nan

        oopsy_pitchers = oopsypit_local[
            ["Player", "Team", "GS", "IP", "H", "ER", "K", "ERA", "WHIP", "K/9", "BB/9", "K%", "BB%","W","SV"]
        ].copy()

        # ensure SRV-needed columns exist
        for pdf in (ja_pitchers, steamer_pitchers,atc_pitchers, bat_pitchers, oopsy_pitchers):
            if "W" not in pdf.columns:
                pdf["W"] = 0
            if "SV" not in pdf.columns:
                pdf["SV"] = 0
            if "SO" not in pdf.columns:
                pdf["SO"] = pdf["K"] if "K" in pdf.columns else 0
            if "IP" not in pdf.columns:
                pdf["IP"] = 0

        # =========================
        # ===== CONTROLS =====
        # =========================
        top_col1, top_col2, top_col3, top_col4 = st.columns([1.1, 1.2, 1.2, 0.9])

        with top_col1:
            group = st.radio("Group", ["Hitters", "Pitchers"], horizontal=True)

        with top_col2:
            source_choice = st.radio("Source", ["MLB DW", "Steamer", "ATC",  "THE BAT", "OOPSY", "All"], horizontal=True)

        with top_col4:
            per600 = st.toggle("600 PA Projections", value=False, disabled=(group != "Hitters"))
            show_points = st.checkbox("Show Points", value=False)
            if show_points:
                scoring_system = st.selectbox("Scoring", ["DraftKings", "Underdog"], index=0)
            else:
                scoring_system = None

        # team list
        if group == "Hitters":
            all_teams = (
                pd.concat([ja_hitters["Team"], steamer_hitters["Team"], atc_hitters["Team"],bat_hitters["Team"], oopsy_hitters["Team"]])
                .dropna()
                .unique()
                .tolist()
            )
        else:
            all_teams = (
                pd.concat([ja_pitchers["Team"], steamer_pitchers["Team"], atc_pitchers["Team"], bat_pitchers["Team"], oopsy_pitchers["Team"]])
                .dropna()
                .unique()
                .tolist()
            )
        all_teams = sorted(list(set(all_teams)))
        teams_opts = ["All Teams"] + all_teams

        with top_col3:
            team_filter = st.selectbox("Team", teams_opts, index=0)

        search_x_col1, search_x_col2 = st.columns([1, 1])

        # Build a single player pool across all sources for the chosen group
        if group == "Hitters":
            player_pool = pd.concat(
                [ja_hitters["Player"], steamer_hitters["Player"], atc_hitters["Player"],bat_hitters["Player"], oopsy_hitters["Player"]]
            ).dropna().unique()
        else:
            player_pool = pd.concat(
                [ja_pitchers["Player"], steamer_pitchers["Player"], atc_pitchers["Player"],bat_pitchers["Player"], oopsy_pitchers["Player"]]
            ).dropna().unique()
        player_pool_sorted = sorted(player_pool)

        # If All, do single-player select; otherwise keep multiselect
        with search_x_col1:
            if source_choice == "All":
                selected_player = st.selectbox(
                    "Select a player (All systems)",
                    options=player_pool_sorted,
                    index=0 if len(player_pool_sorted) else None,
                )
                player_search = [selected_player] if selected_player else []
            else:
                player_search = st.multiselect(
                    "Player search",
                    options=player_pool_sorted,
                    placeholder="Start typing player names...",
                )

        with search_x_col2:
            if group == "Hitters" and source_choice != "All":
                pos_search = st.text_input(
                    "Position search",
                    "",
                    placeholder='Type a position like "2B", "SS", "OF"...',
                )
            else:
                pos_search = ""

        st.markdown("<hr style='margin:0.75rem 0 1rem;'/>", unsafe_allow_html=True)

        # =========================
        # ===== FILTER HELPER =====
        # =========================
        def _filter_df(df: pd.DataFrame, is_hitter: bool = False) -> pd.DataFrame:
            out = df.copy()

            if team_filter != "All Teams":
                out = out[out["Team"] == team_filter]

            if player_search:
                out = out[out["Player"].isin(player_search)]

            if is_hitter and pos_search:
                if "Pos" in out.columns:
                    pos_series = out["Pos"].astype(str).fillna("")
                    token = pos_search.strip().upper()
                    out = out[pos_series.str.contains(token, case=False, na=False)]

            return out

        # =========================
        # ===== BUILD DISPLAY =====
        # =========================
        display_df = pd.DataFrame()

        hitter_sources = {
            "MLB DW": ja_hitters,
            "Steamer": steamer_hitters,
            "ATC": atc_hitters,
            "THE BAT": bat_hitters,
            "OOPSY": oopsy_hitters,
        }
        pitcher_sources = {
            "MLB DW": ja_pitchers,
            "Steamer": steamer_pitchers,
            "ATC": atc_pitchers,
            "THE BAT": bat_pitchers,
            "OOPSY": oopsy_pitchers,
        }

        if group == "Hitters":
            hitters_view = {k: (to_per_600_pa(v) if per600 else v) for k, v in hitter_sources.items()}
            # st.write(hitters_view['THE BAT'])

            if source_choice in ["MLB DW", "Steamer", "ATC", "THE BAT", "OOPSY"]:
                full_pool = hitters_view[source_choice]
                filtered = _filter_df(full_pool, is_hitter=True)
                display_df = calculateSRV_Hitters(full_pool, merge_df=filtered)

                if show_points and scoring_system:
                    display_df["Points"] = calc_points(display_df, "Hitters", scoring_system).round(1)

                cols_order = [
                    "Player", "Team", "Pos", "SRV",
                    "Points" if show_points and scoring_system else None,
                    "PA", "R", "HR", "RBI", "SB",
                    "AVG", "OBP", "SLG", "OPS", "K%", "BB%",
                ]
                cols_order = [c for c in cols_order if c is not None]
                display_df = display_df.reindex(columns=cols_order)

            else:  # All (single player, stacked rows)
                rows = []
                for src_name, pool in hitters_view.items():
                    filtered = _filter_df(pool, is_hitter=True)
                    with_srv = calculateSRV_Hitters(pool, merge_df=filtered)

                    if len(with_srv):
                        tmp = with_srv.copy()
                        tmp.insert(0, "Source", src_name)

                        if show_points and scoring_system:
                            tmp["Points"] = calc_points(tmp, "Hitters", scoring_system).round(1)

                        rows.append(tmp)

                cols_order = [
                    "Player", "Team", "Pos", "Source", "SRV",
                    "Points" if show_points and scoring_system else None,
                    "PA", "R", "HR", "RBI", "SB",
                    "AVG", "OBP", "SLG", "OPS", "K%", "BB%",
                ]
                cols_order = [c for c in cols_order if c is not None]

                if rows:
                    display_df = pd.concat(rows, ignore_index=True).reindex(columns=cols_order)
                else:
                    display_df = pd.DataFrame(columns=cols_order)

                if player_search:
                    st.markdown(f"<h3 style='margin:0 0 .5rem;'>{player_search[0]}</h3>", unsafe_allow_html=True)

        else:  # Pitchers
            if source_choice in ["MLB DW", "Steamer", "ATC","THE BAT", "OOPSY"]:
                full_pool = pitcher_sources[source_choice]
                filtered = _filter_df(full_pool, is_hitter=False)
                display_df = calculateSRV_Pitchers(full_pool, merge_df=filtered)

                if show_points and scoring_system:
                    display_df["Points"] = calc_points(display_df, "Pitchers", scoring_system).round(1)

                cols_order = ["Player", "Team", "SRV"]
                if show_points and scoring_system:
                    cols_order += ["Points"]
                cols_order += ["GS","IP","ERA","WHIP","K%","BB%","W","SV"]

                display_df = display_df.reindex(columns=cols_order)

            else:  # All (single player, stacked rows) — fixed to always show all columns
                rows = []
                for src_name, pool in pitcher_sources.items():
                    filtered = _filter_df(pool, is_hitter=False)
                    with_srv = calculateSRV_Pitchers(pool, merge_df=filtered)

                    if len(with_srv):
                        tmp = with_srv.copy()
                        tmp.insert(0, "Source", src_name)

                        if show_points and scoring_system:
                            tmp["Points"] = calc_points(tmp, "Pitchers", scoring_system).round(1)

                        rows.append(tmp)

                cols_order = ["Player","Team","Source","SRV"]
                if show_points and scoring_system:
                    cols_order += ["Points"]
                cols_order += ["GS","IP","ERA","WHIP","K%","BB%","W","SV","SO","K/9","BB/9"]

                if rows:
                    display_df = pd.concat(rows, ignore_index=True).reindex(columns=cols_order)
                else:
                    display_df = pd.DataFrame(columns=cols_order)

                if player_search:
                    st.markdown(f"<h3 style='margin:0 0 .5rem;'>{player_search[0]}</h3>", unsafe_allow_html=True)

        # =========================
        # ===== STYLING =====
        # =========================
        def style_table(df: pd.DataFrame):
            fmt = {}
            for col in df.columns:
                if col in ["PA", "R", "HR", "RBI", "SB", "SO", "W", "SV", "GS", "H", "ER"]:
                    fmt[col] = "{:.0f}"
                elif col == "Points":
                    fmt[col] = "{:.1f}"
                elif any(stat in col for stat in ["AVG", "OBP", "SLG", "OPS"]):
                    fmt[col] = "{:.3f}"
                elif "ERA" in col or "WHIP" in col:
                    fmt[col] = "{:.2f}"
                elif col == "IP" or col.endswith("IP"):
                    fmt[col] = "{:.1f}"
                elif "SRV" in col:
                    fmt[col] = "{:.2f}"
                elif col.endswith("%"):
                    fmt[col] = "{:.1%}"
                elif "/9" in col:
                    fmt[col] = "{:.1f}"

            numeric_cols = df.select_dtypes(include=["float", "int"]).columns.tolist()
            sty = df.style.format(fmt)

            if numeric_cols:
                sty = sty.background_gradient(axis=0, cmap="Blues", subset=numeric_cols)

            if hasattr(sty, "hide_index"):
                sty = sty.hide_index()

            sty = sty.set_properties(**{"text-align": "left", "font-size": "0.8rem"})
            return sty

        height = 250 if len(display_df) < 5 else 650
        st.dataframe(
            style_table(display_df),
            use_container_width=True,
            hide_index=True,
            height=height,
        )

        st.markdown(
            "<center><hr><font face=Oswald><b>The MLB DW system gives every hitter on the 40-man roster a baseline 100 PA so we can use the 600 PA adjustment to see what they <i>would</i> project like in the case they get unexpected playing time</b></font><hr>",
            unsafe_allow_html=True,
        )

        # =========================
        # ===== DOWNLOAD =====
        # =========================
        csv = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download current view as CSV",
            csv,
            "2026_projections.csv",
            "text/csv",
        )



    if tab == "Prospect Comps":
        import numpy as np
        import pandas as pd
        import streamlit as st

        st.markdown(
            "<h2 style='text-align:center;margin:.25rem 0 1rem;'>Prospect Comps</h2>",
            unsafe_allow_html=True,
        )

        # ========= Helpers =========
        def _prep_hitters(minors: pd.DataFrame, majors: pd.DataFrame):
            use_cols = ["Player", "Team", "Pos", "Age", "HitTool", "Discipline", "Power", "Speed", "Durability"]
            minors = minors.copy()
            majors = majors.copy()
            minors = minors[[c for c in use_cols if c in minors.columns]].dropna(subset=["Player"])
            majors = majors[[c for c in use_cols if c in majors.columns]].dropna(subset=["Player"])

            # numeric cols must exist in BOTH
            num_cols = [
                c
                for c in ["Age", "HitTool", "Discipline", "Power", "Speed", "Durability"]
                if c in minors.columns and c in majors.columns
            ]
            for c in num_cols:
                minors[c] = pd.to_numeric(minors[c], errors="coerce")
                majors[c] = pd.to_numeric(majors[c], errors="coerce")

            minors = minors.dropna(subset=num_cols)
            majors = majors.dropna(subset=num_cols)
            return minors, majors, num_cols

        def _prep_pitchers(minors: pd.DataFrame, majors: pd.DataFrame):
            if "Player" not in minors.columns and "player_name" in minors.columns:
                minors = minors.rename(columns={"player_name": "Player"})
            if "Player" not in majors.columns and "player_name" in majors.columns:
                majors = majors.rename(columns={"player_name": "Player"})

            keep = ["Player", "pitcher", "fERA", "fControl", "fStuff", "fDurability", "Age"]
            minors = minors[[c for c in keep if c in minors.columns]].dropna(subset=["Player"])
            majors = majors[[c for c in keep if c in majors.columns]].dropna(subset=["Player"])

            num_cols = [c for c in ["fERA", "fControl", "fStuff", "fDurability", "Age"] if c in minors.columns and c in majors.columns]
            for c in num_cols:
                minors[c] = pd.to_numeric(minors[c], errors="coerce")
                majors[c] = pd.to_numeric(majors[c], errors="coerce")

            # allow Age to be optional
            minors = minors.dropna(subset=[c for c in num_cols if c != "Age"] or num_cols)
            majors = majors.dropna(subset=[c for c in num_cols if c != "Age"] or num_cols)

            core_feats = [c for c in ["fERA", "fControl", "fStuff", "fDurability"] if c in num_cols]
            has_age = "Age" in num_cols
            return minors, majors, core_feats, has_age

        def _standardize(maj_matrix: np.ndarray, vec: np.ndarray, flip_mask=None):
            mu = maj_matrix.mean(axis=0)
            sd = maj_matrix.std(axis=0, ddof=0)
            sd = np.where(sd == 0, 1.0, sd)
            A = (maj_matrix - mu) / sd
            b = (vec - mu) / sd
            if flip_mask is not None:
                A = np.where(flip_mask, -A, A)
                b = np.where(flip_mask, -b, b)
            return A, b

        def _cosine(A: np.ndarray, b: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
            if weights is not None:
                A = A * weights
                b = b * weights
            An = np.linalg.norm(A, axis=1)
            bn = np.linalg.norm(b)
            An = np.where(An == 0, 1.0, An)
            if bn == 0:
                bn = 1.0
            sims = (A @ b) / (An * bn)
            return np.clip(sims, -1.0, 1.0)

        def _sim_to_score(sim: np.ndarray) -> np.ndarray:
            return ((sim + 1.0) / 2.0) * 100.0

        def _build_output_no_dupes(pool, q_row, features, scores, top_n):
            """
            Build one dataframe (same index!) so columns don't get misaligned.
            """
            base_cols = ["Player"] + [c for c in ["Team", "Pos", "Age"] if c in pool.columns]

            # start with base + feature values from MLB player
            all_feat_cols = [c for c in features if c not in base_cols]
            df = pool[base_cols + all_feat_cols].copy()

            # similarity
            df.insert(1, "Similarity", np.round(scores, 1))

            # deltas vs selected minor leaguer
            for c in features:
                df[f"Δ {c}"] = (pool[c].to_numpy() - float(q_row[c])).round(1)

            # sort and trim
            df = df.sort_values("Similarity", ascending=False).head(top_n).reset_index(drop=True)

            # final guard
            df = df.loc[:, ~df.columns.duplicated()]
            return df

        def _run_comps(
            minors_df: pd.DataFrame,
            majors_df: pd.DataFrame,
            features: list[str],
            query_name: str,
            top_n: int = 10,
            same_pos_only: bool = False,
            pos_col: str | None = None,
            weights_dict: dict | None = None,
            flip_lower_is_better: list[str] | None = None,
        ) -> tuple[pd.DataFrame, pd.Series]:
            q = minors_df[minors_df["Player"] == query_name]
            if q.empty:
                return pd.DataFrame(), pd.Series(dtype=float)
            q = q.iloc[0]

            pool = majors_df.copy()
            if same_pos_only and pos_col and pos_col in minors_df.columns and pos_col in majors_df.columns:
                pool = pool[pool[pos_col] == q[pos_col]].copy()
                if pool.empty:
                    pool = majors_df.copy()

            A = pool[features].to_numpy(dtype=float)
            b = q[features].to_numpy(dtype=float)

            weights = None
            if weights_dict:
                weights = np.array([weights_dict.get(f, 1.0) for f in features], dtype=float)

            flip_mask = np.array([f in (flip_lower_is_better or []) for f in features], dtype=bool)

            A_z, b_z = _standardize(A, b, flip_mask=flip_mask)
            sims = _cosine(A_z, b_z, weights=weights)
            scores = _sim_to_score(sims)

            out = _build_output_no_dupes(pool, q, features, scores, top_n)
            return out, q  # also return the selected player row so we can show it

        # ========= UI =========
        group = st.radio("Group", ["Hitters", "Pitchers"], horizontal=True, index=0)

        if group == "Hitters":
            # these must already be in your session
            minors_hit = fscores_milb_hit.copy()
            majors_hit = fscores_mlb_hit.copy()
            minors_hit, majors_hit, hit_features = _prep_hitters(minors_hit, majors_hit)

            left, right = st.columns([2, 1])
            with left:
                sel_player = st.selectbox(
                    "Select a Minor League Hitter",
                    options=sorted(minors_hit["Player"].unique().tolist()),
                    index=0,
                )
            with right:
                top_n = st.slider("How many comps?", 3, 10, 5, 1)

            with st.expander("Advanced options"):
                same_pos = st.checkbox("Limit comps to the same primary position", value=True)
                st.caption("Similarity = cosine over MLB-standardized features (0–100 score).")
                w_cols = st.columns(6)
                w_hittool   = w_cols[0].number_input("HitTool",   min_value=0.0, value=1.0, step=0.1)
                w_disc      = w_cols[1].number_input("Discipline", min_value=0.0, value=1.0, step=0.1)
                w_power     = w_cols[2].number_input("Power",      min_value=0.0, value=1.0, step=0.1)
                w_speed     = w_cols[3].number_input("Speed",      min_value=0.0, value=1.0, step=0.1)
                w_dur       = w_cols[4].number_input("Durability", min_value=0.0, value=1.0, step=0.1)
                w_age       = w_cols[5].number_input("Age",        min_value=0.0, value=0.5, step=0.1)

                weights_hit = {
                    "HitTool": w_hittool,
                    "Discipline": w_disc,
                    "Power": w_power,
                    "Speed": w_speed,
                    "Durability": w_dur,
                    "Age": w_age,
                }

            with st.spinner("Computing hitter comps..."):
                comps, sel_row = _run_comps(
                    minors_df=minors_hit,
                    majors_df=majors_hit,
                    features=hit_features,
                    query_name=sel_player,
                    top_n=top_n,
                    same_pos_only=same_pos,
                    pos_col="Pos",
                    weights_dict=weights_hit,
                    flip_lower_is_better=None,
                )

            # ---- show selected minor leaguer's scores ----
            sel1,sel2,sel3 = st.columns([1,5,1])
            with sel2:
                if not sel_row.empty:
                    st.markdown("#### Selected player's scores")
                    sel_display = {
                        "Player": sel_player,
                        "Team": sel_row.get("Team", ""),
                        "Pos": sel_row.get("Pos", ""),
                    }
                    for c in hit_features:
                        sel_display[c] = sel_row.get(c, "")
                    st.dataframe(
                        pd.DataFrame([sel_display]),
                        use_container_width=True,
                        hide_index=True,
                    )

            # ---- show comps ----
            st.markdown(f"### Top {top_n} MLB Comps for **{sel_player}**")
            if comps.empty:
                st.info("No comps found. Try turning off same-position filter or adjusting weights.")
            else:
                st.dataframe(
                    comps.style.format(precision=1, thousands=","),
                    use_container_width=True,
                    hide_index=True
                    #height=len(comps)*50,
                )
                st.download_button(
                    "⬇️ Download comps as CSV",
                    data=comps.to_csv(index=False).encode("utf-8"),
                    file_name=f"{sel_player.replace(' ','_')}_MLB_Comps.csv",
                    mime="text/csv",
                )

        else:  # Pitchers
            minors_pitch = fscores_milb_pitch.copy()
            majors_pitch = fscores_mlb_pitch.copy()
            minors_pitch, majors_pitch, pit_core_feats, has_age = _prep_pitchers(minors_pitch, majors_pitch)
            pit_features = pit_core_feats + (["Age"] if has_age else [])

            left, right = st.columns([2, 1])
            with left:
                sel_player = st.selectbox(
                    "Select a Minor League Pitcher",
                    options=sorted(minors_pitch["Player"].unique().tolist()),
                    index=0,
                )
            with right:
                top_n = st.slider("How many comps?", 3, 10, 5, 1)
                #top_n = st.slider("How many comps?", 5, 25, 10, 1)

            with st.expander("Advanced options"):
                st.caption("fERA is treated as ‘lower is better’.")
                w_cols = st.columns(5 if has_age else 4)
                w_fera   = w_cols[0].number_input("fERA",        min_value=0.0, value=1.2, step=0.1)
                w_fctl   = w_cols[1].number_input("fControl",    min_value=0.0, value=1.0, step=0.1)
                w_fstuff = w_cols[2].number_input("fStuff",      min_value=0.0, value=1.0, step=0.1)
                w_fdur   = w_cols[3].number_input("fDurability", min_value=0.0, value=0.7, step=0.1)
                weights_pit = {"fERA": w_fera, "fControl": w_fctl, "fStuff": w_fstuff, "fDurability": w_fdur}
                if has_age:
                    w_age = w_cols[4].number_input("Age", min_value=0.0, value=0.4, step=0.1)
                    weights_pit["Age"] = w_age

            with st.spinner("Computing pitcher comps..."):
                comps, sel_row = _run_comps(
                    minors_df=minors_pitch,
                    majors_df=majors_pitch,
                    features=pit_features,
                    query_name=sel_player,
                    top_n=top_n,
                    same_pos_only=False,
                    pos_col=None,
                    weights_dict=weights_pit,
                    flip_lower_is_better=["fERA"],
                )

            zzz1,zzz2,zzz3 = st.columns([1,5,1])
            with zzz2:
                if not sel_row.empty:
                    st.markdown("#### Selected pitcher's scores")
                    sel_display = {
                        "Player": sel_player,
                    }
                    for c in pit_features:
                        sel_display[c] = sel_row.get(c, "")
                    st.dataframe(
                        pd.DataFrame([sel_display]),
                        use_container_width=True,
                        hide_index=True,
                    )

            st.markdown(f"### Top {top_n} MLB Comps for **{sel_player}**")
            if comps.empty:
                st.info("No comps found. Try adjusting weights.")
            else:
                st.dataframe(
                    comps.style.format(precision=2, thousands=","),
                    use_container_width=True,
                    hide_index=True
                    #height=460,
                )
                st.download_button(
                    "⬇️ Download comps as CSV",
                    data=comps.to_csv(index=False).encode("utf-8"),
                    file_name=f"{sel_player.replace(' ','_')}_MLB_Comps.csv",
                    mime="text/csv",
                )

    
    if tab == "2026 Ranks":
        import pandas as pd, numpy as np, html
        import streamlit as st
        import streamlit.components.v1 as components

        # ===== Title =====
        st.markdown('<h2 style="text-align:center;margin:.25rem 0 1rem;">2026 Ranks</h2>', unsafe_allow_html=True)

        # ===== Load data =====
        # If you want to swap to live Sheets later, hook back into your helper functions.
        hitters_raw = hitterranks.copy()
        pitchers_raw = pitcherranks.copy()

        #st.write(hitters_raw)

        teams_completed = hitters_raw['Team'].unique()

        #st.markdown(f'<h5 style="text-align:center;margin:.25rem 0 1rem;">work in progress...</h5><center>Teams Completed: {teams_completed}</center>', unsafe_allow_html=True)


        # Build link dicts from the Link column
        h_with_links = hitters_raw[~hitters_raw['Link'].isna()]
        h_link_dict = dict(zip(h_with_links['Player'], h_with_links['Link']))

        p_with_links = pitchers_raw[~pitchers_raw['Link'].isna()]
        p_link_dict = dict(zip(p_with_links['Player'], p_with_links['Link']))

        # ===== Toggle =====
        group = st.radio("Group", ["Hitters", "Pitchers"], horizontal=True, index=0)
        df_raw = hitters_raw.copy() if group == "Hitters" else pitchers_raw.copy()

        # Expected cols
        expected = ["Rank","Player","Team","Pos","Primary Pos","Pos Rank","Comments","Link"]
        for c in expected:
            if c not in df_raw.columns:
                df_raw[c] = np.nan

        # Coerce numeric ints for display
        for c in ["Rank","Pos Rank"]:
            df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce").astype("Int64")

        # ===== Filters =====
        pos_field = "Primary Pos" if group == "Hitters" else "Pos"

        c1, c2, c3 = st.columns([1,1,1.6])
        with c1:
            pos_opts = ["All"] + sorted(df_raw[pos_field].dropna().astype(str).unique().tolist())
            sel_pos = st.selectbox(pos_field, pos_opts, index=0)
        with c2:
            team_opts = ["All"] + sorted(df_raw["Team"].dropna().astype(str).unique().tolist())
            sel_team = st.selectbox("Team", team_opts, index=0)
        with c3:
            q = st.text_input("Search Player", placeholder="type a name…").strip().lower()

        df = df_raw.copy()
        if sel_pos != "All":
            df = df[df[pos_field] == sel_pos]
        if sel_team != "All":
            df = df[df["Team"] == sel_team]
        if q:
            df = df[df["Player"].fillna("").str.lower().str.contains(q, na=False)]
        df = df.sort_values(["Rank","Player"], na_position="last").reset_index(drop=True)

        # ===== Row colors =====
        pos_colors = (
            {"C":"#E691FF","1B":"#FFE5B4","2B":"#FF7F47","3B":"#D9EBFA","SS":"#47C5FF","OF":"#5CEDB5","DH":"#91C6FF"}
            if group == "Hitters" else
            {"SP":"#004687","RP":"#004687","P":"#004687"}
        )

        # Which link dict to use
        link_dict = h_link_dict if group == "Hitters" else p_link_dict

        # ===== Utilities =====
        def esc(x):
            if pd.isna(x):
                return ""
            try:
                return html.escape(str(x))
            except Exception:
                return ""

        # ===== CSS =====
        css = """
        <style>
        .wrap { max-width: 1200px; margin: 0 auto; }
        .card { background:#fff; border:1px solid #e9e9ee; border-radius:16px; box-shadow:0 4px 14px rgba(0,0,0,.05); overflow:hidden; }
        table.tbl { width:100%; border-collapse:separate; border-spacing:0; font-size:15px; }
        thead th { position:sticky; top:0; background:#f7f8fb; padding:10px; text-align:center; font-weight:700; border-bottom:1px solid #ececf4; z-index:1; }
        tbody td { padding:10px; text-align:center; border-bottom:1px solid #f2f2f6; }
        tbody tr:last-child td { border-bottom:none; }
        td.player { text-align:left; }
        .pwrap { position:relative; display:inline-block; }
        .pname { font-weight:700; color:#0f172a; cursor:help; }
        .tip {
            visibility:hidden; opacity:0; transition:opacity .12s ease-in-out;
            position:absolute; left:0; top:110%;
            min-width:260px; max-width:540px;
            background:#0f172a; color:#fff; border-radius:10px; padding:10px 12px;
            box-shadow:0 8px 22px rgba(0,0,0,.18); z-index:5; line-height:1.35;
            white-space:normal; word-wrap:break-word;
        }
        .tip::after { content:""; position:absolute; top:-6px; left:14px; border-width:6px; border-style:solid;
                        border-color:transparent transparent #0f172a transparent; }
        .pwrap:hover .tip { visibility:visible; opacity:1; }
        @media (max-width: 800px) { .tip { max-width: 80vw; } }

        /* Read button */
        .readcol { text-align:center; }
        .readbtn {
            display:inline-block; padding:4px 8px; border-radius:80px;
            text-decoration:none; font-weight:600; border:1px solid #dbe0ea;
            background:#f2f5fb; color:#0f172a;
        }
        .readbtn:hover { background:#e6ecf7; }
        .muted { color:#9aa3b2; font-style:italic; }
        </style>
        """

        # ----- Header (conditional) -----
        if group == "Hitters":
            header = """
            <div class="wrap"><div class="card">
            <table class="tbl">
                <thead>
                <tr>
                    <th style="width:70px;">Rank</th>
                    <th>Player</th>
                    <th style="width:90px;">Team</th>
                    <th style="width:90px;">Pos</th>
                    <th style="width:120px;">Primary Pos</th>
                    <th style="width:110px;">Pos Rank</th>
                    <th style="width:160px;">Link</th>
                    <th style="width:45%;">Comments</th>
                </tr>
                </thead>
                <tbody>
            """
        else:  # Pitchers
            header = """
            <div class="wrap"><div class="card">
            <table class="tbl">
                <thead>
                <tr>
                    <th style="width:70px;">Rank</th>
                    <th>Player</th>
                    <th style="width:90px;">Team</th>
                    <th style="width:120px;">Pos</th>
                    <th style="width:160px;">Read</th>
                    <th style="width:55%;">Comments</th>
                </tr>
                </thead>
                <tbody>
            """

        # ----- Rows -----
        rows = []
        for _, r in df.iterrows():
            # background color by position key (Primary Pos for hitters, Pos for pitchers)
            pos_key = esc(r.get(pos_field, ""))
            bg = pos_colors.get(pos_key, "#47C5FF")

            rank    = "" if pd.isna(r["Rank"]) else int(r["Rank"])
            player  = esc(r["Player"])
            team    = esc(r["Team"])
            pos     = esc(r["Pos"])
            ppos    = esc(r.get("Primary Pos", ""))
            posrank = "" if pd.isna(r.get("Pos Rank", np.nan)) else int(r["Pos Rank"])

            cm_full = esc(r["Comments"]).replace("\n"," ")
            cm_prev = (cm_full[:180] + "…") if len(cm_full) > 180 else cm_full

            # Link cell
            raw_player = r["Player"]
            plink = None
            # Prefer dict lookup; if missing, fall back to row's Link column
            if isinstance(raw_player, str):
                plink = link_dict.get(raw_player)
            if (not isinstance(plink, str) or not plink.strip()) and isinstance(r.get("Link", None), str):
                if r["Link"].strip():
                    plink = r["Link"].strip()

            if isinstance(plink, str) and plink.strip():
                link_cell = f'<a class="readbtn" href="{html.escape(plink)}" target="_blank" rel="noopener noreferrer">Read Full Breakdown</a>'
            else:
                link_cell = '<span class="muted">—</span>'

            if group == "Hitters":
                rows.append(f"""
                <tr style="background:{bg};">
                    <td>{rank}</td>
                    <td class="player">
                        <span class="pwrap">
                            <span class="pname">{player}</span>
                            <span class="tip">{cm_full or "No comment."}</span>
                        </span>
                    </td>
                    <td>{team}</td>
                    <td>{pos}</td>
                    <td>{ppos}</td>
                    <td>{posrank}</td>
                    <td class="readcol">{link_cell}</td>
                    <td style="text-align:left;">{cm_prev}</td>
                </tr>
                """)
            else:
                rows.append(f"""
                <tr style="background:{bg};">
                    <td>{rank}</td>
                    <td class="player">
                        <span class="pwrap">
                            <span class="pname">{player}</span>
                            <span class="tip">{cm_full or "No comment."}</span>
                        </span>
                    </td>
                    <td>{team}</td>
                    <td>{pos}</td>
                    <td class="readcol">{link_cell}</td>
                    <td style="text-align:left;">{cm_prev}</td>
                </tr>
                """)

        footer = """
                </tbody>
            </table>
            </div></div>
        """

        html_out = css + header + "\n".join(rows) + footer

        # Sensible container height
        row_h = 44     # px per row (roughly)
        base_h = 120   # header + padding
        max_h = 900
        height = min(max_h, base_h + row_h * max(1, len(df)))

        components.html(html_out, height=height, scrolling=True)

    
    if tab == "Hitter Profiles":
        render_hitter_profiles(hprofiles24, hprofiles25, hprofiles2425)


    ######### HITTER COMP



    # --- HITTER COMPS PAGE ---------------------------------------------------------
    # Usage:
    #   if tab == "Hitter Comps":
    #       render_hitter_comps_page(csv_path="/mnt/data/hitter_profiles_data_2024_2025.csv")
    #
    # Data assumptions:
    # - "BatterName" column exists
    # - Stats include (any capitalization/spaces/percent signs tolerated):
    #     brl%, gb%, air pull%, swing%, contact%, k%, bb%, sbatt%
    # - Optional columns: "PA", "Season" or "Sample" to filter by season buckets

    # -------------------- Helpers --------------------

    # Normalize column name keys (case/space/% tolerant)
    def _norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", (s or "").lower())

    # Map flexible user-provided names to your canonical stat keys
    CANON_KEYS = {
        "brl%": ["brl%", "barrel%", "brl", "barrels%"],
        "gb%": ["gb%", "groundball%", "gbpct"],
        "airpull%": ["airpull%", "air pull%", "pullair%", "pullfb%", "airpullpct"],
        "swing%": ["swing%", "swingpct", "sw%"],
        "contact%": ["contact%", "contactpct", "ct%"],
        "k%": ["k%", "so%", "strikeout%"],
        "bb%": ["bb%", "walk%", "baseonballs%"],
        "sbatt%": ["sbatt%", "sb attempt%", "steal attempt%", "sbattpct", "sbatt"],
    }

    def _locate_columns(df: pd.DataFrame):
        found = {}
        all_cols = { _norm(c): c for c in df.columns }
        for canon, variants in CANON_KEYS.items():
            for v in variants:
                key = _norm(v)
                if key in all_cols:
                    found[canon] = all_cols[key]
                    break
            # If we didn't find via variants, try exact canon
            if canon not in found and _norm(canon) in all_cols:
                found[canon] = all_cols[_norm(canon)]
        return found

    def _percentify(series: pd.Series) -> pd.Series:
        """Convert 0–1 decimals to 0–100 if needed; leave 0–100 ints/floats alone."""
        s = series.astype(float)
        if s.dropna().between(0, 1.0).all():
            return s * 100.0
        return s

    def _zscore(df: pd.DataFrame) -> pd.DataFrame:
        mu = df.mean(numeric_only=True)
        sd = df.std(ddof=0, numeric_only=True).replace(0, np.nan)
        z = (df - mu) / sd
        return z.fillna(0.0)

    def _cosine_dist(a: np.ndarray, B: np.ndarray) -> np.ndarray:
        a = a.astype(float)
        B = B.astype(float)
        a_norm = np.linalg.norm(a)
        B_norm = np.linalg.norm(B, axis=1)
        # Avoid divide by zero
        a_norm = 1e-12 if a_norm == 0 else a_norm
        B_norm = np.where(B_norm == 0, 1e-12, B_norm)
        sim = (B @ a) / (B_norm * a_norm)
        return 1.0 - sim  # distance = 1 - cosine similarity

    def _euclid_dist(a: np.ndarray, B: np.ndarray) -> np.ndarray:
        return np.linalg.norm(B - a[None, :], axis=1)

    def _mahalanobis_dist(a: np.ndarray, B: np.ndarray, VI: np.ndarray) -> np.ndarray:
        diff = B - a[None, :]
        # sqrt((x-μ)^T V^{-1} (x-μ))
        return np.sqrt(np.einsum("ij,jk,ik->i", diff, VI, diff))

    def _mahalanobis_inv(cov: np.ndarray) -> np.ndarray | None:
        try:
            return np.linalg.inv(cov)
        except Exception:
            return None

    # -------------------- Main Renderer --------------------

    def render_hitter_comps_page(data: pd.DataFrame | None = None,
                                csv_path: str | None = None):
        st.markdown("""
            <div style="text-align:center">
                <div style="font-size:36px; font-weight:800;">Hitter Similarity Comps</div>
                <div style="opacity:.8; margin-top:.25rem;">Find 3–5 closest player profiles from your dataset</div>
            </div>
            <hr style="margin:1rem 0 .5rem 0; opacity:.2;">
        """, unsafe_allow_html=True)

        # ---- Load data ----
        data = hprofiles2425.copy()

        # Basic sanity: need names
        if "BatterName" not in data.columns:
            # Try a tolerant fallback name
            name_col = None
            for c in data.columns:
                if _norm(c) in {"battername", "player", "name", "hitter"}:
                    name_col = c
                    break
            if not name_col:
                st.error("No 'BatterName' column found.")
                return
            data = data.rename(columns={name_col: "BatterName"})

        # Locate stat columns flexibly
        stat_map = _locate_columns(data)
        present = {k: v for k, v in stat_map.items() if v in data.columns}
        missing = [k for k in CANON_KEYS.keys() if k not in present]

        if len(present) < 3:
            st.error(f"Not enough stat columns found for comps. Missing: {', '.join(missing)}")
            return

        # Optional filters cluster
        c1, c2, c3 = st.columns([2,1.2,1.2])
        with c1:
            hitter_options = sorted(data["BatterName"].dropna().unique().tolist())
            hitter = st.selectbox("Choose a hitter", hitter_options, index=0)

        # Season/Sample filter if available
        with c2:
            season_col = None
            for candidate in ["Season", "Year", "Sample"]:
                if candidate in data.columns:
                    season_col = candidate
                    break
            season_val = None
            if season_col:
                opts = ["All"] + [str(x) for x in sorted(data[season_col].dropna().unique().tolist())]
                season_val = st.selectbox("Sample filter", opts, index=0)
            else:
                st.caption("No season/sample column detected.")

        with c3:
            min_pa = 0
            if "PA" in data.columns:
                max_pa = int(np.nanmax(data["PA"].values))
                min_pa = st.slider("Min PA", 0, max_pa if max_pa>0 else 0, value=min(50, max_pa), step=10)

        # Filter by season & PA (if present)
        df = data.copy()
        if season_col and season_val and season_val != "All":
            df = df[df[season_col].astype(str) == season_val]
        if "PA" in df.columns:
            df = df[df["PA"].fillna(0) >= min_pa]

        # If multiple rows per hitter (team splits, etc.), aggregate to one row (mean)
        agg_cols = list({v for v in present.values()}) + (["PA"] if "PA" in df.columns else [])
        df_agg = df.groupby("BatterName", as_index=False)[agg_cols].mean(numeric_only=True)

        # Rebuild present mapping against df_agg
        present_agg = {k: v for k, v in present.items() if v in df_agg.columns}

        # Build matrix
        stat_cols = [present_agg[k] for k in ["brl%","gb%","airpull%","swing%","contact%","k%","bb%","sbatt%"] if k in present_agg]
        if hitter not in df_agg["BatterName"].values:
            st.warning("Selected hitter not found after filters.")
            return

        # Percentify columns (0–1 => 0–100), then z-score
        M = df_agg[stat_cols].copy()
        for c in stat_cols:
            M[c] = _percentify(M[c])

        # Optional per-stat weights
        with st.expander("Weights (optional)", expanded=False):
            weights = {}
            for k in ["brl%","gb%","airpull%","swing%","contact%","k%","bb%","sbatt%"]:
                if k in present_agg:
                    w = st.slider(f"Weight: {k}", 0.0, 3.0, 1.0, 0.1)
                    weights[present_agg[k]] = w
            # apply weights by scaling columns
            for c in stat_cols:
                M[c] = M[c] * float(weights.get(c, 1.0))

        Z = _zscore(M)

        # Target vector
        target_row = df_agg[df_agg["BatterName"] == hitter].iloc[0]
        a = Z.loc[df_agg["BatterName"] == hitter, stat_cols].values[0]
        B = Z[stat_cols].values

        # Distance metric selection
        rowA, rowB = st.columns([1.2, 1])
        with rowA:
            metric = st.selectbox("Similarity metric", ["Cosine (direction)", "Euclidean (z-dist)", "Mahalanobis (cov-aware)"])
        with rowB:
            k = st.slider("Number of comps", 3, 5, 5, 1)

        # Compute distances
        if metric.startswith("Cosine"):
            dists = _cosine_dist(a, B)
        elif metric.startswith("Euclidean"):
            dists = _euclid_dist(a, B)
        else:
            cov = np.cov(Z[stat_cols].values, rowvar=False)
            VI = _mahilanobis_inv(cov) if ( _mahilanobis_inv := _mahilanobis_inv ) else None  # python 3.10 fallback trick
            VI = _mahilanobis_inv(cov)
            if VI is None:
                st.warning("Mahalanobis covariance not invertible; falling back to Euclidean.")
                dists = _euclid_dist(a, B)
                metric = "Euclidean (fallback)"
            else:
                dists = _mahalanobis_dist(a, B, VI)

        # Rank & take top k (exclude the player themself)
        result = df_agg[["BatterName"]].copy()
        result["Distance"] = dists
        result = result[result["BatterName"] != hitter].sort_values("Distance", ascending=True).head(k)

        # Build output table with raw stats (post-filter, unweighted raw percents) + distances
        # Reconstruct a nice table
        show_cols = ["BatterName", "Distance"] + stat_cols
        # Pull the unweighted, percentified stats for readability:
        pretty = df_agg[["BatterName"] + stat_cols].copy()
        for c in stat_cols:
            pretty[c] = _percentify(pretty[c])  # ensure in 0–100 scale

        out = result.merge(pretty, on="BatterName", how="left")

        # Format for display
        col_cfg = {
            "BatterName": st.column_config.TextColumn(help="Similar hitter"),
            "Distance": st.column_config.NumberColumn(format="%.3f"),
        }
        for c in stat_cols:
            col_cfg[c] = st.column_config.NumberColumn(format="%.1f", help=f"{c} (%, comparable scale)")

        st.markdown("### Most similar hitters")
        st.dataframe(out[show_cols], use_container_width=True, hide_index=True, column_config=col_cfg)

        # ---------- Viz: Parallel coordinates (z-scores) for target + comps ----------
        st.markdown("#### Profile comparison (z-scores)")
        players_for_viz = [hitter] + out["BatterName"].tolist()
        Z_v = Z.copy()
        Z_v["BatterName"] = df_agg["BatterName"]

        long = Z_v[["BatterName"] + stat_cols].melt(id_vars="BatterName", var_name="Stat", value_name="Z")
        long = long[long["BatterName"].isin(players_for_viz)]

        # Order stats in original desired order
        stat_order = stat_cols  # keep current column order
        chart = (
            alt.Chart(long)
            .mark_line(point=True)
            .encode(
                x=alt.X("Stat:N", sort=stat_order, title=""),
                y=alt.Y("Z:Q", title="z-score (within pool)", scale=alt.Scale(zero=False)),
                color=alt.Color("BatterName:N", legend=alt.Legend(title="Player")),
                tooltip=["BatterName:N", "Stat:N", alt.Tooltip("Z:Q", format=".2f")]
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)

        # ---------- Target snapshot ----------
        st.markdown("#### Selected hitter snapshot")
        target_pretty = pretty[pretty["BatterName"] == hitter].copy()
        st.dataframe(target_pretty.set_index("BatterName"), use_container_width=True)

        # ---------- Debug / footer ----------
        with st.expander("Columns detected", expanded=False):
            st.write("Mapped stat columns (canonical → actual):")
            st.json(present_agg)
            if missing:
                st.caption(f"Missing canon keys not found: {', '.join(missing)}")


    # Optional: alias for your app
    def render_hitter_comps(data=None, csv_path=None):
        render_hitter_comps_page(data=data, csv_path=csv_path)

    if tab == "Hitter Comps":
        render_hitter_comps_page()









    ########################


    if tab == "Hitter Profiles Base":
        st.markdown("<h1><center>Hitter Profiles</center></h1>", unsafe_allow_html=True)

        hitter_selection_list = list(hprofiles2425['BatterName'].unique())
        hp_col1, hp_col2,hp_col3 = st.columns([1,1,3])
        with hp_col1:
            hitter_selection = st.selectbox('Choose a Hitter', hitter_selection_list)
        with hp_col2:
            year_selection = st.selectbox('Choose Sample', ['2025','2024','2024-2025'])
        
        if year_selection == '2025':
            data_to_use = hprofiles25.copy()
        elif year_selection == '2024':
            data_to_use = hprofiles24.copy()
        elif year_selection == '2024-2025':
            data_to_use = hprofiles2425.copy()
        
        data_to_use = data_to_use[data_to_use['BatterName']==hitter_selection]

        # Base stats
        base_stats = data_to_use[['BatterName','PA','AB','R','HR','RBI','SB','AVG','OBP','SLG']]
        st.dataframe(base_stats)

        # Batted Ball Profile
        bb_profile = data_to_use[['BatterName','xwOBA','xwOBACON','Brl%','AirPull%','GB%','LD%','FB%','SweetSpot%']]
        st.dataframe(bb_profile)

        # Plate Discipline
        disc_profile = data_to_use[['BatterName','K%','BB%','Z-Contact%','Z-Swing%']]
        st.dataframe(disc_profile)

        # fScores
        fprofiles = data_to_use[['BatterName','fHitTool','fPower','fDiscipline','fSpeed','fDurability']]
        st.dataframe(fprofiles)


    if tab == "Player Rater":
        import numpy as np
        import pandas as pd
        import streamlit as st

        st.markdown("<h1><center>Dynamic Player Rater</center></h1><br><br><i>SRV = Standard Roto Value</i>", unsafe_allow_html=True)

        # ==== build team dicts (latest affiliate per player) ====
        team_selection_list = list(hitdb["affiliate"].unique())
        teamlist = hitdb[["player_id", "game_date", "affiliate"]].sort_values(by="game_date")
        teamlist = teamlist[["player_id", "affiliate"]].drop_duplicates(keep="last")
        teamdict = dict(zip(teamlist.player_id, teamlist.affiliate))

        teamlist_p = pitdb[["player_id", "game_date", "affiliate"]].sort_values(by="game_date")
        teamlist_p = teamlist_p[["player_id", "affiliate"]].drop_duplicates(keep="last")
        teamdict_p = dict(zip(teamlist_p.player_id, teamlist_p.affiliate))

        # ========= FUNCTIONS =========
        def calculateSRV_Hitters(hitdf: pd.DataFrame, merge_df: pd.DataFrame | None = None):
            """
            Same logic as your old SGP, but final col is now SRV.
            Also preserves player_id when present so we can look players up later.
            """
            df = hitdf.copy()

            count_cats = ["R", "HR", "RBI", "SB"]
            for cat in count_cats:
                std = df[cat].std(ddof=0)
                df[f"{cat}_z"] = (df[cat] - df[cat].mean()) / (std if std != 0 else 1.0)

            total_ab = df["AB"].sum()
            lg_avg = np.divide((df["AVG"] * df["AB"]).sum(), total_ab) if total_ab else df["AVG"].mean()

            df["AVG_contrib"] = (df["AVG"] - lg_avg) * df["AB"]
            std = df["AVG_contrib"].std(ddof=0)
            df["AVG_z"] = (df["AVG_contrib"] - df["AVG_contrib"].mean()) / (std if std != 0 else 1.0)

            z_cols = [f"{c}_z" for c in count_cats] + ["AVG_z"]
            df["SRV"] = df[z_cols].sum(axis=1)

            # keep player_id if we have it
            base_cols = ["Player", "Team", "SRV"] + z_cols
            if "player_id" in df.columns:
                base_cols.insert(1, "player_id")

            df_sorted = df[base_cols].sort_values("SRV", ascending=False).reset_index(drop=True)

            if merge_df is not None:
                out = merge_df.merge(df_sorted[[c for c in ["Player", "Team", "SRV", "player_id"] if c in df_sorted.columns]],
                                    on=[c for c in ["Player", "Team"] if c in merge_df.columns],
                                    how="left")
                out["SRV"] = out["SRV"].round(2)
                return out.sort_values("SRV", ascending=False)

            return df_sorted

        def calculateSRV_Pitchers(pitchdf: pd.DataFrame, merge_df: pd.DataFrame | None = None):
            df = pitchdf.copy()

            count_cats = ["W", "SV", "SO"]
            for cat in count_cats:
                std = df[cat].std(ddof=0)
                df[f"{cat}_z"] = (df[cat] - df[cat].mean()) / (std if std != 0 else 1.0)

            # rate cats as contrib * IP
            lg_era = np.divide((df["ERA"] * df["IP"]).sum(), df["IP"].sum()) if df["IP"].sum() else df["ERA"].mean()
            df["ERA_contrib"] = (lg_era - df["ERA"]) * df["IP"]
            std = df["ERA_contrib"].std(ddof=0)
            df["ERA_z"] = (df["ERA_contrib"] - df["ERA_contrib"].mean()) / (std if std != 0 else 1.0)

            lg_whip = np.divide((df["WHIP"] * df["IP"]).sum(), df["IP"].sum()) if df["IP"].sum() else df["WHIP"].mean()
            df["WHIP_contrib"] = (lg_whip - df["WHIP"]) * df["IP"]
            std = df["WHIP_contrib"].std(ddof=0)
            df["WHIP_z"] = (df["WHIP_contrib"] - df["WHIP_contrib"].mean()) / (std if std != 0 else 1.0)

            z_cols = [f"{c}_z" for c in count_cats] + ["ERA_z", "WHIP_z"]
            df["SRV"] = df[z_cols].sum(axis=1)

            base_cols = ["Player", "Team", "SRV"] + z_cols
            if "player_id" in df.columns:
                base_cols.insert(1, "player_id")

            df_sorted = df[base_cols].sort_values("SRV", ascending=False).reset_index(drop=True)

            if merge_df is not None:
                out = merge_df.merge(df_sorted[[c for c in ["Player", "Team", "SRV", "player_id"] if c in df_sorted.columns]],
                                    on=[c for c in ["Player", "Team"] if c in merge_df.columns],
                                    how="left")
                out["SRV"] = out["SRV"].round(2)
                return out.sort_values("SRV", ascending=False)

            return df_sorted

        def select_and_filter_by_date_slider(df: pd.DataFrame, date_col: str = "Timestamp") -> pd.DataFrame:
            from datetime import timedelta

            dt = pd.to_datetime(df[date_col], errors="coerce", utc=True)
            if getattr(dt.dt, "tz", None) is None:
                dt = dt.dt.tz_localize("UTC")

            df = df.copy()
            df[date_col] = dt

            if not df[date_col].notna().any():
                st.warning(f"No valid dates found in column '{date_col}'.")
                return df.iloc[0:0]

            min_date = df[date_col].min().date()
            max_date = df[date_col].max().date()

            datecol1, datecol2, datecol3 = st.columns([1, 1.5, 1])
            with datecol2:
                start_date, end_date = st.slider(
                    "Select date range",
                    min_value=min_date,
                    max_value=max_date,
                    value=(min_date, max_date),
                    step=timedelta(days=1),
                    format="YYYY-MM-DD",
                )

            start_dt = pd.Timestamp(start_date).tz_localize("UTC")
            end_dt_exclusive = pd.Timestamp(end_date).tz_localize("UTC") + pd.Timedelta(days=1)

            mask = (df[date_col] >= start_dt) & (df[date_col] < end_dt_exclusive)
            filtered = df.loc[mask].copy()

            st.caption(f"Showing {len(filtered):,} of {len(df):,} rows from {start_date} to {end_date} (inclusive).")
            return filtered

        # === FILTER ROW ===
        pos_col1, pos_col2, pos_col3, pos_col4, pos_col5 = st.columns([1, 1, 1, 1, 1])
        with pos_col1:
            player_search = st.text_input("Player search", "").strip()
        with pos_col2:
            pos_chosen = st.selectbox("Choose Position", ["Hitters", "Pitchers"])
        with pos_col3:
            h_pos_chosen = st.selectbox("Hitter Pos", ["All", "C", "1B", "2B", "3B", "SS", "OF"])
        with pos_col4:
            team_selection_list.sort()
            team_selection_list = ["All"] + team_selection_list
            team_choose = st.selectbox("Choose Team", team_selection_list)

        # ===== HITERS =====
        if pos_chosen == "Hitters":
            filtered_hitdb = select_and_filter_by_date_slider(hitdb, date_col="game_date")

            # aggregate over chosen date range
            df = (
                filtered_hitdb
                .groupby(["Player", "player_id"], as_index=False)[["R", "HR", "RBI", "SB", "H", "AB"]]
                .sum()
            )

            # merge in position info
            posdata_unique = posdata.drop_duplicates()
            df = pd.merge(df, posdata_unique, how="left", left_on="player_id", right_on="ID")

            df["Pos2"] = df["Pos"].str.split("/", expand=True)[0]
            df["AVG"] = (df["H"] / df["AB"]).round(3)
            df = df[df["AB"] > 9]  # keep only hitters with some AB
            df["Team"] = df["player_id"].map(teamdict)
            df = df[["Player", "player_id", "Team", "Pos2", "AB", "R", "HR", "RBI", "SB", "AVG"]]
            df = df.rename({"Pos2": "Pos"}, axis=1)

            hitter_srv = calculateSRV_Hitters(df)
            # drop AB from the srv frame; we already have it in df
            if "AB" in hitter_srv.columns:
                hitter_srv = hitter_srv.drop(["AB"], axis=1, errors="ignore")

            show_df = pd.merge(df, hitter_srv, on=["Player", "Team", "player_id"], how="left")
            show_df = show_df.round(2)
            show_df = show_df.sort_values(by="SRV", ascending=False)
            show_df['player_id'] = show_df['player_id'].astype(int)

            # apply team filter
            if team_choose != "All":
                show_df = show_df[show_df["Team"] == team_choose]

            # apply hitter pos filter
            if h_pos_chosen != "All":
                show_df = show_df[show_df["Pos"] == h_pos_chosen]

            show_df = show_df[['Player','player_id','Team','Pos','SRV','AB','R','HR','RBI','SB','AVG']]
            # apply player search filter
            if player_search:
                show_df = show_df[show_df["Player"].str.contains(player_search, case=False, na=False)]
            
                show_df = show_df[['Player','player_id','Team','Pos','SRV','AB','R','HR','RBI','SB','AVG']]


            styled_df = (
                show_df.style
                .background_gradient(subset=["SRV"], cmap="Blues")
                .set_table_styles(
                    [{
                        "selector": "th, td",
                        "props": [("font-size", "16px")]
                    }]
                )
                .set_properties(subset=["SRV"], **{"font-weight": "bold", "font-size": "18px"})
                .format({
                    "AB": "{:.0f}",
                    "R": "{:.0f}",
                    "HR": "{:.0f}",
                    "RBI": "{:.0f}",
                    "SB": "{:.0f}",
                    "AVG": "{:.3f}",
                    "SRV": "{:.2f}",
                    "R_z": "{:.2f}",
                    "HR_z": "{:.2f}",
                    "RBI_z": "{:.2f}",
                    "SB_z": "{:.2f}",
                    "AVG_z": "{:.2f}",
                })
            )

            h_rv_showcol1,h_rv_showcol2,h_rv_showcol3 = st.columns([1,3,1])
            with h_rv_showcol2:
                if len(show_df)<2:
                    st.dataframe(
                        styled_df,
                        hide_index=True,
                        use_container_width=True,
                        height=70,
                    )
                    
                else:
                    st.dataframe(
                        styled_df,
                        hide_index=True,
                        use_container_width=True,
                        height=600,
                    )

            st.markdown("<br><hr>",unsafe_allow_html=True)
            # ===== 30-day rolling SRV plot (hitters) =====
            # show only when we've narrowed to exactly one player
            unique_players = show_df["player_id"].dropna().unique()
            if len(unique_players) == 1:
                selected_pid = unique_players[0]

                # build day-by-day 30d SRV for that player
                hd = hitdb.copy()
                hd["game_date"] = pd.to_datetime(hd["game_date"])
                hd = hd.sort_values("game_date")

                all_dates = hd["game_date"].dt.normalize().unique()
                rows = []
                for d in all_dates:
                    start = d - np.timedelta64(29, "D")
                    window = hd[(hd["game_date"] >= start) & (hd["game_date"] <= d)]
                    if window.empty:
                        continue

                    agg = (
                        window.groupby(["Player", "player_id"], as_index=False)[["R", "HR", "RBI", "SB", "H", "AB"]]
                        .sum()
                    )
                    agg["AVG"] = np.where(agg["AB"] > 0, agg["H"] / agg["AB"], 0)
                    agg["Team"] = agg["player_id"].map(teamdict)

                    srv_frame = calculateSRV_Hitters(agg)
                    this_row = srv_frame[srv_frame["player_id"] == selected_pid]
                    if not this_row.empty:
                        rows.append({"date": pd.to_datetime(d).date(), "SRV": float(this_row["SRV"].iloc[0])})

                if rows:
                    srv_hist = pd.DataFrame(rows).sort_values("date")
                    st.subheader(f"30-Day Rolling SRV – {show_df['Player'].iloc[0]}")
                    srv_hist = srv_hist.set_index("date")
                    st.line_chart(srv_hist)

        # ===== PITCHERS =====
        if pos_chosen == "Pitchers":
            rp_only = st.checkbox("Show Only RP?")

            filtered_pitdb = select_and_filter_by_date_slider(pitdb, date_col="game_date")

            df = (
                filtered_pitdb
                .groupby(["Player", "player_id"], as_index=False)[["IP", "ER", "H", "BB", "SO", "W", "SV"]]
                .sum()
            )

            df["ERA"] = (df["ER"] * 9 / df["IP"]).round(3)
            df["WHIP"] = ((df["H"] + df["BB"]) / df["IP"]).round(3)
            df = df[df["IP"] > 1]

            df["Team"] = df["player_id"].map(teamdict_p)
            df = df[["Player", "player_id", "Team", "IP", "W", "SO", "SV", "ERA", "WHIP"]]

            pitcher_srv = calculateSRV_Pitchers(df)
            if "IP" in pitcher_srv.columns:
                pitcher_srv = pitcher_srv.drop(["IP"], axis=1, errors="ignore")

            show_df = pd.merge(df, pitcher_srv, on=["Player", "Team", "player_id"], how="left")
            show_df = show_df.round(2)
            show_df = show_df.sort_values(by="SRV", ascending=False)

            if team_choose != "All":
                show_df = show_df[show_df["Team"] == team_choose]

            if rp_only:
                show_df = show_df[show_df["SV"] > 0]

            if player_search:
                show_df = show_df[show_df["Player"].str.contains(player_search, case=False, na=False)]

            
            show_df = show_df[['Player','player_id','Team','SRV','IP','W','SO','SV','ERA','WHIP']]
            prvcol1,prvcol2,prvcol3 = st.columns([1,5,1])
            with prvcol2:
                styled_df = (
                    show_df.style
                    .background_gradient(subset=["SRV"], cmap="Blues")
                    .set_table_styles(
                        [{
                            "selector": "th, td",
                            "props": [("font-size", "16px")]
                        }]
                    )
                    .set_properties(subset=["SRV"], **{"font-weight": "bold", "font-size": "18px"})
                    .format({
                        "IP": "{:.1f}",
                        "ERA": "{:.2f}",
                        "WHIP": "{:.2f}",
                        "SRV": "{:.2f}",
                        "W_z": "{:.2f}",
                        "SV_z": "{:.2f}",
                        "SO_z": "{:.2f}",
                        "ERA_z": "{:.2f}",
                        "WHIP_z": "{:.2f}",
                    })
                )

                if len(show_df)<2:
                    st.dataframe(
                    styled_df,
                    hide_index=True,
                    use_container_width=True,
                    height=75,
                )
                else:
                    st.dataframe(
                        styled_df,
                        hide_index=True,
                        use_container_width=True,
                        height=600,
                    )

            st.markdown("<br><hr>",unsafe_allow_html=True)
            # ===== 30-day rolling SRV plot (pitchers) =====
            unique_players = show_df["player_id"].dropna().unique()
            if len(unique_players) == 1:
                selected_pid = unique_players[0]

                pdx = pitdb.copy()
                pdx["game_date"] = pd.to_datetime(pdx["game_date"])
                pdx = pdx.sort_values("game_date")
                all_dates = pdx["game_date"].dt.normalize().unique()
                rows = []
                for d in all_dates:
                    start = d - np.timedelta64(29, "D")
                    window = pdx[(pdx["game_date"] >= start) & (pdx["game_date"] <= d)]
                    if window.empty:
                        continue

                    agg = (
                        window.groupby(["Player", "player_id"], as_index=False)[["IP", "ER", "H", "BB", "SO", "W", "SV"]]
                        .sum()
                    )
                    # rebuild rate stats
                    agg = agg[agg["IP"] > 0]
                    agg["ERA"] = (agg["ER"] * 9 / agg["IP"]).round(3)
                    agg["WHIP"] = ((agg["H"] + agg["BB"]) / agg["IP"]).round(3)
                    agg["Team"] = agg["player_id"].map(teamdict_p)

                    srv_frame = calculateSRV_Pitchers(agg)
                    this_row = srv_frame[srv_frame["player_id"] == selected_pid]
                    if not this_row.empty:
                        rows.append({"date": pd.to_datetime(d).date(), "SRV": float(this_row["SRV"].iloc[0])})

                if rows:
                    srv_hist = pd.DataFrame(rows).sort_values("date").set_index("date")
                    st.subheader(f"30-Day Rolling SRV – {show_df['Player'].iloc[0]}")
                    st.line_chart(srv_hist)

    
    if tab == "Player Rater2":
        st.markdown("<h1><center>Dynamic Player Rater</center></h1>", unsafe_allow_html=True)
        team_selection_list = list(hitdb['affiliate'].unique())
        teamlist=hitdb[['player_id','game_date','affiliate']].sort_values(by='game_date')
        teamlist[['player_id','affiliate']].drop_duplicates(keep='last')
        teamdict = dict(zip(teamlist.player_id,teamlist.affiliate))

        teamlist_p=pitdb[['player_id','game_date','affiliate']].sort_values(by='game_date')
        teamlist_p[['player_id','affiliate']].drop_duplicates(keep='last')
        teamdict_p = dict(zip(teamlist_p.player_id,teamlist_p.affiliate))

        ### FUNCTIONS
        def calculateSGP_Hitters(hitdb: pd.DataFrame, merge_df: pd.DataFrame | None = None):
            df = hitdb.copy()

            count_cats = ["R", "HR", "RBI", "SB"]
            for cat in count_cats:
                std = df[cat].std(ddof=0)
                df[f"{cat}_z"] = (df[cat] - df[cat].mean()) / (std if std != 0 else 1.0)

            total_ab = df["AB"].sum()
            lg_avg = np.divide((df["AVG"] * df["AB"]).sum(), total_ab) if total_ab else df["AVG"].mean()

            df["AVG_contrib"] = (df["AVG"] - lg_avg) * df["AB"]
            std = df["AVG_contrib"].std(ddof=0)
            df["AVG_z"] = (df["AVG_contrib"] - df["AVG_contrib"].mean()) / (std if std != 0 else 1.0)

            z_cols = [f"{c}_z" for c in count_cats] + ["AVG_z"]
            df["SGP"] = df[z_cols].sum(axis=1)

            df_sorted = (
                df[["Player", "Team", "AB", "SGP"] + z_cols]
                .sort_values("SGP", ascending=False)
                .reset_index(drop=True)
            )

            if merge_df is not None:
                out = merge_df.merge(df_sorted[["Player", "Team", "SGP"]], on=["Player", "Team"], how="left")
                out["SGP"] = out["SGP"].round(2)
                return out.sort_values("SGP", ascending=False)

            return df_sorted
        
        def calculateSGP_Pitchers(pitchdb: pd.DataFrame, merge_df: pd.DataFrame | None = None):
            df = pitchdb.copy()

            count_cats = ["W", "SV", "SO"]
            for cat in count_cats:
                std = df[cat].std(ddof=0)
                df[f"{cat}_z"] = (df[cat] - df[cat].mean()) / (std if std != 0 else 1.0)

            lg_era = np.divide((df["ERA"] * df["IP"]).sum(), df["IP"].sum()) if df["IP"].sum() else df["ERA"].mean()
            df["ERA_contrib"] = (lg_era - df["ERA"]) * df["IP"]
            std = df["ERA_contrib"].std(ddof=0)
            df["ERA_z"] = (df["ERA_contrib"] - df["ERA_contrib"].mean()) / (std if std != 0 else 1.0)

            lg_whip = np.divide((df["WHIP"] * df["IP"]).sum(), df["IP"].sum()) if df["IP"].sum() else df["WHIP"].mean()
            df["WHIP_contrib"] = (lg_whip - df["WHIP"]) * df["IP"]
            std = df["WHIP_contrib"].std(ddof=0)
            df["WHIP_z"] = (df["WHIP_contrib"] - df["WHIP_contrib"].mean()) / (std if std != 0 else 1.0)

            z_cols = [f"{c}_z" for c in count_cats] + ["ERA_z", "WHIP_z"]
            df["SGP"] = df[z_cols].sum(axis=1)

            df_sorted = (
                df[["Player", "Team", "IP", "SGP"] + z_cols]
                .sort_values("SGP", ascending=False)
                .reset_index(drop=True)
            )

            if merge_df is not None:
                out = merge_df.merge(df_sorted[["Player", "Team", "SGP"]], on=["Player", "Team"], how="left")
                out["SGP"] = out["SGP"].round(2)
                return out.sort_values("SGP", ascending=False)

            return df_sorted
        
        def select_and_filter_by_date_slider(df: pd.DataFrame, date_col: str = "Timestamp") -> pd.DataFrame:
            """
            Build a date RANGE SLIDER from the data's min/max dates and
            return df filtered to that inclusive range.
            """
            from datetime import timedelta

            # Parse robustly (e.g., "2025-09-01 13:17:19 EDT")
            dt = pd.to_datetime(df[date_col], errors="coerce", utc=True)
            if getattr(dt.dt, "tz", None) is None:
                dt = dt.dt.tz_localize("UTC")

            df = df.copy()
            df[date_col] = dt

            if not df[date_col].notna().any():
                st.warning(f"No valid dates found in column '{date_col}'.")
                return df.iloc[0:0]

            # Slider uses date (not datetime) for a nice UX
            min_date = df[date_col].min().date()
            max_date = df[date_col].max().date()

            datecol1, datecol2, datecol3 = st.columns([1,1.5,1])
            with datecol2:
                start_date, end_date = st.slider(
                    "Select date range",
                    min_value=min_date,
                    max_value=max_date,
                    value=(min_date, max_date),
                    step=timedelta(days=1),
                    format="YYYY-MM-DD",
                )

            # Inclusive end: [start, end] by filtering < (end + 1 day)
            start_dt = pd.Timestamp(start_date).tz_localize("UTC")
            end_dt_exclusive = pd.Timestamp(end_date).tz_localize("UTC") + pd.Timedelta(days=1)

            mask = (df[date_col] >= start_dt) & (df[date_col] < end_dt_exclusive)
            filtered = df.loc[mask].copy()

            st.caption(f"Showing {len(filtered):,} of {len(df):,} rows from {start_date} to {end_date} (inclusive).")
            return filtered

        
        pos_col1, pos_col2,pos_col3,pos_col4,pos_col5 = st.columns([1,1,1,1,1])
        with pos_col2:
            pos_chosen = st.selectbox('Choose Position',['Hitters','Pitchers'])
        with pos_col3:
            h_pos_chosen = st.selectbox('Hitter Pos',['All','C','1B','2B','3B','SS','OF'])
        with pos_col4:
            team_selection_list.sort()
            team_selection_list = ['All'] + team_selection_list
            team_choose = st.selectbox('Choose Team', team_selection_list)

        if pos_chosen == 'Hitters':
            filtered_hitdb = select_and_filter_by_date_slider(hitdb, date_col="game_date")

            df = filtered_hitdb.groupby(['Player','player_id'],as_index=False)[['R','HR','RBI','SB','H','AB']].sum()
            posdata = posdata.drop_duplicates()
            df = pd.merge(df,posdata,how='left',left_on='player_id', right_on='ID')
            df['Pos2'] = df['Pos'].str.split('/',expand=True)[0]
            df['AVG'] = round(df['H']/df['AB'],3)
            df = df[df['AB']>9]
            df['Team'] = df['player_id'].map(teamdict)
            df = df[['Player','Team','Pos2','AB','R','HR','RBI','SB','AVG']]
            df = df.rename({'Pos2': 'Pos'},axis=1)

            hitter_sgp = calculateSGP_Hitters(df)
            hitter_sgp = hitter_sgp.drop(['AB'],axis=1)
            show_df = pd.merge(df,hitter_sgp,on=['Player','Team'],how='left')
            show_df = show_df.round(2)
            show_df = show_df.sort_values(by='SGP',ascending=False)

            if team_choose == 'All':
                pass
            else:
                show_df = show_df[show_df['Team']==team_choose]

            if h_pos_chosen == 'All':
                pass
            else:
                show_df = show_df[show_df['Pos']==h_pos_chosen]

            

            styled_df = (
                show_df.style
                .background_gradient(subset=["SGP"], cmap="Blues")   # blue shading on SGP
                .set_table_styles(                                   # make text bigger
                    [{
                        "selector": "th, td",
                        "props": [("font-size", "16px")]
                    }]
                ).set_properties(subset=["SGP"], **{"font-weight": "bold", "font-size": "18px"})
                .format({"AB": "{:.0f}",
                        "R": "{:.0f}",
                        "HR": "{:.0f}",
                        "RBI": "{:.0f}",
                        "SB": "{:.0f}",
                        "AVG": "{:.3f}",
                        "SGP": "{:.2f}",
                        "R_z": "{:.2f}",
                        "HR_z": "{:.2f}",
                        "RBI_z": "{:.2f}",
                        "SB_z": "{:.2f}",
                        "AVG_z": "{:.2f}",})
                )

            st.dataframe(
                styled_df, hide_index=True,
                use_container_width=True,   # stretch across page
                height=600                  # adjust height to your liking
            )
        if pos_chosen == 'Pitchers':
            rp_only = st.checkbox('Show Only RP?')

            filtered_pitdb = select_and_filter_by_date_slider(pitdb, date_col="game_date")

            df = filtered_pitdb.groupby(['Player','player_id'],as_index=False)[['IP','ER','H','BB','SO','W','SV']].sum()

            df['ERA'] = round(df['ER']*9/df['IP'],3)
            df['WHIP'] = round((df['H']+df['BB'])/df['IP'],3)

            df = df[df['IP']>1]
            df['Team'] = df['player_id'].map(teamdict_p)
            df = df[['Player','Team','IP','W','SO','SV','ERA','WHIP']]

            pitcher_sgp = calculateSGP_Pitchers(df)
            pitcher_sgp = pitcher_sgp.drop(['IP'],axis=1)
            show_df = pd.merge(df,pitcher_sgp,on=['Player','Team'],how='left')
            show_df = show_df.round(2)
            show_df = show_df.sort_values(by='SGP',ascending=False)

            if team_choose == 'All':
                pass
            else:
                show_df = show_df[show_df['Team']==team_choose]

            if rp_only:
                show_df = show_df[show_df['SV']>0]

            styled_df = (
                show_df.style
                .background_gradient(subset=["SGP"], cmap="Blues")   # blue shading on SGP
                .set_table_styles(                                   # make text bigger
                    [{
                        "selector": "th, td",
                        "props": [("font-size", "16px")]
                    }]
                ).set_properties(subset=["SGP"], **{"font-weight": "bold", "font-size": "18px"})
                .format({"IP": "{:.1f}",
                         "ERA": "{:.2f}",
                         "WHIP": "{:.2f}",
                         "SGP": "{:.2f}",
                         "W_z": "{:.2f}",
                         "SV_z": "{:.2f}",
                         "SO_z": "{:.2f}",
                         "ERA_z": "{:.2f}",
                         "WHIP_z": "{:.2f}",
                         })
                )

            st.dataframe(
                styled_df, hide_index=True,
                use_container_width=True,   # stretch across page
                height=600                  # adjust height to your liking
            )

        
    
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


    if tab == "Player Projection Details":
        st.markdown("<h2><center><br>Todays Projection Details</h2></center>", unsafe_allow_html=True)
        a_col1, a_col2, a_col3 = st.columns([1,1,4])
        with a_col1:
            pos_choose = st.selectbox('Choose player', ['Hitters','Pitchers'])
            if pos_choose == 'Hitters':
                player_list = list(hitterproj['Hitter'].unique())
                hitter_choose = st.selectbox('Choose a Hitter', player_list)
            else:
                player_list = list(pitcherproj['Pitcher'].unique())
                pitcher_choose = st.selectbox('Choose a Pitcher', player_list)
        if pos_choose == 'Hitters':
            with a_col2:
                this_hitter_projection = hitterproj[hitterproj['Hitter']==hitter_choose][['Hitter','DKPts','PA','R','HR','RBI','SB','SO','BB']]
                opp_sp = hitterproj[hitterproj['Hitter']==hitter_choose]['OppSP'].iloc[0]
                this_hitter_id = hitterproj[hitterproj['Hitter']==hitter_choose]['ID'].iloc[0]
                st.image(get_player_image(this_hitter_id), width=125)

                this_hitter_vs_avg = h_vs_avg[h_vs_avg['Hitter']==hitter_choose]

                today_dk_proj = this_hitter_vs_avg['DKPts'].iloc[0]
                avg_dk_proj = this_hitter_vs_avg['Avg DK Proj'].iloc[0]
                max_proj = np.max([today_dk_proj,avg_dk_proj])

                today_hr_proj = this_hitter_vs_avg['HR'].iloc[0]
                avg_hr_proj = this_hitter_vs_avg['Avg HR Proj'].iloc[0]
                max_hr_proj = np.max([today_hr_proj,avg_hr_proj])

            with a_col3:
                game_park = pitcherproj[pitcherproj['Pitcher']==opp_sp]['HomeTeam'].iloc[0]

                st.markdown(f"<b><font size=5>Todays Matchup: vs. {opp_sp} in {game_park}</font></b>", unsafe_allow_html=True)
                st.dataframe(this_hitter_projection, hide_index=True)

                player_bet_lines = alllines[(alllines['Player']==hitter_choose)&(alllines['Book']=='DraftKings')][['Type','OU','Line','Price']]
                #st.dataframe(player_bet_lines)


            b_col1, b_col2 = st.columns([1,2.5])
            with b_col1:
                # FANTASY POINTS PLOT
                fig, ax = plt.subplots(figsize=(4, 3))
                labels = ['Today', 'Avg']
                values = [today_dk_proj, avg_dk_proj]
                bars = ax.bar(labels, values, color=['#1f77b4', '#2ca02c'], edgecolor='black', width=0.85)

                # Add league average line
                league_avg = 7.8
                ax.axhline(y=league_avg, color='red', linestyle='--', alpha=0.7)

                # Add numbers on top of bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        x=bar.get_x() + bar.get_width() / 2,
                        y=height + .1 if height >= 0 else height - 0.1,
                        s=f'{height:.1f}',
                        ha='center',
                        va='bottom' if height >= 0 else 'top',
                        fontsize=14,
                        fontweight='bold'
                    )
                # Customize chart
                ax.set_title('FPts Projection Comparison', fontsize=14)
                ax.legend(fontsize=12, loc='best')
                ax.tick_params(axis='both', labelsize=12)
                ax.grid(True, axis='y', linestyle='--', alpha=0.3)
                ax.set_ylim(top=max_proj+2)
                plt.tight_layout(pad=.5)

                # Display the chart
                st.pyplot(fig)

                
                ## HOMERS PLOT
                fig, ax = plt.subplots(figsize=(4,3))
                labels = ['Today', 'Avg']
                values = [today_hr_proj, avg_hr_proj]
                bars = ax.bar(labels, values, color=['#1f77b4', '#2ca02c'], edgecolor='black', width=0.85)

                # Add league average line
                league_avg = 7.8
                ax.axhline(y=league_avg, color='red', linestyle='--', alpha=0.7)

                # Add numbers on top of bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        x=bar.get_x() + bar.get_width() / 2,
                        y=height + .01 if height >= 0 else height - 0.1,
                        s=f'{height:.2f}',
                        ha='center',
                        va='bottom' if height >= 0 else 'top',
                        fontsize=14,
                        fontweight='bold'
                    )
                # Customize chart
                ax.set_title('HR Projection Comparison', fontsize=14)
                ax.legend(fontsize=12, loc='best')
                ax.tick_params(axis='both', labelsize=12)
                ax.grid(True, axis='y', linestyle='--', alpha=0.3)
                ax.set_ylim(top=max_hr_proj+.1)
                plt.tight_layout(pad=.5)

                # Display the chart
                st.pyplot(fig)


    
    if tab == "Matchups":
        st.markdown("<h2><center><br>Projections Detail</h2></center>", unsafe_allow_html=True)

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
        def optimize_lineup(players, player_usage, max_usage, used_lineups, name_to_indices):
            import pulp

            # Initialize PuLP problem
            prob = pulp.LpProblem("DFS_Optimizer", pulp.LpMaximize)

            # Decision variables: 1 if roster spot (row) is used
            player_vars = pulp.LpVariable.dicts("Player", players.index, cat="Binary")

            # Objective: maximize projected points
            prob += pulp.lpSum(players.loc[i, "Points"] * player_vars[i] for i in players.index)

            # 1) Salary cap
            prob += pulp.lpSum(players.loc[i, "Salary"] * player_vars[i] for i in players.index) <= SALARY_CAP

            # 2) Roster size
            prob += pulp.lpSum(player_vars[i] for i in players.index) == ROSTER_SIZE

            # 3) Positional constraints
            for pos, count in POSITIONS.items():
                prob += pulp.lpSum(player_vars[i] for i in players.index if players.loc[i, "Pos"] == pos) == count

            # 3b) Single player per lineup (prevent same Name twice across positions)
            for name, idxs in name_to_indices.items():
                prob += pulp.lpSum(player_vars[i] for i in idxs) <= 1

            # 4) Max exposure constraint (lock out players already at/over cap)
            for i in players.index:
                pname = players.loc[i, "Name"]
                if pname in player_usage and player_usage[pname] >= max_usage:
                    prob += player_vars[i] == 0

            # 5) Exclude previously used exact lineups (no identical set)
            for lineup_indices in used_lineups:
                prob += pulp.lpSum(player_vars[i] for i in lineup_indices) <= ROSTER_SIZE - 1

            # Solve
            prob.solve()

            # Extract results
            if pulp.LpStatus[prob.status] != "Optimal":
                return None, 0, 0, []

            selected_indices = [i for i in players.index if player_vars[i].varValue == 1]
            lineup_df = pd.DataFrame([players.loc[i] for i in selected_indices])
            total_points = float(sum(players.loc[i, "Points"] for i in selected_indices))
            total_salary = float(sum(players.loc[i, "Salary"] for i in selected_indices))
            return lineup_df, total_points, total_salary, selected_indices


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
                # Build once after you finish constructing/cleaning `players` (right after astype(float))
                name_to_indices = players.groupby('Name').apply(lambda s: list(s.index)).to_dict()

                #lineup_df, total_points, total_salary, selected_indices = optimize_lineup(players, player_usage, max_usage, used_lineups)
                lineup_df, total_points, total_salary, selected_indices = optimize_lineup(players, player_usage, max_usage, used_lineups, name_to_indices)

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

    if tab == "Zone Matchups":
        p_hand_dict = dict(zip(mlbplayerinfo.Player, mlbplayerinfo.PitchSide))
        h_hand_dict = dict(zip(mlbplayerinfo.Player, mlbplayerinfo.BatSide))

        hotzonedata = hotzonedata[hotzonedata['zone']>0]
        #hotzonedata['xwOBA'] = np.where(hotzonedata['IsBIP']<49, 0, hotzonedata['xwOBA'])
        st.markdown("<h1><center>Zone Matchups</h1></center>",unsafe_allow_html=True)
        hotzonedata['P Hand'] = hotzonedata['player_name'].map(p_hand_dict)
        hotzonedata['B Hand'] = hotzonedata['BatterName'].map(h_hand_dict)

        zone_matchups_data_1 = pitcherproj[['Pitcher','ID']]
        zone_matchups_data_1.columns=['Pitcher','Pitcher ID']
        zone_matchups_data2 = hitterproj[['Hitter','ID','Team','Opp','OppSP','Park']]
        zone_matchups_data2.columns=['Hitter','ID','Team','Opp','Pitcher','Park']
        zone_matchups_data = pd.merge(zone_matchups_data2, zone_matchups_data_1, on='Pitcher', how='left')

        game_selection = zone_matchups_data2[['Team','Opp','Park']].drop_duplicates()
        game_selection['Symb'] = np.where(game_selection['Team']==game_selection['Park'],'vs','@')
        game_selection = game_selection[game_selection['Symb']=='@']
        game_selection['Game'] = game_selection['Team']+' '+game_selection['Symb']+' '+game_selection['Park']
        
        game_list = list(game_selection['Game'])

        box_col1, box_col2, box_col3 = st.columns([1,1,1])
        with box_col1:
            game_selected = st.selectbox('Select a game',game_list)
        with box_col2:
            available_team_1 = game_selected.split('@')[0]
            available_team_2 = game_selected.split('@')[1]
            team_selected = st.selectbox('Select a team',[available_team_1,available_team_2])
            team_selected = team_selected.strip()
            this_matchup_data = zone_matchups_data[zone_matchups_data['Team']==team_selected]
            this_pid = this_matchup_data['Pitcher ID'].iloc[0]
            this_pname = this_matchup_data['Pitcher'].iloc[0]
            this_matchup_data = zone_matchups_data[zone_matchups_data['Team']==team_selected]
            this_p_hand = hotzonedata[(hotzonedata['pitcher']==this_pid)]['P Hand'].iloc[0]



        with box_col3:
            hitter_selection =list(this_matchup_data['Hitter'])
            zone_hitter_selection = st.selectbox("Select a hitter", hitter_selection)
            hitter_zone_data = hotzonedata[(hotzonedata['BatterName']==zone_hitter_selection)&(hotzonedata['Split']==this_p_hand)][['BatterName','batter','zone','IsBIP','xwOBA']].sort_values(by='zone')

        # Show pitcher map
        pitcher_zone_data_vr = hotzonedata[(hotzonedata['pitcher']==this_pid)&(hotzonedata['Split']=='R')][['player_name','pitcher','Split','zone','IsBIP','xwOBA']].sort_values(by='zone')
        pitcher_zone_data_vl = hotzonedata[(hotzonedata['pitcher']==this_pid)&(hotzonedata['Split']=='L')][['player_name','pitcher','Split','zone','IsBIP','xwOBA']].sort_values(by='zone')

        # TEST PLOT
        col1, col2, col3, col4 = st.columns([1,2,2,1])
        with col2:
            st.markdown(f"<h5>{this_pname} xwOBA Zones vs. RHB</h5>", unsafe_allow_html=True)
            data = {
                'zone': list(pitcher_zone_data_vr['zone']),
                'xwOBA': list(pitcher_zone_data_vr['xwOBA'])
            }
            df = pd.DataFrame(data)
            fig, ax = plt.subplots(3, 3, figsize=(6, 6))
            axes = ax.flatten()
            norm = plt.Normalize(df['xwOBA'].min(), df['xwOBA'].max())
            cmap = plt.get_cmap('RdYlGn_r')  # Reverse green to red

            for idx, zone in enumerate(df['zone']):
                # Create a rectangle for the cell
                rect = plt.Rectangle((0, 0), 1, 1, linewidth=1, edgecolor='black', 
                                    facecolor=cmap(norm(df['xwOBA'][idx])), zorder=0)
                axes[idx].add_patch(rect)
                # Add text
                axes[idx].text(0.5, 0.5, f"{df['xwOBA'][idx]:.3f}", 
                            ha='center', va='center', fontsize=25)
                axes[idx].set_xlim(0, 1)
                axes[idx].set_ylim(0, 1)
                axes[idx].axis('off')

            plt.tight_layout()
            st.pyplot(fig)
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label='xwOBA')
        with col3:
            st.markdown(f"<h5>{this_pname} xwOBA Zones vs. LHB</h5>", unsafe_allow_html=True)
            data = {
                'zone': list(pitcher_zone_data_vl['zone']),
                'xwOBA': list(pitcher_zone_data_vl['xwOBA'])
            }
            df = pd.DataFrame(data)
            fig, ax = plt.subplots(3, 3, figsize=(6, 6))
            axes = ax.flatten()
            norm = plt.Normalize(df['xwOBA'].min(), df['xwOBA'].max())
            cmap = plt.get_cmap('RdYlGn_r')  # Reverse green to red

            for idx, zone in enumerate(df['zone']):
                # Create a rectangle for the cell
                rect = plt.Rectangle((0, 0), 1, 1, linewidth=1, edgecolor='black', 
                                    facecolor=cmap(norm(df['xwOBA'][idx])), zorder=0)
                axes[idx].add_patch(rect)
                # Add text
                axes[idx].text(0.5, 0.5, f"{df['xwOBA'][idx]:.3f}", 
                            ha='center', va='center', fontsize=25)
                axes[idx].set_xlim(0, 1)
                axes[idx].set_ylim(0, 1)
                axes[idx].axis('off')

            plt.tight_layout()
            st.pyplot(fig)
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label='xwOBA')
        
        #hitter_selection =list(this_matchup_data['Hitter'])
        #zone_hitter_selection = st.selectbox("Select a hitter", hitter_selection)
        #hitter_zone_data = hotzonedata[(hotzonedata['BatterName']==zone_hitter_selection)&(hotzonedata['Split']==this_p_hand)][['BatterName','batter','zone','IsBIP','xwOBA']].sort_values(by='zone')
        
        a_col1, a_col2, a_col3 = st.columns([1,1.5,1])
        #with a_col1:
            #zone_hitter_selection = st.selectbox("Select a hitter", hitter_selection)
            #hitter_zone_data = hotzonedata[(hotzonedata['BatterName']==zone_hitter_selection)&(hotzonedata['Split']==this_p_hand)][['BatterName','batter','zone','IsBIP','xwOBA']].sort_values(by='zone')
        with a_col2:
            st.markdown(f"<h4>{zone_hitter_selection} xwOBA Zones vs. {this_p_hand}HB", unsafe_allow_html=True)
            data = {
                'zone': list(hitter_zone_data['zone']),
                'xwOBA': list(hitter_zone_data['xwOBA'])
            }
            df = pd.DataFrame(data)
            fig, ax = plt.subplots(3, 3, figsize=(3,3))
            axes = ax.flatten()
            norm = plt.Normalize(df['xwOBA'].min(), df['xwOBA'].max())
            cmap = plt.get_cmap('RdYlGn_r')  # Reverse green to red

            for idx, zone in enumerate(df['zone']):
                # Create a rectangle for the cell
                rect = plt.Rectangle((0, 0), 1, 1, linewidth=3, edgecolor='black', 
                                    facecolor=cmap(norm(df['xwOBA'][idx])), zorder=0)
                axes[idx].add_patch(rect)
                # Add text
                axes[idx].text(0.5, 0.5, f"{df['xwOBA'][idx]:.3f}", 
                            ha='center', va='center', fontsize=10)
                axes[idx].set_xlim(0, 1)
                axes[idx].set_ylim(0, 1)
                axes[idx].axis('off')

            plt.tight_layout()
            st.pyplot(fig)
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label='xwOBA')




