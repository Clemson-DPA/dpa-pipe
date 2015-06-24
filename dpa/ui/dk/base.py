
# -----------------------------------------------------------------------------

from PySide import QtCore, QtGui

from dpa.ptask.area import PTaskArea
from dpa.ptask import PTask
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

        controls_widget = QtGui.QWidget()
        controls_widget.setLayout(controls_layout)

        scroll_area = QtGui.QScrollArea()
        scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(controls_widget)

        submit_btn = QtGui.QPushButton("Submit")
        submit_btn.clicked.connect(self._submit)
        
        main_layout = QtGui.QVBoxLayout(self)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.addWidget(logo_btn)
        main_layout.addLayout(self._output_options())
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(submit_btn)

    # -------------------------------------------------------------------------
    def _output_options(self):

        output_type_lbl = QtGui.QLabel("Output location:")
        output_type = QtGui.QComboBox()
        output_type.addItems(['Automatic', 'Manual'])

        header_layout = QtGui.QHBoxLayout()
        header_layout.setSpacing(4)
        header_layout.setContentsMargins(4, 4, 4, 4)
        header_layout.addStretch()
        header_layout.addWidget(output_type_lbl)
        header_layout.addWidget(output_type)
        header_layout.addStretch()

        # ---- auto

        cur_area = PTaskArea.current()
        cur_ptask = PTask.get(cur_area.spec)
        if cur_ptask:
            version = cur_area.version or cur_ptask.latest_version.number
        else:
            cur_ptask = None
            version = "None"

        ptask_lbl = QtGui.QLabel("PTask:")
        ptask = QtGui.QLabel("<B>" + str(cur_ptask) + "</B>")

        version_lbl = QtGui.QLabel("Version:")
        version = QtGui.QLabel("<B>" + str(version) + "</B>")


        auto_layout = QtGui.QGridLayout()
        auto_layout.setSpacing(4)
        auto_layout.setContentsMargins(4, 4, 4, 4)
        auto_layout.addWidget(ptask_lbl, 0, 0, QtCore.Qt.AlignRight)
        auto_layout.addWidget(ptask, 0, 1, QtCore.Qt.AlignLeft)
        auto_layout.addWidget(version_lbl, 1, 0, QtCore.Qt.AlignRight)
        auto_layout.addWidget(version, 1, 1, QtCore.Qt.AlignLeft)
        auto_layout.setColumnStretch(0, 0)
        auto_layout.setColumnStretch(1, 1000)

        auto_widgets = QtGui.QWidget()
        auto_widgets.setLayout(auto_layout)

        # version

        # ---- manual

        # directory

        # ---- layout

        output_layout = QtGui.QVBoxLayout()
        output_layout.setSpacing(4)
        output_layout.setContentsMargins(4, 4, 4, 4)
        output_layout.addLayout(header_layout)
        output_layout.addLayout(auto_layout)

        return output_layout 


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

