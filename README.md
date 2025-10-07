# Browser History and Bookmarks Search

The Workflow searches History and Bookmarks of the configured Browsers simulatiously.

## Supported Browsers

- Chromium
- Google Chrome
- Brave and Brave beta (Chromium)
- MS Edge
- Vivaldi
- Opera
- Sidekick
- Arc
- Comet (Perplexity AI)
- Safari

## Requires

* Python 3
* Alfred 5

## Usage

### History


Search History with keyword: `bh`

Type `&` in between of the search terms to search for multiple entries e.g.:
 `Car&Bike` match entries with `Car or Bike rental` but NOT `Car driving school`

### Bookmarks

Search Bookmarks with keyword: `bm`

### Other Actions

Pressing `CMD` to enter `Other Actions...`:

* `Copy to Clipboard`: Copies the URL into the Clipboard
* `Open Domain`: Opens the domain  (e.g. www.google.com) in default Browser
* `Open In...`: Opens the URL with the Alfred's build in Open-In other Browser

### Bookmark Location

When viewing bookmarks, press `SHIFT` to see the bookmark's location in your browser's folder structure:

* The subtitle will show `Location: Bookmarks Bar > Folder Name > Subfolder` 
* Press `SHIFT + ENTER` to copy the location path to clipboard

This helps you quickly find where a bookmark is organized in your browser.
