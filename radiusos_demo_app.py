import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pydeck as pdk

st.set_page_config(page_title="RadiusOS Demo", layout="wide")
st.title("📍 RadiusOS Facility Mapping Demo")

# Step 1: Upload file
uploaded_file = st.sidebar.file_uploader("Upload Job File", type=["csv", "xlsx"])

# Step 2: User input for address & radius
user_address = st.sidebar.text_input("Search Address (City, State, or Full Address)")
radius_miles = st.sidebar.slider("Radius (miles)", 10, 100, 25)

# Geocoder setup
geolocator = Nominatim(user_agent="radiusos_demo")

def geocode_address(text):
    try:
        loc = geolocator.geocode(text)
        return (loc.latitude, loc.longitude)
    except:
        return None

def geocode_facility(row):
    address = f"{row['facility_name']}, {row['city']}, {row['state']}"
    try:
        loc = geolocator.geocode(address)
        return pd.Series([loc.latitude, loc.longitude]) if loc else pd.Series([None, None])
    except:
        return pd.Series([None, None])

# Step 3: Process job list
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df[["lat", "lng"]] = df.apply(geocode_facility, axis=1)

    st.subheader("All Uploaded Jobs (Geocoded)")
    st.dataframe(df)

    # Step 4: Filter by address radius
    if user_address:
        center = geocode_address(user_address)
        if center:
            df["distance_miles"] = df.apply(lambda row: geodesic(center, (row["lat"], row["lng"])).miles if pd.notnull(row["lat"]) else None, axis=1)
            filtered_df = df[df["distance_miles"] <= radius_miles]
            
            st.subheader(f"Jobs within {radius_miles} miles of {user_address}")
            st.dataframe(filtered_df)

            # Step 5: Map
            st.pydeck_chart(pdk.Deck(
                map_style='mapbox://styles/mapbox/light-v9',
                initial_view_state=pdk.ViewState(
                    latitude=center[0],
                    longitude=center[1],
                    zoom=6,
                    pitch=50,
                ),
                layers=[
                    pdk.Layer(
                        'ScatterplotLayer',
                        data=filtered_df,
                        get_position='[lng, lat]',
                        get_color='[200, 30, 0, 160]',
                        get_radius=30000,
                    ),
                    pdk.Layer(
                        'ScatterplotLayer',
                        data=pd.DataFrame([{"lat": center[0], "lng": center[1]}]),
                        get_position='[lng, lat]',
                        get_color='[0, 100, 255, 200]',
                        get_radius=5000,
                    ),
                ],
            ))

            # Step 6: Download filtered list
            st.download_button("Download Filtered Jobs", data=filtered_df.to_csv(index=False), file_name="filtered_jobs.csv", mime="text/csv")

        else:
            st.error("Could not geocode address. Try a full city/state or street.")
