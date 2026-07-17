import json

class Request:
    """
    Request object that parses the incoming request.
    Access the object's attributes to get the request data.
    .method: The request method (GET, POST, etc.)
    .path: The request path
    .protocol: The request protocol
    .headers: The request headers
    .data: The request data
    .content_type: The content type of the request
    """
    def __init__(self, request):
        request = self.parse_http_request(request)
        self.method = request["method"]
        if "?" in request["path"]:
            self.path = request["path"].split("?")[0]
            params = request["path"].split("?")[1].split("&")
            self.params = {}
            for param in params:
                key = param.split("=")[0]
                value = param.split("=")[1]
                self.params[key] = value
        else:
            self.path = request["path"]
            self.params = {} 
        self.protocol = request["protocol"]
        self.headers = request["headers"]
        self.content_type = self.headers.get("Content-Type")
        self.body = request.get("body")

    def parse_http_request(self, request):
            lines = request.split("\n")
            request_line = lines[0]
            headers = {}
            for line in lines[1:]:
                if ":" in line and line != "\r\n":
                    split_line = line.split(":")
                    key = split_line[0]
                    value = split_line[1]
                    headers[key] = value.strip()
                    if key == "Content-Type" and "boundary" in value:
                        headers["boundary"] = value.split("=")[1]
                        headers["Content-Type"] = "multipart/form-data"
            content: dict = self.handle_content_types(headers, request)
            method, path, protocol = request_line.split(" ")
            return {
                "method": method,
                "path": path,
                "protocol": protocol,
                "headers": headers,
                "body": content
            }
    
    def handle_content_types(self, headers, request) -> dict:
        content_type = headers.get("Content-Type")
        if content_type == "application/json":
            return self.handle_json(request)
        elif content_type == "application/x-www-form-urlencoded":
            pass
        elif content_type == "multipart/form-data":
            return self.handle_multipart_form_data(headers, request)
        return {}

    def handle_json(self, request):
        form = request.split("\r\n\r\n")[1]
        form = json.loads(form)
        return form 

    def handle_form_urlencoded(self, request):
        pass

    def handle_multipart_form_data(self, headers, request) -> dict:
        form = request.split(headers["boundary"])
        form_dict = {}
        for key in form[2:]:
            current_key = key.split(";")[1].split("=")[1].strip().split("\r\n")[0].replace('"', "")
            value = key.split(";")[1].split("=")[1].strip().split("\r\n")[2]
            form_dict[current_key] = value
        return form_dict

    def GET(self, key):
        if self.body:
            return self.body.get(key)
        else:
            raise Exception("No body data")

    def __str__(self):
        returnstr = f"""
        Method: {self.method}
        Path: {self.path}
        Protocol: {self.protocol}
        Headers: {self.headers}
        """
        if self.body:
            returnstr += f"body: {self.body}"
        return returnstr