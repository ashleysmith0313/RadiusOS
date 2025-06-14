import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.distance import geodesic
from geopy.geocoders import GoogleV3

# --- Config ---
st.set_page_config(page_title="RadiusOS Facility Mapping", layout="wide")
st.title("📍 RadiusOS Facility Mapping")

# --- Load Data ---
@st.cache_data
def load_data():
    return pd.read_excel("Texas Hospitals Geocoded.xlsx")

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Search Parameters")
user_address = st.sidebar.text_input("Enter your address:", "Austin, TX")
radius_miles = st.sidebar.slider("Search Radius (miles)", 10, 200, 50)

# --- Geocode User Address ---
api_key = "AIzaSyA-21e_swhPCCSIg1Evg-yltTiGQlaarp4"  # Replace with your actual API key
geolocator = GoogleV3(api_key=api_key)

try:
    user_location = geolocator.geocode(user_address)
    user_coords = (user_location.latitude, user_location.longitude)
except Exception as e:
    st.error("Failed to geocode the address. Please check your input or API key.")
    st.stop()

# --- Filter Facilities by Radius ---
def calculate_distance(row):
    return geodesic(user_coords, (row['Latitude'], row['Longitude'])).miles

df['Distance'] = df.apply(calculate_distance, axis=1)
df_filtered = df[df['Distance'] <= radius_miles]

# --- Map Setup ---
m = folium.Map(location=user_coords, zoom_start=7)
folium.Marker(
    location=user_coords,
    tooltip="Your Location",
    icon=folium.Icon(color="blue", icon="home")
).add_to(m)

marker_cluster = MarkerCluster().add_to(m)
for _, row in df_filtered.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        tooltip=row['Facility Name'],
        popup=f"{row['Facility Name']}\n{row['City']}, {row['State']}",
        icon=folium.Icon(color="red", icon="plus-sign")
    ).add_to(marker_cluster)

# --- Display Map ---
st_folium(m, width=1200, height=700)

# --- Show Data ---
st.subheader("Facilities in Radius")
st.dataframe(df_filtered[['Facility Name', 'City', 'State', 'Distance']].sort_values(by='Distance'))
