
# -----------------------------------------------------------------------------
# Imports: 
# -----------------------------------------------------------------------------

import re

from dpa.action import Action, ActionError
from dpa.shell.formatter import ShellFormatters
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask.history import PTaskHistory
from dpa.ptask.spec import PTaskSpec, PTaskSpecError

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class PTaskEnvAction(Action):
    """Print a ptask's shell environment."""
    
    name = "env"
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
            default=PTaskArea.current().spec,
            help="The production task specification."
        )

        parser.add_argument(
            "-s", "--shell", 
            default=ShellFormatters.default().name,
            choices=sorted([f.name for f in ShellFormatters.all()]),
            help="Shell type env commands should target."
        )

        parser.add_argument(
            "-p", "--previous", 
            nargs="?", 
            const="list",
            help="Choose a previous ptask env."
        )

        parser.add_argument(
            "-v", "--version", 
            type=int,
            help="The version of the ptask to print info for."
        )

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, spec, shell, previous=None, version=None):

        super(PTaskEnvAction, self).__init__(
            spec, 
            shell, 
            previous=previous
        )

        self._spec = spec
        self._shell = ShellFormatters.get(shell)
        self._previous = previous
        self._version = version

    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def execute(self):

        if self.previous:
            if self.previous == "list":
                self._list_ptask_history()
                return
            else:
                self._get_ptask_spec_from_history()

        self._print_ptask_env()

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def spec(self):
        return self._spec

    # -------------------------------------------------------------------------
    @spec.setter
    def spec(self, value):
        self._spec = value

    # -------------------------------------------------------------------------
    @property
    def shell(self):
        return self._shell

    # -------------------------------------------------------------------------
    @property
    def previous(self):
        return self._previous

    # -------------------------------------------------------------------------
    @property
    def version(self):
        return self._version

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------
    def _get_ptask_spec_from_history(self):

        # allow selection via history list
        try:
            self.spec = self._get_ptask_spec_history()[int(self.previous)]
        except Exception as e:
            raise ActionError("Invalid ptask history index.")
        
    # -------------------------------------------------------------------------
    def _get_ptask_spec_history(self):
        
        # reversed so most recent is first in the list
        specs = reversed(PTaskHistory().get())

        # remove duplicates but preserve order:
        # http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order 
        unique_specs = set() 
        unique_add = unique_specs.add
        return [s for s in specs if not (s in unique_specs or unique_add(s))]

    # -------------------------------------------------------------------------
    def _list_ptask_history(self):

        specs = self._get_ptask_spec_history()

        if len(specs) == 0:
            print self.shell.echo("No ptask history found.")
            return

        print self.shell.echo("")
        for i, spec in enumerate(specs):
            print self.shell.echo("  {i}: {s}".format(i=i, s=spec))
        print self.shell.echo("")

    # -------------------------------------------------------------------------
    def _print_ptask_env(self):

        # remove any whitespace on the head/tail of the spec
        spec = self.spec.strip()
        ptask_area = None

        if self.version:
            spec = PTaskSpec.VERSION.join([spec, str(self.version)])
            

        replace_match = re.match("\.?/([=\w]+)/([=\w]+)/", spec)

        # handle 'none' as a valid spec - unset current ptask (set it to root)
        if spec.lower() == 'none':
            spec = ""
            full_spec = PTaskSpec.get(spec)
            try:
                ptask_area = PTaskArea(full_spec)
            except:
                pass

        # special character '-' indicates use the last set ptask spec
        elif spec == "-":
            ptask_area = PTaskArea.previous()

        # set to a similar ptask with text replacement
        elif replace_match:

            cur_area_spec = PTaskArea.current().spec
            repl_spec = cur_area_spec.replace(
                replace_match.group(1), replace_match.group(2))
            try:
                ptask_area = PTaskArea(repl_spec)
            except:
                pass
            
        # use the supplied spec relative to the current ptask
        else:

            relative_to = PTaskArea.current().spec

            while ptask_area is None:

                try:
                    full_spec = PTaskSpec.get(spec, relative_to=relative_to)
                except PTaskSpecError as e:
                    raise ActionError(str(e))

                try:
                    # if this is successful, we'll break out of the while
                    ptask_area = PTaskArea(full_spec)
                except PTaskAreaError as e: 
                    # no match, check the parent relative spec
                    relative_to = PTaskSpec.parent(relative_to)
                    # there is no parent, break out of the while
                    if relative_to is None:
                        break

        # dump out commands used for setting the environment for the supplied
        # spec.

        if not ptask_area:
            raise ActionError(
                "Could not determine ptask area from: " + str(spec), 
            )

        ptask = None

        # delay the db query to this point to prevent multiple, unnecessary db
        # queries. if we're at this point, we know there's at least a
        # corresponding directory on disk. 
        if ptask_area.base_spec:
            try:
                ptask = PTask.get(ptask_area.base_spec)
            except PTaskError as e:
                pass

        if not ptask and ptask_area.spec != "":
            raise ActionError("Could not determine ptask from: " + str(spec))
        
        ptask_area.set(shell=self.shell, ptask=ptask)

