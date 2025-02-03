#!/usr/bin/python3
# -*- coding: utf-8 -*-
import codecs
import json
import os
import sys
from plistlib import load
from typing import Union

from Alfred3 import Items as Items
from Alfred3 import Tools as Tools
from Favicon import Icons

# Bookmark file path relative to HOME

BOOKMARKS_MAP = {
    "brave": 'Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks',
    "brave_beta": 'Library/Application Support/BraveSoftware/Brave-Browser-Beta/Default/Bookmarks',
    "chrome": 'Library/Application Support/Google/Chrome/Default/Bookmarks',
    "chromium": 'Library/Application Support/Chromium/Default/Bookmarks',
    "opera": 'Library/Application Support/com.operasoftware.Opera/Bookmarks',
    "sidekick": 'Library/Application Support/Sidekick/Default/Bookmarks',
    "vivaldi": 'Library/Application Support/Vivaldi/Default/Bookmarks',
    "edge": 'Library/Application Support/Microsoft Edge/Default/Bookmarks',
    "arc": "Library/Application Support/Arc/User Data/Default/Bookmarks",
    "safari": 'Library/Safari/Bookmarks.plist'
}

# Show favicon in results or default wf icon
show_favicon = Tools.getEnvBool("show_favicon")

BOOKMARKS = list()
# Get Browser Histories to load based on user configuration
for k in BOOKMARKS_MAP.keys():
    if Tools.getEnvBool(k):
        BOOKMARKS.append(BOOKMARKS_MAP.get(k))


def removeDuplicates(li: list) -> list:
    """
    Removes Duplicates from bookmark file

    Args:
        li(list): list of bookmark entries

    Returns:
        list: filtered bookmark entries
    """
    visited = set()
    output = []
    for a, b in li:
        if a not in visited:
            visited.add(a)
            output.append((a, b))
    return output


def get_all_urls(the_json: str) -> list:
    """
    Extract all URLs and title from Bookmark files

    Args:
        the_json (str): All Bookmarks read from file

    Returns:
        list(tuble): List of tublle with Bookmarks url and title
    """
    def extract_data(data: dict):
        if isinstance(data, dict) and data.get('type') == 'url':
            urls.append({'name': data.get('name'), 'url': data.get('url')})
        if isinstance(data, dict) and data.get('type') == 'folder':
            the_children = data.get('children')
            get_container(the_children)

    def get_container(o: Union[list, dict]):
        if isinstance(o, list):
            for i in o:
                extract_data(i)
        if isinstance(o, dict):
            for k, i in o.items():
                extract_data(i)

    urls = list()
    get_container(the_json)
    s_list_dict = sorted(urls, key=lambda k: k['name'], reverse=False)
    ret_list = [(l.get('name'), l.get('url')) for l in s_list_dict]
    return ret_list


def paths_to_bookmarks() -> list:
    """
    Get all valid bookmarks pahts from BOOKMARKS

    Returns:
        list: valid bookmark paths
    """
    user_dir = os.path.expanduser('~')
    bms = [os.path.join(user_dir, b) for b in BOOKMARKS]
    valid_bms = list()
    for b in bms:
        if os.path.isfile(b):
            valid_bms.append(b)
            Tools.log(f"{b} → found")
        else:
            Tools.log(f"{b} → NOT found")

    return valid_bms


def get_json_from_file(file: str) -> json:
    """
    Get Bookmark JSON

    Args:
        file(str): File path to valid bookmark file

    Returns:
        str: JSON of Bookmarks
    """
    return json.load(codecs.open(file, 'r', 'utf-8-sig'))['roots']


def extract_bookmarks(bookmark_data, bookmarks_list) -> None:
    """
    Recursively extract bookmarks (title and URL) from Safari bookmarks data.
    Args:
        bookmark_data (list or dict): The Safari bookmarks data, which can be a list or a dictionary.
        bookmarks_list (list): The list to which extracted bookmarks (title and URL) will be appended.
    Returns:
        None
    """
    if isinstance(bookmark_data, list):
        for item in bookmark_data:
            extract_bookmarks(item, bookmarks_list)
    elif isinstance(bookmark_data, dict):
        if "Children" in bookmark_data:
            extract_bookmarks(bookmark_data["Children"], bookmarks_list)
        elif "URLString" in bookmark_data and "URIDictionary" in bookmark_data:
            title = bookmark_data["URIDictionary"].get("title", "Untitled")
            url = bookmark_data["URLString"]
            bookmarks_list.append((title, url))


