
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

    _icon_path = IconFactory().disk_path("icon:///images/icons/dk_icon.png")
    _logo_path = IconFactory().disk_path("icon:///images/logos/dk_logo.png")
    _logo_full_path = IconFactory().disk_path("icon:///images/logos/dk_full.png")

    # -------------------------------------------------------------------------
    def __init__(self, parent=None):

        super(BaseDarkKnightDialog, self).__init__(parent=parent)

        cls = self.__class__

        self.setWindowTitle("TDK")
        self.setWindowIcon(QtGui.QIcon(cls._icon_path))

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
        
        controls_layout = self._setup_controls()

        submit_btn = QtGui.QPushButton("Submit")
        submit_btn.clicked.connect(self._submit)
        
        main_layout = QtGui.QVBoxLayout(self)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.addWidget(logo_btn)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self._separator())
        main_layout.addWidget(submit_btn)
        main_layout.addStretch()

    # -------------------------------------------------------------------------
    def _separator(self):

        sep = QtGui.QFrame()
        sep.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Plain)

        return sep

    # -------------------------------------------------------------------------
    def _setup_controls(self):
        """Add UI controls here. Return a layout that can be added to DK."""
        pass

    # -------------------------------------------------------------------------
    def _submit(self):
        """Called when 'Submit' button clicked. Business logic here."""
        pass

