import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib, Gio
from datetime import timedelta
from time import strptime
from ..assets.utils import window_utils, GtkLayerShellUtils, Popups, Notifications
from ..assets.battery_dbus import Battery, PowerProfiles
from ..widgets.widgets import DetailsPopupRow
import os
import math
_v_layer = None


@Gtk.Template(resource_path="/l1p0-menus/ui/power_profile_btn.ui")
class PowerProfileButton(Gtk.Button):
    __gtype_name__ = 'PowerProfileButton'
    icon = Gtk.Template.Child()
    profile_name = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

@Gtk.Template(resource_path="/l1p0-menus/ui/battery_level_bar.ui")
class BatteryLevelBar(Gtk.Box):
    __gtype_name__ = 'BatteryLevelBar'
    icon = Gtk.Template.Child()
    name = Gtk.Template.Child()
    level_bar = Gtk.Template.Child()
    percentage = Gtk.Template.Child()
    menu_btn = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.status = 0
        self.init_template()

@Gtk.Template(resource_path="/l1p0-menus/ui/battery.ui")
class BatteryLayer(Gtk.Window):
    __gtype_name__ = 'battery_window'
    overlay = Gtk.Template.Child()
    combined_battery_time_to = Gtk.Template.Child()
    combined_battery_rate = Gtk.Template.Child()
    battery_overlay = Gtk.Template.Child()
    combined_icon = Gtk.Template.Child()
    combined_battery_level = Gtk.Template.Child()
    combined_battery_status = Gtk.Template.Child()
    batterys_vertical_container = Gtk.Template.Child()
    power_profile_container = Gtk.Template.Child()
    background_level_bar = Gtk.Template.Child()
    level_bar = Gtk.Template.Child()
    
    def __init__(self, config):
        super().__init__(title="Battery Layer")
        self.config = config
        self.shellutils = GtkLayerShellUtils(self, "battery")
        self.load_config(self.config)
        self.set_default_size(400, 300)
        self.init_template()
        self.window_utils = window_utils()
        self.notification = Notifications(self)
        self.notification_enabled = True
        self.notification_threshold = [3, 15, 20]
        self.tick_id = None
        self.combined_battery_animation_value = 0
        self.battery = Battery(self.update_ui_elements)
        self.powerprofile = PowerProfiles(self.update_power_profile_buttons)
        self.overlay_windows={}
        self.battery_status_codes = {
            0: "Unknown",
            1: "Charging",
            2: "Discharging",
            3: "Empty",
            4: "Fully Charged",
            5: "Pending Charge",
            6: "Pending Discharge"
        }
        for battery_name in self.battery.batterys.keys():
            self.overlay_windows[f"{battery_name}"] = self.window_utils.setup_revealer(overlay=self.overlay, popupwindow=PopupWindow, battery=battery_name, battery_dbus=self.battery)
        self.setup_ui()

    def load_config(self, config):
        if config != self.config:
            self.config = config
            self.notification_enabled = self.config.get("notification", True)
            self.notification_threshold = [int(x) for x in self.config.get("notification_threshold", "3, 15, 20").split(",")]
        anchor, margin = self.shellutils.process_config(config, default_anchor="top-right", default_margin=[10, 10])
        self.shellutils.setup_layer_shell(anchor, margin)
            

    def setup_ui(self): 
        self.battery.get_initial_combined_battery_info()
        self.combined_battery_status_code = 0

        self.battery.get_initial_battery_info()
        self.battery_widgets = {}
        for battery_name in self.battery.batterys.keys():
            widgets = BatteryLevelBar()
            widgets.name.set_label(f"{battery_name}")
            widgets.menu_btn.connect("clicked", lambda x, name=battery_name: self.overlay_windows[f"{name}"]["revealer"].set_reveal_child(True))
            self.battery_widgets[battery_name] = widgets
        for battery_name in self.battery.batterys:
            self.batterys_vertical_container.append(self.battery_widgets[battery_name])

        self.setup_power_profile_buttons()


    def setup_power_profile_buttons(self):
        self.power_profile_buttons = {}
        power_profiles = {
            "Power Saver": "power-profile-power-saver-symbolic",
            "Balanced": "power-profile-balanced-symbolic",
            "Performance": "power-profile-performance-symbolic"
        }
        for profile, icon in power_profiles.items():
            button = PowerProfileButton()
            button.icon.set_from_icon_name(icon)
            button.profile_name.set_label(profile)
            self.power_profile_buttons[profile] = button
            self.power_profile_container.append(button)
        self.power_profile_buttons["Performance"].connect("clicked", self.on_power_mode_switched, "performance")
        self.power_profile_buttons["Balanced"].connect("clicked", self.on_power_mode_switched, "balanced")
        self.power_profile_buttons["Power Saver"].connect("clicked", self.on_power_mode_switched, "power-saver")
        self.powerprofile.get_active_profile()

    def update_power_profile_buttons(self, message):
        if "active_profile" in message:
            active = message["active_profile"]
            for profile_name, button in self.power_profile_buttons.items():
                name = profile_name.lower().replace(" ", "-")
                if name == active:
                    button.get_style_context().add_class("active") 
                else:
                    button.get_style_context().remove_class("active") 


    def format_time(self, seconds, label):
        time_formated = str(timedelta(seconds=seconds))
        time_object = strptime(time_formated, "%H:%M:%S")
        if time_object.tm_hour > 0:
            time_to_formated = f"{label} in {time_object.tm_hour}h {time_object.tm_min}min"
        else:
            time_to_formated = f"{label} in {time_object.tm_min}min"
        return time_to_formated
    
    def on_power_mode_switched(self, button, mode):
        if not button.get_style_context().has_class("active"):
            self.powerprofile.set_power_profile(mode)

    def animate_on_present(self):
        self.combined_battery_level.set_label("0%")
        self.animation_value = 0
        
        if self.tick_id:
            self.remove_tick_callback(self.tick_id)

        def manage_animation(widget, frame_clock):
            step = 2
            diff = self.combined_battery_animation_value - self.animation_value
            if abs(diff) < step:
                self.combined_battery_level.set_label(f"{self.combined_battery_animation_value}%")
                self.tick_id = None
                return False
            if diff > 0:
                self.animation_value += step
            else:
                self.animation_value -= step
            self.combined_battery_level.set_label(f"{self.animation_value}%")
            return True
        self.tick_id = self.add_tick_callback(manage_animation)

    def update_ui_elements(self, battery, data):
        things_to_update_bat = ["Model", "Capacity", "Vendor", "Percentage", "State", "ChargeCycles", "TimeToEmpty", "TimeToFull", "EnergyRate", "EnergyFullDesign", "EnergyFull"]
        updates = [update for update in things_to_update_bat if update in data]
        if updates:
            for update in updates:
                if battery != "DisplayDevice":
                    if battery in self.battery.batterys:
                        battery_name = battery
                        if update == "Percentage":
                            self.battery_widgets[battery_name].percentage.set_label(f"{round(data['Percentage'])}%")
                            self.battery_widgets[battery_name].level_bar.set_value(float(round(data['Percentage'])))
                            self.battery_widgets[battery_name].icon.set_from_icon_name(f"{self.window_utils.get_battery_icon(int(self.battery_widgets[battery_name].status), int(round(data['Percentage'])))}")
                        if update == "State":
                            self.battery_widgets[battery_name].status = int(data['State'])
                            self.battery_widgets[battery_name].icon.set_from_icon_name(f"{self.window_utils.get_battery_icon(int(data['State']), int(round(self.battery_widgets[battery_name].level_bar.get_value())))}")
                        if update in ["ChargeCycles", "EnergyFull", "EnergyFullDesign", "Vendor", "Model"]:
                            window = self.overlay_windows[f"{battery_name}"]["overlay"]
                            for key, items in window.match_names.items():
                                if update == items:
                                    update_value = f"{data[update]}Wh" if update in ['EnergyFull', 'EnergyFullDesign'] else data[update]
                                    window.details[key].set_label(f"{update_value}")
                            full = window.details["Energy Full"].get_label()
                            design = window.details["Energy Design"].get_label() 
                            if full != "n/a" and design != "n/a":
                                capacity = round((float(full.replace("Wh", "")) / float(design.replace("Wh", "")) * 100))
                                window.details["Capacity"].set_label(f"{capacity}%")

                elif battery == "DisplayDevice":
                    if update == "Percentage":
                        if self.combined_battery_level.get_label() != f"{round(data['Percentage'])}%":
                            self.combined_battery_level.set_label(f"{round(data['Percentage'])}%")
                            self.level_bar.set_value(round(data['Percentage']))
                            self.combined_battery_animation_value = round(data['Percentage'])
                            self.combined_icon.set_from_icon_name(f"{self.window_utils.get_battery_icon(int(self.combined_battery_status_code), int(round(data['Percentage'])))}")
                            if self.notification_enabled:
                                if round(data['Percentage']) in self.notification_threshold and self.combined_battery_status_code == 2:
                                    self.notification.notify(icon="battery-caution-symbolic", title="Low Battery", message=f'Battery is at {int(round(data["Percentage"]))}%, please plug in your charger.', urgency=2)
                    if update == "TimeToEmpty":
                        self.combined_battery_time_to.set_label(self.format_time(data["TimeToEmpty"], "Empty"))
                    if update == "TimeToFull":
                        self.combined_battery_time_to.set_label(self.format_time(data["TimeToFull"], "Full"))
                    if update == "State":
                        self.combined_battery_status.set_label(f"{self.battery_status_codes.get(data['State'])}")
                        self.combined_battery_status_code = int(data["State"])
                        if data["State"] == 4:
                            self.combined_battery_time_to.set_label("Fully charged")
                    if update == "EnergyRate":
                        self.combined_battery_rate.set_label(f"{data['EnergyRate']:.2f} W")

