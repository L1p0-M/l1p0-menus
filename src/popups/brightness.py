import gi
import socket
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib, Gio
from ..assets.utils import window_utils, GtkLayerShellUtils, HeaderButtons
_v_layer = None


@Gtk.Template(resource_path="/l1p0-menus/ui/header_buttons.ui")
class HeaderButton(Gtk.Button):
    __gtype_name__ = 'HeaderButton'

    header_button_image = Gtk.Template.Child()
    header_button_name = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image = self.get_template_child(HeaderButton, "header_button_image")
        self.name = self.get_template_child(HeaderButton, "header_button_name")
        self.init_template()

@Gtk.Template(resource_path="/l1p0-menus/ui/brightness.ui")
class BrightnessLayer(Gtk.Window):
    __gtype_name__ = 'brightness_window'
    main_container = Gtk.Template.Child()
    main_header_container = Gtk.Template.Child()
    bright_button = Gtk.Template.Child()
    night_button = Gtk.Template.Child()
    tabs = Gtk.Template.Child()
    brightness_label = Gtk.Template.Child()
    brightness_scale = Gtk.Template.Child()
    night_label = Gtk.Template.Child()
    night_scale = Gtk.Template.Child()
    night_switch = Gtk.Template.Child()

    def __init__(self, config):
        super().__init__(title="Brightness Layer")
        self.config = config
        self.shellutils = GtkLayerShellUtils(self, "brightness")
        self.load_config(self.config)
        self.set_default_size(400, 150)
        self.init_template()
        self.tabs = self.get_template_child(BrightnessLayer, "tabs")
        self.night_button = self.get_template_child(BrightnessLayer, "night_button")
        self.bright_button = self.get_template_child(BrightnessLayer, "bright_button")
        self.header_button = HeaderButtons(buttons={
            "Night-Tab": self.night_button,
            "Bright-Tab": self.bright_button
        }, tabs=self.tabs)
        self.night_button.header_button_image.set_from_icon_name("weather-clear-night-symbolic")
        self.night_button.header_button_name.set_text("Night Light")
        self.bright_button.header_button_image.set_from_icon_name("display-brightness-high-symbolic")
        self.bright_button.header_button_name.set_text("Brightness")
      #  self.get_style_context().add_class("brightness-window")
      #  main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
      #  main_container.set_margin_start(0)
      #  main_container.add_css_class("brightness-layer")
        self.brightness = DBusBrightness(self.apply_brightness_update)
        self.hyprsunset = HyprSunsetSocket(self.apply_night_update)
      #  self.set_child(main_container)
      #  self.brightness_widgets = {}
      #  self.night_widgets = {}
        self.night_preset = 2500
        self.setup_tabs()
      #  main_container.append(self.main_header_container)
      #  main_container.append(self.tabs)

    def load_config(self, config):
        if config != self.config:
            self.config = config
        anchor, margin = self.shellutils.process_config(config, default_anchor="top-right", default_margin=[10, 10])
        self.shellutils.setup_layer_shell(anchor, margin)
        if isinstance(config, dict):
            self.night_preset = int(self.config.get('night_preset', 2500))
        else:
            self.night_preset = 2500
        

    def setup_tabs(self):
        current_brightness = self.brightness.get_brightness()
        brightness_scale = self.get_template_child(BrightnessLayer, "brightness_scale")
        brightness_label = self.get_template_child(BrightnessLayer, "brightness_label")
        brightness_handler = brightness_scale.connect("value-changed", self.on_brightness_change)
        night_scale = self.get_template_child(BrightnessLayer, "night_scale")
        night_label = self.get_template_child(BrightnessLayer, "night_label")
        night_handler = night_scale.connect("value-changed", self.on_temp_change)
        night_switch = self.get_template_child(BrightnessLayer, "night_switch")
        night_switch_handler = night_switch.connect("notify::active", self.on_night_switch)
        self.night_widgets = {
            "scale": night_scale,
            "scale_handler": night_handler,
            "label": night_label,
            "switch": self.get_template_child(BrightnessLayer, "night_switch"),
            "switch_handler": night_switch_handler,
        }
        self.brightness_widgets = {
            "scale": brightness_scale,
            "scale_handler": brightness_handler,
            "label": brightness_label,
        }
        brightness_scale.set_value(current_brightness)
        brightness_label.set_text(f"{int(round(current_brightness))}%")
        current_temp = self.hyprsunset.hyprsunset("temperature")     
        light_status = (int(current_temp) < 6000)
        night_switch.set_active(light_status)
        night_scale.set_value(int(current_temp))
        night_label.set_text(f"{int(current_temp)}K")

    # def setup_tabs(self):
    #     self.tabs = Gtk.Stack()
    #     self.tabs.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
    #     main_brightness_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    #     main_nightlight_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    #     self.brightness_page = self.tabs.add_named(main_brightness_container, "Bright-Tab")
    #     self.nightlight_page = self.tabs.add_named(main_nightlight_container, "Night-Tab")
    #     self.main_header_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
    #         margin_start = 10,
    #         margin_end = 10,
    #         margin_top = 10,
    #         margin_bottom = 10 )
    #     self.main_header_container.get_style_context().add_class("header")
    #     self.main_header_container.set_homogeneous(True)
    #     self.tab_buttons = {}
    #     self.header = Header(self.main_header_container, self.tab_buttons, self.tabs)
    #     self.header.setup_header("Brightness", "display-brightness-high-symbolic", "Bright-Tab")
    #     self.setup_brightness_tab(container = main_brightness_container)
    #     self.header.setup_header("Night Light", "weather-clear-night-symbolic", "Night-Tab")
    #     self.setup_night_tab(container = main_nightlight_container)

    # def setup_brightness_tab(self, container):
    #     vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
    #         spacing=15,
    #         margin_start=20,
    #         margin_end=20,
    #         margin_top=20,
    #         margin_bottom=20,)
    #     hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    #     current_brightness = self.brightness.get_brightness()
    #     adj = Gtk.Adjustment(value=0, lower=1, upper=100, step_increment=1)
    #     label = Gtk.Label(label=f"{int(round(current_brightness))}%")
    #     scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
    #     scale.set_value(current_brightness)
    #     scale_handler = scale.connect("value-changed", self.on_brightness_change)
    #     self.brightness_widgets = {
    #         "scale": scale,
    #         "scale_handler": scale_handler,
    #         "label": label,
    #         "container_horizontal": hbox
    #     }
    #     self.add_widgets_to_layout(self.brightness_widgets)
    #     vbox.append(hbox)
    #     container.append(vbox)


    # def setup_night_tab(self, container):
    #     vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
    #         spacing=15,
    #         margin_start=20,
    #         margin_end=20,
    #         margin_top=20,
    #         margin_bottom=20,)
    #     hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    #     adj = Gtk.Adjustment(value=0, lower=1000, upper=6000, step_increment=100)
    #     if not self.hyprsunset.hyprsunset_found:
    #         not_found_label = Gtk.Label(label="Hyprsunset not found")
    #         not_found_label.get_style_context().add_class("error-not-found")
    #         container.append(not_found_label)
    #         return
    #     current_temp = self.hyprsunset.hyprsunset("temperature")     
    #     switch = Gtk.Switch()
    #     light_status = (int(current_temp) < 6000)
    #     switch.set_active(light_status)
    #     switch.get_style_context().add_class("night-switch")
    #     switch_handler = switch.connect("notify::active", self.on_night_switch)
    #     label = Gtk.Label(label=f"{int(current_temp)}K")
    #     scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
    #     scale.set_value(int(current_temp))
    #     scale_handler = scale.connect("value-changed", self.on_temp_change)
    #     self.night_widgets = {
    #         "scale": scale,
    #         "scale_handler": scale_handler,
    #         "label": label,
    #         "switch": switch,
    #         "switch_handler": switch_handler,
    #         "container_horizontal": hbox
    #     }
    #     self.add_widgets_to_layout(self.night_widgets)
    #     vbox.append(hbox)
    #     container.append(vbox)


    # def add_widgets_to_layout(self, widgets):
    #     try:
    #         available_keys = []
    #         for key, widget in widgets.items():
    #             available_keys.append(key) 
    #         if "label" in available_keys:
    #             label = widgets["label"]
    #             label.set_size_request(40, -1)
    #             label.get_style_context().add_class("percent-text")
    #             label.set_margin_start(5)
    #             label.set_margin_end(5)
    #         if "scale" in available_keys:
    #             scale = widgets["scale"]
    #             scale.get_style_context().add_class("brightness-slider")
    #             scale.set_draw_value(False)
    #             scale.set_size_request(200, -1)
    #             scale.set_hexpand(True)
    #             scale.set_margin_start(5)
    #             scale.set_margin_end(5)
    #         if "container_horizontal" in available_keys:
    #             hbox =  widgets["container_horizontal"]
    #             hbox.append(widgets["label"])
    #             hbox.append(widgets["scale"])
    #             if "switch" in available_keys:
    #                 hbox.append(widgets["switch"])
    #     except Exception as e:
    #         print(f"Failed to setup ui: {e}")


    def on_brightness_change(self, scale):
        value = int(scale.get_value())
        valuenew = int((int(value) / 100) * int(self.brightness.max_brightness))
        self.brightness.SetBrightness("intel_backlight", int(valuenew))
        self.brightness_widgets["label"].set_text(f"{value}%")

    def on_temp_change(self, scale):
        value = scale.get_value()
        self.hyprsunset.hyprsunset("temperature", str(value))
        self.night_widgets["label"].set_text(f"{int(value)}K")
        self.update_switch(value)

    def update_switch(self, value):
        switch = self.night_widgets["switch"]
        switch_handler = self.night_widgets["switch_handler"]
        if value < 6000:
            switch.handler_block(switch_handler)
            switch.set_active(True)
            switch.handler_unblock(switch_handler)
        elif value >= 6000:
            switch.handler_block(switch_handler)
            switch.set_active(False)
            switch.handler_unblock(switch_handler)

    def on_night_switch(self, switch, state):
        value = switch.get_state()
        if value == True:
            self.hyprsunset.hyprsunset("temperature", int(self.night_preset))
            self.apply_night_update(int(self.night_preset))
        else:
            self.hyprsunset.hyprsunset("temperature", 6000)
            self.apply_night_update(6000)

    def apply_brightness_update(self, percentage):
        scale = self.brightness_widgets["scale"]
        if percentage != scale.get_value():
            scale.handler_block(self.brightness_widgets["scale_handler"])
            scale.set_value(percentage)
            self.brightness_widgets["label"].set_text(f"{percentage}%")
            scale.handler_unblock(self.brightness_widgets["scale_handler"])

    def apply_night_update(self, temperature):
        try:
            scale = self.night_widgets["scale"]
            scale.handler_block(self.night_widgets["scale_handler"])
            scale.set_value(int(temperature))
            self.night_widgets["label"].set_text(f"{int(temperature)}K")
            scale.handler_unblock(self.night_widgets["scale_handler"])
            self.update_switch(int(temperature))
        except Exception as e:
            print(f"Error during gui update: {e}")
            return False


