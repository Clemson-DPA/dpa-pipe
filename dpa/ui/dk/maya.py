
# -----------------------------------------------------------------------------

from PySide import QtCore, QtGui

from .base import BaseDarkKnightDialog

# -----------------------------------------------------------------------------
class MayaDarkKnightDialog(BaseDarkKnightDialog):

    # -------------------------------------------------------------------------
    def _setup_controls(self):

        controls_layout = QtGui.QGridLayout()
        

        # XXX file format (only exr for now)
        # XXX resolution - make standard...
        
        
        # XXX separate render layers
        # XXX renderer list
        # XXX start, end, step
        # XXX manual frame range
        # XXX generate rib files
        # XXX remove existing ribs
        # XXX queue or local
        # XXX queue name
        # XXX submit button


        controls_widget = QtGui.QWidget()
        controls_widget.setLayout(controls_layout)
        
        return controls_widget 

    # -------------------------------------------------------------------------
    def _submit(self):

        print "SUBMIT!"
