from pymongo import MongoClient
from datetime import datetime, timedelta, UTC
import random

MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client["waste_db"]

# Clear old data
db.reports.delete_many({})
db.trucks.delete_many({})

# Sample trucks
trucks = [
    {"truck_id": "TRUCK-001", "location": {"type": "Point", "coordinates": [7.48, 5.53]}, "last_update": datetime.now(UTC)},
    {"truck_id": "TRUCK-002", "location": {"type": "Point", "coordinates": [7.50, 5.54]}, "last_update": datetime.now(UTC)},
]
db.trucks.insert_many(trucks)

# Sample reports
descriptions = [
    "Overflowing bin at Aba Road",
    "Illegal dumpsite near Ariaria",
    "Missed collection at Umuahia",
    "Spillage at Ikot Ekpene Road",
    "Blocked drainage at Ossah",
]

for i in range(10):
    created = datetime.now(UTC) - timedelta(hours=random.randint(1, 48))
    status = random.choice(["open", "closed"])
    report = {
        "description": random.choice(descriptions),
        "status": status,
        "created_at": created,
        "location": {
            "type": "Point",
            "coordinates": [7.47 + random.uniform(-0.02, 0.02), 5.52 + random.uniform(-0.02, 0.02)]
        }
    }
    if status == "closed":
        assigned_time = created + timedelta(hours=random.randint(1, 3))
        closed_time = assigned_time + timedelta(hours=random.randint(1, 4))
        report.update({
            "assigned_truck": random.choice(["TRUCK-001", "TRUCK-002"]),
            "assigned_at": assigned_time,
            "closed_at": closed_time,
            "satisfaction": random.randint(2, 5)
        })
    db.reports.insert_one(report)

print("✅ Seed data inserted into MongoDB (timezone-aware)")
