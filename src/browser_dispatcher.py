#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import subprocess
import sys

from Alfred3 import Tools
from browser_config import BROWSER_APPS


def open_url_in_browser(app_path: str, url: str) -> bool:
    """
    Opens a URL in the specified browser application

    Args:
        app_path (str): Path to the browser application (e.g., /Applications/Safari.app)
        url (str): URL to open

    Returns:
        bool: True if successful, False otherwise
    """
    # Check if the app exists
    if not os.path.exists(app_path):
        Tools.log(f"Browser app not found: {app_path}")
        return False
    
    try:
        # Use 'open' command with -a flag to specify the application
        subprocess.run(['open', '-a', app_path, url], check=True)
        Tools.log(f"Successfully opened {url} in {app_path}")
        return True
    except subprocess.CalledProcessError as e:
        Tools.log(f"Error opening URL in browser: {e}")
        return False
    except Exception as e:
        Tools.log(f"Unexpected error: {e}")
        return False


def main():
    # Get the action argument passed from Alfred
    action = Tools.getArgv(1)
    
    if not action:
        Tools.log("No action provided")
        sys.exit(1)
    
    # Execute the action
    if action == "sourcebrowser":
        # Read URL and browser from environment variable
        url_with_browser = Tools.getEnv('url')
        
        if not url_with_browser:
            Tools.log("No URL provided in environment")
            sys.exit(1)
        
        # Parse URL and browser from pipe-separated string
        if '|' not in url_with_browser:
            Tools.log(f"Invalid URL format, missing browser info: {url_with_browser}")
            sys.exit(1)
        
        url, browser = url_with_browser.split('|', 1)
        
        Tools.log(f"URL: {url}")
        Tools.log(f"Browser: {browser}")
        
        # Get the app path for the browser
        if browser not in BROWSER_APPS:
            Tools.log(f"Unknown browser: {browser}")
            sys.exit(1)
        
        app_path = BROWSER_APPS[browser]
        Tools.log(f"App Path: {app_path}")
        
        # Open the URL in the specified browser
        success = open_url_in_browser(app_path, url)
        if not success:
            sys.exit(1)
    else:
        Tools.log(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()

