import streamlit as st
import requests

# add API key and secret
spotify_key = "KEY"
spotify_secret = "SECRET"
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

st.title("Concert Prep Playlist Generator")
st.write("\n")

form = st.form("artist_search")
artist_input = form.text_input("**Search for an Artist**", placeholder="Enter artist name")
search = form.form_submit_button(label='Search')

if artist_input != "":
    # search for artist based on text input (name), limited to 10 results
    search_response = requests.get(spotify_base_url + 'search?q={artist_name}&type=artist&limit=10'.format(artist_name=artist_input),
                                   headers=headers)
    search_dict = search_response.json()

    artist_results = []
    for i in range(len(search_dict.get("artists").get("items"))):
        artist_results.append(search_dict["artists"]["items"][i]["name"])

    # format func allows us to save index of the option that is chosen instead of the option label (makes more sense in this case)
    artist_index = st.selectbox("**Select Artist**", range(len(artist_results)), format_func=lambda x: artist_results[x], index=None)

    if artist_index != None:
        artist_name = artist_results[artist_index]
        artist_id = search_dict["artists"]["items"][artist_index]["id"]

        tracks_response = requests.get(spotify_base_url + 'artists/{id}/top-tracks'.format(id=artist_id),
            headers=headers)
        tracks_dict = tracks_response.json()

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(artist_name)

            genres = []
            for i in range(len(search_dict["artists"]["items"][artist_index]["genres"])):
                genres.append(search_dict["artists"]["items"][artist_index]["genres"][i])

            if len(genres) > 0:
                genres_str = ", ".join(genres)
            else:
                genres_str = "N/A"

            st.write("**Genres:** " + genres_str)

            popularity = search_dict["artists"]["items"][artist_index]["popularity"]
            st.write("**Popularity Rating:** " + str(popularity) + "%")

            top_song_name = tracks_dict["tracks"][0]["name"]
            st.write("**Top Song:** \"" + top_song_name + "\"")

            found_preview = False
            for i in range (len(tracks_dict["tracks"])):
                if tracks_dict["tracks"][i]["preview_url"]:
                    st.write("**Song Preview:** " + "\"" + tracks_dict["tracks"][i]["name"] + "\"")
                    st.audio(tracks_dict["tracks"][i]["preview_url"])
                    found_preview = True
                    break
            if not found_preview:
                st.write("**Song Preview:** N\A")

        with col2:
            st.image(search_dict["artists"]["items"][artist_index]["images"][0]["url"])

        st.divider()

        st.write("**Top Albums to Include in Playlist:**")
        albums = {}
        # since we can't fetch every album's top songs, only include albums that have a top track for that artist
        for i in range(len(tracks_dict["tracks"])):
            album = tracks_dict["tracks"][i]["album"]["name"]
            if album not in albums:
                # dict keys: album name, dict values: if an album is selected or not
                albums[album] = st.checkbox("\"" + album + "\"", value=True)

        st.divider()

        # additional logic pending
        playlist_name = st.text_input("**Playlist Name**", placeholder="Name your concert playlist")
        playlist_description = st.text_area("**(Optional) Playlist Description**", placeholder="Add a description for your playlist")
        num_songs = st.number_input("**Playlist Song Count**", min_value=2, max_value=20, placeholder="Enter the number of songs to be added to your playlist")

        # implement logic for playlist cover, display playlist table, and add playlist to spotify features
        #cover_type = st.selectbox("**Playlist Cover Image Type**", options=["URL", "Upload Photo", "Solid Color"])
        #generate = st.button("Generate Playlist")
        #add_playlist = st.button("Add to my Spotify")
