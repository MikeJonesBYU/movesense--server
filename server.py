#!/usr/bin/env python3

from argparse import ArgumentParser
from http.server import HTTPServer

from settings import *
from handlers.test import TestHandler

def stop(server):
    print('\nShutting down the server...')
    server.socket.close()

def start(port=PORT):
    try:
        # Create a web server and define the handler to manage the request
        server = HTTPServer(('', port), TestHandler)
        print('Start server on port {}'.format(port))

        # Serve until told to stop
        server.serve_forever()

    except KeyboardInterrupt:
        stop(server)


if __name__ == '__main__':
    parser = ArgumentParser(description='Process server settings')
    parser.add_argument('-p', '--port', type=int,
                        required=False, help='Server port number')
    args = parser.parse_args()

    if args.port:
        start(args.port)
    else:
        start()
