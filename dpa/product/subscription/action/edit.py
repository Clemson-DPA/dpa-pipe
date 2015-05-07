
from dpa.action import Action, ActionError, ActionAborted
from dpa.product.subscription import ProductSubscription
from dpa.shell.output import Output, Style

# -----------------------------------------------------------------------------
class SubscriptionEditAction(Action):
    """Edit an existing subscription."""

    name = "edit"
    target_type = "subs"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        # lock
        parser.add_argument(
            "-l", "--lock",
            nargs="+",
            help="Lock the supplied subscription ids to prevent updates.",
        )

        # unlock
        parser.add_argument(
            "-u", "--unlock",
            nargs="+",
            help="Unlock the supplied subscription ids to allow updates.",
        )

    # -------------------------------------------------------------------------
    def __init__(self, lock=False, unlock=False):

        super(SubscriptionEditAction, self).__init__(lock=lock, unlock=unlock)

        self._lock = lock
        self._unlock = unlock

    # -------------------------------------------------------------------------
    def execute(self):

        for sub in self._lock:
            if not sub.locked:
                sub.lock()

        for sub in self._unlock:
            if sub.locked:
                sub.unlock()

        if self.interactive:
            print "\nEdits complete!\n"

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):

        if not self._lock and not self._unlock:
            raise ActionError(
                "Must supply an action to perform (lock, unlock, etc.)")
            
        self._lock = self._ids_to_subs(self._lock)
        self._unlock = self._ids_to_subs(self._unlock)

    # -------------------------------------------------------------------------
    def verify(self):

        if self._lock:
            self._sub_table(self._lock, title="Lock")
        if self._unlock:
            self._sub_table(self._unlock, title="Unlock")

        if not Output.prompt_yes_no(Style.bright + "Edit" + Style.reset):
            raise ActionAborted("User chose not to proceed.")
        
    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

    # -------------------------------------------------------------------------
    @property
    def lock(self):
        return self._lock
    
    # -------------------------------------------------------------------------
    @property
    def unlock(self):
        return self._unlock

    # -------------------------------------------------------------------------
    def _ids_to_subs(self, sub_ids):

        subs = []

        if not sub_ids:
            return subs

        for sub_id in sub_ids:

            if isinstance(sub_id, ProductSubscription):
                subs.append(sub_id)
                continue

            try:
                sub = int(sub_id)
            except:
                raise ActionError("Could not determine sub from: {s}".\
                    format(s=sub_id))
            else:
                matches = ProductSubscription.list(id=sub_id)
                if len(matches) != 1:
                    raise ActionError("Unable to identify sub for id: " + \
                        str(sub_id))
                else:
                    subs.append(matches[0])

        return subs

    # -------------------------------------------------------------------------
    def _sub_table(self, subs, title="Subscriptions"):

        sub_id = "Sub. ID"
        product = "Product"
        subscriber = "Subscriber"

        output = Output()
        output.vertical_padding = 0
        output.vertical_separator = None
        output.table_header_separator="-"
        output.header_names = [
            sub_id,
            product,
            subscriber,
        ]

        output.set_header_alignment({
            sub_id: "right"
        })

        for sub in sorted(subs, key=lambda s: s.spec):
            
            output.add_item(
                {
                    sub_id: str(sub.id).zfill(5),
                    product: sub.product_version_spec,
                    subscriber: sub.ptask_version_spec,
                }
            )

        output.dump(output_format="table")

        print ""
    
