# ----------------------------------------------------------------------------

import argparse
import os
import platform
import shlex
from subprocess import Popen

from dpa.action import Action, ActionError
from dpa.config import Config
from dpa.env import EnvVar
from dpa.ptask import PTaskArea

# ----------------------------------------------------------------------------

OPEN_ACTION_CONFIG = "config/actions/open.cfg"

# ----------------------------------------------------------------------------
class OpenAction(Action):

    name = 'open'
    target_type = 'file'
    description = 'Open a file or application.'
    
    # ------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(self, parser):

        # the file or software
        parser.add_argument(
            "filename",
            help="Name of the file or software to open.",
        )
        
        parser.add_argument(
            "-n", "--noop",
            help="No operation. Just print the open command.",
            action='store_true',
        )

        # everything else
        parser.add_argument(
            "args",
            nargs=argparse.REMAINDER,
        )

    # ------------------------------------------------------------------------
    def __init__(self, filename, args, noop):
        super(OpenAction, self).__init__(filename, args, noop)

        self._filename = filename
        self._args = args
        self._noop = noop

    # ------------------------------------------------------------------------
    def execute(self):

        cmd = self.command.format(
            ARGS=" ".join(self.args),
            DPA_PTASK_PATH=EnvVar('DPA_PTASK_PATH').get(),
            EDITOR=EnvVar('EDITOR').get(),
            FILE=self.filename,
        )

        cmd = cmd.strip()

        if self.interactive:
            print "\n> " + cmd + " &\n"

        if self.noop:
            return

        args = shlex.split(cmd)

        try:
            Popen(args)
        except OSError as e:
            raise ActionError(str(e))

    # ------------------------------------------------------------------------
    def undo(self):
        pass

    # ------------------------------------------------------------------------
    def validate(self):

        (root, ext) = os.path.splitext(self.filename)

        ext = ext.lower().lstrip(".")

        # no ext, assume root is sw name
        if not ext:
            self._filename = ""
            self._software = root

        # ext but no match in config
        elif ext and not ext in self.config.extensions:
            raise ActionError("Unknown extension: " + ext) 

        # ext and match in config
        else:
            self._software = self.config.extensions[ext]

        # validate the sw and get the command string
        if not self._software in self.config.software:
            raise ActionError(
                "Don't know how to launch software: " + self._software)
        else:
            if not self.operating_system in \
                self.config.software[self._software]:
                raise ActionError(
                    "No open command for os: " + self.operating_system)
            else:
                self._command = self.config.\
                    software[self._software][self.operating_system]

    # ------------------------------------------------------------------------
    @property
    def args(self):
        return self._args

    # ------------------------------------------------------------------------
    @property
    def command(self):
        return self._command

    # ------------------------------------------------------------------------
    @property
    def config(self):

        if not hasattr(self, '_config'):
            self._config = PTaskArea.current().config(
                OPEN_ACTION_CONFIG,
                composite_ancestors=True,
                composite_method="override",
            )

        return self._config

    # ------------------------------------------------------------------------
    @property
    def filename(self):
        return self._filename

    # ------------------------------------------------------------------------
    @property
    def noop(self):
        return self._noop

    # ------------------------------------------------------------------------
    @property
    def operating_system(self):
        
        if not hasattr(self, '_os'):
            self._os = platform.system()

        return self._os

    # ------------------------------------------------------------------------
    @property
    def software(self):
        return self._software

