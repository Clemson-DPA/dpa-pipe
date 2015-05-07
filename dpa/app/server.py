
import socket

import rpyc
from rpyc.core.service import SlaveService
from rpyc.utils.server import ThreadedServer
from rpyc.utils.registry import REGISTRY_PORT, UDPRegistryClient

# -----------------------------------------------------------------------------
class AppService(SlaveService):

    # -------------------------------------------------------------------------
    def exposed_shutdown(self):
        
        if self.server:
            self.server.close()

        if self.shutdown_callback:
            self.shutdown_callback()

    # -------------------------------------------------------------------------
    @property
    def shutdown_callback(self, callback):

        if not hasattr(self, '_shutdown_callback'):
            self._shutdown_callback = None

        return self._shutdown_callback

    # -------------------------------------------------------------------------
    @shutdown_callback.setter
    def server(self, callback):
        self._shutdown_callback = callback

    # -------------------------------------------------------------------------
    @property
    def server(self):
        
        if not hasattr(self, '_server'):
            self._server = None

        return self._server

    # -------------------------------------------------------------------------
    @server.setter
    def server(self, server):
        self._server = server

# -----------------------------------------------------------------------------
class AppServer(ThreadedServer):

    # -------------------------------------------------------------------------
    def __init__(self, port=0, shutdown_callback=None):

        super(AppServer, self).__init__(
            AppService,
            port=port,
            registrar=UDPRegistryClient(
                ip="255.255.255.255", 
                port=REGISTRY_PORT
            ),
            auto_register=False,
        )

        # give the service a handle to the server for closing
        self.service.server = self
        self.service.shutdown_callback = shutdown_callback
        
