##Style

To style the menus to match your specific theme,l1p0-menus gives you the option to place a style.css file to ~/.config/l1p0-menus/ location and write your own css :) For starting point i recommend to check out the internal(default) css file *here*


##Config

You can place a config.json file to ~/.config/l1p0-menus/ to configure the menus. Valid anchors are: top-right,top-left,top(-center),bottom-left,bottom-right,bottom(-center). Margins are configured as follows: "top, right, bottom, left" 
Example config.json:

```
{
  "weather-clock": {
        "api_key": "YOUR_OPENWEATHERMAP_API_KEY",
        "language": "YOUR LANGUAGE(defaults to 'en')",
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
        "anchor": "top-right"
   }
}
```