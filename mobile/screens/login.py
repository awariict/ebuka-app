from kivy.uix.screenmanager import Screen
import requests

API_URL = "http://localhost:5000"

class LoginScreen(Screen):
    def do_login(self, username, password):
        resp = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        data = resp.json()
        if data.get("success"):
            role = data["user"]["role"]
            if role == "resident":
                self.manager.current = "resident"
            elif role == "collector":
                self.manager.current = "collector"
            elif role == "admin":
                self.manager.current = "admin"
        else:
            self.ids.login_status.text = "Login failed"