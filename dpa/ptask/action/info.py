
# -----------------------------------------------------------------------------
# Imports: 
# -----------------------------------------------------------------------------

from dpa.action import Action, ActionError
from dpa.shell.output import Output, Style
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class PTaskInfoAction(Action):
    """ Print information about a ptask."""

    name = "info"
    target_type = "ptask"

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        parser.add_argument(
            "spec", 
            nargs="?", 
            default="",
            help="Print info for this ptask spec. First checks relative to " + \
                 "the currently set ptask. If no match is found, checks " + \
                 "relative to the project root.",
        )

        parser.add_argument(
            "--no-versions",
            action="store_false",
            dest="versions",
            help="Do not display ptask version information",
        )

        parser.set_defaults(versions=True)

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, spec, versions=True):
        super(PTaskInfoAction, self).__init__(spec)
        self._spec = spec
        self._versions = versions

    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def execute(self):

        if not self.ptask:
            return

        self._ptask_info()

        if self.versions:
            self._ptask_versions_info()

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):
        
        cur_spec = PTaskArea.current().spec
        full_spec = PTaskSpec.get(self.spec, relative_to=cur_spec)

        # try to get a ptask instance from the db
        if full_spec:
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
        else:
            ptask = None

        self._ptask = ptask

    # -------------------------------------------------------------------------
    # Properties
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
    # Private methods:
    # -------------------------------------------------------------------------
    def _ptask_info(self):

        # define the fields names
        version = "Current version"
        description = "Description"
        due_date = "Due date"
        priority = "Priority"
        start_date = "Start date"
        status = "Status"
        ptask_type = "Type"

        # define the look of the output
        output = Output()
        
        # display order of the information
        output.header_names = [
            ptask_type,
            version,
            description,
            status,
            start_date,
            due_date,
            priority,
        ]

        # add all the information 
        output.add_item(
            {
                ptask_type: self.ptask.ptask_type,
                version: self.ptask.latest_version.number_padded,
                description: self.ptask.description,
                status: self.ptask.status,
                start_date: str(self.ptask.start_date),
                due_date: str(self.ptask.due_date),
                priority: str(self.ptask.priority),
            },
            color_all=Style.bright,
        )

        # build the title
        title = " {p.spec}".format(p=self.ptask)
        if not self.ptask.active:
            title += " [INACTIVE]"
        title += " "
        output.title = title

        # dump the output as a list of key/value pairs
        output.dump()

    # -------------------------------------------------------------------------
    def _ptask_versions_info(self):

        version_number = "Version"
        description = "Description"
        location = "Location"
        parent = "Source"
        
        output = Output()
        output.vertical_padding = 0
        output.vertical_separator = None
        output.table_header_separator = '-'
        output.header_names = [
            version_number,
            description,
            location,
            parent,
        ]

        output.set_header_alignment({
            version_number: "right",
            parent: "right",
        })

        for version in sorted(self.ptask.versions, key=lambda v: v.number):

            parent_num = version.parent_spec

            if parent_num:
                (parent_ptask_spec, parent_ver) = parent_num.split("@")
                if parent_ptask_spec == self.ptask.spec:
                    parent_num = parent_ver

            output.add_item(
                {
                    version_number: version.number_padded,
                    description: version.description,
                    location: version.location_code,
                    parent: parent_num,
                },
                colors={
                    version_number: Style.bright,
                }
            )

        output.dump(output_format='table')

        print ""

