import resources.http_codes 
import traceback
import json

class Response:
    def __init__(self, status, data):
        self.status = status
        self.data = data
        self.status_text = self.makeStatusText()

    def makeStatusText(self):
        if self.status in resources.http_codes.http_codes:
            return resources.http_codes.http_codes[self.status]
        else:
            return "Unknown Status"

    def __str__(self):
        return f"Response(status={self.status}, data={self.data})"

    def __repr__(self):
        return str(self)
    

    
class JsonResponse(Response):
    """A response object that returns a JSON response."""
    def __init__(self, data, status=200):
        super().__init__(status, data)
        self.headers = {"Content-Type": "application/json"}
        self.data = f"HTTP/1.1 {self.status}\nContent-Type: application/json \n\n"
        self.data += json.dumps(data)

class HtmlResponse(Response):
    """A response object that returns an HTML response.
    If the data is a string, it will be returned as is.
    If the data is a file path, the file will be read and returned as the response. Just pass the file name as the data. No need to pass the full path.
    If the data is a file path and you want to pass in variables to the HTML file, pass in the variables as keyword arguments. The variables should be in the format %% variable_name %% in the HTML file."""
    def __init__(self, data, status=200, *args, **kwargs):
        super().__init__(status, data)
        self.headers = {"Content-Type": "text/html"}
        self.data = f"HTTP/1.1 {self.status}\nContent-Type: text/html"
        self.calledFrom = "/".join(traceback.extract_stack()[-2].filename.split("/")[:-1:]) + "/templates/"
        if (htmlFile := self.isTemplate(data)):
            with open(htmlFile, "r") as f:
                htmlData = f.read()
            if kwargs:
                htmlData = self.buildHtml(htmlData, **kwargs)
            self.data += "\n\n" + htmlData 
        else:
            self.data += "\n\n" + data

    def isTemplate(self, data):
        if data.endswith(".html"):
            return self.calledFrom + data
    
    def buildHtml(self, html, **kwargs):
        for key, value in kwargs.items():
            html = html.replace(f"%% {key} %%", str(value))
        if "%%{ for" in html:
            forLoops = html.split("%%{ for")
            loopDict = {}
            for idx, loop in enumerate(forLoops[1::]):
                currentLoop = {}
                loop = loop.split(" }%%")[0]
                loop = loop.split(" in ")
                loopList = loop[1].split("\n")[0].strip()
                loopContent = "\n".join(loop[1].split("\n")[1:])
                currentLoop["list"] = loopList
                currentLoop["content"] = loopContent
                currentLoop["var"] = loopContent.split("%%")[1].strip()
                currentLoop["fullLoop"] = "%%{ for" + forLoops[idx + 1]
                loopDict[idx] = currentLoop
            for idx, loop in loopDict.items():
                loopContent = ""
                print(loop["fullLoop"])
                for item in kwargs[loop["list"]]:
                    loopContent += loop["content"].replace(f"%% {loop['var']} %%", item)
                html = html.replace(loop["fullLoop"], loopContent, 1)

        return html
    
    
class HtmlNotFoundResponse(Response):
    """A response object that returns a 404 Not Found HTML response."""
    def __init__(self):
        super().__init__(404, "Not Found")
        self.headers = {"Content-Type": "text/html"}
        self.data = f"HTTP/1.1 404\nContent-Type: text/html\n\n<head><title>404 Not Found</title></head><body><h1>404 Not Found</h1></body>"

class HtmlServerErrorResponse(Response):
    """A response object that returns a 500 Server Error HTML response."""
    def __init__(self):
        super().__init__(500, "Server Error")
        self.headers = {"Content-Type": "text/html"}
        self.data = f"HTTP/1.1 500\nContent-Type: text/html\n\n<head><title>500 Server Error</title></head><body><h1>500 Server Error</h1></body>"

class HtmlForbiddenResponse(Response):
    """A response object that returns a 403 Forbidden HTML response."""
    def __init__(self):
        super().__init__(403, "Forbidden")
        self.headers = {"Content-Type": "text/html"}
        self.data = f"HTTP/1.1 403\nContent-Type: text/html\n\n<head><title>403 Forbidden</title></head><body><h1>403 Forbidden</h1></body>"

class CssResponse(Response):
    """A response object that returns a CSS response."""
    def __init__(self, data, status=200):
        super().__init__(status, data)
        self.headers = {"Content-Type": "text/css"}
        self.data = f"HTTP/1.1 {self.status}\nContent-Type: text/css\n\n{data}"