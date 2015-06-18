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
def queue_submit_cmd(command, queue_name, output_dir=None):
    """Create and submit a shell script with the given command."""
    
    ptask_area = PTaskArea.current()
    ptask_area.provision(QUEUE)
    script_dir = ptask_area.dir(dir_name=QUEUE)

    unique_id = "{u}_{t}_{s}".format(
        u=current_username(),
        t=datetime.datetime.now().strftime("%m%d%Y%H%M%S%f"),
        s=ptask_area.spec.replace('=', '_'),
    )
    script_name = unique_id + '.sh'
    log_name = unique_id + '.log'

    script_path = os.path.join(script_dir, script_name)
    log_path = os.path.join(script_dir, log_name)

    with open(script_path, "w") as script_file:
        script_file.write("#!/bin/bash\n")
        script_file.write(command + "\n") 

    os.chmod(script_path, 0770)

    # ---- submit to the queue

    from cheesyq import DPACheesyQ, DPADataLibrary, DPACheesyQTasks

    data_lib = DPADataLibrary.DjangoLibrary(None)

    render_task = DPACheesyQ.RenderTask()
    render_task.taskid = unique_id
    render_task.logFileName = log_path
    render_task.outputFileName = output_dir

    data_lib.set(render_task.taskid, render_task)
    render_task.addTask(script_path)

    print "QUEUE NAME: " + str(queue_name)
    queue_tasks = DPACheesyQTasks.CheesyQTasks(queue_name, "open")
    queue_tasks.pushTask(render_task.taskid)
        
    print "Submitted task: " + str(render_task.taskid)

