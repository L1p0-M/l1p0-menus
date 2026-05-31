import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import GLib, Gio

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
            self.dbus.call(
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