import argparse
import pulse
import os
import gi
import sys
import socket
import brightness
#import clock

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib
SOCKET_PATH = f"/tmp/audio-brightness.sock"


def handle_socket_input(source, condition, module ):
    conn, _ = source.accept()
    data = conn.recv(1024).decode().strip()
    if data == "toggle_audio":
        if brightness._v_layer:
            brightness.hide_layer()
        pulse.toggle_layer()
        print("audio")
    elif data == "toggle_brightness":
        if pulse._v_layer:
            pulse.hide_layer()
        brightness.toggle_layer()
        print("brightness")
    elif data == "toggle_calendar":
        #clock.toggle_layer()
        print("calndar")
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
    
    load_css()
    pulse.init_layer()
    brightness.init_layer()
    #clock.init_layer()
    print("Daemon fut és figyel...")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Leállítás...")
        loop.quit()


def load_css():
        css_provider = Gtk.CssProvider()
        user_css_provider = Gtk.CssProvider()
        home = get_home_dir()
        try:
            css_provider.load_from_path('style.css')
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                800
            )
        except Exception as e:
            print(f"CSS hiba: {e}")
        try:
            if not os.path.exists(f'{home}/.config/audio-menu/style.css'):
                print(f"Felhasználói CSS fájl nem található: {home}/.config/audio-menu/style.css")
            else:
                user_css_provider.load_from_path(f'{home}/.config/audio-menu/style.css')
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(),
                    user_css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_USER
                )
        except Exception as e:
            print(f"Felhasználói CSS hiba: {e}")
        print("CSS fájlok betöltve.")

def get_home_dir():
    try:
        home = os.environ.get('HOME')
    except:
        home = os.path.expanduser('~')
    print(f"Felhasználói könyvtár: {home}")
    return home

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="App vezérlő script")
    parser.add_argument('--daemon', action='store_true', help='Indítás daemon módban')
    parser.add_argument('--toggle', type=str, help='Váltás: audio vagy brightness')
    parser.add_argument('--reload-css', action='store_true', help='CSS újratöltése')
    
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    elif args.toggle == 'audio':
        send_command("toggle_audio")
    elif args.toggle == 'brightness':
        send_command("toggle_brightness")
    elif args.toggle == 'calendar':
        send_command("toggle_calendar")
    elif args.reload_css:
        send_command("reload_css")
    else:
        parser.print_help()