def get_safari_bookmarks_json(file: str) -> list:
    """
    Get all bookmarks from Safari Bookmark file

    Args:
        file (str): Path to Safari Bookmark file

    Returns:
        list: List of bookmarks (title and URL)

    """
    with open(file, "rb") as fp:
        plist = load(fp)
    bookmarks = []
    extract_bookmarks(plist, bookmarks)
    return bookmarks


def match(search_term: str, results: list) -> list:
    """
    Filters a list of tuples based on a search term.
    Args:
        search_term (str): The term to search for. Can include '&' or '|' to specify AND or OR logic.
        results (list): A list of tuples to search within.
    Returns:
        list: A list of tuples that match the search term based on the specified logic.
    The function supports the following search operators:
        - '&': All search terms must be present in a tuple for it to be included in the result.
        - '|': At least one of the search terms must be present in a tuple for it to be included in the result.
        - No operator: The search term must be present in a tuple for it to be included in the result.
    """

    def is_in_tuple(tple: tuple, st: str) -> bool:
        match = False
        for e in tple:
            if st.lower() in str(e).lower():
                match = True
        return match

    result_lst = []
    if '&' in search_term:
        search_terms = search_term.split('&')
        search_operator = "&"
    elif '|' in search_term:
        search_terms = search_term.split('|')
        search_operator = "|"
    else:
        search_terms = [search_term, ]
        search_operator = ""

    for r in results:
        if search_operator == "&" and all([is_in_tuple(r, ts) for ts in search_terms]):
            result_lst.append(r)
        if search_operator == "|" and any([is_in_tuple(r, ts) for ts in search_terms]):
            result_lst.append(r)
        if search_operator != "|" and search_operator != "&" and any([is_in_tuple(r, ts) for ts in search_terms]):
            result_lst.append(r)
    return result_lst


def main():
    # Log python version
    Tools.log("PYTHON VERSION:", sys.version)
    # check python > 3.7.0
    if sys.version_info < (3, 7):
        Tools.log("Python version 3.7.0 or higher required!")
        sys.exit(0)

    # Workflow item object
    wf = Items()
    query = Tools.getArgv(1) if Tools.getArgv(1) is not None else str()
    bms = paths_to_bookmarks()

    if len(bms) > 0:
        matches = list()
        # Generate list of bookmarks matches the search
        bookmarks = []
        for bookmarks_file in bms:
            if "Safari" in bookmarks_file:
                bookmarks = get_safari_bookmarks_json(bookmarks_file)
               # pass
            else:
                bm_json = get_json_from_file(bookmarks_file)
                bookmarks = get_all_urls(bm_json)
            matches.extend(match(query, bookmarks))
        # finally remove duplicates from all browser bookmarks
        matches = removeDuplicates(matches)
        # generate list of matches for Favicon download
        ico_matches = []
        if show_favicon:
            ico_matches = [(i2, i1) for i1, i2 in matches]
        # Heat Favicon Cache
        ico = Icons(ico_matches)
        # generate script filter output
        for m in matches:
            name = m[0]
            url = m[1]
            wf.setItem(
                title=name,
                subtitle=f"{url[:80]}",
                arg=url,
                quicklookurl=url
            )
            if show_favicon:
                # get favicoon for url
                favicon = ico.get_favion_path(url)
                if favicon:
                    wf.setIcon(
                        favicon,
                        "image"
                    )
            wf.addMod(
                key='cmd',
                subtitle="Other Actions...",
                arg=url
            )
            wf.addMod(
                key="alt",
                subtitle=url,
                arg=url
            )
            wf.addItem()
    if wf.getItemsLengths() == 0:
        wf.setItem(
            title='No Bookmark found!',
            subtitle=f'Search "{query}" in Google...',
            arg=f'https://www.google.com/search?q={query}'
        )
        wf.addItem()
    wf.write()


if __name__ == "__main__":
    main()