@Gtk.Template(resource_path="/l1p0-menus/ui/level_bar.ui")
class HalfCircleLevelBar(Gtk.DrawingArea):
    __gtype_name__ = 'HalfCircleLevelBar'
    def __init__(self, type="level"):
        super().__init__()
        self.type = type
        self.set_content_width(300)
        self.set_content_height(200)
        self.fraction = 0.5
        self.tick_id = None
        self.set_draw_func(self.on_draw)

    def on_draw(self, drawing_area, cr, width, height):
        xc = width / 2
        yc = height - 10
        radius = min(width / 2, height) - 20
        line_width = 15

        context = self.get_style_context()
        active_color = context.get_color() 
        cr.set_line_width(line_width)
        cr.set_line_cap(1)
        if self.get_style_context().has_class("background"):
            Gdk.cairo_set_source_rgba(cr, active_color)
            cr.arc(xc, yc, radius, math.pi, 2 * math.pi)
            cr.stroke()
        else:
            if self.fraction > 0:
                Gdk.cairo_set_source_rgba(cr, active_color)
                end_angle = math.pi + (self.fraction * math.pi)
                cr.arc(xc, yc, radius, math.pi, end_angle)
                cr.stroke()

    def set_value(self, value):
        self.fraction = max(0.0, min(1.0, value / 100.0))
        self.queue_draw()

    def animate_to_value(self, target_fraction):
        self.target = max(0.0, min(1.0, target_fraction / 100.0))

        if self.tick_id:
            self.remove_tick_callback(self.tick_id)

        def manage_animation(widget, frame_clock):
            step = 0.020
            diff = self.target - self.fraction
        
            if abs(diff) < step:
                self.fraction = self.target
                self.queue_draw()
                self.tick_id = None
                return False
            if diff > 0:
                self.fraction += step
            else:
                self.fraction -= step
            
            self.queue_draw()
            return True
        self.tick_id = self.add_tick_callback(manage_animation)



