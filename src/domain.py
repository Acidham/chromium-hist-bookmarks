#!/usr/bin/python3

from sys import stdout
from urllib.parse import urlparse

from Alfred3 import AlfJson, Tools

url = Tools.getEnv('url')
domain = Tools.getDomain(url)

# Create AlfJson object to store output
aj = AlfJson()

# Add the domain as a variable with key "url" 
aj.add_variables({"url": domain})

# Write the JSON output
aj.write_json()
