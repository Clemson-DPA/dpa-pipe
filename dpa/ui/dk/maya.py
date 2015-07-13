
# -----------------------------------------------------------------------------

import datetime
import os
import shutil

from PySide import QtCore, QtGui

from dpa.action.registry import ActionRegistry
from dpa.env import EnvVar
from dpa.env.vars import DpaVars
from dpa.frange import Frange, FrangeError
from dpa.imgres import ImgRes, ImgResError
from dpa.notify import Notification, emails_from_unames
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask import PTask
from dpa.queue import get_unique_id, create_queue_task
from dpa.ui.dk.base import BaseDarkKnightDialog, DarkKnightError
from dpa.ui.icon.factory import IconFactory
from dpa.user import current_username, User

# -----------------------------------------------------------------------------

DK_CONFIG_PATH = "config/notify/dk.cfg"

# -----------------------------------------------------------------------------
class MayaDarkKnightDialog(BaseDarkKnightDialog):

    # FIXME: i don't want to hardcode this stuff ...
    OUTPUT_FILE_TYPES = ['exr']
    RENDER_QUEUES = ['muenster', 'cheddar', 'gouda', 'goat', 'hold', 'nuke', 
        'velveeta', 'cheezwhiz']
    RIBGEN_QUEUES = ['goat', 'cheddar','muenster',  'gouda', 'hold', 'nuke', 
        'velveeta', 'cheezwhiz']

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
            self._frange = Frange(frange_str)
        except FrangeError:
            self._show_error(
                "Unable to determine frame range from: " + frange_str)
            self.setEnabled(True)
            return

        self._frame_list = self._frange.frames

        if not self._frame_list:
            self._show_error("No frames to render.")
            self.setEnabled(True)
            return

        # ---- resolution

        self._res_str = self._file_res.currentText()

        try:
            self._resolution = ImgRes.get(self._res_str)
        except ImgResError:
            self._show_error(
                "Unable to determine output resolution from: " + self._res_str)
            self.setEnabled(True)
            return

        self._file_type = self._file_types.currentText()
        self._camera = self._cameras.currentText()
        self._ribgen_queue = self._ribgen_queues.currentText()
        self._render_queue = self._render_queues.currentText()
        self._separate_layers = self._sep_layers.isChecked()
        self._generate_ribs = self._gen_ribs.isChecked()
        self._remove_ribs = self._rem_ribs.isChecked()
        self._version_note = self._version_note_edit.text()
        self._debug_mode = self._debug.isChecked()

        if not self._version_note:
            self._show_error("Please specify a description of " + 
                "what's changed in this version.")
            self.setEnabled(True)
            return

        if self._render_to_products:
            try:
                self._product_render()
            except Exception as e:
                self._show_error(str(e))
            else:
                super(MayaDarkKnightDialog, self).accept()
        else:
            self._show_error("Oops! Manual rendering not yet implemented!")

        self.setEnabled(True)

    # -----------------------------------------------------------------------------
    def _product_render(self):

        # get timestamp for all the tasks being submitted
        now = datetime.datetime.now()
    
        render_layers = self._get_render_layers()

        # figure out the total number of operations to perform for the progress
        num_ops = 1 + len(render_layers) * len(self._frame_list) # layer > frame
        num_ops += len(self._frame_list) # frame submission

        if self._remove_ribs:
            num_ops += 1

        if self._generate_ribs:
            num_ops += 1

        cur_op = 0

        progress_dialog = QtGui.QProgressDialog(
            "Product render...", "", cur_op, num_ops, self)
        progress_dialog.setWindowTitle("Dark Knight is busy...")
        progress_dialog.setAutoReset(False)
        progress_dialog.setLabelText("Preparing maya file for rendering...")
        progress_dialog.show()

        ptask = self._cur_ptask
        ptask_version = self._cur_ptask.version(self._version)

        ptask_dir = self._cur_ptask.area.dir()
        ver_dir = ptask.area.dir(version=self._version)
        
        # need to get the maya file in the version directory
        maya_file = self.session.cmds.file(q=True, sceneName=True)
        maya_file = maya_file.replace(ptask_dir, ver_dir)

        file_base = os.path.splitext(os.path.split(maya_file)[1])[0]

        # set lazy rib gen before save/sync
        self.session.cmds.setAttr("renderManGlobals.rman__toropt___lazyRibGen",
            True)
        
        # ---- sync current work area to version snapshot to render from

        cur_project = self.session.cmds.workspace(query=True, rootDirectory=True)
        ver_project = cur_project.replace(ptask_dir, ver_dir)

        progress_dialog.setLabelText("Sync'ing work to current version...")

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

        create_action_cls = ActionRegistry().get_action('create', 'product')
        if not create_action_cls:
            progress_dialog.close()
            raise DarkKnightError("Unable to find product creation action.")

        # ---- clean up ribs

        rib_dir = os.path.join(ver_project, 'renderman', file_base, 'rib')
        if self._remove_ribs:

            progress_dialog.setLabelText("Removing ribs...")

            if os.path.isdir(rib_dir):
                try:
                    shutil.rmtree(rib_dir)
                except Exception as e:
                    progress_dialog.close()
                    raise DarkKnightError("Unable to clean up ribs: " + str(e))

            cur_op += 1
            progress_dialog.setValue(cur_op)

        # ---- construct scripts for the queue

        render_summary = []

        for render_layer in render_layers:

            progress_dialog.setLabelText(
                "Creating product for layer: {rl}...".format(rl=render_layer))

            # ensure product exists for each render layer
            create_action = create_action_cls(
                product=render_layer,
                ptask=ptask_version.ptask_spec,
                version=ptask_version.number,
                category='imgseq',
                description=render_layer + " render layer",
                file_type=self._file_type,
                    resolution=self._res_str,
                note=self._version_note,
            )

            try:
                create_action()
            except ActionError as e:
                progress_dialog.close()
                raise DarkKnightError("Unable to create product: " + str(e))

            product_repr = create_action.product_repr
            product_repr_area = product_repr.area

            progress_dialog.setLabelText(
                "Provisioning 'queue' directory in product...")

            # make sure queue directory exists 
            try:
                product_repr_area.provision('queue')
            except Exception as e:
                progress_dialog.close()
                raise DarkKnightError(
                    "Unable to create queue scripts directory: " + str(e))

            queue_dir = product_repr_area.dir(dir_name='queue')

            # dpaset command to run
            dpaset_cmd = "dpaset {pt}@{vn}".format(pt=ptask.spec,
                vn=ptask_version.number)

            # set group permissions on project dir, recursively
            os.system("chmod g+rw {pd} -R".format(pd=ver_project))

            frame_scripts = []
            for frame in self._frame_list:

                frame_padded = str(frame).zfill(4)

                progress_dialog.setLabelText(
                    "Building render shell script for {rl} frame {f}".format(
                        rl=render_layer, f=frame_padded))

                script_path = os.path.join(queue_dir, 
                    "{rl}.{fn}.sh".format(rl=render_layer, fn=frame_padded))

                out_dir = product_repr_area.dir()

                out_file = os.path.join(out_dir, "{rl}.{fn}.{ft}".\
                    format(rl=render_layer, fn=frame_padded, ft=self._file_type))

                wrong_out_files = os.path.join(out_dir, render_layer,
                    "{rl}*.{fn}.{ft}".format(
                        rl=render_layer, fn=frame_padded, ft=self._file_type))

                render_cmd = "Render -r rman -fnc name.#.ext "
                render_cmd += "-proj {proj} ".format(proj=ver_project)
                render_cmd += "-s {sf} -e {ef} -b 1 -pad 4 ".format(
                    sf=frame, ef=frame)
                render_cmd += '-setAttr Format:resolution "{w} {h}" '.format(
                    w=self._resolution.width, h=self._resolution.height)
                render_cmd += "-of OpenEXR "
                render_cmd += "-cam {cam} ".format(cam=self._camera)
                render_cmd += "-im {layer} -rd {odir} -rl {layer} {mf} ".format(
                    layer=render_layer, odir=out_dir, mf=maya_file) 

                with open(script_path, "w") as script_file:
                    script_file.write("#!/bin/bash\n\n")

                    # XXX these should happen automatically in the queue...
                    script_file.write("source /DPA/moosefs/dpa/bash/startup.bash\n")
                    script_file.write("pipeup\n\n")

                    script_file.write("# set the ptask version to render\n")
                    script_file.write(dpaset_cmd + "\n\n")
                    script_file.write("# render!\n")
                    script_file.write(render_cmd + "\n\n")

                    # rman renders to a subdirectory with the render layer name 
                    # when there are more than one layer. we want the images
                    # one level up.
                    if len(render_layers) > 1:
                        script_file.write("mv {wof} {od}\n\n".format(
                            wof=wrong_out_files, od=out_dir))

                    script_file.write("chmod 660 {of}\n\n".format(
                        of=os.path.join(out_dir, "*." + self._file_type)))

                os.chmod(script_path, 0770)

                frame_scripts.append((frame_padded, script_path))

                cur_op += 1
                progress_dialog.setValue(cur_op)

            frame_tasks = []

            task_id_base = get_unique_id(product_repr_area.spec, dt=now)

            # submit the frames to render
            for (frame, frame_script) in frame_scripts:

                if self._generate_ribs:
                    queue = 'hold'
                else:
                    queue = self._render_queue

                progress_dialog.setLabelText(
                    "Submitting frame: " + frame_script)

                task_id = task_id_base + "_" + frame

                if not self._debug_mode:

                    create_queue_task(queue, frame_script, task_id,
                        output_file=out_dir, submit=True, 
                        log_path=frame_script + '.log')

                    frame_tasks.append(task_id)

                cur_op += 1
                progress_dialog.setValue(cur_op)

            if self._generate_ribs:

                progress_dialog.setLabelText("Creating rib generation script...")

                script_path = os.path.join(queue_dir,
                    "{rl}_ribgen.sh".format(rl=render_layer))

                with open(script_path, "w") as script_file:
                    script_file.write("#!/bin/bash\n\n")

                    # XXX these should happen automatically in the queue...
                    script_file.write("source /DPA/moosefs/dpa/bash/startup.bash\n")
                    script_file.write("pipeup\n\n")

                    script_file.write("# set the ptask version to render\n")
                    script_file.write(dpaset_cmd + "\n\n")
                    script_file.write("# generate the ribs...\n")

                    for frame in self._frame_list:

                        rib_cmd = "Render -r rib -fnc name.#.ext "
                        rib_cmd += "-proj {proj} ".format(proj=ver_project)
                        rib_cmd += "-cam {cam} ".format(cam=self._camera)
                        rib_cmd += "-s {sf} -e {ef} -b 1 -pad 4 ".format(
                            sf=frame, ef=frame)
                        rib_cmd += "-rl {layer} ".format(layer=render_layer)
                        rib_cmd += "{mf} ".format(mf=maya_file) 
                        script_file.write(rib_cmd + "\n")

                    script_file.write(
                        "\n# make sure project dir has group permissions\n")
                    script_file.write(
                        "chmod g+rw {pd} -R\n\n".format(pd=ver_project))

                    # submit the frames to render
                    script_file.write("# Submit frames after rib gen \n")
                    for frame_task in frame_tasks:
                        script_file.write("cqmovetask {qn} {tid}\n".format(
                            qn=self._render_queue, tid=frame_task))

                os.chmod(script_path, 0770)

                # submit the ribgen script
                progress_dialog.setLabelText(
                    "Submitting rib gen: " + script_path)

                task_id = task_id_base + "_ribs"

                if not self._debug_mode:

                    create_queue_task(self._ribgen_queue, script_path, 
                        task_id, output_file=rib_dir, submit=True, 
                        log_path=script_path + '.log')

                cur_op += 1
                progress_dialog.setValue(cur_op)

            cur_op += 1
            progress_dialog.setValue(cur_op)
            progress_dialog.close()

            render_summary.append(
                (render_layer, task_id_base, product_repr, queue_dir))

        if not self._debug_mode:

            # send msg...
            msg_title = "Queue submission report: " + \
                now.strftime("%Y/%m/%d %H:%M:%S")
            msg_body = "Submitted the following tasks for" + \
                ptask.spec + ":\n\n"
            msg_body += "  Description: " + self._version_note + "\n"
            msg_body += "  Resolution: " + self._res_str + "\n"
            msg_body += "  File type: " + self._file_type + "\n"
            msg_body += "  Camera: " + self._camera + "\n"
            if self._generate_ribs:
                msg_body += "  Rib gen queue: " + self._ribgen_queue + "\n"
            msg_body += "  Render queue: " + self._render_queue + "\n"
            msg_body += "  Frames: " + str(self._frange) + "\n"
            msg_body += "  Rib directory: " + rib_dir + "\n"
            msg_body += "\n" 
            for (layer, task_id_base, product_repr, queue_dir) in render_summary:
                msg_body += "    Render layer: " + layer + "\n"
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

    # -------------------------------------------------------------------------
    def _get_render_layers(self):

        render_layers = []

        if self._separate_layers:

            # all layers
            for layer in self.session.cmds.ls(type='renderLayer'):
                if (":" not in layer and 
                    self.session.cmds.getAttr(layer+".renderable")):
                    render_layers.append(layer)

        else:
            
            # current layer
            render_layers.append(self.session.cmds.editRenderLayerGlobals(
                query=True, currentRenderLayer=True))

        if "defaultRenderLayer" in render_layers:
            i = render_layers.index("defaultRenderLayer")
            render_layers[i] = "masterLayer"

        return render_layers

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

        version_num = QtGui.QLabel("<B>v" + str(self._version) + "</B>")

        auto_layout = QtGui.QGridLayout()
        auto_layout.addWidget(ptask_lbl, 0, 0, QtCore.Qt.AlignRight)
        auto_layout.addWidget(ptask_edit, 0, 1)
        auto_layout.addWidget(version_num, 0, 2, QtCore.Qt.AlignLeft)
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

        # ---- version note

        version_note_lbl = QtGui.QLabel("Version description:")
        self._version_note_edit = QtGui.QLineEdit()

        # ---- file type

        file_types_lbl = QtGui.QLabel("File type:")
        self._file_types = QtGui.QComboBox()
        self._file_types.addItems(self.__class__.OUTPUT_FILE_TYPES)

        width = self.session.cmds.getAttr('defaultResolution.width')
        height = self.session.cmds.getAttr('defaultResolution.height')

        file_res_lbl = QtGui.QLabel("Resolution:")
        self._file_res = QtGui.QComboBox()
        self._file_res.setEditable(True)
        self._file_res.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self._file_res.addItems(self._get_resolutions(width, height))

        cam_shape_list = self.session.cmds.ls(cameras=True)
        cam_list = []
        for cam_shape in cam_shape_list:
            cam_renderable = self.session.cmds.getAttr(
                cam_shape + ".renderable")
            cam_name = str(
                self.session.cmds.listRelatives(cam_shape, parent=True)[0])
            if cam_renderable:
                cam_list.insert(0, cam_name)
            else:
                cam_list.append(cam_name)

        cameras_lbl = QtGui.QLabel("Camera:")
        self._cameras = QtGui.QComboBox()
        self._cameras.addItems(cam_list)

        frange_lbl = QtGui.QLabel("Frame range:")

        min_time = self.session.cmds.playbackOptions(query=True, minTime=True)
        max_time = self.session.cmds.playbackOptions(query=True, maxTime=True)

        start_time = self.session.cmds.getAttr('defaultRenderGlobals.startFrame')
        end_time = self.session.cmds.getAttr('defaultRenderGlobals.endFrame')

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

        render_queue_lbl = QtGui.QLabel("Render queue:")
        self._render_queues = QtGui.QComboBox()
        self._render_queues.addItems(self.__class__.RENDER_QUEUES)

        ribgen_queue_lbl = QtGui.QLabel("Rib generation queue:")
        self._ribgen_queues = QtGui.QComboBox()
        self._ribgen_queues.addItems(self.__class__.RIBGEN_QUEUES)

        sep_layers_lbl = QtGui.QLabel("Separate render layers:")
        self._sep_layers = QtGui.QCheckBox("")
        self._sep_layers.setChecked(True)

        gen_ribs_lbl = QtGui.QLabel("Generate rib files:")
        self._gen_ribs = QtGui.QCheckBox("")
        self._gen_ribs.setChecked(True)

        rem_ribs_lbl = QtGui.QLabel("Remove existing ribs:")
        self._rem_ribs = QtGui.QCheckBox("")
        self._rem_ribs.setChecked(True)

        debug_lbl = QtGui.QLabel("Debug mode:")
        self._debug = QtGui.QCheckBox("")

        controls_layout.addWidget(version_note_lbl, 0, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._version_note_edit, 0, 1)
        controls_layout.addWidget(frange_lbl, 1, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._frange_stack, 1, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(frange_btn, 1, 2, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(file_res_lbl, 2, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._file_res, 2, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(file_types_lbl, 3, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._file_types, 3, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(cameras_lbl, 4, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._cameras, 4, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(ribgen_queue_lbl, 5, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._ribgen_queues, 5, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(render_queue_lbl, 6, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._render_queues, 6, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(sep_layers_lbl, 7, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._sep_layers, 7, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(gen_ribs_lbl, 8, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._gen_ribs, 8, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(rem_ribs_lbl, 9, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._rem_ribs, 9, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(debug_lbl, 10, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._debug, 10, 1, QtCore.Qt.AlignLeft)
        controls_layout.setColumnStretch(2, 1000)

        controls_vbox = QtGui.QVBoxLayout()
        controls_vbox.addLayout(controls_layout)
        controls_vbox.addStretch()

        controls_widget = QtGui.QWidget()
        controls_widget.setLayout(controls_vbox)
        
        return controls_widget 

    # -------------------------------------------------------------------------
    def _get_resolutions(self, width, height):

        img_res = ImgRes(width, height)
        resolutions = [str(img_res), str(img_res.half), str(img_res.half.half)]
        return resolutions

