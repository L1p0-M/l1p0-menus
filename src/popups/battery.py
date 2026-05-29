import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib, Gio
from datetime import timedelta
from time import strptime
from ..assets.utils import window_utils, GtkLayerShellUtils
import os
import math
_v_layer = None


class BatteryLayer(Gtk.Window):
    def __init__(self, config):
        super().__init__(title="Battery Layer")
        self.config = config
        self.shellutils = GtkLayerShellUtils(self, "battery")
        self.load_config(self.config)
        self.set_default_size(400, 300)
        self.get_style_context().add_class("battery-window")
        self.main_overlay = Gtk.Overlay()
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_container.set_margin_start(0)
        self.main_container.get_style_context().add_class("battery-layer")
        self.main_overlay.set_child(self.main_container)
        self.set_child(self.main_overlay)
        self.vertical_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_container.append(self.vertical_container)
        self.overlay = Gtk.Overlay()
        self.battery = Battery(self.update_ui_elements)
        self.powerprofile = PowerProfiles(self.update_power_profile_buttons)
        self.setup_ui()
        self.overlay_windows={}
        for battery_name in self.battery.batterys.keys():
            revealer = Gtk.Revealer()
            revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
            revealer.set_valign(Gtk.Align.END)
            self.overlay_windows[f"{battery_name}_revealer"] = revealer
            overlay_window = PopupWindow(self, battery_name)
            self.overlay_windows[f"{battery_name}_overlay"] = overlay_window
            self.overlay_windows[f"{battery_name}_revealer"].set_child(overlay_window.panel)
            self.main_overlay.add_overlay(revealer)

    def load_config(self, config):
        if config != self.config:
            self.config = config
        anchor, margin = self.shellutils.process_config(config, default_anchor="top-right", default_margin=[10, 10])
        self.shellutils.setup_layer_shell(anchor, margin)
            

    def setup_ui(self): 
        self.top_horizontal_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.vertical_container.append(self.top_horizontal_container)
        self.batterys_vertical_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.batterys_vertical_container.get_style_context().add_class("batterys-container")
        battery_overlay_vertical_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        background_level_bar = HalfCircleLevelBar(type="background")
        self.level_bar = HalfCircleLevelBar()
        self.overlay.set_child(background_level_bar)
        self.overlay.add_overlay(self.level_bar)
        self.overlay.get_style_context().add_class("battery-overlay")
        battery_overlay_vertical_container.set_valign(Gtk.Align.END)
        battery_overlay_vertical_container.set_halign(Gtk.Align.CENTER)
        battery_overlay_vertical_container.set_margin_bottom(25)
        self.setup_combined_battery_info()
        battery_overlay_horizontal_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.top_horizontal_container.append(self.combined_battery_time_to)
        self.combined_battery_time_to.set_halign(Gtk.Align.START)
        battery_overlay_horizontal_container.append(self.combined_icon)
        self.combined_icon.set_halign(Gtk.Align.START)
        self.combined_battery_status.set_halign(Gtk.Align.CENTER)
        battery_overlay_vertical_container.append(battery_overlay_horizontal_container)
        battery_overlay_vertical_container.append(self.combined_battery_status)
        self.combined_battery_level.set_halign(Gtk.Align.CENTER)
        battery_overlay_horizontal_container.append(self.combined_battery_level)
        self.overlay.add_overlay(battery_overlay_vertical_container)
        self.vertical_container.append(self.overlay)
        self.setup_battery_info()
        for battery_name in self.battery.batterys:
            self.battery_widgets[battery_name]["icon"].set_halign(Gtk.Align.START)
            self.battery_widgets[battery_name]["name_label"].set_halign(Gtk.Align.START)
            self.battery_widgets[battery_name]["Percentage"].set_halign(Gtk.Align.END)
            self.battery_widgets[battery_name]["level_bar"]
            self.battery_widgets[battery_name]["menu_button"].set_valign(Gtk.Align.CENTER)
            battery_level_horizontal_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            battery_level_horizontal_container.append(self.battery_widgets[battery_name]["icon"])
            battery_level_horizontal_container.append(self.battery_widgets[battery_name]["name_label"])
            battery_level_horizontal_container.append(self.battery_widgets[battery_name]["level_bar"])
            battery_level_horizontal_container.append(self.battery_widgets[battery_name]["Percentage"])
            battery_level_horizontal_container.append(self.battery_widgets[battery_name]["menu_button"])
            self.batterys_vertical_container.append(battery_level_horizontal_container)
        self.vertical_container.append(self.batterys_vertical_container)
        self.setup_power_profile_buttons()
        self.vertical_container.append(self.power_profile_container)

        

    def setup_battery_info(self):
        self.battery_info = self.battery.get_initial_battery_info()
        self.battery_widgets = {}
        for battery_name, info in self.battery_info.items():
            battery_level = info["Percentage"]
            battery_name_label = Gtk.Label()
            battery_name_label.get_style_context().add_class("battery-name")
            battery_name_label.set_label(f"{battery_name}")
            battery_icon = Gtk.Image.new_from_icon_name(self.get_battery_icon(int(info["Status"]), int(round(info["Percentage"]))))
            battery_icon.get_style_context().add_class("battery-icon")
            battery_level_label = Gtk.Label()
            battery_level_label.set_label(f"{round(battery_level)}%")
            battery_level_label.get_style_context().add_class("battery-level")
            level_bar = Gtk.LevelBar()
            level_bar.set_min_value(0.0)
            level_bar.set_max_value(100.0)
            level_bar.set_hexpand(True)
            level_bar.set_mode(Gtk.LevelBarMode.CONTINUOUS)
            level_bar.add_offset_value(Gtk.LEVEL_BAR_OFFSET_LOW, 20.0)
            level_bar.add_offset_value(Gtk.LEVEL_BAR_OFFSET_HIGH, 80.0)
            level_bar.add_offset_value(Gtk.LEVEL_BAR_OFFSET_FULL, 100.0)
            level_bar.set_value(float(battery_level))
            level_bar.get_style_context().add_class("battery-level-bar")
            menu_button = Gtk.Button()
            menu_button.connect("clicked", lambda x, name=battery_name: self.overlay_windows[f"{name}_revealer"].set_reveal_child(True))
            menu_button.get_style_context().add_class("battery-menu-button")
            menu_button_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic")
            menu_button.set_child(menu_button_icon)
            self.battery_widgets[battery_name] = {
                "Status": info["Status"],
                "icon": battery_icon,
                "name_label": battery_name_label,
                "Percentage": battery_level_label,
                "level_bar": level_bar,
                "menu_button": menu_button
            }
        return self.battery_widgets

    def setup_power_profile_buttons(self):
        self.power_profile_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.power_profile_container.get_style_context().add_class("power-profile-container")
        self.power_profile_container.set_homogeneous(True)
        self.power_profile_buttons = {}
        power_profiles = ["Performance", "Balanced", "Power Saver"]
        icons = {
            "Performance": "power-profile-performance-symbolic",
            "Balanced": "power-profile-balanced-symbolic",
            "Power Saver": "power-profile-power-saver-symbolic"
        }
        for profile in power_profiles:
            profile_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            button = Gtk.Button()
            button.get_style_context().add_class("power-profile-button")
            mode_icon = Gtk.Image.new_from_icon_name(icons[profile])
            mode_icon.get_style_context().add_class("power-profile-icon")
            profile_container.append(mode_icon)
            button_name = Gtk.Label(label=profile)
            button_name.get_style_context().add_class("power-profile-label")
            profile_container.append(button_name)
            button.set_child(profile_container)
            self.power_profile_buttons[profile] = button
            self.power_profile_container.append(button)
        self.performance_handler = self.power_profile_buttons["Performance"].connect("clicked", self.on_power_mode_switched, "performance")
        self.performance_handler = self.power_profile_buttons["Balanced"].connect("clicked", self.on_power_mode_switched, "balanced")
        self.performance_handler = self.power_profile_buttons["Power Saver"].connect("clicked", self.on_power_mode_switched, "power-saver")
        self.update_power_profile_buttons()
        self.power_profile_container.set_halign(Gtk.Align.CENTER)

    def update_power_profile_buttons(self):
        performance_button = self.power_profile_buttons["Performance"]
        balanced_button = self.power_profile_buttons["Balanced"]
        power_saver_button = self.power_profile_buttons["Power Saver"]
        active = self.powerprofile.get_active_profile()
        match active:
            case "power-saver":
                power_saver_button.get_style_context().add_class("active")
                balanced_button.get_style_context().remove_class("active")
                performance_button.get_style_context().remove_class("active")
            case "balanced":
                power_saver_button.get_style_context().remove_class("active")
                balanced_button.get_style_context().add_class("active")
                performance_button.get_style_context().remove_class("active")
            case "performance":
                power_saver_button.get_style_context().remove_class("active")
                balanced_button.get_style_context().remove_class("active")
                performance_button.get_style_context().add_class("active")     

    def setup_combined_battery_info(self):
        self.combined_battery_info = self.battery.get_initial_combined_battery_info()
        self.combined_battery_level = Gtk.Label()
        self.combined_battery_level.set_label(f"{round(self.combined_battery_info["level"])}%")
        self.combined_battery_level.get_style_context().add_class("combined-battery-level")
        self.level_bar.set_value(round(self.combined_battery_info["level"]))
        self.combined_battery_status = Gtk.Label()
        self.battery_status_codes = {
            0: "Unknown",
            1: "Charging",
            2: "Discharging",
            3: "Empty",
            4: "Fully Charged",
            5: "Pending Charge",
            6: "Pending Discharge"
        }
        self.combined_battery_status_code = self.combined_battery_info["status"]
        self.combined_battery_status.set_label(f"{self.battery_status_codes.get(self.combined_battery_info["status"])}")
        self.combined_battery_status.get_style_context().add_class("combined-battery-status")
        self.combined_icon = Gtk.Image.new_from_icon_name(self.get_battery_icon(int(self.combined_battery_info["status"]), int(round(self.combined_battery_info["level"]))))
        self.combined_icon.set_pixel_size(20)
        self.combined_icon.get_style_context().add_class("combined-battery-icon")
        self.combined_battery_time_to = Gtk.Label()
        self.combined_battery_time_to.get_style_context().add_class("time-to")
        if self.combined_battery_info["status"] == 2: #0: Unknown, 1: Charging, 2: Discharging, 3: Empty, 4: Fully charged, 5: Pending charge, 6: Pending discharge
            label = self.format_time(self.combined_battery_info["time_to_empty"], "Empty")
            self.combined_battery_time_to.set_label(f"{label}")
        elif self.combined_battery_info["status"] == 1:
            label =self.format_time(self.combined_battery_info["time_to_full"], "Full")
            self.combined_battery_time_to.set_label(f"{label}")
        elif self.combined_battery_info["status"] == 4:
            self.combined_battery_time_to.set_label("Fully charged")

    def get_battery_icon(self, status, level):
        icons = {}
        status = int(status)
        if status == 2 or status == 1 or status == 6:
            for i in range(10, 101, 10):
                if status == 2 or status == 6:
                    icons[i] = f"battery-level-{i}-symbolic"
                else:
                    icons[i] = f"battery-level-{i}-charging-symbolic"
            step = int(round(level / 10)) * 10
            if step == 100 and status == 1:
                return "battery-level-100-charged-symbolic"
            else:
                return icons[step]
        elif status == 4:
            return "battery-full-symbolic"
        elif status == 5:
            return "battery-level-0-symbolic"
        else:
            return "battery-missing-symbolic"

    def format_time(self, seconds, label):
        time_formated = str(timedelta(seconds=seconds))
        time_object = strptime(time_formated, "%H:%M:%S")
        if time_object.tm_hour > 0:
            time_to_formated = f"{label} in {time_object.tm_hour}h {time_object.tm_min}min"
        else:
            time_to_formated = f"{label} in {time_object.tm_min}min"
        return time_to_formated
    
    def on_power_mode_switched(self, button, mode):
        if mode != self.powerprofile.get_active_profile():
            self.powerprofile.set_power_profile(mode)

    def animate_on_present(self):
        target = int(round(self.battery.combined_battery_info("Percentage")))
        self.combined_battery_level.set_label("0%")
        self.animation_value = 0
        
        if hasattr(self, 'tick_id') and self.tick_id:
            return

        def manage_animation(widget, frame_clock):
            step = 2
            diff = target - self.animation_value
            if abs(diff) < step:
                self.combined_battery_level.set_label(f"{target}%")
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
        things_to_update_bat = ["Percentage", "State", "ChargeCycles", "TimeToEmpty", "TimeToFull"]
        for update in things_to_update_bat:
            if update in data:
                if battery != "DisplayDevice":
                    for battery_name in self.battery.batterys:
                        if battery_name == battery:
                            if update == "Percentage":
                                self.battery_widgets[battery_name]["Percentage"].set_label(f"{round(data["Percentage"])}%")
                                self.battery_widgets[battery_name]["level_bar"].set_value(float(round(data["Percentage"])))
                                self.battery_widgets[battery_name]["icon"].set_from_icon_name(f"{self.get_battery_icon(int(self.battery_widgets[battery_name]["Status"]), int(round(data["Percentage"])))}")
                            if update == "State":
                                self.battery_widgets[battery_name]["Status"] = data["State"]
                                self.battery_widgets[battery_name]["icon"].set_from_icon_name(f"{self.get_battery_icon(int(data["State"]), int(round(self.battery_widgets[battery_name]["level_bar"].get_value())))}")
                elif battery == "DisplayDevice":
                    if update == "Percentage":
                        if self.combined_battery_level.get_label() != f"{round(data["Percentage"])}%":
                            self.combined_battery_level.set_label(f"{round(data["Percentage"])}%")
                            self.level_bar.set_value(round(data["Percentage"]))
                            self.combined_icon.set_from_icon_name(f"{self.get_battery_icon(int(self.combined_battery_status_code), int(round(data["Percentage"])))}")
                    global _v_layer
                    if update == "TimeToEmpty":
                        if _v_layer.get_visible():
                            self.combined_battery_time_to.set_label(self.format_time(data["TimeToEmpty"], "Empty"))
                    if update == "TimeToFull":
                        if _v_layer.get_visible():
                            self.combined_battery_time_to.set_label(self.format_time(data["TimeToFull"], "Full"))
                    if update == "State":
                        self.combined_battery_status.set_label(f"{self.battery_status_codes.get(data["State"])}")
                        self.combined_battery_status_code = int(data["State"])
                        if data["State"] == 4:
                            self.combined_battery_time_to.set_label("Fully charged")

