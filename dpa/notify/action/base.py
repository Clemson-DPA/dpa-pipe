
from abc import ABCMeta, abstractmethod
import smtplib
from email.mime.text import MIMEText

from dpa.action import Action, ActionError
from dpa.config import Config
from dpa.notify import Notification

# -----------------------------------------------------------------------------
class BaseNotifyAction(Action):
    """Bse notification action."""

    __metaclas__ = ABCMeta

    name = None

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        # ptask spec (name, parent) - can be relative to current ptask
        parser.add_argument(
            "-m", "--message",
            default=None,
            help="Body of the message to send.",
        )

        parser.add_argument(
            "-s", "--subject",
            default=None,
            help="Subject of the message to send.",
        )

        parser.add_argument(
            "-t", "--to",
            nargs="+",
            default=[],
            help="Space separated list of recipient usernames and/or emails",
        )

    # -------------------------------------------------------------------------
    def __init__(self, message, subject=None, to=None):

        super(BaseNotifyAction, self).__init__(message, subject=subject, to=to)

        self._message = message
        self._subject = subject
        self._to = to if to else []
        
    # -------------------------------------------------------------------------
    def execute(self):

        sender = self.sender.email

        recipients = self.to
        recipients.add(sender)

        notification = Notification(
            self.subject, self.message, list(recipients), sender)
        notification.send_email()

        if self.interactive:
            print "\nNotification sent!\n"

    # -------------------------------------------------------------------------
    @abstractmethod
    def prompt(self):
        pass

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    @abstractmethod
    def validate(self):
        pass

    # -------------------------------------------------------------------------
    @property
    def sender(self):
        return self._sender

    # -------------------------------------------------------------------------
    @property
    def subject(self):
        return self._subject

    # -------------------------------------------------------------------------
    @property
    def message(self):
        return self._message

    # -------------------------------------------------------------------------
    @property
    def to(self):
        return self._to

