import streamlit as st
import requests
import pandas as pd

#FIXME have not altered the slider yet, and debugging information is still present.

api_key = "noF5kg6nwwXGlQ4UCnwm9YHGB8ADCjSt"
# root url: https://app.ticketmaster.com/discovery/v2/

@st.cache_data
def generate_list_of_events_by_areacode_and_artist(state_code, attractionID, radius):
    events_nearby_list_url = f"https://app.ticketmaster.com/discovery/v2/events.json?size=30&attractionId={attractionID}&stateCode={state_code}&radius={radius}&apikey={api_key}"
    events_nearby_list_dict = requests.get(events_nearby_list_url).json()
    st.write(events_nearby_list_dict)
    return events_nearby_list_dict

@st.cache_data
def get_list_of_artists(artist):
    artist_list_url = f"https://app.ticketmaster.com/discovery/v2/attractions.json?classificationName=Music&keyword={artist}&apikey={api_key}"
    artist_list_dict = requests.get(artist_list_url).json()
    st.write(artist_list_dict)
    return artist_list_dict


artist = st.text_input("Enter artist to search")
if artist != "":
    artist_search_dict = get_list_of_artists(artist)

    artist_search_list = []
    for i in artist_search_dict.get("_embedded")["attractions"]:
        artist_search_list.append(i["name"])

    artist_search_list.insert(0, "")
    st.write(artist_search_list)

    index = 0
    if len(artist_search_list) >= 3:
        st.info("Multiple artists found for \"" + artist + "\"! Please select the closet match below:")
        artistID = st.selectbox("Select match", options=artist_search_list)
        st.write(artist_search_list.index(artistID))
        if artistID == "":
            st.error("Select a artist")
        else:
            index = int(artist_search_list.index(artistID))

    else:
        artistID = artist_search_list[1]
        st.write(artistID)
        st.write(artist_search_list.index(artistID))
        index = int(artist_search_list.index(artistID))

    if index > 0:
        attractionID = artist_search_dict.get("_embedded").get("attractions")[index-1].get("id")
        st.write(attractionID)

        state_code = st.text_input("Enter your 2 Letter State code", placeholder="State code")
        radius = int(st.text_input("Enter max distance from zip code in miles", placeholder="0"))
        price_med = int(st.text_input("Enter ideal ticket price in US dollars", placeholder="0"))

        if state_code and radius:
            events_nearby_list_dict = generate_list_of_events_by_areacode_and_artist(state_code, attractionID, radius)
            results = {}
            for i in range(events_nearby_list_dict.get("page").get("totalElements")):
                st.text("im here!")
                nam = events_nearby_list_dict.get("_embedded").get("events")[i].get("name")
                st.text("nam success!")
                u = events_nearby_list_dict.get("_embedded").get("events")[i].get("url")
                st.text("u success!")
                if events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges") is None or events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[0] is None:
                    mi = -1
                    ma = -1
                    st.text("ma and mi -1 success!")
                else:
                    if events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[0].get("min") is None:
                        mi = -1
                        st.text("mi -1 success!")
                    else:
                        mi = events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[0].get("min")
                        st.text("mi success!")
                    if events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[0].get("max") is None or events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[0] is None or events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges") is None:
                        ma = -1
                        st.text("ma -1 success!")
                    else:
                        ma = events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[0].get("max")
                        st.text("ma success!")
                results[i] = {
                    'name': nam,
                    'url': u,
                    'min_price': mi,
                    'max_price': ma
                }
            chart_data = pd.DataFrame.from_dict(results, orient='index')
            st.write(chart_data)
            st.bar_chart(
                chart_data, x="name", y=["min_price", "max_price"], color=["#FF0000", "#0000FF"]
            )

