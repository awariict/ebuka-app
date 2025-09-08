from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, ListProperty
import requests
import json

API_URL = "http://localhost:5000"

class ResidentScreen(Screen):
    reports_list = ListProperty([])

    def on_pre_enter(self):
        # Fetch all reports for this resident
        username = self.manager.get_screen("login").ids.username.text
        resp = requests.get(f"{API_URL}/reports_by_user?username={username}")
        if resp.status_code == 200:
            self.reports_list = resp.json().get("reports", [])

    def submit_report(self):
        username = self.manager.get_screen("login").ids.username.text
        description = self.ids.description.text
        address = self.ids.address.text
        lat = float(self.ids.latitude.text)
        lng = float(self.ids.longitude.text)
        photo_path = self.ids.photo.file_path if self.ids.photo.file_path else None

        report = {
            "username": username,
            "description": description,
            "address": address,
            "location": {"lat": lat, "lng": lng},
            "photo_resident": None
        }

        if photo_path:
            with open(photo_path, "rb") as f:
                photo_bytes = f.read()
            report["photo_resident"] = photo_bytes.hex()  # Hex encode for JSON

        resp = requests.post(f"{API_URL}/submit_report", json=report)
        if resp.status_code == 200 and resp.json().get("success"):
            self.ids.status.text = "Report submitted successfully!"
            self.on_pre_enter()
        else:
            self.ids.status.text = "Error submitting report."

    def refresh_reports(self):
        self.on_pre_enter()