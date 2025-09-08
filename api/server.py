from flask import Flask, request, jsonify
from backend.database import *
from backend.logic import hash_password, assign_truck_auto, straight_line_route
from datetime import datetime, timezone

app = Flask(__name__)

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if get_user(data["username"]):
        return jsonify({"success": False, "error": "Username exists"})
    password_hash = hash_password(data["password"])
    create_user(data["username"], password_hash, data["role"])
    return jsonify({"success": True})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = get_user(data["username"])
    if user and user["password"] == hash_password(data["password"]):
        return jsonify({"success": True, "user": {"username": user["username"], "role": user["role"]}})
    return jsonify({"success": False})

@app.route("/submit_report", methods=["POST"])
def submit_report():
    data = request.json
    report = {
        "user": data["username"],
        "description": data["description"],
        "address": data["address"],
        "location": data["location"],
        "photo_resident": data.get("photo_resident"),
        "photo_collector": None,
        "status": "pending",
        "assigned_truck": None,
        "created_at": datetime.now(timezone.utc),
        "arrival_time": None,
        "route": [],
        "evacuated_time": None
    }
    auto_assign = data.get("auto_assign", False)
    if auto_assign:
        truck = assign_truck_auto(report["location"])
        if truck:
            report["assigned_truck"] = truck["truck_id"]
            report["status"] = "en route"
            report["arrival_time"] = datetime.now(timezone.utc)
            report["route"] = straight_line_route(
                [truck.get('location', {}).get('coordinates', [0,0])[1], truck.get('location', {}).get('coordinates', [0,0])[0]],
                [report["location"]["lat"], report["location"]["lng"]]
            )
    create_report(report)
    return jsonify({"success": True})

# More endpoints for collector/admin/report status/truck assignment...

if __name__ == "__main__":
    app.run(port=5000)