
from .base import BaseNotifyAction
from dpa.action import ActionError
from dpa.config import Config
from dpa.ptask import PTaskArea
from dpa.shell.output import Output, Style
from dpa.user import User, UserError

# -----------------------------------------------------------------------------

FAIL_CONFIG_PATH = "config/notify/fail.cfg"

# -----------------------------------------------------------------------------
class FailNotifyAction(BaseNotifyAction):
    """Fail notification action."""

    name = "fail"

    # -------------------------------------------------------------------------
    def prompt(self):

        if self._subject is None:
            self._subject = Output.prompt(
                Style.bright + \
                "\nEnter a one line description of the problem" + \
                Style.normal,
                blank=False,
                help_str="Subject line can't be blank.",
                separator = ":\n"
            )

        if self._message is None:
            self._message = Output.prompt_text_block(
                Style.bright + \
                "\nEnter a detailed description of the problem.\n" + \
                Style.normal + \
                " Include steps to replicate, errors, etc below.\n" + \
                " You can copy/paste below as well.\n",
                blank=False,
                help_str="Message can't be blank.",
            )

    # -------------------------------------------------------------------------
    def validate(self):

        if not self._subject:
            raise ActionError("Subject can't be empty.")

        self._subject = "FAIL: " + self._subject

        if not self._message:
            raise ActionError("Message can't be empty.")

        try:
            self._sender = User.current()
        except UserError:
            raise ActionError("Could not identify current user.")

        # get fail notification recipients from the configs
        ptask_area = PTaskArea.current()
        fail_config = ptask_area.config(
            FAIL_CONFIG_PATH,
            composite_ancestors=True,
            composite_method="append",
        )

        fail_notify = fail_config.get('notify', [])
        self._to.extend(fail_notify)

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

