import gi
import pulsectl
import time

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib
_v_layer = None


class VolumeLayer(Gtk.Window):
    def __init__(self):
        super().__init__(title="Audio Layer")
        self.pulse = pulsectl.Pulse('volume-layer-v2')
        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_namespace(self, "audio-control")
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.TOP)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.RIGHT, True)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.RIGHT, 10)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.TOP, 10)
        self.set_default_size(400, 150)
        self.get_style_context().add_class("audio-window")
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_container.get_style_context().add_class("audio-layer")
        main_container.set_margin_start(0) # Ez a bűvös 10px padding körben
        self.set_child(main_container)
        self.notebook = Gtk.Notebook()
        main_container.append(self.notebook)

        self.pulseaudio = PulseAudio(self.update_ui_elements, self.pulse)
        self.on_volume_change = self.pulseaudio.on_volume_change
        self.on_device_change = self.pulseaudio.on_device_change
        self.on_mute_toggle = self.pulseaudio.on_mute_toggle
        self.get_active_device = self.pulseaudio.get_active_device
        self.get_current_volume = self.pulseaudio.get_current_volume
        self.get_default_device_name = self.pulseaudio.get_default_device_name
        self.get_mute_status = self.pulseaudio.get_mute_status
        self.get_mute_icon = self.pulseaudio.get_mute_icon

        self.setup_audio_tab("Hang", is_mic=False)
        self.setup_audio_tab("Mikrofon", is_mic=True)

   

    def setup_audio_tab(self, label_text, is_mic):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
            spacing=15,
            margin_start=20,
            margin_end=20,
            margin_top=20,
            margin_bottom=20,)
        self.is_mic = is_mic
        hbox_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.current_val = self.get_current_volume(self.is_mic)
        
        adj = Gtk.Adjustment(value=0, lower=0, upper=1, step_increment=0.01)
        if not is_mic:
            self.sink_list = Gtk.StringList.new([])           
            self.vol_percent_label = Gtk.Label(label=f"{int(self.current_val * 100)}%")
            self.percent_label= self.vol_percent_label
            self.vol_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            self.vol_scale.set_value(self.get_current_volume(self.is_mic))
            self.vol_scale_handler = self.vol_scale.connect("value-changed", self.on_volume_change, self.is_mic, self.percent_label)
            self.scale = self.vol_scale
            self.vol_mute_icon = self.get_mute_icon(is_mic=False)
            mute_icon = self.vol_mute_icon
            self.vol_mute_btn = Gtk.ToggleButton()
            self.vol_mute_btn.set_active(self.get_mute_status(self.is_mic))
            self.vol_mute_btn_handler = self.vol_mute_btn.connect("toggled", self.on_mute_toggle, self.is_mic)
            self.mute_btn = self.vol_mute_btn
            self.vol_device = Gtk.DropDown(model=self.sink_list)
            self.setup_default_switcher(self.is_mic)
            self.vol_device_handler = self.vol_device.connect("notify::selected", self.on_device_change, self.is_mic, self.sink_device_names)
            self.combo = self.vol_device

        elif is_mic:
            self.mic_list = Gtk.StringList.new([])
            self.mic_percent_label = Gtk.Label(label=f"{int(self.current_val * 100)}%")
            self.percent_label = self.mic_percent_label
            self.mic_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            self.mic_scale.set_value(self.get_current_volume(self.is_mic))
            self.mic_scale_handler = self.mic_scale.connect("value-changed", self.on_volume_change, self.is_mic, self.percent_label)
            self.scale = self.mic_scale
            self.mic_mute_icon = self.get_mute_icon(self.is_mic)
            mute_icon = self.mic_mute_icon
            self.mic_mute_btn = Gtk.ToggleButton()
            self.mic_mute_btn.set_active(self.get_mute_status(self.is_mic))
            self.mic_mute_btn_handler = self.mic_mute_btn.connect("toggled", self.on_mute_toggle, self.is_mic)
            self.mute_btn = self.mic_mute_btn
            self.mic_device = Gtk.DropDown(model=self.mic_list)
            self.setup_default_switcher(self.is_mic)
            self.mic_device_handler = self.mic_device.connect("notify::selected", self.on_device_change, self.is_mic, self.mic_device_names)
            self.combo = self.mic_device

        self.combo.get_style_context().add_class("device-switcher")
        self.scale.get_style_context().add_class("volume-slider")
        self.update_slider_css_class(self.is_mic)
        self.percent_label.set_size_request(40, -1) # Fix szélesség
        self.percent_label.get_style_context().add_class("percent-text")
        self.scale.set_draw_value(False) # Kikapcsoljuk a GTK gyári felette lévő számát
        self.scale.set_size_request(250, -1)
        self.scale.set_hexpand(True) 
        self.combo.set_hexpand(True)       
        self.mute_btn.set_child(mute_icon)
        hbox_top.append(self.percent_label)
        hbox_top.append(self.scale)
        hbox_top.append(self.mute_btn)
        vbox.append(hbox_top)

        hbox_bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        hbox_bottom.set_hexpand(True)
        hbox_bottom.append(self.combo)
        vbox.append(hbox_bottom)
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        tab_box.set_halign(Gtk.Align.CENTER)
        tab_box.set_valign(Gtk.Align.CENTER)
    
        icon_name = "microphone-sensitivity-high-symbolic" if is_mic else "audio-speakers-symbolic"
        tab_icon = Gtk.Image.new_from_icon_name(icon_name)
        tab_icon.set_icon_size(Gtk.IconSize.NORMAL)
        tab_label = Gtk.Label(label=label_text)
    
        tab_box.append(tab_icon)
        tab_box.append(tab_label)

        page_num = self.notebook.append_page(vbox, tab_box)
        child = self.notebook.get_page(vbox)
        child.set_property("tab_expand", True)
        child.set_property("tab-fill", True)



    def update_slider_css_class(self, is_mic):
        if is_mic:
            mute_status = self.get_mute_status(is_mic=True)
            if mute_status:
                self.mic_scale.get_style_context().add_class("muted")
            else:
                self.mic_scale.get_style_context().remove_class("muted")
        elif is_mic == False:
            mute_status = self.get_mute_status(is_mic=False)
            if mute_status:
                self.vol_scale.get_style_context().add_class("muted")
            else:
                self.vol_scale.get_style_context().remove_class("muted")
        
    def setup_default_switcher(self, is_mic):
        if is_mic:
            devices = [d for d in self.pulse.source_list() if 'monitor' not in d.name.lower()]
            self.mic_device_names = [d.name for d in devices]
            device_names = self.mic_device_names
            target_list = self.mic_list
            target_device = self.mic_device
        else:
            devices = self.pulse.sink_list()
            self.sink_device_names = [d.name for d in devices]
            device_names = self.sink_device_names
            target_list = self.sink_list
            target_device = self.vol_device

        default_name = self.get_default_device_name(is_mic)
        dropdown_items = [d.description for d in devices]
        target_list.splice(0, target_list.get_n_items(), dropdown_items)
        if default_name in device_names:
            idx = device_names.index(default_name)
            target_device.set_selected(idx)

    def update_default_switcher(self, is_mic):
        if is_mic:
            devices = [d for d in self.pulse.source_list() if 'monitor' not in d.name.lower()]
            current_stored_names = self.mic_device_names
            target_list_model = self.mic_list
            target_device = self.mic_device
        else:
            devices = self.pulse.sink_list()
            current_stored_names = self.sink_device_names
            target_list_model = self.sink_list
            target_device = self.vol_device
        new_default_name = self.get_default_device_name(is_mic)
        new_descriptions = [d.description for d in devices]
        new_names = [d.name for d in devices]
        if new_names != current_stored_names:
            if is_mic:
                self.mic_device_names = new_names
            else:
                self.sink_device_names = new_names
            current_stored_names = new_names
            target_list_model.splice(0, target_list_model.get_n_items(), new_descriptions)
        if new_default_name in current_stored_names:
            idx = current_stored_names.index(new_default_name)
            if target_device.get_selected() != idx:
                target_device.set_selected(idx)
      

    def update_ui_elements(self, ev, type="pulse"):
        if ev is not None:
            if "sink" in str(ev.facility) or "server" in str(ev.facility):
                self.vol_scale.handler_block(self.vol_scale_handler)
                self.vol_mute_btn.handler_block(self.vol_mute_btn_handler)
                self.vol_device.handler_block(self.vol_device_handler)
                new_vol = self.get_current_volume(is_mic=False)
                self.vol_scale.set_value(new_vol)
                mute_status = self.get_mute_status(is_mic=False)
                if mute_status:
                    self.vol_scale.get_style_context().add_class("muted")
                else:
                    self.vol_scale.get_style_context().remove_class("muted")
                self.vol_mute_btn.set_active(mute_status)
                self.vol_mute_btn.set_child(self.get_mute_icon(is_mic=False))
                self.update_default_switcher(is_mic=False)
                self.vol_percent_label.set_label(f"{int(new_vol * 100)}%")
                self.vol_scale.handler_unblock(self.vol_scale_handler)
                self.vol_mute_btn.handler_unblock(self.vol_mute_btn_handler)
                self.vol_device.handler_unblock(self.vol_device_handler)

            if "source" in str(ev.facility) or "server" in str(ev.facility):
                self.mic_scale.handler_block(self.mic_scale_handler)
                self.mic_mute_btn.handler_block(self.mic_mute_btn_handler)
                self.mic_device.handler_block(self.mic_device_handler)
                new_vol = self.get_current_volume(is_mic=True)
                self.mic_scale.set_value(new_vol)
                mute_status = self.get_mute_status(is_mic=True)
                if mute_status:
                    self.mic_scale.get_style_context().add_class("muted")
                else:
                    self.mic_scale.get_style_context().remove_class("muted")
                self.mic_mute_btn.set_active(mute_status)
                self.mic_mute_btn.set_child(self.get_mute_icon(is_mic=True))
                self.update_default_switcher(is_mic=True)
                self.mic_percent_label.set_label(f"{int(new_vol * 100)}%")
                self.mic_scale.handler_unblock(self.mic_scale_handler)
                self.mic_mute_btn.handler_unblock(self.mic_mute_btn_handler)
                self.mic_device.handler_unblock(self.mic_device_handler)
        if type == "icon":
            self.vol_mute_btn.set_child(self.get_mute_icon(is_mic=False))
            self.mic_mute_btn.set_child(self.get_mute_icon(is_mic=True))
        elif type == "css-mic":
            self.update_slider_css_class(is_mic=True)
        elif type == "css-vol":
            self.update_slider_css_class(is_mic=False)
        return False


