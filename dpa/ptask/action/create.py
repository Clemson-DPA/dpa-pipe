
# -----------------------------------------------------------------------------
# Imports: 
# -----------------------------------------------------------------------------

import re

from dpa.action import Action, ActionError, ActionAborted
from dpa.action.registry import ActionRegistry
from dpa.cli import ParseDateArg
from dpa.config import Config
from dpa.location import current_location_code
from dpa.product.subscription import (
    ProductSubscription, 
    ProductSubscriptionError,
)
from dpa.ptask import PTask, PTaskError, validate_ptask_name
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask.cli import ParsePTaskSpecArg
from dpa.ptask.spec import PTaskSpec
from dpa.ptask.version import PTaskVersion, PTaskVersionError
from dpa.shell.output import Output, Style
from dpa.user import current_username

# ----------------------------------------------------------------------------
# Globals
# ----------------------------------------------------------------------------

PROJECT_MASTER_CONFIG_PATH = "config/project/master.cfg"

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class PTaskCreateAction(Action):
    """Create a new ptask."""

    name = "create"
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
            help="The spec representing the ptask to create.",
        )

        # ptask type
        parser.add_argument(
            "-t", "--type",
            dest="ptask_type",
            default=None,
            help="The type of ptask to create.",
            metavar="type"
        )

        # description
        parser.add_argument(
            "-d", "--description", 
            default=None,
            help="A description of the ptask being created.",
            metavar='"description"'
        )

        # creator
        parser.add_argument(
            "-c", "--creator", 
            default=current_username(),
            help="The creator of this ptask.",
            metavar="username"
        )

        # start_date
        parser.add_argument(
            "-b", "--begins",
            action=ParseDateArg,
            dest="start_date",
            help="The start date of the new ptask.",
            metavar="YYYY-MM-DD",
        )

        # due_date
        parser.add_argument(
            "-e", "--ends", 
            action=ParseDateArg,
            dest="due_date",
            help="The due date of the new ptask.",
            metavar="YYYY-MM-DD",
        )

        # source
        parser.add_argument(
            "-s", "--source", 
            action=ParsePTaskSpecArg,
            help="The ptask to use when creating this ptask.",
            metavar="source_spec",
        )

        # force - hidden option to force creation without prompting
        parser.add_argument(
            "-f", "--force",
            action="store_true",
            default=False,
            help="Force creation without prompting for values.",
        )

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, spec, ptask_type=None, description=None, creator=None,
        start_date=None, due_date=None, source=None, force=True):
        super(PTaskCreateAction, self).__init__(
            spec,
            ptask_type=ptask_type,
            description=description,
            creator=creator,
            start_date=start_date,
            due_date=due_date,
            source=source,
            force=force,
        )

        # allow calling code to override the target to specify the ptask type
        # to create
        if ptask_type is None:
            if self.__class__.target_type is not 'ptask':
                ptask_type = self.__class__.target_type
            else:
                raise ActionError("PTask type is required.")

        # do some initial validation on the supplied spec
        parent = PTaskSpec.parent(spec)

        if parent != "":
            try:
                parent = PTask.get(parent)
            except PTaskError:
                raise ActionError("Parent ptask does not exist: " + parent)

        name = PTaskSpec.name(spec)
        try:
            name = validate_ptask_name(name)
        except PTaskError as e:
            raise ActionError("Invalid ptask name: " + str(e))
        
        # input
        self._spec = spec
        self._ptask_type = ptask_type
        self._description = description
        self._creator = creator
        self._start_date = start_date
        self._due_date = due_date
        self._source = source
        self._force = force

        # to create
        self._ptask = None
        self._ptask_area = None
        self._ptask_version = None

    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def execute(self):

        self._create_ptask()
        self._create_ptask_area()
        self._create_ptask_version()

        if self.source:
            self._source_another_ptask()

        if self.interactive:
            print "\nSuccessfully created: " + \
                Style.bright + self.ptask.spec + Style.reset + "\n"

    # -------------------------------------------------------------------------
    def prompt(self):

        parent_spec = PTaskSpec.parent(self.spec)
        template_options = []

        if parent_spec:
            par_ptask = PTask.get(parent_spec)
            par_ptask_type = par_ptask.ptask_type
        else:
            par_ptask_type = 'none'

        ptask_area = PTaskArea(parent_spec, validate=False) 
        master_config = ptask_area.config(
            PROJECT_MASTER_CONFIG_PATH,
            composite_ancestors=True,
        )

        if not master_config or not hasattr(master_config, 'hierarchy'):
            raise ActionError("Unable to find project master config.")

        if not self.ptask_type in master_config.hierarchy[par_ptask_type]:
            raise ActionError(
                "Cannot create '{t}' ptask inside '{p}' ptask".format(
                    t=self.ptask_type,
                    p=par_ptask_type,
                )
            )

        # ---- prompt for missing fields 
        if not self.source and self.ptask_type in master_config.templates:
            for template_spec in master_config.templates[self.ptask_type]:
                trimmed_spec = re.sub(
                    "^templates?=", 
                    "", 
                    template_spec, 
                    flags=re.IGNORECASE
                )
                template_options.append(
                    (
                        re.sub("[=_-]+", " ", trimmed_spec).title(),
                        template_spec
                    )
                )

            self._source = Output.prompt_menu(
                "Select a template to source",
                prompt_str="Selection",
                options=template_options,
                help_str="Please choose from the templates listed.",
                none_option=True,
                custom_prompt="Custom Source",
                custom_blank=False
            )

        # see if the ptask already exists
        if not self.ptask:
            try:
                self._ptask = PTask.get(self.spec)
            except PTaskError:
                pass
            else:
                if not self.force:
                    raise ActionAborted("PTask already exists.")
                else:
                    if not self._description:
                        self._description = self.ptask.description
                    if not self._start_date:
                        self._start_date = self.ptask.start_date
                    if not self._due_date:
                        self._due_date = self.ptask.due_date

        if (not self.description or 
            not self.start_date or 
            not self.due_date):

            if self.force:
                raise ActionError(
                    "Cannot force creation without required fields."
                )
            else:
                print "\nPlease enter information about this new {b}{t}{r}:".\
                    format(
                        b=Style.bright,
                        t=self.ptask_type,
                        r=Style.reset,
                    )

        ptask_display = " [{pt}] {b}{s}{r}".format(
            pt=self.ptask_type,
            b=Style.bright,
            s=self.spec,
            r=Style.reset,
        )

        if not self.description:
            self._description = Output.prompt(
                '{pd} description'.format(pd=ptask_display),
                blank=False,
            )

        if not self.start_date:
            self._start_date = Output.prompt_date(
                '{pd} start date'.format(pd=ptask_display),
                blank=False,
            ) 
 
        if not self.due_date:
            self._due_date = Output.prompt_date(
                '{pd} due date'.format(pd=ptask_display),
                blank=False,
            )

    # -------------------------------------------------------------------------
    def undo(self):

        if hasattr(self, '_ptask'):
            self.logger.warning("Cannot undo attempted ptask creation. " + \
                "See pipeline admin for help cleaning up unwanted ptasks.")

    # -------------------------------------------------------------------------
    def validate(self):

        if self.source:
            try:
                self._source = PTask.get(self.source)
            except PTaskError:
                raise ActionError(
                    "Unable to retrieve ptask from source argument: " + \
                        str(self.source),
                )

    # -------------------------------------------------------------------------
    def verify(self):

        ptask_type_field = "Type"
        spec_field = "Spec"
        description_field = "Description"
        creator_field = "Creator"
        start_date_field = "Starts"
        due_date_field = "Due"
        source_field = "Source"

        output = Output()
        output.header_names = [
            ptask_type_field,
            spec_field,
            description_field,
            creator_field,
            start_date_field,
            due_date_field,
            source_field,
        ]

        if self.source:
            source_disp = self.source.spec
        else:
            source_disp = "None"

        output.add_item(
            {
                ptask_type_field: self.ptask_type,
                spec_field: self.spec,
                description_field: self.description,
                creator_field: self.creator,
                start_date_field:str(self.start_date),
                due_date_field: str(self.due_date),
                source_field: source_disp,
            },
            color_all=Style.bright,
        )

        if self.force:
            output.title = "Creating:"
        else:
            output.title = "Confirm create:"
        output.dump()

        if not self.force:
            if self.ptask:
                if not Output.prompt_yes_no("This ptask already exists. " + \
                    Style.bright + "Continue anyway" + Style.reset):
                    raise ActionAborted(
                        "PTask already exists. User chose not to continue."
                    )
            else:
                prompt_str = "Create " + Style.bright + self.spec + Style.reset
                if self.source:
                    prompt_str += \
                        " + " + \
                        str(len(self.source.children_recursive)) + \
                        " child ptasks"
                if not Output.prompt_yes_no(prompt_str):
                    raise ActionAborted("User chose not to proceed.")

    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def spec(self):
        return self._spec

    # -------------------------------------------------------------------------
    @property
    def ptask_type(self):
        return self._ptask_type

    # -------------------------------------------------------------------------
    @property
    def description(self):
        return self._description

    # -------------------------------------------------------------------------
    @property
    def creator(self):
        return self._creator

    # -------------------------------------------------------------------------
    @property
    def start_date(self):
        return self._start_date

    # -------------------------------------------------------------------------
    @property
    def due_date(self):
        return self._due_date

    # -------------------------------------------------------------------------
    @property
    def source(self):
        return self._source

    # -------------------------------------------------------------------------
    @property
    def force(self):
        return self._force

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

    # -------------------------------------------------------------------------
    @property
    def ptask_area(self):
        return self._ptask_area

    # -------------------------------------------------------------------------
    @property
    def ptask_version(self):
        return self._ptask_version

    # -------------------------------------------------------------------------
    # Private methods:
    # -------------------------------------------------------------------------
    def _create_ptask(self):

        parent = PTaskSpec.parent(self.spec)
        name = PTaskSpec.name(self.spec)

        # create
        if not self.ptask:
            try:
                self.logger.debug("Creating ptask: " + str(self.spec))
                self._ptask = PTask.create(
                    name, 
                    self.ptask_type,
                    self.description, 
                    creator_username=self.creator, 
                    parent_spec=parent, 
                    start_date=str(self.start_date), 
                    due_date=str(self.due_date),
                )
            except PTaskError as e:
                raise ActionError("Failed to create ptask: " + str(e)) 
        # update
        else:
            try:
                self.logger.debug("Updating ptask: " + str(self.spec))
                self.ptask.update(
                    description=self.description, 
                    start_date=str(self.start_date), 
                    due_date=str(self.due_date),
                )
            except PTaskError as e:
                raise ActionError("Failed to update ptask: " + str(e)) 

    # -------------------------------------------------------------------------
    def _create_ptask_area(self):

        # ---- create the directory path if it doesn't exist

        try:
            self._ptask_area = PTaskArea(self.ptask.spec)
        except PTaskAreaError:
            pass
        else:
            if not self.force:
                raise ActionError("PTask area already exists.")

        if not self.ptask_area:
            try:
                self._ptask_area = PTaskArea.create(self.ptask)
            except PTaskAreaError as e:
                raise ActionError("Failed to create ptask area: " + str(e))

    # -------------------------------------------------------------------------
    def _create_ptask_version(self):

        version = 1
        location_code = current_location_code()

        if self.ptask.versions:
            if not self.force:
                raise ActionError("PTask version already exists.")
        else:
            try:
                ptask_version = PTaskVersion.create(
                    self.creator,
                    "In progress...",
                    location_code,
                    ptask_spec=self.ptask.spec,
                    number=version,
                ) 
            except PTaskVersionError as e:
                raise ActionError("Failed to create ptask version: " + str(e)) 

        # provision a version directory in the ptask area
        self.ptask_area.provision(
            self.ptask_area.dir(version=version, verify=False)
        )

    # -------------------------------------------------------------------------
    def _source_another_ptask(self):

        source_action_class = ActionRegistry().get_action('source', 'ptask')
        if not source_action_class:
            raise ActionError("Could not find ptask source action.")

        try:
            source_action = source_action_class(
                source=self.source,
                destination=self.ptask, 
                force=True,
            )
            source_action.interactive = False
            source_action()

        except ActionError as e:
            raise ActionError("Failed to source ptask: " + str(e))

        exceptions = []

        # copy the subscriptions from the source ptask
        self._source_subs(self.source, self.ptask)

        # recursively create child ptasks from the source
        for source_child in self.source.children:

            try:
                child_spec = \
                    self.ptask.spec + PTaskSpec.SEPARATOR + source_child.name
                child_create = PTaskCreateAction(
                    child_spec,
                    ptask_type=source_child.type,
                    description="Sourced from: " + source_child.spec,
                    creator=self.creator,
                    start_date=self.start_date,
                    due_date=self.due_date,
                    source=source_child,
                    force=True,
                )
                child_create.interactive = False
                child_create()
            except ActionError as e:
                exceptions.append(e)
        
        if exceptions:
            msg = "\n".join([str(e) for e in exceptions])
            raise ActionError(
                "Problem sourcing: " + self.source.spec + "\n\n" + msg
            )

    # -------------------------------------------------------------------------
    def _source_subs(self, source_ptask, dest_ptask):

        if self.interactive:
            print "\nSourcing subscriptions:"

        dest_ptask_version_spec = dest_ptask.latest_version.spec
        exceptions = []
        
        for sub in source_ptask.latest_version.subscriptions:
            try:
                new_sub = ProductSubscription.create(
                    dest_ptask_version_spec,
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
        else:
            # build the import directory...
            if self.interactive:
                print "\nRefreshing subscriptions."
            
            # refresh the subscriptions on disk
            refresh_action_cls = ActionRegistry().get_action('refresh', 'subs')
            if not refresh_action_cls:
                raise ActionError("Could not find sub refresh action.")

            try:
                refresh_action = refresh_action_cls(dest_ptask)
                refresh_action.interactive = False
                refresh_action()
            except ActionError as e:
                raise ActionError("Failed to refresh subs on disk: " + str(e))

