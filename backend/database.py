from pymongo import MongoClient
from backend.config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_user(username):
    return db.users.find_one({"username": username})

def create_user(username, password_hash, role):
    db.users.insert_one({"username": username, "password": password_hash, "role": role})

def get_trucks():
    return list(db.trucks.find())

def create_truck(truck_id, location):
    db.trucks.insert_one({"truck_id": truck_id, "location": location})

def get_reports_by_user(username):
    return list(db.reports.find({"user": username}))

def create_report(report):
    db.reports.insert_one(report)

def get_all_reports():
    return list(db.reports.find())

def update_report(report_id, updates):
    db.reports.update_one({"_id": report_id}, {"$set": updates})

def get_report(report_id):
    return db.reports.find_one({"_id": report_id})

def delete_user(username):
    db.users.delete_one({"username": username})