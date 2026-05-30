import gi
import pulsectl
import threading

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib
from ..assets.utils import Header, window_utils, GtkLayerShellUtils
_v_layer = None


class VolumeLayer(Gtk.Window):
    def __init__(self, config):
        super().__init__(title="Audio Layer")
        self.config = config
        self.pulseaudio = Pulseaudio(self.update_ui_elements)
        self.shellutils = GtkLayerShellUtils(self, "audio")
        self.load_config(self.config)
        self.set_default_size(400, 150)
        self.get_style_context().add_class("audio-window")
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_container.get_style_context().add_class("audio-layer")
        self.main_container.set_margin_start(0)
        self.window_utils = window_utils()
        self.overlay = Gtk.Overlay()
        self.set_child(self.overlay)
        self.overlay.set_child(self.main_container)
        self.setup_header()
        self.main_container.append(self.main_header_container)
        self.mic_widgets = {}
        self.vol_widgets = {}
        self.mic_window = {}
        self.vol_window = {}
        self.setup_tab(is_mic=False, container = self.main_vol_container)
        self.setup_tab(is_mic=True, container = self.main_mic_container)
        self.main_container.append(self.tabs)

    def load_config(self, config):
        if self.config != config:
            self.config = config
        anchor, margin = self.shellutils.process_config(config, default_anchor="top-right", default_margin=[10, 10])
        self.shellutils.setup_layer_shell(anchor, margin)

    def setup_header(self):
        self.tabs = Gtk.Stack()
        self.tabs.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.main_mic_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_vol_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.volume_page = self.tabs.add_named(self.main_vol_container, "Volume-Tab")
        self.mic_page = self.tabs.add_named(self.main_mic_container, "Mic-Tab")
        self.main_header_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
            margin_start = 10,
            margin_end = 10,
            margin_top = 10,
            margin_bottom = 10 )
        self.main_header_container.get_style_context().add_class("header")
        self.main_header_container.set_homogeneous(True)
        self.tab_buttons = {}
        self.header = Header(self.main_header_container, self.tab_buttons, self.tabs)
        self.header.setup_header("Volume", "audio-speakers-symbolic", "Volume-Tab")
        self.header.setup_header("Mic", "microphone-sensitivity-high-symbolic", "Mic-Tab")

        
    def setup_tab(self, is_mic, container):
        current_window = self.window_utils.setup_revealer(overlay=self.overlay, popupwindow=PopupWindow, is_mic=is_mic, pulseaudio=self.pulseaudio)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
            spacing=15,
            margin_start=20,
            margin_end=20,
            margin_top=20,
            margin_bottom=20,)
        hbox_control = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        initial_values = self.pulseaudio.get_initial_values(is_mic)
        adj = Gtk.Adjustment(value=0, lower=0, upper=1, step_increment=0.01)
        percent_label = Gtk.Label(label=f"{int(round((initial_values["volume"])*100))}%")
        percent_label.get_style_context().add_class("percent-text")
        percent_label.set_halign(Gtk.Align.START)
        percent_label.set_size_request(40, -1)
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        scale.get_style_context().add_class("volume-slider")
        scale.set_value(initial_values["volume"])
        self.update_slider_css_class(is_mic, initial_values["mute_status"], scale)
        scale_handler = scale.connect("value-changed", self.pulseaudio.on_volume_change, is_mic, percent_label)
        scale.set_draw_value(False)
        scale.set_size_request(200, -1)
        mute_btn = Gtk.ToggleButton()
        mute_btn.set_child(initial_values["mute_icon"])
        mute_btn.set_active(initial_values["mute_status"])
        mute_btn_handler = mute_btn.connect("toggled", self.pulseaudio.on_mute_toggle, is_mic, self.update_slider_css_class)
        mute_btn.set_halign(Gtk.Align.END)
        menu_btn = Gtk.Button()
        menu_btn.get_style_context().add_class("audio-menu-button")
        menu_btn.set_child(Gtk.Image.new_from_icon_name("open-menu-symbolic"))
        menu_btn.connect("clicked", lambda x, reveal=current_window["revealer"]: reveal.set_reveal_child(True))
        menu_btn.set_halign(Gtk.Align.END)
        vbox.append(hbox_control)
        hbox_control.append(percent_label)
        hbox_control.append(scale)
        hbox_control.append(mute_btn)
        hbox_control.append(menu_btn)
        container.append(vbox)
        
        widgets = {
            "label" : percent_label,
            "scale" : scale,
            "scale_handler": scale_handler,
            "mute_btn": mute_btn,
            "mute_btn_handler": mute_btn_handler,
            "menu_btn": menu_btn
        }
        if is_mic:
            self.mic_widgets = widgets
            self.mic_window = current_window
        else:
            self.vol_widgets = widgets
            self.vol_window = current_window


    def update_slider_css_class(self, is_mic, mute_status=None, scale_widget=None):
        if mute_status is None:
            mute_status = self.get_mute_status(is_mic)
        if scale_widget is None:
            scale_widget = self.mic_widgets["scale"] if is_mic else self.vol_widgets["scale"]
        if mute_status:
            scale_widget.get_style_context().add_class("muted")
        else:
            scale_widget.get_style_context().remove_class("muted")

    def update_ui_elements(self, ev):      
        try:
            if ev.facility == pulsectl.PulseEventFacilityEnum.server:
                self.mic_window["overlay"].setup_devices()
                self.vol_window["overlay"].setup_devices()
                self.mic_window["overlay"].update_ui_for_new_defaults(is_mic=True)
                self.vol_window["overlay"].update_ui_for_new_defaults(is_mic=False)
                return False
            
            new_properties = {}
            if ev.facility == pulsectl.PulseEventFacilityEnum.sink:
                sink = self.pulseaudio.pulse.sink_info(ev.index)
                event_type = sink
                widgets = self.vol_widgets
                is_mic = False
                subname = "vol"

            if ev.facility == pulsectl.PulseEventFacilityEnum.source:
                source = self.pulseaudio.pulse.source_info(ev.index)
                event_type = source
                widgets = self.mic_widgets
                is_mic = True
                subname = "mic"

            default_device = self.pulseaudio.default_device[subname]
            device_name = event_type.name
              
            if self.pulseaudio.last_state[subname].get(device_name) is None:
                self.pulseaudio.last_state[subname][device_name] = { "volume": 1, "mute_status": False}
            last_properties = self.pulseaudio.last_state[subname][device_name]

            if last_properties:
                if device_name == default_device:

                    new_properties[device_name] = {
                        "mute_status": event_type.mute,
                        "volume": event_type.volume.values[0]
                    }

                    if new_properties[device_name]["volume"] != last_properties["volume"]:
                        print("volume change!!")
                        widgets["scale"].handler_block(widgets["scale_handler"])
                        widgets["scale"].set_value(new_properties[device_name]["volume"])
                        widgets["label"].set_label(f"{int(round(new_properties[device_name]["volume"] * 100))}%")
                        widgets["scale"].handler_unblock(widgets["scale_handler"])
                        
                    if new_properties[device_name]["mute_status"] != last_properties["mute_status"]:
                        print("mute change!!")
                        muted = new_properties[device_name]["mute_status"]
                        widgets["mute_btn"].handler_block(widgets["mute_btn_handler"])
                        widgets["mute_btn"].set_active(muted)
                        widgets["mute_btn"].set_child(self.pulseaudio.get_mute_icon(is_mic, muted))
                        self.update_slider_css_class(is_mic, new_properties[device_name]["mute_status"], widgets["scale"])
                        widgets["mute_btn"].handler_unblock(widgets["mute_btn_handler"])

            for keys in new_properties[device_name].keys():
                last_properties[keys] = new_properties[device_name][keys]

        except Exception as e:
            print(f"Lekérdezési hiba: {e}")
        finally:
            self.pulseaudio.update_id = None
        return False

