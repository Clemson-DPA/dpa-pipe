
from dpa.action import Action, ActionError, ActionAborted
from dpa.action.registry import ActionRegistry
from dpa.product.subscription import (
    ProductSubscription, 
    ProductSubscriptionError
)
from dpa.shell.output import Output, Style, Fg

# -----------------------------------------------------------------------------
class SubscriptionRemoveAction(Action):
    """Remove an existing subscription."""

    name = "remove"
    target_type = "sub"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        # product
        parser.add_argument(
            "sub_id",
            help="The id of the subscription to remove.",
        )

        # refresh disk
        parser.add_argument(
            "--no-refresh",
            action="store_true",
            help="Don't update the import directory on disk.",
        )

    # -------------------------------------------------------------------------
    def __init__(self, sub_id, no_refresh=False):

        super(SubscriptionRemoveAction, self).__init__(sub_id)

        self._sub_id = sub_id
        self._no_refresh = no_refresh

    # -------------------------------------------------------------------------
    def execute(self):

        try:
            ProductSubscription.delete(
                self.subscription.ptask_version_spec,
                self.subscription.product_version_spec,
            )
        except ProductSubscriptionError as e:
            raise ActionError("Subscription removal failed: " + str(e))
        else:
            if self.interactive:
                print "\nSubscription removed.\n"

        if self._no_refresh:
            return

        # refresh the subscriptions on disk
        refresh_action_cls = ActionRegistry().get_action('refresh', 'subs')
        if not refresh_action_cls:
            raise ActionError("Could not find sub refresh action.")

        try:
            refresh_action = refresh_action_cls(
                self.subscription.ptask_version.ptask)
            refresh_action.interactive = False
            refresh_action()
        except ActionError as e:
            raise ActionError("Failed to refresh subs on disk: " + str(e))

    # -------------------------------------------------------------------------
    def validate(self):

        try:
            self._sub_id = int(self._sub_id)
        except ValueError:
            raise ActionError("Invalid subscription id.")

        # make sure subscription exists
        matches = ProductSubscription.list(id=self._sub_id)
        if len(matches) != 1:
            raise ActionError(
                "Unable to identify subscription for id: " + str(self._sub_id)
            )

        self._subscription = matches[0]

        # make sure subsription is not locked
        if self._subscription.locked:
            raise ActionError("Can't remove locked subscription.")

        # make sure ptask version has no published products
        if self._subscription.ptask_version.published:
            raise ActionError(
                "Can't modify subscriptions. " + \
                "The ptask version has published products."
            )

    # -------------------------------------------------------------------------
    def verify(self):

        ptask_version = self.subscription.ptask_version
        product_version = self.subscription.product_version
        ptask = ptask_version.ptask
        product = product_version.product

        ptask_ver_header = "PTask version"
        product_ver_header = "Unsubscribing from"

        output = Output()
        output.title = "Removig subscription:"
        output.header_names = [
            ptask_ver_header,
            product_ver_header,
        ]

        if product.official_version_number == product_version.number:
            official = Fg.green + "  (official)" + Fg.reset
        else:
            official = ""

        output.add_item(
            {
                ptask_ver_header: ptask_version.spec,
                product_ver_header: product_version.spec + official,
            },
            color_all=Style.bright,
        )

        output.dump()

        if not Output.prompt_yes_no("Unsubscribe"):        
            raise ActionAborted("User chose not to proceed.")

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    @property
    def sub_id(self):
        return self._sub_id

    # -------------------------------------------------------------------------
    @property
    def subscription(self):
        return self._subscription

