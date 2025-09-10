import streamlit as st
from pymongo import MongoClient
import hashlib
from datetime import datetime, timezone
import folium
from streamlit_folium import st_folium
import pandas as pd
from bson import ObjectId

from map_function import show_map   # <--- Import your map function

# ----------------------------
# DATABASE CONNECTION (SAFE)
# ----------------------------
from pymongo import MongoClient
import streamlit as st

MONGO_URI = "mongodb+srv://euawari_db_user:6SnKvQvXXzrGeypA@cluster0.fkkzcvz.mongodb.net/waste_db?retryWrites=true&w=majority"

try:
    # Set a 5-second timeout so it won’t hang forever
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")   # Force a connection check
    db = client["waste_db"]
    st.sidebar.success("✅ MongoDB connected successfully!")
except Exception as e:
    st.sidebar.error(f"❌ Database connection failed: {e}")
    st.stop()  # Stop app if DB is not reachable



# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    return db.users.find_one({"username": username, "password": hash_password(password)})

def register_user(username, password, role):
    if db.users.find_one({"username": username}):
        return False
    db.users.insert_one({"username": username, "password": hash_password(password), "role": role})
    return True

def get_trucks():
    return list(db.trucks.find({}))

def get_truck_by_id(truck_id):
    return db.trucks.find_one({"truck_id": truck_id})

def straight_line_route(start, end):
    # For demonstration: just return [start, end] as the route
    return [start, end]

def find_nearest_truck(report_location):
    trucks = get_trucks()
    if not trucks or not report_location:
        return None
    min_dist = float("inf")
    nearest = None
    for t in trucks:
        coords = t.get("location", {}).get("coordinates", [0,0])
        if len(coords) == 2:
            t_lat, t_lng = coords[1], coords[0]
            dist = ((t_lat - report_location["lat"])**2 + (t_lng - report_location["lng"])**2)**0.5
            if dist < min_dist:
                min_dist = dist
                nearest = t
    return nearest

def get_on_time_status(report):
    # "On time" = evacuated within 24 hours of creation for demo purposes
    if report.get("status") == "evacuated":
        created = report.get("created_at")
        evacuated_time = report.get("evacuated_time")
        if created and evacuated_time:
            delta = evacuated_time - created
            hours = delta.total_seconds() / 3600
            return "On Time" if hours <= 24 else "Late"
    elif report.get("status") == "evacuated":
        return "Unknown (missing timestamps)"
    return "Not yet evacuated"

