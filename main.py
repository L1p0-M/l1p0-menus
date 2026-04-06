from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')
import argparse
import pulse
import os
import gi
import sys
import socket
import brightness
import clock
import battery
import json

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib
SOCKET_PATH = f"/tmp/l1p0-menus.sock"


def handle_socket_input(source, condition, module ):
    conn, _ = source.accept()
    data = conn.recv(1024).decode().strip()
    if data == "toggle_audio":
        if brightness._v_layer:
            brightness.hide_layer()
        if battery._v_layer:
            battery.hide_layer()
        pulse.toggle_layer()
    elif data == "toggle_brightness":
        if pulse._v_layer:
            pulse.hide_layer()
        if battery._v_layer:
            battery.hide_layer()
        brightness.toggle_layer()
    elif data == "toggle_calendar":
        clock.toggle_layer()
    elif data == "toggle_battery":
        if brightness._v_layer:
            brightness.hide_layer()
        if pulse._v_layer:
            pulse.hide_layer()
        battery.toggle_layer()
    elif data == "reload_css":
        print("Reloading CSS..")
        load_css()
        
    conn.close()
    return True 

def send_command(command):
    if not os.path.exists(SOCKET_PATH):
        print("Error: Start the daemon first!")
        sys.exit(1)
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.sendall(command.encode())
        client.close()
    except Exception as e:
        print(f"Error connecting to the daemon: {e}")
        sys.exit(1)

def run_daemon():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)
    server.setblocking(False) 

    GLib.io_add_watch(server, GLib.IO_IN, handle_socket_input, None)
    
    config = load_config()
    load_css()
    pulse.init_layer()
    brightness.init_layer()
    clock.init_layer(config)
    battery.init_layer()
    print("Daemon runing...")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Stopping...")
        loop.quit()

def load_config():
    try:
        home = get_home_dir()
        config_path = f"{home}/.config/l1p0-menu/config.json"
        if not os.path.exists(config_path):
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
        base_css_path = resource_path('style.css')
        try:
            css_provider.load_from_path(base_css_path)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                800
            )
        except Exception as e:
            print(f"CSS error: {e}")
        try:
            if not os.path.exists(f'{home}/.config/l1p0-menu/style.css'):
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
        print("CSS fájlok betöltve.")

def get_home_dir():
    try:
        home = os.environ.get('HOME')
    except:
        home = os.path.expanduser('~')
    return home

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L1p0 Menus for Hyprland")
    parser.add_argument('--daemon', action='store_true', help='Start the daemon')
    parser.add_argument('--toggle', type=str, help='Toggle menus, Available options: audio,brightness,calendar,battery')
    parser.add_argument('--reload-css', action='store_true', help='Reload user and internal CSS')
    
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    elif args.toggle == 'audio':
        send_command("toggle_audio")
    elif args.toggle == 'brightness':
        send_command("toggle_brightness")
    elif args.toggle == 'calendar':
        send_command("toggle_calendar")
    elif args.toggle == 'battery':
        send_command("toggle_battery")
    elif args.reload_css:
        send_command("reload_css")
    else:
        parser.print_help()