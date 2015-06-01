"""Create a new version of the supplied ptask."""

from PySide import QtCore, QtGui

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea
from dpa.ui.app.session import SessionActionDialog
from dpa.ui.icon.factory import IconFactory
        
# -----------------------------------------------------------------------------

VERSION_ICON_URI = "icon:///images/icons/version_32x32.png"
VERSION_OPTIONS_CONFIG = "config/ui/actions/ptask/version.cfg"

# -----------------------------------------------------------------------------
class PTaskVersionDialog(SessionActionDialog):
    
    # -------------------------------------------------------------------------
    def __init__(self):

        self._ptask_area = PTaskArea.current()
        options_config = self._ptask_area.config(VERSION_OPTIONS_CONFIG,
            composite_ancestors=True)

        try:
            self._ptask = PTask.get(self._ptask_area.spec)
        except PTaskError as e:
            error_dialog = QtGui.QErrorMessage(self)
            error_dialog.setWindowTitle('Version Failure')
            error_dialog.showMessage("Unable to determine current ptask.")
            return

        icon_path = IconFactory().disk_path(VERSION_ICON_URI)

        super(PTaskVersionDialog, self).__init__(
            title='Version up',
            options_config=options_config,
            icon_path=icon_path,
            action_button_text='Submit',
            modal=False,
        )

    # -------------------------------------------------------------------------
    def accept(self):

        if not self._confirm():
            return 

        self.session.save()

        # handles closing the dialog
        super(PTaskVersionDialog, self).accept()

        # version up the work area
        try:
            version_action_cls = ActionRegistry().get_action('version', 'work')
            version_action = version_action_cls(self._ptask.spec, **self.options.value)
            version_action()
        except ActionError as e:
            error_dialog = QtGui.QErrorMessage(self.parent())
            error_dialog.setWindowTitle('PTask Version Failure')
            error_dialog.showMessage(
                "There was an error versioning this ptask:<br><br>" + \
                str(e)
            )
        else:
            QtGui.QMessageBox.question(self, "Version Up Success",
                "Version up was successful.",
                buttons=QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok,
                defaultButton=QtGui.QMessageBox.NoButton,
            )
            
    # -------------------------------------------------------------------------
    def _confirm(self):

        confirm_message = """
            Confirm version creation of version: <b>{next_ver}</b>:<br>
            
            <table>
                <tr>
                    <td align="right">PTask :&nbsp;&nbsp;</td>
                    <td align="left"><b>{ptask}</b></td>
                </tr>
        """.format(
            next_ver=self._ptask.next_version_number_padded,
            ptask=self._ptask.spec,
        )

        for (key, val) in self.options.value.iteritems():
            confirm_message += """
                <tr>
                    <td align="right">{k} :&nbsp;&nbsp;</td>
                    <td align="left"><b>{v}</b></td>
                </tr>
            """.format(
                k=key.title(),
                v=val,
            )

        confirm_message += """
            </table><br><br>
            Continuing will save your current session.<br><br>
            <b>Version up?</b>
        """

        # info dialog showing what will be done
        proceed = QtGui.QMessageBox.question(
            self,
            "Version Up Confirmation",
            confirm_message,
            buttons=QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Yes,
            defaultButton=QtGui.QMessageBox.NoButton,
        )

        return proceed == QtGui.QMessageBox.Yes

