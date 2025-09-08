from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from mobile.screens.login import LoginScreen
from mobile.screens.resident import ResidentScreen
from mobile.screens.collector import CollectorScreen
from mobile.screens.admin import AdminScreen
from mobile.screens.mapview import MapViewScreen

class WasteScreenManager(ScreenManager):
    pass

class WasteApp(App):
    def build(self):
        Builder.load_file("kv/theme.kv")
        sm = WasteScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(ResidentScreen(name="resident"))
        sm.add_widget(CollectorScreen(name="collector"))
        sm.add_widget(AdminScreen(name="admin"))
        sm.add_widget(MapViewScreen(name="mapview"))
        return sm

if __name__ == "__main__":
    WasteApp().run()