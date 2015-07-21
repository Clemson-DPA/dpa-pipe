
import os

from PySide import QtCore, QtGui

from dpa.app.session import Session, SessionRegistry, SessionError

# -----------------------------------------------------------------------------

try:
    import nuke
except ImportError:
    NUKE_IMPORTED = False
    NUKE_HAS_UI = False
else:
    NUKE_IMPORTED = True
    NUKE_HAS_UI = nuke.GUI

# -----------------------------------------------------------------------------
class NukeSession(Session):

    app_name = 'nuke'
    
    # -------------------------------------------------------------------------
    @classmethod
    def current(cls):
        if not NUKE_IMPORTED:
            return None
        return cls()

    # -------------------------------------------------------------------------
    def __init__(self, file_path=None):

        super(NukeSession, self).__init__()

        self._nuke = self.init_module('nuke')

        if file_path:
            self.open_file(file_path)

    # -------------------------------------------------------------------------
    def close(self):
        self.nuke.scriptExit()

    # -------------------------------------------------------------------------
    def open_file(self, file_path):
        
        if not os.path.exists(file_path):
            raise SessionError(
                "Can not open '{f}'. File does not exist.".format(f=file_path))

        self.nuke.scriptOpen(file_path)
        
    # -------------------------------------------------------------------------
    def save(self, file_path=None):

        self.nuke.scriptSave(file_path)

    # -------------------------------------------------------------------------
    @property
    def nuke(self):
        return self._nuke

    # -------------------------------------------------------------------------
    @property
    def in_session(self):
        return NUKE_IMPORTED
    
    # -------------------------------------------------------------------------
    @property
    def main_window(self):

        if not NUKE_HAS_UI:
            return None

        return QtGui.QApplication.activeWindow()

    # -------------------------------------------------------------------------
    @property
    def name(self):
        return self.__class__.app_name

# -----------------------------------------------------------------------------
SessionRegistry().register(NukeSession)

