import gi
import dbus
import socket
import os
from gi.repository import Gio
import time

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib
_v_layer = None

class BrightnessLayer(Gtk.Window):
    def __init__(self):
        super().__init__(title="Brightness Layer")

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "brightness-control")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 10)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 10)
        self.set_default_size(400, 150)
        self.get_style_context().add_class("brightness-window")
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_container.set_border_width(20)
        self.add(main_container)
        self.notebook = Gtk.Notebook()
        main_container.pack_start(self.notebook, True, True, 0)

        self.hyprctl = HyprctlSocket(self.apply_night_update)
        self.dbusbrightness = DBusBrightness(self.apply_brightness_update)
        self.setup_brightness_tab("Fényerő", tab="brightness")
        self.setup_brightness_tab("Éjszakai fény", tab="night")
        

    def setup_brightness_tab(self, label_text, tab):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox.set_border_width(20)
        hbox_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        #only on brightness tab
        if tab == "brightness":
            current_brightness = self.dbusbrightness.get_brightness(type="percentage")
            adj = Gtk.Adjustment(value=0, lower=1, upper=100, step_increment=1)
            self.brightness_label = Gtk.Label(label=f"{int(current_brightness)}%")
            self.label = self.brightness_label
            self.brightness_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            self.brightness_handler_id = self.brightness_scale.connect("value-changed", self.on_brightness_change)
            self.brightness_scale.set_value(current_brightness)
            self.scale = self.brightness_scale

        #only on nightmode tab
        elif tab == "night":
            adj = Gtk.Adjustment(value=0, lower=1000, upper=6000, step_increment=100)
            self.current_temp = int(self.hyprctl.hyprsunset("temperature"))
            self.switch = Gtk.Switch()
            self.switch_handler_id = self.switch.connect("notify::active", self.on_night_switch)
            self.temp_label = Gtk.Label(label=f"{int(self.current_temp)}K")
            self.label = self.temp_label
            self.temp_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            self.temp_handler_id = self.temp_scale.connect("value-changed", self.on_temp_change)
            self.temp_scale.set_value(self.current_temp)
            self.scale = self.temp_scale
            self.light_status = (self.current_temp != 6000)
            self.switch.set_hexpand(True)
            self.switch.set_active(self.light_status)
            self.switch.get_style_context().add_class("night-switch")
            hbox_top.pack_end(self.switch, True, True, 5)
        
        self.label.set_size_request(40, -1)
        self.label.get_style_context().add_class("percent-text")
        hbox_top.pack_start(self.label, False, False, 5)

        self.scale.get_style_context().add_class("brightness-slider")
        self.scale.set_draw_value(False) # disable value at the top of the slider
        self.scale.set_size_request(250, -1)
        self.scale.set_hexpand(True)
        
        hbox_top.pack_start(self.scale, True, True, 5)

        vbox.pack_start(hbox_top, False, False, 0)

        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        tab_box.set_halign(Gtk.Align.CENTER)
        tab_box.set_valign(Gtk.Align.CENTER)
    
        icon_name = "display-brightness-symbolic" if tab=="brightness" else "night-light-symbolic"
        tab_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        tab_label = Gtk.Label(label=label_text)
    
        tab_box.pack_start(tab_icon, False, False, 0)
        tab_box.pack_start(tab_label, False, False, 0)
        tab_box.show_all()

        page_num = self.notebook.append_page(vbox, tab_box)
        child = self.notebook.get_nth_page(page_num)
        self.notebook.child_set_property(child, "tab-expand", True)
        self.notebook.child_set_property(child, "tab-fill", True)

    def on_brightness_change(self, scale):
        value = int(scale.get_value())
        valuenew = int((int(value) / 100) * int(self.dbusbrightness.get_brightness(type="max")))
        self.dbusbrightness.SetBrightness("intel_backlight", int(valuenew))
        self.brightness_label.set_text(f"{value}%")

    def on_temp_change(self, scale):
        value = scale.get_value()
        self.hyprctl.hyprsunset("temperature", str(value))
        self.temp_label.set_text(f"{int(value)}K")
        self.update_switch(value)

    def update_switch(self, value):
        if value < 6000:
            self.switch.handler_block(self.switch_handler_id)
            self.switch.set_active(True)
            self.switch.handler_unblock(self.switch_handler_id)
        elif value >= 6000:
            self.switch.handler_block(self.switch_handler_id)
            self.switch.set_active(False)
            self.switch.handler_unblock(self.switch_handler_id)

    def on_night_switch(self, switch, state):
        value = switch.get_state()
        if value == True:
            self.hyprctl.hyprsunset("temperature", 2500)
            self.temp_scale.set_value(2500)
        else:
            self.hyprctl.hyprsunset("temperature", 6000)
            self.temp_scale.set_value(6000)

    def apply_brightness_update(self, percentage):
        self.brightness_scale.handler_block(self.brightness_handler_id)
        self.brightness_scale.set_value(percentage)
        self.brightness_label.set_text(f"{percentage}%")
        self.brightness_scale.handler_unblock(self.brightness_handler_id)

    def apply_night_update(self, temperature):
        try:
            if int(temperature) != int(self.current_temp):
                self.current_temp = int(temperature)
                self.temp_scale.handler_block(self.temp_handler_id)
                self.temp_scale.set_value(int(temperature))
                self.temp_label.set_text(f"{int(temperature)}K")
                self.temp_scale.handler_unblock(self.temp_handler_id)
                self.update_switch(int(temperature))
        except Exception as e:
            print(e)
            return False


