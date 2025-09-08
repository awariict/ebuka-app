from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty
import requests

API_URL = "http://localhost:5000"

class CollectorScreen(Screen):
    open_reports = ListProperty([])

    def on_pre_enter(self):
        resp = requests.get(f"{API_URL}/open_reports")
        if resp.status_code == 200:
            self.open_reports = resp.json().get("reports", [])

    def assign_truck(self, report_id, truck_id):
        data = {"report_id": report_id, "truck_id": truck_id}
        resp = requests.post(f"{API_URL}/assign_truck", json=data)
        if resp.status_code == 200 and resp.json().get("success"):
            self.on_pre_enter()

    def update_report(self, report_id, status, photo_path=None):
        update_data = {"report_id": report_id, "status": status}
        if photo_path:
            with open(photo_path, "rb") as f:
                photo_bytes = f.read()
            update_data["photo_collector"] = photo_bytes.hex()
        resp = requests.post(f"{API_URL}/update_report", json=update_data)
        if resp.status_code == 200 and resp.json().get("success"):
            self.on_pre_enter()