from main.responses import HtmlResponse, JsonResponse 

def index(request):
    return JsonResponse({"ping": True})