class PopupWindow:
    def __init__(self, is_mic, pulseaudio, windows):
        self.window = windows
        self.Pulse = pulseaudio
        self.is_mic = is_mic
        self.panel = Gtk.ScrolledWindow()
        self.panel.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.panel.set_propagate_natural_height(True)
        self.panel.set_max_content_height(200)
        self.panel.set_min_content_height(100)
        self.panel.add_css_class("audio-device-menu")
        self.panel.set_size_request(200, 150)
        self.panel_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_start=20,
            margin_end=20,
            margin_top=20,
            margin_bottom=20
            )
        self.vol_buttons = {}
        self.mic_buttons = {}
        self.device_dict = {}
        self.setup_ui()
        self.panel.set_child(self.panel_content)
    
    def setup_ui(self):
        close_btn = Gtk.Button()
        close_icon = Gtk.Image.new_from_icon_name("window-close-symbolic")
        close_btn.set_child(close_icon)
        close_btn.connect("clicked", lambda x: self.window["revealer"].set_reveal_child(False))
        close_btn.get_style_context().add_class("close-button")
        close_btn.set_halign(Gtk.Align.END)
        self.panel_content.append(close_btn)
        self.devices_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.setup_devices()
        self.panel_content.append(self.devices_container)

    def setup_devices(self):
        while child := self.devices_container.get_first_child():
            self.devices_container.remove(child)
        if self.is_mic:
            devices = [d for d in self.Pulse.pulse.source_list() if 'monitor' not in d.name.lower()]
            self.mic_buttons = {}
            buttons = self.mic_buttons
        else:
            devices = self.Pulse.pulse.sink_list()
            self.vol_buttons = {}
            buttons = self.vol_buttons
        for d in devices:
            self.device_dict[d.description] = d.name
            device_name_button = Gtk.Button(label=f"{d.description}")
            buttons[f"{d.name}"] = device_name_button
            self.devices_container.append(device_name_button)
            device_name_button.connect("clicked", lambda x, device_name=d.name, is_mic=self.is_mic: self.Pulse.on_device_change(is_mic, device_name, self.update_ui_for_new_defaults))
            device_name_button.get_style_context().add_class("audio-device-button")

        self.update_button_css(self.is_mic)
            
    
    def update_button_css(self, is_mic, dev_name=None):
        buttons = self.mic_buttons if is_mic else self.vol_buttons
        default_device = dev_name or self.Pulse.get_default_device_name(is_mic)

        for names, button in buttons.items():
            if  default_device == names:
                button.get_style_context().add_class("active")
            else:
                button.get_style_context().remove_class("active")

    def update_ui_for_new_defaults(self, is_mic, dev_name=None):
        self.update_button_css(is_mic, dev_name)
        values = self.Pulse.get_initial_values(is_mic)
        widgets = self.main_window.mic_widgets if is_mic else self.main_window.vol_widgets
        widgets["scale"].handler_block(widgets["scale_handler"])
        widgets["mute_btn"].handler_block(widgets["mute_btn_handler"])
        widgets["scale"].set_value(values["volume"])
        widgets["label"].set_label(f"{int(round(values["volume"] * 100))}%")
        widgets["mute_btn"].set_active(values["mute_status"])
        widgets["mute_btn"].set_child(values["mute_icon"])
        self.main_window.update_slider_css_class(is_mic, values["mute_status"], widgets["scale"])
        widgets["scale"].handler_unblock(widgets["scale_handler"])
        widgets["mute_btn"].handler_unblock(widgets["mute_btn_handler"])

