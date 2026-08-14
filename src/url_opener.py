#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
URL opening helpers.

macOS LaunchServices (used by `open`, by AppleScript's `open location` and by
Alfred's own "Open URL" object) re-percent-encodes the fragment of a URL when
that fragment contains characters which are not legal in a fragment per
RFC 3986 - most commonly a second "#". Re-encoding escapes the *whole* fragment,
so already percent-encoded sequences are encoded a second time:

    https://app.diagrams.net/#Hfoo%2Fbar.drawio#%7B%22pageId%22%3A%22x%22%7D
 -> https://app.diagrams.net/#Hfoo%252Fbar.drawio%23%257B%2522pageId%2522%253A%2522x%2522%257D

The browser then receives a different fragment than the one that was bookmarked
and the page fails to load. Web apps that keep state in the fragment (draw.io,
diagrams.net, many SPAs) hit this regularly.

For those URLs we bypass LaunchServices and hand the URL straight to the
browser executable as an argv, which passes it through untouched.
"""

import os
import plistlib
import re
import subprocess

from Alfred3 import Tools
from browser_config import BROWSER_APPS

# RFC 3986: fragment = *( pchar / "/" / "?" ), pchar = unreserved / pct-encoded
# / sub-delims / ":" / "@". A fragment built only from these characters is left
# alone by LaunchServices; anything else makes it re-encode the whole fragment.
_SAFE_FRAGMENT = re.compile(r"^(?:[A-Za-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9A-Fa-f]{2})*$")

# Browsers that cannot be handed a URL on the command line. LaunchServices is
# the only way in, so such URLs stay subject to the re-encoding described above.
_NO_ARGV_BUNDLE_IDS = ("com.apple.safari",)


def is_launchservices_safe(url: str) -> bool:
    """
    Check whether macOS LaunchServices would pass a URL through unchanged.

    Args:
        url (str): URL to check

    Returns:
        bool: True if `open` can be used without mangling the URL
    """
    fragment = url.partition('#')[2]
    if not fragment:
        return True
    return bool(_SAFE_FRAGMENT.match(fragment))


def get_bundle_id(app_path: str) -> str:
    """
    Read the bundle identifier of an application bundle.

    Args:
        app_path (str): Path to the .app bundle

    Returns:
        str: Bundle identifier, empty string if it cannot be read
    """
    try:
        with open(os.path.join(app_path, 'Contents', 'Info.plist'), 'rb') as fp:
            return plistlib.load(fp).get('CFBundleIdentifier', '')
    except Exception as e:
        Tools.log(f"Cannot read Info.plist of {app_path}: {e}")
        return ''


def get_app_executable(app_path: str) -> str:
    """
    Get the main executable of an application bundle.

    Args:
        app_path (str): Path to the .app bundle

    Returns:
        str: Path to the executable, empty string if it cannot be determined
    """
    try:
        with open(os.path.join(app_path, 'Contents', 'Info.plist'), 'rb') as fp:
            executable = plistlib.load(fp).get('CFBundleExecutable', '')
    except Exception as e:
        Tools.log(f"Cannot read Info.plist of {app_path}: {e}")
        return ''
    if not executable:
        return ''
    binary = os.path.join(app_path, 'Contents', 'MacOS', executable)
    return binary if os.path.isfile(binary) else ''


def get_default_browser_app() -> str:
    """
    Determine the app bundle registered as the default https handler.

    Returns:
        str: Path to the .app bundle, empty string if it cannot be determined
    """
    prefs = os.path.expanduser(
        '~/Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist')
    bundle_id = ''
    try:
        with open(prefs, 'rb') as fp:
            handlers = plistlib.load(fp).get('LSHandlers', [])
        for h in handlers:
            if h.get('LSHandlerURLScheme') == 'https':
                bundle_id = h.get('LSHandlerRoleAll', '')
                break
    except Exception as e:
        Tools.log(f"Cannot read LaunchServices preferences: {e}")
        return ''
    if not bundle_id:
        Tools.log("No default https handler configured, Safari is assumed")
        return ''

    # LaunchServices stores bundle ids lower cased, compare accordingly
    bundle_id = bundle_id.lower()
    # Known browsers first, this avoids a Spotlight query in the common case
    for app_path in BROWSER_APPS.values():
        if os.path.isdir(app_path) and get_bundle_id(app_path).lower() == bundle_id:
            return app_path
    try:
        found = subprocess.run(
            ['mdfind', f"kMDItemCFBundleIdentifier == '{bundle_id}'c"],
            capture_output=True, text=True, timeout=5).stdout.splitlines()
    except Exception as e:
        Tools.log(f"mdfind for {bundle_id} failed: {e}")
        return ''
    for line in found:
        if line.endswith('.app'):
            return line
    Tools.log(f"Cannot locate application for bundle id {bundle_id}")
    return ''


def _open_via_executable(app_path: str, url: str) -> bool:
    """
    Hand the URL to the browser executable directly, bypassing LaunchServices.

    Args:
        app_path (str): Path to the .app bundle
        url (str): URL to open

    Returns:
        bool: True if the browser was launched
    """
    if get_bundle_id(app_path).lower() in _NO_ARGV_BUNDLE_IDS:
        Tools.log(f"{app_path} does not accept URLs as argument")
        return False
    binary = get_app_executable(app_path)
    if not binary:
        return False
    try:
        subprocess.Popen(
            [binary, url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True)
    except Exception as e:
        Tools.log(f"Error launching {binary}: {e}")
        return False
    # The executable opens the tab but does not necessarily raise the window
    subprocess.run(['open', '-a', app_path], check=False)
    Tools.log(f"Opened {url} via {binary}")
    return True


def open_url(url: str, app_path: str = '') -> bool:
    """
    Open a URL, in the given browser or in the default browser.

    URLs that LaunchServices would rewrite are passed to the browser executable
    directly so that the fragment survives unchanged.

    Args:
        url (str): URL to open
        app_path (str, optional): Path to the browser .app bundle. Defaults to
                                  the default browser.

    Returns:
        bool: True if successful, False otherwise
    """
    if app_path and not os.path.exists(app_path):
        Tools.log(f"Browser app not found: {app_path}")
        return False

    if not is_launchservices_safe(url):
        target = app_path or get_default_browser_app()
        if target and _open_via_executable(target, url):
            return True
        Tools.log(f"Falling back to `open`, {url} may get re-encoded")

    cmd = ['open', '-a', app_path, url] if app_path else ['open', url]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        Tools.log(f"Error opening URL: {e}")
        return False
    Tools.log(f"Opened {url}" + (f" in {app_path}" if app_path else ''))
    return True
