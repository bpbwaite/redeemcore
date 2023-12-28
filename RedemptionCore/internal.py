import json
import contextlib
from threading import Thread
from pathlib import Path
from functools import partial
from itertools import chain
from http.server import SimpleHTTPRequestHandler, HTTPServer
from http import HTTPStatus
from typing import Any
from socket import gethostname
from urllib.parse import urlparse

from .settings import logger, actionFile

class RequestServer(SimpleHTTPRequestHandler):
    # todo: wrap try-except blocks
    cct = str.maketrans(
            {c: fr'\x{c:02x}' for c in chain(range(0x20), range(0x7f,0xa0))})
    # redefinition of control table
    # sometimes python can't find the attribute of a super-super-super class

    def log_message(self, format: str, *args: Any) -> None:
        with contextlib.suppress(Exception):
            logger.debug('Serving %s : %s' %
                        (self.address_string(),
                        (format % args).translate(self.cct)))

    def do_GET(self) -> None:
        with contextlib.suppress(Exception):
            f = ''
            if urlparse(self.path).path == '/actions':
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type','application/json')
                self.end_headers()
                f = open(actionFile, 'rb')

            else:
                f = self.send_head()

            if f:
                try:
                    self.copyfile(f, self.wfile)
                finally:
                    f.close()

    def do_POST(self):
        with contextlib.suppress(Exception):
            self.send_response(200)
            self.end_headers()
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()

            # verify somewhat valid json
            if 'actions' in json.loads(post_data):
                with open(actionFile, 'wt') as F:
                    F.write(post_data)

def serve(directory: str, port: int = 3001):
    try:
        host_name = gethostname().strip().lower()
        directory = Path(directory).as_posix()
        if host_name and port:
            logger.info(f'Serving {directory} on http://{host_name}:{port}')
            handler = partial(RequestServer, directory=directory)
            httpd = HTTPServer(("", port), handler) # localhost
            thread = Thread(target=httpd.serve_forever)
            thread.daemon = True
            thread.start()
    except:
        logger.error('Internal server error')
