
# ----------------------------------------------------------------------------
# Imports:
# ----------------------------------------------------------------------------

from dpa.action import Action, ActionError
from dpa.ptask.action.sync import _PTaskSyncAction
from dpa.location import current_location_code
from dpa.shell.output import Style

# ----------------------------------------------------------------------------
# Classes:
# ----------------------------------------------------------------------------
class PTaskSourceAction(_PTaskSyncAction):
    """Source the contents of one ptask into another."""

    # ------------------------------------------------------------------------
    def execute(self):

        try:
            super(PTaskSourceAction, self).execute()
        except ActionError as e:
            raise ActionError("Unable to source ptask: " + str(e))
        else:
            print "\nSuccessfully sourced: ",
            if self.source_version:
                print Style.bright + str(self.source_version.spec) + \
                    Style.reset + "\n"
            else:
                print Style.bright + str(self.source.spec) + " [latest]" + \
                    Style.reset + "\n"

    # ------------------------------------------------------------------------
    def validate(self):

        super(PTaskSourceAction, self).validate()

        # ---- make sure the destination location is the current location.

        cur_loc_code = current_location_code()

        if self.destination_version:
            dest_loc_code = self.destination_version.location_code
        else:
            dest_loc_code = self.destination_latest_version.location_code

        if cur_loc_code != dest_loc_code:
            raise ActionError("Destination location must be this location.")

