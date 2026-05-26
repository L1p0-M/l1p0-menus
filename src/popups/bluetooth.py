import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib, Gio
from ..assets.utils import window_utils, Popups
from ..assets.bluetooth_dbus import DbusBluez


class Bluetooth:
    def __init__(self, container, overlay):
        self.main_container = container
        self.dbusbluez = DbusBluez(self.update_ui_elements)
        self.loading = False
        self.main_overlay = overlay
        self.wait_till_paired = False
        self.bluetooth_cards_details = {}
        self.window_utils = window_utils()
        self.empty_widgets = self.window_utils.init_empty_text("Bluetooth is currently disabled", "bluetooth-disabled-symbolic")
        self.auth_windows = self.window_utils.setup_revealer(self.main_overlay, PopupWindow, "pairing", None, None)
        self.setup_bluetooth_tab()
        self.internal_update = False

    def setup_bluetooth_tab(self):
        switch_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
            margin_start=20,
            margin_end=20,
            margin_top=5,
            margin_bottom=10,
            spacing=10)
        switch_container.set_hexpand(True)
        switch_container.set_halign(Gtk.Align.CENTER)
        self.toggle_switch = Gtk.Switch()
        self.bluetooth_toggle_event = self.toggle_switch.connect("state-set", self.on_bluetooth_toggle)
        self.toggle_switch.get_style_context().add_class("network-switch")
        self.toggle_switch_label = Gtk.Label(label="Bluetooth")
        self.discover_switch = Gtk.Switch()
        self.discover_toggle_event = self.discover_switch.connect("state-set", self.on_discoverable_switch)
        self.discover_switch.get_style_context().add_class("network-switch")
        self.discover_switch_label = Gtk.Label(label="Discoverable")
        switch_container.append(self.toggle_switch)
        switch_container.append(self.toggle_switch_label)
        switch_container.append(self.discover_switch)
        switch_container.append(self.discover_switch_label)
        self.main_container.append(switch_container)
        self.scrolled_bluetooth_panel, self.scrolled_bluetooth_container = self.window_utils.setup_scrolled_windows(340, 340, self.update_headers, self._sort_func)
        self.main_container.append(self.scrolled_bluetooth_panel)
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.bluetooth_reload_btn = Gtk.Button()
        self.bluetooth_reload_btn.get_style_context().add_class("bluetooth-reload")
        self.bluetooth_reload_btn.connect("clicked", lambda x: self.on_refresh())
        self.bluetooth_reload_btn.set_hexpand(True)
        self.bluetooth_reload_btn.set_margin_top(20)
        self.reload_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic")
        self.reload_icon.get_style_context().add_class("reload-icon")
        self.bluetooth_reload_btn.set_child(self.reload_icon)
        bottom_box.append(self.bluetooth_reload_btn)
        self.main_container.append(bottom_box)
        self._default_state()
        

    def setup_cards(self, device):
        dev_name = device["name"]
        if dev_name in self.bluetooth_cards_details:
            self.update_ui_elements({"update_card": device})
            return
        row = Gtk.ListBoxRow()
        row.paired = device["paired"] if device["paired"] is not None else False
        active = device["connected"]
        row.is_active = active
        row.name = dev_name
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        card.set_hexpand(True)
        name_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name_container.set_hexpand(True)
        name = Gtk.Label(label=f"{dev_name}")
        name.set_halign(Gtk.Align.START)
        bottom_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bottom_container.get_style_context().add_class("subname")
        subname = Gtk.Label(label=f"{'Connected' if device['connected'] else 'Paired' if device['paired'] else 'Available'}")
        subname.set_halign(Gtk.Align.START)
        icon = Gtk.Image.new_from_icon_name(f"{device['icon'] if device['icon'] != 'unknown' else 'bluetooth'}-symbolic")
        icon.get_style_context().add_class("wifi-icon")
        battery_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        separator_label = Gtk.Label(label=" - ")
        battery_level = self.dbusbluez.get_connected_battery(device['address']) if device['connected'] and device['paired'] else 'Unknown'
        battery_label = Gtk.Label(label=f"{battery_level}%")
        no_level = ["Unknown", None]
        battery_icon = Gtk.Image.new_from_icon_name(f"{self.window_utils.get_battery_icon(level=int(battery_level)) if battery_level not in no_level else 'battery-missing-symbolic'}")
        battery_icon.set_valign(Gtk.Align.CENTER)
        battery_container.append(separator_label)
        battery_container.append(battery_icon)
        battery_container.append(battery_label)
        battery_container.set_visible(True if device["connected"] else False)
        name_container.append(name)
        bottom_container.append(subname)
        bottom_container.append(battery_container)
        name_container.append(bottom_container)
        connect_btn = Gtk.Button(label=f"{'Disconnect' if device['connected'] else 'Connect' if device['paired'] else 'Pair'}")
        connect_btn.get_style_context().add_class("connect-button")
        connect_btn.set_halign(Gtk.Align.END)
        connect_btn.connect("clicked", lambda x, address=device["address"], device=dev_name: self.on_connect_pressed(address, device) )
        loader_container =Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        spinner = Gtk.Image.new_from_icon_name("process-working-symbolic")
        spinner.get_style_context().add_class("spinner")
        loading_label = Gtk.Label(label=f"{'Disconnecting...' if device['connected'] else 'Connecting...' if device['paired'] else 'Pairing...'}")
        loader_container.append(spinner)
        loader_container.append(loading_label)
        loader_container.set_visible(False)
        details_btn = Gtk.Button()
        details_btn.set_child(Gtk.Image.new_from_icon_name("info-outline-symbolic"))
        details_btn.get_style_context().add_class("wifi-details-button")
        details_btn.set_margin_end(10)
        details_btn.set_visible(False)
        card.append(icon)
        card.append(name_container)
        card.append(loader_container)
        card.append(details_btn)
        card.append(connect_btn)
        card.get_style_context().add_class("network-card")
        row.set_child(card)
        self.scrolled_bluetooth_container.append(row)
        self.bluetooth_cards_details[dev_name] = {
            "details": device,
            "row": row,
            "card": card,
            "connect_btn": connect_btn,
            "spinner": spinner,
            "subname": subname,
            "loader_container": loader_container,
            "battery_container": battery_container,
            "loading_label": loading_label,
            "details_btn": details_btn,
            "active": active,
            "paired": device["paired"],
            "revealer": None,
            "battery": battery_label,
            "battery_icon": battery_icon
        }
        if row.paired:
            self._setup_details_if_paired(self.bluetooth_cards_details[dev_name])
        if row.is_active:
            card.get_style_context().add_class("active")
        self.scrolled_bluetooth_container.invalidate_sort()
        
    def _sort_func(self, row1, row2):
        if hasattr(row1, "is_active") and hasattr(row2, "is_active"):
            if row1.is_active != row2.is_active:
                return -1 if row1.is_active else 1
        if hasattr(row1, "paired") and hasattr(row2, "paired"):
            if row1.paired != row2.paired:
                return -1 if row1.paired else 1
            if hasattr(row1, "name") and hasattr(row2, "name"):
                return -1 if row1.name < row2.name else 1
        return 0

    
    def update_headers(self, row, before):
        try:
            if row == self.empty_widgets["box"].get_parent():
                row.set_header(None)
                return
            
            if before is None:
                if hasattr(row, "is_active") and row.is_active:
                    row.set_header(self.window_utils.create_header("CONNECTED DEVICES"))
                elif hasattr(row, "paired") and row.paired:
                    row.set_header(self.window_utils.create_header("PAIRED DEVICES"))
                else:
                    row.set_header(self.window_utils.create_header("AVAILABLE DEVICES"))
                return

            if (hasattr(before, "is_active") and hasattr(row, "is_active") and 
                hasattr(before, "paired") and hasattr(row, "paired")):
                
                if before.is_active and not row.is_active and row.paired:
                    row.set_header(self.window_utils.create_header("PAIRED DEVICES"))

                elif before.paired and not row.paired:
                    row.set_header(self.window_utils.create_header("AVAILABLE DEVICES"))
 
                else:
                    row.set_header(None)
            else:
                row.set_header(None)

        except TypeError as e:
            print(f"Error while sorting headers: {e}")

    def update_ui_elements(self, message):
        if "switches" in message:
            if self.internal_update:
                self.internal_update = False
                return
            if "Powered" in message["switches"]:
                power_state = message["switches"]["Powered"]
                if power_state != self.toggle_switch.get_active():
                    self.toggle_switch.handler_block(self.bluetooth_toggle_event)
                    self.toggle_switch.set_active(power_state)
                    self.toggle_switch.handler_unblock(self.bluetooth_toggle_event)
                if not power_state:
                    self._default_state()
                
            if "Discoverable" in message["switches"]:
                discoverable_state = message["switches"]["Discoverable"]
                self.discover_switch.handler_block(self.discover_toggle_event)
                self.discover_switch.set_active(discoverable_state)
                self.discover_switch.handler_unblock(self.discover_toggle_event)

        elif "discovering" in message:
            discovering_state = message["discovering"]

        elif "devices" in message:
            if hasattr(self, "refresh_timeout") and self.refresh_timeout:
                GLib.source_remove(self.refresh_timeout)
                self.reload_icon.get_style_context().remove_class("active")
            if self.empty_widgets["box"].get_parent() is not None:
                self.hide_empty_widgets()
            for device in message["devices"]:
                dev_params = message["devices"][device]
                self.setup_cards(dev_params)

        elif "added_device" in message:
            if self.empty_widgets["box"].get_parent() is not None:
                self.hide_empty_widgets()
            details = message["added_device"]
            if details["name"] not in self.bluetooth_cards_details:
                self.setup_cards(details)

        elif "removed_device" in message:
            to_remove = message["removed_device"]
            if to_remove in self.bluetooth_cards_details:
                self.scrolled_bluetooth_container.remove(self.bluetooth_cards_details[to_remove]["row"])
                if self.bluetooth_cards_details[to_remove]["revealer"] is not None:
                    self.main_overlay.remove_overlay(self.bluetooth_cards_details[to_remove]["revealer"]["revealer"])
                del self.bluetooth_cards_details[to_remove]
                
        elif "trusted" in message:
            name, dev = self._get_device_from_mac(message["trusted"])
            if dev is None:
                return
            if dev["revealer"] is not None:
                if dev["revealer"]["overlay"].internal_update:
                    dev["revealer"]["overlay"].internal_update = False
                    return
                dev["revealer"]["overlay"].trusted_switch.set_active(message["message"]["Trusted"])

        elif "paired" in message:
            name, dev = self._get_device_from_mac(message["paired"])
            if dev is None:
                return
            paired = message["message"]["Paired"]
            dev["paired"] = paired
            dev["row"].paired = paired
            if self.wait_till_paired and paired:
                self.on_sucessfull_connection(message["paired"], {"connection": message["paired"], "message": {"Connected": True}})
            self._setup_details_if_paired(dev)
            self.scrolled_bluetooth_container.invalidate_sort()
            print(f"{name} is now paired")

        elif "battery" in message:
            mac = message["device"]
            battery = message["battery"]
            name, dev = self._get_device_from_mac(mac)
            if dev is None:
                return
            dev["battery"].set_label(f"{battery}%")
            dev["battery_icon"].set_from_icon_name(self.window_utils.get_battery_icon(level=int(battery)))
            dev["battery_container"].set_visible(True)

        elif "update_card" in message:
            details = message["update_card"]
            name = details["name"]
            if name in self.bluetooth_cards_details:
                device = self.bluetooth_cards_details[name]
                device["details"] = details
                device["active"] = details["connected"]
                device["paired"] = details["paired"]
                device["row"].is_active = details["connected"]
                device["row"].paired = details["paired"]
                device["details_btn"].set_visible(details["paired"])
                device["connect_btn"].set_label(f"{'Disconnect' if details['connected'] else 'Connect' if details['paired'] else 'Pair'}")
                device["subname"].set_label(f"{'Connected' if details['connected'] else 'Paired' if details['paired'] else 'Available'}")
                self._setup_details_if_paired(device)
                self.scrolled_bluetooth_container.invalidate_sort()

        elif "connection" in message and "Connected" in message["message"]:
            mac = message["connection"]
            name = self._get_name_from_mac(mac)
            if name is None:
                return
            dev = self.bluetooth_cards_details[name]
            if self.wait_till_paired and message["message"]["Connected"]:
                return
            self.on_sucessfull_connection(mac, message)


    def on_connect_pressed(self, address, device, *args):
        if device in self.bluetooth_cards_details:
            dev = self.bluetooth_cards_details[device]
            dev["connect_btn"].set_visible(False)
            dev["details_btn"].set_visible(False)
            dev["spinner"].get_style_context().add_class("active")
            dev["loading_label"].set_label(f"{'Disconnecting...' if dev['active'] else 'Connecting...' if dev['paired'] else 'Pairing...'}")
            dev["loader_container"].set_visible(True)
            self.wait_till_paired = False
            if dev["active"]:
                self.dbusbluez.connect_disconnect_to_device(address, "Disconnect")
            else:
                if not dev['paired']:
                    self.wait_till_paired = True
                self.dbusbluez.connect_disconnect_to_device(address)
    
    def on_sucessfull_connection(self, mac, message):
        name = self._get_name_from_mac(mac)
        if name is None:
            return
        dev = self.bluetooth_cards_details[name]
        dev["active"] = message["message"]["Connected"]
        dev["connect_btn"].set_visible(True)
        dev["details_btn"].set_visible(dev["paired"])
        dev["spinner"].get_style_context().remove_class("active")
        dev["loader_container"].set_visible(False)
        dev["battery_container"].set_visible(False)
        dev["connect_btn"].set_label(f"{'Disconnect' if message['message']['Connected'] else 'Pair' if self.wait_till_paired else 'Connect'}")
        dev["subname"].set_label(f"{'Connected' if dev['active'] else 'Paired' if dev['paired'] else 'Available'}")
        dev["row"].is_active = message["message"]["Connected"]
        dev["row"].paired = dev["paired"]
        if dev["active"]:
            dev["card"].get_style_context().add_class("active")
        else:
            dev["card"].get_style_context().remove_class("active")
        self.scrolled_bluetooth_container.invalidate_sort()
        print(f"{name} updated connected: {message["message"]["Connected"]}")

    def on_discoverable_switch(self, switch, state):
        self.internal_update = True
        self.dbusbluez.toggle_discoverable(switch, state)

    def on_bluetooth_toggle(self, switch, state):
        self.internal_update = True
        self.dbusbluez.toggle_bluetooth(switch, state)
        if not state:
            self._default_state()
            return
    
        self.empty_widgets["loader"].set_visible(True)
        self.empty_widgets["loader"].get_style_context().add_class("active")
        self.empty_widgets["text"].set_label("Loading devices...")
        self.empty_widgets["icon"].set_visible(False)

    def on_refresh(self):
        if self.toggle_switch.get_active():
            self.dbusbluez._get_bluez_objects()
            self.reload_icon.get_style_context().add_class("active")
            def timeout_func():
                self.reload_icon.get_style_context().remove_class("active")
                self.refresh_timeout = None
                return False
            self.refresh_timeout = GLib.timeout_add(5000, timeout_func)
                    

    def _default_state(self):
        while child := self.scrolled_bluetooth_container.get_first_child():
            self.scrolled_bluetooth_container.remove(child)
        for names in self.bluetooth_cards_details.keys():
            if self.bluetooth_cards_details[names]["revealer"] is not None:
                self.main_overlay.remove_overlay(self.bluetooth_cards_details[names]["revealer"]["revealer"])
        self.bluetooth_cards_details = {}
        self.empty_widgets["loader"].set_visible(False)
        self.empty_widgets["box"].set_visible(True)
        self.empty_widgets["icon"].set_visible(True)
        self.empty_widgets["loader"].get_style_context().remove_class("active")
        self.empty_widgets["text"].set_label("Bluetooth is currently disabled")
        if self.empty_widgets["box"].get_parent() is None:
            self.scrolled_bluetooth_container.append(self.empty_widgets["box"])

    def hide_empty_widgets(self):
        if self.empty_widgets["box"].get_parent() is not None:
            row = self.empty_widgets["box"].get_parent()
            if row.get_parent() is not None:
                row.get_parent().remove(row)
            self.empty_widgets["box"].set_visible(False)
            self.empty_widgets["loader"].get_style_context().remove_class("active")
            self.empty_widgets["text"].set_label("Bluetooth is currently disabled")
            self.empty_widgets["icon"].set_visible(True)

    

    def _get_name_from_mac(self, mac):
        for name, items in self.bluetooth_cards_details.items():
            if items["details"]["address"] == mac:
                return name
        return None
    
    def _get_device_from_mac(self, mac):
        name = self._get_name_from_mac(mac)
        if name is None or name not in self.bluetooth_cards_details:
            return None, None
        return name, self.bluetooth_cards_details[name]
    
    def _setup_details_if_paired(self, device):
        if not device["paired"]:
            return
        if not self.loading:
            device["details_btn"].set_visible(True)
        if device["revealer"] is not None:
            return
        revealer = self.window_utils.setup_revealer(self.main_overlay, PopupWindow, "details", self.dbusbluez, device["details"])
        device["revealer"] = revealer
        device["details_btn"].connect("clicked", lambda x, reveal=device["revealer"]["revealer"]: reveal.set_reveal_child(True))
        

    def on_agent_call(self, call_type, device, passkey, callback):
        auth_window = self.auth_windows["overlay"]
        if call_type == "cancel":
            auth_window.on_close()
        if call_type == "confirmation" and passkey is not None:
            from popups.wifi import _v_layer
            _v_layer.header.change_tab("Bluetooth-Tab")
            if not _v_layer.get_visible():
                _v_layer.show()
                _v_layer.present()
            auth_window.callback_for_auth = callback
            auth_window.shown_code.set_label(str(passkey))
            auth_window.confirm_container.set_visible(True)
            self.auth_windows["revealer"].set_reveal_child(True)



