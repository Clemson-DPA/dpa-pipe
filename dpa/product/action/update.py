# -----------------------------------------------------------------------------

from dpa.action import Action, ActionError, ActionAborted
from dpa.notify import Notification
from dpa.shell.output import Output, Style, Fg
from dpa.product import Product, ProductError
from dpa.product.version import ProductVersion, ProductVersionError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec
from dpa.user import User

# -----------------------------------------------------------------------------

LATEST_VERSION = "-1"

# -----------------------------------------------------------------------------
class ProductUpdateAction(Action):
    """Update a product's state."""

    name = "update"
    target_type = "product"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):
        
        parser.add_argument(
            "spec",
            nargs="?",
            default="",
            help="Print info for this product spec.",
        )

        # ---- publish/unpublish

        parser.add_argument(
            "-p", "--publish",
            nargs='?',
            const=LATEST_VERSION,
            default=None,
            metavar="<v>,<v>,<v>...",
            type=str,
            help="Publish version(s) of this product. Default is latest.",
        )

        parser.add_argument(
            "-u", "--unpublish",
            nargs='?',
            const=LATEST_VERSION,
            default=None,
            metavar="<v>,<v>,<v>...",
            type=str,
            help="Unpublish version(s) of this product. Default is latest.",
        )

        # ---- publish/unpublish

        parser.add_argument(
            "-d", "--deprecate",
            nargs='?',
            const=LATEST_VERSION,
            default=None,
            metavar="<v>,<v>,<v>...",
            type=str,
            help="Deprecate version(s) of this product. Default is latest.",
        )

        parser.add_argument(
            "--undeprecate",
            nargs='?',
            const=LATEST_VERSION,
            default=None,
            metavar="<v>,<v>,<v>...",
            type=str,
            help="Undeprecate version(s) of this product. Default is latest.",
        )

        # ---- official/no official

        official_group = parser.add_mutually_exclusive_group()

        official_group.add_argument(
            "-o", "--official",
            nargs='?',
            default=None,
            const=LATEST_VERSION,
            metavar="<v>",
            type=str,
            help="Official a version of this product. Default is latest.",
        )

        official_group.add_argument(
            "-n", "--noofficial",
            action="store_true",
            help="Set this product to have no official version.",
        )

    # -------------------------------------------------------------------------
    def __init__(self, spec, publish=None, unpublish=None, official=None, 
        noofficial=None, deprecate=None, undeprecate=None):

        super(ProductUpdateAction, self).__init__(spec, publish=publish, 
            unpublish=unpublish, official=official, noofficial=noofficial,
            deprecate=None, undeprecate=None,
        )

        self._spec = spec
        self._publish = publish
        self._unpublish = unpublish
        self._official = official
        self._noofficial = noofficial
        self._deprecate = deprecate
        self._undeprecate = undeprecate

    # -------------------------------------------------------------------------
    def execute(self):
        
        updates = {}
        versions = {}

        if self.publish: 
            for ver in self.publish:
                versions[ver.spec] = ver
                data = updates.setdefault(ver.spec, {})
                data['published'] = True

        if self.unpublish: 
            for ver in self.unpublish:
                versions[ver.spec] = ver
                data = updates.setdefault(ver.spec, {})
                data['published'] = False

        if self.deprecate: 
            for ver in self.deprecate:
                versions[ver.spec] = ver
                data = updates.setdefault(ver.spec, {})
                data['deprecated'] = True

        if self.undeprecate: 
            for ver in self.undeprecate:
                versions[ver.spec] = ver
                data = updates.setdefault(ver.spec, {})
                data['deprecated'] = False

        if updates:
            for (ver_spec, data) in updates.iteritems():
                print "\nUpdating: " + Style.bright + ver_spec + Style.normal
                version = versions[ver_spec]
                for (key, value) in data.iteritems():
                    print "  " + key + "=" + str(value)
                version.update(**data)

        if self.official:
            self.product.set_official(self.official)
            print "\nUpdated: {b}{s}{n}".format(
                    b=Style.bright,
                    s=self.official.spec,
                    n=Style.normal,
            )
            print "  officialed"
        elif self.noofficial:
            print "\nUpdated: {b}removed official version.{n}".format(
                b=Style.bright,
                n=Style.normal,
            )
            self.product.clear_official()

        print "\nDone.\n"

    # -------------------------------------------------------------------------
    def notify(self):

        # XXX db intensive. revisit at some point
        
        # for now, only alert on publish/official/deprecate 
        if not self.publish and not self.official and not self.deprecate:
            return

        ptasks_to_notify = []

        msg = "A product you may be using has been updated:\n\n"
        msg += "PRODUCT: " + self.product.spec + "\n\n"

        if self.official:
            
            product = self.official.product
            ptasks_to_notify.extend(product.dependent_ptasks)
            msg += "NOW OFFICIAL: " + self.official.number_padded + " - " + \
                self.official.release_note + "\n"

        if self.publish:
            
            for ver in self.publish:
                product = ver.product
                ptasks_to_notify.extend(product.dependent_ptasks)
                msg += "NOW PUBLISHED: " + ver.number_padded + " - " + \
                    ver.release_note + "\n"

        if self.deprecate:

            for ver in self.deprecate:
                product = ver.product
                ptasks_to_notify.extend(product.dependent_ptasks)
                msg += "NOW DEPRECATED: " + ver.number_padded + " - " + \
                    ver.release_note + "\n"

        msg += "\nYou should update your subscriptions accordingly."

        subject = "Product Update: " + self.product.spec
        sender = User.current().email
    
        # TODO: the recipients should be creators of versions subscribed 
        recipients = set([p.creator.email for p in ptasks_to_notify])

        # no need to send if there are no ptask creators to notify.
        if recipients:
            notification = Notification(subject, msg, list(recipients),
                sender=sender)
            notification.send_email()

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):

        cur_spec = PTaskArea.current().spec
        full_spec = PTaskSpec.get(self.spec, relative_to=cur_spec)

        product = None
        if full_spec:
            try:
                product = Product.get(full_spec)
            except ProductError as e:
                # fall back to input spec
                try:
                    product = Product.get(self.spec)
                except ProductError:
                    raise ActionError(
                        'Could not determine product from: "{s}"'.format(
                            s=self.spec
                        )
                    )
        if product:
            self._product = product
        else:
            raise ActionError(
                'Could not determine product from: "{s}"'.format(
                    s=self.spec
                )
            )

        if self.publish:
            vers = self._nums_to_versions(self.publish)
            self._publish = [v for v in vers if not v.published]

        if self.unpublish:
            vers = self._nums_to_versions(self.unpublish)
            self._unpublish = [v for v in vers if v.unpublish]

        if self.deprecate:
            vers = self._nums_to_versions(self.deprecate)
            self._deprecate = [v for v in vers if not v.deprecated]

        if self.undeprecate:
            vers = self._nums_to_versions(self.undeprecate)
            self._undeprecate = [v for v in vers if v.deprecated]

        if self.official:
            vers = self._nums_to_versions(self.official)
            if len(vers) > 1:
                raise ActionError("Can't official more than one version.")
            to_official = vers[0]
            if to_official.number == self.product.official_version_number:
                raise ActionError(
                    "Version {v} of '{p}' is already official.".format(
                        v=to_official.number,
                        p=self.product.spec,
                    )
                )
            if not to_official.published:
                if not self.publish:
                    self._publish = [to_official]
                else:
                    self._publish.append(to_official)
            self._official = to_official

        if self.publish and self.unpublish:
            overlap = set([v.spec for v in self.publish]).intersection(
                set([v.spec for v in self.unpublish]))
            if len(overlap) > 0:
                raise ActionError(
                    "Can't publish and unpublish the same versions.")

        if self.deprecate and self.undeprecate:
            overlap = set([v.spec for v in self.deprecate]).intersection(
                set([v.spec for v in self.undeprecate]))
            if len(overlap) > 0:
                raise ActionError(
                    "Can't deprecate and undeprecate the same versions.")

        # XXX publish if not already when officialing
        # XXX can't official a deprecated version
        # XXX can't deprecate the official version
        # XXX can't unpublish something that has subscribers
        # XXX add active to subscription model

        if (self.publish is None and 
            self.unpublish is None and
            self.deprecate is None and
            self.undeprecate is None and
            self.official is None and
            self.noofficial is False):
            raise ActionError("No actions to perform.")

    # -------------------------------------------------------------------------
    def verify(self):

        if (not self.publish and not self.unpublish and not self.deprecate and
            not self.undeprecate and not self.official and not self.noofficial):
            raise ActionAborted("No updates to perform.")

        print "\nProduct: {b}{s}{n}\n".format(
            b=Style.bright,
            s=self.product.spec,
            n=Style.normal,
        )

        if self.publish:
            self._version_table(self.publish, title="Publish")
        if self.unpublish:
            self._version_table(self.unpublish, title="Un-publish")
        if self.deprecate:
            self._version_table(self.deprecate, title="Deprecate")
        if self.undeprecate:
            self._version_table(self.undeprecate, title="Un-deprecate")
        if self.official:
            self._version_table([self.official], title="Official")
        if self.noofficial:
            print "{o}: {b}{m}{n}\n".format(
                o="No official",
                b=Style.bright,
                m="This product will have no official versions.",
                n=Style.normal,
            )

        if not Output.prompt_yes_no(Style.bright + "Update" + Style.reset):
            raise ActionAborted("User chose not to proceed.")

    # -------------------------------------------------------------------------
    @property
    def spec(self):
        return self._spec

    # -------------------------------------------------------------------------
    @property
    def product(self):
        return self._product

    # -------------------------------------------------------------------------
    @property
    def publish(self):
        return self._publish

    # -------------------------------------------------------------------------
    @property
    def unpublish(self):
        return self._unpublish

    # -------------------------------------------------------------------------
    @property
    def deprecate(self):
        return self._deprecate

    # -------------------------------------------------------------------------
    @property
    def undeprecate(self):
        return self._undeprecate

    # -------------------------------------------------------------------------
    @property
    def official(self):
        return self._official

    # -------------------------------------------------------------------------
    @property
    def noofficial(self):
        return self._noofficial

    # -------------------------------------------------------------------------
    def _nums_to_versions(self, nums):

        product_vers = None

        versions = []
        for num in nums.split(","):
            if num is LATEST_VERSION:

                if not product_vers:
                    product_vers = self.product.versions
                    product_vers.sort(key=lambda v: v.number)
                
                versions.append(product_vers[-1])
            elif isinstance(num, ProductVersion) and num.product == self.product:
                versions.append(num)
            else:
                try:
                    matches = ProductVersion.list(
                        product=self.product.spec,
                        number=num
                    )
                except ProductVersionError:
                    raise ActionError(
                        "Could not find a version {n} for '{s}'".format(
                            n=num, s=self.product.spec
                        )
                    )
                else:
                    if len(matches) != 1:
                        raise ActionError(
                            "Could not find a version {n} for '{s}'".format(
                                n=num, s=self.product.spec
                            )
                        )
                    versions.append(matches[0])

        return versions

    # -------------------------------------------------------------------------
    def _version_table(self, versions, title='Versions'):

        number = title
        note = "Release note"
        reps = "Reps"
        creator = "Creator"
        created = "Created"

        output = Output()
        output.vertical_padding = 0
        output.vertical_separator = None
        output.table_header_separator="-"
        output.header_names = [
            number,
            note,
            reps,
            creator,
            created,
        ]

        output.set_header_alignment({
            number: "right",
        })

        output.set_header_colors({
            number: Style.bright,
        })

        for version in sorted(versions, key=lambda v: v.number):

            output.add_item(
                {
                    number: version.number_padded,
                    note: version.release_note,
                    reps: _representations(version),
                    creator: version.creator_username,
                    created: _datetime_format(version.created),
                },
            )

        output.dump(output_format='table')

        print ""

# -----------------------------------------------------------------------------
def _datetime_format(datetime):
    return datetime.strftime("%Y/%m/%d %H:%M:%S")

# -----------------------------------------------------------------------------
def _representations(version):

    reps = []
    for rep in version.representations:
        rep_str = rep.spec.replace(version.spec, "")
        reps.append(rep_str.lstrip("=").rstrip("=none"))
    
    return ",".join(reps)