class HyprSunsetSocket():
    def __init__(self, callback=None):
        self.update_gui = callback
        self.internal_update = True
        runtime = os.environ['XDG_RUNTIME_DIR']
        try:
            instance_sig = os.environ['HYPRLAND_INSTANCE_SIGNATURE']
            self.sunset_socket_path=f"{runtime}/hypr/{instance_sig}/.hyprsunset.sock"
            if os.path.exists(self.sunset_socket_path):
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(0.2)
                    client.connect(self.sunset_socket_path)
                    self.hyprsunset_found = True
            else:
                self.hyprsunset_found = False
                return
        except Exception as e:
            print(f"Hyprsunset Disabled: {e}")
            self.hyprsunset_found = False
            return None
        self.current_temp = 6000
        self._update_loop_id = None
        
    def hyprsunset(self, attr:str, value=None):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(0.2)
                client.connect(self.sunset_socket_path)
                if value is not None:
                    self.internal_update = True
                    cmd = f"{attr} {value}"
                else:
                    cmd = f"{attr}"
                client.sendall(cmd.encode('utf-8'))
                response = client.recv(4096)
                return response.decode('utf-8')
        except Exception as e:
            print(f"Error while getting/setting temperature: {e}")
            return None

    def update_temp(self):
        try:    
            if self.internal_update:
                self.internal_update = False
                return True
    
            new_temp = self.hyprsunset("temperature")
            if new_temp is None or not str(new_temp).isdigit():
                return True
            
            if int(new_temp) != int(self.current_temp):
                self.current_temp = new_temp
                GLib.idle_add(self.update_gui, new_temp)
            return True
        except Exception as e:
            print(f"Error while updateing temp: {e}")
            return True

    def start_update_loop(self):
        if not hasattr(self, "_update_loop_id"):
            return
        global _v_layer
        if self._update_loop_id is not None:
            GLib.source_remove(self._update_loop_id)
            self._update_loop_id = None
        self.was_visible = _v_layer.get_visible()
        if self.was_visible:
            self._update_loop_id = GLib.timeout_add(200, self.update_temp)
        else:
            self._update_loop_id = GLib.timeout_add_seconds(10, self.update_temp)
    
