from main.responses import HtmlResponse, JsonResponse
from resources.request import Request

def getUsers(request: Request):
    users = [
        {"name": "John", "age": 25},
        {"name": "Jane", "age": 22},
        {"name": "Bob", "age": 30},
    ]
    return JsonResponse(users, 200)

def getBlogUsers(request: Request):
    users = [
        {"name": "John", "age": 25},
        {"name": "Jane", "age": 22},
        {"name": "Bob", "age": 30},
        {"name": "Alice", "age": 28},
        {"name": "Eve", "age": 35},
    ]
    return JsonResponse(users, 200)