import webbrowser
import urllib.parse
import logging

logger = logging.getLogger(__name__)

class WebCommands:
    def __init__(self):
        pass  # No selenium driver needed for basic web commands

    def google_search(self, query):
        """Perform Google search"""
        encoded = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded}"
        webbrowser.open(url)
        return f"Searching Google for {query}"

    def open_whatsapp(self):
        """Open WhatsApp Web"""
        webbrowser.open("https://web.whatsapp.com")
        return "WhatsApp Web opened"

    def open_youtube(self):
        """Open YouTube"""
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"

    def open_url(self, url):
        """Open any URL"""
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opening {url}"