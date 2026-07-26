import gi
import time
import datetime
from ..assets import weather as weather
from ..assets.utils import Header, window_utils, GtkLayerShellUtils, Popups, IPCSocket
from ..widgets.widgets import ScrolledPanel, PopupHeader
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib
_v_layer = None


@Gtk.Template(resource_path="/l1p0-menus/ui/weather_card.ui")
class WeatherCard(Gtk.Box):
    __gtype_name__ = 'WeatherCard'
    temp = Gtk.Template.Child()
    icon = Gtk.Template.Child()
    desc = Gtk.Template.Child()
    time = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

@Gtk.Template(resource_path="/l1p0-menus/ui/clock_weather.ui")
class CalendarLayer(Gtk.Window):
    __gtype_name__ = 'calendar_window'
    overlay = Gtk.Template.Child()
    clock = Gtk.Template.Child()
    date = Gtk.Template.Child()
    calendar = Gtk.Template.Child()
    menu_btn = Gtk.Template.Child()
    main_weather_container = Gtk.Template.Child()
    sunrise_container = Gtk.Template.Child()
    current_sunrise = Gtk.Template.Child()
    current_weather_icon = Gtk.Template.Child()
    current_weather_temp = Gtk.Template.Child()
    current_weather_feel = Gtk.Template.Child()
    current_weather_desc = Gtk.Template.Child()
    current_weather_place = Gtk.Template.Child()
    sunset_container = Gtk.Template.Child()
    current_sunset = Gtk.Template.Child()
    upcoming_weather_container = Gtk.Template.Child()


    def __init__(self, config):
        super().__init__(title="Calendar Layer")
        self.config = config
        self.shellutils = GtkLayerShellUtils(self, "calendar")
        self.load_config(self.config)
        self.set_default_size(300, 150)
        self.init_template()
        self.window_utils = window_utils()
        self.ipc = IPCSocket(name="weather", on_receive=self._on_ipc_receive)
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
                    if hasattr(self, 'popupwindow'):
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

            else:
                city = None
                language = 'en'
                api_key = None
                self.show_sunset = False
                self.show_feels_like = True

            if not hasattr(self, 'weather'):
                self.weather = weather.OpenWeatherMap(city, api_key, language, self._on_weather_callback)
            else:
                self.weather.city = city
                self.weather.api_key = api_key
                self.weather.language = language

            if not hasattr(self, 'popupwindow'):
                windows = self.window_utils.setup_revealer(overlay=self.overlay, popupwindow=PopupWindow, match_icons=self.weather.matchIcon, date_format=self.date_format)
                self.popupwindow = windows["overlay"]
                self.revealer = windows["revealer"]
                self.menu_btn.connect("clicked", lambda x: self.revealer.set_reveal_child(True))
            if hasattr(self, 'main_weather_container'):
                self.update_weather()
                return
           # self.setup_weather()
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
                self.clock_update_timer = None
            except:
                pass
        if self.weather_timer:
            try: 
                GLib.source_remove(self.weather_timer)
                self.weather_timer = None
            except:
                pass
        self.clock_update_timer = GLib.timeout_add_seconds(1, self.update_clock)
        if self.config is not None and "api_key" in self.config:
            self.weather_timer = GLib.timeout_add_seconds(3600, self.update_weather)

    def setup_time(self):
        self.clock.set_label(time.strftime(str("%H:%M") ))
        self.date.set_label(time.strftime(self.date_format))
        self.resetToCurrentDate()
        if self.config is not None and "kurzewoche" in self.config and self.config.get("kurzewoche", False):
            self.calendar.connect("next-month", self.markKurzeWoche)
            self.calendar.connect("prev-month", self.markKurzeWoche)
            self.calendar.connect("next-year", self.markKurzeWoche)
            self.calendar.connect("prev-year", self.markKurzeWoche)
            self.markKurzeWoche()



    def set_weather_values(self, weather):
        current_weather = weather[0]
        self.current_weather_icon.set_from_icon_name(self.weather.matchIcon(current_weather["icon"]))
        self.current_weather_desc.set_label(f"{current_weather["description"].upper()}")
        self.current_weather_temp.set_label(f"{int(current_weather["temp"])}°")
        self.current_weather_place.set_label(f"{current_weather["name"]}, {current_weather["country"]}")
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


    def setup_forecast(self, weather_forecast):
        try:
            self.popupwindow.setup_weather(weather_forecast)
        except Exception as e:
            print(e)
        while child := self.upcoming_weather_container.get_first_child():
            self.upcoming_weather_container.remove(child)
        for i in range(4):
            card = WeatherCard()
            card.temp.set_label(f"{int(weather_forecast[i]["temp"])}°")
            card.desc.set_label(f"{weather_forecast[i]["description"].upper()}")
            card.icon.set_from_icon_name(self.weather.matchIcon(weather_forecast[i]["icon"]))
            dates = weather_forecast[i]["dt_txt"]
            dates_object = time.strptime(dates, "%Y-%m-%d %H:%M:%S")
            dates_formated = time.strftime("%H:%M", dates_object)
            card.time.set_label(f"{dates_formated}")
            self.upcoming_weather_container.append(card)
        
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
        try:
            sucess = self.weather.GetWeatherObject(weathertype="weather")
            sucess_forecast = self.weather.GetWeatherObject(weathertype="forecast")

            if not sucess or not sucess_forecast:
                self.main_weather_container.set_visible(False)
        except Exception as e:
            print(f"Error while trying to get weather infos: {e}")
        return True

    
    def on_present(self):
        self.resetToCurrentDate()
        if self.config is not None and "kurzewoche" in self.config and self.config.get("kurzewoche", False):
            self.markKurzeWoche()

    def _on_weather_callback(self, weathertype, message):
        if not message:
            self.main_weather_container.set_visible(False)
            return
        if not self.main_weather_container.get_visible():
            self.main_weather_container.set_visible(True)
        if weathertype == "forecast":
            self.setup_forecast(message)
        elif weathertype == "weather":
            self.set_weather_values(message)

    def _on_ipc_receive(self, sender, message):
        if sender == "wifi":
            if "connected" in message and not self.main_weather_container.get_visible():
                self.weather.GetWeatherObject(weathertype="weather")
                self.weather.GetWeatherObject(weathertype="forecast")


