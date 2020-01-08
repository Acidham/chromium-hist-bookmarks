#!/usr/bin/python
import codecs
import json
import os

from Alfred import Items as Items
from Alfred import Tools as Tools

# Bookmark file path relative to HOME
BOOKMARKS = [
    '/Library/Application Support/Chromium/Default/Bookmarks',
    '/Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks',
    '/Library/Application Support/BraveSoftware/Brave-Browser-Dev/Default/Bookmarks',
    '/Library/Application Support/Google/Chrome/Default/Bookmarks',
    '/Library/Application Support/Vivaldi/Default/Bookmarks',
    '/Library/Application Support/com.operasoftware.Opera/Bookmarks'
]


def get_all_urls(the_json):
    """
    Extract all URLs and title from Bookmark files

    Args:
        the_json (str): All Bookmarks read from file

    Returns:
        list: Bookmarks url and title
    """
    def extract_data(data):
        if type(data) == dict and data.get('type') == 'url':
            urls.append({'name': data.get('name'), 'url': data.get('url')})
        if type(data) == dict and data.get('type') == 'folder':
            the_children = data.get('children')
            get_container(the_children)

    def get_container(o):
        if isinstance(o, list):
            for i in o:
                extract_data(i)
        if isinstance(o, dict):
            for k, i in o.items():
                extract_data(i)

    urls = list()
    get_container(the_json)
    return sorted(urls, key=lambda k: k['name'], reverse=False)


def paths_to_bookmarks():
    """
    Get all valid bookmarks pahts from BOOKMARKS

    Returns:
        list: valid bookmark paths
    """
    user_dir = os.path.expanduser('~')
    bms = [user_dir + p for p in BOOKMARKS]
    valid_bms = list()
    for b in bms:
        if os.path.isfile(b):
            valid_bms.append(b)
    return valid_bms


def get_json_from_file(file):
    """
    Get Bookmark JSON

    Args:
        file (str): File path to valid bookmark file

    Returns:
        str: JSON of Bookmarks
    """
    return json.load(codecs.open(file, 'r', 'utf-8-sig'))['roots']


wf = Items()
query = Tools.getArgv(1) if Tools.getArgv(1) is not None else str()
bms = paths_to_bookmarks()

if len(bms) > 0:
    for bookmarks_file in bms:
        bm_json = get_json_from_file(bookmarks_file)
        bookmarks = get_all_urls(bm_json)
        for bm in bookmarks:
            name = bm.get('name')
            url = bm.get('url')
            if query == str() or query.lower() in name.lower():
                wf.setItem(
                    title=name,
                    subtitle=url,
                    arg=url,
                    quicklookurl=url
                )
                wf.addItem()
else:
    wf.setItem(
        title="Bookmark File not found!",
        subtitle='Ensure a Chromium Browser is installed',
        valid=False
    )
    wf.addItem()

if wf.getItemsLengths() == 0:
    wf.setItem(
        title='No Bookmark found!',
        subtitle='Search \"%s\" in Google...' % query,
        arg='https://www.google.com/search?q=%s' % query
    )
    wf.addItem()

wf.write()
