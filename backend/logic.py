import hashlib
from datetime import datetime, timezone
from backend.database import get_trucks

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def assign_truck_auto(report_location):
    trucks = get_trucks()
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

def straight_line_route(start, end):
    return [start, end]

def on_time_status(report):
    if report.get("status") == "evacuated":
        created = report.get("created_at")
        evacuated_time = report.get("evacuated_time")
        if created and evacuated_time:
            delta = evacuated_time - created
            hours = delta.total_seconds() / 3600
            return "On Time" if hours <= 24 else "Late"
    return "Not yet evacuated"