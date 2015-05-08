# -----------------------------------------------------------------------------
# Imports: 
# -----------------------------------------------------------------------------

from dpa.action import Action, ActionError, ActionAborted
from dpa.action.registry import ActionRegistry
from dpa.location import current_location_code
from dpa.product.subscription import (
    ProductSubscription, 
    ProductSubscriptionError,
)
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskAreaError
from dpa.ptask.cli import ParsePTaskSpecArg
from dpa.ptask.version import PTaskVersion, PTaskVersionError
from dpa.shell.output import Output, Bg, Fg, Style
from dpa.user import current_username

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class PTaskVersionAction(Action):
    """Create a new ptask version."""

    name = "version"
    target_type = "ptask"

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        # ptask spec (name, parent) - can be relative to current ptask
        parser.add_argument(
            "spec",
            action=ParsePTaskSpecArg,
            nargs="?",
            help="The spec representing the ptask to version up.",
        )

        # description
        parser.add_argument(
            "-d", "--description", 
            default=None,
            help="A description of the work done in the source version.",
            metavar='"description"'
        )

        # source version
        parser.add_argument(
            "-s", "--source_version",
            default=None,
            help="The version of the ptask to source when creating the new version.",
        )

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, spec, description=None, source_version=None):

        super(PTaskVersionAction, self).__init__(
            spec, 
            description=description,
            source_version=source_version,
        )

        self._spec = spec
        self._description = description
        self._source_version = source_version

    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def execute(self):

        self._update_description()
        self._sync_latest()
        self._create_version()
        self._copy_subs()

        if self.latest_version != self.source_version:
            self._source_non_latest()

        self._refresh_subs()

        print "\nVersion up successful!\n"

    # -------------------------------------------------------------------------
    def prompt(self):

        # get the description
        if not self.description:
            self._description = Output.prompt(
                "\n Please describe the work done in this version:\n    ",
                blank=False,
                separator=">>>"
            )

    # -------------------------------------------------------------------------
    def validate(self):
        
        try:
            self._ptask = PTask.get(self.spec)
        except PTaskError:
            raise ActionError(
                "Unable to determine ptask from: " + str(self.spec)
            )

        self._latest_version = self.ptask.latest_version

        # determine the source version. also store a reference to the latest
        # version for efficiency
        if self.source_version:
            source_version = self.ptask.version(self.source_version)
            if source_version is None:
                raise ActionError(
                    "Could not determine source version from: " + \
                        self.source_version
                )
            self._source_version = source_version
        else:
            self._source_version = self.latest_version

        # latest version must exist in this location. 
        if self.latest_version.location_code != current_location_code():
            raise ActionError(
                "The latest version of this ptask is not owned by this " +
                "location.\nOwnership of this ptask must first be " + 
                "transferred to this location."
            )

        if self.source_version.ptask != self.ptask:
            raise ActionError(
                "Source version's ptask does not match the ptask being " + \
                "versioned."
            )

    # -------------------------------------------------------------------------
    def verify(self):

        next_version = self.ptask.next_version_number_padded

        ptask = "PTask"
        source_version = "Source version"
        description = "v{v} description".format(v=self.latest_version.number)

        output = Output()
        output.header_names = [
            ptask,
            source_version,
            description,
        ]

        output.add_item({
            ptask: Style.bright + str(self.ptask.spec) + Style.reset,
            source_version: \
                Style.bright + \
                str(self.source_version.number_padded) + \
                Style.reset,
            description: Style.bright + str(self.description) + Style.reset,
        })

        output.title = "Confirm version creation: {v}".format(v=next_version)
        output.dump()

        if not Output.prompt_yes_no(Style.bright + "Version up" + Style.reset):
            print "\nAborting!\n"
            raise ActionAborted("User aborted before version attempted.")

    # -------------------------------------------------------------------------
    def undo(self):
        pass
        
    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def spec(self):
        return self._spec

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

    # -------------------------------------------------------------------------
    @property
    def new_ptask_version(self):
        return self._new_ptask_version

    # -------------------------------------------------------------------------
    @property
    def description(self):
        return self._description

    # -------------------------------------------------------------------------
    @property
    def source_version(self):
        return self._source_version

    # -------------------------------------------------------------------------
    @property
    def latest_version(self):
        return self._latest_version

    # -------------------------------------------------------------------------
    # Private methods:
    # -------------------------------------------------------------------------
    def _create_version(self):

        new_version = self.ptask.next_version_number
        location_code = current_location_code()

        try:
            self._new_ptask_version = PTaskVersion.create(
                current_username(),
                "in progress...".format(n=new_version),
                location_code,
                ptask_spec=self.ptask.spec,
                number=new_version,
                parent_spec=self.source_version.spec,
            ) 
        except PTaskVersionError as e:
            raise ActionError("Failed to create ptask version: " + str(e))
        else:
            print "\nNew version successfully created in the database."

        # ---- provision a version directory in the ptask area

        try:
            self.ptask.area.provision(
                self.ptask.area.dir(version=new_version, verify=False)
            )
        except PTaskAreaError as e:
            raise ActionError("Unable to provision version directory.")
        else:
            print "\nSuccessfully provisioned directory for version: " + \
                str(new_version)

    # -------------------------------------------------------------------------
    def _source_non_latest(self):

        source_action_class = ActionRegistry().get_action('source', 'ptask')
        if not source_action_class:
            raise ActionError("Could not find ptask source action.")

        try:
            source_action = source_action_class(
                source=self.ptask,
                source_version=self.source_version,
                destination=self.ptask,
                delete=True,
            )
            source_action.interactive = False
            source_action()
        except ActionError as e:
            raise ActionError( 
                "Failed to copy source version into the work directory.".\
                    format(v=self.latest_version.number)
            )
        else:
            print "\nSuccessfully copied source version into the work " + \
                "directory."

    # -------------------------------------------------------------------------
    def _sync_latest(self):

        # make sure the destination directory exists. it should be there
        # and empty, but just in case...

        try:
            self.ptask.area.provision(
                self.ptask.area.dir(
                    version=self.latest_version.number, verify=False
                )
            )
        except PTaskAreaError as e:
            raise ActionError(
                "Unable to create missing destination directory."
            )

        # sync the latest version directory with the contents of the work
        # directory (excluding products and child directories)

        source_action_class = ActionRegistry().get_action('source', 'ptask')
        if not source_action_class:
            raise ActionError("Could not find ptask source action.")

        try:
            source_action = source_action_class(
                source=self.ptask,
                destination=self.ptask,
                destination_version=self.latest_version
            )
            source_action.interactive = False
            source_action()
        except ActionError as e:
            raise ActionError( 
                "Failed to copy latest work in to version {v} directory.".\
                    format(v=self.latest_version.number)
            )

    # ------------------------------------------------------------------------
    def _update_description(self):

        try:
            self.latest_version.update(description=self.description)
        except PTaskVersionError as e:
            raise ActionError(str(e))

    # ------------------------------------------------------------------------
    def _copy_subs(self):

        if self.interactive:
            print "\nCopying forward subscriptions:"

        ptask_version_spec = self.new_ptask_version
        exceptions = []
        
        for sub in self.source_version.subscriptions:
            try:
                new_sub = ProductSubscription.create(
                    ptask_version_spec,
                    sub.product_version_spec,
                )
            except ProductSubscriptionError as e:
                exceptions.append((sub, e))
            else:
                print "  " + Style.bright + \
                    str(sub.product_version_spec) + Style.normal

        if exceptions:
            msgs = []
            for (sub, e) in exceptions:
                msgs.append(sub.product_version_spec + ": " + str(e))
            
            raise ActionError(
                "Unable to copy forward some subscriptions:\n\n" + \
                    "\n".join(msgs)
            )

    # -------------------------------------------------------------------------
    def _refresh_subs(self):

        if self.interactive:
            print "\nRefreshing subscriptions."
            
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

