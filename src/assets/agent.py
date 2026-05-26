import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import GLib, Gio



class SecretAgent:
    AGENT_INTERFACE = "org.freedesktop.NetworkManager.SecretAgent"
    BLUEZ_AGENT_INTERFACE = "org.bluez.Agent1"
    AGENT_MANAGER_PATH = "/org/freedesktop/NetworkManager/AgentManager"
    BLUEZ_AGENT_MANAGER_PATH = "/org/bluez"
    AGENT_MANAGER_INTERFACE = "org.freedesktop.NetworkManager.AgentManager"
    BLUEZ_AGENT_MANAGER_INTERFACE = "org.bluez.AgentManager1"
    AGENT_ID = "com.freedesktop.l1p0menus.secretagent"
    AGENT_PATH = "/org/freedesktop/NetworkManager/SecretAgent"
    BLUEZ_AGENT_PATH = "/com/freedesktop/l1p0menus/btagent"
    
    def __init__(self, password_callback, wifidbus, bt_callback=None):
        self.password_callback = password_callback
        self.wifidbus = wifidbus
        self.bt_callback = bt_callback
        self.pending_requests = {}
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.registration_id = None
        self.bt_registration_id = None
        
    def register(self):
        agents = ["networkmanager", "bluez"]

        for agent in agents:
            if agent == "networkmanager":
                interface = self.AGENT_INTERFACE
                agent_path = self.AGENT_PATH
                agent_manager_path = self.AGENT_MANAGER_PATH
                agent_manager_interface = self.AGENT_MANAGER_INTERFACE
                base_dbus = "org.freedesktop.NetworkManager"
                reg_id = self.registration_id
                handle_call = self._handle_method_call
                register_function = self.register_nm_agent
                
            elif agent == "bluez":
                interface = self.BLUEZ_AGENT_INTERFACE
                agent_path = self.BLUEZ_AGENT_PATH
                agent_manager_path = self.BLUEZ_AGENT_MANAGER_PATH
                agent_manager_interface = self.BLUEZ_AGENT_MANAGER_INTERFACE
                base_dbus = "org.bluez"
                reg_id = self.bt_registration_id
                handle_call = self._handle_bt_method_call
                register_function = self.register_bluez_agent

            introspection_xml = self._get_introspection_xml(agent)
            node_info = Gio.DBusNodeInfo.new_for_xml(introspection_xml)
            interface_info = node_info.lookup_interface(interface)

            reg_id = self.bus.register_object(
                agent_path,
                interface_info,
                handle_call,
                None,
                None
            )

            agent_manager = Gio.DBusProxy.new_sync(
                self.bus,
                Gio.DBusProxyFlags.NONE,
                None,
                base_dbus,
                agent_manager_path,
                agent_manager_interface,
                None
            )
            register_function(agent_manager=agent_manager)
        
    def register_nm_agent(self, agent_manager):
        try:
            agent_manager.call_sync(
                "Register",
                GLib.Variant("(s)", (self.AGENT_ID,)),
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )
            print(f"Secret agent registered: {self.AGENT_ID}")
        except Exception as e:
            print(f"Failed to register agent: {e}")
            raise
            
    def _handle_method_call(self, connection, sender, object_path, 
                           interface_name, method_name, parameters, invocation):

        if method_name == "GetSecrets":
            self._handle_get_secrets(parameters, invocation)
        elif method_name == "CancelGetSecrets":
            self._handle_cancel(parameters, invocation)
        elif method_name == "SaveSecrets":
            invocation.return_value(None)
        elif method_name == "DeleteSecrets":
            invocation.return_value(None)
        else:
            invocation.return_error_literal(
                Gio.dbus_error_quark(),
                Gio.DBusError.UNKNOWN_METHOD,
                f"Unknown method: {method_name}"
            )
    
    def _handle_get_secrets(self, parameters, invocation):
        connection_settings, connection_path, setting_name, hints, flags = parameters.unpack()
        

        ssid = "Unknown"
        if "802-11-wireless" in connection_settings:
            wireless = connection_settings["802-11-wireless"]
            if "ssid" in wireless:
                ssid_bytes = wireless["ssid"]
                ssid = self.wifidbus._decode_ssid(ssid_bytes)
    
        request_id = f"{connection_path}:{setting_name}"
        self.pending_requests[request_id] = invocation
        
        def on_password_received(password):
            if request_id not in self.pending_requests:
                return
    
            del self.pending_requests[request_id]
            
            if password is None:
                self.wifidbus.deactivate_connection()
                invocation.return_error_literal(
                    Gio.dbus_error_quark(),
                    Gio.DBusError.ACCESS_DENIED,
                    "User cancelled"
                )
                return
            
            secrets = {
                setting_name: {
                    "psk": GLib.Variant("s", password)
                }
            }

            secrets_variant = self._build_secrets_variant(secrets)
            invocation.return_value(GLib.Variant("(a{sa{sv}})", (secrets_variant,)))
        
        GLib.idle_add(
            lambda: self.password_callback(ssid, flags, on_password_received)
        )
    
    def _build_secrets_variant(self, secrets_dict):
        result = {}
        for setting_name, setting_secrets in secrets_dict.items():
            inner = {}
            for key, variant in setting_secrets.items():
                inner[key] = variant
            result[setting_name] = inner
        return result
    
    def _handle_cancel(self, parameters, invocation):
        connection_path, setting_name = parameters.unpack()
        request_id = f"{connection_path}:{setting_name}"
        
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
            
        invocation.return_value(None)


    def _get_introspection_xml(self, type_of_agent="networkmanager"):
        if type_of_agent == "networkmanager":
            introspection_xml = """
            <node>
                <interface name="org.freedesktop.NetworkManager.SecretAgent">
                    <method name="GetSecrets">
                        <arg name="connection" type="a{sa{sv}}" direction="in"/>
                        <arg name="connection_path" type="o" direction="in"/>
                        <arg name="setting_name" type="s" direction="in"/>
                        <arg name="hints" type="as" direction="in"/>
                        <arg name="flags" type="u" direction="in"/>
                        <arg name="secrets" type="a{sa{sv}}" direction="out"/>
                    </method>
                    <method name="CancelGetSecrets">
                        <arg name="connection_path" type="o" direction="in"/>
                        <arg name="setting_name" type="s" direction="in"/>
                    </method>
                    <method name="SaveSecrets">
                        <arg name="connection" type="a{sa{sv}}" direction="in"/>
                        <arg name="connection_path" type="o" direction="in"/>
                    </method>
                    <method name="DeleteSecrets">
                        <arg name="connection" type="a{sa{sv}}" direction="in"/>
                        <arg name="connection_path" type="o" direction="in"/>
                    </method>
                </interface>
            </node>
            """
            
        elif type_of_agent == "bluez":
            introspection_xml = """
            <node>
                <interface name="org.bluez.Agent1">
                    <method name="RequestPinCode">
                        <arg name="device" type="o" direction="in"/>
                        <arg name="pincode" type="s" direction="out"/>
                    </method>
                    <method name="RequestPasskey">
                        <arg name="device" type="o" direction="in"/>
                        <arg name="passkey" type="u" direction="out"/>
                    </method>
                    <method name="RequestConfirmation">
                        <arg name="device" type="o" direction="in"/>
                        <arg name="passkey" type="u" direction="in"/>
                    </method>
                    <method name="RequestAuthorization">
                        <arg name="device" type="o" direction="in"/>
                    </method>
                    <method name="AuthorizeService">
                        <arg name="device" type="o" direction="in"/>
                        <arg name="uuid" type="s" direction="in"/>
                    </method>
                    <method name="Cancel"/>
                    <method name="Release"/>
                </interface>
            </node>
            """
        return introspection_xml

