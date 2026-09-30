"""
Browser automation tools: opening websites and executing web/YouTube searches.
"""

import webbrowser
import urllib.parse
from typing import Tuple


def open_url(url: str) -> Tuple[bool, str]:
    """Open a URL in the user's default web browser."""
    try:
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url
        webbrowser.open(clean_url, new=2)
        return True, f"Opened {clean_url}"
    except Exception as e:
        return False, f"Failed to open URL '{url}': {e}"


def search_web(query: str) -> Tuple[bool, str]:
    """Execute a Google web search in the default browser."""
    try:
        encoded_query = urllib.parse.quote_plus(query.strip())
        search_url = f"https://www.google.com/search?q={encoded_query}"
        webbrowser.open(search_url, new=2)
        return True, f"Searching Google for '{query}'"
    except Exception as e:
        return False, f"Failed to execute web search: {e}"


def search_youtube(query: str) -> Tuple[bool, str]:
    """Execute a YouTube search in the default browser."""
    try:
        encoded_query = urllib.parse.quote_plus(query.strip())
        yt_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        webbrowser.open(yt_url, new=2)
        return True, f"Searching YouTube for '{query}'"
    except Exception as e:
        return False, f"Failed to execute YouTube search: {e}"


def search_maps(query: str) -> Tuple[bool, str]:
    """Execute a Google Maps search in the default browser."""
    try:
        encoded_query = urllib.parse.quote_plus(query.strip())
        maps_url = f"https://www.google.com/maps/search/{encoded_query}"
        webbrowser.open(maps_url, new=2)
        return True, f"Searching Google Maps for '{query}'"
    except Exception as e:
        return False, f"Failed to search Google Maps: {e}"


def search_amazon(query: str) -> Tuple[bool, str]:
    """Execute an Amazon product search in the default browser."""
    try:
        encoded_query = urllib.parse.quote_plus(query.strip())
        amazon_url = f"https://www.amazon.com/s?k={encoded_query}"
        webbrowser.open(amazon_url, new=2)
        return True, f"Searching Amazon for '{query}'"
    except Exception as e:
        return False, f"Failed to search Amazon: {e}"
