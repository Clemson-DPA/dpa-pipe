"""The code in here is specific to clemson dpa. 

Reimplement these based on how your facility submits tasks to your queue and 
monkey path. Given more time, I'd like to think of a better way to do this.

"""

# -----------------------------------------------------------------------------

import datetime
import os

from dpa.ptask.area import PTaskArea
from dpa.user import current_username

QUEUE = 'cheesyq'

# -----------------------------------------------------------------------------
def get_unique_id(area_spec="", id_extra=None, dt=None):

    if not dt:
        dt = datetime.datetime.now()

    if id_extra:
        id_extra = "_" + id_extra
    else:
        id_extra = ""

    return "{u}_{t}_{s}{e}".format(
        u=current_username(),
        t=dt.strftime("%Y_%m_%d_%H_%M_%S"),
        s=area_spec.replace('=', '_'),
        e=id_extra,
    )

# -----------------------------------------------------------------------------
def queue_submit_cmd(command, queue_name, output_file=None, id_extra=None,
    dt=None):
    """Create and submit a shell script with the given command."""
    
    ptask_area = PTaskArea.current()
    ptask_area.provision(QUEUE)
    script_dir = ptask_area.dir(dir_name=QUEUE)

    unique_id = get_unique_id(ptask_area.spec, id_extra=id_extra, dt=dt)

    script_name = unique_id + '.sh'
    log_name = unique_id + '.log'

    script_path = os.path.join(script_dir, script_name)
    log_path = os.path.join(script_dir, log_name)

    with open(script_path, "w") as script_file:
        script_file.write("#!/bin/bash\n")
        script_file.write(command + "\n") 
        script_file.write("chmod 660 " + output_file + "\n")

    os.chmod(script_path, 0770)

    create_queue_task(queue_name, script_path, unique_id, 
        output_file=output_file, submit=True, log_path=log_path)

# -----------------------------------------------------------------------------
def create_queue_task(queue_name, script_path, unique_id, output_file=None,
    submit=True, log_path=None):

    # ---- submit to the queue

    from cheesyq import DPACheesyQ, DPADataLibrary, DPACheesyQTasks

    data_lib = DPADataLibrary.DjangoLibrary(None)

    render_task = DPACheesyQ.RenderTask()
    render_task.taskid = unique_id

    if log_path:
        render_task.logFileName = log_path

    if output_file:
        render_task.outputFileName = output_file
        render_task.outputLocation = os.path.dirname(output_file)

    data_lib.set(render_task.taskid, render_task)
    render_task.addTask(script_path)

    if submit:
        os.system("cqresubmittask {qn} {tid}".format(
            qn=queue_name,
            tid=render_task.taskid
        ))
            
        print "Submitted task: " + str(render_task.taskid)

