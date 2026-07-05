import gi
gi.require_version('Soup', '3.0')
from gi.repository import GLib, Gio, Soup
import urllib.parse
import json

class OpenWeatherMap():
    def __init__(self, city, api_key, language, callback=None):
        self.city = city
        self.api_key = api_key
        self.language = language
        self.callback = callback
        self.icons = {
            "01d": "weather-clear-symbolic",
            "01n": "weather-clear-night-symbolic",
            "02d": "weather-few-clouds-symbolic",
            "02n": "weather-few-clouds-night-symbolic",
            "03d": "weather-overcast-symbolic",
            "03n": "weather-overcast-symbolic",
            "04n": "weather-overcast-symbolic",
            "04d": "weather-overcast-symbolic",
            "09d": "weather-showers-symbolic",
            "09n": "weather-showers-symbolic",
            "10d": "weather-showers-symbolic",
            "10n": "weather-showers-symbolic",
            "11d": "weather-storm-symbolic",
            "11n": "weather-storm-symbolic",
            "13d": "weather-snow-symbolic",
            "13n": "weather-snow-symbolic",
            "50d": "weather-fog-symbolic",
            "50n": "weather-fog-symbolic",
            "missing": "image-missing",
        }

    def GetWeatherObject(self, weathertype="weather"):
        try:
            if weathertype == "forecast":
                base_url= 'http://api.openweathermap.org/data/2.5/forecast'
            else:
                base_url= 'http://api.openweathermap.org/data/2.5/weather'

            if self.city is None or self.api_key is None:
                print("City or API key not set in config!")
                return None
            
            params = {
                'q': self.city,
                'appid': self.api_key,
                'units': 'metric',
                'lang': self.language
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"

            session = Soup.Session()
            message = Soup.Message.new("GET", url)

            session.send_and_read_async(
                message,
                GLib.PRIORITY_DEFAULT,
                None,
                self._on_response_ready,
                weathertype
            )
            return True
        except Exception as e:
            print(f"Unable to get weather data! {e}")
            return None

    def _on_response_ready(self, session, result, weathertype):
        try:
            bytes_data = session.send_and_read_finish(result)
            
            if bytes_data:
                json_str = bytes_data.get_data().decode('utf-8')
                data = json.loads(json_str)
            else:
                GLib.idle_add(self._clear_up_data, weathertype, None)
            if isinstance(data, dict) and int(data.get("cod", 401)) in [400, 401]:
                GLib.idle_add(self._clear_up_data, weathertype, None)
                return
            if weathertype == "forecast":
                GLib.idle_add(self._clear_up_data, "forecast", data["list"])
            else:
                GLib.idle_add(self._clear_up_data, "weather", data)
                
        except Exception as e:
            print(f"Error while processing the response from API: {e}")
            GLib.idle_add(self._clear_up_data, weathertype, None)

    def _clear_up_data(self, weathertype, data):
        if not data:
            GLib.idle_add(self.callback, weathertype, None)
            return
        if weathertype == "forecast":
            forecast_day = []
            props = ["main", "weather", "wind", "dt_txt"]
            for i in range(len(data)):
                data_to_process = {}
                for prop in props:
                    if prop in data[i]:
                        data_to_process[prop] = data[i][prop] if prop != "weather" else data[i][prop][0]
                forecast = self.MakeWeatherObject(type="forecast", data=data_to_process)
                forecast_day.append(forecast)
        else:
            forecast_day = []
            sys_props = ["sunset", "sunrise", "country"]
            props = ["main", "weather", "wind", "sys", "timezone", "name"]
            data_to_process = {}
            for prop in props:
                if prop in data:
                    if prop == "sys":
                        for list_items in sys_props:
                            data_to_process[list_items] = data[prop][list_items]
                    elif prop == "weather":
                        data_to_process[prop] = data[prop][0]
                    else:
                        data_to_process[prop] = data[prop]
            forecast = self.MakeWeatherObject(type="weather", data=data_to_process)
            forecast_day.append(forecast)
        GLib.idle_add(self.callback, weathertype, forecast_day)
    
    def MakeWeatherObject(self, type="weather", data=None):
        forecast_day = {}
        props_main = ["main", "weather", "wind", "dt_txt", "sunrise", "sunset", "country", "timezone", "name"]
        sub_props = {
            "main": ["temp", "temp_max", "temp_min", "feels_like"],
            "weather": ["icon", "description"],
            "wind": ["speed", "deg"],
        }
        if data:
            for prop in props_main:
                if prop in data:
                    if prop in sub_props:
                        for sub_prop in sub_props[prop]:
                            if sub_prop in data[prop]:
                                forecast_prop = sub_prop if prop != "wind" else "wind_" + sub_prop
                                forecast_day[forecast_prop] = data[prop][sub_prop]
                    else:
                        forecast_day[prop] = data[prop]
        return forecast_day
    
    def matchIcon(self, icon):
        #https://openweathermap.org/weather-conditions
        try:
            if icon in self.icons:
                icon_name = self.icons[icon]
            else:
                icon_name = self.icons["missing"]
            return icon_name
        except Exception as e:
            print(f"Unable to get icon! {e}")
            return "image-missing"