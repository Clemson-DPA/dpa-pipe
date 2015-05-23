
import os
import time

# attempt to import mari module. if it fails, not in a mari session.
try: 
    import mari
except ImportError:
    MARI_IMPORTED = False
else:
    MARI_IMPORTED = True

# -----------------------------------------------------------------------------

from dpa.app.session import RemoteMixin, Session, SessionRegistry, SessionError

# -----------------------------------------------------------------------------
class MariSession(RemoteMixin, Session):

    # XXX should come from config
    SERVER_EXECUTABLE = "/home/gguerre/pipedev/dpa-pipe/bin/dpa_mari_server"

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
    	
    	if project: 
    		if archive:
    			if file_path:
    				if os.path.exists(file_path) and not overwrite:
	    				raise SessionError(
	    					"Cannot save '{f}'. File exists.".format(f=file_path))
    			
	    			project.save(force_save=True)
	    			project.close(confirm_if_modified=False)
	    			self.mari.projects.archive(project.uuid(),file_path)
	    		else:
	    			raise SessionError("Cannot archive without a filepath.")
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
    def name(self):
        """Returns the name of the application."""
        return "mari"

    # -------------------------------------------------------------------------
    @property
    def server_executable(self):
        return self.__class__.SERVER_EXECUTABLE

# -----------------------------------------------------------------------------
SessionRegistry().register(MariSession)