# ----------------------------
# SESSION STATE
# ----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# ----------------------------
# APP STYLE
# ----------------------------
st.set_page_config(page_title="Ebuka Waste Management", layout="wide")
st.markdown("""
<style>
body { background-color: #e6f0ff; color: #000000; }
.sidebar .sidebar-content { background-color: #cce0ff; }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# DASHBOARD FUNCTION
# ----------------------------
def show_dashboard(user):
    st.sidebar.write(f"Logged in as: {user['username']} ({user['role']})")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # RESIDENT DASHBOARD
    if user["role"] == "resident":
        st.title("Resident Dashboard")
        st.subheader("Submit a Waste Report")

        desc = st.text_area("Description of the issue")
        address = st.text_input("Address")
        st.markdown("**Provide your location:**")
        lat = st.number_input("Your Latitude", value=5.53, format="%.6f")
        lng = st.number_input("Your Longitude", value=7.48, format="%.6f")
        photo_file = st.file_uploader("Upload Photo", type=["png","jpg","jpeg"], key="resident_photo")
        if st.button("Submit Report"):
            if desc and address and photo_file:
                report = {
                    "user": user["username"],
                    "description": desc,
                    "address": address,
                    "location": {"lat": lat, "lng": lng},
                    "photo_resident": photo_file.read(),
                    "photo_collector": None,
                    "status": "pending",
                    "assigned_truck": None,
                    "created_at": datetime.now(timezone.utc),
                    "arrival_time": None,
                    "route": [],
                    "evacuated_time": None
                }
                auto_assign_setting = db.settings.find_one({"key": "auto_assign"})
                if auto_assign_setting and auto_assign_setting.get("value") == True:
                    nearest_truck = find_nearest_truck(report["location"])
                    if nearest_truck:
                        arrival_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                        route = straight_line_route(
                            [nearest_truck.get('location', {}).get('coordinates', [0,0])[1], nearest_truck.get('location', {}).get('coordinates', [0,0])[0]],
                            [lat, lng]
                        )
                        report["assigned_truck"] = nearest_truck["truck_id"]
                        report["status"] = "en route"
                        report["arrival_time"] = arrival_time
                        report["route"] = route
                db.reports.insert_one(report)
                st.success("Report submitted successfully!")

        st.sidebar.subheader("My Submitted Reports")
        my_reports = list(db.reports.find({"user": user["username"]}).sort("created_at", -1))
        for r in my_reports:
            st.sidebar.markdown(f"- {r.get('description','N/A')} ({r.get('status','N/A')})")

        st.subheader("My Reports")
        for r in my_reports:
            st.markdown(f"**Description:** {r.get('description', 'N/A')}")
            st.markdown(f"**Address:** {r.get('address', 'N/A')}")
            st.markdown(f"**Status:** {r.get('status', 'N/A')}")
            st.markdown(f"**Assigned Truck:** {r.get('assigned_truck','Not assigned')}")
            arrival_time = r.get("arrival_time")
            if arrival_time:
                st.markdown(f"**Truck Arrival Time:** {arrival_time}")
            else:
                st.markdown("**Truck Arrival Time:** Not yet assigned")
            route = r.get("route", [])
            if route and isinstance(route, list) and len(route) > 1:
                st.markdown("**Truck Route:**")
                st.write(route)
            if r.get("photo_resident") not in [None, b'', '']:
                st.image(r["photo_resident"], caption="Resident Photo", use_container_width=True)
            if r.get("photo_collector") not in [None, b'', '']:
                st.image(r["photo_collector"], caption="Collector Photo", use_container_width=True)
            st.markdown("---")

        st.subheader("Map of My Reports & Truck Routes")
        m = folium.Map(location=[lat,lng], zoom_start=12)
        for r in my_reports:
            loc = r.get("location")
            if loc and isinstance(loc, dict) and "lat" in loc and "lng" in loc:
                folium.Marker(
                    [loc["lat"], loc["lng"]],
                    popup=f"{r.get('description','No description')} | Status: {r.get('status','N/A')}",
                    icon=folium.Icon(color="red" if r.get('status')=="pending" else "green")
                ).add_to(m)
            route = r.get("route", [])
            if route and isinstance(route, list) and len(route) > 1:
                folium.PolyLine(route, color="blue", weight=3, opacity=0.7).add_to(m)
        trucks = db.trucks.find({})
        for t in trucks:
            loc = t.get("location", {})
            coords = loc.get("coordinates", [])
            if len(coords) == 2:
                t_lat, t_lng = coords[1], coords[0]
                folium.Marker(
                    [t_lat, t_lng],
                    popup=f"{t.get('truck_id','')} | Last update: {t.get('last_update','N/A')}",
                    icon=folium.Icon(color="blue")
                ).add_to(m)
        st_folium(m, width=700, height=400)

    # COLLECTOR DASHBOARD
    elif user["role"] == "collector":
        st.title("Collector Dashboard")
        st.subheader("Complaints To Evacuate")
        open_reports = list(db.reports.find({"status": {"$in":["pending","en route","ongoing"]}}))
        trucks = get_trucks()
        for r in open_reports:
            st.markdown(f"**Resident:** {r.get('user', 'N/A')}")
            st.markdown(f"**Description:** {r.get('description', 'N/A')}")
            st.markdown(f"**Address:** {r.get('address', 'N/A')}")
            loc = r.get("location")
            if loc:
                st.markdown(f"**Location:** lat={loc.get('lat','N/A')}, lng={loc.get('lng','N/A')}")
            if r.get("photo_resident") not in [None, b'', '']:
                st.image(r["photo_resident"], caption="Resident Photo", use_container_width=True)
            assigned_truck = r.get("assigned_truck")
            if assigned_truck:
                st.markdown(f"**Assigned Truck:** {assigned_truck}")
            else:
                truck_options = {f"{t.get('truck_id','No ID')}": t for t in trucks}
                if truck_options:
                    selected_truck_key = st.selectbox(
                        f"Select Truck for complaint '{r.get('description','N/A')}'",
                        list(truck_options.keys()),
                        key=f"collector_assign_truck_{str(r['_id'])}"
                    )
                    if st.button(f"Assign Truck to '{r.get('description','N/A')}'", key=f"collector_assign_btn_{str(r['_id'])}"):
                        truck = truck_options[selected_truck_key]
                        route = straight_line_route(
                            [truck.get('location', {}).get('coordinates', [0,0])[1], truck.get('location', {}).get('coordinates', [0,0])[0]],
                            [loc.get('lat',0), loc.get('lng',0)]
                        )
                        arrival_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                        db.reports.update_one(
                            {"_id": r["_id"]},
                            {"$set": {
                                "assigned_truck": truck["truck_id"],
                                "status": "en route",
                                "arrival_time": arrival_time,
                                "route": route
                            }}
                        )
                        st.success(f"Truck {truck['truck_id']} assigned!")
                        st.rerun()
            status = st.selectbox(
                f"Update Status for '{r.get('description','N/A')}'",
                ["pending", "en route", "ongoing", "awaiting confirmation", "evacuated"],
                index=["pending", "en route", "ongoing", "awaiting confirmation", "evacuated"].index(r.get("status", "pending")),
                key=f"collector_status_{str(r['_id'])}"
            )
            photo_file = st.file_uploader(
                f"Upload Collector Photo for '{r.get('description','N/A')}'",
                type=["png", "jpg", "jpeg"],
                key=f"collector_photo_{str(r['_id'])}"
            )
            if st.button(f"Update Complaint for '{r.get('description','N/A')}'", key=f"collector_update_{str(r['_id'])}"):
                update_data = {"status": status}
                if photo_file:
                    update_data["photo_collector"] = photo_file.read()
                if status == "evacuated":
                    update_data["evacuated_time"] = datetime.now(timezone.utc)
                db.reports.update_one({"_id": r["_id"]}, {"$set": update_data})
                st.success("Updated!")
                st.rerun()
            st.markdown("---")

        st.subheader("Truck Locations & Routes")
        m = folium.Map(location=[5.53,7.48], zoom_start=12)
        for t in trucks:
            loc = t.get("location", {})
            coords = loc.get("coordinates", [])
            if len(coords) == 2:
                lat, lng = coords[1], coords[0]
                folium.Marker(
                    [lat, lng],
                    popup=f"{t.get('truck_id','')} | Last update: {t.get('last_update','N/A')}",
                    icon=folium.Icon(color="blue")
                ).add_to(m)
        assigned_reports = list(db.reports.find({"assigned_truck": {"$ne": None}}))
        for r in assigned_reports:
            route = r.get("route", [])
            if route and isinstance(route, list) and len(route) > 1:
                folium.PolyLine(route, color="purple", weight=3, opacity=0.8).add_to(m)
        st_folium(m, width=700, height=400)

    # ADMIN DASHBOARD
    elif user["role"] == "admin":
        st.title("Admin Dashboard")
        menu = [
            "Users Management",
            "View Complaints",
            "Map View",
            "Assignments",
            "Analytics",
            "Settings"
        ]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Users Management":
            # ... unchanged code ...
            users_list = list(db.users.find())
            for u in users_list:
                st.write(f"{u['username']} | Role: {u['role']}")
                with st.expander(f"Edit {u['username']}", expanded=False):
                    new_username = st.text_input(f"New username for {u['username']}", value=u['username'], key=f"edit_username_{u['_id']}")
                    new_password = st.text_input(f"New password for {u['username']}", type="password", key=f"edit_password_{u['_id']}")
                    if st.button(f"Update credentials for {u['username']}", key=f"update_creds_{u['_id']}"):
                        update_fields = {"username": new_username}
                        if new_password:
                            update_fields["password"] = hash_password(new_password)
                        db.users.update_one({"_id": u["_id"]}, {"$set": update_fields})
                        st.success("Updated credentials")
                        st.rerun()
                if st.button(f"Delete {u['username']}", key=f"delete_{str(u['_id'])}"):
                    db.users.delete_one({"_id": u["_id"]})
                    st.success("Deleted")
                    st.rerun()

            st.subheader("Add New User (Contractor or Resident)")
            new_user_username = st.text_input("Username for new user", key="new_user_username")
            new_user_password = st.text_input("Password for new user", type="password", key="new_user_password")
            new_user_role = st.selectbox("Role for new user", ["resident", "collector"], key="new_user_role")
            if st.button("Add User", key="add_user_btn"):
                if new_user_username and new_user_password:
                    if db.users.find_one({"username": new_user_username}):
                        st.error("Username already exists.")
                    else:
                        db.users.insert_one({
                            "username": new_user_username,
                            "password": hash_password(new_user_password),
                            "role": new_user_role
                        })
                        st.success(f"Added new {new_user_role}: {new_user_username}")
                        st.rerun()
                else:
                    st.warning("Please enter both username and password.")

        elif choice == "View Complaints":
            reports = list(db.reports.find())
            for r in reports:
                st.markdown(f"**Resident:** {r.get('user', 'N/A')}")
                st.markdown(f"**Description:** {r.get('description', 'N/A')}")
                st.markdown(f"**Address:** {r.get('address', 'N/A')}")
                st.markdown(f"**Status:** {r.get('status', 'N/A')}")
                st.markdown(f"**Assigned Truck:** {r.get('assigned_truck','Not assigned')}")
                if r.get("photo_resident") not in [None, b'', '']:
                    st.image(r["photo_resident"], caption="Resident Photo", use_column_width=True)
                if r.get("photo_collector") not in [None, b'', '']:
                    st.image(r["photo_collector"], caption="Collector Photo", use_column_width=True)
                st.markdown(f"**On-Time Status:** {get_on_time_status(r)}")
                st.markdown("---")

        elif choice == "Map View":
            show_map()

        elif choice == "Assignments":
            open_reports = list(db.reports.find({"status":"pending"}))
            trucks = get_trucks()
            if open_reports and trucks:
                st.write("Pending Complaints:")
                for r in open_reports:
                    st.markdown(f"- **ID:** {r['_id']}, **Resident:** {r.get('user','N/A')}, **Desc:** {r.get('description','N/A')}, **Address:** {r.get('address','N/A')}")
                report_options = {f"{r.get('description','No description')} @ {r.get('address','No address')} (ID:{r['_id']})": r for r in open_reports}
                truck_options = {f"{t.get('truck_id','No ID')}": t for t in trucks}
                selected_report_key = st.selectbox("Select Report", list(report_options.keys()), key="assign_report")
                selected_truck_key = st.selectbox("Select Truck", list(truck_options.keys()), key="assign_truck")
                if st.button("Assign Truck"):
                    report = report_options[selected_report_key]
                    truck = truck_options[selected_truck_key]
                    arrival_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    route = straight_line_route(
                        [truck.get('location', {}).get('coordinates', [0,0])[1], truck.get('location', {}).get('coordinates', [0,0])[0]],
                        [report.get('location', {}).get('lat', 0), report.get('location', {}).get('lng', 0)]
                    )
                    db.reports.update_one(
                        {"_id":report["_id"]},
                        {"$set":{
                            "assigned_truck":truck["truck_id"],
                            "status":"en route",
                            "arrival_time": arrival_time,
                            "route": route
                        }}
                    )
                    st.success(f"Truck {truck['truck_id']} assigned to complaint '{report['description']}'")
                    st.rerun()
                st.subheader("Current Assignments")
                assigned_reports = list(db.reports.find({"assigned_truck": {"$ne": None}}))
                for ar in assigned_reports:
                    st.markdown(f"- {ar.get('description','No description')} @ {ar.get('address','No address')} → Assigned Truck: {ar.get('assigned_truck','N/A')} (Status: {ar.get('status','N/A')})")
            else:
                st.info("No pending complaints or no registered trucks to assign.")

        elif choice == "Analytics":
            reports = list(db.reports.find({}))
            if reports:
                df = pd.DataFrame(reports)
                st.metric("Total Complaints", len(df))
                st.metric("Closed", len(df[df["status"]=="evacuated"]))
                st.metric("Open", len(df[df["status"]!="evacuated"]))
                on_time = 0
                late = 0
                for r in reports:
                    ot = get_on_time_status(r)
                    if ot == "On Time":
                        on_time += 1
                    elif ot == "Late":
                        late += 1
                st.metric("Evacuated On Time", on_time)
                st.metric("Evacuated Late", late)

        elif choice == "Settings":
            auto_assign_setting = db.settings.find_one({"key": "auto_assign"})
            auto_assign = auto_assign_setting["value"] if auto_assign_setting else False
            auto_assign_new = st.checkbox("Auto-Assign Truck in Real Time as Complaints are Made", value=auto_assign)
            if st.button("Save Settings"):
                db.settings.update_one({"key": "auto_assign"}, {"$set": {"value": auto_assign_new}}, upsert=True)
                st.success("Settings updated.")
                st.rerun()

# ----------------------------
# MAIN APP
# ----------------------------
def show_login():
    st.title("Ebuka Waste Management Login/Register")
    option = st.radio("Choose action", ["Login", "Register"])
    if option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        username = st.text_input("Choose Username")
        password = st.text_input("Choose Password", type="password")
        role = st.selectbox("Role", ["resident","collector","admin"])
        if st.button("Register"):
            if register_user(username, password, role):
                st.success("Registered! Please login.")
            else:
                st.error("Username already exists.")

if st.session_state.user is None:
    show_login()
else:
    show_dashboard(st.session_state.user)
