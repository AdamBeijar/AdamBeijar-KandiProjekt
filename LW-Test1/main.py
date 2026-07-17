import getopt
import sys
from main.server import Server

def helpMessage():
    print("Usage: ")
    print("   * python main.py startServer [options]")
    print("   Options:")
    print("       -h, --host: Host to listen on (default:127.0.0.1)")
    print("       -p, --port: Port to listen on (default:8080)")
    print("       --cert: SSL certificate file")
    print("       --key: SSL key file")
    print("       --dev: Development mode (default: False)")
    print("   * python main.py help - Show this help message")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        helpMessage()
        sys.exit(1)
    if sys.argv[1] == "startServer":
        port = 8080
        host = "127.0.0.1"
        cert = None
        key = None
        development = False
        try:
            opts, args = getopt.getopt(sys.argv[2:], "h:p:", ["host=", "port=", "cert=", "key=", "dev"])
        except getopt.GetoptError as err:
            print(str(err))
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-h", "--host"):
                host = arg
            elif opt in ("-p", "--port"):
                port = int(arg)
            elif opt == "--cert":
                cert = arg
            elif opt == "--key":
                key = arg
            elif opt == "--dev":
                development = True
        server = Server(port=port, host=host, cert_file=cert, key_file=key, development=development)
        server.start()
    elif sys.argv[1] == "help":
        helpMessage()

