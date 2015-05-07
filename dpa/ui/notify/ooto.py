
from PySide import QtCore, QtGui

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.ptask.area import PTaskArea
from dpa.ui.app.session import SessionActionDialog
from dpa.ui.icon.factory import IconFactory
        
# -----------------------------------------------------------------------------

OOTO_ICON_URI = "icon:///images/icons/ooto_32x32.png"
OOTO_OPTIONS_CONFIG = "config/ui/actions/ooto.cfg"

# -----------------------------------------------------------------------------
class OotoDialog(SessionActionDialog):
    
    # -------------------------------------------------------------------------
    def __init__(self):

        ptask_area = PTaskArea.current()
        options_config = ptask_area.config(OOTO_OPTIONS_CONFIG,
            composite_ancestors=True)

        icon_path = IconFactory().disk_path(OOTO_ICON_URI)

        super(OotoDialog, self).__init__(
            title='Out Of The Office (OOTO)',
            options_config=options_config,
            icon_path=icon_path,
            action_button_text='Submit',
            modal=False,
        )

    # -------------------------------------------------------------------------
    def accept(self):

        # handles closing the dialog
        super(OotoDialog, self).accept()

        try:
            ooto_action_cls = ActionRegistry().get_action('ooto')
            ooto_action = ooto_action_cls(**self.options.value)
            ooto_action()
        except ActionError as e:
            error_dialog = QtGui.QErrorMessage(self.parent())
            error_dialog.setWindowTitle('DPA OOTO Failure')
            error_dialog.showMessage(
                "There was an error submitting the ooto message:<br><br>" + \
                str(e)
            )
            
