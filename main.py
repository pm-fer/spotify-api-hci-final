import streamlit as st
from artist_and_tour_info import feature1 #map and artist search
api_key = "noF5kg6nwwXGlQ4UCnwm9YHGB8ADCjSt"


tab1, tab2 = st.tabs(["Concert Search", "Playlist Creator"])

with tab1:
   st.header("Concert Search")
   feature1()  # display on page

with tab2:
   st.header("Playlist Creator")
   st.write("Pls put something here")