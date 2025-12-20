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
from browser_config import BOOKMARKS_MAP, get_browser_name_from_path


# Show favicon in results or default wf icon
show_favicon = Tools.getEnvBool("show_favicon")

# Determine default search operator (AND/OR)
search_operator_default = Tools.getEnv(
    "search_operator_default", "AND").upper() != "OR"

BOOKMARKS = list()
# Get Browser Histories to load based on user configuration
for k in BOOKMARKS_MAP.keys():
    if Tools.getEnvBool(k):
        BOOKMARKS.append(BOOKMARKS_MAP.get(k))


def removeDuplicates(li: list) -> list:
    """
    Removes Duplicates from bookmark file based on URL.
    When same URL exists in multiple browsers, keeps first occurrence.

    Args:
        li(list): list of bookmark entries (name, url, path, browser)

    Returns:
        list: filtered bookmark entries with duplicate URLs removed
    """
    seen_urls = {}
    result = []
    for entry in li:
        url = entry[1]  # URL is at index 1
        if url not in seen_urls:
            seen_urls[url] = True
            result.append(entry)
    return result


def get_all_urls(the_json: str, browser: str) -> list:
    """
    Extract all URLs, title, and folder path from Bookmark files

    Args:
        the_json (str): All Bookmarks read from file
        browser (str): Browser name

    Returns:
        list(tuple): List of tuple with Bookmarks (name, url, path, browser)
    """
    def extract_data(data: dict, path: list):
        if isinstance(data, dict) and data.get('type') == 'url':
            folder_path = ' > '.join(path) if path else 'Root'
            urls.append({
                'name': data.get('name'),
                'url': data.get('url'),
                'path': folder_path
            })
        if isinstance(data, dict) and data.get('type') == 'folder':
            folder_name = data.get('name', 'Unnamed Folder')
            the_children = data.get('children')
            new_path = path + [folder_name]
            get_container(the_children, new_path)

    def get_container(o: Union[list, dict], path: list = []):
        if isinstance(o, list):
            for i in o:
                extract_data(i, path)
        if isinstance(o, dict):
            for k, i in o.items():
                # Use the key as folder name for root-level containers
                container_name = k.replace('_', ' ').title() if k not in [
                    'children'] else ''
                if container_name and isinstance(i, dict) and i.get('type') == 'folder':
                    extract_data(i, [container_name]
                                 if container_name else path)
                else:
                    extract_data(i, path)

    urls = list()
    get_container(the_json)
    s_list_dict = sorted(urls, key=lambda k: k['name'], reverse=False)
    ret_list = [(l.get('name'), l.get('url'), l.get('path'), browser)
                for l in s_list_dict]
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


def extract_safari_bookmarks(bookmark_data, bookmarks_list, path=[], browser="safari") -> None:
    """
    Recursively extract bookmarks (title, URL, path, and browser) from Safari bookmarks data.
    Args:
        bookmark_data (list or dict): The Safari bookmarks data, which can be a list or a dictionary.
        bookmarks_list (list): The list to which extracted bookmarks (title, URL, path, browser) will be appended.
        path (list): Current folder path as a list of folder names.
        browser (str): Browser name (default: "safari")
    Returns:
        None
    """
    if isinstance(bookmark_data, list):
        for item in bookmark_data:
            extract_safari_bookmarks(item, bookmarks_list, path, browser)
    elif isinstance(bookmark_data, dict):
        if "Children" in bookmark_data:
            folder_name = bookmark_data.get("Title", "")
            new_path = path + [folder_name] if folder_name else path
            extract_safari_bookmarks(
                bookmark_data["Children"], bookmarks_list, new_path, browser)
        elif "URLString" in bookmark_data and "URIDictionary" in bookmark_data:
            title = bookmark_data["URIDictionary"].get("title", "Untitled")
            url = bookmark_data["URLString"]
            folder_path = ' > '.join(path) if path else 'Root'
            bookmarks_list.append((title, url, folder_path, browser))


def get_safari_bookmarks_json(file: str, browser: str = "safari") -> list:
    """
    Get all bookmarks from Safari Bookmark file

    Args:
        file (str): Path to Safari Bookmark file
        browser (str): Browser name (default: "safari")

    Returns:
        list: List of bookmarks (title, URL, path, and browser)

    """
    with open(file, "rb") as fp:
        plist = load(fp)
    bookmarks = []
    extract_safari_bookmarks(plist, bookmarks, [], browser)
    return bookmarks


def match(search_term: str, results: list) -> list:
    """
    Filters a list of tuples based on a search term.
    Args:
        search_term (str): The term to search for. Can include '&' or '|' to specify AND or OR logic.
        results (list): A list of tuples (name, url, path, browser) to search within.
    Returns:
        list: A list of tuples that match the search term based on the specified logic.
    """
    def is_in_tuple(tple: tuple, st: str) -> bool:
        # Search in name, url, path (but not browser)
        # Only search first 3 elements for better performance
        for e in tple[:3]:
            if st.lower() in str(e).lower():
                return True  # Early exit on first match
        return False

    result_lst = []
    
    # Parse search terms once
    if '&' in search_term:
        search_terms = search_term.split('&')
        use_and_logic = True
    elif '|' in search_term:
        search_terms = search_term.split('|')
        use_and_logic = False
    else:
        search_terms = search_term.split()
        use_and_logic = search_operator_default
    
    # Determine check function once before loop
    check_func = all if use_and_logic else any

    for r in results:
        if check_func(is_in_tuple(r, ts) for ts in search_terms):
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
    Tools.log(f"Search query: '{query}'")
    bms = paths_to_bookmarks()
    Tools.log(f"Found {len(bms)} bookmark file(s)")

    if len(bms) > 0:
        matches = list()
        # Generate list of bookmarks matches the search
        bookmarks = []
        for bookmarks_file in bms:
            browser = get_browser_name_from_path(bookmarks_file, "bookmarks")
            if "Safari" in bookmarks_file:
                bookmarks = get_safari_bookmarks_json(bookmarks_file, browser)
                Tools.log(f"Loaded {len(bookmarks)} Safari bookmarks")
               # pass
            else:
                bm_json = get_json_from_file(bookmarks_file)
                bookmarks = get_all_urls(bm_json, browser)
                Tools.log(
                    f"Loaded {len(bookmarks)} bookmarks from {bookmarks_file}")
            matches.extend(match(query, bookmarks))
        # finally remove duplicates from all browser bookmarks
        matches = removeDuplicates(matches)
        Tools.log(f"Total matches after deduplication: {len(matches)}")
        # generate list of matches for Favicon download
        ico_matches = []
        if show_favicon:
            ico_matches = [(i2, i1) for i1, i2, i3, i4 in matches]
        # Heat Favicon Cache
        ico = Icons(ico_matches)
        # generate script filter output
        for m in matches:
            url = m[1]
            name = m[0] if m[0] else url.split('/')[2]
            path = m[2] if len(m) > 2 else 'Unknown'
            browser = m[3] if len(m) > 3 else 'unknown'
            # Combine url and browser with pipe separator
            url_with_browser = f"{url}|{browser}"
            Tools.log(f"Bookmark: '{name}' | Path: '{path}' | Browser: '{browser}'")
            wf.setItem(
                title=name,
                subtitle=f"{url[:80]}",
                arg=url_with_browser,
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
                arg=url_with_browser
            )
            wf.addMod(
                key="alt",
                subtitle=url,
                arg=url_with_browser
            )
            wf.addMod(
                key="shift",
                subtitle=f"Location: {path}",
                arg=path
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
