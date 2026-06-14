import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib, Gio
_v_layer = None
from ..assets.utils import Header, Popups, window_utils, GtkLayerShellUtils
from ..assets.wifi_dbus import WifiDbus
from ..assets.agent import SecretAgent
from .bluetooth import Bluetooth

class NetworkLayer(Gtk.Window):
    def __init__(self, config):
        super().__init__(title="Network Layer")
        self.config = config
        self.shellutils = GtkLayerShellUtils(self, "network")
        self.load_config(self.config)
        self.set_default_size(400, 500)
        self.get_style_context().add_class("network-window")
        self.main_overlay = Gtk.Overlay()
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_container.set_margin_start(0)
        main_container.get_style_context().add_class("network-layer")
        self.main_overlay.set_child(main_container)
        self.set_child(self.main_overlay)
        self.wifidbus = WifiDbus(self.update_ui_elements)
        self.passwd_windows = {}
        self.saved_windows = {}
        self.wifi_cards_details = {}
        self.window_utils = window_utils()
        self.empty_widgets = self.window_utils.init_empty_text("Wi-fi is currently disabled", "network-wireless-disabled-symbolic")
        self.retry_num = 0
        self.preparing = None
        self.setup_tabs()
        main_container.append(self.main_header_container)
        main_container.append(self.tabs)
        self.secret_agent = SecretAgent(self.on_password_required, self.wifidbus, self.bluetooth.on_agent_call)
        self.secret_agent.register()

    def load_config(self, config):
        if self.config != config:
            self.config = config
        anchor, margin = self.shellutils.process_config(config, default_anchor="top-right", default_margin=[10, 10])
        self.shellutils.setup_layer_shell(anchor, margin)

    
    def setup_tabs(self):
        self.tabs = Gtk.Stack()
        self.tabs.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.main_wifi_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_bluetooth_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.wifi_page = self.tabs.add_named(self.main_wifi_container, "Wifi-Tab")
        self.bluetooth_page = self.tabs.add_named(self.main_bluetooth_container, "Bluetooth-Tab")
        self.main_header_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
            margin_start = 10,
            margin_end = 10,
            margin_top = 10,
            margin_bottom = 10 )
        self.main_header_container.get_style_context().add_class("header")
        self.main_header_container.set_homogeneous(True)
        self.tab_buttons = {}
        self.header = Header(self.main_header_container, self.tab_buttons, self.tabs)
        self.header.setup_header("Internet", "network-wireless-signal-excellent-symbolic", "Wifi-Tab")
        self.header.setup_header("Bluetooth", "bluetooth-symbolic", "Bluetooth-Tab")
        self.setup_wifi_tab()
        self.bluetooth = Bluetooth(self.main_bluetooth_container, self.main_overlay, self.set_keyboard_mode)
        

    def setup_wifi_tab(self):
        self.saved_windows = self.window_utils.setup_revealer(overlay=self.main_overlay, popupwindow=PopupWindow, set_keyboard_mode=None, windowtype="saved", wifidbus=self.wifidbus)
        self.passwd_windows = self.window_utils.setup_revealer(overlay=self.main_overlay, popupwindow=PopupWindow, set_keyboard_mode=self.set_keyboard_mode, windowtype="password", wifidbus=self.wifidbus)
        self.details_windows = self.window_utils.setup_revealer(overlay=self.main_overlay, popupwindow=PopupWindow, set_keyboard_mode=None, windowtype="details", wifidbus=self.wifidbus)
        self.scrolled_wifi_panel, self.scrolled_wifi_container = self.window_utils.setup_scrolled_windows(340, 300, self.update_headers, self.wifi_sort_func)
        self.setup_wifi_switches()
        self.main_wifi_container.append(self.scrolled_wifi_panel)
        self.main_wifi_container.set_vexpand(True)
        self.scrolled_wifi_container.set_vexpand(True)
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bottom_box.set_valign(Gtk.Align.END)
        self.wifi_reload_btn = Gtk.Button()
        self.wifi_reload_btn.get_style_context().add_class("wifi-reload")
        self.wifi_reload_btn.set_hexpand(True)
        self.wifi_reload_btn.set_margin_top(20)
        self.reload_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic")
        self.reload_icon.get_style_context().add_class("reload-icon")
        self.wifi_reload_btn.set_child(self.reload_icon)
        self.wifi_reload_btn.connect("clicked", lambda x: self.on_refresh())
        self.saved_networks_btn = Gtk.Button()
        self.saved_networks_btn.connect("clicked", lambda x, reveal=self.saved_windows["revealer"]: reveal.set_reveal_child(True))
        self.saved_networks_btn.set_hexpand(False)
        self.saved_networks_btn.set_margin_top(20)
        saved_icon_overlay = Gtk.Overlay()
        saved_wifi_icon = Gtk.Image.new_from_icon_name("network-wireless-signal-excellent-symbolic")
        saved_wifi_icon.set_pixel_size(24)
        saved_wifi_icon.set_valign(Gtk.Align.CENTER)
        saved_wifi_icon.set_halign(Gtk.Align.CENTER)
        saved_icon_overlay.set_child(saved_wifi_icon)
        save_icon = Gtk.Image.new_from_icon_name("document-save-symbolic")
        save_icon.set_pixel_size(8)
        save_icon.set_valign(Gtk.Align.END)
        save_icon.set_halign(Gtk.Align.END)
        saved_icon_overlay.add_overlay(save_icon)
        self.saved_networks_btn.set_child(saved_icon_overlay)
        self.saved_networks_btn.get_style_context().add_class("saved-menu-button")
        bottom_box.append(self.wifi_reload_btn)
        bottom_box.append(self.saved_networks_btn)
        self.main_wifi_container.append(bottom_box)
        if not self.wifi_switch.get_active() or not self.net_switch.get_active():
            self.empty_state()
        self.wifidbus.get_wifi_networks_data()

    def setup_wifi_switches(self):
        switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, 
            margin_start=20,
            margin_end=20,
            margin_top=5,
            margin_bottom=10,
            spacing=10)
        switch_box.set_hexpand(True)
        switch_box.set_halign(Gtk.Align.CENTER)
        self.wifi_switch = Gtk.Switch()
        self.wifi_switch.get_style_context().add_class("wifi-switch")
        self.wifi_switch.connect("state-set", self.on_wifi_switch)
        self.wifi_switch.set_active(self.wifidbus.get_wifi_status())
        self.net_switch = Gtk.Switch()
        self.net_switch.set_active(True)
        self.net_switch.get_style_context().add_class("network-switch")
        self.net_switch.connect("state-set", self.on_network_switch)
        self.net_switch.set_active(self.wifidbus.get_network_status())
        wifi_label = Gtk.Label(label="Wi-Fi")
        net_label = Gtk.Label(label="Network")
        switch_box.append(self.wifi_switch)
        switch_box.append(wifi_label)
        switch_box.append(self.net_switch)
        switch_box.append(net_label)
        self.main_wifi_container.append(switch_box)

    def setup_wifi_cards(self, network):
        if network["ssid"] in self.wifi_cards_details:
            self.update_ui_elements({"update_card": network})
            return
        self.active_connections = self.wifidbus.get_active_networks()
        network_details = network
        row = Gtk.ListBoxRow()
        row.strength = network_details['strength']
        active = network_details["ssid"] in self.active_connections
        row.is_active = active
        row.ssid = network_details["ssid"]
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        card.set_hexpand(True)
        ssid_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        ssid_container.set_hexpand(True)
        ssid = Gtk.Label(label=f"{network_details['ssid']}")
        ssid.set_halign(Gtk.Align.START)
        strength = Gtk.Label(label=f"Signal - {network_details['strength']}%")
        strength.get_style_context().add_class("subname")
        strength.set_halign(Gtk.Align.START)
        strength_icon = Gtk.Image.new_from_icon_name(self.get_wifi_signal_icon(network_details['strength']))
        strength_icon.get_style_context().add_class("wifi-icon")
        ssid_container.append(ssid)
        ssid_container.append(strength)
        lock_icon = Gtk.Image.new_from_icon_name(f"{'object-locked' if network_details['secured'] else 'object-unlocked'}")
        lock_icon.set_margin_end(10)
        lock_icon.set_halign(Gtk.Align.END)
        connect_btn = Gtk.Button(label="Connect")
        connect_btn.connect("clicked", self.on_button_clicked, network_details)
        connect_btn.get_style_context().add_class("connect-button")
        connect_btn.set_halign(Gtk.Align.END)
        loader_container =Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        spinner = Gtk.Image.new_from_icon_name("process-working-symbolic")
        spinner.get_style_context().add_class("spinner")
        spinner.set_halign(Gtk.Align.END)
        loading_label = Gtk.Label(label="Connecting...")
        loader_container.append(spinner)
        loader_container.append(loading_label)
        loader_container.set_visible(False)
        details_btn = Gtk.Button()
        details_btn.set_child(Gtk.Image.new_from_icon_name("info-outline-symbolic"))
        details_btn.get_style_context().add_class("wifi-details-button")
        details_btn.set_margin_end(10)
        details_btn.connect("clicked", lambda x, revealer=self.details_windows["revealer"]: revealer.set_reveal_child(True))
        details_btn.set_visible(False)
        card.append(strength_icon)
        card.append(ssid_container)
        card.append(lock_icon)
        card.append(loader_container)
        card.append(details_btn)
        card.append(connect_btn)
        card.get_style_context().add_class("network-card")
        row.set_child(card)
        self.scrolled_wifi_container.append(row)
        if active and not network["ssid"] == self.preparing:
            card.get_style_context().add_class("active")
            lock_icon.set_visible(False)
            details_btn.set_visible(True)
        self.wifi_cards_details[network_details['ssid']] = {
            "details": network_details,
            "row": row,
            "card": card,
            "connect_btn": connect_btn,
            "strength": strength,
            "lock_icon": lock_icon,
            "strength_icon": strength_icon,
            "spinner": spinner,
            "loader_container": loader_container,
            "loading_label": loading_label,
            "details_btn": details_btn,
            "active": active,
        }
        if network["ssid"] == self.preparing:
            self.toggle_loader(network["ssid"], True)
            return
        self.update_card_css(network_details, card, connect_btn)
        self.scrolled_wifi_container.invalidate_sort()

    def check_for_wired_connection(self):
        if "wired" in self.active_connections.keys():
            card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            speed_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            speed_container.set_hexpand(True)
            card.get_style_context().add_class("network-card")
            card.get_style_context().add_class("active")
            card.set_hexpand(True)
            wired_icon = Gtk.Image.new_from_icon_name("network-wired")
            wired_icon.get_style_context().add_class("wifi-icon")
            wired_label = Gtk.Label(label=f"{self.active_connections['wired']['id']}")
            wired_label.set_halign(Gtk.Align.START)
            speed_label = Gtk.Label(label=f"Speed: {self.wifidbus.get_ethernet_speed()} Mb/s")
            speed_label.set_halign(Gtk.Align.START)
            disconnect_btn = Gtk.Button(label="Disconnect")
            disconnect_btn.connect("clicked", self.on_ethernet_button_clicked)
            disconnect_btn.get_style_context().add_class("connect-button")
            disconnect_btn.set_halign(Gtk.Align.END)
            speed_container.append(wired_label)
            speed_container.append(speed_label)
            card.append(wired_icon)
            card.append(speed_container)
            card.append(disconnect_btn)
            row = Gtk.ListBoxRow()
            row.is_active = True
            row.set_child(card)
            row.strength = 200
            self.scrolled_wifi_container.append(row)
    
    def on_ethernet_button_clicked(self, *args):
        self.wifidbus.deactivate_connection("ethernet")

    def wifi_sort_func(self, row1, row2):
        if hasattr(row1, "is_active") and hasattr(row2, "is_active"):
            if row1.is_active != row2.is_active:
                return -1 if row1.is_active else 1
            if hasattr(row1, "strength") and hasattr(row2, "strength"):
                return row2.strength - row1.strength
        return 0
    
    def update_headers(self, row, before):
        if before is None and hasattr(row, "is_active"):
            text = "ACTIVE CONNECTIONS" if row.is_active else "AVAILABLE NETWORKS"
            header = Gtk.Label(label=text)
            header.get_style_context().add_class("header-label")
            header.set_halign(Gtk.Align.START)
            header.set_margin_top(10)
            header.set_margin_bottom(5)
            row.set_header(header)
            return

        if hasattr(before, "is_active") and hasattr(row, "is_active"):
            if before.is_active and not row.is_active:
                header = Gtk.Label(label="AVAILABLE NETWORKS")
                header.get_style_context().add_class("header-label")
                header.set_halign(Gtk.Align.START)
                header.set_margin_top(15)
                header.set_margin_bottom(5)
                row.set_header(header)
            else:
                row.set_header(None)
        else:
            row.set_header(None)

    def update_card_css(self, network, card, connect_btn):
        if self.wifi_cards_details[network["ssid"]]['active'] and not network["ssid"] == self.preparing:
            card.get_style_context().add_class("active")
            connect_btn.set_label("Disconnect")
            self.wifi_cards_details[network["ssid"]]["active"] = True
            
        else:
            card.get_style_context().remove_class("active")
            connect_btn.set_label("Connect")
            self.wifi_cards_details[network["ssid"]]["active"] = False

    def on_button_clicked(self, btn, network):
        ssid = network["ssid"]
        if self.wifi_cards_details[ssid]['active']:
            self.wifidbus.deactivate_connection()
        else:
            self.wifidbus.activate_connection(network)
        
    def on_password_required(self, ssid, flags, respond_callback):
        allow_interaction = bool(flags & 0x1)
        request_new = bool(flags & 0x2)
        self.passwd_windows["overlay"].passwdinput.set_text("") 
        self.passwd_windows["overlay"].password_callback = respond_callback
        if allow_interaction:
            if request_new:  
                self.passwd_windows["overlay"].retry_text.set_label("Wrong Password")
                self.passwd_windows["overlay"].retry_text.set_visible(True)
                if self.retry_num > 3:
                    self.retry_num = 0
                    respond_callback(None)
                    return
                else:
                    self.retry_num += 1
            else:
                self.passwd_windows["overlay"].retry_text.set_visible(False)
                self.retry_num = 1
            self.passwd_windows["overlay"].passwdinput.set_text("")
            self.passwd_windows["overlay"].password_callback = respond_callback
            self.passwd_windows["revealer"].set_reveal_child(True)
            Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.ON_DEMAND)
        else:
            respond_callback(None)
            return

    def get_wifi_signal_icon(self, signal):
        levels = [
            (80, "excellent"),
            (60, "good"),
            (40, "ok"),
            (10, "weak"),
            (0,  "none")
        ]
        for threshold, icon in levels:
            if int(signal) >= threshold:
                return f"network-wireless-signal-{icon}-symbolic"
            
    def update_ui_elements(self, parameters):
        if "available_networks" in parameters:
            if not self.wifi_switch.get_active():
                return
            if hasattr(self, "refresh_timeout") and self.refresh_timeout:
                try:
                    source_id = self.refresh_timeout
                    self.refresh_timeout = None
                    GLib.source_remove(self.refresh_timeout)
                except:
                    pass
                self.reload_icon.get_style_context().remove_class("active")
            if parameters["available_networks"]:
                if self.empty_widgets["box"].get_parent() is not None:
                    self.hide_empty_widgets()
                to_remove = [ssid for ssid in self.wifi_cards_details if ssid not in parameters["available_networks"]]
                for ssid in to_remove:
                    self.scrolled_wifi_container.remove(self.wifi_cards_details[ssid]["row"])
                    del self.wifi_cards_details[ssid]
                for keys, values in parameters["available_networks"].items():
                    self.setup_wifi_cards(values)
                self.check_for_wired_connection()
        if "saved_networks" in parameters:
            self.saved_windows["overlay"].setup_saved()
        if "updated_network" in parameters:
            network = parameters["updated_network"]
            if "bitrate" in parameters:
                speed = f"{int(int(parameters['bitrate'])/ 1000)} Mb/s"
                label = self.details_windows["overlay"].details["Bitrate"]
                if label.get_label() != speed:
                    label.set_label(f"{speed}")
            if "strength" in parameters:
                for keys, values in self.wifi_cards_details.items():
                    if values["details"]["path"] == network:
                        self.wifi_cards_details[keys]["details"]["strength"] = parameters["strength"]
                        self.wifi_cards_details[keys]["strength"].set_text(f"Signal - {parameters['strength']}%")
                        break

        if "status_update" in parameters:
            network = parameters["status_update"]
            status = parameters["status"]
            if status == "disconnected":
                self.preparing = None
                for ssid, details in self.wifi_cards_details.items():
                    details["row"].is_active = False
                    self.toggle_loader(ssid, False)
                    details["active"] = False
                    details["card"].get_style_context().remove_class("active")
                    details["details_btn"].set_visible(False)
                    details["lock_icon"].set_visible(True)
                    self.update_card_css(details["details"], details["card"], details["connect_btn"])
                self.scrolled_wifi_container.invalidate_sort()
            else:
                self.active_connections = self.wifidbus.get_active_networks()
                for ssid, path in self.active_connections.items():
                    if path == network:
                        if status == "connected" and ssid in self.wifi_cards_details:
                            self.preparing = None
                            self.wifi_cards_details[ssid]["active"] = True
                            self.toggle_loader(ssid, False)
                            self.wifi_cards_details[ssid]["row"].is_active = True
                            self.wifi_cards_details[ssid]["connect_btn"].set_visible(True)
                            self.wifi_cards_details[ssid]["lock_icon"].set_visible(False)
                            self.scrolled_wifi_container.invalidate_sort()
                            details = self.wifidbus.get_active_network_details()
                            for key, value in self.details_windows["overlay"].match_names.items():
                                self.details_windows["overlay"].details[value].set_label(details[value])
                            self.update_card_css(self.wifi_cards_details[ssid]["details"], self.wifi_cards_details[ssid]["card"], self.wifi_cards_details[ssid]["connect_btn"])
                            break
                        elif status == "preparing":
                            if ssid in self.wifi_cards_details:
                                self.toggle_loader(ssid, True)
                            else:
                                self.preparing = ssid
                            break
    
    def toggle_loader(self, ssid, state):
        if ssid in self.wifi_cards_details:
            self.wifi_cards_details[ssid]["loader_container"].set_visible(state)
            self.wifi_cards_details[ssid]["connect_btn"].set_visible(not state)
            self.wifi_cards_details[ssid]["lock_icon"].set_visible(not state)
            self.wifi_cards_details[ssid]["details_btn"].set_visible(not state)
            if not state:
                self.wifi_cards_details[ssid]["spinner"].get_style_context().remove_class("active")
                return
            self.wifi_cards_details[ssid]["spinner"].get_style_context().add_class("active")
    
    def cleanup(self):
        if self.secret_agent:
            self.secret_agent.unregister()

    def on_refresh(self):
        if self.wifi_switch.get_active() and self.net_switch.get_active():
            self.wifidbus.request_scan()
            self.reload_icon.get_style_context().add_class("active")
            def timeout_func():
                if hasattr(self, 'refresh_timeout') and self.refresh_timeout is None:
                    return False
                self.reload_icon.get_style_context().remove_class("active")
                self.refresh_timeout = None
                return False
            self.refresh_timeout = GLib.timeout_add(5000, timeout_func)


    def on_wifi_switch(self, switch, state):
        self.wifidbus.toggle_wifi(switch, state)        
        if not state:
            self.empty_state()
            self.empty_widgets["icon"].set_from_icon_name("network-wireless-disconnected-symbolic")
            self.empty_widgets["text"].set_label("Wi-fi is currently disabled")
            return
        self._on_wifi_turned_on()

            
    def empty_state(self):
        for values in self.wifi_cards_details.values():
            if values["row"].get_parent() is not None:
                self.scrolled_wifi_container.remove(values["row"])
        self.wifi_cards_details = {}
        self.empty_widgets["loader"].set_visible(False)
        self.empty_widgets["icon"].set_visible(True)
        self.empty_widgets["box"].set_visible(True)
        self.empty_widgets["loader"].get_style_context().remove_class("active")
        if self.empty_widgets["box"].get_parent() is None:
            self.scrolled_wifi_container.append(self.empty_widgets["box"])

    def hide_empty_widgets(self):
        if self.empty_widgets["box"].get_parent() is not None:
            row = self.empty_widgets["box"].get_parent()
            if row.get_parent() is not None:
                row.get_parent().remove(row)
            self.empty_widgets["box"].set_visible(False)
            self.empty_widgets["loader"].get_style_context().remove_class("active")
            

    def on_network_switch(self, switch, state):
        self.wifidbus.toggle_network(switch, state)
        self.wifi_switch.set_sensitive(state)
        if not state:
            self.wifi_switch.get_style_context().add_class("disabled")
            self.empty_state()
            self.empty_widgets["icon"].set_from_icon_name("network-wired-disconnected-symbolic")
            self.empty_widgets["text"].set_label("Network is currently disabled")
            return
        elif state and self.wifi_switch.get_active():
            self._on_wifi_turned_on()
        else:
            self.empty_widgets["icon"].set_from_icon_name("network-wireless-disconnected-symbolic")
            self.empty_widgets["text"].set_label("Wi-fi is currently disabled")
        self.wifi_switch.get_style_context().remove_class("disabled")
            

    def set_keyboard_mode(self, mode):
        if mode:
            Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.ON_DEMAND)
        else:
            Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.NONE)

    def _on_wifi_turned_on(self):
        self.empty_widgets["loader"].set_visible(True)
        self.empty_widgets["loader"].get_style_context().add_class("active")
        self.empty_widgets["icon"].set_visible(False)
        self.empty_widgets["text"].set_label("Scanning for available networks...")
        GLib.idle_add(self.wifidbus.get_wifi_networks_data)

