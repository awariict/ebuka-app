from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty
import requests

API_URL = "http://localhost:5000"

class AdminScreen(Screen):
    users_list = ListProperty([])
    all_reports = ListProperty([])

    def on_pre_enter(self):
        # Get all users and reports for admin
        users_resp = requests.get(f"{API_URL}/all_users")
        reports_resp = requests.get(f"{API_URL}/all_reports")
        if users_resp.status_code == 200:
            self.users_list = users_resp.json().get("users", [])
        if reports_resp.status_code == 200:
            self.all_reports = reports_resp.json().get("reports", [])

    def add_user(self, username, password, role):
        resp = requests.post(f"{API_URL}/register", json={
            "username": username,
            "password": password,
            "role": role
        })
        if resp.status_code == 200 and resp.json().get("success"):
            self.on_pre_enter()

    def remove_user(self, username):
        resp = requests.post(f"{API_URL}/remove_user", json={"username": username})
        if resp.status_code == 200 and resp.json().get("success"):
            self.on_pre_enter()