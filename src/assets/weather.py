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
        forecast_day = []
        if weathertype == "forecast":
            for i in range(len(data)):
                self.forecast_main = data[i]["main"]
                self.forecast_weather = data[i]["weather"][0]
                self.forecast_wind = data[i]["wind"]
                self.forecast_date = data[i]["dt_txt"]
                forecast = self.MakeWeatherObject(type="forecast")
                forecast_day.append(forecast)
        else:
            self.forecast_main = data["main"]
            self.forecast_weather = data["weather"][0]
            self.forecast_wind = data["wind"]
            self.forecast_sunset = data["sys"]["sunset"]
            self.forecast_sunrise = data["sys"]["sunrise"]
            self.forecast_country = data["sys"]["country"]
            self.forecast_timezone = data["timezone"]
            self.forecast_city = data["name"]
            forecast = self.MakeWeatherObject()
            forecast["sunset"] = self.forecast_sunset
            forecast["sunrise"] = self.forecast_sunrise
            forecast["country"] = self.forecast_country
            forecast["city"] = self.forecast_city
            forecast["timezone"] = self.forecast_timezone
            forecast_day.append(forecast)
        GLib.idle_add(self.callback, weathertype, forecast_day)
    
    def MakeWeatherObject(self, type="weather"):
        forecast_day = {}
        forecast_day["temp"] = self.forecast_main["temp"]
        forecast_day["temp_max"] = self.forecast_main["temp_max"]
        forecast_day["temp_min"] = self.forecast_main["temp_min"]
        forecast_day["feels_like"] = self.forecast_main["feels_like"]
        forecast_day["icon"] = self.forecast_weather["icon"]
        forecast_day["description"] = self.forecast_weather["description"]
        forecast_day["wind_speed"] = self.forecast_wind["speed"]
        forecast_day["wind_degre"] = self.forecast_wind["deg"]
        if type == "forecast":
            forecast_day["date"] = self.forecast_date
        return forecast_day
    
    def matchIcon(self, icon):
        #https://openweathermap.org/weather-conditions
        try:
            match icon:
                case "01d":
                    icon_name = "weather-clear-symbolic"
                case "01n":
                    icon_name = "weather-clear-night-symbolic"
                case "02d":
                    icon_name = "weather-few-clouds-symbolic"
                case "02n":
                    icon_name = "weather-few-clouds-night-symbolic"
                case "03d":
                    icon_name = "weather-overcast-symbolic"
                case "03n":
                    icon_name = "weather-overcast-symbolic"
                case "04n":
                    icon_name = "weather-overcast-symbolic"
                case "04d":
                    icon_name = "weather-overcast-symbolic"
                case "09d":
                    icon_name = "weather-showers-symbolic"
                case "09n":
                    icon_name = "weather-showers-symbolic"
                case "10d":
                    icon_name = "weather-showers-symbolic"
                case "10n":
                    icon_name = "weather-showers-symbolic"
                case "11d":
                    icon_name = "weather-storm-symbolic"
                case "11n":
                    icon_name = "weather-storm-symbolic"
                case "13d":
                    icon_name = "weather-snow-symbolic"
                case "13n":
                    icon_name = "weather-snow-symbolic"
                case "50d":
                    icon_name = "weather-fog-symbolic"
                case "50n":
                    icon_name = "weather-fog-symbolic"
                case "*":
                    icon_name = "image-missing"
            return icon_name
        except Exception as e:
            print(f"Unable to get icon! {e}")
            return "image-missing"