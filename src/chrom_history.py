#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
import sqlite3
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


def match(search_term, results):
    search_terms = search_term.split('&') if '&' in search_term else search_term.split(' ')

    for s in search_terms:
        n_list = list()
        s = normalize('NFD', s.decode('utf-8'))
        for r in results:
            t = normalize('NFD', r[1].decode('utf-8'))
            # sys.stderr.write('Title: '+t+'\n')
            s = normalize('NFD', s.decode('utf-8'))
            # sys.stderr.write("url: " + s + '\n')
            if s.lower() in t.lower():
                n_list.append(r)
        results = n_list
    return results[:50]


def path_to_fire_history():
    """
    Get valid pathes to firefox history from BOOKMARKS variable

    Returns:
        list: available paths of history files
    """
    user_dir = os.path.expanduser('~')
    f_home = user_dir + FIRE_HISTORIE
    f_home_dirs = ['{0}/{1}'.format(f_home, o) for o in os.listdir(f_home)]
    valid_hist = None
    for f in f_home_dirs:
        if os.path.isdir(f):
            f_sub_dirs = ['{0}/{1}'.format(f, o) for o in os.listdir(f)]
            for fs in f_sub_dirs:
                if os.path.isfile(fs) and os.path.basename(fs) == 'places.sqlite':
                    valid_hist = fs
    return valid_hist


def load_chrome_histories(chrome_locked_db):
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
                urls.title IS NOT NULL
                AND urls.title != '' order by last_visit_time DESC limit 100;"""
                cursor.execute(select_statement)
                r = cursor.fetchall()
                results.extend(r)
            os.remove(history_db)
        except IOError:
            pass
    return results


def load_fire_history(fire_locked_db):
    """
    Load Firefox History files into list

    Args:
        fire_locked_db (list): Contains valid history paths

    Returns:
        list: hitory entries unfiltered
    """
    fire_history_db = '/tmp/places.sqlite'
    results = list()
    try:
        shutil.copy2(fire_locked_db, '/tmp')
        with sqlite3.connect(fire_history_db) as c:
            cursor = c.cursor()
            select_statement = """
            select DISTINCT url,title,visit_count
            FROM moz_places JOIN moz_historyvisits
            WHERE title is not NULL and title != '' order by last_visit_date DESC limit 100;"""
            cursor.execute(select_statement)
            r = cursor.fetchall()
            results.extend(r)
        os.remove(fire_history_db)
    except:
        pass
    return results


wf = Items()

search_term = Tools.getArgv(1) if Tools.getArgv(1) is not None else ''
# sys.stderr.write(search_term.encode('utf-8'))
chrome_locked_db = path_to_chrome_histories()
fire_locked_db = path_to_fire_history()

hist_all = load_chrome_histories(chrome_locked_db)
fire_hist = load_fire_history(fire_locked_db)
hist_all = hist_all + fire_hist

# Remove duplicate Entries
results = removeDuplicates(hist_all)
# Search entered into Alfred
# results = filterResults(results, search_term)
results = match(search_term, results) if len(search_term) > 0 else results[:50]
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
