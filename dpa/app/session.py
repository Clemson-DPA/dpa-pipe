
from abc import ABCMeta, abstractmethod, abstractproperty
import importlib
import shlex
import subprocess
import socket
import time

import rpyc

from dpa.app.entity import EntityRegistry
from dpa.ptask.area import PTaskArea
from dpa.ptask import PTaskError, PTask
from dpa.singleton import Singleton

# -----------------------------------------------------------------------------
class SessionRegistry(Singleton):

    # -------------------------------------------------------------------------
    def init(self):

        self._registry = {}

    # -------------------------------------------------------------------------
    def current(self):

        for registered_cls in self._registry.values():
            if registered_cls.current():
                return registered_cls()

        return None

    # -------------------------------------------------------------------------
    def register(self, cls):
        self._registry[cls.app_name] = cls
        
# -----------------------------------------------------------------------------
class Session(object):

    __metaclass__ = ABCMeta 

    app_name = None

    # -------------------------------------------------------------------------
    @classmethod
    def current(cls):
        return None

    # -------------------------------------------------------------------------
    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    @abstractmethod
    def close(self):
        """Close the current file."""

    # -------------------------------------------------------------------------
    def list_entities(self, categories=None):
        """List entities in the session.""" 

        entities = []
        entity_classes = EntityRegistry().get_entity_classes(
            self.__class__.app_name)
        for entity_class in entity_classes:
            entities.extend(entity_class.list(self))

        if categories:
            filtered = [e for e in entities if e.category in categories]
        else:
            filtered = entities

        return filtered

    # -------------------------------------------------------------------------
    @classmethod
    def open_file(self, filepath):
        """Open a new session with the supplied file."""

    # -------------------------------------------------------------------------
    @abstractmethod
    def save(self, filepath=None):
        """Save the current session. Save to the file path if provided."""

    # -------------------------------------------------------------------------
    @abstractproperty
    def in_session(self):
        """Returns True if inside a current app session."""

    # -------------------------------------------------------------------------
    def init_module(self, module_path):

        _module = None

        if self.in_session:
            try:
                _module = importlib.import_module(module_path)
            except ImportError:
                pass # will raise below

        if not _module:
            raise SessionError(
                "Failed to initialize session. " + \
                "'{mod}' module could not be imported.".format(mod=module_path)
            )

        return _module

    # -------------------------------------------------------------------------
    @property
    def app_name(self):
        return self.__class__.app_name

    # -------------------------------------------------------------------------
    @property
    def ptask_area(self):
        """Return the current ptask area for this session."""

        if not hasattr(self, '_ptask_area'):
            self._ptask_area = PTaskArea.current()

        return self._ptask_area

    # -------------------------------------------------------------------------
    @property
    def ptask(self):

        if not hasattr(self, '_ptask'):
            ptask_area = self.ptask_area
            if not ptask_area.spec:
                self._ptask = None
            else:
                try:
                    self._ptask = PTask.get(ptask_area.spec)
                except PTaskError as e:
                    raise SessionError("Unable to determine ptask.")

        return self._ptask

    # -------------------------------------------------------------------------
    @property
    def ptask_version(self):
        """Return the current ptask version for this session."""

        if not hasattr(self, '_ptask_version'):

            ptask = self.ptask
            if not ptask:
                self._ptask_version = None
            else:
                self._ptask_version = ptask.latest_version

        return self._ptask_version

# -----------------------------------------------------------------------------
class RemoteMixin(object):

    __metaclass__ = ABCMeta 

    # -------------------------------------------------------------------------
    def __init__(self, remote=False):
        
        self._remote = remote

    # -------------------------------------------------------------------------
    def __del__(self):
        self.shutdown()

    # -------------------------------------------------------------------------
    def __enter__(self):
        return self
        
    # -------------------------------------------------------------------------
    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    # -------------------------------------------------------------------------
    @staticmethod
    def _get_port():

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("",0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    # -------------------------------------------------------------------------
    @property
    def remote(self):
        """Returns True if in a session, False otherwise."""
        return self._remote

    # -------------------------------------------------------------------------
    @property
    def remote_connection(self):

        if not hasattr(self, '_remote_connection'):
            self._remote_connection = self._connect_remote()

        return self._remote_connection

    # -------------------------------------------------------------------------
    @abstractproperty
    def server_executable(self):
        """The executable for starting the remote app server."""

    # -------------------------------------------------------------------------
    def shutdown(self):

        if hasattr(self, '_remote_connection'):
            try:
                self._remote_connection.root.shutdown()
            except EOFError:
                # this is the expected error on shutdown
                pass
            else:
                self._remote_connection = None

    # -------------------------------------------------------------------------
    def init_module(self, module_path):

        _module = None

        if self.remote:

            # need to give time for standalone app to import properly
            tries = 0
            while not _module or tries < 30:

                try:
                    self.remote_connection.execute("import " + module_path)
                    _module = getattr(
                        self.remote_connection.modules, module_path)
                    break
                except ImportError:
                    tries += 1
                    time.sleep(1)

            if not _module:
                self.shutdown()

        elif self.in_session:
            try:
                _module = importlib.import_module(module_path)
            except ImportError:
                pass # will raise below

        if not _module:
            raise SessionError(
                "Failed to initialize session. " + \
                "'{mod}' module could not be imported.".format(mod=module_path)
            )

        return _module

    # -------------------------------------------------------------------------
    def _connect_remote(self):

        port = self._get_port()
        
        cmd = "{cmd} {port}".format(cmd=self.server_executable, port=port)
        args = shlex.split(cmd)
        subprocess.Popen(args)

        connection = None

        tries = 0
        while not connection or tries < 30:

            try:
                connection = rpyc.classic.connect("localhost", port)
                break
            except socket.error:
                tries += 1
                time.sleep(1)

        if not connection:
            raise SessionError("Unable connect to remote session.")

        return connection

# -----------------------------------------------------------------------------
class SessionError(Exception):
    pass

