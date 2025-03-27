import streamlit as st, pandas as pd, os 

# DATA LOAD BLOCK
base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, 'Data')
hproj = pd.read_csv(f'{file_path}/Tableau_DailyHitterProj.csv')
pproj = pd.read_csv(f'{file_path}/Tableau_DailyPitcherProj.csv')
bets = pd.read_csv(f'{file_path}/betValues.csv')

st.dataframe(hproj)
st.dataframe(pproj)
st.dataframe(bets)