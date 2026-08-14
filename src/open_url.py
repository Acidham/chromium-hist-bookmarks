#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Open the selected URL in the default browser.

Replaces Alfred's built in "Open URL" object, which routes through
LaunchServices and therefore re-encodes fragments of URLs such as
https://app.diagrams.net/#Hfoo%2Fbar.drawio#%7B%22pageId%22%3A%22x%22%7D
See url_opener.py for details.
"""

import sys

from Alfred3 import Tools
from url_opener import open_url

url = Tools.getEnv('url')

if not url:
    Tools.log("No URL provided in environment")
    sys.exit(1)

if not open_url(url):
    sys.exit(1)
