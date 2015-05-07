
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import os

from dpa.env.vars import DpaVars

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class PTaskHistory(object):

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, history_file=None, history_size=None):
        
        if history_file is None:
            history_file = DpaVars.ptask_history_file().get()

        if history_size is None:
            history_size = DpaVars.ptask_history_size().get()

        self.history_file = os.path.expanduser(history_file)
        self.history_size = history_size

    # -------------------------------------------------------------------------
    # Instance methods:
    # -------------------------------------------------------------------------
    def add(self, ptask_spec):
        """Adds a new ptask_spec to the history file."""

        # create the file if it doesn't exist
        if not os.path.exists(self.history_file):
            open(self.history_file, "a").close()

        with open(self.history_file, 'r+') as history:
            specs = history.read().strip()
            specs = [l for l in specs.split(os.linesep) if l]
            specs.append(ptask_spec)
            specs = specs[-1 * self.history_size:]
            history.seek(0)
            history.write(os.linesep.join(specs))
            history.truncate()

    # -------------------------------------------------------------------------
    def get(self):
        """:returns: :py:obj:`list` of ptask specs from the history file."""

        try:
            with open(self.history_file, 'r') as history:
                specs = history.read().strip().split("\n")
        except IOError:
            return []

        return specs

    # -------------------------------------------------------------------------
    # Instance properties:
    # -------------------------------------------------------------------------
    @property
    def latest(self):
        """:returns: a spec for the latest ptask spec set in the history."""

        try:
            return self.get()[-1]
        except IndexError:
            return None

    # -------------------------------------------------------------------------
    @property
    def previous(self):
        """:returns: a spec for the next to last ptask spec set in history."""

        try:
            return self.get()[-2]
        except IndexError:
            return None

