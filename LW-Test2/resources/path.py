import traceback
import types

class path:
    """A path object that is used to route requests to the correct view.
    If you want to create a 404 page for all paths that don't exist, use a wildcard (*) in the path.
    You can also use the include() function to include another urls.py file."""
    def __init__(self, path, name=None, view=None, method=None, include=None):
        self.path = path
        self.name = name
        self.view = view
        self.method = method
        self.args = []
        self.include = include

    def __call__(self, request):
        if self.view:
            return self.view(request)
        else:
            raise Exception("No view found for path")

    def __str__(self):
        return self.path
    