class Pulseaudio:
    def __init__(self, callback=None):
        self.pulse = pulsectl.Pulse('audio-layer')
        self.callback = callback
        self.last_state = {"vol": {}, "mic": {}}
        self.default_device = {"vol": None, "mic": None}
        self.internal_update = False
        self.update_id = None
        self.stop_event = threading.Event()
        threading.Thread(target=self.listen, daemon=True).start()

    def listen(self):
        with pulsectl.Pulse('event-listener') as pulse_listener:
            pulse_listener.event_mask_set('sink', 'server', 'source')
            pulse_listener.event_callback_set(self.on_pulse_event)
            print("PulseAudio event listener started...")
            try:
                while not self.stop_event.is_set():
                    pulse_listener.event_listen(timeout=0.5)
            except Exception as e:
                print(f"Error during listening for Pulseaudio events: {e}")

    def on_pulse_event(self, ev):
        try:
            if self.internal_update:
                self.internal_update = False
                return
            if self.callback and ev.t == pulsectl.PulseEventTypeEnum.change:
                if self.update_id:
                    GLib.source_remove(self.update_id)

                self.update_id = GLib.timeout_add(50, self.callback, ev)
        except Exception as e:
            print(f"Failed to call the ui update function: {e}")
        finally:
            self.internal_update = False


    def get_initial_values(self, is_mic):
        try:
            volume = self.get_volume(is_mic)
            mute_status = self.get_mute_status(is_mic)
            default_device = self.get_default_device_name(is_mic)
            mute_icon = self.get_mute_icon(is_mic, mute_status)

            values = {
                "volume": volume,
                "mute_status": mute_status,
                "default_device": default_device,
                "mute_icon": mute_icon
            }
            self.last_state[f"{"mic" if is_mic else "vol"}"][default_device] = values
            self.default_device[f"{"mic" if is_mic else "vol"}"] = default_device
            return values

        except Exception as e:
            print(f"Failed to get initial values: {e}")

    def get_active_device(self, is_mic):
        info = self.pulse.server_info()
        name = info.default_source_name if is_mic else info.default_sink_name
        return self.pulse.get_source_by_name(name) if is_mic else self.pulse.get_sink_by_name(name)
    
    def get_volume(self, is_mic):
        try:
            return self.get_active_device(is_mic).volume.value_flat
        except: 
            return 0
        
    def get_mute_status(self, is_mic):
        try:
            return bool(self.get_active_device(is_mic).mute)
        except:
            return False

    def get_default_device_name(self, is_mic):
        info = self.pulse.server_info()
        return info.default_source_name if is_mic else info.default_sink_name
    
    def get_mute_icon(self, is_mic, mute_status=None):
        mute_icon = None
        if mute_status is not None:
            mute_icon = mute_status
        else:
            mute_icon = self.get_mute_status(is_mic)
        if mute_icon:    
            return Gtk.Image.new_from_icon_name("audio-volume-muted-symbolic")
        else:
            return Gtk.Image.new_from_icon_name("audio-volume-high-symbolic")
            
    def on_volume_change(self, widget, is_mic, label):
        self.internal_update = True
        val = widget.get_value()
        dev = self.get_active_device(is_mic)
        self.pulse.volume_set_all_chans(dev, widget.get_value())
        label.set_text(f"{int(round(val * 100))}%")

    def on_mute_toggle(self, button, is_mic, update_css):
        self.internal_update = True
        dev = self.get_active_device(is_mic)
        active = button.get_active()
        self.pulse.mute(dev, active)
        update_css(is_mic, active)
        button.set_child(self.get_mute_icon(is_mic, active))

    def on_device_change(self, is_mic, dev_name, callback):
        self.internal_update = True
        target = self.pulse.get_source_by_name(dev_name) if is_mic else self.pulse.get_sink_by_name(dev_name)
        self.pulse.default_set(target) if is_mic == False else self.pulse.source_default_set(target)
        GLib.timeout_add(100, callback, is_mic, dev_name)

def init_layer(config):
    global _v_layer
    if _v_layer is None:
        _v_layer = VolumeLayer(config)
        _v_layer.connect("close-request", lambda w, e: w.hide() or True)

def toggle_layer():
    global _v_layer
    if _v_layer.get_visible():
        _v_layer.hide()
    else:
        _v_layer.header.change_tab("Volume-Tab")
        _v_layer.show()
        _v_layer.present()

def reload_config(config):
    global _v_layer
    if _v_layer:
        _v_layer.load_config(config)

def hide_layer():
    global _v_layer
    _v_layer.hide()