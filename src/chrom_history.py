#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
import sqlite3
import sys
from unicodedata import normalize

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

FIRE_HISTORIE = '/Library/Application Support/Firefox/Profiles'


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
        if cur and prev.lower() != cur.lower():
            newList.append(i)
            prev = cur
    return newList


def path_to_chrome_histories():
    """
    Get valid pathes to chrome history from BOOKMARKS variable

    Returns:
        list: available paths of history files
    """
    user_dir = os.path.expanduser('~')
    hists = [user_dir + h for h in HISTORIES]
    valid_hists = list()
    for h in hists:
        if os.path.isfile(h):
            valid_hists.append(h)
            Tools.log("{0} found".format(h))
        else:
            Tools.log("{0} NOT found".format(h))
    return valid_hists


def get_sql(field, search):
    search_terms = search.split('&') if '&' in search else search.split(' ')
    search_terms = [normalize('NFC', s.decode('utf-8')) for s in search_terms]
    search_terms = [u'LOWER({0}) LIKE LOWER("%{1}%")'.format(field, s) for s in search_terms]
    if "&" in search:
        sql = u" AND ".join(search_terms)
    else:
        sql = u" OR ".join(search_terms)
    return sql


def path_to_fire_history():
    """
    Get valid pathes to firefox history from BOOKMARKS variable

    Returns:
        list: available paths of history files
    """
    user_dir = os.path.expanduser('~')
    f_home = user_dir + FIRE_HISTORIE
    valid_hist = list()
    if os.path.isdir(f_home):
        Tools.log('{0} found'.format(f_home))
        f_home_dirs = ['{0}/{1}'.format(f_home, o) for o in os.listdir(f_home)]
        for f in f_home_dirs:
            if os.path.isdir(f):
                f_sub_dirs = ['{0}/{1}'.format(f, o) for o in os.listdir(f)]
                for fs in f_sub_dirs:
                    if os.path.isfile(fs) and os.path.basename(fs) == 'places.sqlite':
                        valid_hist = fs
    else:
        Tools.log("{0} NOT found".format(f_home))
    return valid_hist


def search_chrome_histories(chrome_locked_db, query):
    """
    Load Chrome History files into list

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
            with sqlite3.connect(history_db) as c:
                cursor = c.cursor()
                select_statement = """
                SELECT DISTINCT urls.url, urls.title, urls.visit_count
                FROM urls, visits
                WHERE urls.id = visits.url AND
                urls.title IS NOT NULL AND
                ({0}) OR
                ({1}) AND
                urls.title != '' order by last_visit_time DESC LIMIT 1000;""".format(get_sql("urls.title", query), get_sql("urls.url", query))
                cursor.execute(select_statement)
                r = cursor.fetchall()
                results.extend(r)
            os.remove(history_db)
        except sqlite3.Error:
            pass
    return results


def search_fire_history(fire_locked_db, query):
    """
    Load Firefox History files into list

    Args:
        fire_locked_db (list): Contains valid history paths

    Returns:
        list: hitory entries unfiltered
    """
    fire_history_db = '/tmp/places.sqlite'
    results = list()
    if len(fire_locked_db) > 0:
        try:
            shutil.copy2(fire_locked_db, '/tmp')

            with sqlite3.connect(fire_history_db) as c:
                cursor = c.cursor()
                select_statement = u"""
                select DISTINCT url,title,visit_count
                FROM moz_places JOIN moz_historyvisits
                WHERE ({0}) OR
                ({1}) AND
                title != '' order by last_visit_date DESC LIMIT 1000;""".format(get_sql("title", query), get_sql("url", query))
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
        title = i[1].encode('utf-8')
        visits = i[2]
        wf.setItem(
            title=title,
            subtitle="(Visits: {0}) {1}".format(str(visits), url),
            arg=url,
            quicklookurl=url
        )
        wf.addItem()
a = wf.getItemsLengths()
if wf.getItemsLengths() == 0:
    wf.setItem(
        title="Nothing found in History!",
        subtitle="Search with Google?",
        arg='https://www.google.com/search?q={0}'.format(search_term.encode('utf-8'))
    )
    wf.addItem()
wf.write()
