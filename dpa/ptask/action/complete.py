# -----------------------------------------------------------------------------
# Imports: 
# -----------------------------------------------------------------------------

from dpa.action import Action
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask.spec import PTaskSpec

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class PTaskCompleteSpecAction(Action):
    """Prints completion options for a given partial ptask spec."""

    name = "complete"
    target_type = "ptask"
    logging = False

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        parser.add_argument(
            "spec", 
            nargs="?", 
            default="",
            help="The partial ptask spec to complete."
        )
        
    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, spec="."):
        super(PTaskCompleteSpecAction, self).__init__(spec)
        self._spec = spec

    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def execute(self):

        match_specs = self._complete(
            self.spec, 
            relative_to=PTaskArea.current().spec,
        )

        if match_specs:
            print " ".join([s for s in match_specs])

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
    def _complete(self, spec, relative_to=None):

        in_spec = self.spec.strip().strip(PTaskSpec.SEPARATOR)
        full_spec = PTaskSpec.get(in_spec, relative_to=relative_to)
        ptask_area = None

        # is the supplied spec a ptask area? if so, print sub directories
        # if not, get the parent spec and print its sub directories
        try:
            ptask_area = PTaskArea(full_spec)
        except PTaskAreaError:
            in_spec = PTaskSpec.parent(in_spec)
            full_spec = PTaskSpec.parent(full_spec)
            try:
                ptask_area = PTaskArea(full_spec)
            except PTaskAreaError:
                pass

        if not ptask_area:
            return

        # append the child name to the input spec and print them out for completion
        match_specs = []
        for area_dir in ptask_area.dirs(children=True, product_dirs=True):
            if in_spec:
                match_specs.append(in_spec + PTaskSpec.SEPARATOR + area_dir)
            else:
                match_specs.append(area_dir)

        return [m + PTaskSpec.SEPARATOR for m in match_specs]
        
