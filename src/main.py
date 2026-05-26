from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')
from argparse import ArgumentParser
import popups.pulse as pulse
from os import path, environ, remove
import gi
from sys import exit
import socket
import popups.brightness as brightness
import popups.clock as clock
import popups.battery as battery
import popups.wifi as wifi
import json

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib, Gio
SOCKET_PATH = f"/tmp/l1p0-menus.sock"


def handle_socket_input(source, condition, module ):
    try:
        conn, _ = source.accept()
        data = conn.recv(1024).decode().strip()
        process_command(data)
        conn.close()
    except Exception as e:
        print(f"Socket error: {e}")
    return True

def process_command(data):
    commands = {
        "toggle_audio": (pulse, ["brightness", "battery", "wifi"]),
        "toggle_brightness": (brightness, ["pulse", "battery", "wifi"]),
        "toggle_battery": (battery, ["brightness", "pulse", "wifi"]),
        "toggle_calendar": (clock, []),
        "toggle_network": (wifi, ["brightness", "battery", "pulse"])
    }

    if data in commands:
        module, targets_to_hide = commands[data]
        
        for target_name in targets_to_hide:
            target_mod = globals().get(target_name)
            if target_mod and getattr(target_mod, "_v_layer", None):
                target_mod.hide_layer()
    
        module.toggle_layer()

    elif data == "reload_css":
        print("Reloading CSS..")
        load_css()
        
    return False 

def send_command(command):
    if not path.exists(SOCKET_PATH):
        print("Error: Start the daemon first!")
        exit(1)
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.sendall(command.encode())
        client.close()
    except Exception as e:
        print(f"Error connecting to the daemon: {e}")
        exit(1)

def run_daemon():
    if path.exists(SOCKET_PATH):
        remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)
    server.setblocking(False) 

    GLib.io_add_watch(server, GLib.IO_IN, handle_socket_input, None)
    
    load_resources()
    config = load_config()
    load_css()
    pulse.init_layer()
    brightness.init_layer()
    clock.init_layer(config)
    battery.init_layer()
    wifi.init_layer()
    print("Daemon runing...")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Stopping...")
        loop.quit()
    finally:
        print("Cleaning up...")
        wifi.cleanup()
        server.close()

def load_config():
    try:
        home = get_home_dir()
        config_path = f"{home}/.config/l1p0-menu/config.json"
        if not path.exists(config_path):
            print(f"User config file not found at: {config_path}")
        else:
            with open(f"{config_path}") as f:
                config = json.load(f)
                if "api_key" in config:    
                    return config
                else:
                    return None
    except Exception as e:
        print(e)

def load_css():
        css_provider = Gtk.CssProvider()
        user_css_provider = Gtk.CssProvider()
        home = get_home_dir()
        try:
            css_provider.load_from_resource("/l1p0-menus/assets/style.css")
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                800
            )
        except Exception as e:
            print(f"CSS error: {e}")
        try:
            if not path.exists(f'{home}/.config/l1p0-menu/style.css'):
                print(f"User css file not found at: {home}/.config/l1p0-menu/style.css")
            else:
                user_css_provider.load_from_path(f'{home}/.config/l1p0-menu/style.css')
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(),
                    user_css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_USER
                )
        except Exception as e:
            print(f"User css error: {e}")
        print("CSS files loaded.")

def get_home_dir():
    try:
        home = environ.get('HOME')
    except:
        home = path.expanduser('~')
    return home

def load_resources():
    try:
        base_dir = path.dirname(path.abspath(__file__))
        resource_path = path.join(base_dir, "resources.gresource")
        resource = Gio.Resource.load(resource_path)
        resource._register()
    except Exception as e:
        print(f"Failed to load resources: {e}")

def main():
    parser = ArgumentParser(description="L1p0 Menus for Hyprland")
    parser.add_argument('--daemon', action='store_true', help='Start the daemon')
    parser.add_argument('--toggle', type=str, help='Toggle menus, Available options: audio,brightness,calendar,battery,network')
    parser.add_argument('--reload-css', action='store_true', help='Reload user and internal CSS')
    
    args = parser.parse_args()
    available_widgets = ["audio", "brightness", "calendar", "battery", "network"]

    if args.daemon:
        run_daemon()
    elif args.toggle in available_widgets:
        toggle = args.toggle
        send_command(f"toggle_{toggle}")
    elif args.reload_css:
        send_command("reload_css")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()