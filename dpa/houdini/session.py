
import os
import time

# attempt to import hou module. if it fails, not in a houdini session.
try: 
    import hou
except ImportError:
    HOU_IMPORTED = False
else:
    HOU_IMPORTED = True

from dpa.app.session import RemoteMixin, Session, SessionError

# -----------------------------------------------------------------------------
class HoudiniSession(RemoteMixin, Session):

    # XXX should come from config
    SERVER_EXECUTABLE = "/home/jtomlin/dev/dpa-pipe/bin/dpa_houdini_server"

    # -------------------------------------------------------------------------
    def __init__(self, filepath=None, remote=False):

        self._hou = self.init_module('hou', remote)

        if filepath:
            self.open_file(filepath)

    # -------------------------------------------------------------------------
    def close(self):
        if self.remote_connection:
            self.shutdown() 
        else:
            self.hou.hipFile.clear()

    # -------------------------------------------------------------------------
    def open_file(self, filepath):

        if not os.path.exists(filepath):
            raise SessionError(
                "Can not open '{f}'. File does not exist.".format(f=filepath))

        try:
            self.hou.hipFile.load(filepath)
        except RuntimeError as e:
            raise SessionError(str(e))

    # -------------------------------------------------------------------------
    def save(self, filepath=None, overwrite=False):

        if filepath and os.path.exists(filepath) and not overwrite:
            raise SessionError(
                "Can not save '{f}'. File exists.".format(f=filepath))

        self.hou.hipFile.save(file_name=filepath)

    # -------------------------------------------------------------------------
    @property
    def hou(self):
        return self._hou
        
    # -------------------------------------------------------------------------
    @property
    def in_session(self):
        """Returns True if inside a current app session."""
        return HOU_IMPORTED or self.remote_connection

    # -------------------------------------------------------------------------
    @property
    def name(self):
        """Returns the name of the application."""
        return "houdini"

    # -------------------------------------------------------------------------
    @property
    def server_executable(self):
        return self.__class__.SERVER_EXECUTABLE

