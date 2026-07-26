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
        

@Gtk.Template(resource_path="/l1p0-menus/ui/scrolled_panel.ui")
class ScrolledPanel(Gtk.ScrolledWindow):
    __gtype_name__ = 'ScrolledPanel'
    panel_content = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

    def set_propertys(self, max_height:int, min_height:int, header_function=None, sort_function=None):
        self.set_max_content_height(max_height)
        self.set_min_content_height(min_height)
        if header_function:
            self.panel_content.set_header_func(header_function)
        if sort_function:
            self.panel_content.set_sort_func(sort_function)

@Gtk.Template(resource_path="/l1p0-menus/ui/details_popup.ui")
class DetailsPopupRow(Gtk.Box):
    __gtype_name__ = 'DetailsPopupRow'
    icon = Gtk.Template.Child()
    property_name = Gtk.Template.Child()
    property_value = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

@Gtk.Template(resource_path="/l1p0-menus/ui/popup_header.ui")
class PopupHeader(Gtk.Box):
    __gtype_name__ = 'PopupHeader'
    header_text = Gtk.Template.Child()
    close_btn = Gtk.Template.Child()

    def __init__(self, close_funktion=None, **kwargs):
        super().__init__(**kwargs)
        self.init_template()
        self.close_funktion = close_funktion

    @Gtk.Template.Callback()
    def on_close(self, *args):
        if self.close_funktion and callable(self.close_funktion):
            self.close_funktion()