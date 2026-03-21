import gi
import pulsectl
import time

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib
_v_layer = None


class VolumeLayer(Gtk.Window):
    def __init__(self):
        super().__init__(title="Audio Layer")
        self.pulse = pulsectl.Pulse('volume-layer-v2')
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "audio-control")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 10)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 10)
        self.set_default_size(400, 150)
        self.get_style_context().add_class("audio-window")
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_container.set_border_width(20) # Ez a bűvös 10px padding körben
        self.add(main_container)
        self.notebook = Gtk.Notebook()
        main_container.pack_start(self.notebook, True, True, 0)

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
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox.set_border_width(20)
        self.is_mic = is_mic
        hbox_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.current_val = self.get_current_volume(self.is_mic)
        
   
        # Slider
        adj = Gtk.Adjustment(value=0, lower=0, upper=1, step_increment=0.01)
        if not is_mic:           
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
            self.vol_device = Gtk.ComboBoxText()
            self.vol_device_handler = self.vol_device.connect("changed", self.on_device_change, self.is_mic)
            self.combo = self.vol_device



        elif is_mic:
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
            self.mic_device = Gtk.ComboBoxText()
            self.mic_device_handler = self.mic_device.connect("changed", self.on_device_change, self.is_mic)
            self.combo = self.mic_device

            

        self.setup_default_switcher(self.is_mic)
        self.combo.get_style_context().add_class("device-switcher")
        self.scale.get_style_context().add_class("volume-slider")
        self.update_slider_css_class(self.is_mic)
        self.percent_label.set_size_request(40, -1) # Fix szélesség
        self.percent_label.get_style_context().add_class("percent-text")
        self.scale.set_draw_value(False) # Kikapcsoljuk a GTK gyári felette lévő számát
        self.scale.set_size_request(250, -1)
        self.scale.set_hexpand(True) 
        self.combo.set_hexpand(True)       
        self.mute_btn.set_image(mute_icon)
        hbox_top.pack_start(self.percent_label, False, False, 5)
        hbox_top.pack_start(self.scale, True, True, 5)
        hbox_top.pack_end(self.mute_btn, False, False, 5)
        vbox.pack_start(hbox_top, False, False, 0)

        # Eszközválasztó
        hbox_bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        hbox_bottom.set_hexpand(True)
  
        
        
        hbox_bottom.pack_start(self.combo, False, False, 5)

        vbox.pack_start(hbox_bottom, False, False, 0)
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        tab_box.set_halign(Gtk.Align.CENTER)
        tab_box.set_valign(Gtk.Align.CENTER)
    
        icon_name = "audio-input-microphone-symbolic" if is_mic else "audio-speakers-symbolic"
        tab_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        tab_label = Gtk.Label(label=label_text)
    
        tab_box.pack_start(tab_icon, False, False, 0)
        tab_box.pack_start(tab_label, False, False, 0)
        tab_box.show_all() 

        page_num = self.notebook.append_page(vbox, tab_box)
        child = self.notebook.get_nth_page(page_num)
        self.notebook.child_set_property(child, "tab-expand", True)
        self.notebook.child_set_property(child, "tab-fill", True)



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
        else:
            devices = self.pulse.sink_list()
        default_name = self.get_default_device_name(is_mic)
        for i, dev in enumerate(devices):
            self.combo.append(dev.name, dev.description)
            if dev.name == default_name:
                self.combo.set_active(i)

    def check_new_sink_devices(self):
        devices = self.pulse.sink_list()
        default_name = self.get_default_device_name(is_mic=False)
        model = self.vol_device.get_model()
        new_devices= {}
        current_devices = {}
        for i, dev in enumerate(devices):
            new_devices[dev.name] = dev.description
            if dev.name == default_name:
                self.vol_device.set_active(i)
        for row in model:
            current_devices[row[1]] = row[0]
        to_remove = set(current_devices) - set(new_devices)
        to_add = set(new_devices) - set(current_devices)
        if to_add:
            for name in to_add:
                device_description = new_devices[name]
                self.vol_device.append(name, device_description)
        if to_remove:
            for name in to_remove:
                try:
                    for  index, row in enumerate(model):
                        if row[1] == name:
                            index_to_remove = index
                            break
                    self.vol_device.remove(index_to_remove)
                
                except Exception as e:
                    print(e)
                
    def check_new_source_devices(self):
        devices = [d for d in self.pulse.source_list() if 'monitor' not in d.name.lower()]
        default_name = self.get_default_device_name(is_mic=True)
        model = self.mic_device.get_model()
        new_devices= {}
        current_devices = {}
        for i, dev in enumerate(devices):
            new_devices[dev.name] = dev.description
            if dev.name == default_name:
                self.mic_device.set_active(i)
        for row in model:
            current_devices[row[1]] = row[0]
        to_remove = set(current_devices) - set(new_devices)
        to_add = set(new_devices) - set(current_devices)
        if to_add:
            for name in to_add:
                device_description = new_devices[name]
                self.mic_device.append(name, device_description)
        if to_remove:
            for name in to_remove:
                try:
                    for  index, row in enumerate(model):
                        if row[1] == name:
                            index_to_remove = index
                            break
                    self.mic_device.remove(index_to_remove)
                
                except Exception as e:
                    print(e)
      

    def update_ui_elements(self, ev, type="pulse"):
        if ev is not None:
            if "sink" in str(ev.facility):
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
                self.vol_mute_btn.set_image(self.get_mute_icon(is_mic=False))
                self.check_new_sink_devices()
                self.vol_percent_label.set_label(f"{int(new_vol * 100)}%")
                self.vol_scale.handler_unblock(self.vol_scale_handler)
                self.vol_mute_btn.handler_unblock(self.vol_mute_btn_handler)
                self.vol_device.handler_unblock(self.vol_device_handler)

            elif "source" in str(ev.facility):
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
                self.mic_mute_btn.set_image(self.get_mute_icon(is_mic=True))
                self.check_new_source_devices()
                self.mic_percent_label.set_label(f"{int(new_vol * 100)}%")
                self.mic_scale.handler_unblock(self.mic_scale_handler)
                self.mic_mute_btn.handler_unblock(self.mic_mute_btn_handler)
                self.mic_device.handler_unblock(self.mic_device_handler)
        if type == "icon":
            self.vol_mute_btn.set_image(self.get_mute_icon(is_mic=False))
            self.mic_mute_btn.set_image(self.get_mute_icon(is_mic=True))
        elif type == "css-mic":
            self.update_slider_css_class(is_mic=True)
        elif type == "css-vol":
            self.update_slider_css_class(is_mic=False)
        return False