class PopupWindow:
    def __init__(self, battery, battery_dbus, windows):
        self.window = windows
        self.battery_dbus = battery_dbus
        self.battery = battery
        self.popups = Popups()
        self.panel = Gtk.Frame()
        self.panel.add_css_class("floating-panel")
        self.panel.set_size_request(-1, 170)
        self.panel_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
            margin_start=20,
            margin_end=20,
            margin_top=20,
            margin_bottom=20
            )
        self.match_names = {
            "Vendor": "Vendor",
            "Model": "Model",
            "Capacity": "Capacity",
            "Charge Cycles": "ChargeCycles",
            "Energy Full": "EnergyFull",
            "Energy Design": "EnergyFullDesign"
        }
        self.icons = {
            "Vendor": "preferences-system-symbolic",
            "Model": "dialog-information-symbolic",
            "Capacity": "battery-missing-symbolic",
            "Charge Cycles": "battery-ac-adapter-symbolic",
            "Energy Full": "battery-level-100-symbolic",
            "Energy Design": "battery-level-100-symbolic"
        }
        self.setup_ui()


    def setup_ui(self):
        self.popups.create_header(header_text=f"BATTERY DETAILS ({self.battery})", close_function=self.window, main_container=self.panel_content)
        self.details = {}
        for property_names, detail_name in self.match_names.items():
            detail_row = DetailsPopupRow()
            detail_row.property_name.set_label(property_names)
            detail_row.icon.set_from_icon_name(self.icons.get(property_names))
            detail_row.property_value.set_label("n/a")
            self.panel_content.append(detail_row)
            self.details[property_names] = detail_row.property_value
        self.panel.set_child(self.panel_content)
        

def on_present():
    global _v_layer
    _v_layer.level_bar.set_value(0)
    _v_layer.animate_on_present()
    _v_layer.level_bar.animate_to_value(_v_layer.combined_battery_animation_value)

def init_layer(config):
    try:
        global _v_layer
        if _v_layer is None:
            _v_layer = BatteryLayer(config)
            _v_layer.connect("close-request", lambda w, e: w.hide() or True)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize BatteryLayer: {e}")

def toggle_layer():
    global _v_layer
    if _v_layer.get_visible():
        _v_layer.hide()
    else:
        _v_layer.show()
        _v_layer.present()
        on_present()

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