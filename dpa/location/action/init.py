
# -----------------------------------------------------------------------------
# Imports: 
# -----------------------------------------------------------------------------

import os

import dpa
from dpa.action import Action, ActionError, ActionAborted
from dpa.env.vars import DpaVars
from dpa.location import Location
from dpa.shell.output import Output, Style

# -----------------------------------------------------------------------------

BASH_ACTIVATE_TEMPLATE = 'activate.bash'
BASH_README_TEMPLATE = 'README'

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class LocationInitAction(Action):
    """Initialize a pipeline location. (staff only).
    
    This action initializes a pipeline location. Before this action is run, a
    location must have been created on the server side. This action requires
    that the matching location code be provided to initialize the local
    filesystem as well as a data server address to connect to. 

    """

    name = 'init'
    target_type = 'location'

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        parser.add_argument(
            "-c", "--code",
            default=None,
            help="The location code to initialize."
        )

        parser.add_argument(
            "-s", "--server",
            default=None,
            help="The data server this location will connect to.",
            metavar="address",
        )

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, code=None, server=None):
        
        super(LocationInitAction, self).__init__(
            code=code,
            server=server,
        )

        self._code = code
        self._server = server
        
    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def execute(self):

        MODE = 0770

        # ensure filesystem root exists
        fs_root = self.location.filesystem_root 
        if not os.path.isdir(fs_root):
            try:
                os.makedirs(fs_root, MODE)
            except error as e:
                raise ActionError(
                    "Unable to create filesystem root directory: " + fs_root + \
                    "\n  " + str(e)
                )

        # remember the directories created below
        dir_lookup = {}

        # create standard directories ('projects', 'bash', 'config', etc.)
        for dir_name in ['bash', 'projects', 'config', '.logs']:
            dir_path = os.path.join(fs_root, dir_name)
            dir_lookup[dir_name] = dir_path
            if not os.path.isdir(dir_path):
                try:
                    os.makedirs(dir_path, MODE)
                except error as e:
                    raise ActionError(
                        "Unable to create root subdirectory: " + dir_path + \
                        "\n  " + str(e)
                    )
                    
        # locate the install location to find the bash template
        install_pkg_dir = os.path.dirname(os.path.abspath(dpa.__file__))

        # ---- bash template

        # the file to read from 
        bash_template_file = os.path.join(
            install_pkg_dir, 'data', 'bash', BASH_ACTIVATE_TEMPLATE
        )
        if not os.path.exists(bash_template_file):
            raise ActionError("Unable to locate LOCATION template bash script.")

        # the file to write to
        bash_activate_file = os.path.join(
            dir_lookup['bash'], BASH_ACTIVATE_TEMPLATE
        )

        # ---- readme file

        # readme file
        bash_readme_template_file = os.path.join(
            install_pkg_dir, 'data', 'bash', BASH_README_TEMPLATE
        )
        if not os.path.exists(bash_readme_template_file):
            raise ActionError("Unable to locate README template file.")

        # the file to write to
        bash_readme_file = os.path.join(
            dir_lookup['bash'], BASH_README_TEMPLATE
        )

        # ---- format template files

        file_pairs = [
            (bash_template_file, bash_activate_file),
            (bash_readme_template_file, bash_readme_file),
        ]

        replacements = (
            ("__DPA_LOCATION_CODE__", self.location.code),
            ("__DPA_DATA_SERVER__", self.server),
            ("__DPA_FILESYSTEM_ROOT__", self.location.filesystem_root),
        )

        # handle the file formatting and writing
        for in_file_path, out_file_path in file_pairs:
            with open(in_file_path) as in_file:
                with open(out_file_path, 'w') as out_file:
                    text = in_file.read()

                    for in_str, out_str in replacements:
                        text = text.replace(in_str, out_str)

                    # write new text to bash file in config dir
                    out_file.write(text)

        # print info to user about bash file to source 
        Output.text(
            "\nA bash script has been created to activate the pipeline in " + \
            "this location. The path to the bash script is: \n\n" + \
            "  " + Style.bright + bash_activate_file + Style.reset + "\n\n" + \
            "See the README in the same directory for instructions on how " + \
            "to reference the script.\n",
            margin=4,
        )

    # -------------------------------------------------------------------------
    def prompt(self):

        # ---- prompt for missing fields

        if not self.code or not self.server:
            print "\nPlease enter the following information:"

        if not self.code:
            print "\nThe db code for this location:"
            self._code = Output.prompt(
                "  " + Style.bright + "Location code" + Style.reset,
                blank=False,
            )

        if not self.server:
            print "\nThe address of the data server this location will " + \
                  "connect to:"
            self._server = Output.prompt(
                "  " + Style.bright + "Data server address" + Style.reset,
                blank=False,
            )

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):

        # make sure the code and server are valid for a connection by retrieving
        # the location data.
        self._location = self._validate_location()

        if not self.location.active:
            raise ActionError(
                "Location is set to " + \
                Style.bright + "inactive " + Style.reset + \
                "on the server."
            )

    # -------------------------------------------------------------------------
    def verify(self):

        code = "Code"
        name = "Name"
        description = "Description"
        server = "Data server"
        filesystem_root = "Filesystem root"

        output = Output()
        output.header_names = [
            code,
            name,
            description,
            server,
            filesystem_root,
        ]

        output.add_item(
            {
                code: self.location.code,
                name: self.location.name,
                description: self.location.description,
                server: self.server,
                filesystem_root: self.location.filesystem_root,
            },
            color_all=Style.bright,
        )

        output.title = "Location summary:"
        output.dump()

        if not Output.prompt_yes_no(
            Style.bright + "Initialize location" + Style.reset
        ):
            raise ActionAborted("User chose not to proceed.") 

    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def code(self):
        return self._code
    
    # -------------------------------------------------------------------------
    @property
    def location(self):
        return self._location

    # -------------------------------------------------------------------------
    @property
    def server(self):
        return self._server

    # -------------------------------------------------------------------------
    # Private methods:
    # -------------------------------------------------------------------------
    def _validate_location(self):

        # ---- make sure code and server are valid

        # first, set the server value in the environment
        server_var = DpaVars.data_server() 
        server_var.value = self.server
        server_var.set()

        # now query the location code
        try:
            location = Location.get(self.code)
        except ActionError as e:
            raise ActionError(
                "Unable to verify location: " + self.code + "\n" + str(e)
            )

        return location

