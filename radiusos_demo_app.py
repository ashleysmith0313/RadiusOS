import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="RadiusOS Facility Mapping", layout="wide")
st.title("📍 RadiusOS Facility Mapping Demo")

uploaded_file = st.file_uploader("Upload Excel file with facility, city, state", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if {'facility_name', 'city', 'state'}.issubset(df.columns):

        df['full_address'] = df['facility_name'] + ", " + df['city'] + ", " + df['state']

        geolocator = Nominatim(user_agent="radiusos_mapper")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        latitudes = []
        longitudes = []

        for address in df['full_address']:
            try:
                location = geocode(address)
                latitudes.append(location.latitude if location else None)
                longitudes.append(location.longitude if location else None)
            except Exception as e:
                latitudes.append(None)
                longitudes.append(None)

        df['lat'] = latitudes
        df['lng'] = longitudes

        df_valid = df.dropna(subset=['lat', 'lng'])

        st.subheader("Search From an Address")
        user_address = st.text_input("Enter an address to search from")
        radius = st.slider("Select radius (miles)", min_value=1, max_value=200, value=50)

        if user_address:
            user_location = geocode(user_address)
            if user_location:
                user_point = (user_location.latitude, user_location.longitude)

                df_valid['distance_miles'] = df_valid.apply(
                    lambda row: geodesic(user_point, (row['lat'], row['lng'])).miles,
                    axis=1
                )

                filtered_df = df_valid[df_valid['distance_miles'] <= radius]

                st.subheader("📍 Matching Facilities Within Radius")
                st.dataframe(filtered_df[['facility_name', 'city', 'state', 'distance_miles']].sort_values(by='distance_miles'))

                if not filtered_df.empty:
                    fmap = folium.Map(location=user_point, zoom_start=8)
                    folium.Marker(
                        location=user_point,
                        icon=folium.Icon(color='blue', icon='search', prefix='fa'),
                        popup="Search Origin"
                    ).add_to(fmap)

                    for _, row in filtered_df.iterrows():
                        folium.Marker(
                            location=[row['lat'], row['lng']],
                            icon=folium.Icon(color='red', icon='map-marker', prefix='fa'),
                            popup=f"{row['facility_name']}<br>{row['city']}, {row['state']}"
                        ).add_to(fmap)

                    folium.Circle(
                        radius=radius * 1609.34,
                        location=user_point,
                        color='blue',
                        fill=True,
                        fill_opacity=0.1
                    ).add_to(fmap)

                    st.subheader("🗺️ Map of Facilities Within Radius")
                    st_folium(fmap, width=900, height=600)
            else:
                st.error("Could not geocode the address you entered. Try something more specific.")
    else:
        st.error("Missing one or more required columns: facility_name, city, state")
