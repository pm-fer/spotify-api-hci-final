import streamlit as st
import requests
import pandas as pd
import plotly.express as px

spotify_key = "4deea18e81a04f68b25d4368813b0134"
spotify_secret = "2d0e76be78b54422b2d9fae7c71f1ff9"
spotify_base_url = 'https://api.spotify.com/v1/'
auth_url = "https://accounts.spotify.com/api/token"
auth_response = requests.post(auth_url, {
    'grant_type': 'client_credentials',
    'client_id': spotify_key,
    'client_secret': spotify_secret,
})
auth_data = auth_response.json()
access_token = auth_data['access_token']
headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}

def vibe_check():
    st.write("\n")

    form = st.form("artist_search")
    artist_input = form.text_input("**Search for an Artist**", placeholder="Enter artist name")
    search = form.form_submit_button(label='Search')

    if artist_input != "":
        # search for artist based on text input (name), limited to 10 results
        search_response = requests.get(
            spotify_base_url + 'search?q={artist_name}&type=artist&limit=10'.format(artist_name=artist_input),
            headers=headers)
        search_dict = search_response.json()

        artist_results = []
        for i in range(len(search_dict.get("artists").get("items"))):
            artist_results.append(search_dict["artists"]["items"][i]["name"])

        # format func allows us to save index of the option that is chosen instead of the option label (makes more sense in this case)
        artist_index = st.selectbox("**Select Artist**", range(len(artist_results)),
                                    format_func=lambda x: artist_results[x], index=None)

        if artist_index != None:
            artist_name = artist_results[artist_index]
            artist_id = search_dict["artists"]["items"][artist_index]["id"]

            tracks_response = requests.get(spotify_base_url + 'artists/{id}/top-tracks'.format(id=artist_id),
                                           headers=headers)
            tracks_dict = tracks_response.json()

            track_ids = ''
            for track in tracks_dict['tracks']:
                track_ids += track["id"] + ','

            track_ids = track_ids[:len(track_ids) - 1]

            audio_features_response = requests.get(spotify_base_url + 'audio-features?ids={ids}'.format(ids=track_ids),
                                           headers=headers)
            audio_features_dict = audio_features_response.json()

            tracks_data = []
            for i, track in enumerate(tracks_dict['tracks']):
                danceability = audio_features_dict["audio_features"][i]["danceability"] * 100.0
                energy = audio_features_dict["audio_features"][i]["energy"] * 100.0
                valence = audio_features_dict["audio_features"][i]["valence"] * 100.0
                liveness = audio_features_dict["audio_features"][i]["liveness"] * 100.0
                track_data = {
                    'Track Name': track['name'],
                    'Popularity': track['popularity'],
                    'Danceability': danceability,
                    'Energy': energy,
                    'Valence': valence,
                    'Liveness': liveness
                }
                tracks_data.append(track_data)

            tracks_df = pd.DataFrame(tracks_data)

            st.divider()

            # line chart with point markers and y-axis label
            fig = px.line(tracks_df, x="Track Name", y=["Popularity", "Danceability", "Energy", "Valence", "Liveness"],
                          color_discrete_sequence=["#43B3FF", "#A020F0", "#FF69B4", "#2CE5C3", "#1F53E0"])
            fig.update_traces(mode='lines+markers')
            fig.update_layout(width=800, height=500, yaxis_title="Rating")
            st.plotly_chart(fig)