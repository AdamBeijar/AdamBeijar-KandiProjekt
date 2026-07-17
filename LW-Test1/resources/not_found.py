from resources.path import path
from main.responses import HtmlNotFoundResponse 

def not_found():
    """Return a path that will return a 404 Not Found response."""
    return path("/not_found", "not_found", not_found_view, "GET")

def not_found_view(request):
    return HtmlNotFoundResponse()

def not_found_static():
    """Return a path that will return a 404 Not Found response for static files."""
    return path("/not_found", "not_found", not_found_view, "GET")