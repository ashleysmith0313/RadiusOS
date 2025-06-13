import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

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

        st.subheader("All Uploaded Jobs (Geocoded)")
        st.dataframe(df[['facility_name', 'city', 'state', 'lat', 'lng']])
    else:
        st.error("Missing one or more required columns: facility_name, city, state")
