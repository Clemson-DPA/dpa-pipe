
# -----------------------------------------------------------------------------

import datetime
import os

from PySide import QtCore, QtGui

from dpa.config import Config
from dpa.notify import Notification, emails_from_unames
from dpa.nuke.utils import create_product_before_render
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask import PTask
from dpa.queue import get_unique_id, create_queue_task
from dpa.ui.dk.base import BaseDarkKnightDialog, DarkKnightError
from dpa.user import current_username, User

# -----------------------------------------------------------------------------

DK_CONFIG_PATH = "config/notify/dk.cfg"

# -----------------------------------------------------------------------------
class NukeDarkKnightDialog(BaseDarkKnightDialog):

    # XXX meh.
    RENDER_QUEUES = ['nuke', 'muenster', 'cheddar', 'gouda', 'goat', 'hold',
        'velveeta', 'cheezwhiz']

    # -------------------------------------------------------------------------
    def __init__(self, parent=None):

        super(NukeDarkKnightDialog, self).__init__(parent=parent)

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

        self._version_note_edit.setFocus()

    # -------------------------------------------------------------------------
    def accept(self):

        self.setEnabled(False)

        # ---- get the values from the UI

        self._frange = self._get_frange_from_controls()
        if not self._frange:
            self.setEnabled(True)
            return

        self._frame_list = self._frange.frames

        self._render_queue = self._render_queues.currentText()
        self._version_note = self._version_note_edit.text()
        self._node_to_render = self._write_node_select.itemData(
            self._write_node_select.currentIndex())
        self._debug_mode = self._debug.isChecked()

        if not self._version_note:
            self._show_error("Please specify a description of " + 
                "what's changed in this version.")
            self.setEnabled(True)
            return

        try:
            self._render_to_product()
        except Exception as e:
            self.setEnabled(True)
            raise
        else:
            super(NukeDarkKnightDialog, self).accept()

        self.setEnabled(True)
        
    # -------------------------------------------------------------------------
    def _render_to_product(self):

        # add the version note for the product
        render_node = self.session.nuke.toNode(self._node_to_render)
        render_node['product_ver_note'].setValue(self._version_note)

        # ---- progress dialog

        num_ops = 6
        cur_op = 0

        progress_dialog = QtGui.QProgressDialog(
            "Product render...", "", cur_op, num_ops, self)
        progress_dialog.setWindowTitle("Dark Knight is busy...")
        progress_dialog.setAutoReset(False)
        progress_dialog.setLabelText("Preparing nuke file for rendering...")
        progress_dialog.show()

        # ensure the product has been created
        progress_dialog.setLabelText("Creating product...")

        product_repr = create_product_before_render(node=render_node)
        product_repr_area = product_repr.area

        cur_op += 1
        progress_dialog.setValue(cur_op)

        # get timestamp for all the tasks being submitted
        now = datetime.datetime.now()

        ptask_area = PTaskArea.current()
        ptask = PTask.get(ptask_area.spec)

        if ptask_area.version:
            ptask_version = ptask.version(ptask_area.version)
        else:
            ptask_version = ptask.latest_version

        ptask_dir = ptask_area.dir()
        ver_dir = ptask_area.dir(version=ptask_version.number)

        nuke_file = self.session.nuke.root().name()
        nuke_file = nuke_file.replace(ptask_dir, ver_dir)

        file_base = os.path.splitext(os.path.split(nuke_file)[1])[0]

        # ---- sync current work area to version snapshot to render from

        progress_dialog.setLabelText("Sync'ing the latest work...")

        try:
            self.session.save() 
            self._sync_latest()
        except Exception as e:
            self._show_error("Unable to save & sync the latest work: " + str(e))
            self.setEnabled(True)
            progress_dialog.close()
            return

        cur_op += 1
        progress_dialog.setValue(cur_op)

        # make sure queue directory exists 

        progress_dialog.setLabelText("Provisioning the queue directory...")

        try:
            product_repr_area.provision('queue')
        except Exception as e:
            raise DarkKnightError(
                "Unable to create queue scripts directory: " + str(e))

        cur_op += 1
        progress_dialog.setValue(cur_op)

        queue_dir = product_repr_area.dir(dir_name='queue')
        tasks_info_file = os.path.join(queue_dir, 'tasks_info.cfg')
        tasks_info_config = Config()

        progress_dialog.setLabelText("Building the queue script...")

        # dpaset command to run
        dpaset_cmd = 'eval "`dpa env ptask {pt}@{vn}`"'.format(
            pt=ptask.spec, vn=ptask_version.number)

        frange_str = str(self._frange).replace("-", "_").replace(":", "_")

        script_path = os.path.join(queue_dir, 
            "{pn}.{fr}.sh".format(pn=render_node['product_name'].value(),
                fr=frange_str))

        render_cmd = "nuke --cont -f -F {fs}-{fe}x{step} -X {rn} -V 2 -x {nf}".\
            format(
                fs=self._frange.start,
                fe=self._frange.end,
                step=self._frange.step,
                rn=self._node_to_render,
                nf=nuke_file,
            )

        with open(script_path, "w") as script_file:
            script_file.write("#!/bin/bash\n\n")

            # XXX these should happen automatically in the queue...
            script_file.write("source /DPA/wookie/dpa/bash/startup.bash\n")
            script_file.write("pipeup\n\n")

            script_file.write("# set the ptask version to render\n")
            script_file.write(dpaset_cmd + "\n\n")

            script_file.write("# render!\n")
            script_file.write(render_cmd + "\n\n")

        os.chmod(script_path, 0770)

        cur_op += 1
        progress_dialog.setValue(cur_op)
            
        task_id = get_unique_id(product_repr_area.spec, dt=now)
        task_id += "_" + frange_str

        tasks_info_config.add('task_id', task_id)

        out_file = self.session.nuke.filename(render_node, 
            self.session.nuke.REPLACE)

        if not self._debug_mode:

            progress_dialog.setLabelText("Submitting to the queue...")

            create_queue_task(self._render_queue, script_path, 
                task_id, output_file=out_file, submit=True, 
                log_path=script_path + '.log')

        tasks_info_config.write(tasks_info_file)
        os.chmod(tasks_info_file, 0660)

        cur_op += 1
        progress_dialog.setValue(cur_op)

        if not self._debug_mode:

            progress_dialog.setLabelText("Sending submission report...")

            # send msg...
            msg_title = "Queue submission report: " + \
                now.strftime("%Y/%m/%d %H:%M:%S")
            msg_body = "Submitted the following task for " + \
                ptask.spec + ":\n\n"
            msg_body += "  Product representation: " + product_repr.spec + "\n"
            msg_body += "  Description: " + self._version_note + "\n"
            msg_body += "  Render queue: " + self._render_queue + "\n"
            msg_body += "  Frames: " + str(self._frange) + "\n"
            msg_body += "      Task ID: " + task_id + "\n"
            msg_body += "      Scripts directory: " + queue_dir + "\n"
            msg_body += "\n"

            dk_config = ptask.area.config(DK_CONFIG_PATH, 
                composite_ancestors=True, composite_method="append")
            recipients = dk_config.get('notify', [])
            recipients.append(current_username())
            recipients = emails_from_unames(recipients)
            notification = Notification(msg_title, msg_body, recipients,
                sender=User.current().email)
            notification.send_email()

        cur_op += 1
        progress_dialog.setValue(cur_op)
        progress_dialog.close()

    # -------------------------------------------------------------------------
    def _setup_controls(self):

        # ---- verison node

        version_note_lbl = QtGui.QLabel("Version description:")
        self._version_note_edit = QtGui.QLineEdit()

        # ---- write node

        write_nodes = [node for node in self.session.nuke.allNodes(
            filter='Write') if node.knob('product_name')]

        if not write_nodes:
            raise DarkKnightError("No WriteProduct nodes to render.")

        try:
            default_node = self.session.nuke.selectedNode()
        except:
            default_node = write_nodes[0]

        write_node_lbl = QtGui.QLabel('Rendering:')
        self._write_node_select = QtGui.QComboBox()
        default_index = 0
        for (i, node) in enumerate(write_nodes):
            node_name = node.name() 
            node_disp = "{pn} ({nn})".format(
                pn=node['product_name'].value(), nn=node_name)
            self._write_node_select.addItem(node_disp, node_name)
            if node_name == default_node.name():
                default_index = i
        self._write_node_select.setCurrentIndex(default_index)

        # ---- frame range

        min_time = self.session.nuke.root().firstFrame()
        max_time = self.session.nuke.root().lastFrame()
        start_time = min_time 
        end_time = max_time

        frange_lbl = QtGui.QLabel("Frame range:")
        self._make_frame_range_controls(
            min_time, max_time, start_time, end_time)

        controls_layout = QtGui.QGridLayout()

        # ---- queue

        render_queue_lbl = QtGui.QLabel("Render queue:")
        self._render_queues = QtGui.QComboBox()
        self._render_queues.addItems(self.__class__.RENDER_QUEUES)

        # ---- debug 

        debug_lbl = QtGui.QLabel("Debug mode:")
        self._debug = QtGui.QCheckBox("")

        # ---- layout the controls

        controls_layout.addWidget(version_note_lbl, 0, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._version_note_edit, 0, 1)
        controls_layout.addWidget(write_node_lbl, 1, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._write_node_select, 1, 1)
        controls_layout.addWidget(frange_lbl, 2, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._frange_stack, 2, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(self._frange_btn, 2, 2, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(render_queue_lbl, 3, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._render_queues, 3, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(debug_lbl, 4, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._debug, 4, 1, QtCore.Qt.AlignLeft)
        controls_layout.setColumnStretch(2, 1000)
        
        controls_vbox = QtGui.QVBoxLayout()
        controls_vbox.addLayout(controls_layout)
        controls_vbox.addStretch()

        controls_widget = QtGui.QWidget()
        controls_widget.setLayout(controls_vbox)
        
        return controls_widget
        
