# L1p0-Menus

##Preview

<p align="center">
<video src="https://github.com/user-attachments/assets/36596ac5-4c08-462e-918b-0e4e2543f144" width="600" autoplay loop muted playsinline></video>
</p>

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