class PulseAudio():
    def __init__(self, callback, pulse):
        self.pulse = pulse
        self.update_ui_elements = callback
        self.pulse.event_mask_set('sink', 'source')
        self.pulse.event_callback_set(self.on_pulse_event)
        self.last_internal_update = 0
        GLib.timeout_add(300, self.check_pulse_events)
    
    def check_pulse_events(self):
        """Ez a függvény 100ms-enként ránéz, jött-e adat a Pulse-tól."""
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

        

    def on_device_change(self, combo, is_mic):
        self.last_internal_update = time.time()
        dev_name = combo.get_active_id()
        if dev_name:
            target = self.pulse.get_source_by_name(dev_name) if is_mic else self.pulse.get_sink_by_name(dev_name)
            self.pulse.default_set(target)


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
                return Gtk.Image.new_from_icon_name("audio-volume-muted-symbolic", Gtk.IconSize.BUTTON)
            else:
                return Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.BUTTON)
        elif is_mic == False:
            if self.get_mute_status(is_mic):
                return Gtk.Image.new_from_icon_name("audio-volume-muted-symbolic", Gtk.IconSize.BUTTON)
            else:
                return Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.BUTTON)

def init_layer():
    global _v_layer
    if _v_layer is None:
        _v_layer = VolumeLayer()
        # Ne lépjen ki a Gtk, ha bezárják az ablakot, csak rejtse el
        _v_layer.connect("delete-event", lambda w, e: w.hide() or True)

def toggle_layer():
    """Váltás látható és rejtett állapot között."""
    global _v_layer
    if _v_layer.get_visible():
        _v_layer.hide()
    else:
        _v_layer.show_all()
        _v_layer.present()

def hide_layer():
    """Csak elrejtés."""
    global _v_layer
    _v_layer.hide()
