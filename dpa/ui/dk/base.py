
# -----------------------------------------------------------------------------

from PySide import QtCore, QtGui

from dpa.ui.app.session import SessionDialog
from dpa.ui.icon.factory import IconFactory

# -----------------------------------------------------------------------------
class BaseDarkKnightDialog(SessionDialog):
    """Base class for application specific Dark Knight implementations.
    
    Why "Dark Knight"? The old queue submission tool was called "Batman". 
    This is the new, improved reboot version.
    
    """

    _icon_path = IconFactory().disk_path("icon:///images/icons/dk_64x64.png")
    _logo_path = IconFactory().disk_path("icon:///images/logos/dk_logo.png")
    _logo_full_path = IconFactory().disk_path("icon:///images/logos/dk_full.png")
    _dir_path = IconFactory().disk_path("icon:///images/icons/dir_32x32.png")

    # -------------------------------------------------------------------------
    def __init__(self, parent=None):

        super(BaseDarkKnightDialog, self).__init__(parent=parent)

        cls = self.__class__

        self.setWindowTitle("TDK")
        self.setWindowIcon(QtGui.QIcon(cls._icon_path))

        self.main_layout = QtGui.QVBoxLayout(self)
        self.main_layout.setSpacing(4)
        self.main_layout.setContentsMargins(4, 4, 4, 4)

        # ---- logo image

        logo_btn = QtGui.QPushButton()
        logo_btn.setCheckable(True)
        logo_btn.setFlat(True)
        logo_full = QtGui.QPixmap(cls._logo_full_path)
        logo = QtGui.QPixmap(cls._logo_path)

        def _display_logo(checked):
            if checked: 
                logo_btn.setFixedSize(logo_full.size())
                logo_btn.setIcon(QtGui.QIcon(logo_full))
                logo_btn.setIconSize(logo_full.size())
            else:
                logo_btn.setFixedSize(logo.size())
                logo_btn.setIcon(QtGui.QIcon(logo))
                logo_btn.setIconSize(logo.size())
                
        _display_logo(logo_btn.isChecked())
        logo_btn.toggled.connect(_display_logo)

        logo_layout = QtGui.QHBoxLayout()
        logo_layout.addStretch()
        logo_layout.addWidget(logo_btn)
        logo_layout.addStretch()
        
        self.main_layout.addLayout(logo_layout)
        self.main_layout.setStretchFactor(logo_btn, 0)

    # -------------------------------------------------------------------------
    def _separator(self):

        sep = QtGui.QFrame()
        sep.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Plain)

        return sep

