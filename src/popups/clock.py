import gi
import time
import datetime
from ..assets import weather as weather
from ..assets.utils import Header, window_utils, GtkLayerShellUtils, Popups
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib
_v_layer = None


class CalendarLayer(Gtk.Window):
    def __init__(self, config):
        super().__init__(title="Calendar Layer")
        self.config = config
        self.shellutils = GtkLayerShellUtils(self, "calendar")
        self.load_config(self.config)
        self.set_default_size(300, 150)
        self.get_style_context().add_class("calendar-window")
        self.overlay = Gtk.Overlay()
        self.window_utils = window_utils()
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_container.set_margin_start(0)
        self.main_container.get_style_context().add_class("calendar-layer")
        self.set_child(self.overlay)
        self.overlay.set_child(self.main_container)
        self.horizontal_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.horizontal_container.set_homogeneous(True)
        self.main_container.append(self.horizontal_container)
        self.date_format = "%Y-%m-%d"
        self.show_feels_like = True
        self.setup_time()
        self.clock_update_timer = None
        self.weather_timer = None
        self.setup_weather_config()
        self.StartUpdateLoop()

    def load_config(self, config):
        if self.config != config:
            self.config = config
            if self.config is not None and "date_format" in self.config:
                formats_to_diff = ["%d", "%a", "%A"]
                if any(fmt in self.config.get("date_format", "%Y-%m-%d") for fmt in formats_to_diff):
                    self.date_format = self.config.get("date_format", "%Y-%m-%d")
                    self.date.set_label(time.strftime(str(self.date_format)))
                    self.popupwindow.date_format = self.date_format
            self.setup_weather_config()
            if self.config is not None and self.config.get('kurzewoche', False):
                self.markKurzeWoche()
            else:
                self.calendar.clear_marks()
        anchor, margin = self.shellutils.process_config(self.config, default_anchor="top-center", default_margin=[10])
        self.shellutils.setup_layer_shell(anchor, margin)

    def setup_weather_config(self):
        try:
            if isinstance(self.config, dict):
                self.show_sunset = self.config.get("show_sunset", False)
                self.show_feels_like = self.config.get("show_feels_like", True)
                api_key = self.config.get('api_key', None)
                language = self.config.get('language', 'en')
                city = self.config.get('city', None)
                if hasattr(self, 'weather'):
                    self.weather.city = city
                    self.weather.api_key = api_key
                    self.weather.language = language
                else:
                    self.weather = weather.OpenWeatherMap(city, api_key, language)
            else:
                if hasattr(self, 'weather'):
                    self.weather.city = None
                    self.weather.api_key = None
                    self.weather.language = "en"
                else:
                    self.weather = weather.OpenWeatherMap(city=None, api_key=None, language="en")
                self.show_sunset = False
                self.show_feels_like = True

            if not hasattr(self, 'popupwindow'):
                windows = self.window_utils.setup_revealer(overlay=self.overlay, popupwindow=PopupWindow, match_icons=self.weather.matchIcon, date_format=self.date_format)
                self.popupwindow = windows["overlay"]
                self.revealer = windows["revealer"]
            if hasattr(self, 'main_weather_container'):
                self.StartUpdateLoop()
                return
            self.setup_weather()
        except Exception as e:
            if self.config is not None:
                print(f"Missing variable from config: {e}weather is disabled!")
            else:
                print(e)
                pass

    def StartUpdateLoop(self):
        if self.clock_update_timer:
            try:
                GLib.source_remove(self.clock_update_timer)
            except:
                pass
        self.clock_update_timer = GLib.timeout_add_seconds(1, self.update_clock)
        if self.config is not None and "api_key" in self.config:
            self.update_weather()

    def setup_time(self):
        self.time_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.horizontal_container.append(self.time_container)
        self.clock = Gtk.Label()
        self.clock.set_label(time.strftime(str("%H:%M") ))
        self.clock.get_style_context().add_class("clock")
        self.clock.set_hexpand(False)
        self.clock.set_halign(Gtk.Align.CENTER)
        self.time_container.append(self.clock)

        self.date = Gtk.Label()
        self.date.set_label(time.strftime(self.date_format))
        self.date.get_style_context().add_class("date")
        self.date.set_hexpand(False)
        self.date.set_halign(Gtk.Align.CENTER)
        self.time_container.append(self.date)

        self.calendar = Gtk.Calendar()
        self.calendar.set_size_request(320, -1)
        self.calendar.set_halign(Gtk.Align.CENTER)
        self.calendar.set_property("show-week-numbers", False)
        self.calendar.get_style_context().add_class("calendar")
        self.resetToCurrentDate()
        if self.config is not None and "kurzewoche" in self.config and self.config.get("kurzewoche", False):
            self.calendar.connect("next-month", self.markKurzeWoche)
            self.calendar.connect("prev-month", self.markKurzeWoche)
            self.calendar.connect("next-year", self.markKurzeWoche)
            self.calendar.connect("prev-year", self.markKurzeWoche)
            self.markKurzeWoche()
        self.calendar.set_hexpand(False)
        self.time_container.append(self.calendar)



    def setup_weather(self):
        self.main_weather_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
            margin_start=20,
            margin_end=20,
            margin_top=20,
            margin_bottom=0,)
        self.horizontal_container.append(self.main_weather_container)
        menu_button = Gtk.Button()
        menu_button.connect("clicked", lambda x: self.revealer.set_reveal_child(True))
        menu_button.set_hexpand(True)
        menu_button.set_halign(Gtk.Align.END)
        self.main_weather_container.append(menu_button)
        menu_button.get_style_context().add_class("weather-menu-button")
        menu_button_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic")
        menu_button.set_child(menu_button_icon)
        self.main_horizontal_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_weather_container.append(self.main_horizontal_container)
        weather_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        weather_container.set_hexpand(True)
        self.setup_sunrise_sunset()
        self.main_horizontal_container.append(self.sunrise_container)
        self.sunrise_container.set_valign(Gtk.Align.END)
        self.main_horizontal_container.append(weather_container)
        self.current_weather_desc = Gtk.Label()
        self.current_weather_desc.get_style_context().add_class("weather-description")
        self.current_weather_temp = Gtk.Label()
        self.current_weather_temp.get_style_context().add_class("weather-temp")
        self.current_weather_feel = Gtk.Label()
        self.current_weather_feel.get_style_context().add_class("weather-feel")
        self.current_weather_wind = Gtk.Label()
        self.current_weather_place = Gtk.Label()
        self.current_weather_place.get_style_context().add_class("weather-city")
        self.current_weather_icon = Gtk.Image.new_from_icon_name("weather-clear-symbolic")
        self.current_weather_temp.set_hexpand(True)
        self.current_weather_feel.set_hexpand(True)
        self.current_weather_desc.set_hexpand(True)
        self.current_weather_temp.set_halign(Gtk.Align.END)
        self.current_weather_feel.set_halign(Gtk.Align.START)
        self.current_weather_desc.set_halign(Gtk.Align.CENTER)
        self.current_weather_icon.get_style_context().add_class("weather-icon")
        weather_container.append(self.current_weather_icon)
        temp_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        weather_container.append(temp_container)
        temp_container.append(self.current_weather_temp)
        temp_container.append(self.current_weather_feel)
        weather_container.append(self.current_weather_desc)
        weather_container.append(self.current_weather_place)
        self.main_horizontal_container.append(self.sunset_container)
        self.sunset_container.set_valign(Gtk.Align.END)
        self.upcoming_weather_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.upcoming_weather_container.get_style_context().add_class("upcoming-container")
        self.upcoming_weather_container.set_homogeneous(True)
        self.main_weather_container.append(self.upcoming_weather_container)
        self.set_weather_values()
        self.setup_forecast()

    def set_weather_values(self):
        weather = self.weather.GetWeeklyForecast(type="weather")
        if weather is None:
            self.main_weather_container.set_visible(False)
            raise ValueError("API returned empty weather data")
        current_weather = weather[0]
        self.current_weather_icon.set_from_icon_name(self.weather.matchIcon(current_weather["icon"]))
        self.current_weather_desc.set_label(f"{current_weather["description"].upper()}")
        self.current_weather_temp.set_label(f"{int(current_weather["temp"])}°")
        self.current_weather_wind.set_label(f"{int(current_weather["wind_speed"])}km/h")
        self.current_weather_place.set_label(f"{current_weather["city"]}, {current_weather["country"]}")
        if not self.show_feels_like:
            self.current_weather_feel.set_visible(False)
            self.current_weather_temp.set_halign(Gtk.Align.CENTER)
        else:
            self.current_weather_feel.set_label(f"{int(current_weather["feels_like"])}°")
            self.current_weather_temp.set_halign(Gtk.Align.END)
            self.current_weather_feel.set_visible(True)

        if not self.show_sunset:
            self.sunset_container.set_visible(False)
            self.sunrise_container.set_visible(False)
        else:
            sunset_info = self.calculate_sunset(current_weather["sunset"], current_weather["sunrise"], current_weather["timezone"])
            self.current_sunset.set_label(f"{sunset_info["sunset"]}")
            self.current_sunrise.set_label(f"{sunset_info["sunrise"]}")
            self.sunset_container.set_visible(True)
            self.sunrise_container.set_visible(True)

        if not self.main_weather_container.get_visible():
            self.main_weather_container.set_visible(True)

    def setup_sunrise_sunset(self):
        self.sunrise_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sunset_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.current_sunrise = Gtk.Label()
        self.current_sunset = Gtk.Label()
        self.sunrise_container.get_style_context().add_class("weather-sunrise")
        self.sunset_container.get_style_context().add_class("weather-sunset")
        sunrise_icon = Gtk.Image.new_from_icon_name("daytime-sunrise-symbolic")
        sunset_icon = Gtk.Image.new_from_icon_name("daytime-sunset-symbolic")
        sunset_icon.get_style_context().add_class("sunset-icon")
        sunrise_icon.get_style_context().add_class("sunrise-icon")
        self.sunrise_container.append(sunrise_icon)
        self.sunset_container.append(sunset_icon)
        self.sunrise_container.append(self.current_sunrise)
        self.sunset_container.append(self.current_sunset)

    def setup_forecast(self):
        weather_forecast = self.weather.GetWeeklyForecast(type="forecast")
        if weather_forecast is None:
            self.main_weather_container.set_visible(False)
            raise ValueError("API returned empty weather data")
        try:
            self.popupwindow.setup_weather(weather_forecast)
        except Exception as e:
            print(e)
        while child := self.upcoming_weather_container.get_first_child():
            self.upcoming_weather_container.remove(child)
        for i in range(4):
            next_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            next_container.get_style_context().add_class("upcoming-items-container")
            upcoming_temp = Gtk.Label()
            upcoming_temp.set_label(f"{int(weather_forecast[i]["temp"])}°")
            upcoming_desc = Gtk.Label()
            upcoming_desc.set_label(f"{weather_forecast[i]["description"].upper()}")
            upcoming_desc.set_wrap(True)
            upcoming_desc.set_wrap_mode(0)
            upcoming_desc.set_lines(2)
            upcoming_desc.set_ellipsize(2)
            upcoming_desc.set_justify(2)
            upcoming_desc.set_valign(Gtk.Align.CENTER)
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
        if not self.main_weather_container.get_visible():
            self.main_weather_container.set_visible(True)
        
    def calculate_sunset(self, sunset, sunrise, shift_seconds):
        utc_sunset_time = datetime.datetime.fromtimestamp(sunset, tz=datetime.timezone.utc)
        utc_sunrise_time = datetime.datetime.fromtimestamp(sunrise, tz=datetime.timezone.utc)
        local_tz = datetime.timezone(datetime.timedelta(seconds=shift_seconds))
        local_sunset_time = utc_sunset_time.astimezone(local_tz).strftime("%H:%M")
        local_sunrise_time = utc_sunrise_time.astimezone(local_tz).strftime("%H:%M")
        return {"sunset": local_sunset_time, "sunrise": local_sunrise_time}
        
    def resetToCurrentDate(self):
        today = GLib.DateTime.new_now_local()
        self.calendar.set_date(today)
    
    def markKurzeWoche(self, calendar=None):
        self.calendar.clear_marks()
        if self.config is not None and not self.config.get('kurzewoche', False):
            return
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
        if str(time.strftime("%H:%M")) != str(self.clock.get_label()):
            self.clock.set_label(time.strftime(str("%H:%M") ))
        if str(time.strftime(self.date_format)) != str(self.date.get_label()):
            self.date.set_label(time.strftime(str(self.date_format) ))
            self.resetToCurrentDate()
        return True

    def update_weather(self):
        if self.weather_timer:
            try:
                GLib.source_remove(self.weather_timer)
                self.weather_timer = None
            except:
                pass
        polling_delay = 3600
        try:
            self.set_weather_values()
            self.setup_forecast()
        except Exception as e:
            if hasattr(self, 'main_weather_container'):
                self.main_weather_container.set_visible(False)
            polling_delay = 60
        self.weather_timer = GLib.timeout_add_seconds(polling_delay, self.update_weather)
        return False

    
    def on_present(self):
        self.resetToCurrentDate()
        if self.config is not None and "kurzewoche" in self.config and self.config.get("kurzewoche", False):
            self.markKurzeWoche()

