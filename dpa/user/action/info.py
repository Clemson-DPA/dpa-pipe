# -----------------------------------------------------------------------------
# Imports: 
# -----------------------------------------------------------------------------

from dpa.action import Action
from dpa.shell.output import Output, Style
from dpa.user import User, UserError, current_username

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class UserPrintInfoAction(Action):
    """ Print information about a user."""

    name = "info"
    target_type = "user"

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        parser.add_argument(
            "username", 
            nargs="?", 
            default=current_username(),
            help="Print info for the supplied username."
        )

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, username):

        super(UserPrintInfoAction, self).__init__(username)
        self._username = username

    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def execute(self):

        try:
            user = User.get(self.username)
        except UserError:
            self.logger.error(
                'Could not determine user from: "{u}"'.format(u=self.username)
            )
            raise

        # output headers. reused while defining the look of the output
        username = 'Username'
        last_name = 'Last'
        first_name = 'First'
        email = 'Email'
        active = 'Active'

        # define the look of the output
        output = Output()
        # defining the data headers
        output.header_names = [username, email]
        output.add_item(
            {
                username: user.username,
                email: user.email,
            },
            color_all=Style.bright,
        )
        
        # build the title
        title = " {u.first_name} {u.last_name}".format(u=user)
        if not user.is_active:
            title += " [INACTIVE]"
        title += " "
        output.title = title

        # dump the output as a list of key/value pairs
        output.dump()

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def username(self):
        return self._username

