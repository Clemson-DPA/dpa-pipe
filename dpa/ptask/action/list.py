
# -----------------------------------------------------------------------------
# Imports: 
# -----------------------------------------------------------------------------

import re

from dpa.action import Action, ActionError
from dpa.shell.output import Output, Style
from dpa.ptask import PTask, PTaskError
from dpa.ptask.spec import PTaskSpec

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class PTaskListAction(Action):
    """List ptasks matching a supplied wildcard spec string."""

    name = "list"
    target_type = "ptasks"

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        parser.add_argument(
            "wild_spec", 
            nargs="?", 
            default="",
            help="List ptasks matching this wildcard spec. (wildcard is %%)",
        )

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, wild_spec):
        super(PTaskListAction, self).__init__(wild_spec)

        self._wild_spec = wild_spec

    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def execute(self):

        ptasks = []

        # search the ptasks for specs matching the supplied string
        if PTaskSpec.WILDCARD in self.wild_spec:

            search_str = ",".join(
                filter(None,
                    self.wild_spec.strip().split(PTaskSpec.WILDCARD)
                )
            )

            if not search_str:
                raise ActionError(
                    "Search is too broad. " + \
                    "Please supply a string to search against."
                )

            try:
                # XXX this is inefficient. need better filtering on the backend
                ptasks = PTask.list(search=search_str)
            except PTaskError:
                pass
        else:
            
            try:
                ptasks.append(PTask.get(self.wild_spec))
            except PTaskError:
                pass

        matching_ptasks = []

        # the rest api's search filter isn't that great. it doesn't maintain any
        # knowledge of order for the supplied filters. So, it will return ptasks
        # that match all of the search terms, but not necessarily in the order
        # supplied. Do one more match against the returned ptasks specs keeping
        # the order of the supplied wildcard spec. 

        regex_spec = "^" + \
            self.wild_spec.replace(PTaskSpec.WILDCARD, "([\w=]+)?") + "$"
        regex_spec = re.compile(regex_spec)

        for ptask in ptasks:
            if regex_spec.match(ptask.spec):
                matching_ptasks.append(ptask)

        match_count = len(matching_ptasks)

        if match_count == 0:
            print '\nFound 0 ptasks matching: "{s}"\n'.format(s=self.wild_spec)
            return

        # define the fields names
        spec = "Spec"
        ptask_type = "Type"
        status = "Status"

        # define the look of the output
        output = Output()
        output.vertical_separator = None
        output.table_cell_separator = '  '
        output.table_header_separator = '-'

        if match_count == 1:
            output.title = "{s}: 1 match".format(s=self.wild_spec)
        else:
            output.title = "{s}: {n} matches".format(
                s=self.wild_spec, n=match_count)
        
        # display order of the information
        output.header_names = [
            spec, 
            ptask_type, 
            status,
        ]

        for ptask in sorted(matching_ptasks, key=lambda p: p.spec):
            # add all the information 
            output.add_item(
                {
                    spec: ptask.spec,
                    ptask_type: ptask.ptask_type,
                    status: ptask.status,
                },
                colors={
                    spec: Style.bright,
                }
            )

        # dump the output as a list of key/value pairs
        output.dump(output_format='table')

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def wild_spec(self):
        return self._wild_spec