class HalfCircleLevelBar(Gtk.DrawingArea):
    def __init__(self, type="level"):
        super().__init__()
        self.type = type
        self.set_content_width(300)
        self.set_content_height(200)
        self.fraction = 0.5
        self.get_style_context().add_class("half-circle-bar")
        if self.type == "background":
            self.get_style_context().add_class("background")
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
        if self.type == "background":
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
        self.target = max(0.0, min(1.0, target_fraction))
        if hasattr(self, 'tick_id') and self.tick_id:
            return

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


class Battery:
    def __init__(self, callback=None):
        self.callback = callback
        batterys_path = "/sys/class/power_supply/BAT"
        self.updateables = []
        self.proxys = {}
        try:
            self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            self.batterys = {}
            for i in range(2):
                path = f"{batterys_path}{i}"
                if os.path.exists(path):
                    self.batterys[f"BAT{i}"] = path
            for battery_name in self.batterys:
                self.connect_to_upower(battery_name)
                self.updateables.append(battery_name)
                path = f"/org/freedesktop/UPower/devices/battery_{battery_name}"
                self.proxys[battery_name] = Gio.DBusProxy.new_sync(
                    self.bus,
                    Gio.DBusProxyFlags.NONE,
                    None,
                    "org.freedesktop.UPower",
                    path,
                    "org.freedesktop.UPower.Device",
                    None
                )
            self.connect_to_upower("DisplayDevice")
            self.updateables.append("DisplayDevice")
            self.proxys["DisplayDevice"] = Gio.DBusProxy.new_sync(
                self.bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.freedesktop.UPower",
                "/org/freedesktop/UPower/devices/DisplayDevice",
                "org.freedesktop.UPower.Device",
                None
            )
        except Exception as e:
            print(e)
        
    def combined_battery_info(self, property_name):
        try:
            variant = self.proxys["DisplayDevice"].get_cached_property(property_name)
            if variant:
                return variant.unpack()
            else:
                variant = self.proxys["DisplayDevice"].call_sync(
                    "org.freedesktop.DBus.Properties.Get",
                    GLib.Variant("(ss)", ("org.freedesktop.UPower.Device", property_name)),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None
                )
                if variant:
                    return variant.unpack()[0]
                return None

        except Exception as e:
            print(f"Error occurred while fetching combined {property_name}: {e}")
            return None

    def dbus_call(self, battery_name, property_name):
        try:
            variant = self.proxys[battery_name].get_cached_property(property_name)
            if variant:
                return variant.unpack()
            else:
                variant = self.proxys[battery_name].call_sync(
                    "org.freedesktop.DBus.Properties.Get",
                    GLib.Variant("(ss)", ("org.freedesktop.UPower.Device", property_name)),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None
                )
                if variant:
                    return variant.unpack()[0]
                return None

        except Exception as e:
            print(f"Error occurred while fetching {property_name} for {battery_name}: {e}")
            return None


    def connect_to_upower(self, battery_name):
        if battery_name != "DisplayDevice":
            name = f"battery_{battery_name}"
        else:
            name = battery_name
        self.connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.connection.signal_subscribe(
            "org.freedesktop.UPower",
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            f"/org/freedesktop/UPower/devices/{name}",
            None,
            Gio.DBusSignalFlags.NONE,
            self.on_battery_changed,
            None
        )


    def on_battery_changed(self, connection, sender, path, interface, signal, parameters, user_data):
        for battery in self.updateables:
            if battery in path:
                changed_properties = parameters.get_child_value(1).unpack()
                if len(changed_properties) > 1:
                    self.callback(battery, changed_properties)

    def get_initial_battery_info(self):
        batterys = {}
        try:
            for battery_name, battery_path in self.batterys.items():
                battery_level = self.dbus_call(battery_name, "Percentage")
                battery_status = self.dbus_call(battery_name, "State")
                charge_cycles = self.dbus_call(battery_name, "ChargeCycles")
                energy_full = self.dbus_call(battery_name, "EnergyFull")
                energy_full_design = self.dbus_call(battery_name, "EnergyFullDesign")
                vendor = self.dbus_call(battery_name, "Vendor")
                model = self.dbus_call(battery_name, "Model")
                batterys[battery_name] = {
                    "Percentage": battery_level,
                    "Status": battery_status,
                    "ChargeCycles": charge_cycles,
                    "EnergyFull": energy_full,
                    "EnergyFullDesign": energy_full_design,
                    "Vendor": vendor,
                    "Model": model
                }
            return batterys
                
        except Exception as e:
            print(f"Error occurred while fetching battery info: {e}")

    def get_initial_combined_battery_info(self):
        try:
            batterys = {}
            batterys["level"] = self.combined_battery_info("Percentage")
            batterys["status"] = self.combined_battery_info("State")
            batterys["time_to_empty"] = self.combined_battery_info("TimeToEmpty")
            batterys["time_to_full"] = self.combined_battery_info("TimeToFull")
            return batterys
                
        except Exception as e:
            print(f"Error occurred while fetching battery info: {e}")

