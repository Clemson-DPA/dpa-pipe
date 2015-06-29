
# -----------------------------------------------------------------------------

import os

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
        
        controls_widget = self._setup_controls()
        scroll_area = None

        if controls_widget:
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
        main_layout.setStretchFactor(logo_btn, 0)

        output_options = self._output_options()
        if output_options:
            main_layout.addLayout(output_options)
            main_layout.setStretchFactor(output_options, 0)

        if scroll_area:
            main_layout.addWidget(scroll_area)
            main_layout.setStretchFactor(scroll_area, 1000)

        main_layout.addWidget(submit_btn)
        main_layout.setStretchFactor(submit_btn, 0)

    # -------------------------------------------------------------------------
    def _output_options(self):

        output_type_lbl = QtGui.QLabel("Output:")
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
        ptask_edit = QtGui.QLineEdit(str(cur_ptask))
        ptask_edit.setReadOnly(True)

        version_lbl = QtGui.QLabel("Version:")
        version_num = QtGui.QLabel("<B>" + str(version) + "</B>")

        auto_layout = QtGui.QGridLayout()
        auto_layout.setSpacing(4)
        auto_layout.setContentsMargins(4, 4, 4, 4)
        auto_layout.addWidget(ptask_lbl, 0, 0, QtCore.Qt.AlignRight)
        auto_layout.addWidget(ptask_edit, 0, 1)
        auto_layout.addWidget(version_lbl, 1, 0, QtCore.Qt.AlignRight)
        auto_layout.addWidget(version_num, 1, 1, QtCore.Qt.AlignLeft)
        auto_layout.setColumnStretch(0, 0)
        auto_layout.setColumnStretch(1, 1000)

        auto_widgets = QtGui.QWidget()
        auto_widgets.setLayout(auto_layout)

        # ---- manual

        dir_lbl = QtGui.QLabel("Directory:")
        dir_edit = QtGui.QLineEdit(os.getcwd())

        dir_btn = QtGui.QPushButton()
        dir_btn.setFlat(True)
        dir_btn_size = QtCore.QSize(22, 22)
        dir_btn.setFixedSize(dir_btn_size)
        dir_btn.setIcon(QtGui.QIcon(self.__class__._dir_path))
        dir_btn.setIconSize(dir_btn_size)

        dir_dialog = QtGui.QFileDialog(self, 'Output directory', 
            os.getcwd())
        dir_dialog.setFileMode(QtGui.QFileDialog.Directory)
        dir_dialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
        dir_dialog.setOption(QtGui.QFileDialog.DontResolveSymlinks, True)
        dir_dialog.setOption(QtGui.QFileDialog.HideNameFilterDetails, True)
        dir_dialog.fileSelected.connect(dir_edit.setText)

        dir_btn.clicked.connect(dir_dialog.show)

        manual_layout = QtGui.QGridLayout()
        manual_layout.setSpacing(4)
        manual_layout.setContentsMargins(4, 4, 4, 4)
        manual_layout.addWidget(dir_lbl, 0, 0, QtCore.Qt.AlignRight)
        manual_layout.addWidget(dir_edit, 0, 1)
        manual_layout.addWidget(dir_btn, 0, 2)
        manual_layout.setColumnStretch(0, 0)
        manual_layout.setColumnStretch(1, 1000)
        manual_layout.setColumnStretch(2, 0)

        manual_widgets = QtGui.QWidget()
        manual_widgets.setLayout(manual_layout)

        output_stack = QtGui.QStackedWidget()
        output_stack.addWidget(auto_widgets)
        output_stack.addWidget(manual_widgets)

        output_type.activated.connect(output_stack.setCurrentIndex)

        # ---- layout

        output_layout = QtGui.QVBoxLayout()
        output_layout.setSpacing(4)
        output_layout.setContentsMargins(4, 4, 4, 4)
        output_layout.addLayout(header_layout)
        output_layout.addWidget(output_stack)
        #output_layout.addWidget(file_type)

        return output_layout 

    # -------------------------------------------------------------------------
    @property
    def output_file_types(self):
        """Returns a list of output file types."""
        return ["exr"]

    # -------------------------------------------------------------------------
    def _separator(self):

        sep = QtGui.QFrame()
        sep.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Plain)

        return sep

    # -------------------------------------------------------------------------
    def _setup_controls(self):
        """Add UI controls here. Return a widget that can be added to DK."""
        pass

    # -------------------------------------------------------------------------
    def _submit(self):
        """Called when 'Submit' button clicked. Business logic here."""
        pass

