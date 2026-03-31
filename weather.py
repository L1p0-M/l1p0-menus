import requests
import json


class OpenWeatherMap():
    def __init__(self, city, api_key, language):
        self.city = city
        self.api_key = api_key
        self.language = language

    def GetWeatherObject(self, type="weather"):
        if type == "forecast":
            base_url= 'http://api.openweathermap.org/data/2.5/forecast'
        else:
            base_url= 'http://api.openweathermap.org/data/2.5/weather'
            
        params = {
            'q' : self.city,
            'appid' : self.api_key,
            'units' : 'metric',
            'lang' : self.language
        }

        response = requests.get(base_url,params=params)
        self.weather_data = response.json()

        if self.weather_data['cod'] == '404':
            print('Error on getting data')
        if type == "forecast":
            self.weather_object = self.weather_data["list"]
        else:
            self.weather_object = self.weather_data
        return self.weather_object


    def GetWeeklyForecast(self, type="weather"):
        forecast_day = []
        self.forecast = self.GetWeatherObject(type)
        if type == "forecast":
            for i in range(len(self.forecast)):
                self.forecast_main = self.forecast[i]["main"]
                self.forecast_weather = self.forecast[i]["weather"][0]
                self.forecast_wind = self.forecast[i]["wind"]
                self.forecast_date = self.forecast[i]["dt_txt"]
                forecast = self.MakeWeatherObject(type="forecast")
                forecast_day.append(forecast)
        else:
            self.forecast_main = self.forecast["main"]
            self.forecast_weather = self.forecast["weather"][0]
            self.forecast_wind = self.forecast["wind"]
            self.forecast_sunset = self.forecast["sys"]["sunset"]
            self.forecast_sunrise = self.forecast["sys"]["sunrise"]
            self.forecast_country = self.forecast["sys"]["country"]
            self.forecast_timezone = self.forecast["timezone"]
            self.forecast_city = self.forecast["name"]
            forecast = self.MakeWeatherObject()
            forecast["sunset"] = self.forecast_sunset
            forecast["sunrise"] = self.forecast_sunrise
            forecast["country"] = self.forecast_country
            forecast["city"] = self.forecast_city
            forecast["timezone"] = self.forecast_timezone
            forecast_day.append(forecast)
        return forecast_day
    
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
                    icon_name = "weather-clear"
                case "01n":
                    icon_name = "weather-clear-night"
                case "02d":
                    icon_name = "weather-few-clouds"
                case "02n":
                    icon_name = "weather-few-clouds-night"
                case "03d":
                    icon_name = "weather-clouds"
                case "03n":
                    icon_name = "weather-clouds-night"
                case "04n":
                    icon_name = "weather-clouds-night"
                case "04d":
                    icon_name = "weather-clouds"
                case "09d":
                    icon_name = "weather-showers"
                case "09n":
                    icon_name = "weather-showers"
                case "10d":
                    icon_name = "weather-showers"
                case "10n":
                    icon_name = "weather-showers"
                case "11d":
                    icon_name = "weather-storm"
                case "11n":
                    icon_name = "weather-storm"
                case "13d":
                    icon_name = "weather-snow"
                case "13n":
                    icon_name = "weather-snow"
                case "50d":
                    icon_name = "weather-fog"
                case "50n":
                    icon_name = "weather-fog"
                case "*":
                    icon_name = "image-missing"
            return icon_name
        except Exception as e:
            print(f"Unable to get icon! {e}")
            return "image-missing"