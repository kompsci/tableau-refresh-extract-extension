"""Python wrapper around smtplib."""

import logging
import os
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

LOGGER = logging.getLogger()

class TSEmail():

    def __init__(self, smtp_email_host, smtp_email_port, smtp_email_sender):
        """

        Args:
            smtp_email_host (str):  SMTP Host
            smtp_email_port (str):  SMTP Email Port
            smtp_email_sender (str):   SMTP Email Sender
        """


        self.smtp_host = smtp_email_host
        self.smtp_port = smtp_email_port
        self.email_sender = smtp_email_sender


    def send_email(self, subject, body, recipients, cc=None, bcc=None, attachments=None):
        """Send email over SMTP

        Args:
            subject (str): Subject of the email
            body (str): Body of the email in HTML markup.
            recipients (list): Email addresses of users to be included in TO line.
            cc (list): Email addresses of users to be included in CC line.
            bcc (list): Email address of users to be included in BCC line.
            attachments (list): List of files fromatted in MIMEApplication attachment.
        """
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = self.email_sender
        msg['To'] = ", ".join(map(str, recipients))

        if cc:
            msg['Cc'] = ", ".join(map(str, cc))
            recipients.extend(cc)

        if bcc:
            recipients.extend(bcc)

        email_body = MIMEText(body, "html")
        msg.attach(email_body)

        if attachments:
            for attachment in attachments:
                msg.attach(attachment)

        smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
        try:
            smtp.sendmail(self.email_sender, recipients, msg.as_string())
            LOGGER.debug(
                "Successfully sent email to %s", ", ".join(map(str, recipients)))
        except smtplib.SMTPRecipientsRefused as e:
            LOGGER.error("Error sending email to %s - %s",
                         ", ".join(map(str, recipients)), e)
        finally:
            smtp.quit()

    def format_attachment(self, file_path, filename):
        """Format a file to be attached in an email using MIMEApplication.

        Args:
            file_path (str): Path to the file to be attached.
            filename (str): Name of file attached in email message.

        Returns:
            MIMEApplication: File formatted for email attachment.

        """
        if os.path.isfile(file_path):
            file_extension = Path(filename).suffix

            with open(file_path, "rb") as attach_file:
                attach_data = attach_file.read()

            attachment = MIMEApplication(attach_data, file_extension)
            attachment.add_header("Content-Disposition", "attachment",
                                  filename=filename)

            return attachment

