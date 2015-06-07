"""Check/Update subscriptions of the supplied ptask."""
from collections import defaultdict

from PySide import QtCore, QtGui

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea
from dpa.ui.app.session import SessionActionDialog
from dpa.ui.icon.factory import IconFactory
from dpa.app.session import SessionRegistry
        
# -----------------------------------------------------------------------------

VERSION_ICON_URI = "icon:///images/icons/import_32x32.png"
VERSION_OPTIONS_CONFIG = "config/product/subscription/update.cfg"

# -----------------------------------------------------------------------------
class ProductSubscriptionUpdateDialog(SessionActionDialog):
    
    # -------------------------------------------------------------------------
    def __init__(self):

        self._ptask_area = PTaskArea.current()
        options_config = self._ptask_area.config(VERSION_OPTIONS_CONFIG,
            composite_ancestors=True)

        self.check_subscriptions()

        if 'outdated' in self.sublist:
            options_config['options']['outdated_subs'].set('choices', 
                self.sublist['outdated'].keys())

        if 'unofficial' in self.sublist:
            options_config['options']['unofficial_subs'].set('choices', 
                self.sublist['unofficial'].keys())

        if 'current' in self.sublist:
            options_config['options']['current_subs'].set('choices', 
                self.sublist['current'].keys())

        try:
            self._ptask = PTask.get(self._ptask_area.spec)
        except PTaskError as e:
            error_dialog = QtGui.QErrorMessage(self)
            error_dialog.setWindowTitle('Subscription Update Failure')
            error_dialog.showMessage("Unable to update subscriptions.")
            return

        icon_path = IconFactory().disk_path(VERSION_ICON_URI)

        super(ProductSubscriptionUpdateDialog, self).__init__(
            title='Update Existing Subscriptions',
            options_config=options_config,
            icon_path=icon_path,
            action_button_text='Update',
            modal=False,
        )

    # -------------------------------------------------------------------------
    def accept(self):
        print "before confirm"

        if not self._confirm():
            return 

        # Just like in PTaskVersionDialog, this needs to 
        # Call the session's reload()-like feature (should be written)
        # Necessary for programs like Mari, not necessarily Maya

        # handles closing the dialog
        super(ProductSubscriptionUpdateDialog, self).accept()

        try:
            if len(self.updatelist) > 0:
                version_action_cls = ActionRegistry().get_action('update', 'subs')
                version_action = version_action_cls(self._ptask, self.updatelist['subs'][0])
                version_action()
        except ActionError as e:
            error_dialog = QtGui.QErrorMessage(self.parent())
            error_dialog.setWindowTitle('Update Subscription Failure')
            error_dialog.showMessage(
                "There was an error updating the subscriptions."
            )
        else:
            QtGui.QMessageBox.question(self, "Updating Subscriptions Successful",
                "Updating subscriptions was successful.",
                buttons=QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok,
                defaultButton=QtGui.QMessageBox.NoButton,
            )
            
    # -------------------------------------------------------------------------
    def _confirm(self):
        self._to_update = defaultdict(dict)
        self._to_update['subs'] = []

        for pspec in self.options.value['outdated_subs']:
            self._to_update['subs'].append(self.sublist['outdated'][pspec])

        confirm_message = """
            Confirm subscription update:<br>
            
            <table>
                <tr>
                    <td align="left">Product Spec:&nbsp;&nbsp;</td>
                    <td align="left"><b>Version&nbsp;&nbsp;</b></td>
                    <td align="left"><b>New Version</b></td>
                </tr>
        """.format(
            ptask=self._ptask.spec,
        )

        i = 0
        for spec in self.options.value.outdated_subs:
            to_version = self.updatelist['subs'][0][i].product_version.product.official_version
            if not to_version:
                to_version = self.updatelist['subs'][0][i].product_version.product.latest_published().number

            cur_version = self.updatelist['subs'][0][i].product_version.number
            confirm_message += """
                <tr>
                    <td align="left">{k} :&nbsp;&nbsp;</td>
                    <td align="left"><b>{v} &nbsp;&nbsp;</b></td>
                    <td align="left"><b>{nv}</b></td>
                </tr>
            """.format(
                k=spec,
                v=cur_version,
                nv=to_version
            )
            i += 1

        confirm_message += """
            </table><br><br>
            This will also refresh your import directory and attempt to reload.<br><br>
            <b>Update Subscriptions?</b>
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

            
    # -------------------------------------------------------------------------
    def check_subscriptions(self):
        sublist = defaultdict(dict)

        # get existing subscriptions, exclude deprecated
        for sub in SessionRegistry().current().ptask_version.subscriptions:
            sub_prod = sub.product_version.product

            if sub.product_version.number == sub_prod.latest_published().number:
                sublist['current'][sub_prod.spec] = [sub]

                if sub.product_version.number != sub_prod.official_version:
                    sublist['unofficial'][sub_prod.spec] = [sub]
            else:
                sublist['outdated'][sub_prod.spec] = [sub]

                if sub.product_version.number != sub_prod.official_version:
                    sublist['unofficial'][sub_prod.spec] = [sub]

        self._sublist = sublist

    #  -------------------------------------------------------------------------
    @property
    def sublist(self):
        if not hasattr(self, '_sublist'):
            return defaultdict(dict)

        return self._sublist

    #  -------------------------------------------------------------------------
    @property
    def updatelist(self):
        if not hasattr(self, '_to_update'):
            return defaultdict(dict)

        return self._to_update
