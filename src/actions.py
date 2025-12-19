#!/usr/bin/python3

import os
from urllib.parse import urlparse

from Alfred3 import Items, Tools
from browser_config import BROWSER_APPS, get_browser_display_name

url_with_browser = Tools.getEnv('url')
# Parse URL and browser from pipe-separated string
if '|' in url_with_browser:
    url, browser = url_with_browser.split('|', 1)
else:
    url = url_with_browser
    browser = None

domain = Tools.getDomain(url)

# Script Filter item [Title, Subtitle, arg]
wf_items = [
    ['Copy to Clipboard', 'Copy URL to Clipboard', 'clipboard'],
    ['Open Domain', f'Open {domain}', 'domain'],
    ['Open URL in...', 'Open URL in another Browser', 'openin'],
]

# Add "Open in Source Browser" option if browser info is available
if browser and browser in BROWSER_APPS:
    app_path = BROWSER_APPS[browser]
    # Check if the app exists
    if os.path.exists(app_path):
        browser_display_name = get_browser_display_name(browser)
        wf_items.append(['Open in Source Browser', f'Open URL in {browser_display_name}', 'sourcebrowser'])

# Create WF script filter output object and emit
wf = Items()
for w in wf_items:
    wf.setItem(
        title=w[0],
        subtitle=w[1],
        arg=w[2]
    )
    icon_path = f'icons/{w[2]}.png'
    wf.setIcon(
        icon_path,
        m_type='image'
    )
    wf.addItem()
wf.write()
