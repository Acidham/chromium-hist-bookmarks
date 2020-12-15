# Chromium History and Bookmark Search for Alfred

## Required

* **Python 3**

* Supported Chromium & Gecko Browsers:
  * Chromium
  * Google Chrome
  * Brave and Brave Dev (Chromium)
  * Vivaldi
  * Opera
  * Firefox

## Configuration

The Workflow uses only History & Bookmarks files when browser is installed. In addition, the Workflow environment variables allow limiting which browser history & bookmarks will be searched.

* `True` = Included in search
* `False` = Excluded from search

## Usage

### History Search

* `bh` query 
    * Type `&` in between of the search terms to search for multiple entries e.g.: 
         `Car&Bike` match entries with `Car or Bike rental` but NOT `Car driving school`
* *SHIFT* for Quicklook URL

### Bookmark Search

* `bm`query
* *SHIFT* for quicklook URL

