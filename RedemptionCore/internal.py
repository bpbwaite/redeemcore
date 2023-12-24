from threading import Thread
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from socket import gethostname
from typing import Any

from .settings import logger

class loggingServer(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        logger.debug('Server to %s : %s' %
                    (self.address_string(),
                    (format % args).translate(self._control_char_table)))

def serve(directory: Path, port: int = 3001):
    try:
        host_name = gethostname().strip().lower()
        backslash = r'\\'
        if host_name and port:
            logger.info(f"Serving {directory.replace(backslash, '/')} on http://{host_name}:{port}")
            handler = partial(loggingServer, directory=directory)
            httpd = TCPServer(("", port), handler) # localhost

            thread = Thread(target=httpd.serve_forever)
            thread.daemon = True
            thread.start()
    except:
        logger.error('Internal server error')
