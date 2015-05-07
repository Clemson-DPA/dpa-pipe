
import smtplib
from email.mime.text import MIMEText

# -----------------------------------------------------------------------------
class Notification(object):

    # -------------------------------------------------------------------------
    def __init__(self, subject, message, recipients, sender=None):
        
        self._subject = subject
        self._message = message
        self._recipients = list(set(recipients))
        self._sender = sender
        
    # -------------------------------------------------------------------------
    def send_email(self):

        msg = MIMEText(self.message)
        msg['Subject'] = self.subject

        if self.sender:
            msg['From'] = self.sender

        recipients = ", ".join(self.recipients)
        msg['To'] = recipients
        
        s = smtplib.SMTP('localhost')
        try:
            s.sendmail(self.sender, recipients, msg.as_string())
        except Exception as e:
            raise NotificationError("Failed to send notification: " + str(e))

    # -------------------------------------------------------------------------
    @property
    def message(self):
        return self._message

    # -------------------------------------------------------------------------
    @message.setter
    def message(self, msg):
        self._message = msg

    # -------------------------------------------------------------------------
    @property
    def recipients(self):
        return self._recipients

    # -------------------------------------------------------------------------
    @recipients.setter
    def recipients(self, email_addrs):
        self._recipients = email_addrs

    # -------------------------------------------------------------------------
    @property
    def sender(self):
        return self._sender

    # -------------------------------------------------------------------------
    @sender.setter
    def sender(self, addr):
        self._sender = addr

    # -------------------------------------------------------------------------
    @property
    def subject(self):
        return self._subject

    # -------------------------------------------------------------------------
    @subject.setter
    def subject(self, sub):
        self._subject = sub

# -----------------------------------------------------------------------------
class NotificationError(Exception):
    pass

