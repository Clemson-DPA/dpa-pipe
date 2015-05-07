
from PySide import QtCore, QtGui

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.ptask.area import PTaskArea
from dpa.ui.app.session import SessionActionDialog
from dpa.ui.icon.factory import IconFactory
        
# -----------------------------------------------------------------------------

FAIL_ICON_URI = "icon:///images/icons/warning_32x32.png"
FAIL_OPTIONS_CONFIG = "config/ui/actions/fail.cfg"

# -----------------------------------------------------------------------------
class FailDialog(SessionActionDialog):
    
    # -------------------------------------------------------------------------
    def __init__(self):

        ptask_area = PTaskArea.current()
        options_config = ptask_area.config(FAIL_OPTIONS_CONFIG,
            composite_ancestors=True)

        icon_path = IconFactory().disk_path(FAIL_ICON_URI)

        super(FailDialog, self).__init__(
            title='Failure Report',
            options_config=options_config,
            icon_path=icon_path,
            action_button_text='Submit',
            modal=False,
        )

    # -------------------------------------------------------------------------
    def accept(self):

        # handles closing the dialog
        super(FailDialog, self).accept()

        try:
            fail_action_cls = ActionRegistry().get_action('fail')
            fail_action = fail_action_cls(**self.options.value)
            fail_action()
        except ActionError as e:
            error_dialog = QtGui.QErrorMessage(self.parent())
            error_dialog.setWindowTitle('DPA Fail Failure')
            error_dialog.showMessage(
                "There was an error submitting the fail message:<br><br>" + \
                str(e)
            )
            
