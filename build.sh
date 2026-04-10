#!/bin/bash

glib-compile-resources resources.xml --target=resources.gresource


python3 -m nuitka --standalone --onefile \
--include-package=gi \
--include-package=cairo \
--include-package-data=gi \
--include-package-data=cairo \
--include-data-files=resources.gresource=resources.gresource \
-o l1p0-menus \
main.py

sudo install -Dm755 l1p0-menus /usr/bin/l1p0-menus
