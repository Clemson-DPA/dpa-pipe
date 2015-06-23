
# -----------------------------------------------------------------------------

from PySide import QtCore, QtGui

from dpa.ui.app.session import SessionDialog
from dpa.ui.icon.factory import IconFactory

# -----------------------------------------------------------------------------
class DarkKnightDialog(SessionDialog):

    # -------------------------------------------------------------------------
    def __init__(self, parent=None):

        super(DarkKnightDialog, self).__init__(parent=parent)

        self.setWindowTitle("TDK")

        icon_lbl = QtGui.QLabel()
        icon_lbl.setPixmap(QtGui.QPixmap(
            IconFactory().disk_path("icon:///images/logos/dk.png")))

        test_btn = QtGui.QPushButton("TEST")

        main_layout = QtGui.QGridLayout(self)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.addWidget(icon_lbl, 0, 0, 1, 2,
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        main_layout.addWidget(test_btn, 1, 0, 1, 2)

        # XXX dark knight logo here...

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

