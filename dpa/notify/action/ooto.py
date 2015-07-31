
from .base import BaseNotifyAction
from dpa.action import ActionError
from dpa.config import Config
from dpa.ptask.area import PTaskArea
from dpa.shell.output import Output, Style
from dpa.user import User, UserError

# -----------------------------------------------------------------------------

OOTO_CONFIG_PATH = "config/notify/ooto.cfg"

# -----------------------------------------------------------------------------
class OotoNotifyAction(BaseNotifyAction):
    """Out of the office notification action."""

    name = "ooto"

    # -------------------------------------------------------------------------
    def prompt(self):

        if self._message is None:
            self._message = Output.prompt_text_block(
                Style.bright + \
                "\nEnter OOTO message" + \
                Style.normal,
                blank=False,
                help_str="OOTO message can't be blank.",
            )

    # -------------------------------------------------------------------------
    def validate(self):

        if not self._message:
            raise ActionError("Message can not be empty.")

        try:
            self._sender = User.current()
        except UserError:
            raise ActionError("Could not identify current user.")

        # get ooto notification recipients from the configs
        ptask_area = PTaskArea.current()
        ooto_config = ptask_area.config(
            OOTO_CONFIG_PATH,
            composite_ancestors=True,
            composite_method="append",
        )

        ooto_notify = ooto_config.get('notify', [])
        self._to.extend(ooto_notify)

        # for all usernames specified, make sure they're a valid user,
        # get their email addresses.
        recipients = set()
        for recipient in self._to:
            
            # assume already a valid email address
            if "@" in recipient:
                recipients.add(recipient)
            else:
                try:
                    recipient = User.get(recipient)
                except UserError:
                    raise ActionError(
                        "Could not identify user: " + str(recipient)
                    )
                else:
                    recipients.add(recipient.email)

        if not recipients:
            recipients = [self._sender.email]

        self._to = recipients

        # tag the message with a signature, including the current ptask area
        # if there is one. 
        if ptask_area:
            self._message += "\n\nCurrent ptask: {p}".format(p=ptask_area.spec)
        self._message += "\n\n- {s}".format(s=self._sender.full_name)

        self._subject = "OOTO: {fn} ({un})".format(
            fn=self.sender.full_name,
            un=self.sender.username,
        )

