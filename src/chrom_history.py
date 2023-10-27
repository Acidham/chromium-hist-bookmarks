#!/usr/bin/python3
# -*- coding: utf-8 -*-
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
from Favicon import Icons

HISTORY_MAP = {
    "brave": "Library/Application Support/BraveSoftware/Brave-Browser/Default/History",
    "brave_beta": "Library/Application Support/BraveSoftware/Brave-Browser-Beta/Default/History",
    "chromium": "Library/Application Support/Chromium/Default/History",
    "chrome": "Library/Application Support/Google/Chrome/Default/History",
    "opera": "Library/Application Support/com.operasoftware.Opera/History",
    "sidekick": 'Library/Application Support/Sidekick/Default/History',
    "vivaldi": "Library/Application Support/Vivaldi/Default/History",
    "edge": "Library/Application Support/Microsoft Edge/Default/History",
    "arc": "Library/Application Support/Arc/User Data/Default/History",
    "safari": "Library/Safari/History.db"
}

# Get Browser Histories to load per env (true/false)
HISTORIES = list()
for k in HISTORY_MAP.keys():
    if Tools.getEnvBool(k):
        HISTORIES.append(HISTORY_MAP.get(k))

# Get ignored Domains settings
d = Tools.getEnv("ignored_domains", None)
ignored_domains = d.split(',') if d else None

# Show favicon in results or default wf icon
show_favicon = Tools.getEnvBool("show_favicon")

# if set to true history entries will be sorted
# based on recent visitied otherwise number of visits
sort_recent = Tools.getEnvBool("sort_recent")

# Date format settings
DATE_FMT = Tools.getEnv("date_format", default='%d. %B %Y')


def history_paths() -> list:
    """
    Get valid pathes to history from HISTORIES variable

    Returns:
        list: available paths of history files
    """
    user_dir = os.path.expanduser("~")
    hists = [os.path.join(user_dir, h) for h in HISTORIES]

    valid_hists = list()
    # write log if history db was found or not
    for h in hists:
        if os.path.isfile(h):
            valid_hists.append(h)
            Tools.log(f"{h} → found")
        else:
            Tools.log(f"{h} → NOT found")
    return valid_hists


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
    # Remove duplicate Entries
    results = removeDuplicates(results)
    # evmove ignored domains
    if ignored_domains:
        results = remove_ignored_domains(results, ignored_domains)
    # Reduce search results to 30
    results = results[:30]
    # Sort by element. Element 2=visited, 3=recent
    sort_by = 3 if sort_recent else 2
    results = Tools.sortListTuple(results, sort_by)  # Sort based on visits
    return results


def remove_ignored_domains(results: list, ignored_domains: list) -> list:
    """
    removes results based on domain ignore list

    Args:
        results (list): History results list with tubles
        ignored_domains (list): list of domains to ignore

    Returns:
        list: _description_
    """
    new_results = list()
    if len(ignored_domains) > 0:
        for r in results:
            for i in ignored_domains:
                inner_result = r
                if i in r[0]:
                    inner_result = None
                    break
            if inner_result:
                new_results.append(inner_result)
    else:
        new_results = results
    return new_results


def sql(db: str) -> list:
    """
    Executes SQL depending on History path
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
            # SQL satement for Safari
            if "Safari" in db:
                select_statement = f"""
                    SELECT history_items.url, history_visits.title, history_items.visit_count,(history_visits.visit_time + 978307200)
                    FROM history_items
                        INNER JOIN history_visits
                        ON history_visits.history_item = history_items.id
                    WHERE history_items.url IS NOT NULL AND
						history_visits.TITLE IS NOT NULL AND
						history_items.url != '' order by visit_time DESC
                """
            # SQL statement for Chromium Brothers
            else:
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
        Tools.log(f"SQL Error: {e}")
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
    Time Stamp (ms) into formatted date string

    Args:

        time_ms (int):  time in ms from 01/01/1601
        fmt (str, optional): Format of the Date string. Defaults to '%d. %B %Y'.

    Returns:

        str: Formatted Date String
    """
    t_string = time.strftime(fmt, time.gmtime(time_ms))
    return t_string


def main():
    # Get wf cached directory for writing into debugger
    wf_cache_dir = Tools.getCacheDir()
    # Get wf data directory for writing into debugger
    wf_data_dir = Tools.getDataDir()
    # Check and write python version
    Tools.log(f"Cache Dir: {wf_cache_dir}")
    Tools.log(f'Data Dir: {wf_data_dir}')
    Tools.log("PYTHON VERSION:", sys.version)
    if sys.version_info < (3, 7):
        Tools.log("Python version 3.7.0 or higher required!")
        sys.exit(0)

    # Create Workflow items object
    wf = Items()
    search_term = Tools.getArgv(1)
    locked_history_dbs = history_paths()
    # if selected browser(s) in config was not found stop here
    if len(locked_history_dbs) == 0:
        wf.setItem(
            title="Browser History not found!",
            subtitle="Ensure Browser is installed or choose available browser(s) in CONFIGURE WORKFLOW",
            valid=False
        )
        wf.addItem()
        wf.write()
        sys.exit(0)
    # get search results exit if Nothing was entered in search
    results = list()
    if search_term is not None:
        results = get_histories(locked_history_dbs, search_term)
    else:
        sys.exit(0)
    # if result the write alfred response
    if len(results) > 0:
        # Cache Favicons
        if show_favicon:
            ico = Icons(results)
        for i in results:
            url = i[0]
            title = i[1]
            visits = i[2]
            last_visit = formatTimeStamp(i[3], fmt=DATE_FMT)
            wf.setItem(
                title=title,
                subtitle=f"Last visit: {last_visit}(Visits: {visits})",
                arg=url,
                quicklookurl=url
            )
            if show_favicon:
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
            title="Nothing found in History!",
            subtitle=f'Search "{search_term}" in Google?',
            arg=f"https://www.google.com/search?q={search_term}",
        )
        wf.addItem()
    wf.write()


if __name__ == "__main__":
    main()
