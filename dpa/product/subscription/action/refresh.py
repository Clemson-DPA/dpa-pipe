
import os
import shutil

from dpa.action import Action, ActionError, ActionAborted
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask.spec import PTaskSpec
from dpa.ptask.version import PTaskVersion, PTaskVersionError
from dpa.shell.output import Output, Style

# -----------------------------------------------------------------------------
class SubscriptionRefreshAction(Action):
    """Refresh subscriptions for the supplied ptask."""

    name = "refresh"
    target_type = "subs"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):
        """List subscriptions for the supplied ptask."""

        parser.add_argument(
            "ptask", 
            nargs="?", 
            default=".",
            help="The ptask to reload."
        )

    # -------------------------------------------------------------------------
    def __init__(self, ptask):

        super(SubscriptionRefreshAction, self).__init__(ptask)
        self._ptask = ptask

    # -------------------------------------------------------------------------
    def execute(self):

        print ""

        import_dir = self._prep_import_dir()

        for sub in self.ptask_version.subscriptions:
            self._link_sub(sub, app='global')

        print ""
            
        # TODO later:
        # transfer subs that aren't local
        # for each app directory in ptask version area
        # get app instance
        # give app instance list of subscriptions to sanitize
        # app is responsible for building it's own import area with sanitized subs
        
    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):

        if not isinstance(self.ptask, PTask):

            cur_spec = PTaskArea.current().spec
            full_spec = PTaskSpec.get(self.ptask, relative_to=cur_spec)

            # try to get a ptask instance from the db
            try:
                ptask = PTask.get(full_spec)
            except PTaskError as e:
                # fall back to the input spec
                try:
                    ptask = PTask.get(self.spec)
                except PTaskError:
                    raise ActionError(
                        'Could not determine ptask from: "{s}"'.format(
                            s=self.spec)
                    )

            self._ptask = ptask

        self._ptask_version = self.ptask.latest_version
                    
    # -------------------------------------------------------------------------
    def verify(self):

        prompt_str = "\nRefresh subscriptions for " + Style.bright + \
            self.ptask.spec + Style.reset + " version " + Style.bright + \
            self.ptask_version.number_padded + Style.reset + "\n"
        if not Output.prompt_yes_no(prompt_str):
            raise ActionAborted("User chose not to proceed.")

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

    # -------------------------------------------------------------------------
    @property
    def ptask_version(self):    
        return self._ptask_version

    # -------------------------------------------------------------------------
    def _prep_import_dir(self):

        area = PTaskArea(self.ptask.spec)
        import_dir = area.dir(dir_name="import", verify=False, path=True)

        if os.path.exists(import_dir):
            print "Cleaning up existing import directory."
            try:
                shutil.rmtree(import_dir)
            except Exception as e:
                raise ActionError("Failed to remove old import dir: " + str(e))

        global_import_dir = os.path.join('import', 'global')

        try:
            print "Provisioning new import directory."
            area.provision('import')
            area.provision(global_import_dir)
        except PTaskAreaError as e:
            raise ActionError(
                "Failed to provision global import directory: " + str(e))

        return area.dir(dir_name=global_import_dir, path=True)

    # -------------------------------------------------------------------------
    def _link_sub(self, sub, app):

        area = PTaskArea(self.ptask.spec)

        product_ver = sub.product_version
        product_ver_area = PTaskArea(product_ver.spec)
        product_ver_path = product_ver_area.path

        product = product_ver.product

        product_ver_import_dir = os.path.join('import', app, product.name)
            
        try:
            area.provision(product_ver_import_dir)
        except PTaskAreaError as e:
            raise ActionError(
                "Failed to provision product import dir: " + str(e))
        
        link_name = os.path.join(area.path,
            product_ver_import_dir, product.category)

        print "Creating subscription {a} link for: {pv}".format(
            a=app, pv=product_ver.spec)

        os.symlink(product_ver_path, link_name)

