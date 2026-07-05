import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import GLib, Gio
import subprocess



class DbusBluez:
    def __init__(self, callback):
        self.callback = callback
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.bluetooth_devices = {}
        self._device_proxy = {}
        self.bluez_proxy = None
        self._connecting_to = None
        self.adapter_object_path = None
        self._get_bluez_objects()

        if self.callback is not None:
            self._subscribe_to_changes()
        
    def _subscribe_to_changes(self):
        self.bus.signal_subscribe(
            "org.bluez",
            None,
            None,
            None,
            None,
            Gio.DBusSignalFlags.NONE,
            self.update_on_dbus,
            None
        )
        
    def get_bluetooth_infos(self):
        name = self.bluez_proxy.get_cached_property("Alias")
        name = name.unpack() if name is not None else self._get_property_forced(proxy=self.bluez_proxy, interface="org.bluez.Adapter1", prop_name="Alias")

        powered = self.bluez_proxy.get_cached_property("Powered")
        powered = powered.unpack() if powered is not None else self._get_property_forced(proxy=self.bluez_proxy, interface="org.bluez.Adapter1", prop_name="Powered")

        discover = self.bluez_proxy.get_cached_property("Discoverable")
        discover = discover.unpack() if discover is not None else self._get_property_forced(proxy=self.bluez_proxy, interface="org.bluez.Adapter1", prop_name="Discoverable")

        pairable = self.bluez_proxy.get_cached_property("Pairable")
        pairable = pairable.unpack() if pairable is not None else self._get_property_forced(proxy=self.bluez_proxy, interface="org.bluez.Adapter1", prop_name="Pairable")
    
        discoverable_timeout = self.bluez_proxy.get_cached_property("DiscoverableTimeout")
        discoverable_timeout = discoverable_timeout.unpack() if discoverable_timeout is not None else self._get_property_forced(proxy=self.bluez_proxy, interface="org.bluez.Adapter1", prop_name="DiscoverableTimeout")

        return {
            "Alias": name,
            "Powered": powered,
            "Discoverable": discover,
            "Pairable": pairable,
            "DiscoverableTimeout": discoverable_timeout
        }

    def toggle_bluetooth(self, switch, state):
        subprocess.Popen(f"rfkill {'unblock' if state else 'block'} bluetooth", shell=True)
        if not state:
            self.bluez_proxy = None
            self.adapter_object_path = None
        if state:
            GLib.timeout_add_seconds(3, self._get_bluez_objects)


    def toggle_discoverable(self, switch, state):
        if not self.bluez_proxy:
            proxy_available = self._get_adapter_proxy()
            if not proxy_available:
                return
        self._set_bluez_property("Discoverable", state, "b")

    def set_dicoverable_timeout(self, timeout:int):
        if not self.bluez_proxy:
            proxy_available = self._get_adapter_proxy()
            if not proxy_available:
                return
        self._set_bluez_property("DiscoverableTimeout", timeout, "u")
        GLib.idle_add(self.callback, {"adapter": {"DiscoverableTimeout": timeout}})

    def set_name(self, name:str):
        if not self.bluez_proxy:
            proxy_available = self._get_adapter_proxy()
            if not proxy_available:
                return
        self._set_bluez_property("Alias", name, "s")
        GLib.idle_add(self.callback, {"adapter": {"Alias": name}})

    def toggle_trusted(self, address, switch, state):
        if address not in self._device_proxy:
            self._get_device_proxy(address)
        self._set_bluez_property("Trusted", state, "b", "org.bluez.Device1", self._device_proxy[address])

    def forget_device(self, address):
        if not self.bluez_proxy:
            proxy_available = self._get_adapter_proxy()
            if not proxy_available:
                return
            
        self.bluez_proxy.call(
            "RemoveDevice",
            GLib.Variant('(o)', [f"{self.adapter_object_path}/dev_{address.replace(':', '_')}"]),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            None,
            None
        )
        
    def connect_disconnect_to_device(self, address, method="Connect"):
        if address not in self._device_proxy:
            self._get_device_proxy(address)
        self._connecting_to = address
        self._device_proxy[address].call(
            method,
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            self._update_ui_after_connect,
            address
        )

    def discovery(self, value):
        method = "StartDiscovery" if value else "StopDiscovery"
        if self.bluez_proxy is None:
            proxy_available = self._get_adapter_proxy()
            if not proxy_available:
                return
        self.bluez_proxy.call(
            method,
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            None,
            None
        )

    def get_connected_battery(self, mac):
        address_formated = mac.replace(":", "_")
        battery_proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.bluez",
            f"{self.adapter_object_path}/dev_{address_formated}",
            "org.bluez.Battery1",
            None
        )
        cached = battery_proxy.get_cached_property("Percentage")
        battery_percentage = cached.unpack() if cached is not None else None
        if battery_percentage is None:
            battery_percentage = self._get_property_forced(
                    battery_proxy,
                    "org.bluez.Battery1",
                    "Percentage"
                )
        return battery_percentage


    def _get_device_proxy(self, address):
        if self.adapter_object_path and address not in self._device_proxy:
            address_formated = address.replace(":", "_")
            self._device_proxy[address] = Gio.DBusProxy.new_sync(
                self.bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.bluez",
                f"{self.adapter_object_path}/dev_{address_formated}",
                "org.bluez.Device1",
                None
        )

    def _get_adapter_proxy(self):
        if self.adapter_object_path is None:
            return None
        self.bluez_proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.bluez",
            self.adapter_object_path,
            "org.bluez.Adapter1",
            None
        )
        return True

    def _get_bluez_objects(self):    
        proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.bluez",
            "/",
            "org.freedesktop.DBus.ObjectManager",
            None
        )
        try:
            proxy.call(
                "GetManagedObjects",
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                self._setup_devices,
                None
            )
            return False
        except Exception as e:
            print(f"error getting bluez objects: {e}")
            return True
        

    def _setup_devices(self, source_object, res, user_data): 
        self.bluetooth_devices = {} 
        result = source_object.call_finish(res)
        if result:
            nodes = result.unpack()[0]
            if not any('org.bluez.Adapter1' in subdict for subdict in nodes.values()):
                GLib.timeout_add_seconds(5, self._get_bluez_objects)
                return
            print("Found bluetooth adapter, setting up devices...")
            for path, interfaces in nodes.items():
                if "org.bluez.Adapter1" in interfaces:
                    self.adapter_object_path = path
                    if self.adapter_object_path:
                        if not self.bluez_proxy:
                            self._get_adapter_proxy()
                        infos = self.get_bluetooth_infos()
                        GLib.idle_add(self.callback, {"adapter": infos})
                elif "org.bluez.Device1" in interfaces:
                    device = interfaces["org.bluez.Device1"]
                    self._add_device_to_dict(device)
                    if device["Address"] is not None:
                        self._get_device_proxy(device["Address"])
            if self.bluetooth_devices:
                GLib.idle_add(self.callback, {"devices": self.bluetooth_devices})

    def _add_device_to_dict(self, device):
        if "Name" in device:
            self.bluetooth_devices[device["Name"]] = {
                "icon": device["Icon"] if "Icon" in device else "bluetooth",
                "name": device["Name"],
                "paired": device["Paired"],
                "trusted": device["Trusted"],
                "blocked": device["Blocked"],
                "connected": device["Connected"],
                "address": device["Address"]
            }
            return self.bluetooth_devices[device["Name"]]
        else:
            return None


    def _set_bluez_property(self, property_name, value, value_type, interface="org.bluez.Adapter1", proxy=None):
        variant_value = GLib.Variant(value_type, value)
        variant_params = GLib.Variant('(ssv)', [
            interface, 
            property_name, 
            variant_value
        ])
        if proxy is None:
            if self.bluez_proxy is None:
                proxy_available = self._get_adapter_proxy()
                if not proxy_available:
                    return
            proxy = self.bluez_proxy
        proxy.call(
            "org.freedesktop.DBus.Properties.Set",
            variant_params,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            None,
            None
        )

    def _update_ui_after_connect(self, source_object, res, user_data):
        try:
            result = source_object.call_finish(res)
        except Exception as e:
            print(f"error on connect... {e}")
            GLib.idle_add(self.callback, {"connection": user_data, "message": {"Connected": False}})

    def update_on_dbus(self, connection, sender_name, object_path, interface_name, signal_name, parameters, user_data):
        parameter = parameters.unpack()
        #print(interface_name)
        #print(parameter)
        #print(object_path)
        #print(signal_name)

        if signal_name == "PropertiesChanged":
            if "org.bluez.Device1" in parameter:
                if f"{self.adapter_object_path}/dev_" in object_path:
                    mac = self._path_to_mac(object_path)
                    if "Connected" in parameter[1]:
                        GLib.idle_add(self.callback, {"connection": mac, "message": parameter[1]})
                    elif "Trusted" in parameter[1]:
                        GLib.idle_add(self.callback, {"trusted": mac, "message": parameter[1]})
                    elif "Paired" in parameter[1]:
                        GLib.idle_add(self.callback, {"paired": mac, "message": parameter[1]})
            elif "org.bluez.Adapter1" in parameter:
                if isinstance(parameter[1], dict):
                    adapter_params = ["DiscoverableTimeout", "Discoverable", "Powered", "Alias", "Discovering"]
                    if any(param in parameter[1] for param in adapter_params):
                        GLib.idle_add(self.callback, {"adapter": parameter[1]})

        elif signal_name == "InterfacesAdded":
            if isinstance(parameter[1], dict):
                if "org.bluez.Device1" in parameter[1]:
                    dev_props = parameter[1]["org.bluez.Device1"]
                    if "Name" in dev_props:
                        distilled_infos = self._add_device_to_dict(dev_props)
                        GLib.idle_add(self.callback, {"added_device": distilled_infos})

                if "org.bluez.Battery1" in parameter[1]:
                    device_path = parameter[0]
                    if "Percentage" in parameter[1]["org.bluez.Battery1"]:
                        battery = parameter[1]["org.bluez.Battery1"]["Percentage"]
                        mac = self._path_to_mac(device_path)
                        GLib.idle_add(self.callback, {"device": mac, "battery": battery})
        
        elif signal_name == "InterfacesRemoved":
            to_remove = None
            path, interfaces = parameter
            if "org.bluez.Device1" not in interfaces:
                return
            mac = self._path_to_mac(path)
            for name, items in self.bluetooth_devices.items():
                if items['address'] == mac:
                    to_remove = name
                    break
            if to_remove is not None:
                del self.bluetooth_devices[to_remove]
                GLib.idle_add(self.callback, {"removed_device": to_remove})
    




    def _path_to_mac(self, path):
        mac = (path.replace(f"{self.adapter_object_path}/dev_", "").replace("_", ":"))
        return mac

    def _get_property_forced(self, proxy, interface, prop_name):
        try:
            variant = proxy.call_sync(
                "org.freedesktop.DBus.Properties.Get",
                GLib.Variant("(ss)", (interface, prop_name)),
                Gio.DBusCallFlags.NONE, -1, None
            )
            return variant.unpack()[0]
        except Exception:
            return None