class PopupWindow:
    def __init__(self, match_icons, date_format="%Y-%m-%d", windows=None):
        self.window = windows
        self.match_icons = match_icons
        self.date_format = date_format
        self.panel = Gtk.Frame()
        self.popups = Popups()
        self.window_utils = window_utils()
       # self.scrolled_weather = ScrolledPanel()
       # self.scrolled_weather_content = self.scrolled_weather.panel_content
       # self.scrolled_weather.set_propertys(max_height=200, min_height=150, header_function=self.update_headers, sort_function=self._sort_func)
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
        header = PopupHeader(close_funktion=lambda: self.window["revealer"].set_reveal_child(False))
        header.header_text.set_label("UPCOMING WEATHER")
        self.panel_content.append(header)
        #self.popups.create_header(header_text="UPCOMING WEATHER", close_function=self.windows, main_container=self.panel_content)
        self.panel_content.append(self.scrolled_weather)

    def setup_weather(self, weather_forecast):
        rows = {}
        for values in self.rows.values():
            if values.get_parent() is not None:
                self.scrolled_weather_content.remove(values)
        for i in range(len(weather_forecast)):
            card = WeatherCard()
            dates = weather_forecast[i]["dt_txt"]
            dates_object = time.strptime(dates, "%Y-%m-%d %H:%M:%S")
            dates_formated = time.strftime("%H:%M", dates_object)
            show_date = time.strftime(self.date_format, dates_object)
            card.temp.set_label(f"{int(weather_forecast[i]["temp"])}°")
            card.desc.set_label(f"{weather_forecast[i]["description"].upper()}")
            card.desc.get_style_context().add_class("popup-upcoming-description")
            card.icon.set_from_icon_name(self.match_icons(weather_forecast[i]["icon"]))
            card.icon.get_style_context().add_class("popup-upcoming-icons")
            card.time.set_label(f"{dates_formated}")
            card.time.get_style_context().add_class("popup-upcoming-time")
            if show_date not in rows:
                rows[show_date] = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                rows[show_date].set_homogeneous(False)
            card.get_style_context().add_class("popup-upcoming-items-container")
            rows[show_date].append(card)
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
    try:
        global _v_layer
        if _v_layer is None:
            _v_layer = CalendarLayer(config)
            _v_layer.connect("close-request", lambda w, e: w.hide() or True)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize CalendarLayer: {e}")

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