############# Bluetooth ##############

    def register_bluez_agent(self, agent_manager):
        try:
            agent_manager.call_sync(
                "RegisterAgent",
                GLib.Variant("(os)", (self.BLUEZ_AGENT_PATH, "DisplayYesNo")),
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )
            agent_manager.call_sync(
                "RequestDefaultAgent",
                GLib.Variant("(o)", (self.BLUEZ_AGENT_PATH,)),
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )
            print(f"Bluez agent registered: {self.BLUEZ_AGENT_PATH}")
        except Exception as e:
            print(f"Failed to register bluez agent: {e}")
            raise

    def _handle_bt_method_call(self, connection, sender, object_path,
                                interface_name, method_name, parameters, invocation):
        print(f"[BT AGENT] method={method_name}, params={parameters.unpack()}")

        if method_name == "RequestConfirmation":
            device, passkey = parameters.unpack()

            def on_confirmed(confirmed):
                if confirmed:
                    invocation.return_value(None)
                else:
                    invocation.return_error_literal(
                        Gio.dbus_error_quark(),
                        Gio.DBusError.ACCESS_DENIED,
                        "User rejected"
                    )
            GLib.idle_add(lambda: self.bt_callback("confirmation", device, passkey, on_confirmed))

        elif method_name == "RequestPinCode":
            device = parameters.unpack()[0]
            def on_pin_received(pin):
                if pin:
                    invocation.return_value(GLib.Variant("(s)", (pin,)))
                else:
                    invocation.return_error_literal(
                        Gio.dbus_error_quark(),
                        Gio.DBusError.ACCESS_DENIED,
                        "User cancelled"
                    )
            GLib.idle_add(lambda: self.bt_callback("pincode", device, None, on_pin_received))

        elif method_name == "RequestPasskey":
            device = parameters.unpack()[0]
            def on_passkey_received(passkey):
                if passkey:
                    invocation.return_value(GLib.Variant("(u)", (int(passkey),)))
                else:
                    invocation.return_error_literal(
                        Gio.dbus_error_quark(),
                        Gio.DBusError.ACCESS_DENIED,
                        "User cancelled"
                    )
            GLib.idle_add(lambda: self.bt_callback("passkey", device, None, on_passkey_received))

        elif method_name in ("RequestAuthorization", "AuthorizeService"):
            invocation.return_value(None)

        elif method_name in ("Cancel", "Release"):
            if self.bt_callback:
                GLib.idle_add(lambda: self.bt_callback("cancel", None, None, None))
            invocation.return_value(None)


    def unregister(self):

        def unregister_bluez_agent():
            if self.bt_registration_id:
                self.bus.unregister_object(self.bt_registration_id)
            try:
                agent_manager = Gio.DBusProxy.new_sync(
                    self.bus, 
                    Gio.DBusProxyFlags.NONE, 
                    None,
                    "org.bluez", 
                    self.BLUEZ_AGENT_MANAGER_PATH,
                    self.BLUEZ_AGENT_MANAGER_INTERFACE, 
                    None
                )
                agent_manager.call_sync(
                    "UnregisterAgent",
                    GLib.Variant("(o)", (self.BLUEZ_AGENT_PATH,)),
                    Gio.DBusCallFlags.NONE, -1, None
                )
            except Exception:
                pass

        def unregister_nm():
            if self.registration_id:
                self.bus.unregister_object(self.registration_id)
                
            try:
                agent_manager = Gio.DBusProxy.new_sync(
                    self.bus,
                    Gio.DBusProxyFlags.NONE,
                    None,
                    "org.freedesktop.NetworkManager",
                    self.AGENT_MANAGER_PATH,
                    self.AGENT_MANAGER_INTERFACE,
                    None
                )
                agent_manager.call_sync(
                    "Unregister",
                    None,
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None
                )
            except Exception:
                pass

        unregister_bluez_agent()
        unregister_nm()

