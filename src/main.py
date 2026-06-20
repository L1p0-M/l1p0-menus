from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')
from argparse import ArgumentParser
from os import path, environ, remove
import gi
from sys import exit
from .popups import brightness as brightness
from .popups import clock as clock
from .popups import battery as battery
from .popups import wifi as network
from .popups import pulse as pulse
from .assets.utils import IPCSocket
import json

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gtk4LayerShell, GLib, Gio

runtime_dir = environ.get('XDG_RUNTIME_DIR', '/tmp')
SOCKET_PATH = path.join(runtime_dir, "l1p0-menus.sock")
SENDER_IPC = IPCSocket("daemon_cli_sender", None)
CONFIG = None
ACTIVE_CONNECTIONS = {}
MATCH_CONFIG = {
        pulse: "audio",
        brightness: "brightness",
        clock: "weather-clock",
        battery: "battery",
        network: "network"
    }

def handle_incoming_connection(service, connection, source_object):
    input_stream = connection.get_input_stream()
    data_input = Gio.DataInputStream.new(input_stream)
    listen_to_client(data_input, connection)
    return True

def listen_to_client(data_input, connection):
    data_input.read_line_async(
        GLib.PRIORITY_DEFAULT,
        None,
        on_client_data_received,
        (data_input, connection)
    )

def on_client_data_received(stream, result, user_data):
    data_input, connection = user_data
    try:
        line, length = stream.read_line_finish_utf8(result)
        if not line:
            remove_connection(connection)
            return
        try:
            payload = json.loads(line.strip())
            process_routing_command(payload, connection)
        except json.JSONDecodeError:
            process_command(line.strip())

        listen_to_client(data_input, connection)

    except Exception as e:
        print(f"Error while receiving data: {e}")
        remove_connection(connection)


def remove_connection(connection):
    global ACTIVE_CONNECTIONS
    to_remove = [k for k, v in ACTIVE_CONNECTIONS.items() if v == connection]
    for key in to_remove:
        del ACTIVE_CONNECTIONS[key]
        print(f"Client disconnected: {key}")


def process_routing_command(payload, connection):
    global ACTIVE_CONNECTIONS
    
    sender = payload.get("sender")
    target = payload.get("target")
    data = payload.get("data")

    if sender and ACTIVE_CONNECTIONS.get(sender) != connection:
        ACTIVE_CONNECTIONS[sender] = connection
        print(f"Client connected to the socket: {sender}")

    if target == "daemon":
        process_command(data)
        return

    if target in ACTIVE_CONNECTIONS:
        target_connection = ACTIVE_CONNECTIONS[target]
        output_stream = target_connection.get_output_stream()
        
        msg = json.dumps(payload) + "\n"
        output_stream.write_all_async(
            msg.encode('utf-8'),
            GLib.PRIORITY_DEFAULT,
            None,
            None,
            None
        )
    else:
        print(f"Error: The ({target}) client is not available!")

def process_command(data):
    commands = {
        "toggle_audio": pulse,
        "toggle_brightness": brightness,
        "toggle_battery": battery,
        "toggle_calendar": clock,
        "toggle_network": network
    }

    default_anchor = {
        pulse: "top-right",
        brightness: "top-right",
        clock: "top-center",
        battery: "top-right",
        network: "top-right"
    }

    if data in commands:
        module = commands[data]
        config = CONFIG if CONFIG is not None else {}
        module_anchor = config.get(MATCH_CONFIG[module], {}).get("anchor", default_anchor[module])
        for popup, config_name in MATCH_CONFIG.items():
            if popup != module and config.get(config_name, {}).get("anchor", default_anchor[popup]) == module_anchor:
                if popup.get_visibility():
                    popup.hide_layer()
    
        module.toggle_layer()

    elif data == "reload_css":
        print("Reloading CSS..")
        load_css()
    elif data == "reload_config":
        print("Reloading config..")
        reload_config()
        
    return False 

def send_command(command):
    if not path.exists(SOCKET_PATH):
        print("Error: Start the daemon first!")
        exit(1)
    try:
        SENDER_IPC.send_to("daemon", command)
    except Exception as e:
        print(f"Error sending command to the daemon: {e}")
        exit(1)

def run_daemon():
    if path.exists(SOCKET_PATH):
        try:
            remove(SOCKET_PATH)
        except Exception as e:
            exit(1)
    server = Gio.SocketService.new()
    server.connect("incoming", handle_incoming_connection)
    try:
        address = Gio.UnixSocketAddress.new(SOCKET_PATH)
        Gio.SocketListener.add_address(server, address, Gio.SocketType.STREAM, Gio.SocketProtocol.DEFAULT, None)
        server.start()
        print("Daemon running...")
    except Exception as e:
        print(f"Failed to start the daemon: {e}")
        exit(1)
    
    load_resources()
    global CONFIG
    CONFIG = get_config()
    load_css()
    popups = [pulse, brightness, battery, clock, network]
    for popup in popups:
        popup.init_layer(config=None)
    reload_config(CONFIG)
    print("Popups initialized...")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Stopping...")
        loop.quit()
    finally:
        print("Cleaning up...")
        network.cleanup()
        server.close()
        for connection in ACTIVE_CONNECTIONS.values():
            connection.close()

def get_config():
    try:
        home = get_home_dir()
        config_path = f"{home}/.config/l1p0-menu/config.json"
        if not path.exists(config_path):
            print(f"User config file not found at: {config_path}")
        else:
            with open(f"{config_path}") as f:
                config = json.load(f)  
                return config
    except Exception as e:
        print(e)
        return {}

def reload_config(config=None):
    if config is None:
        config = get_config()
    if not config:
        print("No config to reload")
        return
    print("Loading config...")
    global CONFIG
    CONFIG = config
    for popup, config_name in MATCH_CONFIG.items():
        popup.reload_config(config.get(config_name, None))

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
    parser.add_argument('--reload-config', action='store_true', help='Reload config and apply to layers')
    
    args = parser.parse_args()
    available_widgets = ["audio", "brightness", "calendar", "battery", "network"]

    if args.daemon:
        run_daemon()
    elif args.toggle in available_widgets:
        toggle = args.toggle
        send_command(f"toggle_{toggle}")
    elif args.reload_css:
        send_command("reload_css")
    elif args.reload_config:
        send_command("reload_config")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()