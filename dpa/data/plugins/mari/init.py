# Mari startup code. If MARI_SCRIPT_PATH points to this file's parent directory,
# then this file will run automatically. This code will act as a broker for 
# importing mari plugins found within the current pipeline context. 

# -----------------------------------------------------------------------------

import imp
import os
import shlex
import subprocess
import sys
import traceback

# -----------------------------------------------------------------------------
def _populate_sys_path():

    # hack to get regular python session's paths. assumes mari python version
    # matches system python version.

    # this is required to prevent the external python process from barfing
    try:
        del os.environ['PYTHONHOME']
    except KeyError:
        pass

    # get the paths from the system python
    cmd = "python -c 'import sys;print sys.path'"
    paths_str = subprocess.Popen(shlex.split(cmd),
        stdout=subprocess.PIPE).communicate()[0]
    paths = eval(paths_str)

    # if path is not in mari's sys path, append it.
    for path in paths:
        if path and path not in sys.path:
            sys.path.append(path)

# -----------------------------------------------------------------------------
def _import_mari_plugins():

    from dpa.ptask.area import PTaskArea

    # first, get the context
    ptask_area = PTaskArea.current()

    # get a list of mari plugin directories
    plugin_dirs = ptask_area.ancestor_paths(
        'plugins/mari', include_install=False)

    for plugin_dir in reversed(plugin_dirs):

        if not os.path.isdir(plugin_dir):
            continue
        
        file_names = os.listdir(plugin_dir)

        for file_name in file_names:

            # only python files
            if not file_name.endswith(".py"):
                continue
            
            full_path = os.path.join(plugin_dir, file_name)

            module_name = 'mari_plugin_' + file_name.replace(".", "_")

            try:
                module = imp.load_source(module_name, full_path)
            except Exception as e:
                print "Unable to load mari plugin: " + full_path    
                traceback.print_exc()                

# -----------------------------------------------------------------------------

# get the python path setup
_populate_sys_path()

# register MariSession with SessionFactory
print "Loading MariSession"
import dpa.mari.session

# register Mari Entityies
print "Loading Mari Entities"
import dpa.mari.entity.maps
import dpa.mari.entity.geom

# do the loading
print "Loading DPA mari plugins..."
_import_mari_plugins()

