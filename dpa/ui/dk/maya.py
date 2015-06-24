
# -----------------------------------------------------------------------------

from PySide import QtCore, QtGui

from .base import BaseDarkKnightDialog

# -----------------------------------------------------------------------------
class MayaDarkKnightDialog(BaseDarkKnightDialog):

    # -------------------------------------------------------------------------
    def _setup_controls(self):

        layout = QtGui.QGridLayout()
        
        
        
        # XXX info about ptask, version, etc.
        # XXX separate render layers
        # XXX file format (only exr for now)
        # XXX resolution - make standard...
        # XXX renderer list
        # XXX start, end, step
        # XXX manual frame range
        # XXX generate rib files
        # XXX remove existing ribs
        # XXX queue or local
        # XXX queue name
        # XXX submit button

        return layout

    # -------------------------------------------------------------------------
    def _submit(self):

        print "SUBMIT!"
