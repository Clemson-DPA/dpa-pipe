
from PySide import QtCore, QtGui

from dpa.app.session import Session, SessionRegistry, SessionError
from dpa.ui.action.options import ActionOptionWidget

# -----------------------------------------------------------------------------
class SessionDialog(QtGui.QDialog):

    # -------------------------------------------------------------------------
    def __init__(self):

        self._session = SessionRegistry().current()
        if not self._session:
            raise SessionError("Unable to determine current app session.")

        super(SessionDialog, self).__init__(self._session.main_window)
        
    # -------------------------------------------------------------------------
    @property
    def session(self):
        return self._session

# -----------------------------------------------------------------------------
class SessionActionDialog(SessionDialog):

    # -------------------------------------------------------------------------
    def __init__(self, title, options_config, icon_path=None, 
        action_button_text=None, modal=False):

        super(SessionActionDialog, self).__init__()

        self.setModal(modal)
        self.setWindowTitle(title)

        icon_lbl = QtGui.QLabel()
        icon_lbl.setPixmap(QtGui.QPixmap(icon_path))
        icon_lbl.setAlignment(QtCore.Qt.AlignRight)

        title = QtGui.QLabel(title)
        title.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        font = title.font()
        font.setPointSize(18)
        title.setFont(font)

        header_layout = QtGui.QHBoxLayout()
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title)
        header_layout.setStretchFactor(title, 90)

        self._options = ActionOptionWidget(options_config)

        self._btn_box = QtGui.QDialogButtonBox()
        self._btn_box.addButton(QtGui.QDialogButtonBox.Cancel)
        self._action_btn = self._btn_box.addButton(QtGui.QDialogButtonBox.Ok)

        if action_button_text:
            self._action_btn.setText(action_button_text)

        layout = QtGui.QVBoxLayout(self)
        layout.addLayout(header_layout)
        layout.addWidget(self._options)
        layout.addWidget(self._btn_box)

        self._options.value_changed.connect(self.check_value)

        self._btn_box.accepted.connect(self.accept)
        self._btn_box.rejected.connect(self.reject)

        self.check_value()

    # -------------------------------------------------------------------------
    @property
    def options(self):
        return self._options

    # -------------------------------------------------------------------------
    def check_value(self):
        
        if self._options.value_ok:
            self._action_btn.setEnabled(True)
        else:
            self._action_btn.setEnabled(False)

