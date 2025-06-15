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

# --- Page Config ---
st.set_page_config(page_title="RadiusOS Facility Mapping", page_icon="📍", layout="wide")
st.markdown("""
    <style>
    body {
        background-color: #F4F4F9;
    }
    .stApp {
        color: #264653;
        font-family: 'Segoe UI', sans-serif;
    }
    .stSlider > div[data-baseweb="slider"] {
        color: #2A9D8F;
    }
    .stButton > button {
        background-color: #2A9D8F;
        color: white;
    }
    a {
        color: #2A9D8F !important;
        text-decoration: none;
        font-weight: bold;
    }
    table td, table th {
        font-size: 16px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

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
st.title("📍 RadiusOS Facility Mapping")
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
    m = folium.Map(location=map_center, zoom_start=8, tiles='CartoDB positron')

    # Add user location pin
    folium.Marker(
        location=search_coords,
        tooltip="Search Location",
        icon=folium.Icon(color="blue", icon="search", prefix="fa")
    ).add_to(m)

    for _, row in filtered_df.iterrows():
        name = row.get("facility_name", "")
        address = row.get("full_address", "")
        website = row["website"] if "website" in row and pd.notna(row["website"]) else "Website not found"
        website_html = f'<a href="{website}" target="_blank">Visit Website</a>' if website != "Website not found" else website

        popup_html = folium.Popup(folium.IFrame(html=f"""
        <div style='white-space: normal; width: 280px;'>
            <b>{name}</b><br>
            {address}<br>
            {website_html}<br>
            {round(row['distance_miles'], 2)} miles away
        </div>
        """, width=300, height=150), max_width=310)

        folium.Marker(
            location=[row['latitude'], row['longitude']],
            tooltip=name,
            popup=popup_html
        ).add_to(m)

    st_data = st_folium(m, width=900, height=600)

    # --- Table of Results ---
    st.subheader("List of Nearby Facilities")
    columns_to_show = [col for col in ["facility_name", "full_address", "distance_miles", "website"] if col in filtered_df.columns]
    if columns_to_show:
        display_df = filtered_df[columns_to_show].copy()
        display_df["website"] = display_df["website"].apply(
            lambda url: f'<a href="{url}" target="_blank">Visit Website</a>'
            if pd.notna(url) and url != "Website not found" else "Website not found"
        )
        st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.warning("Expected columns not found in the dataset.")