class PopupWindow:
    def __init__(self, set_keyboard_mode, windowtype, wifidbus, windows):
        self.set_keyboard_mode = set_keyboard_mode
        self.password_callback = None
        self.popup = Popups()
        self.details = {}
        self.wifidbus = wifidbus
        self.type = windowtype
        self.windows = windows
        self.panel = Gtk.Frame()
        self.panel.add_css_class("floating-panel-wifi")
        self.panel.set_size_request(-1, -1)
        self.panel_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_start=20,
            margin_end=20,
            margin_top=20,
            margin_bottom=20
            )
        self.panel.set_child(self.panel_content)
        self.match_names = {
            "IPv4 Address": "AddressData",
            "Gateway": "Gateway",
            "DNS": "NameserverData",
            "MAC Address": "HwAddress",
            "Speed": "Bitrate"
        }
        self.icons = {
            "IPv4 Address": "network-server-symbolic",
            "Gateway": "network-modem-symbolic",
            "DNS": "network-vpn-symbolic",
            "MAC Address": "network-wired-activated-symbolic",
            "Speed": "preferences-system-network-symbolic"
        }
        self.setup_ui()
    
    def setup_ui(self):
        header_text = {
            "saved": "Saved Networks",
            "details": "Network Details",
            "password": "Enter password"
        }
        self.popup.create_header(header_text=f"{header_text[self.type].upper()}", close_function=lambda x: self.on_close(self.type), main_container=self.panel_content)
        if self.type == "password":
            self.setup_password_ui()
            self.panel_content.append(self.passwdinput)
        elif self.type == "details":
            self.hor_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.hor_container.set_homogeneous(True)
            self.details = self.popup.setup_details(
                match_names=self.match_names,
                match_icons=self.icons,
                details = self.wifidbus.get_active_network_details(),
                container=self.hor_container)
            self.panel_content.append(self.hor_container)
        else:
            self.setup_wifi_box()        

    def setup_wifi_box(self):
        self.wifi_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
        self.scrolled_wifi_container = Gtk.ScrolledWindow()
        self.scrolled_wifi_container.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_wifi_container.set_propagate_natural_height(True)
        self.scrolled_wifi_container.set_max_content_height(300)
        self.scrolled_wifi_container.set_min_content_height(200)
        self.setup_saved()
        self.scrolled_wifi_container.set_child(self.wifi_container)
        self.panel_content.append(self.scrolled_wifi_container)

    def setup_saved(self):
        while child := self.wifi_container.get_first_child():
           self.wifi_container.remove(child)
        saved_networks = self.wifidbus.get_saved_connections()
        if saved_networks:
            for ssids in saved_networks:
                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                card.set_hexpand(True)
                ssid_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                ssid_container.set_hexpand(True)
                ssid = Gtk.Label(label=f"{ssids}")
                ssid.set_halign(Gtk.Align.START)
                autoconnect = str(saved_networks[ssids]["autoconnect"])
                autoconnect_status = Gtk.Label(label=f"{'Autoconnect Enabled' if autoconnect else 'Manual Connect Only'}")
                autoconnect_status.get_style_context().add_class("subname")
                autoconnect_status.set_halign(Gtk.Align.START)
                icon = Gtk.Image.new_from_icon_name("network-wireless-signal-excellent-symbolic")
            #strength_icon.set_pixel_size(25)
                icon.get_style_context().add_class("wifi-icon")
                ssid_container.append(ssid)
                ssid_container.append(autoconnect_status)
                autoconnect_switch = Gtk.Switch()
                autoconnect_switch.set_active(saved_networks[ssids]["autoconnect"])
                autoconnect_switch.get_style_context().add_class("autoconnect-switch")
                autoconnect_switch.connect("state-set", self.on_autoconnect_switched, saved_networks[ssids]["path"], autoconnect_status, )
                forget_btn = Gtk.Button(label="Forget")
                forget_btn.get_style_context().add_class("forget-button")
                forget_btn.set_halign(Gtk.Align.END)
                forget_btn.connect("clicked", lambda x, path=saved_networks[ssids]["path"]: self.wifidbus.forget_network(path))
                card.append(icon)
                card.append(ssid_container)
                card.append(autoconnect_switch)
                card.append(forget_btn)
                card.get_style_context().add_class("network-card")
                self.wifi_container.append(card)
        
    def setup_password_ui(self):
        self.retry_text = Gtk.Label(label="Wrong Password")
        self.retry_text.set_visible(False)
        self.panel_content.append(self.retry_text)
        self.connect_to = None
        self.passwdinput = Gtk.PasswordEntry()
        self.passwdinput.set_hexpand(True)
        self.passwdinput.set_show_peek_icon(True)
        self.passwdinput.get_style_context().add_class("password-entry")
        self.passwdinput.set_halign(Gtk.Align.CENTER)
        self.passwdinput.set_margin_top(20)
        self.passwdinput.set_margin_bottom(20)
        self.passwdinput.set_size_request(200, -1)
        self.passwdinput.props.placeholder_text = "Enter Password"
        connect_btn = Gtk.Button(label="Connect")
        connect_btn.get_style_context().add_class("connect-button")
        self.passwdinput.connect("activate", lambda x: self.on_password_entered(self.passwdinput))


    def on_autoconnect_switched(self, switch, state, path, label):
        self.wifidbus.update_autoconnect(path, state)
        label.set_text(f"{'Autoconnect Enabled' if state else 'Manual Connect Only'}")


    def on_password_entered(self, entry):
        password = entry.get_text()
        if len(password) < 8:
            self.retry_text.set_label("Password must be at least 8 characters")
            self.retry_text.set_visible(True)
            self.passwdinput.set_text("")
            return
        if self.password_callback:
            self.password_callback(password)
        self.windows["revealer"].set_reveal_child(False)
        if self.set_keyboard_mode:
            self.set_keyboard_mode(False)

    def on_close(self, windowtype="saved"):
        self.windows["revealer"].set_reveal_child(False)
        if windowtype == "password":
            if self.set_keyboard_mode:
                self.set_keyboard_mode(False)
            self.password_callback(None)
        

def init_layer(config):
    global _v_layer
    if _v_layer is None:
        _v_layer = NetworkLayer(config)
        _v_layer.connect("close-request", lambda w, e: w.hide() or True)

def toggle_layer():
    global _v_layer
    if _v_layer.get_visible():
        _v_layer.bluetooth.dbusbluez.discovery(False)
        _v_layer.hide()
    else:
        _v_layer.header.change_tab("Wifi-Tab")
        _v_layer.bluetooth.dbusbluez.discovery(True)
        _v_layer.show()
        _v_layer.present()

def reload_config(config):
    global _v_layer
    if _v_layer:
        _v_layer.load_config(config)

def hide_layer():
    global _v_layer
    _v_layer.hide()

def cleanup():
    global _v_layer
    if _v_layer:
        _v_layer.cleanup()

def get_visibility():
    global _v_layer
    return _v_layer.get_visible()