
import nuke

from dpa.ptask.area import PTaskArea
from dpa.ui.icon.factory import IconFactory

from dpa.nuke.nodes import add_commands

# -----------------------------------------------------------------------------

NUKE_TOOLBAR_CONFIG = 'config/nuke/toolbars.cfg'

# -----------------------------------------------------------------------------
def load_toolbars():
    """Load all custom toolbars via config files."""

    ptask_area = PTaskArea.current()
    nuke_toolbar_config = ptask_area.config(
        config_file=NUKE_TOOLBAR_CONFIG, composite_ancestors=True)

    for (toolbar_name, toolbar_config) in nuke_toolbar_config.iteritems():

        toolbar = nuke.toolbar(toolbar_name)
        for (item_key, item_config) in toolbar_config.iteritems():

            name = item_config.get('label', item_key)
            command = item_config.get('command', "print 'No op'")
            icon = item_config.get('image', None)
            tooltip = item_config.get('annotation', "")

            if icon:
                icon = IconFactory().disk_path(icon)

            toolbar.addCommand(name=name, command=command, icon=icon,
                tooltip=tooltip)

# -----------------------------------------------------------------------------

load_toolbars()

print "Loading DPA Nuke nodes..."
add_commands()

