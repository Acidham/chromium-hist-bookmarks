#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import sqlite3
import sys
import uuid
from multiprocessing import Pool
from unicodedata import normalize

from Alfred3 import Items as Items
from Alfred3 import Tools as Tools

HISTORY_MAP = {
    "chromium": "/Library/Application Support/Chromium/Default/History",
    "brave": "/Library/Application Support/BraveSoftware/Brave-Browser/Default/History",
    "brave_dev": "/Library/Application Support/BraveSoftware/Brave-Browser-Dev/Default/History",
    "chrome": "/Library/Application Support/Google/Chrome/Default/History",
    "vivaldi": "/Library/Application Support/Vivaldi/Default/History",
    "opera": "/Library/Application Support/com.operasoftware.Opera/History",
    "firefox": "/Library/Application Support/Firefox/Profiles"
}

HISTORIES = list()
# Get Browser Histories to load per env
for k in HISTORY_MAP.keys():
    browser = Tools.getEnv(k)
    is_set = True if browser == "True" else False
    HISTORIES.append(HISTORY_MAP.get(k))

# Limit SQL results for better performance
# will only be applied to Firefox history
SQL_LIMIT = 100000

Tools.log("PYTHON VERSION:", sys.version)
if sys.version_info < (3, 7):
    print("Python version 3.7.0 or higher required!")
    sys.exit(0)


def history_paths() -> list:
    """
    Get valid pathes to history from HISTORIES variable

    Returns:
        list: available paths of history files
    """
    user_dir = os.path.expanduser("~")
    hists = [f"{user_dir}{h}" for h in HISTORIES]
    valid_hists = list()
    for h in hists:
        if "Firefox" in h:
            h = path_to_fire_history(h)
        if os.path.isfile(h):
            valid_hists.append(h)
            Tools.log(f"{h} found")
        else:
            Tools.log(f"{h} NOT found")
    return valid_hists


def path_to_fire_history(f_home: str) -> str:
    """
    Get valid pathes to firefox history

    Returns:
        str: available paths of history file
    """
    valid_hist = ""
    if os.path.isdir(f_home):
        Tools.log(f"{f_home} found")
        f_home_dirs = [f"{f_home}/{o}" for o in os.listdir(f_home)]
        for f in f_home_dirs:
            if os.path.isdir(f) and f.endswith("default-release"):
                f_sub_dirs = [f"{f}/{o}" for o in os.listdir(f)]
                for fs in f_sub_dirs:
                    if os.path.isfile(fs) and os.path.basename(fs) == "places.sqlite":
                        valid_hist = fs
                        break
    else:
        Tools.log(f"{f_home} NOT found")
    return valid_hist


def get_histories(dbs: list, query: str) -> list:
    """
    Load History files into list with multiprocessing

    Args:
        dbs(list): Contains valid history paths

    Returns:
        list: hitory entries unfiltered
    """

    results = list()
    with Pool(len(dbs)) as p:
        results = p.map(sql, [db for db in dbs])
    matches = []
    for r in results:
        matches = matches + r
    results = search_in_tuples(matches, query)
    return results


def sql(db: str) -> list:
    res = []
    history_db = f"/tmp/{uuid.uuid1()}"
    try:
        shutil.copy2(db, history_db)
        with sqlite3.connect(history_db) as c:
            cursor = c.cursor()
            if "Firefox" in db:
                select_statement = f"""
                select DISTINCT url, title, visit_count
                FROM moz_places JOIN moz_historyvisits
                WHERE title != '' order by last_visit_date DESC LIMIT {SQL_LIMIT}; """
            else:
                select_statement = f"""
                SELECT DISTINCT urls.url, urls.title, urls.visit_count
                FROM urls, visits
                WHERE urls.id = visits.url AND
                urls.title IS NOT NULL AND
                urls.title != '' order by last_visit_time DESC; """
            Tools.log(select_statement)
            cursor.execute(select_statement)
            r = cursor.fetchall()
            res.extend(r)
        os.remove(history_db)
    except sqlite3.Error:
        pass
    return res


def get_search_terms(search: str) -> tuple:
    """
    Explode search term string

    Args:
        search(str): search term(s), can contain & or |

    Returns:
        tuple: Tuple with search terms
    """
    if "&" in search:
        search_terms = tuple(search.split("&"))
    elif "|" in search:
        search_terms = tuple(search.split("|"))
    else:
        search_terms = tuple(search.split(" "))
    search_terms = [normalize("NFC", s) for s in search_terms]
    return search_terms


def removeDuplicates(li: list) -> list:
    """
    Removes Duplicates from history file

    Args:
        li(list): list of history entries

    Returns:
        list: filtered history entries
    """
    visited = set()
    output = []
    for a, b, c in li:
        if b not in visited:
            visited.add(b)
            output.append((a, b, c))
    return output


def search_in_tuples(tuples: list, search: str) -> list:
    """
    Search for serach term in list of tuples

    Args:
        tuples(list): List contains tuple to search
        search(str): Search contains & or & or none

    Returns:
        list: tuple list with result of query srting
    """

    def is_in_tuple(tple: tuple, st: str) -> bool:
        match = False
        for e in tple:
            if st.lower() in str(e).lower():
                match = True
        return match

    search_terms = get_search_terms(search)
    result = list()
    for t in tuples:
        # Search AND
        if "&" in search and all([is_in_tuple(t, ts) for ts in search_terms]):
            result.append(t)
        # Search OR
        if "|" in search and any([is_in_tuple(t, ts) for ts in search_terms]):
            result.append(t)
        # Search Single term
        if "|" not in search and "&" not in search and any([is_in_tuple(t, ts) for ts in search_terms]):
            result.append(t)
    return result


def main():
    wf = Items()

    search_term = Tools.getArgv(1)
    locked_history_dbs = history_paths()
    if search_term is not None:
        histories = get_histories(locked_history_dbs, search_term)
    else:
        sys.exit(0)
    # Remove duplicate Entries
    results = removeDuplicates(histories)
    # Search entered into Alfred
    results = results[:30]
    # Sort based on visits
    results = Tools.sortListTuple(results, 2)

    if len(results) > 0:
        for i in results:
            url = i[0]
            title = i[1]
            visits = i[2]
            wf.setItem(
                title=title, subtitle=f"(Visits: {visits}) {url}", arg=url, quicklookurl=url
            )
            wf.addItem()
    if wf.getItemsLengths() == 0:
        wf.setItem(
            title="Nothing found in History!",
            subtitle=f'Search "{search_term}" in Google?',
            arg=f"https://www.google.com/search?q={search_term}",
        )
        wf.addItem()
    wf.write()


if __name__ == "__main__":
    main()
