import streamlit as st
import requests
from PIL import Image
from io import BytesIO

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

        st.divider()

        playlist_name = st.text_input("**Playlist Name**", placeholder="Name your concert playlist")

        cover_type = st.selectbox("**Playlist Cover Image Type**", options=["Default", "URL", "Upload Image", "Solid Color"])

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
                        if file_extension not in ['jpg', 'jpeg', 'png']:
                            st.error("Invalid image format. Please upload a JPG or PNG image.")
                            image_type = "Default"
                        else:
                            st.success("Successfully uploaded playlist cover image!")
                            uploaded_image_bytes = BytesIO(uploaded_image.read())
                            playlist_cover = Image.open(uploaded_image_bytes)
                            image_type = "Uploaded Image"
                if cover_type == "Solid Color":
                    color = st.color_picker("**Color Picker**", value="#43B3FF")
                    playlist_cover = Image.new("RGB", (200,200), color)
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
                playlist_cover = cropped_cover.resize((500,500))

                # preview smaller temp image in order to maintain quality of original image
                cover_preview = playlist_cover.resize((200,200))
                st.image(cover_preview, caption="Current Cover: " + image_type)

        playlist_description = st.text_area("**(Optional) Playlist Description**", placeholder="Add a description for your playlist")
        num_songs = st.number_input("**Playlist Song Count**", min_value=2, max_value=20, placeholder="Enter the number of songs to be added to your playlist")

        # implement logic for display playlist table and add playlist to spotify features
        #generate = st.button("Generate Playlist")
        #add_playlist = st.button("Add to my Spotify")