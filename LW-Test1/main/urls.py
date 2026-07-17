from resources.path import path
from resources.include import include
from main.views import index

# Define the URL patterns as "path("path", view, method)".
# If you want to use the include() function, use "path("path", include("module.urls"))".

urls = [
    path("/", "index", index, "GET")
]