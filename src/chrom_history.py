#!/usr/bin/python

from Alfred import Items as Items
from Alfred import Tools as Tools
import sqlite3
import shutil
import os

BRAVE_HISTORY = '/Library/Application Support/BraveSoftware/Brave-Browser/Default/History'
BRAVE_DEV_HISTORY = '/Library/Application Support/BraveSoftware/Brave-Browser-Dev/Default/History'

def removeDuplicates(li):
    prev = str()
    newList = list()
    for i in li:
        cur = i[1]
        if prev.lower() != cur.lower():
            newList.append(i)
            prev = cur
    return newList


def filterResults(li,term):
    if term != '':
        newList = list()
        for i in li:
            if (term.lower() in i[1].lower()) or (term.lower() in i[0].lower()):
                newList.append(i)
    else:
        newList = li
    return newList[:50]


def path_to_history():
    user_dir = os.path.expanduser('~')
    bm = user_dir + BRAVE_HISTORY
    bm_dev = user_dir + BRAVE_DEV_HISTORY
    return bm if os.path.isfile(bm) else bm_dev


wf = Items()

search_term = Tools.getArgv(1) if Tools.getArgv(1) is not None else ''
chrome_locked_db = path_to_history()
history_db = '/tmp/History'

try:
    shutil.copy2(chrome_locked_db, '/tmp')
except IOError:
    wf.setItem(
        title="Brave Browser History not found!",
        subtitle="You may use an older version of Brave or no Brave",
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
    results = cursor.fetchall()

os.remove(history_db)

# Remove duplicate Entries
results = removeDuplicates(results)
# Search entered into Alfred
results = filterResults(results,search_term)
# Sort based on visits
results = Tools.sortListTuple(results, 2)

if len(results) > 0:
    for i in results:
        url = i[0]
        title = i[1]
        visits = i[2]
        wf.setItem(
            title=title,
            subtitle="(Visits: %s) %s" % (str(visits),url),
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
