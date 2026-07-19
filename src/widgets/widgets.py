import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib



@Gtk.Template(resource_path="/l1p0-menus/ui/popup_menu_btn.ui")
class MenuButton(Gtk.Button):
    __gtype_name__ = 'MenuButton'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

@Gtk.Template(resource_path="/l1p0-menus/ui/mute_btn.ui")
class MuteButton(Gtk.ToggleButton):
    __gtype_name__ = 'MuteButton'

    button_image = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()
        self.image = self.get_template_child(MuteButton, "button_image")

@Gtk.Template(resource_path="/l1p0-menus/ui/header_buttons.ui")
class HeaderButton(Gtk.Button):
    __gtype_name__ = 'HeaderButton'

    header_button_image = Gtk.Template.Child()
    header_button_name = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()
        self.image = self.get_template_child(HeaderButton, "header_button_image")
        self.name = self.get_template_child(HeaderButton, "header_button_name")

@Gtk.Template(resource_path="/l1p0-menus/ui/revealer.ui")
class PopupRevealer(Gtk.Revealer):
    __gtype_name__ = 'PopupRevealer'

    panel = Gtk.Template.Child()
    panel_content = Gtk.Template.Child()
    header_label = Gtk.Template.Child()
    close_btn = Gtk.Template.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

    @Gtk.Template.Callback()
    def close_revealer(self, button):
        self.set_reveal_child(False)

@Gtk.Template(resource_path="/l1p0-menus/ui/scrolled_panel.ui")
class ScrolledPanel(Gtk.ScrolledWindow):
    __gtype_name__ = 'ScrolledPanel'
    panel_content = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

@Gtk.Template(resource_path="/l1p0-menus/ui/details_popup.ui")
class DetailsPopupRow(Gtk.Box):
    __gtype_name__ = 'DetailsPopupRow'
    icon = Gtk.Template.Child()
    property_name = Gtk.Template.Child()
    property_value = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()