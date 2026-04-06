#!/bin/bash

python3 -m nuitka --standalone --onefile \
--include-package=gi \
--include-package=cairo \
--include-package-data=gi \
--include-package-data=cairo \
--include-data-files=style.css=style.css \
main.py

sudo install -Dm755 main.bin /usr/bin/l1p0-menus