class DBusBrightness():
    def __init__(self, callback=None):
        self.internal_update = False
        self.on_change_callback = callback
        self.brightness_path = "/sys/class/backlight/intel_backlight/brightness"
        self.max_brightness = self.get_brightness(type="max")
        self.dbus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.dbus_name = "org.freedesktop.login1"
        self.dbus_path = "/org/freedesktop/login1/session/auto"
        self.dbus_object = "org.freedesktop.login1.Session"
        self.proxy = Gio.DBusProxy.new_sync(
            self.dbus,
            Gio.DBusProxyFlags.NONE,
            None,
            self.dbus_name,
            self.dbus_path,
            self.dbus_object,
            None
        )

        file = Gio.File.new_for_path(self.brightness_path)
        self.monitor = file.monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.monitor.connect("changed", self.on_file_changed)

    def SetBrightness(self, device:str, value:int):
        parameters = GLib.Variant('(ssu)', ("backlight", device, int(value)))
        self.internal_update = True
        try:
            self.dbus.call(
                self.dbus_name,
                self.dbus_path,
                self.dbus_object,
                "SetBrightness",
                parameters,
                None,
                Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION,
                -1,
                None
            )
        except Exception as e:
            print(f"Error occured while changing brightness: {e}")

    def get_brightness(self, type="percentage"):
        try:
            base_path = "/sys/class/backlight/intel_backlight"
            with open(f"{base_path}/max_brightness", "r") as f:
                max_brightness = float(f.read().strip())
            with open(f"{base_path}/brightness", "r") as f:
                current_brightness = float(f.read().strip())
            if type == "percentage":
                return int(round(float(current_brightness) / float(max_brightness) * 100))
            elif type == "raw":
                return current_brightness 
            elif type == "max":
                return max_brightness
        except Exception as e:
            print(f"Error while getting brightness: {e}")
            return 0
        
    def on_file_changed(self, monitor, file, other_file, event_type):
        if event_type != Gio.FileMonitorEvent.CHANGED:
            return
        if self.internal_update == True:
            self.internal_update = False
            return
        try:
            percentage = self.get_brightness("percentage")
            if self.on_change_callback:
                GLib.idle_add(self.on_change_callback, int(percentage))
        except Exception as e:
                print(f"Olvasási hiba: {e}")
        finally:
            self.internal_update = False
        return False

def init_layer(config):
    try:
        global _v_layer
        if _v_layer is None:
            _v_layer = BrightnessLayer(config)
            if 'HYPRLAND_INSTANCE_SIGNATURE' in os.environ:
                _v_layer.hyprsunset.start_update_loop()
            _v_layer.connect("close-request", lambda w, e: w.hide() or True)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize BrightnessLayer: {e}")

def toggle_layer():
    global _v_layer
    if _v_layer.get_visible():
        _v_layer.hide()
    else:
       # _v_layer.header.change_tab("Bright-Tab")
        _v_layer.header_button.change_tab("Bright-Tab")
        _v_layer.show()
        _v_layer.present()
    if 'HYPRLAND_INSTANCE_SIGNATURE' in os.environ:
        _v_layer.hyprsunset.start_update_loop()

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

