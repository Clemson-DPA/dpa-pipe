
# -----------------------------------------------------------------------------

from dpa.action import Action, ActionError, ActionAborted
from dpa.action.registry import ActionRegistry
from dpa.product import Product, ProductError
from dpa.product.version import ProductVersion, ProductVersionError
from dpa.product.subscription import (
    ProductSubscription, 
    ProductSubscriptionError
)
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec
from dpa.ptask.version import PTaskVersion
from dpa.shell.output import Output, Style, Fg

# -----------------------------------------------------------------------------
class SubscriptionCreateAction(Action):
    """Create a new subscription."""

    name = "create"
    target_type = "sub"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        # product
        parser.add_argument(
            "product",
            help="The product to subscribe to.",
        )

        # ptask
        parser.add_argument(
            "ptask",
            nargs="?",
            default="",
            help="The ptask subscribing to the product.",
        )

        # product version
        parser.add_argument(
            "-v", "--version",
            type=int,
            help="The version of the product to subscribe to. " + \
                 "Default is the official version. If no official " + \
                 "version, then the latest published. If no published " + \
                 "versions, the tool will fail."
        )

        # ptask version
        parser.add_argument(
            "--ptask-version",
            type=int,
            help="The version of the ptask subscribing to the product. " + \
                 "Default is the current version.",
        )

        # refresh disk
        parser.add_argument(
            "--no-refresh",
            action="store_true",
            help="Don't update the import directory on disk.",
        )

    # -------------------------------------------------------------------------
    def __init__(self, product, ptask, version=None,
        ptask_version=None, no_refresh=False):

        super(SubscriptionCreateAction, self).__init__(product, ptask,
            version=version, ptask_version=ptask_version)

        self._product = product
        self._ptask = ptask
        self._product_version = version
        self._ptask_version = ptask_version
        self._no_refresh = no_refresh

    # -------------------------------------------------------------------------
    def execute(self):

        try:
            sub = ProductSubscription.create(
                self.ptask_version,
                self.product_version,
            )
        except ProductSubscriptionError as e:
            raise ActionError("Subscription failed: " + str(e))
        else:
            if self.interactive:
                print "\nSubscription created.\n"

        if self._no_refresh:
            return

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

    # -------------------------------------------------------------------------
    def validate(self):

        # need to identify the product version being subscribed to and the 
        # ptask version subscribing to it.

        # get the product
        if not isinstance(self._product, Product):
            try:
                self._product = Product.get(self._product)
            except ProductError:
                raise ActionError(
                    "Unable to find product: " + str(self._product)
                )
        
        # get ptask
        if not isinstance(self._ptask, PTask):
            try:
                cur_spec = PTaskArea.current().spec
                full_spec = PTaskSpec.get(self._ptask, relative_to=cur_spec)
                self._ptask = PTask.get(full_spec)
            except PTaskError:
                raise ActionError("Unable to find ptask: " + str(self._ptask))

        # find the version to subscribe to
        if isinstance(self._product_version, ProductVersion):
            pass
        elif self._product_version:
            matches = ProductVersion.list(
                product=self.product.spec, number=int(self._product_version))
            if len(matches) != 1:
                raise ActionError(
                    "Unable to find product '{p}' at version '{v}'".format(
                        p = self.product.spec, v=self._product_version
                    )
                )
            else:
                self._product_version = matches[0]
        else:
            # get the official version
            official_version = self._product.official_version
            if official_version:
                self._product_version = official_version
            else:
                # get the latest, non-deprecated version
                latest_published = self._product.latest_published()
                if latest_published:
                    self._product_version = latest_published
                else:
                    raise ActionError(
                        "No available versions of product '{p}'".format(
                            p=self._product.spec
                        )
                    )

        # find the version of the ptask doing the subscribing
        if isinstance(self._ptask_version, PTaskVersion):
            pass
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

    
        # XXX the rules below need to be exposed outside of just the create
        # code. UIs, for example, should be able to check these cases before
        # allowing the user to perform actions...

        # if this ptask has any existing published versions, error out
        published = ProductVersion.list(
            ptask_version=self._ptask_version,
            published=True
        )
        if len(published) > 0:
            raise ActionError(
                "Unable to create new subscription. This ptask version " + \
                "already has published product versions.\n" + \
                "You need to version up to modify subscriptions."
            )

        # see if there is an existing subscription:
        self._existing_sub = self._ptask_version.is_subscribed(self._product)
        if (self._existing_sub and 
           (self._existing_sub.product_version_spec == \
            self._product_version.spec)):
            raise ActionError("Subscription already exists!")

        if self._product_version.deprecated:
            raise ActionError(
                "Product version is deprecated. Specify an alternate version."
            )

        # make sure product is published or from same ptask
        if (not self._product_version.published and 
            not self._product.ptask_spec == self._ptask.spec):
            raise ActionError(
                "Product version is not published. Specify a published version."
            )

        # XXX don't allow self subs to products with higher version number

    # -------------------------------------------------------------------------
    def verify(self):

        ptask_ver = "PTask version"
        product_ver = "Subscribing to"

        output = Output()
        output.title = "Creating subscription:"
        output.header_names = [
            ptask_ver,
            product_ver,
        ]

        if self.product.official_version_number == self.product_version.number:
            official = Fg.green + "  (official)" + Fg.reset
        else:
            official = ""

        output.add_item(
            {
                ptask_ver: self.ptask_version.spec,
                product_ver: self.product_version.spec + official,
            },
            color_all=Style.bright,
        )

        output.dump()

        if not Output.prompt_yes_no("Subscribe"):        
            raise ActionAborted("User chose not to proceed.") 

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    @property
    def existing_sub(self):
        return self._existing_sub

    # -------------------------------------------------------------------------
    @property
    def product(self):
        return self._product

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

    # -------------------------------------------------------------------------
    @property
    def product_version(self):
        return self._product_version

    # -------------------------------------------------------------------------
    @property
    def ptask_version(self):
        return self._ptask_version

