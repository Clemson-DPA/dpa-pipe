
import sys
import time

from dpa.app.server import AppServer
from dpa.cli.action import CommandLineAction

# ------------------------------------------------------------------------------
class ClApp(CommandLineAction):

    name = "clapp"

    # --------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        parser.add_argument(
            "port",
            type=int,
            help="Port number to serve."
        )

    # --------------------------------------------------------------------------
    def __init__(self, port):

        super(ClApp, self).__init__(port)

        self._port = port
        self._server = None
        self._shutdown = False

    # --------------------------------------------------------------------------
    def execute(self):

        self._server = AppServer(
            self.port, 
            shutdown_callback=self._shutdown_server,
        )
        self._server.start()

        while not self._shutdown:
            time.sleep(1)

        sys.exit(0)

    # --------------------------------------------------------------------------
    def undo(self):
        pass

    # --------------------------------------------------------------------------
    @property
    def port(self):
        return self._port

    # --------------------------------------------------------------------------
    @property
    def server(self):
        return self._server

    # --------------------------------------------------------------------------
    def _shutdown_server(self):
        
        self._shutdown = True

