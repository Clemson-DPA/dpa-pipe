
from dpa.action import Action, ActionError
from dpa.env.vars import DpaVars
from dpa.shell.output import Output, Style
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec

# -----------------------------------------------------------------------------
class SubscriptionListAction(Action):
    """List subscriptions for the supplied ptask."""

    name = "list"
    target_type = "subs"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):
        """List subscriptions for the supplied ptask."""

        parser.add_argument(
            "spec", 
            nargs="?", 
            default="",
            help="Print info for this ptask spec. First checks relative to " + \
                 "the currently set ptask. If no match is found, checks " + \
                 "relative to the project root.",
        )

        parser.add_argument(
            "-v", "--versions",
            dest="versions",
            nargs="*",
            default=[],
            help="Show subscriptions for the supplied verisons. Default " + \
                 "is current. A list of integers can be supplied for " + \
                 "specific versions, or 'all' for all versions."
        )

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, spec, versions=None):
        super(SubscriptionListAction, self).__init__(spec)
        self._spec = spec
        self._versions = versions

    # -------------------------------------------------------------------------
    def execute(self):

        for version in sorted(self.versions, key=lambda v: v.number):

            subs = version.subscriptions
            sub_count = len(subs)
        
            print "\n{c} {s} for {b}{p}{n}:".format(
                c=str(sub_count),
                s='subsription' if sub_count == 1 else 'subscriptions',
                b=Style.bright,
                p=version.spec,
                n=Style.normal,
            )

            if len(subs) == 0:
                continue

            _subs_table(subs)
    
        print ""

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):

        cur_spec = PTaskArea.current().spec
        full_spec = PTaskSpec.get(self.spec, relative_to=cur_spec)

        # if we're listing the current ptask's subs, and no versions specified
        if cur_spec == full_spec and not self._versions:
            ptask_ver = DpaVars.ptask_version().get()
            if ptask_ver:
                self._versions = [ptask_ver]

        if not self._versions:
            self._versions = ["latest"]

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

        if self._versions == ['latest']:
            versions = [self.ptask.latest_version]
        elif self._versions == ['all']:
            versions = self.ptask.versions
        else:
            self._versions = map(int, self._versions)
            versions = [v for v in self.ptask.versions 
                if v.number in self._versions]

        if len(versions) == 0:
            raise ActionError(
                "No matches found for {p} version: {v}".format(
                    p=ptask.spec,
                    v=Style.bright + str(self._versions) + Style.normal,
                )
            )

        self._versions = versions

    # -------------------------------------------------------------------------
    @property
    def spec(self):
        return self._spec

    # ------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

    # ------------------------------------------------------------------------
    @property
    def versions(self):
        return self._versions

# -------------------------------------------------------------------------
def _subs_table(subs):

    sub_id = "Id"
    product_ver = "Product version" 
    locked = "Locked"

    output = Output()
    output.vertical_padding = 0
    output.vertical_separator = None
    output.table_header_separator = '-'
    output.header_names = [
        sub_id,
        product_ver,
        locked,
    ]

    output.set_header_alignment({
        sub_id: "right",
    })

    for sub in sorted(subs, key=lambda s: s.spec):

        output.add_item(
            {
                sub_id: str(sub.id).zfill(5),
                product_ver: sub.product_version_spec,
                locked: sub.locked,
            },
            color_all=Style.bright,
        )

    output.dump(output_format='table')

