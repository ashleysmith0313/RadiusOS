import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import GoogleV3
from geopy.distance import geodesic
import os

# --- Config ---
DATA_FILE = "Geocoded_Hospitals.xlsx"
API_KEY = os.getenv("GOOGLE_API_KEY") or "AIzaSyA-21e_swhPCCSIg1Evg-yltTiGQlaarp4"

# --- Load Data ---
df = pd.read_excel(DATA_FILE)
df.columns = df.columns.str.strip().str.lower()

# --- Clean Data ---
df = df[pd.to_numeric(df['latitude'], errors='coerce').notnull() & pd.to_numeric(df['longitude'], errors='coerce').notnull()]
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

# --- Geocoder ---
geolocator = GoogleV3(api_key=API_KEY, timeout=10)

def geocode_address(address):
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None

# --- UI ---
st.title("RadiusOS Facility Mapping")
st.caption("e.g. 2510 Oasis Dr, Longview, TX 75601")
address_input = st.text_input("Enter an address to search")
radius = st.slider("Select radius (in miles)", 1, 100, 25)

if address_input:
    lat_lon = geocode_address(address_input)
    if not lat_lon or None in lat_lon:
        st.error("Could not geocode that address. Please try another.")
        st.stop()
    search_coords = lat_lon

    # --- Calculate distances ---
    df['distance_miles'] = df.apply(lambda row: geodesic(search_coords, (row['latitude'], row['longitude'])).miles, axis=1)
    filtered_df = df[df['distance_miles'] <= radius].sort_values(by='distance_miles')

    # --- Map ---
    st.subheader("Facilities within radius")
    map_center = search_coords
    m = folium.Map(location=map_center, zoom_start=8)

    for _, row in filtered_df.iterrows():
        name = row.get("facility_name", "")
        address = row.get("full_address", "")
        website = row.get("website", "Website not found")
        website_html = f'<a href="{website}" target="_blank">Visit Website</a>' if website != "Website not found" else website

        popup_html = f"""
        <div style='white-space: normal; width: 250px;'>
            <b>{name}</b><br>
            {address}<br>
            {website_html}<br>
            {round(row['distance_miles'], 2)} miles away
        </div>
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            tooltip=name,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

    st_data = st_folium(m, width=700, height=500)

    # --- Table of Results ---
    st.subheader("List of Nearby Facilities")
    st.dataframe(filtered_df[["facility_name", "full_address", "distance_miles", "website"]].reset_index(drop=True))
