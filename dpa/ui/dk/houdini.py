
# -----------------------------------------------------------------------------

import datetime
import os
import glob

from PySide import QtCore, QtGui

from dpa.config import Config
from dpa.action.registry import ActionRegistry
from dpa.notify import Notification, emails_from_unames
from dpa.houdini.utils import create_product_before_render
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask import PTask
from dpa.queue import get_unique_id, create_queue_task
from dpa.ui.dk.base import BaseDarkKnightDialog, DarkKnightError
from dpa.user import current_username, User

# -----------------------------------------------------------------------------

DK_CONFIG_PATH = "config/notify/dk.cfg"

# -----------------------------------------------------------------------------
class HoudiniDarkKnightDialog(BaseDarkKnightDialog):

    # XXX meh.
    RENDER_QUEUES = ['cheezwhiz', 'cheddar', 'hold', 'nuke', 'velveeta', 
        'muenster']

    # -------------------------------------------------------------------------
    def __init__(self, parent=None):

        super(HoudiniDarkKnightDialog, self).__init__(parent=parent)

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
            super(HoudiniDarkKnightDialog, self).accept()

        self.setEnabled(True)
        
    # -------------------------------------------------------------------------
    def _render_to_product(self):

        # get render node reference
        render_node = self.session.hou.node(self._node_to_render)

        # ---- progress dialog
        num_ops = 8
        cur_op = 0
        progress_dialog = QtGui.QProgressDialog(
            "Product render...", "", cur_op, num_ops, self)
        progress_dialog.setWindowTitle("Dark Knight is busy...")
        progress_dialog.setAutoReset(False)
        progress_dialog.setLabelText("Preparing nuke file for rendering...")
        progress_dialog.show()

        #########################################
        # ensure the product has been created
        #########################################
        progress_dialog.setLabelText("Creating product...")

        if not render_node.type().name()=='ifd' or not self._version_note:
            raise Exception("The supplied node is not a WriteProduct node.")

        print "Creating product for node... " + str(render_node)

        ptask_area = PTaskArea.current()
        ptask = PTask.get(ptask_area.spec)

        if ptask_area.version:
            ptask_version = ptask.version(ptask_area.version)
        else:
            ptask_version = ptask.latest_version

        category = 'imgseq'
        file_type = 'exr'

        product_name = render_node.name()
        product_desc = render_node.name() + " mantra render"
        product_ver_note = self._version_note

        camera_node = self.session.hou.node(render_node.evalParm('camera'))
        if not camera_node:
            raise Exception("Camera specified is not valid.")
        width = camera_node.evalParm("resx")
        height = camera_node.evalParm("resy")
        resolution = "%sx%s" % (width, height)
            
        create_action_cls = ActionRegistry().get_action('create', 'product')
        if not create_action_cls:
            raise Exception("Unable to find product creation action.")

        create_action = create_action_cls(
            product=product_name,
            ptask=ptask.spec,
            version=ptask_version.number,
            category=category,
            description=product_desc,
            file_type=file_type,
            resolution=resolution,
            note=product_ver_note,
        )

        try:
            create_action()
        except ActionError as e:
            raise Exception("Unable to create product: " + str(e))

        # provision the ifd directory
        try:
            create_action.product_repr.area.provision('ifd')
        except Exception as e:
            raise Exception(
                "Unable to create ifd file directory: " + str(e))

        ifd_dir = os.path.join(create_action.product_repr.area.path,
            'ifd', product_name + '.$F4.ifd')
        out_path = os.path.join(create_action.product_repr.area.path,
            product_name + '.$F4.' + file_type)

        # by default, the mantra frame range has an expression on frame numbers
        render_node.parm('f1').deleteAllKeyframes()
        render_node.parm('f2').deleteAllKeyframes()

        # set frange
        render_node.parm('trange').set(1)
        render_node.parm('f1').set(self._frange.start)
        render_node.parm('f2').set(self._frange.end)
        render_node.parm('f3').set(self._frange.step)

        # set output
        render_node.parm('soho_outputmode').set(1)
        render_node.parm('soho_diskfile').set(ifd_dir)
        render_node.parm('soho_diskfile').disable(0)
        render_node.parm('vm_picture').set(out_path)
        render_node.parm('soho_mkpath').set(1)

        product_repr = create_action.product_repr
        product_repr_area = product_repr.area

        cur_op += 1
        progress_dialog.setValue(cur_op)

        #########################################
        # create ifd files
        #########################################
        progress_dialog.setLabelText("Generating ifd files...")
        render_node.parm('execute').pressButton()
        ifd_file_list = glob.glob(
                            os.path.join(
                                create_action.product_repr.area.path,
                                'ifd', '*.ifd')
                            )
        for ifd_file in ifd_file_list:
            os.chmod(ifd_file, 0770)

        cur_op += 1
        progress_dialog.setValue(cur_op)

        #########################################
        # sync current work area to version snapshot to render from
        #########################################
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

        #########################################
        # ensure queue directory exists
        #########################################
        progress_dialog.setLabelText("Provisioning the queue directory...")

        try:
            product_repr_area.provision('queue')
        except Exception as e:
            raise DarkKnightError(
                "Unable to create queue scripts directory: " + str(e))

        cur_op += 1
        progress_dialog.setValue(cur_op)

        out_dir = product_repr_area.path
        ifd_dir = product_repr_area.dir(dir_name='ifd')
        queue_dir = product_repr_area.dir(dir_name='queue')
        tasks_info_file = os.path.join(queue_dir, 'tasks_info.cfg')
        tasks_info_config = Config()

        cur_op += 1
        progress_dialog.setValue(cur_op)


        #########################################
        # buidling queue scripts
        #########################################
        progress_dialog.setLabelText("Building the queue script...")

        # # dpaset command to run
        dpaset_cmd = 'eval "`dpa env ptask {pt}@{vn}`"'.format(
            pt=ptask.spec, vn=ptask_version.number)

        # write out queue shell scripts
        frame_scripts = []
        for frame in self._frame_list:

            frame_padded = str(frame).zfill(4)

            ifd_file = os.path.join(ifd_dir, 
                "{pn}.{fn}.ifd".format(pn=product_name, fn=frame_padded))

            script_path = os.path.join(queue_dir, 
                "{pn}.{fn}.sh".format(pn=product_name, fn=frame_padded))

            out_file = os.path.join(out_dir, 
                "{pn}.{fn}.{ft}".format(pn=product_name, fn=frame_padded, ft=file_type) )

            render_cmd = "/opt/hfs14/bin/mantra -f {ifd} -V 2a".\
                format(
                    ifd=ifd_file
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

            frame_scripts.append((frame_padded, script_path, out_file))

            os.chmod(script_path, 0770)

        cur_op += 1
        progress_dialog.setValue(cur_op)


        ################################################
        # submit to the queue
        ################################################
        now = datetime.datetime.now()
        task_id_base = get_unique_id(product_repr_area.spec, dt=now)

        frame_tasks = []
        # create frame tasks
        for (frame, frame_script, out_file) in frame_scripts:

            progress_dialog.setLabelText(
                "Submitting frame: " + frame_script)

            task_id = task_id_base + "_" + frame

            if not self._debug_mode:

                # create tasks, don't actually submit yet
                create_queue_task(self._render_queue, frame_script, task_id,
                    output_file=out_file, submit=False, 
                    log_path=frame_script + '.log')

                frame_tasks.append((frame, task_id))
                #
                #  resubmit frame-by-frame because 
                #  group submit seems to be occasionally
                #  having problems.
                os.system("cqresubmittask {qn} {tid}".format(
                    qn=self._render_queue, tid=task_id))

        cur_op += 1
        progress_dialog.setValue(cur_op)

        ################################################
        # task info stuff, allows task ids to 
        # be retrieved with product spec
        ################################################
        progress_dialog.setLabelText("Creating task info file...")

        tasks_info_file = os.path.join(queue_dir, 'tasks_info.cfg')
        tasks_info_config = Config()
        tasks_info_config.add('base_id', task_id_base)

        frame_info = Config()
        for (frame, task_id) in frame_tasks:
            frame_info.add(str(frame), task_id)
        tasks_info_config.add('frame_ids', frame_info)

        tasks_info_config.write(tasks_info_file)
        os.chmod(tasks_info_file, 0660)

        cur_op += 1
        progress_dialog.setValue(cur_op)


        ################################################
        # email report
        ################################################
        if not self._debug_mode:
            # send msg...
            msg_title = "Queue submission report: " + \
                now.strftime("%Y/%m/%d %H:%M:%S")
            msg_body = "Submitted the following tasks for " + \
                ptask.spec + ":\n\n"
            msg_body += "  Description: " + self._version_note + "\n"
            msg_body += "  Resolution: " + resolution + "\n"

            msg_body += "  Render queue: " + self._render_queue + "\n"
            msg_body += "  Frames: " + str(self._frange) + "\n"
            msg_body += "  Ifd directory: " + ifd_dir + "\n"
            msg_body += "\n" 

            msg_body += "      Base task ID: " + task_id_base + "\n"
            msg_body += "      Product representation: " + \
                product_repr.spec + "\n"
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
            print recipients

        cur_op += 1
        progress_dialog.setValue(cur_op)
        progress_dialog.close()

    # -------------------------------------------------------------------------
    def _setup_controls(self):

        # ---- verison node

        version_note_lbl = QtGui.QLabel("Version description:")
        self._version_note_edit = QtGui.QLineEdit()

        # ---- mantra nodes

        write_nodes = [node 
            for node in self.session.hou.node("/").allSubChildren() 
            if node.type().name()=='ifd']

        if not write_nodes:
            raise DarkKnightError("No WriteProduct nodes to render.")

        try:
            default_node = self.session.hou.selectedNodes()[0]
        except:
            default_node = write_nodes[0]

        write_node_lbl = QtGui.QLabel('Rendering:')
        self._write_node_select = QtGui.QComboBox()
        default_index = 0
        for (i, node) in enumerate(write_nodes):
            node_name = node.name() 
            node_path = node.path() 
            node_disp = "{pn} ({nn})".format(
                pn=node_name, nn=node_path)
            self._write_node_select.addItem(node_disp, node_path)
            if node_name == default_node.name():
                default_index = i
        self._write_node_select.setCurrentIndex(default_index)

        # ---- frame range

        # frange
        render_node_path = self._write_node_select.itemData(
            self._write_node_select.currentIndex())
        render_node = self.session.hou.node(render_node_path)
        min_time = render_node.evalParm('f1')
        max_time = render_node.evalParm('f2')
        start_time = min_time 
        end_time = max_time

        frange_lbl = QtGui.QLabel("Frame range:")
        self._make_frame_range_controls(
            min_time, max_time, start_time, end_time)

        self._frame_step.setValue(render_node.evalParm('f3'))

        controls_layout = QtGui.QGridLayout()

        # ---- queue

        render_queue_lbl = QtGui.QLabel("Render queue:")
        self._render_queues = QtGui.QComboBox()
        self._render_queues.addItems(self.__class__.RENDER_QUEUES)

        # ---- debug 

        debug_lbl = QtGui.QLabel("Debug mode:")
        self._debug = QtGui.QCheckBox("")

        # 
        self.connect(self._write_node_select, QtCore.SIGNAL("currentIndexChanged(const QString&)"), self._updateFrange)

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
        


    # -------------------------------------------------------------------------
    def _updateFrange(self):
        render_node_path = self._write_node_select.itemData(
            self._write_node_select.currentIndex())
        render_node = self.session.hou.node(render_node_path)
        self._frame_start.setValue(render_node.evalParm('f1'))
        self._frame_end.setValue(render_node.evalParm('f2'))
        self._frame_step.setValue(render_node.evalParm('f3'))