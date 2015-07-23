
# -----------------------------------------------------------------------------

from PySide import QtCore, QtGui

from dpa.frange import Frange, FrangeError
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
    def _make_frame_range_controls(self,
        min_time, max_time, start_time, end_time):

        self._frame_start = QtGui.QSpinBox()
        self._frame_start.setMinimum(min_time)
        self._frame_start.setMaximum(max_time)
        self._frame_start.setValue(int(start_time))
        self._frame_start.setFixedWidth(50)

        frame_to = QtGui.QLabel("to")

        self._frame_end = QtGui.QSpinBox()
        self._frame_end.setMinimum(min_time)
        self._frame_end.setMaximum(max_time)
        self._frame_end.setValue(int(end_time))
        self._frame_end.setFixedWidth(50)

        frame_by = QtGui.QLabel("by")

        self._frame_step = QtGui.QSpinBox()
        self._frame_step.setValue(1)
        self._frame_step.setFixedWidth(50)

        auto_frange_layout = QtGui.QHBoxLayout()
        auto_frange_layout.setContentsMargins(0, 0, 0, 0)
        auto_frange_layout.setSpacing(4)
        auto_frange_layout.addWidget(self._frame_start)
        auto_frange_layout.addWidget(frame_to)
        auto_frange_layout.addWidget(self._frame_end)
        auto_frange_layout.addWidget(frame_by)
        auto_frange_layout.addWidget(self._frame_step)

        auto_frange = QtGui.QWidget()
        auto_frange.setLayout(auto_frange_layout)

        self._manual_frange = QtGui.QLineEdit(
            str(int(start_time)) + "-" + str(int(end_time)))
        self._manual_frange.setFixedHeight(22)

        self._frange_stack = QtGui.QStackedWidget()
        self._frange_stack.addWidget(auto_frange)
        self._frange_stack.addWidget(self._manual_frange)

        edit_icon_path = IconFactory().disk_path(
            "icon:///images/icons/edit_32x32.png")

        self._frange_btn = QtGui.QPushButton()
        self._frange_btn_size = QtCore.QSize(22, 22)
        self._frange_btn.setFlat(True)
        self._frange_btn.setCheckable(True)
        self._frange_btn.setFixedSize(self._frange_btn_size)
        self._frange_btn.setIcon(QtGui.QIcon(edit_icon_path))
        self._frange_btn.setIconSize(self._frange_btn_size)
        self._frange_btn.toggled.connect(
            lambda c: self._frange_stack.setCurrentIndex(int(c)))

    # -------------------------------------------------------------------------
    def _get_frange_from_controls(self):

        # auto frame range 
        if self._frange_stack.currentIndex() == 0:
                            
            frange_str = str(self._frame_start.value()) + "-" + \
                str(self._frame_end.value()) + ":" + \
                str(self._frame_step.value())
                            
        # manual frame range
        else:
            frange_str = self._manual_frange.text()
                            
        try:                
            frange = Frange(frange_str)
        except FrangeError:
            self._show_error(
                "Unable to determine frame range from: " + frange_str)
            return None

        return frange

    # -------------------------------------------------------------------------
    def _separator(self):

        sep = QtGui.QFrame()
        sep.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Plain)

        return sep

    # -------------------------------------------------------------------------
    def _show_error(self, msg):
        
        error_dialog = QtGui.QErrorMessage(self)
        error_dialog.setWindowTitle("TDK Errors")
        error_dialog.showMessage(msg)

    # -------------------------------------------------------------------------
    def _sync_latest(self):

        ptask = self.session.ptask
        area = self.session.ptask_area
        latest_ver = ptask.latest_version

        area.provision(
            area.dir(version=latest_ver.number, verify=False))

        source_action_class = ActionRegistry().get_action('source', 'ptask')
        if not source_action_class:
            raise DarkKnightError("Could not find ptask source action.")

        source_action = source_action_class(
            source=ptask,
            destination=ptask,
            destination_version=latest_ver,
            wait=True,
        )
        source_action.interactive = False
        source_action()

# -----------------------------------------------------------------------------
class DarkKnightError(Exception):
    pass