class HyprctlSocket():
    def __init__(self, callback=None):
        self.update_gui = callback
        runtime = os.environ['XDG_RUNTIME_DIR']
        instance_sig = os.environ['HYPRLAND_INSTANCE_SIGNATURE']
        self.hypr_socket_path=f"{runtime}/hypr/{instance_sig}/.socket.sock"
        self.sunset_socket_path=f"{runtime}/hypr/{instance_sig}/.hyprsunset.sock"
        GLib.timeout_add(500, self.update_temp)

    def hyprsunset(self, attr=str, value=None):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.connect(self.sunset_socket_path)
                if value is not None:
                    cmd = f"{attr} {value}"
                else:
                    cmd = f"{attr}"
                client.sendall(cmd.encode('utf-8'))
                response = client.recv(4096)
                return response.decode('utf-8')
        except Exception as e:
            return e

    def update_temp(self):
        try:
            new_temp = self.hyprsunset("temperature")
            GLib.idle_add(self.update_gui, new_temp)
        except Exception as e:
            return e
        return True

    
class DBusBrightness():
    def __init__(self, callback=None):
        self.last_internal_update = 0
        self.on_change_callback = callback
        self.brightness_path = "/sys/class/backlight/intel_backlight/brightness"
        self.bus = dbus.SystemBus()
        self.proxy = self.bus.get_object(
            "org.freedesktop.login1", "/org/freedesktop/login1/session/auto"
            )
        self.interface = dbus.Interface(self.proxy, "org.freedesktop.login1.Session")

        
        file = Gio.File.new_for_path(self.brightness_path)
        self.monitor = file.monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.monitor.connect("changed", self.on_file_changed)


    def SetBrightness(self, device=str, value=int):
        self.last_internal_update = time.time()
        try:
            self.interface.SetBrightness("backlight", device, dbus.UInt32(value))
        except dbus.DBusException as e:
            self.ignore_next_change = False
            print(f"Error setting brightness via DBus: {e}")

    @staticmethod
    def get_brightness(type="percentage"):
        try:
            base_path = "/sys/class/backlight/intel_backlight"
            with open(f"{base_path}/max_brightness", "r") as f:
                max_brightness = int(f.read().strip())
            with open(f"{base_path}/brightness", "r") as f:
                current_brightness = int(f.read().strip())
            if type == "percentage":
                return int(current_brightness) / int(max_brightness) * 100
            elif type == "raw":
                return current_brightness 
            elif type == "max":
                return max_brightness
        except:
            return 0
        
    def on_file_changed(self, monitor, file, other_file, event_type):
        if event_type != Gio.FileMonitorEvent.CHANGED:
            return
        if (time.time() - self.last_internal_update) < 0.2:
            return
        if hasattr(self, '_update_pending') and self._update_pending:
            return
        self._update_pending = True
        try:
            percentage = self.get_brightness("percentage")
            if self.on_change_callback:
                GLib.idle_add(self.on_change_callback, int(percentage))
        except Exception as e:
                print(f"Olvasási hiba: {e}")
        finally:
            self._update_pending = False
        return False


def init_layer():
    global _v_layer
    if _v_layer is None:
        _v_layer = BrightnessLayer()
        _v_layer.connect("delete-event", lambda w, e: w.hide() or True)

def toggle_layer():
    global _v_layer
    if _v_layer.get_visible():
        _v_layer.hide()
    else:
        _v_layer.show_all()
        _v_layer.present()

def hide_layer():
    global _v_layer
    _v_layer.hide()

