import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib, Gio

class WifiDbus:
    def __init__(self, callback=None):
        self.callback = callback
        self.update_to_none = False
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self._get_nm_proxy()
        self._get_device_proxy()
        self._get_settings_proxy()
        self._get_ethernet_device_proxy()
        self.ipv4_proxy = {}

        if self.callback is not None:
            self._subscribe_to_changes()
        
    def _subscribe_to_changes(self):
        self.bus.signal_subscribe(
            "org.freedesktop.NetworkManager",
            None,
            None,
            None,
            None,
            Gio.DBusSignalFlags.NONE,
            self.update_on_dbus,
            None
        )

    def get_wifi_networks_data(self):
        return self._get_available_networks()

    def _get_wifi_path(self): 
        devices = self.nm_proxy.GetDevices()
        for path in devices:
            dev_proxy = Gio.DBusProxy.new_sync(
                self.bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.freedesktop.NetworkManager",
                path,
                "org.freedesktop.NetworkManager.Device",
                None
            )
            dev_type = dev_proxy.get_cached_property("DeviceType").unpack()
            if dev_type == 2: # 2 = NM_DEVICE_TYPE_WIFI
                self.wifi_path = path
            if dev_type == 1: # 1 = NM_DEVICE_TYPE_ETHERNET
                self.ethernet_path = path
        return None
    
    def _get_nm_proxy(self):
            self.nm_proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager",
            "org.freedesktop.NetworkManager",
            None
        )
    
    def _get_device_proxy(self):
        self._get_wifi_path()
        if self.wifi_path:
            self._get_wifi_proxy(self.wifi_path)
            self.dev_proxy = Gio.DBusProxy.new_sync(
                self.bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.freedesktop.NetworkManager",
                self.wifi_path,
                "org.freedesktop.NetworkManager.Device",
                None
            )

    def _get_ethernet_device_proxy(self):
        if self.ethernet_path:
            self._get_ethernet_proxy(self.ethernet_path)
            self._get_wifi_proxy(self.wifi_path)
            self.ethernet_dev_proxy = Gio.DBusProxy.new_sync(
                self.bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.freedesktop.NetworkManager",
                self.ethernet_path,
                "org.freedesktop.NetworkManager.Device",
                None
            )

    def _get_ethernet_proxy(self, path):
        self.ethernet_device_proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.NetworkManager",
            path,
            "org.freedesktop.NetworkManager.Device.Wired",
            None
        )

    def _get_wifi_proxy(self, path):
        self.device_proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.NetworkManager",
            path,
            "org.freedesktop.NetworkManager.Device.Wireless",
            None
        )

    def _get_connection_proxy(self, connection_path):
        connection_proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.NetworkManager",
            connection_path,
            "org.freedesktop.NetworkManager.Settings.Connection",
            None
        )
        return connection_proxy
    
    def _get_settings_proxy(self):
        self.settings_proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager/Settings",
            "org.freedesktop.NetworkManager.Settings",
            None
        )

    def _get_ipv4_proxy(self, path):
        if not path in self.ipv4_proxy.keys():
            self.ipv4_proxy[path] = Gio.DBusProxy.new_sync(
                self.bus,
                Gio.DBusProxyFlags.NONE,
                None,
                "org.freedesktop.NetworkManager",
                path,
                "org.freedesktop.NetworkManager.IP4Config",
                None
            )
    
    def get_ethernet_speed(self):
        if self.ethernet_device_proxy:
            return self.ethernet_device_proxy.get_cached_property("Speed").unpack()

    def get_active_network_details(self):
        details = {}
        if self.device_proxy:
            propertys = ["Bitrate", "HwAddress"]
            for prop in propertys:
                prop_value = self.device_proxy.get_cached_property(prop).unpack()
                if prop_value is None:
                    prop_value = self._get_property_forced(
                        self.device_proxy,
                        "org.freedesktop.NetworkManager.Device.Wireless",
                        prop
                    )
                if prop_value is not None:
                    if prop == "Bitrate":
                        prop_value = f"{int(int(prop_value) / 1000)} Mb/s"
                else:
                    prop_value = "N/A"
                details[prop] = prop_value

        if self.dev_proxy:
            ipv4config = self.dev_proxy.get_cached_property("Ip4Config").unpack()
            if ipv4config is None:
                ipv4config = self._get_property_forced(
                    self.dev_proxy,
                    "org.freedesktop.NetworkManager.Device",
                    "Ip4Config"
                )
            if not ipv4config in self.ipv4_proxy.keys():
                self._get_ipv4_proxy(ipv4config)
        if self.ipv4_proxy[ipv4config]:
            propertys = ["Gateway", "AddressData", "NameserverData"]
            for prop in propertys:
                prop_value = self.ipv4_proxy[ipv4config].get_cached_property(prop).unpack()
                if prop_value is None:
                    prop_value = self._get_property_forced(
                        self.ipv4_proxy[ipv4config],
                        "org.freedesktop.NetworkManager.IP4Config",
                        prop
                    )
                no_value = [None, [], ""]
                if prop_value not in no_value:
                    if prop == "AddressData" or prop == "NameserverData":
                        prop_value = prop_value[0]["address"]
                else:
                    prop_value = "N/A"
                details[prop] = prop_value
        return details



    def _get_network_details(self, ap_path):
        try:
            res = self.bus.call_sync(
                "org.freedesktop.NetworkManager",
                ap_path,
                "org.freedesktop.DBus.Properties",
                "GetAll",
                GLib.Variant('(s)', ["org.freedesktop.NetworkManager.AccessPoint"]),
                GLib.VariantType.new("(a{sv})"),
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )
        
            unpacked_data = res.unpack()[0]
        
            ssid_variant = unpacked_data.get("Ssid")
            ssid = self._decode_ssid(ssid_variant) if ssid_variant else "Unknown"
            if ssid == "Unknown":
                return
            strength = int(unpacked_data.get("Strength", 0))
        
            wpa_flags = unpacked_data.get("WpaFlags", 0)
            rsn_flags = unpacked_data.get("RsnFlags", 0)
            is_secured = (wpa_flags != 0 or rsn_flags != 0)

            return {
                "ssid": ssid,
                "strength": strength,
                "secured": is_secured,
                "wpa_flags": wpa_flags if wpa_flags != 0 else None,
                "rsn_flags": rsn_flags if rsn_flags != 0 else None,
                "flags": unpacked_data.get("Flags", 0),
                "path": ap_path
            }
        
        except GLib.Error as e:
            if "UnknownMethod" not in e.message and "UnknownObject" not in e.message:
                print(f"Error getting data from ({ap_path}): {e}")
            return None
    
    def _get_available_networks(self, ap_paths=None):
        unique_networks = {}
        if ap_paths == None:
            ap_paths = self.device_proxy.GetAllAccessPoints()
        for path in ap_paths:
            details = self._get_network_details(path)
            if details is not None:
                if details["ssid"] not in unique_networks or details["strength"] > unique_networks[details["ssid"]]["strength"]:
                    unique_networks[details["ssid"]] = details
        return unique_networks
    
    def get_active_networks(self):
        self.active_connections = {}
        active_connections = self.nm_proxy.get_cached_property("ActiveConnections").unpack()
        for path in active_connections:
            active_proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.NetworkManager",
            path,
            "org.freedesktop.NetworkManager.Connection.Active",
            None
            )
            connection_path = active_proxy.get_cached_property("Connection").unpack()
            conn_type = active_proxy.get_cached_property("Type").unpack()

            if connection_path is None or conn_type is None:
                connection_path = self._get_property_forced(
                    active_proxy,
                    "org.freedesktop.NetworkManager.Connection.Active",
                    "Connection"
                ).unpack()
                conn_type = self._get_property_forced(
                    active_proxy,
                    "org.freedesktop.NetworkManager.Connection.Active",
                    "Type"
                ).unpack()

            if not connection_path or not conn_type:
                continue

            if conn_type == "802-3-ethernet":
                proxy = self._get_connection_proxy(connection_path)
                settings = proxy.call_sync("GetSettings", None, Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
                connection_id = settings["connection"]["id"]
                self.active_connections["wired"] = {
                    "path": path,
                    "id": connection_id,
                }

            elif conn_type == "802-11-wireless":
                proxy = self._get_connection_proxy(connection_path)
                settings = proxy.call_sync("GetSettings", None, Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
                ssid_bytes = settings['802-11-wireless']['ssid']
                ssid = self._decode_ssid(ssid_bytes)
                self.active_connections[ssid] = path
        return self.active_connections
                

    def request_scan(self):
        try:
            self.device_proxy.call(
                "RequestScan",
                GLib.Variant('(a{sv})', [{}]),
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )
        except Exception as e:
            print(f"Error while rescan: {e}")

    def deactivate_connection(self, type="wifi"):
        try:
            if type == "wifi":
                proxy = self.dev_proxy
            elif type == "ethernet":
                proxy = self.ethernet_dev_proxy
            if proxy:
                proxy.call_sync(
                    "Disconnect",
                    None,
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None
                )
        except Exception as e:
            print(f"Error while deactivating: {e}")

    def activate_connection(self, network):
        try:
            ssid = network["ssid"]
            ap_path = network["path"]
            saved_networks = self.get_saved_connections()
            if ssid in saved_networks:
                self.nm_proxy.ActivateConnection(
                    '(ooo)',
                    saved_networks[ssid]["path"],
                    "/",
                    ap_path
            )
            else:
                rsn = network["rsn_flags"]
                wpa = network["wpa_flags"]
                security = None
                if network["flags"] >= 1:
                    if rsn is not None and rsn != 0:
                        security = {"management": "wpa-psk", "key": "open"}
                    else:
                        security = {"management": "none", "key": "wep-key0"}
                connection_settings = {
                    'connection': {
                        'type': GLib.Variant('s', '802-11-wireless'),
                        'id': GLib.Variant('s', ssid),
                        'autoconnect': GLib.Variant('b', True)
                    },
                    '802-11-wireless': {
                        'ssid': GLib.Variant('ay', list(ssid.encode())),
                        'mode': GLib.Variant('s', 'infrastructure')
                    },
                }

                if security:
                    connection_settings['802-11-wireless-security'] = {
                            'key-mgmt': GLib.Variant('s', security["management"])
                        }

                self.nm_proxy.call(
                    "AddAndActivateConnection",
                    GLib.Variant("(a{sa{sv}}oo)", (connection_settings, self.wifi_path, ap_path)),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None,
                    self.on_saved_updated,
                    None
                )
        except Exception as e:
            print(f"Error while connecting to network: {e}")

    def toggle_network(self, toggle, state):
        self._block_update(state)
        self._call_nm_proxy("Enable", GLib.Variant('(b)', [toggle.get_active()]))

    def toggle_wifi(self, toggle, state):
        self._block_update(state)
        self._set_nm_property("WirelessEnabled", GLib.Variant('b', toggle.get_active()))

    def get_wifi_status(self):
        wifistatus = self.nm_proxy.get_cached_property("WirelessEnabled")
        if wifistatus is None:
            wifistatus = self._get_property_forced(
                    self.nm_proxy,
                    "org.freedesktop.NetworkManager",
                    "WirelessEnabled"
                ).unpack()
        return wifistatus

    def _block_update(self, toggle):
        if toggle == False:
            self.update_to_none = True
        else:
            self.update_to_none = False

    def forget_network(self, path):
        try:
            connection = self._get_connection_proxy(path)
            connection.call(
                "Delete",
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                self.on_saved_updated,
                None,
            )
        except Exception as e:
            print(f"Error while deleting saved connection: {e}")

    def on_saved_updated(self, *args):
        self.callback({"saved_networks": []})

    def update_autoconnect(self, path, autoconnect):
        try:
            connection = self._get_connection_proxy(path)
            raw_settings = self._get_settings(path).get_child_value(0)
            rebuilt = {}
            for i in range(raw_settings.n_children()):
                entry = raw_settings.get_child_value(i)
                section_name = entry.get_child_value(0).get_string()
                section_dict = entry.get_child_value(1)
                
                props = {}
                for j in range(section_dict.n_children()):
                    prop = section_dict.get_child_value(j)
                    key = prop.get_child_value(0).get_string()
                    variant_wrapper = prop.get_child_value(1)
                    
                    if section_name == 'connection' and key == 'autoconnect':
                        props[key] = GLib.Variant('b', autoconnect)
                    else:
                        props[key] = variant_wrapper.get_child_value(0)
                
                rebuilt[section_name] = props
            if 'autoconnect' not in rebuilt.get('connection', {}):
                rebuilt['connection']['autoconnect'] = GLib.Variant('b', autoconnect)
            
            updated = GLib.Variant('(a{sa{sv}})', (rebuilt,))
            
            connection.call(
                'Update',
                updated,
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                None,
                None
            )

        except Exception as e:
            print(f"Error while updateing autoconnect: {e}")

    def update_on_dbus(self, connection, sender_name, object_path, interface_name, signal_name, parameters, user_data):
        parameter = parameters.unpack()
        if not isinstance(parameter, (list, tuple)) or len(parameter) < 2:
            return
        #print(f"Signal received: {signal_name} from {sender_name} at {object_path}")
        #print(f"{parameter}")
        if "org.freedesktop.NetworkManager.Device" in str(parameter[0]):
            props = parameter[1]
            if "State" in props:
                state = props["State"]
                active_path = self._get_property_forced(self.dev_proxy, 
                                "org.freedesktop.NetworkManager.Device", "ActiveConnection")
                activating_path = self._get_property_forced(self.dev_proxy, 
                                "org.freedesktop.NetworkManager.Device", "ActivatingConnection")
                target_path = activating_path if activating_path != "/" else active_path
                if 40 <= state <= 90:
                    GLib.idle_add(self.callback, {"status_update": target_path, "status": "preparing", "state_code": state})
                elif state == 100 or state == 110:
                    GLib.idle_add(self.callback, {"status_update": target_path, "status": "connected", "state_code": state})
                elif state == 30 or state == 120:
                    GLib.idle_add(self.callback, {"status_update": target_path, "status": "disconnected", "state_code": state})

        if "org.freedesktop.NetworkManager.Device.Wireless" in str(parameter[0]):
            if "AccessPoints" in str(parameter[1]):
                if not self.update_to_none:
                    GLib.timeout_add(500, self._delayed_network_update)
                else:
                    GLib.idle_add(self.callback, {"available_networks": []})

        elif "org.freedesktop.NetworkManager.AccessPoint" in str(parameter[0]):
            props = parameter[1] if len(parameter) > 1 else {}
            if "Strength" in props:
                GLib.idle_add(self.callback, {"updated_network": object_path, "strength": props['Strength']})

    def _delayed_network_update(self):
        try:
            ap_paths = self.device_proxy.GetAllAccessPoints()
            wifis = self._get_available_networks(ap_paths)
            GLib.idle_add(self.callback, {"available_networks": wifis})
        except Exception as e:
            print(f"Error while network update: {e}")
        return False

    def _call_nm_proxy(self, method, value):
        self.nm_proxy.call(
            method,
            value,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            None,
            None,
        )

    def _set_nm_property(self, property_name, value):
        variant_params = GLib.Variant('(ssv)', [
            "org.freedesktop.NetworkManager", 
            property_name, 
            value
        ])
    
        self.nm_proxy.call(
            "org.freedesktop.DBus.Properties.Set",
            variant_params,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            None,
            None,
        )

    def get_saved_connections(self):
        saved_ssids = {}
        connection_paths = self.settings_proxy.call_sync(
            "ListConnections",
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )
        paths = connection_paths.unpack()[0]

        for path in paths:
            settings = self._get_settings(path).unpack()[0]
            if settings["connection"]["type"] == "802-11-wireless":
                ssid_bytes = settings['802-11-wireless']['ssid']
                ssid = self._decode_ssid(ssid_bytes)
                if "autoconnect" in settings["connection"]: 
                    autoconnect = settings["connection"]["autoconnect"]
                else:
                    autoconnect = True
                saved_ssids[ssid] = {
                    "path": path,
                    "autoconnect": autoconnect
                }
        return saved_ssids
    
    def _get_settings(self, path):
        proxy = self._get_connection_proxy(path)
        settings = proxy.call_sync(
            "GetSettings",
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None)
        return settings

                
    def _get_property_forced(self, proxy, interface, prop_name):
        try:
            variant = proxy.call_sync(
                "org.freedesktop.DBus.Properties.Get",
                GLib.Variant("(ss)", (interface, prop_name)),
                Gio.DBusCallFlags.NONE, -1, None
            )
            return variant.unpack()[0]
        except Exception:
            return "/" if "Connection" in prop_name else None
        
    def _decode_ssid(self, ssid_bytes):
        return bytes(ssid_bytes).decode('utf-8', errors='replace')
