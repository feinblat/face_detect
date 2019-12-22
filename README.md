# Usage

Usage: main.py [options]

Options:
  -h, --help            show this help message and exit
  -b BASE_PATH, --base-path=BASE_PATH
                        images file dir
  -p PORT, --port=PORT  server port (default 8080)
  -l LOCAL_IP, --local-ip=LOCAL_IP
                        server ip
  -k KEY, --key=KEY     azure auth key
  -d, --debug           allow debug prints

# API
POST /
expected content-type header is application/json
and the body has to contain a list of paths (relative to the base-path parameter)
