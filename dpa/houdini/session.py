
import os

from PySide import QtCore, QtGui

from dpa.app.session import Session, SessionRegistry, SessionError

# -----------------------------------------------------------------------------

try:
    import hou
except ImportError:
    HOU_IMPORTED = False
    HOU_HAS_UI = False
else:
    HOU_IMPORTED = True
    HOU_HAS_UI = hasattr(hou, 'ui')

# -----------------------------------------------------------------------------
class HoudiniSession(Session):

    app_name = 'houdini'

    # -------------------------------------------------------------------------
    @classmethod
    def current(cls):
        if not HOU_IMPORTED:
            return None
        return cls()

    # -------------------------------------------------------------------------
    def __init__(self, file_path=None):

        super(HoudiniSession, self).__init__()

        self._hou = self.init_module('hou')

        if file_path:
            self.open_file(file_path)

    # -------------------------------------------------------------------------
    def close(self):
        self.hou.exit()

    # -------------------------------------------------------------------------
    def open_file(self, file_path):
    
        if not os.path.exists(file_path):
            raise SessionError(
                "Can not open '{f}'. File does not exist.".format(f=file_path))

        self.hou.hipFile.load(file_path)

    # -------------------------------------------------------------------------
    def save(self, file_path=None):

        self.hou.hipFile.save(file_name=file_path)

    # -------------------------------------------------------------------------
    @property
    def hou(self):
        return self._hou
        
    # -------------------------------------------------------------------------
    @property
    def in_session(self):
        """Returns True if inside a current app session."""
        return HOU_IMPORTED

    # -------------------------------------------------------------------------
    @property
    def main_window(self):

        if not HOU_HAS_UI:
            return None

        return QtGui.QApplication.activeWindow()

    # -------------------------------------------------------------------------
    @property
    def name(self):
        """Returns the name of the application."""
        return self.__class__.app_name

# -----------------------------------------------------------------------------
SessionRegistry().register(HoudiniSession)

