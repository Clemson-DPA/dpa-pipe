
import os
import time

# -----------------------------------------------------------------------------
# attempt to import maya commands module. if it fails, not in a maya session.
try: 
    import maya.cmds as cmds
except ImportError:
    MAYA_CMDS_IMPORTED = False
else:
    MAYA_CMDS_IMPORTED = True

# -----------------------------------------------------------------------------
# attempt to import maya ui module. if it fails, not in the UI
try:
    from PySide import QtCore, QtGui
    from maya import OpenMayaUI as omui
    from shiboken import wrapInstance
except:
    MAYA_UI_IMPORTED = False
else:
    MAYA_UI_IMPORTED = True

# -----------------------------------------------------------------------------

from dpa.app.session import RemoteMixin, Session, SessionRegistry, SessionError

# -----------------------------------------------------------------------------
class MayaSession(RemoteMixin, Session):

    app_name = 'maya'

    # XXX should come from config
    SERVER_EXECUTABLE = "/home/jtomlin/dev/dpa-pipe/bin/dpa_maya_server"

    # -------------------------------------------------------------------------
    @classmethod
    def current(cls):
        if not MAYA_CMDS_IMPORTED:
            return None
        return cls()

    # -------------------------------------------------------------------------
    def __init__(self, file_path=None, remote=False):

        super(MayaSession, self).__init__(remote=remote)

        self._cmds = self.init_module('maya.cmds')
        self._mel = self.init_module('maya.mel')

        if file_path:
            self.open_file(file_path)

    # -------------------------------------------------------------------------
    def close(self):
        if self.remote_connection:
            self.shutdown() 
        else:
            self.cmds.file(newFile=True)

    # -------------------------------------------------------------------------
    def open_file(self, file_path):

        if not os.path.exists(file_path):
            raise SessionError(
                "Can not open '{f}'. File does not exist.".format(f=file_path))

        try:
            self.cmds.file(file_path, o=True)
        except RuntimeError as e:
            raise SessionError(str(e))

    # -------------------------------------------------------------------------
    def require_plugin(self, plugin_name):
        
        # ensure abc plugin in is loaded
        if not self.cmds.pluginInfo(
            plugin_name, query=True, loaded=True):

            # load the plugin
            self.cmds.loadPlugin(plugin_name)
            if not self.cmds.pluginInfo(
                plugin_name, query=True, loaded=True):
                raise SessionError("Unable to load plugin: " + plugin_name)

    # -------------------------------------------------------------------------
    def save(self, file_path=None, bake_references=False, overwrite=False):

        if bake_references:
            refs = self.cmds.ls(type='reference')
            for ref in refs:
                ref_file = self.cmds.referenceQuery(ref, f=True)
                self.cmds.file(ref_file, importReference=True)

        if file_path:
            if os.path.exists(file_path) and not overwrite:
                raise SessionError(
                    "Can not save '{f}'. File exists.".format(f=file_path))
            cur_path = self.file_path
            self.cmds.file(rename=file_path)
            self.cmds.file(save=True)
            self.cmds.file(rename=cur_path)
        else:
            self.cmds.file(save=True)

    # -------------------------------------------------------------------------
    def selected(self, selection_list, dependencies=False):
        return SelectionContext(self, selection_list, dependencies=dependencies)

    # -------------------------------------------------------------------------
    @property
    def cmds(self):
        return self._cmds
        
    # -------------------------------------------------------------------------
    @property
    def file_path(self):
        return self.cmds.file(q=True, sceneName=True)

    # -------------------------------------------------------------------------
    @property
    def in_session(self):
        """Returns True if inside a current app session."""
        return MAYA_CMDS_IMPORTED or hasattr(self, 'remote_connection')

    # -------------------------------------------------------------------------
    @property
    def main_window(self):
        """Returns the Qt main window used to parent dialogs/widgets."""

        if not MAYA_UI_IMPORTED:
            return None

        if not hasattr(self, '_main_window'):
            self._main_window = wrapInstance(
                long(omui.MQtUtil.mainWindow()), QtGui.QWidget) 

        return self._main_window

    # -------------------------------------------------------------------------
    @property
    def mel(self):
        return self._mel
        
    # -------------------------------------------------------------------------
    @property
    def server_executable(self):
        return self.__class__.SERVER_EXECUTABLE

# -----------------------------------------------------------------------------
class SelectionContext(object):

    def __init__(self, session, selection_list, dependencies=False):
        self._session = session
        self._selection_list = selection_list
        self._dependencies = dependencies

    # ------------------------------------------------------------------------
    def __enter__(self):
        
        # store current selection state
        self._saved_selection = self._session.cmds.ls(selection=True) 

        # select selection list
        self._session.cmds.select(self._selection_list, replace=True,
            allDependencyNodes=self._dependencies)
        
    # ------------------------------------------------------------------------
    def __exit__(self, exc_type, exc_value, traceback):

        # restore selection list
        if self._saved_selection:
            self._session.cmds.select(self._saved_selection, replace=True)

        return False

# -----------------------------------------------------------------------------
SessionRegistry().register(MayaSession)

