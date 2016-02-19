"""
This module helps you use PyQt in Houdini's GUI by integrating PyQt's event
loop into Houdini's.  Replace calls to QApplication.exec_() in your
code with calls to pyqt_houdini.exec_(app).
"""

from PySide import QtCore
from PySide import QtGui
import hou

class IntegratedEventLoop(object):
    """This class behaves like QEventLoop except it allows PyQt to run inside
    Houdini's event loop on the main thread.  You probably just want to
    call exec_() below instead of using this class directly.
    """
    def __init__(self, application, dialogs):
        # We need the application to send posted events.  We hold a reference
        # to any dialogs to ensure that they don't get garbage collected
        # (and thus close in the process).  The reference count for this object
        # will go to zero when it removes itself from Houdini's event loop.
        self.application = application
        self.dialogs = dialogs
        self.event_loop = QtCore.QEventLoop()

    def exec_(self):
        hou.ui.addEventLoopCallback(self.processEvents)

    def processEvents(self):
        # There is no easy way to know when the event loop is done.  We can't
        # use QEventLoop.isRunning() because it always returns False since
        # we're not inside QEventLoop.exec_().  We can't rely on a
        # lastWindowClosed signal because the window is usually made invisible
        # instead of closed.  Instead, we need to explicitly check if any top
        # level widgets are still visible.
        if not anyQtWindowsAreOpen():
            hou.ui.removeEventLoopCallback(self.processEvents)

        self.event_loop.processEvents()
        self.application.sendPostedEvents(None, 0)

def anyQtWindowsAreOpen():
    return any(w.isVisible() for w in QtGui.QApplication.topLevelWidgets())

def exec_(application, *args):
    """You cannot call QApplication.exec_, or Houdini will freeze while PyQt
    waits for and processes events.  Instead, call this function to allow
    Houdini's and PyQt's event loops to coexist.  Pass in any dialogs as
    extra arguments, if you want to ensure that something holds a reference
    to them while the event loop runs.

    This function returns right away.
    """
    IntegratedEventLoop(application, args).exec_()

def execSynchronously(application, *args):
    """This function is like exec_, except it will not return until all PyQt
    windows have closed.  Houdini will remain responsive while the PyQt window
    is open.
    """
    exec_(application, *args)
    hou.ui.waitUntil(lambda: not anyQtWindowsAreOpen())

