import folium
from streamlit_folium import st_folium

def show_map():
    """
    Displays a map showing all trucks and all complaints.
    - Green marker: Resident complaint (with description/status popup)
    - Blue marker: Truck (with truck_id popup)
    - Blue line: Route (if available)
    """
    import streamlit as st
    from pymongo import MongoClient

    MONGO_URI = "mongodb+srv://euawari_db_user:6SnKvQvXXzrGeypA@cluster0.fkkzcvz.mongodb.net/waste_db?retryWrites=true&w=majority"
    client = MongoClient(MONGO_URI)
    db = client["waste_db"]
    

    st.subheader("Map View: All Trucks and Resident Complaints")

    m = folium.Map(location=[5.53, 7.48], zoom_start=12)

    # Plot all complaints
    for r in db.reports.find({}):
        loc = r.get("location")
        if loc and "lat" in loc and "lng" in loc:
            status = r.get('status','N/A')
            color = "red" if status=="pending" else "green"
            folium.Marker(
                [loc["lat"], loc["lng"]],
                popup=f"{r.get('description','No description')} | Status: {status}",
                icon=folium.Icon(color=color)
            ).add_to(m)
        # Draw route if available
        route = r.get("route", [])
        if route and isinstance(route, list) and len(route) > 1:
            folium.PolyLine(route, color="blue", weight=3, opacity=0.7).add_to(m)

    # Plot all trucks
    for t in db.trucks.find({}):
        loc = t.get("location", {})
        coords = loc.get("coordinates", [])
        if len(coords) == 2:
            t_lat, t_lng = coords[1], coords[0]
            folium.Marker(
                [t_lat, t_lng],
                popup=f"{t.get('truck_id','')} | Last update: {t.get('last_update','N/A')}",
                icon=folium.Icon(color="blue")
            ).add_to(m)

    st_folium(m, width=700, height=500)
