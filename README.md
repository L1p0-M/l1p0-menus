# L1p0-Menus

A fast, full event-driven desktop popup menu system designed specifically for Wayland and Hyprland environments. 

No polling, no CPU wasting. Built on top of a Python daemon using `gio` for native D-Bus integration.

## Preview

<p align="center">
<video src="https://github.com/user-attachments/assets/36596ac5-4c08-462e-918b-0e4e2543f144" width="600" autoplay loop muted playsinline></video>
</p>

## ✨ Features & Architecture

* **Pure Event-Driven:** Zero-percent idle CPU usage. The daemon sleeps and wakes up instantly only when D-Bus signals or external events trigger it.
* **GTK4 + Layer Shell:** Leveraging `gtk4-layer-shell` for hardware-accelerated, responsive, and native Wayland layer management.
* **Modern & Smooth Animations:** Fully animated UI elements using native GTK `Revealer` widgets, providing fluid, hardware-accelerated transitions for dropdowns and detail panels.
* **First-Class D-Bus Citizen:** Built-in `GIO/GDBus` integration. It functions as a fully registered `SecretAgent` for both `NetworkManager` and `BlueZ`, securely handling Wi-Fi passwords and Bluetooth pairing prompts natively within the UI.
* **Highly Customizable:** Complete separation of logic, configuration, and styling via standard `config.json` and a powerful custom `style.css` file.
* **Modern Packaging:** Clean, robust deployment built entirely with `Hatchling` following the latest PEP 517 standards. Perfect for simple Arch Linux (AUR) PKGBUILD maintenance.

## Available Popups / Modules

The package currently includes the following fully-featured popup menus:

* **📅 Weather & Calendar:** A beautiful calendar dropdown equipped with an hourly/daily weather forecast breakdown powered by OpenWeatherMap.
* **🔋 Battery Status:** Displays active discharging/charging rates with a collapsible detailed view showing hardware info (Vendor, Model, Charge Cycles, Energy Pull, and Design Capacity).
* **🌐 Network Manager:** Full Wi-Fi control. Scan available networks, view connection details (IP, Gateway, DNS, MAC, Speed), and connect securely via the integrated SecretAgent. Manage your saved networks from the ui: Turn off/on autoconnect or forget the network.
* **🔵 Bluetooth Control:** Easily toggle Bluetooth, switch discoverability, scan for devices, pair/disconnect, and view battery levels for connected peripherals.
* **☀️ Brightness & Night Light:** Smooth brightness slider with an integrated Night Light toggle and custom temperature preset adjustment.
* **🔊 Audio:** Master volume and microphone sliders with quick-access audio output source switching (e.g., internal audio to Bluetooth headset).

## Style

To style the menus to match your specific theme, `l1p0-menus` gives you the option to place a `style.css` file in the `~/.config/l1p0-menu/` directory and write your own CSS. :) 

As a starting point, I recommend checking out the internal (default) CSS file [here](src/assets/style.css).

---

## Config

You can place a `config.json` file in `~/.config/l1p0-menu/` to configure the menus. 

* **Valid anchors:** `top-right`, `top-left`, `top` (or `top-center`), `bottom-left`, `bottom-right`, `bottom` (or `bottom-center`).
* **Margins configuration:** Configured as a string: `"top, right, bottom, left"`.

### Example `config.json`:

```json
{
  "weather-clock": {
        "api_key": "YOUR_OPENWEATHERMAP_API_KEY",
        "language": "YOUR LANGUAGE (defaults to 'en')",
        "city": "YOUR CITY",
        "show_sunset": true,
        "margin": "10",
        "anchor": "top-center"
   },
   "network": {
        "margin": "10, 10",
        "anchor": "top-right"
   },
   "battery": {
        "margin": "10, 10",
        "anchor": "top-right"
   },
   "audio": {
        "margin": "10, 10",
        "anchor": "top-right"
   },
   "brightness": {
        "margin": "10, 10",
        "anchor": "top-right",
        "night_preset": "2500"
   }
}
```

## Popup animation and Blur

Every popup has its own namespace to make it easy to have different animations on each one. Add this to your `hyprland.lua` to enable blur and popup animations:

```lua
hl.layer_rule({
    match = { namespace = "audio-layer" },
    blur = true,
    blur_popups = true,
    ignore_alpha = 0,
    animation = "slide top"
})

hl.layer_rule({
    match = { namespace = "brightness-layer" },
    blur = true,
    blur_popups = true,
    ignore_alpha = 0,
    animation = "slide top"
})

hl.layer_rule({
    match = { namespace = "calendar-layer" },
    blur = true,
    blur_popups = true,
    ignore_alpha = 0,
    animation = "slide top"
})

hl.layer_rule({
    match = { namespace = "battery-layer" },
    blur = true,
    blur_popups = true,
    ignore_alpha = 0,
    animation = "slide top"
})

hl.layer_rule({
    match = { namespace = "network-layer" },
    blur = true,
    blur_popups = true,
    ignore_alpha = 0,
    animation = "slide top"
})
```

# License

This project is licensed under the MIT License. You can read it [here](LICENSE).

# AI Usage

No AI was used during the development of this project, only good old documentation, 10-year-old StackOverflow questions, and a massive amount of coffee. :D
