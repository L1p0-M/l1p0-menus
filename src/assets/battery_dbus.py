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
            if self.batterys == {}:
                raise RuntimeError("No batteries found")
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
            raise RuntimeError(f"Failed to initialize Battery: {e}")

    def dbus_call(self, battery_name="DisplayDevice", property_name=None):
        try:
            if property_name is None:
                print("Property name is required for dbus_call")
                return None
            self.proxys[battery_name].call(
                "org.freedesktop.DBus.Properties.Get",
                GLib.Variant("(ss)", ("org.freedesktop.UPower.Device", property_name)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                self._on_dbus_call_finished,
                battery_name, property_name
            )
            return None

        except Exception as e:
            print(f"Error occurred while fetching {property_name} for {battery_name}: {e}")
            return None
        
    def _on_dbus_call_finished(self, proxy, result, battery_name, property_name):
        try:
            variant = proxy.call_finish(result)
            if variant:
                if property_name in ["TimeToEmpty", "TimeToFull"]:
                    if variant.unpack()[0] == 0:
                        return
                GLib.idle_add(self.callback, battery_name, {property_name: variant.unpack()[0]})
        except Exception as e:
            print(f"Error occurred while getting Battery DBus call results: {e}")


    def connect_to_upower(self, battery_name):
        if battery_name != "DisplayDevice":
            name = f"battery_{battery_name}"
        else:
            name = battery_name
        self.bus.signal_subscribe(
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
            props_to_get = ["State", "Percentage", "ChargeCycles", "EnergyFull", "EnergyFullDesign", "Vendor", "Model"]
            for battery_name, battery_path in self.batterys.items():
                for prop in props_to_get:
                    self.dbus_call(battery_name=battery_name, property_name=prop)
                
        except Exception as e:
            print(f"Error occurred while fetching battery info: {e}")

    def get_initial_combined_battery_info(self):
        try:
            props_to_get = ["State", "Percentage", "TimeToEmpty", "TimeToFull", "EnergyRate"]
            for prop in props_to_get:
                self.dbus_call(battery_name="DisplayDevice", property_name=prop)
                
        except Exception as e:
            print(f"Error occurred while fetching battery info: {e}")



class PowerProfiles:
    def __init__(self, callback):
        self.callback = callback
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
            self.proxy.call(
                "org.freedesktop.DBus.Properties.Get",
                GLib.Variant("(ss)", (self.bus_name, "ActiveProfile")),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                self._on_dbus_call_finished,
                None
            )
            return None

        except Exception as e:
            print(f"Error occurred while fetching active powerprofile: {e}")
            return None

    def on_profile_changed(self, connection, sender, path, interface, signal, parameters, user_data):
        changed_properties = parameters.get_child_value(1).unpack()
        if "ActiveProfile" in changed_properties:
            new_active_profile = changed_properties["ActiveProfile"]
            GLib.idle_add(self.callback, {"active_profile": new_active_profile})
    
    def _on_dbus_call_finished(self, proxy, result, user_data):
        try:
            variant = proxy.call_finish(result)
            if variant:
                GLib.idle_add(self.callback, {"active_profile": variant.unpack()[0]})
        except Exception as e:
            print(f"Error occurred while getting PowerProfiles DBus call results: {e}")