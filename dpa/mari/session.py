
import os
import time

# -----------------------------------------------------------------------------
# attempt to import mari module. if it fails, not in a mari session.
try: 
    import mari
except ImportError:
    MARI_IMPORTED = False
else:
    MARI_IMPORTED = True

# -----------------------------------------------------------------------------
# attempt to import maya ui module. if it fails, not in the UI
try:
    from PySide import QtCore, QtGui
except:
    MARI_UI_IMPORTED = False
else:
    MARI_UI_IMPORTED = True

# -----------------------------------------------------------------------------

from dpa.app.session import RemoteMixin, Session, SessionRegistry, SessionError

# -----------------------------------------------------------------------------
class MariSession(RemoteMixin, Session):

    app_name = 'mari'

    # XXX should come from config
    SERVER_EXECUTABLE = "/home/gguerre/pipedev/dpa-pipe/bin/dpa_mari_server"

    # -------------------------------------------------------------------------
    @classmethod
    def current(cls):
        if not MARI_IMPORTED:
            return None
        return cls()

    # -------------------------------------------------------------------------
    def __init__(self, file_path=None, remote=False):

        super(MariSession, self).__init__(remote=remote)

        self._mari = self.init_module('mari')

        if file_path:
            self.open_file(file_path)

    # -------------------------------------------------------------------------
    def close(self, confirm_dialog=False):
        if self.remote_connection:
            self.shutdown() 
        else:
            self.mari.app.quit(confirm_dialog)

    # -------------------------------------------------------------------------
    def open_file(self, file_path):

        if not os.path.exists(file_path):
            raise SessionError(
                "Can not open '{f}'. File does not exist.".format(f=file_path))

        try:
            project = self.mari.projects.extract(file_path)
            self.mari.projects.open(project.uuid())
        except RuntimeError as e:
            raise SessionError(str(e))

    # -------------------------------------------------------------------------
    def save(self, file_path=None, archive=True, overwrite=False):

        # check to see if there's a project open?
        # otherwise don't do anything else...?
        project = self.mari.projects.current()
        uuid = project.uuid()
        
        if project: 
            if archive:

                project_name = project.name()
                project.save(force_save=True)
                project.close(confirm_if_modified=False)

                if file_path:
                    if os.path.exists(file_path) and not overwrite:
                        raise SessionError(
                            "Cannot save '{f}'. File exists.".format(f=file_path))
                else:
                    # make sure the mari directory exists
                    self.ptask_area.provision('mari')
                    
                    # build a path to the file
                    file_path = os.path.join(
                        self.ptask_area.dir(dir_name='mari'),
                        project_name + '.mra'
                    )

                self.mari.projects.archive(uuid, file_path)

                if file_path:
                    os.chmod(file_path, 0770)
            else:
                project.save(force_save=True)
        else:
            raise SessionError("No opened Mari project to save/archive.")

    # -------------------------------------------------------------------------
    @property
    def mari(self):
        return self._mari

    # -------------------------------------------------------------------------
    @property
    def in_session(self):
        """Returns True if inside a current app session."""
        return MARI_IMPORTED or self.remote_connection

    # -------------------------------------------------------------------------
    @property
    def main_window(self):
        """Returns the Qt main window used to parent dialogs/widgets."""

        if not MARI_UI_IMPORTED:
            return None

        if not hasattr(self, '_main_window'):
            self._main_window = QtGui.QWidget()

        return self._main_window

    # -------------------------------------------------------------------------
    @property
    def name(self):
        """Returns the name of the application."""
        return "mari"

    # -------------------------------------------------------------------------
    @property
    def server_executable(self):
        return self.__class__.SERVER_EXECUTABLE

# -----------------------------------------------------------------------------
SessionRegistry().register(MariSession)
