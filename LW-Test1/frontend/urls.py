import frontend.views as views
from resources.path import path

urls = {
    path("/", "index", views.index, "GET"),
}