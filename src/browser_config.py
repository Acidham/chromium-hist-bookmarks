#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Centralized browser configuration for the Alfred workflow.
Contains all browser-related paths and mappings.
"""

# Browser application paths
BROWSER_APPS = {
    "brave": "/Applications/Brave Browser.app",
    "brave_beta": "/Applications/Brave Browser Beta.app",
    "chromium": "/Applications/Chromium.app",
    "chrome": "/Applications/Google Chrome.app",
    "opera": "/Applications/Opera.app",
    "sidekick": "/Applications/Sidekick.app",
    "vivaldi": "/Applications/Vivaldi.app",
    "edge": "/Applications/Microsoft Edge.app",
    "arc": "/Applications/Arc.app",
    "dia": "/Applications/Dia.app",
    "thorium": "/Applications/Thorium.app",
    "comet": "/Applications/Comet.app",
    "helium": "/Applications/Helium.app",
    "safari": "/Applications/Safari.app"
}

# Browser history database paths (relative to user home directory)
HISTORY_MAP = {
    "brave": "Library/Application Support/BraveSoftware/Brave-Browser/Default/History",
    "brave_beta": "Library/Application Support/BraveSoftware/Brave-Browser-Beta/Default/History",
    "chromium": "Library/Application Support/Chromium/Default/History",
    "chrome": "Library/Application Support/Google/Chrome/Default/History",
    "opera": "Library/Application Support/com.operasoftware.Opera/History",
    "sidekick": "Library/Application Support/Sidekick/Default/History",
    "vivaldi": "Library/Application Support/Vivaldi/Default/History",
    "edge": "Library/Application Support/Microsoft Edge/Default/History",
    "arc": "Library/Application Support/Arc/User Data/Default/History",
    "dia": "Library/Application Support/Dia/User Data/Default/History",
    "thorium": "Library/Application Support/Thorium/Default/History",
    "comet": "Library/Application Support/Comet/Default/History",
    "helium": "Library/Application Support/net.imput.helium/Default",
    "safari": "Library/Safari/History.db"
}

# Browser bookmark file paths (relative to user home directory)
BOOKMARKS_MAP = {
    "brave": "Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks",
    "brave_beta": "Library/Application Support/BraveSoftware/Brave-Browser-Beta/Default/Bookmarks",
    "chrome": "Library/Application Support/Google/Chrome/Default/Bookmarks",
    "chromium": "Library/Application Support/Chromium/Default/Bookmarks",
    "opera": "Library/Application Support/com.operasoftware.Opera/Bookmarks",
    "sidekick": "Library/Application Support/Sidekick/Default/Bookmarks",
    "vivaldi": "Library/Application Support/Vivaldi/Default/Bookmarks",
    "edge": "Library/Application Support/Microsoft Edge/Default/Bookmarks",
    "arc": "Library/Application Support/Arc/User Data/Default/Bookmarks",
    "dia": "Library/Application Support/Dia/User Data/Default/Bookmarks",
    "thorium": "Library/Application Support/Thorium/Default/Bookmarks",
    "comet": "Library/Application Support/Comet/Default/Bookmarks",
    "helium": "Library/Application Support/net.imput.helium/Default/Bookmarks",
    "safari": "Library/Safari/Bookmarks.plist"
}


def get_browser_name_from_path(file_path: str, map_type: str = "history") -> str:
    """
    Get browser name from file path by matching against the appropriate map.
    
    Args:
        file_path (str): Path to history/bookmark file
        map_type (str): Type of map to use - "history", "bookmarks", or "app"
    
    Returns:
        str: Browser name (e.g., 'chrome', 'brave', 'safari') or 'unknown'
    """
    if map_type == "history":
        path_map = HISTORY_MAP
    elif map_type == "bookmarks":
        path_map = BOOKMARKS_MAP
    elif map_type == "app":
        path_map = BROWSER_APPS
    else:
        return "unknown"
    
    for browser_name, path in path_map.items():
        if path in file_path:
            return browser_name
    
    return "unknown"


def get_browser_display_name(browser: str) -> str:
    """
    Convert browser key to display-friendly name.
    
    Args:
        browser (str): Browser key (e.g., 'brave_beta')
    
    Returns:
        str: Display name (e.g., 'Brave Beta')
    """
    return browser.replace('_', ' ').title()

