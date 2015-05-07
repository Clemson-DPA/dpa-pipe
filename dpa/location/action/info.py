# -----------------------------------------------------------------------------
# Imports: 
# -----------------------------------------------------------------------------

from dpa.action import Action, ActionError
from dpa.shell.output import Output, Style
from dpa.location import Location, LocationError, current_location_code

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class LocationInfoAction(Action):
    """ Print information about a location."""

    name = "info"
    target_type = "location"

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        parser.add_argument(
            "code", 
            nargs="?", 
            default=current_location_code(),
            help="Print info for the supplied location code."
        )

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, code):
        super(LocationInfoAction, self).__init__(code)
        self._code = code

    # -------------------------------------------------------------------------
    # Instance methods:
    # -------------------------------------------------------------------------
    def execute(self):

        # output headers. reused while defining the look of the output
        description = 'Description'
        timezone = 'Timezone'
        lat_long = 'Lat/Long'
        active = 'Active'
        code = 'Code'
        host = 'Host'
        filesystem_root = 'Filesystem root'

        # define the look of the output
        output = Output()
        # defining the data headers
        output.header_names = [
            code,
            description,
            host,
            filesystem_root,
            timezone,
            lat_long,
        ]
        output.add_item(
            {
                code: self.location.code,
                description: self.location.description,
                host: self.location.host,
                filesystem_root: self.location.filesystem_root,
                timezone: self.location.timezone,
                lat_long: "{l.latitude}, {l.longitude}".format(l=self.location),
            },
            color_all=Style.bright,
        )
        
        # build the title
        title = " {l.name} ".format(l=self.location)
        if not self.location.active:
            title += " [INACTIVE]"
        title += " "
        output.title = title

        # dump the output as a list of key/value pairs
        output.dump()

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):

        try:
            location = Location.get(self.code)
        except LocationError as e:
            raise ActionError(
                'Could not determine location from code: "{c}"'.\
                    format(c=self.code)
            )

        self._location = location

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def code(self):
        return self._code

    # -------------------------------------------------------------------------
    @property
    def location(self):
        return self._location

