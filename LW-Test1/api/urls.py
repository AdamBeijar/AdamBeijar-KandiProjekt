from resources.path import path
import api.views as views
from resources.include import include

urls = [
    path("/getUsers", "index", views.getUsers, "GET"),
    path("/blog", include("api/blogs_urls.py"), "GET")
]