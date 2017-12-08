
# -----------------------------------------------------------------------------

import datetime
import os
import shutil
import re

from PySide import QtCore, QtGui

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.config import Config
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
PRMAN_CONFIG_PATH = "config/maya/prman.cfg"

# -----------------------------------------------------------------------------
class MayaDarkKnightDialog(BaseDarkKnightDialog):

    # FIXME: i don't want to hardcode this stuff ...
    OUTPUT_FILE_TYPES = ['exr']
    RENDER_QUEUES = ['cheddar', 'nuke', 'velveeta', 'cheezwhiz', 'muenster', 'brie', 'hold']
    RIBGEN_QUEUES = ['rathgore', 'cheddar', 'nuke', 'velveeta', 'cheezwhiz', 'brie', 'hold']
    RENDERERS = ['Renderman', 'Arnold']

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

        self._frange = self._get_frange_from_controls()
        if not self._frange:
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
        self._renderer_to_use = self._renderers.currentText()
        self._scenegen_queue = self._scenegen_queues.currentText()
        self._render_queue = self._render_queues.currentText()
        self._separate_layers = self._sep_layers.isChecked()
        self._generate_scenes = self._gen_scenes.isChecked()
        self._remove_scenes = self._rem_scenes.isChecked()
        self._version_note = self._version_note_edit.text()
        self._debug_mode = self._debug.isChecked()

        # Choose product renderer
        product_render = self._product_render_renderman
        if self._renderer_to_use == 'Arnold':
            product_render = self._product_render_arnold

        if not self._version_note:
            self._show_error("Please specify a description of " + 
                "what's changed in this version.")
            self.setEnabled(True)
            return

        if self._render_to_products:
            try:
                product_render()
            except Exception as e:
                self._show_error(str(e))
            else:
                super(MayaDarkKnightDialog, self).accept()
        else:
            self._show_error("Oops! Manual rendering not yet implemented!")

        self.setEnabled(True)

    # -----------------------------------------------------------------------------
    def _product_render_renderman(self):

        # get timestamp for all the tasks being submitted
        now = datetime.datetime.now()
    
        render_layers = self._get_render_layers()

        # figure out the total number of operations to perform for the progress
        num_ops = 1 + len(render_layers) * len(self._frame_list) # layer > frame
        num_ops += len(self._frame_list) # frame submission

        if self._remove_scenes:
            num_ops += 1

        if self._generate_scenes:
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

        self.session.cmds.setAttr('defaultResolution.width', self._resolution.width)
        self.session.cmds.setAttr('defaultResolution.height', self._resolution.height)

        if self._file_type == 'exr':
            self.session.cmds.setAttr("rmanFinalOutputGlobals0.rman__riopt__Display_type",
            "openexr", type="string")

        # set the output file naming convention to name.#.ext
        self.session.cmds.setAttr("defaultRenderGlobals.animation", True)
        self.session.cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", True)
        self.session.cmds.setAttr("defaultRenderGlobals.outFormatControl", False)

        # set all other cameras to not be renderable (this seems to work)
        cam_shape_list = self.session.cmds.ls(cameras=True)
        for cam_shape in cam_shape_list:
            cam_name = str(
                self.session.cmds.listRelatives(cam_shape, parent=True)[0])
            if cam_name == self._camera:
                self.session.cmds.setAttr(cam_shape + ".renderable", 1)
            else:
                self.session.cmds.setAttr(cam_shape + ".renderable", 0)

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

        # ---- clean up scenes

        scene_dir = os.path.join(ver_project, 'renderman', file_base, 'rib')
        if self._remove_scenes:

            progress_dialog.setLabelText("Removing ribs...")

            if os.path.isdir(scene_dir):
                try:
                    shutil.rmtree(scene_dir)
                except Exception as e:
                    progress_dialog.close()
                    raise DarkKnightError("Unable to clean up ribs: " + str(e))

            cur_op += 1
            progress_dialog.setValue(cur_op)

        # ---- get a list of warnings to ignore

        prman_config = ptask.area.config(PRMAN_CONFIG_PATH, 
            composite_ancestors=True, composite_method="override")
        prman_warnings = " ".join(
            ["-woff " + w for w in prman_config.get('woff', [])])

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
            tasks_info_file = os.path.join(queue_dir, 'tasks_info.cfg')
            tasks_info_config = Config()

            # dpaset command to run
            dpaset_cmd = 'eval "`dpa env ptask {pt}@{vn}`"'.format(
                pt=ptask.spec, vn=ptask_version.number)
            
            # set group permissions on project dir, recursively
            os.system("chmod g+rw {pd} -R".format(pd=ver_project))

            # figure out the render layer
            if render_layer == 'masterLayer':
                layer_index = self.session.cmds.getAttr("defaultRenderLayer.rlid")
            else:
                layer_index = self.session.cmds.getAttr(render_layer + ".rlid")

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

                simple_scene = "{proj}renderman/{fb}/rib/{fn}/{fn}.rib".format(
                    proj=ver_project, fb=file_base, fn=frame_padded)

                layer_scene = "{proj}renderman/{fb}/rib/{fn}/{fn}_{rl}.rib".\
                    format(proj=ver_project, fb=file_base, fn=frame_padded,
                        rl=render_layer)

                render_cmd = "dpa_ribrender -r $RIB_PATH "
                render_cmd += "-o {od} ".format(od=out_dir)
                # For Josh: I'm altering how this works in dpa_ribrender
                render_cmd += "-f {rl} ".format(rl=render_layer)
                render_cmd += "-p {proj} ".format(proj=ver_project)
                render_cmd += "--prman '-t:0 -cwd \"{proj}\" {warn}' ".\
                    format(proj=ver_project, warn=prman_warnings)

                with open(script_path, "w") as script_file:
                    script_file.write("#!/bin/bash\n\n")

                    # XXX these should happen automatically in the queue...
                    script_file.write("source /DPA/wookie/dpa/bash/startup.bash\n")
                    script_file.write("pipeup\n\n")

                    script_file.write("# set the ptask version to render\n")
                    script_file.write(dpaset_cmd + "\n")
                    script_file.write("cd " + ver_project + "\n\n")

                    # the logic for determining which scene will be generated is
                    # unclear at this point. So we'll build a conditional
                    script_file.write("if [[ -f {lr} ]]; then\n".format(lr=layer_scene))
                    script_file.write("    export RIB_PATH={lr}\n".format(lr=layer_scene))
                    script_file.write("else\n")
                    script_file.write("    export RIB_PATH={sr}\n".format(sr=simple_scene))
                    script_file.write("fi\n")

                    script_file.write("# render!\n")
                    script_file.write(render_cmd + "\n\n")

                    script_file.write("chmod 660 {of}\n\n".format(
                        of=os.path.join(out_dir, 
                            render_layer + "*." + self._file_type)))

                os.chmod(script_path, 0770)

                frame_scripts.append((frame_padded, script_path, out_file))

                cur_op += 1
                progress_dialog.setValue(cur_op)

            frame_tasks = []

            task_id_base = get_unique_id(product_repr_area.spec, dt=now)
            tasks_info_config.add('base_id', task_id_base)

            if self._generate_scenes:
                frame_queue = 'hold'
            else:
                frame_queue = self._render_queue

            # create frame tasks
            for (frame, frame_script, out_file) in frame_scripts:

                progress_dialog.setLabelText(
                    "Submitting frame: " + frame_script)

                task_id = task_id_base + "_" + frame

                if not self._debug_mode:

                    # create tasks, don't actually submit yet
                    create_queue_task(frame_queue, frame_script, task_id,
                        output_file=out_file, submit=False, 
                        log_path=frame_script + '.log')

                    frame_tasks.append((frame, task_id))
                    #
                    #  resubmit frame-by-frame because 
                    #  group submit seems to be occasionally
                    #  having problems.
                    os.system("cqresubmittask {qn} {tid}".format(
                        qn=frame_queue, tid=task_id))

                cur_op += 1
                progress_dialog.setValue(cur_op)

            frame_info = Config()
            for (frame, task_id) in frame_tasks:
                frame_info.add(str(frame), task_id)
            tasks_info_config.add('frame_ids', frame_info)

            # resubmit all at once (workaround for slow individual submissions)
            #
            #  This approach seems to be having problems with the server
            #  communications.  Switch to frame-by-frame resubmit because
            #  that has worked where this fails
            #os.system("cqresubmittask {qn} {tid}".format(
            #    qn=frame_queue, tid=task_id_base))

            if self._generate_scenes:

                progress_dialog.setLabelText("Creating rib generation script...")

                script_path = os.path.join(queue_dir,
                    "{rl}_ribgen.sh".format(rl=render_layer))

                with open(script_path, "w") as script_file:
                    script_file.write("#!/bin/bash\n\n")

                    # XXX these should happen automatically in the queue...
                    script_file.write("source /DPA/wookie/dpa/bash/startup.bash\n")
                    script_file.write("pipeup\n\n")

                    script_file.write("# set the ptask version to render\n")
                    script_file.write(dpaset_cmd + "\n")
                    script_file.write("cd " + ver_project + "\n\n")

                    script_file.write("# generate the ribs...\n")

                    job_scene_cmd = 'maya2016 -batch -proj "{proj}" '.format(
                        proj=ver_project)
                    job_scene_cmd += '-command "renderManBatchGenRibForLayer {li} {sf} {ef} 1" '.\
                        format(li=layer_index, sf=self._frange.start, ef=self._frange.end)
                    job_scene_cmd += '-file "{mf}"'.format(mf=maya_file)
                    script_file.write(job_scene_cmd + "\n")

                    frames_scene_cmd = 'maya2016 -batch -proj "{proj}" '.format(
                        proj=ver_project)
                    frames_scene_cmd += '-command "renderManBatchGenRibForLayer {li} {sf} {ef} 2" '.\
                        format(li=layer_index, sf=self._frange.start, ef=self._frange.end)
                    frames_scene_cmd += '-file "{mf}"'.format(mf=maya_file)
                    script_file.write(frames_scene_cmd + "\n")

                    script_file.write(
                        "\n# make sure project dir has group permissions\n")
                    script_file.write(
                        "chmod g+rw {pd} -R\n\n".format(pd=ver_project))

                    # submit the frames to render
                    script_file.write("# Submit frames after rib gen \n")
                    for (frame, frame_task) in frame_tasks:
                        script_file.write("cqmovetask {qn} {tid}\n".format(
                            qn=self._render_queue, tid=frame_task))
                    
                    # changed to move group
                    #script_file.write("cqmovetask {qn} {tid}\n".format(
                        #qn=self._render_queue, tid=task_id_base))

                os.chmod(script_path, 0770)

                # submit the scenegen script
                progress_dialog.setLabelText(
                    "Submitting rib gen: " + script_path)

                task_id = task_id_base + "_ribs"
                tasks_info_config.add('ribgen_id', task_id)

                if not self._debug_mode:

                    create_queue_task(self._scenegen_queue, script_path, 
                        task_id, output_file=scene_dir, submit=True, 
                        log_path=script_path + '.log')

                cur_op += 1
                progress_dialog.setValue(cur_op)

            cur_op += 1
            progress_dialog.setValue(cur_op)
            progress_dialog.close()

            render_summary.append(
                (render_layer, task_id_base, product_repr, queue_dir))

            # For now, disable wrangling tickets. bsddb is causing problems
            # - zshore, 2015-10-23
            # if not self._debug_mode:

            #     # ---- dpa specific queue stuff            

            #     from cheesyq import DPAWrangler

            #     # create wrangling ticket 
            #     wrangle = DPAWrangler.WrangleRecord(task_id_base)
            #     wrangle.frames = self._frame_list
            #     db = DPAWrangler.GetWranglingDB()
            #     db.set(wrangle.baseId, wrangle)
            #     DPAWrangler.AssignWranglerTask("none", task_id_base)

            #  - jtessen  2016-01-11
            # switch to using a cmd line wrangle item creator to avoid the
            # bsddb issue
            wranglecmd = 'cqcreatewrangleitem ' + task_id_base + ' '
            for f in self._frame_list:
                wranglecmd = wranglecmd + str(f) + ' '
            print wranglecmd
            os.system(wranglecmd)
                

            tasks_info_config.write(tasks_info_file)
            os.chmod(tasks_info_file, 0660)

        if not self._debug_mode:

            # send msg...
            msg_title = "Queue submission report: " + \
                now.strftime("%Y/%m/%d %H:%M:%S")
            msg_body = "Submitted the following tasks for " + \
                ptask.spec + ":\n\n"
            msg_body += "  Description: " + self._version_note + "\n"
            msg_body += "  Resolution: " + self._res_str + "\n"
            msg_body += "  File type: " + self._file_type + "\n"
            msg_body += "  Camera: " + self._camera + "\n"
            if self._generate_scenes:
                msg_body += "  Rib gen queue: " + self._scenegen_queue + "\n"
            msg_body += "  Render queue: " + self._render_queue + "\n"
            msg_body += "  Frames: " + str(self._frange) + "\n"
            msg_body += "  Rib directory: " + scene_dir + "\n"
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

    # -----------------------------------------------------------------------------
    def _product_render_arnold(self):

        # get timestamp for all the tasks being submitted
        now = datetime.datetime.now()
    
        render_layers = self._get_render_layers()

        # figure out the total number of operations to perform for the progress
        num_ops = 1 + len(render_layers) * len(self._frame_list) # layer > frame
        num_ops += len(self._frame_list) # frame submission

        if self._remove_scenes:
            num_ops += 1

        if self._generate_scenes:
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

        self.session.cmds.setAttr('defaultResolution.width', self._resolution.width)
        self.session.cmds.setAttr('defaultResolution.height', self._resolution.height)

        # set the output file naming convention to name.#.ext
        self.session.cmds.setAttr("defaultRenderGlobals.animation", True)
        self.session.cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", True)
        self.session.cmds.setAttr("defaultRenderGlobals.outFormatControl", False)

        # set all other cameras to not be renderable (this seems to work)
        cam_shape_list = self.session.cmds.ls(cameras=True)
        for cam_shape in cam_shape_list:
            cam_name = str(
                self.session.cmds.listRelatives(cam_shape, parent=True)[0])
            if cam_name == self._camera:
                self.session.cmds.setAttr(cam_shape + ".renderable", 1)
            else:
                self.session.cmds.setAttr(cam_shape + ".renderable", 0)

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

        # ---- clean up ASSs

        scene_dir = os.path.join(ver_project, 'arnold', file_base, 'ass')
        if self._remove_scenes:

            progress_dialog.setLabelText("Removing ass files...")

            if os.path.isdir(scene_dir):
                try:
                    shutil.rmtree(scene_dir)
                except Exception as e:
                    progress_dialog.close()
                    raise DarkKnightError("Unable to clean up ass files: " + str(e))

            cur_op += 1
            progress_dialog.setValue(cur_op)

        # ---- get a list of warnings to ignore

        #prman_config = ptask.area.config(PRMAN_CONFIG_PATH, 
        #    composite_ancestors=True, composite_method="override")
        #prman_warnings = " ".join(
        #    ["-woff " + w for w in prman_config.get('woff', [])])

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
            tasks_info_file = os.path.join(queue_dir, 'tasks_info.cfg')
            tasks_info_config = Config()

            # dpaset command to run
            dpaset_cmd = 'eval "`dpa env ptask {pt}@{vn}`"'.format(
                pt=ptask.spec, vn=ptask_version.number)
            
            # set group permissions on project dir, recursively
            os.system("chmod g+rw {pd} -R".format(pd=ver_project))

            # figure out the render layer
            if render_layer == 'masterLayer':
                layer_index = self.session.cmds.getAttr("defaultRenderLayer.rlid")
            else:
                layer_index = self.session.cmds.getAttr(render_layer + ".rlid")

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

                simple_scene = "{proj}arnold/{fb}/ass/{fb}.{fn}.ass".format(
                    proj=ver_project, fb=file_base, fn=frame_padded)

                layer_scene = "{proj}arnold/{fb}/ass/{fb}_{rl}.{fn}.ass".\
                    format(proj=ver_project, fb=file_base, fn=frame_padded,
                        rl=render_layer)

                render_cmd = "/opt/solidangle/arnold-maya2016/bin/kick -dw -v 6 -i $ASS_PATH "
                render_cmd += "-l /opt/solidangle/arnold-maya2016/shaders "
                render_cmd += "-l /opt/solidangle/arnold-maya2016/procedurals "
                render_cmd += "-o {od} ".format(od=out_file)
                #render_cmd += "-f {rl} ".format(rl=render_layer)
                #render_cmd += "-p {proj} ".format(proj=ver_project)
                #render_cmd += "--prman '-t:0 -cwd \"{proj}\" {warn}' ".\dd
                #    format(proj=ver_project, warn=prman_warnings)

                with open(script_path, "w") as script_file:
                    script_file.write("#!/bin/bash\n\n")

                    # XXX these should happen automatically in the queue...
                    script_file.write("source /DPA/wookie/dpa/bash/startup.bash\n")
                    script_file.write("pipeup\n")

                    # 'kick' command has to be added to $PATH
                    # Create env variable for Arnold License server
                    script_file.write("export ADSKFLEX_LICENSE_FILE=@license3.cs.clemson.edu\n\n")

                    script_file.write("# set the ptask version to render\n")
                    script_file.write(dpaset_cmd + "\n")
                    script_file.write("cd " + ver_project + "\n\n")
                    
                    # Add necessary paths to the environment for XGen
                    script_file.write("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/autodesk/maya2016/plug-ins/xgen/lib:/usr/autodesk/maya2016/lib:/opt/solidangle/arnold-maya2016/bin\n\n")

                    # the logic for determining which ass will be generated is
                    # unclear at this point. So we'll build a conditional
                    script_file.write("if [[ -f {lr} ]]; then\n".format(lr=layer_scene))
                    script_file.write("    export ASS_PATH={lr}\n".format(lr=layer_scene))
                    script_file.write("else\n")
                    script_file.write("    export ASS_PATH={sr}\n".format(sr=simple_scene))
                    script_file.write("fi\n")

                    script_file.write("# render!\n")
                    script_file.write(render_cmd + "\n\n")
                    script_file.write("chmod 660 {of}\n\n".format(
                        of=os.path.join(out_dir, 
                            render_layer + "*." + self._file_type)))

                os.chmod(script_path, 0770)

                frame_scripts.append((frame_padded, script_path, out_file))

                cur_op += 1
                progress_dialog.setValue(cur_op)

            frame_tasks = []

            task_id_base = get_unique_id(product_repr_area.spec, dt=now)
            tasks_info_config.add('base_id', task_id_base)

            if self._generate_scenes:
                frame_queue = 'hold'
            else:
                frame_queue = self._render_queue

            # create frame tasks
            for (frame, frame_script, out_file) in frame_scripts:

                progress_dialog.setLabelText(
                    "Submitting frame: " + frame_script)

                task_id = task_id_base + "_" + frame

                if not self._debug_mode:

                    # create tasks, don't actually submit yet
                    create_queue_task(frame_queue, frame_script, task_id,
                        output_file=out_file, submit=False, 
                        log_path=frame_script + '.log')

                    frame_tasks.append((frame, task_id))
                    #
                    #  resubmit frame-by-frame because 
                    #  group submit seems to be occasionally
                    #  having problems.
                    os.system("cqresubmittask {qn} {tid}".format(
                        qn=frame_queue, tid=task_id))

                cur_op += 1
                progress_dialog.setValue(cur_op)

            frame_info = Config()
            for (frame, task_id) in frame_tasks:
                frame_info.add(str(frame), task_id)
            tasks_info_config.add('frame_ids', frame_info)

            # resubmit all at once (workaround for slow individual submissions)
            #
            #  This approach seems to be having problems with the server
            #  communications.  Switch to frame-by-frame resubmit because
            #  that has worked where this fails
            #os.system("cqresubmittask {qn} {tid}".format(
            #    qn=frame_queue, tid=task_id_base))

            if self._generate_scenes:

                progress_dialog.setLabelText("Creating ass generation script...")

                script_path = os.path.join(queue_dir,
                    "{rl}_assgen.sh".format(rl=render_layer))

                with open(script_path, "w") as script_file:
                    script_file.write("#!/bin/bash\n\n")

                    # XXX these should happen automatically in the queue...
                    script_file.write("source /DPA/wookie/dpa/bash/startup.bash\n")
                    script_file.write("pipeup\n\n")

                    script_file.write("# set the ptask version to render\n")
                    script_file.write(dpaset_cmd + "\n")
                    script_file.write("cd " + ver_project + "\n\n")

                    script_file.write("# generate the ass files...\n")

                    current_render_layer = render_layer
                    if render_layer == 'masterLayer':
                        current_render_layer = "defaultRenderLayer"

                    switch_render_layer_cmd = "editRenderLayerGlobals "
                    switch_render_layer_cmd += "-currentRenderLayer \"{rl}\"".\
                        format(rl=current_render_layer)

                    arnold_export_cmd = "arnoldExportAss -f \"{ad}/{fb}_{rl}.ass\" ".\
                        format(ad=scene_dir, fb=file_base, rl=render_layer)
                    arnold_export_cmd += "-startFrame {sf} -endFrame {ef} -frameStep 1 ".\
                        format(li=layer_index, sf=self._frange.start, ef=self._frange.end)
                    arnold_export_cmd += "-mask 255 -lightLinks 1 -shadowLinks 1 -cam {cam} ".\
                        format(cam=self._camera)
                    arnold_export_cmd += "-expandProcedurals "
                    
                    maya_batch_cmd = 'maya2016 -batch -proj "{proj}" '.format(
                        proj=ver_project)
                    maya_batch_cmd += '-command \'{srlc}; {ar}\' '.\
                        format(srlc=switch_render_layer_cmd, ar=arnold_export_cmd)
                    maya_batch_cmd += '-file "{mf}"'.format(mf=maya_file)
                    script_file.write(maya_batch_cmd + "\n")

                    script_file.write(
                        "\n# make sure project dir has group permissions\n")
                    script_file.write(
                        "chmod g+rw {pd} -R\n\n".format(pd=ver_project))

                    # submit the frames to render
                    script_file.write("# Submit frames after ass gen \n")
                    for (frame, frame_task) in frame_tasks:
                        script_file.write("cqmovetask {qn} {tid}\n".format(
                            qn=self._render_queue, tid=frame_task))
                    
                    # changed to move group
                    #script_file.write("cqmovetask {qn} {tid}\n".format(
                        #qn=self._render_queue, tid=task_id_base))

                os.chmod(script_path, 0770)

                # submit the scenegen script
                progress_dialog.setLabelText(
                    "Submitting ass gen: " + script_path)

                task_id = task_id_base + "_asses"
                tasks_info_config.add('assgen_id', task_id)

                if not self._debug_mode:

                    create_queue_task(self._scenegen_queue, script_path, 
                        task_id, output_file=scene_dir, submit=True, 
                        log_path=script_path + '.log')

                cur_op += 1
                progress_dialog.setValue(cur_op)

            cur_op += 1
            progress_dialog.setValue(cur_op)
            progress_dialog.close()

            render_summary.append(
                (render_layer, task_id_base, product_repr, queue_dir))
            
            # For now, disable wrangling tickets. bsddb is causing problems
            # - zshore, 2015-10-23
            # if not self._debug_mode:

            #     # ---- dpa specific queue stuff
            
            #     from cheesyq import DPAWrangler

            #     # create wrangling ticket 
            #     wrangle = DPAWrangler.WrangleRecord(task_id_base)
            #     wrangle.frames = self._frame_list
            #     db = DPAWrangler.GetWranglingDB()
            #     db.set(wrangle.baseId, wrangle)
            #     DPAWrangler.AssignWranglerTask("none", task_id_base)
            wranglecmd = 'cqcreatewrangleitem ' + task_id_base + ' '
            for f in self._frame_list:
                wranglecmd = wranglecmd + str(f) + ' '
            print wranglecmd
            os.system(wranglecmd)
                

            tasks_info_config.write(tasks_info_file)
            os.chmod(tasks_info_file, 0660)

        if not self._debug_mode:

            # send msg...
            msg_title = "Queue submission report: " + \
                now.strftime("%Y/%m/%d %H:%M:%S")
            msg_body = "Submitted the following tasks for " + \
                ptask.spec + ":\n\n"
            msg_body += "  Description: " + self._version_note + "\n"
            msg_body += "  Resolution: " + self._res_str + "\n"
            msg_body += "  File type: " + self._file_type + "\n"
            msg_body += "  Camera: " + self._camera + "\n"
            if self._generate_scenes:
                msg_body += "  Ass gen queue: " + self._scenegen_queue + "\n"
            msg_body += "  Render queue: " + self._render_queue + "\n"
            msg_body += "  Frames: " + str(self._frange) + "\n"
            msg_body += "  Ass directory: " + scene_dir + "\n"
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

        regex = re.compile("defaultRenderLayer[0-9]+")
        render_layers = [x for x in render_layers if not regex.match(x)]

        if "defaultRenderLayer" in render_layers:
            i = render_layers.index("defaultRenderLayer")
            render_layers[i] = "masterLayer"

        print(render_layers)

        return render_layers

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

        start_time = self.session.cmds.getAttr('defaultRenderGlobals.startFrame')
        end_time = self.session.cmds.getAttr('defaultRenderGlobals.endFrame')

        min_time = self.session.cmds.playbackOptions(query=True, minTime=True)
        max_time = self.session.cmds.playbackOptions(query=True, maxTime=True)

        frange_lbl = QtGui.QLabel("Frame range:")
        self._make_frame_range_controls(
            min_time, max_time, start_time, end_time) 

        render_queue_lbl = QtGui.QLabel("Render queue:")
        self._render_queues = QtGui.QComboBox()
        self._render_queues.addItems(self.__class__.RENDER_QUEUES)

        scenegen_queue_lbl = QtGui.QLabel("Scene generation queue:")
        self._scenegen_queues = QtGui.QComboBox()
        self._scenegen_queues.addItems(self.__class__.RIBGEN_QUEUES)

        renderers_lbl = QtGui.QLabel("Renderer:")
        self._renderers = QtGui.QComboBox()
        self._renderers.addItems(self.__class__.RENDERERS)

        sep_layers_lbl = QtGui.QLabel("Separate render layers:")
        self._sep_layers = QtGui.QCheckBox("")
        self._sep_layers.setChecked(True)

        gen_scenes_lbl = QtGui.QLabel("Generate scene (rib/ass) files:")
        self._gen_scenes = QtGui.QCheckBox("")
        self._gen_scenes.setChecked(True)

        rem_scenes_lbl = QtGui.QLabel("Remove existing scenes (rib/ass):")
        self._rem_scenes = QtGui.QCheckBox("")
        self._rem_scenes.setChecked(True)

        debug_lbl = QtGui.QLabel("Debug mode:")
        self._debug = QtGui.QCheckBox("")

        controls_layout.addWidget(version_note_lbl, 0, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._version_note_edit, 0, 1)
        controls_layout.addWidget(frange_lbl, 1, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._frange_stack, 1, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(self._frange_btn, 1, 2, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(file_res_lbl, 2, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._file_res, 2, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(file_types_lbl, 3, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._file_types, 3, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(cameras_lbl, 4, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._cameras, 4, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(scenegen_queue_lbl, 5, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._scenegen_queues, 5, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(render_queue_lbl, 6, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._render_queues, 6, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(renderers_lbl, 7, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._renderers, 7, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(sep_layers_lbl, 8, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._sep_layers, 8, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(gen_scenes_lbl, 9, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._gen_scenes, 9, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(rem_scenes_lbl, 10, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._rem_scenes, 10, 1, QtCore.Qt.AlignLeft)
        controls_layout.addWidget(debug_lbl, 11, 0, QtCore.Qt.AlignRight)
        controls_layout.addWidget(self._debug, 11, 1, QtCore.Qt.AlignLeft)
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

