import random
from pymongo import MongoClient

NUM_TRUCKS = 10
client = MongoClient("mongodb://localhost:27017")
db = client["waste_db"]

trucks = [
    {
        "truck_id": f"TRUCK{i+1}",
        "location": {"coordinates": [7.4 + random.random()*0.1, 5.5 + random.random()*0.1]}
    }
    for i in range(NUM_TRUCKS)
]

db.trucks.delete_many({})  # Clean old trucks
db.trucks.insert_many(trucks)
print("10 trucks inserted!")