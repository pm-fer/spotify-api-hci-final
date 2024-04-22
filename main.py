import streamlit as st
import requests
import pandas as pd
from PIL import Image
import spotipy
from spotipy import SpotifyOAuth
from spotipy.client import SpotifyException
from artist_and_tour_info import concert_search #map and artist search
import webbrowser
import io
from io import BytesIO
import base64

tm_key = "noF5kg6nwwXGlQ4UCnwm9YHGB8ADCjSt"
spotify_key = "4deea18e81a04f68b25d4368813b0134"
spotify_secret = "2d0e76be78b54422b2d9fae7c71f1ff9"
spotify_base_url = 'https://api.spotify.com/v1/'
redirect_uri = 'http://localhost:8501/'
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

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=spotify_key,
    client_secret=spotify_secret,
    redirect_uri=redirect_uri,
    scope='playlist-modify-public playlist-modify-private ugc-image-upload'
))

if 'auth_complete' not in st.session_state:
    st.session_state.auth_complete = False

auth_code = ""
if 'code' in st.query_params:
    auth_code = st.query_params['code']
    sp.auth_manager.get_access_token(auth_code)

st.set_page_config(page_title='Concert Prep', page_icon=':musical_note:')

tab1, tab2, tab3 = st.tabs(["Playlist Creator", "Concert Search", "Concert Vibes"])

