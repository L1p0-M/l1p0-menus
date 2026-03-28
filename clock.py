import gi
import time
import datetime
import weather


gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib
_v_layer = None


class CalendarLayer(Gtk.Window):
    def __init__(self, config=None):
        super().__init__(title="Calendar Layer")
        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_namespace(self, "calendar-layer")
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.TOP)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.TOP, 10)
        self.set_default_size(300, 150)
        self.get_style_context().add_class("calendar-window")
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_container.set_margin_start(0)
        self.main_container.get_style_context().add_class("calendar-layer")
        self.set_child(self.main_container)
        self.horizontal_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.horizontal_container.set_homogeneous(True)
        self.main_container.append(self.horizontal_container)
        self.setup_time()
        if config is not None:
            try:
                api_key = config["api_key"]
                language = config["language"]
                city = config["city"]
                self.weather = weather.OpenWeatherMap(city, api_key, language,)
                self.setup_weather()
                self.set_default_size(600, 150)
            except Exception as e:
                print(f"Missing variable from config: {e}")
        self.StartUpdateLoop()


    def StartUpdateLoop(self):
        GLib.timeout_add(1000, self.update_clock)
        #GLib.timeout_add(3600, self.update_weather)

    def setup_time(self):
        self.time_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.horizontal_container.append(self.time_container)
        self.clock = Gtk.Label()
        self.clock.set_label(time.strftime(str("%H:%M") ))
        self.clock.get_style_context().add_class("clock")
        self.clock.set_hexpand(True)
        self.time_container.append(self.clock)

        self.date = Gtk.Label()
        self.date.set_label(time.strftime(str("%Y-%m-%d") ))
        self.date.get_style_context().add_class("date")
        self.date.set_hexpand(True)
        self.time_container.append(self.date)

        self.calendar = Gtk.Calendar()
        self.calendar.set_size_request(200, -1)
        self.calendar.set_property("show-week-numbers", False)
        self.calendar.connect("next-month", self.markKurzeWoche)
        self.calendar.connect("prev-month", self.markKurzeWoche)
        self.calendar.connect("next-year", self.markKurzeWoche)
        self.calendar.connect("prev-year", self.markKurzeWoche)
        self.calendar.get_style_context().add_class("calendar")
        self.resetToCurrentDate()
        self.markKurzeWoche()
        self.calendar.set_hexpand(True)
        self.time_container.append(self.calendar)



    def setup_weather(self):
        weather_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, 
            margin_start=20,
            margin_end=20,
            margin_top=40,
            margin_bottom=20,)
        self.horizontal_container.append(weather_container)
        current_weather = self.weather.GetWeeklyForecast(type="weather")[0]
        self.current_weather_icon = Gtk.Image.new_from_icon_name(self.weather.matchIcon(current_weather["icon"]))
        self.current_weather_icon.get_style_context().add_class("weather-icon")
        weather_container.append(self.current_weather_icon)
        temp_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        weather_container.append(temp_container)
        self.current_weather_desc = Gtk.Label()
        self.current_weather_desc.get_style_context().add_class("weather-description")
        self.current_weather_desc.set_label(f"{current_weather["description"].upper()}")
        self.current_weather_temp = Gtk.Label()
        self.current_weather_temp.get_style_context().add_class("weather-temp")
        self.current_weather_temp.set_label(f"{int(current_weather["temp"])}°")
        self.current_weather_feel = Gtk.Label()
        self.current_weather_feel.get_style_context().add_class("weather-feel")
        self.current_weather_feel.set_label(f"{int(current_weather["feels_like"])}°")
        self.current_weather_wind = Gtk.Label()
        self.current_weather_wind.set_label(f"{int(current_weather["wind_speed"])}km/h")
        self.current_weather_temp.set_hexpand(True)
        self.current_weather_feel.set_hexpand(True)
        self.current_weather_desc.set_hexpand(True)
        self.current_weather_temp.set_halign(Gtk.Align.END)
        self.current_weather_feel.set_halign(Gtk.Align.START)
        self.current_weather_desc.set_halign(Gtk.Align.CENTER)
        temp_container.append(self.current_weather_temp)
        temp_container.append(self.current_weather_feel)
        weather_container.append(self.current_weather_desc)
        self.upcoming_weather_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.upcoming_weather_container.get_style_context().add_class("upcoming-container")
        weather_container.append(self.upcoming_weather_container)
        self.setup_forecast()

    #def set_weather_values(self):
     #   current_weather = self.weather.GetWeeklyForecast(type="weather")[0]
      #  self.current_weather_icon = Gtk.Image.new_from_icon_name(self.weather.matchIcon(current_weather["icon"]))
       # self.current_weather_desc.set_label(f"{current_weather["description"].upper()}")
        #self.current_weather_temp.set_label(f"{int(current_weather["temp"])}°")
        #self.current_weather_feel.set_label(f"{int(current_weather["feels_like"])}°")
        #self.current_weather_wind.set_label(f"{int(current_weather["wind_speed"])}km/h")

    def setup_forecast(self):
        weather_forecast = self.weather.GetWeeklyForecast(type="forecast")
        for i in range(4):
            next_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            next_container.get_style_context().add_class("upcoming-items-container")
            upcoming_temp = Gtk.Label()
            upcoming_temp.set_label(f"{int(weather_forecast[i]["temp"])}°")
            upcoming_desc = Gtk.Label()
            upcoming_desc.set_label(f"{weather_forecast[i]["description"].upper()}")
            upcoming_desc.get_style_context().add_class("upcoming-description")
            upcoming_icons = Gtk.Image.new_from_icon_name(self.weather.matchIcon(weather_forecast[i]["icon"]))
            upcoming_icons.get_style_context().add_class("upcoming-icons")
            dates = weather_forecast[i]["date"]
            dates_object = time.strptime(dates, "%Y-%m-%d %H:%M:%S")
            dates_formated = time.strftime("%H:%M", dates_object)
            upcoming_time = Gtk.Label()
            upcoming_time.set_label(f"{dates_formated}")
            upcoming_time.get_style_context().add_class("upcoming-time")
            next_container.append(upcoming_icons)
            next_container.append(upcoming_temp)
            next_container.append(upcoming_desc)
            next_container.append(upcoming_time)
            self.upcoming_weather_container.append(next_container)
        
    def resetToCurrentDate(self):
        today = GLib.DateTime.new_now_local()
        self.calendar.set_date(today)
    
    def markKurzeWoche(self, calendar=None):
        self.calendar.clear_marks()
        currently_shown_month = self.calendar.get_date().get_month()
        currently_shown_year = self.calendar.get_date().get_year()
        fridays = self.get_fridays(currently_shown_year, currently_shown_month)
        for d in fridays:
            if d[0] % 2:
                self.calendar.mark_day(d[1])

    def get_fridays(self, year, month):
        result = []
        current_date = datetime.date(year, month, 1)
        days_to_friday = (4 - current_date.weekday() + 7) % 7
        current_date += datetime.timedelta(days=days_to_friday)
    
        while current_date.month == month:
            week_num = current_date.isocalendar()[1]
            day_num = current_date.day
            result.append((week_num, day_num))
            current_date += datetime.timedelta(days=7)
        return tuple(result)

    def update_clock(self):
        #global _v_layer
        #if _v_layer.get_visible():
        if str(time.strftime("%H:%M")) != str(self.clock.get_label()):
            self.clock.set_label(time.strftime(str("%H:%M") ))
        return True
        #else:
            #return False

    def update_weather(self):
        pass

    
    def on_present(self):
        self.resetToCurrentDate()
        self.markKurzeWoche()
        #self.StartUpdateLoop()

def init_layer(config):
    global _v_layer
    if _v_layer is None:
        _v_layer = CalendarLayer(config)
        _v_layer.connect("close-request", lambda w, e: w.hide() or True)

def toggle_layer():
    global _v_layer
    if _v_layer.get_visible():
        _v_layer.hide()
    else:
        _v_layer.on_present()
        _v_layer.show()
        _v_layer.present()

def hide_layer():
    global _v_layer
    _v_layer.hide()
