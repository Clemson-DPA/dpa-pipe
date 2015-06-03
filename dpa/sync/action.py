
# ----------------------------------------------------------------------------
# Imports:
# ----------------------------------------------------------------------------

import os
import shlex
from subprocess import CalledProcessError, Popen, PIPE

from dpa.action import Action, ActionError

# ----------------------------------------------------------------------------
class SyncAction(Action):

    name = 'sync'
    target_type = 'paths'
    description = 'Sync a destination path with a source path.' 
    
    # ------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(self, parser):

        # source
        parser.add_argument(
            "source",
            help="The source path",
        )

        parser.add_argument(
            "destination",
            help="The destination path",
        )

        parser.add_argument(
            "-w", "--wait",
            action="store_true",
            help="Wait for the sync to finish before returning.",
        )

        parser.add_argument(
            "-i", "--includes",
            action='append',
            help="Patterns of files to include when sync'ing"
        )

        parser.add_argument(
            "-e", "--excludes",
            action='append',
            help="Patterns of files to exclude when sync'ing"
        )

        parser.add_argument(
            "-d", "--delete",
            help="Delete destination files that don't exist in the source.",
            action="store_true",
        )

    # ------------------------------------------------------------------------
    def __init__(self, source, destination, includes=None, excludes=None, 
        wait=True, delete=False):

        super(SyncAction, self).__init__(
            source, 
            destination,
            includes=includes,
            excludes=excludes,
            wait=wait,
        )

        self._source_path = source
        self._destination_path = destination
        self._includes = includes
        self._excludes = excludes
        self._wait = wait
        self._delete = delete

    # ------------------------------------------------------------------------
    def execute(self):

        options = ["-a", "-v", "-O"] 

        if self.includes:
            for include in self.includes:
                options.append('--include="{i}"'.format(i=include))

        if self.excludes:
            for exclude in self.excludes:
                options.append('--exclude="{i}"'.format(i=exclude))

        if self.delete:
            options.append("--delete-after")

        options = " ".join(options)

        command = "rsync {o} {s} {d}".format(
            o=options, 
            s=self.source_path, 
            d=self.destination_path,
        )

        args = shlex.split(command)

        if self.wait:
            try:
                msg = Popen(args,
                    stdout=PIPE)
                self.logger.info(msg)
            except CalledProcessError as e:
                raise ActionError(str(e))
        else:
            try:
                proc = Popen(args)
            except OSError as e:
                raise ActionError(str(e))

    # ------------------------------------------------------------------------
    def undo(self):
        pass

    # ------------------------------------------------------------------------
    # Properties:
    # ------------------------------------------------------------------------
    @property
    def source_path(self):
        return self._source_path

    # ------------------------------------------------------------------------
    @property
    def destination_path(self):
        return self._destination_path

    # ------------------------------------------------------------------------
    @property
    def includes(self):
        return self._includes

    # ------------------------------------------------------------------------
    @property
    def excludes(self):
        return self._excludes

    # ------------------------------------------------------------------------
    @property
    def wait(self):
        return self._wait

    # ------------------------------------------------------------------------
    @property
    def delete(self):
        return self._delete

