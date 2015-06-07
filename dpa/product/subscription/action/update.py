
# -----------------------------------------------------------------------------

from collections import defaultdict

from dpa.action import Action, ActionError, ActionAborted
from dpa.action.registry import ActionRegistry
from dpa.product.subscription import (
    ProductSubscription, ProductSubscriptionError
)
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec
from dpa.ptask.version import PTaskVersion
from dpa.shell.output import Output, Style

# -----------------------------------------------------------------------------
class SubscriptionUpdateAction(Action):

    name = "update"
    target_type = "subs"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        # ptask
        parser.add_argument(
            "ptask", 
            nargs="?",
            default=".",
            help="Update subs for this ptask spec.",
        )

        # ptask version
        parser.add_argument(
            "-v", "--version",
            type=int,
            help="The version of the ptask subscribing to the product. " + \
                 "Default is the current version.",
        )

        # sub ids 
        parser.add_argument(
            "-s", "--subs",
            nargs="*",
            help="Apply updates for supplied subscription ids or product specs.",
        )

        # refresh disk
        parser.add_argument(
            "--no-refresh",
            action="store_true",
            help="Don't update the import directory on disk.",
        )
    
    # -------------------------------------------------------------------------
    def __init__(self, ptask, subs=None, version=None, no_refresh=False):

        super(SubscriptionUpdateAction, self).__init__(ptask, subs=subs,
            version=version)

        self._ptask = ptask
        self._subs = subs
        self._ptask_version = version
        self._no_refresh = no_refresh

    # -------------------------------------------------------------------------
    def execute(self):

        for sub in self._subs:
            
            update_map = self._update_map[sub.id]

            cur_ver = update_map['old']
            new_ver = update_map['new']

            if not new_ver:
                continue

            # unsubscribe from the current version
            try:
               ProductSubscription.delete(
                   self._ptask_version.spec, cur_ver.spec)
            except ProductSubscriptionError as e:
                raise ActionError("Unsubscribe failed: " + str(e))

            # subscribe to the new version
            try:
                sub = ProductSubscription.create(self._ptask_version, new_ver)
            except ProductSubscriptionError as e:
                raise ActionError("Subscribe failed: " + str(e))

        if not self._no_refresh:

            # refresh the subscriptions on disk
            refresh_action_cls = ActionRegistry().get_action('refresh', 'subs')
            if not refresh_action_cls:
                raise ActionError("Could not find sub refresh action.")

            try:
                refresh_action = refresh_action_cls(self.ptask)
                refresh_action.interactive = False
                refresh_action()
            except ActionError as e:
                raise ActionError("Failed to refresh subs on disk: " + str(e))

        if self.interactive:
            print "\nUpdate complete!\n"

    # -------------------------------------------------------------------------
    def validate(self):

        # validate the ptask
        if not isinstance(self._ptask, PTask):
            try:
                cur_spec = PTaskArea.current().spec
                full_spec = PTaskSpec.get(self._ptask, relative_to=cur_spec)
                self._ptask = PTask.get(full_spec)
            except PTaskError:
                raise ActionError("Could not determine ptask from: {p}".format(
                    p=self._ptask))

        # find the version of the ptask to update
        if isinstance(self._ptask_version, PTaskVersion):
            if not self._ptask_version.ptask_spec == self._ptask_spec:
                raise ActionError(
                    "Supplied ptask version doesn't match supplied ptask.")
        elif self._ptask_version:
            matches = PTaskVersion.list(
                ptask=self._ptask.spec, number=self._ptask_version
            )
            if len(matches) != 1:
                raise ActionError(
                    "Unable to find ptask '{p}' at version '{v}'".format(
                        p=self._ptask.spec, v=self._ptask_version
                    )
                )
            else:
                self._ptask_version = matches[0]
        else:
            self._ptask_version = self._ptask.latest_version

        # XXX rule
        
        # don't allow if ptask_version already has published products
        if self._ptask_version.published:
            raise ActionError(
                "Subscriptions can not be modified." + \
                "Version {v} of {p} has published products.".format(
                    v=self._ptask_version.number_padded, 
                    p=self._ptask.spec
                ))

        # XXX

        subs = [] 

        # valdiate the subscriptions to update
        if self._subs:

            # get explicit subs
            for sub in self._subs:

                if isinstance(sub, ProductSubscription):
                    subs.append(sub)
                    continue

                try:
                    sub = int(sub)
                except:
                    raise ActionError("Could not determine sub from: {s}".\
                        format(s=sub))
                else:
                    matches = ProductSubscription.list(id=sub)         
                    if len(matches) != 1:
                        raise ActionError("Unable to identify sub for id: " + \
                            str(sub))
                    else:
                        subs.append(matches[0])

        else:
            # all subs for ptask version
            subs.extend(self._ptask_version.subscriptions)

        self._subs = subs

        update_map = defaultdict(dict)

        for sub in subs:
            
            sub_product_ver = sub.product_version
            
            update_map[sub.id]['old'] = sub_product_ver

            if sub.locked:
                update_map[sub.id]['new'] = None
                update_map[sub.id]['note'] = 'Subscription locked'
                continue 

            if sub_product_ver.is_official:
                update_map[sub.id]['new'] = None
                update_map[sub.id]['note'] = 'Already subscribed to official'
                continue 

            sub_product = sub_product_ver.product

            official_ver = sub_product.official_version

            if official_ver and official_ver.number > sub_product_ver.number:
                update_map[sub.id]['new'] = official_ver
                update_map[sub.id]['note'] = 'Official version'
                continue 

            all_vers = [v for v in sub_product.versions if v.published]
            all_vers.sort(key=lambda v: v.number_padded)

            if all_vers:
                latest_pub = all_vers[-1]
                if latest_pub.number > sub_product_ver.number:
                    update_map[sub.id]['new'] = latest_pub 
                    update_map[sub.id]['note'] = 'Latest published version'
                    continue 
                else:
                    update_map[sub.id]['new'] = None
                    update_map[sub.id]['note'] = 'Already using latest published'
                    continue 
                    
            else:
                update_map[sub.id]['new'] = None
                update_map[sub.id]['note'] = 'No new published versions'
                continue 

        self._update_map = update_map
                    
    # -------------------------------------------------------------------------
    def verify(self):

        product = "Product"
        source = "From"
        current = "Old"
        new = "New"
        note = "Note"

        output = Output()
        output.title = "Subscriptions to update:"
        output.header_names = [
            source,
            product,
            current,
            new,
            note,
        ]

        output.set_header_alignment({
            current: "right",
            new: "right",
        })

        updates = False

        for sub in sorted(self._subs, key=lambda s: s.spec):
            
            update_map = self._update_map[sub.id]
            cur_ver = update_map['old']
            cur_product = cur_ver.product
            new_ver = update_map['new']
            update_note = update_map['note']

            if new_ver:
                updates = True
                new_ver_disp = new_ver.number_padded
            else:
                new_ver_disp = "----"

            output.add_item(
                {
                    source: cur_product.ptask.spec,
                    product: cur_product.name_spec,
                    current: cur_ver.number_padded,
                    new: new_ver_disp,
                    note: update_note,
                },
            )
            
            output.dump(output_format='table')

        if not updates:
            raise ActionAborted("Nothing to update.")

        if not Output.prompt_yes_no(Style.bright + "Update" + Style.reset):
            raise ActionAborted("User chose not to proceed.")

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        
        return self._ptask

    # -------------------------------------------------------------------------
    @property
    def ptask_version(self):
        
        return self._ptask_version

    # -------------------------------------------------------------------------
    @property
    def subs(self):
        
        return self._subs

