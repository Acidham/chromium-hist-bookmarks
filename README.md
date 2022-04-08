# Chromium History and Bookmark Search for Alfred

## Required

* **Python 3**

* Supported Chromium & Gecko Browsers:
  * Brave and Brave Dev (Chromium)
  * Google Chrome and Chromium
  * Firefox
  * Opera
  * Sidekick
  * Vivaldi

## Configuration

This Workflow uses only history & bookmarks files from installed browsers. Additionally, the Workflow's environment variables allow limiting which browsers' histories & bookmarks are searched.

* `True` = Included in search
* `False` = Excluded from search

### Date Format

`date_format` defines how the date will be shown for last visit. Visit https://strftime.org/ for reference.

### Sorting

`sort_recent` if set to `True` history entries will be sorted based on recent visits otherwise number of visits

## Usage

### History Search

* `bh` query
    * Type `&` in between of the search terms to search for multiple entries e.g.:
         `Car&Bike` match entries with `Car or Bike rental` but NOT `Car driving school`
* `CMD` shows the URL
* `ALT` opens Domain of the URL instead of the full URL
* `SHIFT` opens page in Quicklook

### Bookmark Search

* `bm`query
* *SHIFT* for quicklook URL