class PopupWindow:
    def __init__(self, windowtype, bluezdbus, device, windows):
        self.popups = Popups()
        self.details = {}
        self.bluezdbus = bluezdbus
        self.windowtype = windowtype
        self.device = device
        self.windows = windows
        self.callback_for_auth = None
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
        if self.windowtype == "details":
            self.trusted_switch = Gtk.Switch()
            self.internal_update = False
            self.trusted_switch.set_active(self.device.get("trusted", False))
            self.trusted_switch.connect("state-set", lambda switch, state, address=self.device['address']: self.on_trusted_switch(address, switch, state))
            self.match_names = {
                "Name": "name",
                "MAC Address": "address",
                "Trusted": self.trusted_switch,
            }
            self.icons = {
                "Name": "bluetooth-symbolic",
                "MAC Address": "network-wired-activated-symbolic",
                "Trusted": "security-high-symbolic"
            }
        self.setup_ui()
    
    def setup_ui(self):
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_text = {
            "pairing": "Confirm Pairing",
            "details": "Device Details",
        }
        header_label = Gtk.Label(label=f"{(header_text[self.windowtype]).upper()}")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_hexpand(True)
        header_label.get_style_context().add_class("header-label")
        header_box.append(header_label)
        close_btn = Gtk.Button()
        close_icon = Gtk.Image.new_from_icon_name("window-close-symbolic")
        close_btn.set_child(close_icon)
        close_btn.connect("clicked", lambda x: self.on_close(self.windowtype))
        close_btn.get_style_context().add_class("close-button")
        close_btn.set_halign(Gtk.Align.END)
        close_btn.set_valign(Gtk.Align.CENTER)
        header_box.append(close_btn)
        self.panel_content.append(header_box)
        if self.windowtype == "details":
            self.hor_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.hor_container.set_homogeneous(True)
            self.popups.setup_details(
                match_names=self.match_names,
                match_icons=self.icons,
                details=self.device,
                container=self.hor_container)
            forget_btn = Gtk.Button(label='Forget Device')
           # forget_btn.set_halign(Gtk.Align.CENTER)
            forget_btn.set_hexpand(True)
            forget_btn.connect("clicked", lambda x, device=self.device["address"]: self.on_forget(device))
            forget_btn.get_style_context().add_class("forget-button")
            self.panel_content.append(self.hor_container)
            self.panel_content.append(forget_btn)
        elif self.windowtype == "pairing":
            self.setup_pairing_window()

    def setup_pairing_window(self):
        self.overlay = Gtk.Overlay()
        
        def setup_confirm_layout():
            self.confirm_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            instruction_text = Gtk.Label(label="Does this passkey match your device?")
            self.shown_code = Gtk.Label()
            self.shown_code.set_size_request(-1, 100)
            self.shown_code.get_style_context().add_class("auth-code")
            self.button_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                margin_top= 10,
                margin_bottom=10,
                margin_start=10,
                margin_end=10)
            self.button_container.set_homogeneous(True)
            yes_btn = Gtk.Button(label="YES")
            yes_btn.set_margin_end(10)
            yes_btn.set_margin_start(10)
            yes_btn.connect("clicked", lambda x: self.on_auth_confirm("confirm", True))
            yes_btn.get_style_context().add_class("confirm-button")
            no_btn = Gtk.Button(label="NO")
            no_btn.set_margin_end(10)
            no_btn.set_margin_start(10)
            no_btn.connect("clicked", lambda x: self.on_auth_confirm("confirm", False))
            no_btn.get_style_context().add_class("confirm-button")
            self.button_container.append(no_btn)
            self.button_container.append(yes_btn)
            self.confirm_container.append(instruction_text)
            self.confirm_container.append(self.shown_code)
            self.confirm_container.append(self.button_container)
            self.confirm_container.set_visible(False)
            self.overlay.set_child(self.confirm_container)

        setup_confirm_layout()
        self.panel_content.append(self.overlay)

        
    def hide_all_auth_type(self):
        to_hide = [self.confirm_container]
        for container in to_hide:
            if container.get_visible():
                container.set_visible(False)

    def on_close(self, windowtype="details"):
        self.windows["revealer"].set_reveal_child(False)
        if windowtype == "pairing":
            self.hide_all_auth_type()

    def on_auth_confirm(self, auth_type, state):
        if auth_type == "confirm":
            if self.callback_for_auth:
                self.callback_for_auth(state)
        self.on_close()

    def on_forget(self, device):
        self.bluezdbus.forget_device(device)
        self.on_close()

    def on_trusted_switch(self, address, switch, state):
        self.internal_update = True
        self.bluezdbus.toggle_trusted(address, switch, state)