class PowerProfiles:
    def __init__(self, callback):
        self.update_ui_elements = callback
        self.dbus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.dbus_path = "/net/hadess/PowerProfiles"
        self.bus_name = "net.hadess.PowerProfiles"
        self.object = "org.freedesktop.UPower.PowerProfiles"
        self.connect_to_dbus()
        self.proxy = Gio.DBusProxy.new_sync(
                self.dbus,
                Gio.DBusProxyFlags.NONE,
                None,
                self.bus_name,
                self.dbus_path,
                self.object,
                None
            )

    def connect_to_dbus(self):
        self.dbus.signal_subscribe(
            self.bus_name,
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            self.dbus_path,
            None,
            Gio.DBusSignalFlags.NONE,
            self.on_profile_changed,
            None
        )

    def set_power_profile(self, profile_name):
        
        parameters = GLib.Variant('(ssv)', (
            "net.hadess.PowerProfiles",
            "ActiveProfile",
            GLib.Variant('s', profile_name)
        ))

        try:
            self.dbus.call_sync(
                "net.hadess.PowerProfiles",
                "/net/hadess/PowerProfiles",
                "org.freedesktop.DBus.Properties",
                "Set",
                parameters,
                None,
                Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION,
                -1,
                None
            )
        except Exception as e:
            print(f"Error occured while changing profile: {e}")
        
    def get_active_profile(self):
        try:
            variant = self.proxy.get_cached_property("ActiveProfile")
            if variant:
                return variant.unpack()
            else:
                variant = self.proxy.call_sync(
                    "org.freedesktop.DBus.Properties.Get",
                    GLib.Variant("(ss)", (self.bus_name, "ActiveProfile")),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None
                )
                if variant:
                    return variant.unpack()[0]
                return None

        except Exception as e:
            print(f"Error occurred while fetching active powerprofile: {e}")
            return None

    def on_profile_changed(self, connection, sender, path, interface, signal, parameters, user_data):
        changed_properties = parameters.get_child_value(1).unpack()
        if "ActiveProfile" in changed_properties:
            new_active_profile = changed_properties["ActiveProfile"]
            self.update_ui_elements()