class PopupWindow:
    def __init__(self, match_icons, date_format="%Y-%m-%d", windows=None):
        self.windows = windows
        self.match_icons = match_icons
        self.date_format = date_format
        self.panel = Gtk.Frame()
        self.popups = Popups()
        self.window_utils = window_utils()
        self.scrolled_weather, self.scrolled_weather_content = self.window_utils.setup_scrolled_windows(max_height=200, min_height=150, header_function=self.update_headers, sort_function=self._sort_func)
        self.panel.add_css_class("popup-weather-panel")
        self.panel.set_size_request(-1, 170)
        self.panel_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_start=20,
            margin_end=20,
            margin_top=20,
            margin_bottom=20
            )
        self.panel.set_child(self.panel_content)
        self.rows = {}
        self.setup_ui()

    def setup_ui(self):
        self.popups.create_header(header_text="UPCOMING WEATHER", close_function=self.windows, main_container=self.panel_content)
        self.panel_content.append(self.scrolled_weather)

    def setup_weather(self, weather_forecast):
        rows = {}
        for values in self.rows.values():
            if values.get_parent() is not None:
                self.scrolled_weather_content.remove(values)
        for i in range(len(weather_forecast)):
            dates = weather_forecast[i]["date"]
            dates_object = time.strptime(dates, "%Y-%m-%d %H:%M:%S")
            dates_formated = time.strftime("%H:%M", dates_object)
            show_date = time.strftime(self.date_format, dates_object)
            upcoming_temp = Gtk.Label()
            upcoming_temp.set_label(f"{int(weather_forecast[i]["temp"])}°")
            upcoming_desc = Gtk.Label()
            upcoming_desc.set_label(f"{weather_forecast[i]["description"].upper()}")
            upcoming_desc.set_wrap(True)
            upcoming_desc.set_wrap_mode(0)
            upcoming_desc.set_lines(2)
            upcoming_desc.set_ellipsize(2)
            upcoming_desc.set_justify(2)
            upcoming_desc.set_valign(Gtk.Align.CENTER)
            upcoming_desc.get_style_context().add_class("popup-upcoming-description")
            upcoming_icons = Gtk.Image.new_from_icon_name(self.match_icons(weather_forecast[i]["icon"]))
            upcoming_icons.get_style_context().add_class("popup-upcoming-icons")
            upcoming_time = Gtk.Label()
            upcoming_time.set_label(f"{dates_formated}")
            upcoming_time.get_style_context().add_class("popup-upcoming-time")
            if show_date not in rows:
                rows[show_date] = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                rows[show_date].set_homogeneous(False)
            next_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            next_container.get_style_context().add_class("popup-upcoming-items-container")
            next_container.append(upcoming_icons)
            next_container.append(upcoming_temp)
            next_container.append(upcoming_desc)
            next_container.append(upcoming_time)
            rows[show_date].append(next_container)
        for keys in rows.keys():
            count_childs = 0
            current_childs = rows[keys].get_first_child()
            while current_childs is not None:
                current_childs = current_childs.get_next_sibling()
                count_childs += 1
            if count_childs >= 5:
                rows[keys].set_homogeneous(True)
            row = Gtk.ListBoxRow()
            row.date = keys
            row.set_child(rows[keys])
            self.scrolled_weather_content.append(row)
            self.rows[keys] = row
        self.scrolled_weather_content.invalidate_sort()

    def _sort_func(self, row1, row2):
        if hasattr(row1, "date") and hasattr(row2, "date"):
            if row1.date != row2.date:
                return -1 if row1.date else 1
        return 0

    
    def update_headers(self, row, before):
        try:
            if before is None:
                if hasattr(row, "date") and row.date is not None:
                    row.set_header(self.window_utils.create_header(row.date))
                return
            
            if hasattr(before, "date") and hasattr(row, "date") and before.date != row.date:
                row.set_header(self.window_utils.create_header(row.date))

            else:
                row.set_header(None)
        except Exception as e:
            print(f"Error updating headers: {e}")
            row.set_header(None)
        


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

def reload_config(config):
    global _v_layer
    if _v_layer:
        _v_layer.load_config(config)

def hide_layer():
    global _v_layer
    _v_layer.hide()

def get_visibility():
    global _v_layer
    return _v_layer.get_visible()
