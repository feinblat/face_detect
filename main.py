import logging
from optparse import OptionParser
import sys

from aiohttp import web

from web_server import BestSmileWebServer


def main(base_path: str, local_ip: str,  port: int, auth_key: str, debug: bool):
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG if debug else logging.INFO)
    web_server = BestSmileWebServer(api_key=auth_key, base_path=base_path)
    web.run_app(web_server.app, host=local_ip, port=port)


def cli_main():
    parser = OptionParser()
    parser.add_option("-b", "--base-path", dest="base_path",
                      help="images file dir")
    parser.add_option("-p", "--port", dest="port",  type="int", default=8080,
                      help="server port (default 8080)")
    parser.add_option("-l", "--local-ip", dest="local_ip", default='127.0.0.1',
                      help="server ip")
    parser.add_option("-k", "--key", dest="key",
                      help="azure auth key")
    parser.add_option("-d", "--debug", dest="debug",
                      action='store_true',
                      help="allow debug prints")
    opts, args = parser.parse_args()

    if not opts.base_path or not opts.key:
        print('Invalid Usage', file=sys.stderr)
        parser.print_help()
        exit(1)
    main(opts.base_path, opts.local_ip, opts.port, opts.key, opts.debug)


if __name__ == '__main__':
    cli_main()
