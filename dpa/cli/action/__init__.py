
# ----------------------------------------------------------------------------
# Imports:
# ----------------------------------------------------------------------------

from abc import ABCMeta
import argparse
import sys

from dpa.action import Action
from dpa.logging import Logger
from dpa.ptask.area import PTaskArea

# ----------------------------------------------------------------------------
# Classes:
# ----------------------------------------------------------------------------
class CommandLineAction(Action):
    """A base class for command line actions."""

    __metaclass__ = ABCMeta

    target_type = "cli"

    # ------------------------------------------------------------------------
    # Methods:
    # ------------------------------------------------------------------------
    def log_action(self):

        if not self.__class__.logging:
            return

        # log the command
        msg = "({s})".format(s=PTaskArea.current().spec)
        msg += " " + " ".join(sys.argv)

        self.logger.info(msg)
        
