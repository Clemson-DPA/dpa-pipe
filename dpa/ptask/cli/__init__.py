# -----------------------------------------------------------------------------
# Module: dpa.argparse
# Contact: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import argparse
import sys

from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class ParsePTaskSpecArg(argparse.Action):
    """argparse.Action subclass. parses a ptask spec.

    Use this class as an argument to the 'action' argument when calling
    add_argument on an argparse parser. When the command line arguments are 
    parsed, the resulting namespace will include a parsed ptask spec object
    assigned to the argument's destination. 

    This action will parse and resolve a ptask spec relative to the currently
    set ptask environment. 

    """

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, in_spec, option_string=None):

        # assume the current ptask if not supplied
        if not in_spec:
            in_spec = "."

        cur_spec = PTaskArea.current().spec
        in_spec = in_spec.strip().strip(PTaskSpec.SEPARATOR)
        full_spec = PTaskSpec.get(in_spec, relative_to=cur_spec)

        setattr(namespace, self.dest, full_spec)

