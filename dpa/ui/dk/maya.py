
# -----------------------------------------------------------------------------

import os

from PySide import QtCore, QtGui

from dpa.env import EnvVar
from dpa.env.vars import DpaVars
from dpa.frange import Frange, FrangeError
from dpa.imgres import ImgRes, ImgResError
from dpa.ptask.area import PTaskArea
from dpa.ptask import PTask
from .base import BaseDarkKnightDialog
from dpa.ui.icon.factory import IconFactory

# -----------------------------------------------------------------------------
class MayaDarkKnightDialog(BaseDarkKnightDialog):

    # XXX i don't want to hardcode this stuff...
    OUTPUT_DEFAULT_RES = '1920x1080'
    OUTPUT_FILE_TYPES = ['exr']
    QUEUES = ['cheddar', 'muenster', 'gouda', 'goat', 'hold', 'nuke', 
        'velveeta', 'cheezwhiz']
    RENDERERS = ['RenderMan']

    # -------------------------------------------------------------------------
    def __init__(self, parent=None):

        super(MayaDarkKnightDialog, self).__init__(parent=parent)

        # ---- output options

        output_options = self._output_options()

        self.main_layout.addLayout(output_options)
        self.main_layout.setStretchFactor(output_options, 0)

        # ---- controls

        controls_widget = self._setup_controls()

        scroll_area = QtGui.QScrollArea()
        scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(controls_widget)

        self.main_layout.addWidget(scroll_area)
        self.main_layout.setStretchFactor(scroll_area, 1000)

        # ---- submit btn

        cancel_btn = QtGui.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)

        submit_btn = QtGui.QPushButton("Submit")
        submit_btn.clicked.connect(self.accept)

        btn_layout = QtGui.QHBoxLayout()
        btn_layout.setContentsMargins(4, 4, 4, 4)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(submit_btn)
        btn_layout.addStretch()

        self.main_layout.addLayout(btn_layout)
        self.main_layout.setStretchFactor(btn_layout, 0)

    # -------------------------------------------------------------------------
    def accept(self):

        self.setEnabled(False)

        # ---- get the values from the UI

        # ptask/version                
        if self._output_stack.currentIndex() == 0:
            self._render_to_products = True
            if not self._cur_ptask or not self._version:
                self._show_error(
                    "Could not determine ptask/version to render to.") 
                self.setEnabled(True)
                return
        
        # manual directory
        else:
            self._render_to_products = False
            self._output_dir = self._dir_edit.text()

        # ---- frame range

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
            self.setEnabled(True)
            return

        self._frame_list = frange.frames

        # ---- resolution

        res_str = self._file_res.currentText()

        try:
            self._resolution = ImgRes.get(res_str)
        except ImgResError:
            self._show_error(
                "Unable to determine output resolution from: " + res_str)
            self.setEnabled(True)
            return

        self._file_type = self._file_types.currentText()
        self._camera = self._cameras.currentText()
        self._renderer = self._renderers.currentText()
        self._queue = self._queues.currentText()
        self._separate_layers = self._sep_layers.isChecked()
        self._generate_ribs = self._gen_ribs.isChecked()
        self._remove_ribs = self._rem_ribs.isChecked()

        # XXX submit the renders

        # ensure directory structure exists
        # generate shell scripts

        self.setEnabled(True)
        super(MayaDarkKnightDialog, self).accept()

    # -------------------------------------------------------------------------
    def _show_error(self, msg):
        
        error_dialog = QtGui.QErrorMessage(self)
        error_dialog.setWindowTitle("TDK Errors")
        error_dialog.showMessage(msg)

    # -------------------------------------------------------------------------
    def _output_options(self):

        output_type_lbl = QtGui.QLabel("Output:")
        output_type = QtGui.QComboBox()
        output_type.addItems(['Automatic', 'Manual'])

        header_layout = QtGui.QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(output_type_lbl)
        header_layout.addWidget(output_type)
        header_layout.addStretch()

        # ---- auto

        cur_area = PTaskArea.current()
        self._cur_ptask = PTask.get(cur_area.spec)
        if self._cur_ptask:
            self._version = \
                cur_area.version or self._cur_ptask.latest_version.number
        else:
            self._cur_ptask = None
            self._version = "None"

        ptask_lbl = QtGui.QLabel("PTask:")
        ptask_edit = QtGui.QLineEdit(str(self._cur_ptask))
        ptask_edit.setReadOnly(True)

        version_lbl = QtGui.QLabel("Version:")
        version_num = QtGui.QLabel("<B>" + str(self._version) + "</B>")

        auto_layout = QtGui.QGridLayout()
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
        self._dir_edit = QtGui.QLineEdit(os.getcwd())

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
        dir_dialog.fileSelected.connect(self._dir_edit.setText)

        dir_btn.clicked.connect(dir_dialog.show)

        manual_layout = QtGui.QGridLayout()
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.addWidget(dir_lbl, 0, 0, QtCore.Qt.AlignRight)
        manual_layout.addWidget(self._dir_edit, 0, 1)
        manual_layout.addWidget(dir_btn, 0, 2)
        manual_layout.setColumnStretch(0, 0)
        manual_layout.setColumnStretch(1, 1000)
        manual_layout.setColumnStretch(2, 0)

        manual_widgets = QtGui.QWidget()
        manual_widgets.setLayout(manual_layout)

        self._output_stack = QtGui.QStackedWidget()
        self._output_stack.addWidget(auto_widgets)
        self._output_stack.addWidget(manual_widgets)

        output_type.activated.connect(self._output_stack.setCurrentIndex)

        # ---- layout

        output_layout = QtGui.QVBoxLayout()
        output_layout.addLayout(header_layout)
        output_layout.addWidget(self._output_stack)

        return output_layout 

    # -------------------------------------------------------------------------
    def _setup_controls(self):

        controls_layout = QtGui.QGridLayout()

        # ---- file type

        file_types_lbl = QtGui.QLabel("File type:")
        self._file_types = QtGui.QComboBox()
        self._file_types.addItems(self.__class__.OUTPUT_FILE_TYPES)

        file_res_lbl = QtGui.QLabel("Resolution:")
        self._file_res = QtGui.QComboBox()
        self._file_res.setEditable(True)
        self._file_res.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self._file_res.addItems(self._get_resolutions())

        cam_list = self.session.cmds.listCameras(perspective=True)
        cam_list.extend(self.session.cmds.listCameras(orthographic=True))

        cameras_lbl = QtGui.QLabel("Camera:")
        self._cameras = QtGui.QComboBox()
        self._cameras.addItems(cam_list)

        frange_lbl = QtGui.QLabel("Frame range:")
    
        min_time = self.session.cmds.playbackOptions(
            query=True, minTime=True)
        max_time = self.session.cmds.playbackOptions(
            query=True, maxTime=True)

        anim_start_time = self.session.cmds.playbackOptions(
            query=True, animationStartTime=True)
        anim_end_time = self.session.cmds.playbackOptions(
            query=True, animationEndTime=True)

        self._frame_start = QtGui.QSpinBox()
        self._frame_start.setValue(min_time)
        self._frame_start.setMinimum(anim_start_time)
        self._frame_start.setMaximum(anim_end_time)
        self._frame_start.setFixedWidth(50)

        frame_to = QtGui.QLabel("to")

        self._frame_end = QtGui.QSpinBox()
        self._frame_end.setValue(max_time)
        self._frame_end.setMinimum(anim_start_time)
        self._frame_end.setMaximum(anim_end_time)
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
            str(int(min_time)) + "-" + str(int(max_time)))
        self._manual_frange.setFixedHeight(22)

        self._frange_stack = QtGui.QStackedWidget()
        self._frange_stack.addWidget(auto_frange)
        self._frange_stack.addWidget(self._manual_frange)

        edit_icon_path = IconFactory().disk_path("icon:///images/icons/edit_32x32.png")

        frange_btn = QtGui.QPushButton()
        frange_btn_size = QtCore.QSize(22, 22)
        frange_btn.setFlat(True)
        frange_btn.setCheckable(True)
        frange_btn.setFixedSize(frange_btn_size)
        frange_btn.setIcon(QtGui.QIcon(edit_icon_path))
        frange_btn.setIconSize(frange_btn_size)
        frange_btn.toggled.connect(
            lambda c: self._frange_stack.setCurrentIndex(int(c)))

        renderers_lbl = QtGui.QLabel("Renderer:")
        self._renderers = QtGui.QComboBox()
        self._renderers.addItems(self.__class__.RENDERERS)

        queue_lbl = QtGui.QLabel("Render queue:")        
        self._queues = QtGui.QComboBox()
        self._queues.addItems(self.__class__.QUEUES)

        sep_layers_lbl = QtGui.QLabel("Separate render layers:")
        self._sep_layers = QtGui.QCheckBox("")
        self._sep_layers.setChecked(True)

        gen_ribs_lbl = QtGui.QLabel("Generate rib files:")
        self._gen_ribs = QtGui.QCheckBox("")
        self._gen_ribs.setChecked(True)

        rem_ribs_lbl = QtGui.QLabel("Remove existing ribs:")
        self._rem_ribs = QtGui.QCheckBox("")

        controls_layout.addWidget(frange_lbl, 0, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._frange_stack, 0, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(frange_btn, 0, 2, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(file_res_lbl, 1, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._file_res, 1, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(file_types_lbl, 2, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._file_types, 2, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(cameras_lbl, 3, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._cameras, 3, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(renderers_lbl, 4, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._renderers, 4, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(queue_lbl, 5, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._queues, 5, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(sep_layers_lbl, 6, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._sep_layers, 6, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(gen_ribs_lbl, 7, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._gen_ribs, 7, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(rem_ribs_lbl, 8, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._rem_ribs, 8, 1, QtCore.Qt.AlignLeft)
        controls_layout.setColumnStretch(2, 1000)

        controls_vbox = QtGui.QVBoxLayout()
        controls_vbox.addLayout(controls_layout)
        controls_vbox.addStretch()

        controls_widget = QtGui.QWidget()
        controls_widget.setLayout(controls_vbox)
        
        return controls_widget 

    # -------------------------------------------------------------------------
    def _get_resolutions(self):

        res_var = EnvVar('DPA_OUTPUT_RESOLUTION', '1920x1080')
        resolution = res_var.get()

        img_res = ImgRes.get(resolution)

        resolutions = [str(img_res), str(img_res.half), str(img_res.half.half)]

        return resolutions

