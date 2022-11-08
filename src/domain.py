#!/usr/bin/python3

from sys import stdout
from urllib.parse import urlparse

from Alfred3 import Tools

url = Tools.getEnv('url')
domain = Tools.strJoin(urlparse(url).scheme, "://", urlparse(url).netloc)

stdout.write(domain)
