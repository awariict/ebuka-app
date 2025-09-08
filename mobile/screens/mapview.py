from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty
import requests

API_URL = "http://localhost:5000"

class MapViewScreen(Screen):
    trucks = ListProperty([])
    reports = ListProperty([])

    def on_pre_enter(self):
        trucks_resp = requests.get(f"{API_URL}/trucks")
        reports_resp = requests.get(f"{API_URL}/all_reports")
        if trucks_resp.status_code == 200:
            self.trucks = trucks_resp.json().get("trucks", [])
        if reports_resp.status_code == 200:
            self.reports = reports_resp.json().get("reports", [])
        # You can add logic here to update the map every 10 seconds using Clock.schedule_interval

    # This method would update the map widget, using your actual Kivy MapView implementation.
    def update_map(self):
        pass