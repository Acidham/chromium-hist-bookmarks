#!/usr/bin/python3

from urllib.parse import urlparse

from Alfred3 import Items, Tools

url = Tools.getEnv('url')
domain = Tools.getDomain(url)

# Script Filter item [Title,Subtitle,arg/uid/icon]
wf_items = [
    ['Copy to Clipboard', 'Copy URL to Clipboard', 'clipboard'],
    ['Open Domain', f'Open {domain}', 'domain'],
    ['Open URL in...', 'Open URL in another Browser', 'openin'],
]

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
