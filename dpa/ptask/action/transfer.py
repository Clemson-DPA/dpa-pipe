

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------

from dpa.action import Action, ActionError
from dpa.action.registry import ActionRegistry
from dpa.location import current_location_code
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskAreaError
from dpa.ptask.cli import ParsePTaskSpecArg
from dpa.shell.output import Output, Style

# ----------------------------------------------------------------------------
# Classes:
# ----------------------------------------------------------------------------
class PTaskTransferAction(Action):

    name = 'transfer'
    target_type = 'ptask'

    # ----------------------------------------------------------------------------
    # Class methods:
    # ----------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        parser.add_argument(
            "ptask",
            action=ParsePTaskSpecArg,
            nargs="?",
            help="The spec representing the ptask to transfer."
        )
        
    # ----------------------------------------------------------------------------
    # Instance methods:
    # ----------------------------------------------------------------------------
    def __init__(self, ptask):

        super(PTaskTransferAction, self).__init__(ptask)

        self._ptask = ptask
        self._ptask_latest_version = None

    # ----------------------------------------------------------------------------
    def execute(self):

        # sync the contents of the latest version to this location
        self._sync_latest_remote()

        # update the latest version and set it's location to this location
        try:
            self.ptask_latest_version.update(
                location=current_location_code(),
            )
        except PTaskVersionError as e:
            raise ActionError(
                "Failed to update the location of latest version of the " + \
                    "ptask: " + str(e)
            )

        print "\nTransfer successful!\n"

    # ----------------------------------------------------------------------------
    def validate(self):

        # make sure the ptask evaluates to a real ptask
        try:
            self._ptask = PTask.get(self.ptask)
        except PTaskError:
            raise ActionError(
                "Unable to determine ptask from: " + str(self.ptask)
            )

        # for efficiency
        self._ptask_latest_version = self.ptask.latest_version

        # make sure the latest version is not this location
        if self.ptask_latest_version.location_code == current_location_code():
            raise ActionError(
                "Latest version of {b}{p}{r} already owned by this location.".\
                    format(
                        b=Style.bright,
                        p=self.ptask.spec,
                        r=Style.reset,
                    )
            )

    # ----------------------------------------------------------------------------
    def verify(self):

        ptask_field = 'PTask'
        latest_version_field = 'Latest version'
        from_field = 'From'
        to_field = 'To'

        output = Output()
        output.header_names = [
            ptask_field,
            latest_version_field,
            from_field,
            to_field,
        ]

        output.add_item(
            {
                ptask_field: self.ptask.spec,
                latest_version_field: self.ptask_latest_version.number_padded,
                from_field: self.ptask_latest_version.location_code,
                to_field: current_location_code(),
            },
            color_all=Style.bright,
        )

        output.title = "Confirm transfer:"
        output.dump()

        if not Output.prompt_yes_no(Style.bright + "Transfer" + Style.reset):
            raise ActionAborted("User chose not to proceed.")

    # ----------------------------------------------------------------------------
    def undo(self):
        pass

    # ----------------------------------------------------------------------------
    # Properties:
    # ----------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

    # ----------------------------------------------------------------------------
    @property
    def ptask_latest_version(self):
        return self._ptask_latest_version

    # ----------------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------------
    def _sync_latest_remote(self):

        # sync the local work directory with the contents of the remote work
        # directory (excluding products and child directories)

        source_action_class = ActionRegistry().get_action('sync', 'ptask')
        if not source_action_class:
            raise ActionError("Could not find ptask source action.")

        try:
            source_action = source_action_class(
                ptask=self.ptask,
                version="latest",
                force=True,
            )
            source_action.interactive = False
            source_action()
        except ActionError as e:
            raise ActionError("Failed to sync the remote work directory.")

