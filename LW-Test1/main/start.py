import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from main import Server

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, server):
        self.server = server

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"File {event.src_path} has been modified")
            self.server.stop()
            self.server = Server()
            self.server.start()

if __name__ == "__main__":
    server = Server()
    
    event_handler = ChangeHandler(server)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()
    
    server.start()  # Start the initial server
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        server.stop()  # Ensure the server is stopped on exit
    
    observer.join()
