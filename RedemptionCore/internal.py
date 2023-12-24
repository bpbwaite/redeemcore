from threading import Thread
from pathlib import Path
from functools import partial
from itertools import chain
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from socket import gethostname
from typing import Any

from .settings import logger

class loggingServer(SimpleHTTPRequestHandler):
    cct = str.maketrans(
            {c: fr'\x{c:02x}' for c in chain(range(0x20), range(0x7f,0xa0))})
    # redefinition of control table
    # sometimes python can't find the attribute of a super-super class
    def log_message(self, format: str, *args: Any) -> None:
        logger.debug('Serving %s : %s' %
                    (self.address_string(),
                    (format % args).translate(self.cct)))

def serve(directory: Path, port: int = 3001):
    try:
        host_name = gethostname().strip().lower()
        backslash = '\\'
        if host_name and port:
            logger.info(f'Serving {directory.replace(backslash, "/")} on http://{host_name}:{port}')
            handler = partial(loggingServer, directory=directory)
            httpd = TCPServer(("", port), handler) # localhost

            thread = Thread(target=httpd.serve_forever)
            thread.daemon = True
            thread.start()
    except:
        logger.error('Internal server error')
