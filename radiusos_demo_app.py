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

    # Drop exact duplicate columns (not just names)
    df = df.loc[:, ~df.columns.duplicated()]

    st.write("Detected columns:", df.columns.tolist())

    # Only proceed if required columns exist and are Series
    if isinstance(df.get('latitude'), pd.Series) and isinstance(df.get('longitude'), pd.Series):
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])

        address_input = st.text_input("Enter an address to search")
        radius = st.slider("Select radius (in miles)", min_value=1, max_value=100, value=25)

        if address_input:
            lat, lon = geocode_address(address_input)

            if lat is None or lon is None:
                st.error("Could not geocode the entered address. Please try a different one.")
            else:
                search_coords = (lat, lon)

                def get_distance(row):
                    try:
                        return geodesic(search_coords, (float(row['latitude']), float(row['longitude']))).miles
                    except Exception:
                        return float('inf')

                df['distance_miles'] = df.apply(lambda row: get_distance(row), axis=1)
                filtered_df = df[df['distance_miles'] <= radius].copy()
                filtered_df = filtered_df.sort_values(by='distance_miles')

                # Create map
                m = folium.Map(location=search_coords, zoom_start=8)
                folium.Marker(search_coords, tooltip="Search Location", icon=folium.Icon(color='blue')).add_to(m)

                for _, row in filtered_df.iterrows():
                    tooltip_text = f"{row.get('facility_name') or row.get('facility name', 'Unknown Facility')}\n{row.get('full_address', 'No address')}"
                    folium.Marker(
                        location=[row['latitude'], row['longitude']],
                        tooltip=tooltip_text,
                        icon=folium.Icon(color='red', icon='plus-sign')
                    ).add_to(m)

                st_folium(m, width=1000, height=600)

                st.subheader("Facilities within radius")
                display_df = filtered_df[[
                    row for row in ['facility_name', 'facility name', 'full_address', 'city', 'state', 'distance_miles'] if row in filtered_df.columns
                ]].copy()
                display_df.columns = [
                    'Facility Name' if col in ['facility_name', 'facility name'] else
                    'Address' if col == 'full_address' else
                    'City' if col == 'city' else
                    'State' if col == 'state' else
                    'Distance (miles)' for col in display_df.columns
                ]

                st.dataframe(display_df, use_container_width=True)
    else:
        st.error("The uploaded file does not contain valid 'latitude' and 'longitude' columns.")
else:
    st.info("Please upload a geocoded Excel file to begin.")
