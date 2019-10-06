#!/usr/bin/python

import os
import shutil
import sqlite3

from Alfred import Items as Items
from Alfred import Tools as Tools

# Hitory file relative to HOME
HISTORIES = [
    '/Library/Application Support/Chromium/Default/History',
    '/Library/Application Support/BraveSoftware/Brave-Browser/Default/History',
    '/Library/Application Support/BraveSoftware/Brave-Browser-Dev/Default/History',
    '/Library/Application Support/Google/Chrome/Default/History',
    '/Library/Application Support/Vivaldi/Default/History',
    '/Library/Application Support/com.operasoftware.Opera/History'
]


def removeDuplicates(li):
    """
    Removes Duplicates from history file

    Args:
        li (list): list of history entries

    Returns:
        list: filtered history entries
    """
    prev = str()
    newList = list()
    for i in li:
        cur = i[1]
        if prev.lower() != cur.lower():
            newList.append(i)
            prev = cur
    return newList


def filterResults(li, term):
    """
    Search/Filter results based on search term

    Args:
        li (list): List of all History entries
        term (str): Search terms with or without '&'

    Returns:    
        list: entries matche term
    """
    if term != '':
        terms = term.split('&')
        for t in terms:
            newList = list()
            for i in li:
                if (t.lower() in i[1].lower()) or (t.lower() in i[0].lower()):
                    newList.append(i)
            li = newList
    else:
        newList = li
    return newList[:50]


def path_to_histories():
    """
    Get valid pathes to history from BOOKMARKS variable

    Returns:
        list: available paths of history files
    """
    user_dir = os.path.expanduser('~')
    hists = [user_dir + h for h in HISTORIES]
    valid_hists = list()
    for h in hists:
        if os.path.isfile(h):
            valid_hists.append(h)
    return valid_hists


def load_all_histories(chrome_locked_db):
    """
    Load History files into list

    Args:
        chrome_locked_db (list): Contains valid history paths

    Returns:
        list: hitory entries unfiltered
    """
    history_db = '/tmp/History'
    results = list()
    for db in chrome_locked_db:
        try:
            shutil.copy2(db, '/tmp')
        except IOError:
            wf.setItem(
                title="No Chromium Browser History found!",
                subtitle="You may use an older version of a Chromium Browser",
                valid=False
            )
            wf.addItem()
            wf.write()
            exit()

        with sqlite3.connect(history_db) as c:
            cursor = c.cursor()
            select_statement = "SELECT DISTINCT urls.url, urls.title, urls.visit_count " \
                "FROM urls, visits " \
                "WHERE urls.id = visits.url AND urls.title IS NOT NULL AND urls.title != '';"
            cursor.execute(select_statement)
            r = cursor.fetchall()
            results.extend(r)
            os.remove(history_db)
    return results


wf = Items()

search_term = Tools.getArgv(1) if Tools.getArgv(1) is not None else ''
chrome_locked_db = path_to_histories()
hist_all = load_all_histories(chrome_locked_db)

# Remove duplicate Entries
results = removeDuplicates(hist_all)
# Search entered into Alfred
results = filterResults(results, search_term)
# Sort based on visits
results = Tools.sortListTuple(results, 2)

if len(results) > 0:
    for i in results:
        url = i[0]
        title = i[1]
        visits = i[2]
        wf.setItem(
            title=title,
            subtitle="(Visits: %s) %s" % (str(visits), url),
            arg=url,
            quicklookurl=url
        )
        wf.addItem()
else:
    wf.setItem(
        title="Nothing found in History!",
        subtitle="Search with Google?",
        arg='https://www.google.com/search?q=%s' % search_term
    )
    wf.addItem()
wf.write()
