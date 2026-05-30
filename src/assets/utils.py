import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib, Gio


class Header:
    def __init__(self, main_container, buttons, tabs):
        self.main_header_container = main_container
        self.tab_buttons = buttons
        self.tabs = tabs

    def setup_header(self, name, icon_name, tab_name):
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        container.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label(label=name)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        button = Gtk.Button()
        button.get_style_context().add_class("header-button")
        container.append(icon)
        container.append(label)
        button.set_child(container)
        self.main_header_container.append(button)
        self.tab_buttons[tab_name] = button
        button.connect("clicked", lambda x, name=tab_name: self.change_tab(name))
    
    def change_tab(self, tab_name):
        for name, button in self.tab_buttons.items():
            if name == tab_name:
                button.get_style_context().add_class("active")
            else:
                button.get_style_context().remove_class("active")
        self.tabs.set_visible_child_name(tab_name)

class window_utils:
    def __init__(self):
        pass

    def setup_scrolled_windows(self, max_height:int, min_height:int, header_function=None, sort_function=None):
        panel = Gtk.ScrolledWindow()
        panel.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        panel.set_propagate_natural_height(True)
        panel.set_max_content_height(max_height)
        panel.set_min_content_height(min_height)
        panel.add_css_class("scrolled-menu")
        panel.set_size_request(-1, -1)
        panel_content = Gtk.ListBox()
        panel_content.set_selection_mode(Gtk.SelectionMode.NONE)
        if header_function:
            panel_content.set_header_func(header_function)
        if sort_function:
            panel_content.set_sort_func(sort_function)
        panel.set_child(panel_content)
        return panel, panel_content
    
    def get_battery_icon(self, status=2, level=None):
        icons = {}
        status = int(status)
        if status == 2 or status == 1 or status == 6:
            for i in range(10, 101, 10):
                if status == 2 or status == 6:
                    icons[i] = f"battery-level-{i}-symbolic"
                else:
                    icons[i] = f"battery-level-{i}-charging-symbolic"
            step = int(round(level / 10)) * 10
            if step == 100 and status == 1:
                return "battery-level-100-charged-symbolic"
            else:
                return icons[step]
        elif status == 4:
            return "battery-full-symbolic"
        elif status == 5:
            return "battery-level-0-symbolic"
        else:
            return "battery-missing-symbolic"

    def setup_revealer(self, overlay, popupwindow,**kwargs):
        windows = {}
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        revealer.set_valign(Gtk.Align.END)
        windows["revealer"] = revealer
        overlay_window = popupwindow(**kwargs, windows=windows)
        windows["overlay"] = overlay_window
        windows["revealer"].set_child(overlay_window.panel)
        overlay.add_overlay(revealer)
        return windows
    

    def init_empty_text(self, default_text, disabled_icon_name):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        label_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_size_request(-1, 340)

        top_spacer = Gtk.Box()
        top_spacer.set_vexpand(True)
        bottom_spacer = Gtk.Box()
        bottom_spacer.set_vexpand(True)

        text = Gtk.Label(label=default_text)
        disabled_icon = Gtk.Image.new_from_icon_name(disabled_icon_name)
        disabled_icon.set_pixel_size(48)
        loader = Gtk.Image.new_from_icon_name("process-working-symbolic")
        loader.get_style_context().add_class("spinner")
        loader.set_pixel_size(48)
        loader.set_visible(False)

        box.append(top_spacer)
        box.append(disabled_icon)
        box.append(loader)
        #label_container.append(loader)
        label_container.append(text)
        box.append(label_container)
        box.append(bottom_spacer)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        box.set_hexpand(True)
        box.set_vexpand(True)
        label_container.set_halign(Gtk.Align.CENTER)
        label_container.set_valign(Gtk.Align.CENTER)
        return {
            "box": box,
            "text": text,
            "icon": disabled_icon,
            "loader": loader,
        }
    
    def create_header(self, text):
        header = Gtk.Label(label=text)
        header.get_style_context().add_class("header-label")
        header.set_halign(Gtk.Align.START)
        header.set_margin_top(10)
        header.set_margin_bottom(5)
        return header
    
class Popups:
    def __init__(self):
        pass

    def setup_details(self, match_names, match_icons, details, container):
        return_details = {}
        details_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        value_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for key, value in match_names.items():
            icon_name_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            icon = Gtk.Image.new_from_icon_name(f"{match_icons[key]}")
            icon.set_margin_end(10)
            propertys = Gtk.Label(label=key)
            propertys.get_style_context().add_class("popup-parameter")
            if isinstance(value, str):
                property_value = Gtk.Label(label=f"{details[value]}")
                property_value.get_style_context().add_class("popup-value")
            if isinstance(value, Gtk.Switch):
                property_value = value
                property_value.get_style_context().add_class("popup-switch")
                property_value.set_margin_top(0)
            property_value.set_halign(Gtk.Align.END)
            propertys.set_halign(Gtk.Align.START)
            icon_name_container.append(icon)
            icon_name_container.append(propertys)
            details_container.append(icon_name_container)
            value_container.append(property_value)
            return_details[value] = property_value
        container.append(details_container)
        container.append(value_container)
        return return_details
    
class GtkLayerShellUtils:
    def __init__(self, window, window_name):
        self.window = window
        Gtk4LayerShell.init_for_window(self.window)
        Gtk4LayerShell.set_namespace(self.window, f"{window_name}-layer")

    def setup_layer_shell(self, anchor, margin):
        Gtk4LayerShell.set_layer(self.window, Gtk4LayerShell.Layer.TOP)
        self._match_anchor(anchor)
        
        get_margins = lambda lst, idx, default=0: lst[idx] if len(lst) > idx else default
        Gtk4LayerShell.set_margin(self.window, Gtk4LayerShell.Edge.TOP, get_margins(margin, 0))
        Gtk4LayerShell.set_margin(self.window, Gtk4LayerShell.Edge.RIGHT, get_margins(margin, 1))
        Gtk4LayerShell.set_margin(self.window, Gtk4LayerShell.Edge.BOTTOM, get_margins(margin, 2))
        Gtk4LayerShell.set_margin(self.window, Gtk4LayerShell.Edge.LEFT, get_margins(margin, 3))

    def _match_anchor(self, anchor):
        anchor_mapping = {
            "top": Gtk4LayerShell.Edge.TOP,
            "bottom": Gtk4LayerShell.Edge.BOTTOM,
            "left": Gtk4LayerShell.Edge.LEFT,
            "right": Gtk4LayerShell.Edge.RIGHT
        }
        for anchor_name, anchor_value in anchor_mapping.items():
            is_active = anchor_name in anchor.lower()
            Gtk4LayerShell.set_anchor(self.window, anchor_value, is_active)

    def process_config(self, config, default_anchor="top-right", default_margin=[10, 10]):
        if config and isinstance(config, dict):
            anchor = config.get("anchor", default_anchor)
            if isinstance(config.get("margin", default_margin), str):
                margin = [int(x) for x in config.get("margin", default_margin).split(",")]
            else:
                margin = default_margin
            print(f"Config anchor: {anchor}, margin: {margin}")
        else:
            anchor = default_anchor
            margin = default_margin
        return anchor, margin
