#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import sqlite3
import sys
from unicodedata import normalize

from Alfred3 import Items as Items
from Alfred3 import Tools as Tools

# Hitory file relative to HOME
HISTORIES = [
    "/Library/Application Support/Chromium/Default/History",
    "/Library/Application Support/BraveSoftware/Brave-Browser/Default/History",
    "/Library/Application Support/BraveSoftware/Brave-Browser-Dev/Default/History",
    "/Library/Application Support/Google/Chrome/Default/History",
    "/Library/Application Support/Vivaldi/Default/History",
    "/Library/Application Support/com.operasoftware.Opera/History",
]

FIRE_HISTORIE = "/Library/Application Support/Firefox/Profiles"

Tools.log("PYTHON VERSION:", sys.version)
if sys.version_info < (3, 7):
    print('Python version 3.7.0 or higher required!')
    sys.exit(0)


def removeDuplicates(li: list) -> list:
    """
    Removes Duplicates from history file

    Args:
        li(list): list of history entries

    Returns:
        list: filtered history entries
    """
    prev = str()
    newList = list()
    for i in li:
        cur = i[1]
        if cur and prev.lower() != cur.lower():
            newList.append(i)
            prev = cur
    return newList


def path_to_chrome_histories() -> list:
    """
    Get valid pathes to chrome history from BOOKMARKS variable

    Returns:
        list: available paths of history files
    """
    user_dir = os.path.expanduser("~")
    hists = [f"{user_dir}{h}" for h in HISTORIES]
    valid_hists = list()
    for h in hists:
        if os.path.isfile(h):
            valid_hists.append(h)
            Tools.log(f"{h} found")
        else:
            Tools.log(f"{h} NOT found")
    return valid_hists


def get_sql(field: str, search: str) -> str:
    search_terms = search.split("&") if "&" in search else search.split("|")
    search_terms = [normalize("NFC", s) for s in search_terms]
    search_terms = [f'LOWER({field}) LIKE LOWER("%{s}%")' for s in search_terms]
    if "&" in search:
        sql = " AND ".join(search_terms)
    elif "|":
        sql = " OR ".join(search_terms)
    else:
        sql = f"LOWER{field} LIKE LOWER({normalize('NFC', search)})"
    return sql


def path_to_fire_history() -> str:
    """
    Get valid pathes to firefox history from BOOKMARKS variable

    Returns:
        str: available paths of history file
    """
    user_dir = os.path.expanduser("~")
    f_home = f"{user_dir}{FIRE_HISTORIE}"
    valid_hist = ""
    if os.path.isdir(f_home):
        Tools.log(f"{f_home} found")
        f_home_dirs = [f"{f_home}/{o}" for o in os.listdir(f_home)]
        for f in f_home_dirs:
            if os.path.isdir(f):
                f_sub_dirs = [f"{f}/{o}" for o in os.listdir(f)]
                for fs in f_sub_dirs:
                    if os.path.isfile(fs) and os.path.basename(fs) == "places.sqlite":
                        valid_hist = fs
                        break
    else:
        Tools.log(f"{f_home} NOT found")
    return valid_hist


def search_chrome_histories(chrome_locked_db: list, query: str) -> list:
    """
    Load Chrome History files into list

    Args:
        chrome_locked_db(list): Contains valid history paths

    Returns:
        list: hitory entries unfiltered
    """
    history_db = "/tmp/History"
    results = list()
    for db in chrome_locked_db:
        try:
            shutil.copy2(db, "/tmp")
            with sqlite3.connect(history_db) as c:
                cursor = c.cursor()
                select_statement = f"""
                SELECT DISTINCT urls.url, urls.title, urls.visit_count
                FROM urls, visits
                WHERE urls.id = visits.url AND
                urls.title IS NOT NULL AND
                ({get_sql("urls.title", query)}) OR
                ({get_sql("urls.url", query)}) AND
                urls.title != '' order by last_visit_time DESC LIMIT 1000; """
                cursor.execute(select_statement)
                r = cursor.fetchall()
                results.extend(r)
            os.remove(history_db)
        except sqlite3.Error:
            pass
    return results


def search_fire_history(fire_locked_db: str, query: str) -> list:
    """
    Load Firefox History files into list

    Args:
        fire_locked_db(list): Contains valid history paths

    Returns:
        list: hitory entries unfiltered
    """
    fire_history_db = "/tmp/places.sqlite"
    results = list()
    if fire_locked_db:
        try:
            shutil.copy2(fire_locked_db, "/tmp")

            with sqlite3.connect(fire_history_db) as c:
                cursor = c.cursor()
                select_statement = f"""
                select DISTINCT url, title, visit_count
                FROM moz_places JOIN moz_historyvisits
                WHERE({get_sql("title", query)}) OR
                ({get_sql("url", query)}) AND
                title != '' order by last_visit_date DESC LIMIT 1000;"""
                cursor.execute(select_statement)
                r = cursor.fetchall()
                results.extend(r)
            os.remove(fire_history_db)
        except sqlite3.Error:
            pass
    return results


wf = Items()

search_term = Tools.getArgv(1)
chrome_locked_db = path_to_chrome_histories()
fire_locked_db = path_to_fire_history()

if search_term is not None:
    hist_all = search_chrome_histories(chrome_locked_db, search_term)
    fire_hist = search_fire_history(fire_locked_db, search_term)
    hist_all = hist_all + fire_hist
else:
    sys.exit(0)


# Remove duplicate Entries
results = removeDuplicates(hist_all)
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
            title=title,
            subtitle=f"(Visits: {visits}) {url}",
            arg=url, quicklookurl=url
        )
        wf.addItem()
a = wf.getItemsLengths()
if wf.getItemsLengths() == 0:
    wf.setItem(
        title="Nothing found in History!",
        subtitle=f'Search "{search_term}" in Google?',
        arg=f"https://www.google.com/search?q={search_term}",
    )
    wf.addItem()
wf.write()
