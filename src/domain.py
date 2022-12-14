#!/usr/bin/python3

from sys import stdout
from urllib.parse import urlparse

from Alfred3 import AlfJson, Tools

url = Tools.getEnv('url')
domain = Tools.getDomain(url)

aj = AlfJson()
aj.add_variables({"url": domain})
aj.write_json()
