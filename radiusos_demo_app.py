import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
from geopy.geocoders import GoogleV3
import os

# Set your Google API key here or from Streamlit secrets
API_KEY = st.secrets["google_api_key"] if "google_api_key" in st.secrets else os.getenv("GOOGLE_API_KEY")

def geocode_address(address):
    geolocator = GoogleV3(api_key=API_KEY, timeout=10)
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

st.set_page_config(page_title="RadiusOS Facility Mapping", layout="wide")
st.title("📍 RadiusOS Facility Mapping")

# File uploader
uploaded_file = st.file_uploader("Upload your geocoded Excel file", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # Normalize column names to lowercase for consistency
    df.columns = df.columns.str.strip().str.lower()

    # Drop rows with missing coordinates
    df = df.dropna(subset=['latitude', 'longitude'])

    address_input = st.text_input("Enter an address to search")
    radius = st.slider("Select radius (in miles)", min_value=1, max_value=100, value=25)

    if address_input:
        lat, lon = geocode_address(address_input)

        if lat is None or lon is None:
            st.error("Could not geocode the entered address. Please try a different one.")
        else:
            search_coords = (lat, lon)
            filtered_df = df[df.apply(lambda row: geodesic(search_coords, (row['latitude'], row['longitude'])).miles <= radius, axis=1)]

            # Create map
            m = folium.Map(location=search_coords, zoom_start=8)
            folium.Marker(search_coords, tooltip="Search Location", icon=folium.Icon(color='blue')).add_to(m)

            for _, row in filtered_df.iterrows():
                tooltip_text = row.get('facility_name') or row.get('facility name') or "Unknown Facility"
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    tooltip=tooltip_text,
                    icon=folium.Icon(color='red', icon='plus-sign')
                ).add_to(m)

            st_folium(m, width=1000, height=600)

            st.subheader("Facilities within radius")
            st.dataframe(filtered_df)
else:
    st.info("Please upload a geocoded Excel file to begin.")
