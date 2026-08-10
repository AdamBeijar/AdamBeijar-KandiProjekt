import importlib.util
import sys

def include(filename):
    module = importPythonFile(filename)
    return module

def importPythonFile(filename):
    module_name = filename[:-3]  # remove the '.py' extension
    spec = importlib.util.spec_from_file_location(module_name, filename)
    module = importlib.util.module_from_spec(spec) # type: ignore
    sys.modules[module_name] = module
    spec.loader.exec_module(module) # type: ignore
    return module

if __name__ == "__main__":
    urls = include("test/testurl.py")
    print(urls.urls)