class PopupWindow:
    def __init__(self, main_window, battery):
        self.main_window = main_window
        self.battery = battery
        self.panel = Gtk.Frame()
        self.panel.add_css_class("floating-panel")
        self.panel.set_size_request(-1, 170)
        self.panel_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_start=20,
            margin_end=20,
            margin_top=20,
            margin_bottom=20
            )
        self.setup_ui()

    def setup_ui(self):
        close_btn = Gtk.Button()
        close_icon = Gtk.Image.new_from_icon_name("window-close-symbolic")
        close_btn.set_child(close_icon)
        close_btn.connect("clicked", lambda x, name=f"{self.battery}": self.main_window.overlay_windows[f"{name}_revealer"].set_reveal_child(False))
        close_btn.get_style_context().add_class("close-button")
        close_btn.set_halign(Gtk.Align.END)
        self.panel_content.append(close_btn)
        
        infos = self.get_overlay_window_values()
        main_horizontal_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        main_horizontal_container.set_homogeneous(True)
        parameters = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        values = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        available_parameters = ["Vendor", "Model", "Capacity", "Charge Cycles", "Energy Full", "Energy Design"]
        for parameter in available_parameters:
            parameter_label = Gtk.Label(label=f"{parameter}:")
            parameter_label.get_style_context().add_class("popup-parameter")
            parameters.append(parameter_label)
            parameter_label.set_halign(Gtk.Align.START)
            values_label = Gtk.Label(label=f"{infos[parameter]}")
            values.append(values_label)
            values_label.set_halign(Gtk.Align.END)
            values_label.get_style_context().add_class("popup-value")
        main_horizontal_container.append(parameters)
        main_horizontal_container.append(values)
        self.panel_content.append(main_horizontal_container)
        self.panel.set_child(self.panel_content)


    def get_overlay_window_values(self):
        battery_info = self.main_window.battery.get_initial_battery_info()[self.battery]
        cycle_count = battery_info["ChargeCycles"]
        energie_full = f"{battery_info["EnergyFull"]}Wh"
        energie_full_design = f"{battery_info["EnergyFullDesign"]}Wh"
        state_of_battery = f"{round((float(battery_info["EnergyFull"]) / float(battery_info["EnergyFullDesign"]) * 100))}%"
        vendor = f"{battery_info["Vendor"]}"
        model = f"{battery_info["Model"]}"
        info = {
            "Vendor": vendor,
            "Model": model,
            "Capacity": state_of_battery,
            "Charge Cycles": cycle_count,
            "Energy Full": energie_full,
            "Energy Design": energie_full_design
        }
        return info
        

def on_present():
    global _v_layer
    current_level = _v_layer.level_bar.fraction
    _v_layer.level_bar.set_value(0)
    _v_layer.level_bar.animate_to_value(current_level)
    _v_layer.animate_on_present()

def init_layer(config):
    global _v_layer
    if _v_layer is None:
        _v_layer = BatteryLayer(config)
        _v_layer.connect("close-request", lambda w, e: w.hide() or True)

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