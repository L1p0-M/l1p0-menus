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