class PulseAudio():
    def __init__(self, callback, pulse):
        self.pulse = pulse
        self.update_ui_elements = callback
        self.pulse.event_mask_set('sink', 'source', 'server')
        self.pulse.event_callback_set(self.on_pulse_event)
        self._pulse_loop_id = None
        self.last_internal_update = 0
    
    def start_update_loop(self):
        global _v_layer
        if self._pulse_loop_id is not None:
            GLib.source_remove(self._pulse_loop_id)
            self._pulse_loop_id = None
        self.was_visible = _v_layer.get_visible()
        if self.was_visible:
            self._pulse_loop_id = GLib.timeout_add(100, self.check_pulse_events)
        else:
            self._pulse_loop_id = GLib.timeout_add_seconds(5, self.check_pulse_events)

    def check_pulse_events(self):
        try:
            self.pulse.event_listen(timeout=0.001) 
        except Exception:
            pass
        return True
    
    def on_pulse_event(self, ev):
        if (time.time() - self.last_internal_update) < 0.2:
            return
        if hasattr(self, '_update_pending') and self._update_pending:
            return
        self._update_pending = True
        try:
            GLib.idle_add(self.update_ui_elements, ev)
        except Exception as e:
            print(f"Update hiba: {e}")
        finally:
            self._update_pending = False

    def on_volume_change(self, widget, is_mic, label):
        self.last_internal_update = time.time()
        val = widget.get_value()
        dev = self.get_active_device(is_mic)
        self.pulse.volume_set_all_chans(dev, widget.get_value())
        label.set_text(f"{int(val * 100)}%")

    def on_mute_toggle(self, button, is_mic):
        self.last_internal_update = time.time()
        dev = self.get_active_device(is_mic)
        self.pulse.mute(dev, button.get_active())
        self.update_ui_elements(None, type="icon")
        if is_mic:
            self.update_ui_elements(None, type="css-mic")
        elif is_mic == False:
            self.update_ui_elements(None, type="css-vol")

        

    def on_device_change(self, dropdown, pspec, is_mic, device_names):
        #self.last_internal_update = time.time()
        index = dropdown.get_selected()
        dev_name = device_names[index]
        if dev_name:
            target = self.pulse.get_source_by_name(dev_name) if is_mic else self.pulse.get_sink_by_name(dev_name)
            self.pulse.default_set(target) if is_mic == False else self.pulse.source_default_set(target)


    def get_active_device(self, is_mic):
        info = self.pulse.server_info()
        name = info.default_source_name if is_mic else info.default_sink_name
        return self.pulse.get_source_by_name(name) if is_mic else self.pulse.get_sink_by_name(name)

    def get_current_volume(self, is_mic):
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
    
    def get_mute_icon(self, is_mic):
        if is_mic:
            if self.get_mute_status(is_mic):
                return Gtk.Image.new_from_icon_name("audio-volume-muted-symbolic")
            else:
                return Gtk.Image.new_from_icon_name("audio-volume-high-symbolic")
        elif is_mic == False:
            if self.get_mute_status(is_mic):
                return Gtk.Image.new_from_icon_name("audio-volume-muted-symbolic")
            else:
                return Gtk.Image.new_from_icon_name("audio-volume-high-symbolic")

def init_layer():
    global _v_layer
    if _v_layer is None:
        _v_layer = VolumeLayer()
        _v_layer.pulseaudio.start_update_loop()
        _v_layer.connect("close-request", lambda w, e: w.hide() or True)

def toggle_layer():
    global _v_layer
    if _v_layer.get_visible():
        _v_layer.hide()
    else:
        _v_layer.show()
        _v_layer.present()
    _v_layer.pulseaudio.start_update_loop()

def hide_layer():
    global _v_layer
    _v_layer.hide()