with tab1:
   st.header("Playlist Creator")

   def set_default_cover():
      if artist_image_url != "":
         return get_image_from_url(artist_image_url)
      else:
         return "default-playlist-cover.png"


   def get_image_from_url(image_url):
      try:
         image_response = requests.get(image_url)
         if image_response.status_code == 200:
            image_bytes = BytesIO(image_response.content)
            return Image.open(image_bytes)
         else:
            return False
      except Exception as e:
         return False

   st.write("\n")

   auth_url = sp.auth_manager.get_authorize_url()
   st.write("**If you plan to add your playlist to Spotify, click here and continue on the new tab.**")
   login = st.button("Log in to Spotify")
   if login:
      webbrowser.open_new_tab(auth_url)
   if auth_code != "":
      st.success("Successfully logged in! You may now close the other tab.")
   else:
      st.warning("You are currently not logged in.")

   st.divider()

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

         st.divider()

         col1, col2 = st.columns(2)
         with col1:
            st.subheader(artist_name)

            genres = set()
            for i in range(len(search_dict["artists"]["items"][artist_index]["genres"])):
               genres.add(search_dict["artists"]["items"][artist_index]["genres"][i])

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
            for i in range(len(tracks_dict["tracks"])):
               if tracks_dict["tracks"][i]["preview_url"]:
                  st.write("**Song Preview:** " + "\"" + tracks_dict["tracks"][i]["name"] + "\"")
                  st.audio(tracks_dict["tracks"][i]["preview_url"])
                  found_preview = True
                  break
            if not found_preview:
               st.write("**Song Preview:** N\A")

         with col2:
            artist_image_url = search_dict["artists"]["items"][artist_index]["images"][0]["url"]
            st.image(artist_image_url)

         st.divider()

         st.write("**Top Albums to Include in Playlist:**")
         albums = {}
         # since we can't fetch every album's top songs, only include albums that have a top track for that artist
         for i in range(len(tracks_dict["tracks"])):
            album = tracks_dict["tracks"][i]["album"]["name"]
            if album not in albums:
               # dict keys: album name, dict values: if an album is selected or not
               albums[album] = st.checkbox("\"" + album + "\"", value=True)

         # getting the song duration for the tracks and adding date formatting
         for i, track in enumerate(tracks_dict['tracks']):
            track_id = track['id']
            track_info_response = requests.get(spotify_base_url + 'tracks/{id}'.format(id=track_id), headers=headers)
            track_info_dict = track_info_response.json()
            tracks_dict['tracks'][i]['duration_ms'] = pd.to_datetime(track_info_dict['duration_ms'],
                                                                     unit='ms').strftime('%M:%S')

         # creating the dataframe for the playlist preview table
         tracks_data = []
         for track in tracks_dict['tracks']:
            track_data = {
               'Track Name': track['name'],
               'Album Name': track['album']['name'],
               'Release Date': track['album']['release_date'],
               'Duration': track['duration_ms'],
               'Track URI': track['uri']
            }
            tracks_data.append(track_data)
         df_tracks = pd.DataFrame(tracks_data)

         st.divider()

         playlist_name = st.text_input("**Playlist Name**", placeholder="Name your concert playlist")
         if not playlist_name.strip():
            playlist_name = artist_name + " Concert Prep Playlist"

         cover_type = st.selectbox("**Playlist Cover Image Type**",
                                   options=["Default", "URL", "Upload Image", "Solid Color"])

         col3, col4 = st.columns(2)
         with col4:
            playlist_cover = set_default_cover()
            image_type = "Default"
            if cover_type != "":
               if cover_type == "Default":
                  playlist_cover = set_default_cover()
               if cover_type == "URL":
                  # testing url: https://picsum.photos/200/300
                  cover_url = st.text_input("**Cover URL**", placeholder="Enter the URL of the cover image")
                  if cover_url != "":
                     image = get_image_from_url(cover_url)
                     if not image:
                        st.error("Invalid image url.")
                     else:
                        st.success("Successfully extracted playlist cover image!")
                        playlist_cover = image
                        image_type = "URL"
               if cover_type == "Upload Image":
                  uploaded_image = st.file_uploader("**Choose an image**")
                  if uploaded_image:
                     file_extension = uploaded_image.name.split('.')[-1].lower()
                     if file_extension not in ['jpg', 'jpeg']:
                        st.error("Invalid image format. Please upload a JPG image.")
                        image_type = "Default"
                     else:
                        st.success("Successfully uploaded playlist cover image!")
                        uploaded_image_bytes = BytesIO(uploaded_image.read())
                        playlist_cover = Image.open(uploaded_image_bytes)
                        image_type = "Uploaded Image"
               if cover_type == "Solid Color":
                  color = st.color_picker("**Color Picker**", value="#43B3FF")
                  playlist_cover = Image.new("RGB", (200, 200), color)
                  image_type = "Solid Color"
         with col3:
            st.write("\n")
            if playlist_cover and playlist_cover != "":
               width, height = playlist_cover.size
               size = min(width, height)
               left = int((width - size) / 2)
               upper = int((height - size) / 2)
               right = int(left + size)
               lower = int(upper + size)
               cropped_cover = playlist_cover.crop((left, upper, right, lower))

               # image to be used for playlist
               playlist_cover = cropped_cover.resize((500, 500))

               # preview smaller temp image in order to maintain quality of original image
               cover_preview = playlist_cover.resize((200, 200))
               st.image(cover_preview, caption="Current Cover: " + image_type)

         playlist_description = st.text_area("**Playlist Description**",
                                             placeholder="Add an optional description for your playlist")

         num_songs = st.number_input("**Playlist Song Count (max. 10 songs)**", value=10, min_value=2, max_value=10,
                                     placeholder="Enter the number of songs to be added to your playlist")

         # filter tracks based on selected albums
         selected_albums = [album for album, selected in albums.items() if selected]
         df_filtered_tracks = df_tracks[df_tracks['Album Name'].isin(selected_albums)]

         if len(df_filtered_tracks) < num_songs:
            st.warning("Unable to create a playlist with {num_songs} songs due to selected album filters.".format(
               num_songs=num_songs))
            num_songs = len(df_filtered_tracks)

         st.divider()

         col5, col6 = st.columns([2, 1])
         with col5:
            st.header("**Playlist Preview**")
            if playlist_name != "":
               st.subheader(playlist_name)
            else:
               st.subheader("**Name:** N/A")
            if playlist_description != "":
               st.write("**Description:** " + playlist_description)
            else:
               st.write("**Description:** N/A")

         with col6:
            st.image(cover_preview)

         st.write("\n")

         # display DataFrame as a table with indices starting from 1
         df_filtered_tracks.reset_index(drop=True, inplace=True)
         df_filtered_tracks.index += 1
         st.dataframe(df_filtered_tracks.head(num_songs), use_container_width=True)

         # Iterate over the DataFrame rows and get the track URIs
         track_uris = []
         empty_playlist = False
         if len(df_filtered_tracks) == 0:
            st.error("Your playlist is empty! Please update your selected album filters.".format(num_songs=num_songs))
            empty_playlist = True
         else:
            for index, row in df_filtered_tracks.iterrows():
               track_uri = row['Track URI']
               track_uris.append(track_uri)
               if index - 1 == num_songs - 1:
                  break

         st.divider()

         # adding playlist to the user's spotify account logic
         if auth_code != "" and not empty_playlist:
            st.subheader("Add to Spotify")
            username_form = st.form("username")
            username = username_form.text_input("**Spotify Username**", placeholder="Enter your username to continue.")
            add_playlist = username_form.form_submit_button(label='Add Playlist')
            if username != "":
               if add_playlist:
                  try:
                     img_byte_arr = io.BytesIO()
                     playlist_cover.save(img_byte_arr, format='JPEG')
                     img_byte_arr = img_byte_arr.getvalue()
                     encoded_img = base64.b64encode(img_byte_arr).decode()

                     playlist = sp.user_playlist_create(username, playlist_name, description=playlist_description)
                     sp.playlist_add_items(playlist['id'], track_uris)
                     sp.playlist_upload_cover_image(playlist['id'], encoded_img)
                     st.success(f'Playlist "{playlist_name}" successfully created and added to your Spotify!')
                  except SpotifyException as se:
                     error_message = se.msg
                     if "cannot create a playlist for another user" in error_message:
                        st.error("Could not add playlist. Make sure your username is correct.")
                     elif "not registered in the Developer Dashboard" in error_message:
                        st.info("Could not add playlist. Our app is currently in development, so users must be "
                                "registered on our Spotify Developer Dashboard in order to use the app as intended.")
                     else:
                        st.error(error_message)
                  except Exception as e:
                     st.error("Unknown error.")


with tab2:
   st.header("Concert Search")
   concert_search(tm_key)

with tab3:
   st.header("Vibe Check an Artist")
   st.write("Pls put something here 2")