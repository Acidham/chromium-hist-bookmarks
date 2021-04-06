#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import os
import shutil
import sqlite3
import sys
import time
import uuid
from multiprocessing.pool import ThreadPool as Pool
from unicodedata import normalize

from Alfred3 import Items as Items
from Alfred3 import Tools as Tools

HISTORY_MAP = {
    "brave": "/Library/Application Support/BraveSoftware/Brave-Browser/Default/History",
    "brave_dev": "/Library/Application Support/BraveSoftware/Brave-Browser-Dev/Default/History",
    "chromium": "/Library/Application Support/Chromium/Default/History",
    "chrome": "/Library/Application Support/Google/Chrome/Default/History",
    "firefox": "/Library/Application Support/Firefox/Profiles",
    "opera": "/Library/Application Support/com.operasoftware.Opera/History",
    "sidekick": '/Library/Application Support/Sidekick/Default/History',
    "vivaldi": "/Library/Application Support/Vivaldi/Default/History"
}

HISTORIES = list()
# Get Browser Histories to load per env (true/false)
for k in HISTORY_MAP.keys():
    is_set = Tools.getEnvBool(k)
    if is_set:
        HISTORIES.append(HISTORY_MAP.get(k))

# Limit SQL results for better performance
# will only be applied to Firefox history
SQL_FIRE_LIMIT = Tools.getEnv("sql_fire_limit", default=500)
DATE_FMT = Tools.getEnv("date_format", default='%d. %B %Y')

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
            Tools.log(f"{h} → found")
        else:
            Tools.log(f"{h} → NOT found")
    return valid_hists


def path_to_fire_history(f_home: str) -> str:
    """
    Get valid pathes to firefox history

    Returns:
        str: available paths of history file
    """
    valid_hist = ""
    if os.path.isdir(f_home):
        f_home_dirs = [f"{f_home}/{o}" for o in os.listdir(f_home)]
        for f in f_home_dirs:
            if os.path.isdir(f) and f.endswith("default-release"):
                f_sub_dirs = [f"{f}/{o}" for o in os.listdir(f)]
                for fs in f_sub_dirs:
                    if os.path.isfile(fs) and os.path.basename(fs) == "places.sqlite":
                        valid_hist = fs
                        break
    else:
        Tools.log(f"{f_home} → NOT found")
    return valid_hist


def get_histories(dbs: list, query: str) -> list:
    """
    Load History files into list

    Args:
        dbs(list): list with valid history paths

    Returns:
        list: filters history entries
    """

    results = list()
    with Pool(len(dbs)) as p:  # Exec in ThreadPool
        results = p.map(sql, [db for db in dbs])
    matches = []
    for r in results:
        matches = matches + r
    results = search_in_tuples(matches, query)
    results = removeDuplicates(results)  # Remove duplicate Entries
    results = results[:30]  # Search entered into Alfred
    results = Tools.sortListTuple(results, 2)  # Sort based on visits
    return results


def sql(db: str) -> list:
    """
    Executes SQL for Firefox and Chrome depending on History path
    provided in db: str

    Args:
        db (str): Path to History file

    Returns:
        list: result list of dictionaries (Url, Title, VisiCount)
    """
    res = []
    history_db = f"/tmp/{uuid.uuid1()}"
    try:
        shutil.copy2(db, history_db)
        with sqlite3.connect(history_db) as c:
            cursor = c.cursor()
            if "Firefox" in db:  # SQL for Firefox Browser
                select_statement = f"""
                select DISTINCT url, title, visit_count, last_visit_date/1000000
                FROM moz_places JOIN moz_historyvisits
                WHERE title != '' order by last_visit_date DESC LIMIT {SQL_FIRE_LIMIT}; """
            else:  # SQL for Chromium Browsers
                select_statement = f"""
                SELECT DISTINCT urls.url, urls.title, urls.visit_count, (urls.last_visit_time/1000000 + (strftime('%s', '1601-01-01')))
                FROM urls, visits
                WHERE urls.id = visits.url AND
                urls.title IS NOT NULL AND
                urls.title != '' order by last_visit_time DESC; """
            Tools.log(select_statement)
            cursor.execute(select_statement)
            r = cursor.fetchall()
            res.extend(r)
        os.remove(history_db)  # Delete History file in /tmp
    except sqlite3.Error as e:
        Tools.log(f"SQL Error{e}")
        sys.exit(1)
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
        search_terms = (search,)
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
    for a, b, c, d in li:
        if b not in visited:
            visited.add(b)
            output.append((a, b, c, d))
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


def formatTimeStamp(time_ms: int, fmt: str = '%d. %B %Y') -> str:
    """
    Converts Time Stamp into date string

    Args:

        time_ms (int):  time in ms from 01/01/1601
        fmt (str, optional): Format of the Date string. Defaults to '%d. %B %Y'.

    Returns:

        str: Formatted Date String
    """
    t_string = time.strftime(fmt, time.gmtime(time_ms))
    return t_string


def main():
    wf = Items()

    search_term = Tools.getArgv(1)
    locked_history_dbs = history_paths()
    results = list()
    if search_term is not None:
        results = get_histories(locked_history_dbs, search_term)
    else:
        sys.exit(0)
    if len(results) > 0:
        for i in results:
            url = i[0]
            title = i[1]
            visits = i[2]
            # last_visit = formatChromeTimeStamp(i[3])
            last_visit = formatTimeStamp(i[3], fmt=DATE_FMT)
            wf.setItem(
                title=title,
                subtitle=f"Last visited: {last_visit} (Visits: {visits})",
                arg=url,
                quicklookurl=url
            )
            wf.addMod(
                key='cmd',
                subtitle=f"{i[0]} → copy to Clipboard",
                arg='i[0]'
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
