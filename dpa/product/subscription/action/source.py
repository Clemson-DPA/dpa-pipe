import re

from dpa.action import Action, ActionError, ActionAborted
from dpa.action.registry import ActionRegistry
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec
from dpa.ptask.version import PTaskVersion
from dpa.shell.output import Output, Style, Fg

# -----------------------------------------------------------------------------
class SubscriptionSourceAction(Action):
    """Source subscriptions from another ptask."""

    name = "source"
    target_type = "subs"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        # source ptask
        parser.add_argument(
            "ptask",
            help="The ptask to source subs from.",
        )

        # subs string to match
        parser.add_argument(
            "match_str",
            help="String to match against product specs to source. " + \
                "Use '%%' as a wildcard"
        )

        # ptask version
        parser.add_argument(
            "-v", "--version",
            type=int,
            help="The version of the ptask to source subs from.",
        )

    # -------------------------------------------------------------------------
    def __init__(self, ptask, match_str, version=None):

        super(SubscriptionSourceAction, self).__init__(ptask, match_str,
            version=None)

        self._ptask = ptask
        self._match_str = match_str
        self._version = version

    # -------------------------------------------------------------------------
    def execute(self):

        # ---- get the actions we need

        create_action_cls = ActionRegistry().get_action('create', 'sub')
        if not create_action_cls:
            raise ActionError("Could not find create sub action.")

        refresh_action_cls = ActionRegistry().get_action('refresh', 'subs')
        if not refresh_action_cls:
            raise ActionError("Could not find sub refresh action.")

        # ---- use the create sub action to create/replace the subs

        errors = []

        for sub in self.subs_to_source:

            product_version = sub.product_version
            product = product_version.product

            try:
                create_action = create_action_cls(
                    product=product,
                    ptask=self.current_ptask,
                    version=product_version,
                    ptask_version=self.current_ptask_version,
                    no_refresh=True
                )
                create_action.interactive = False
                create_action()
            except ActionError as e:
                errors.append(e)

        # ---- refresh the subs' import dirs

        try:
            refresh_action = refresh_action_cls(self.current_ptask)
            refresh_action.interactive = False
            refresh_action()
        except ActionError as e:
            raise ActionError("Failed to refresh subs on disk: " + str(e))

        # ---- spit some errors if need be

        if errors:
            raise ActionError("Errors occurred during source:\n" + \
                "\n    ".join([str(e) for e in errors]))

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):

        # current ptask/version
        try:
            area = PTaskArea.current()
            self._current_ptask = PTask.get(area.spec)
            self._current_ptask_version = self._current_ptask.latest_version
        except PTaskError:
            raise ActionError("Unable to find ptask: " + str(self._ptask))

        # source ptask
        if not isinstance(self._ptask, PTask):
            try:
                cur_spec = PTaskArea.current().spec
                full_spec = PTaskSpec.get(self._ptask, relative_to=cur_spec)
                self._ptask = PTask.get(full_spec)
            except PTaskError:
                raise ActionError("Unable to find ptask: " + str(self._ptask))

        # source ptask version
        if isinstance(self._version, PTaskVersion):
            pass
        elif self._version:
            matches = PTaskVersion.list(
                ptask=self._ptask.spec, number=self._version
            )
            if len(matches) != 1:
                raise ActionError(
                    "Unable to find ptask '{p}' at version '{v}'".format(
                        p=self._ptask.spec, v=self._version
                    )
                )
            else:
                self._version = matches[0]
        else:
            self._version = self._ptask.latest_version

        # source subs
        self._match_str = self._match_str.replace("%", ".*")

        all_subs = self._version.subscriptions
        self._subs_to_source = []
        for sub in all_subs:
            if re.search(self._match_str, sub.product_version_spec):
                self._subs_to_source.append(sub)

        if not self._subs_to_source:
            raise ActionAborted("No subscriptions to source.")

    # -------------------------------------------------------------------------
    def verify(self):

        ptask_ver = "PTask version"
        product_ver = "Subscribing to"

        output = Output()
        output.title = "Source subscriptions from: " + self._version.spec
        output.header_names = [
            ptask_ver,
            product_ver,
        ]

        for sub in self.subs_to_source:
            output.add_item(
                {
                    ptask_ver: self.current_ptask_version.spec,
                    product_ver: sub.product_version_spec,
                },
                color_all=Style.bright,
            )

        output.dump(output_format='table')

        if not Output.prompt_yes_no("Source"):
            raise ActionAborted("User chose not to proceed.")

    # -------------------------------------------------------------------------
    @property
    def current_ptask(self):
        return self._current_ptask

    # -------------------------------------------------------------------------
    @property
    def current_ptask_version(self):
        return self._current_ptask_version

    # -------------------------------------------------------------------------
    @property
    def subs_to_source(self):
        return self._subs_to_source

