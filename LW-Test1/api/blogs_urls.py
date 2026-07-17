from resources.path import path
import api.views as views

urls = [
    path("/getBlogUsers", "getBlogUsers", views.getBlogUsers, "GET"),
]