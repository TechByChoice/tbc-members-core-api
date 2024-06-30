import os

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from utils.logging_helper import get_logger

logger = get_logger(__name__)


def send_dynamic_email(email_data):
    """
    Sends an email using SendGrid API with dynamic data.

    :param email_data: A dictionary containing the email details.
                       Required keys are 'subject', 'recipient_emails', 'template_id', and 'dynamic_template_data'.
    """
    # Set up the API key
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    if sendgrid_api_key is None:
        raise ValueError(
            "The SendGrid API key is not set in the environment variables."
        )

    # Create a Mail object
    message = Mail(
        from_email=os.getenv("SENDGRID_FROM_EMAIL"),
        to_emails=email_data["recipient_emails"],
    )
    message.template_id = email_data["template_id"]
    message.dynamic_template_data = email_data["dynamic_template_data"]

    try:
        # Create SendGrid client and send the email
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"Email sent with status code: {response.status_code}")
        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def send_password_email(email, first_name, user, reset_link):
    """
    Send a password reset email to the user.
    """
    mail_subject = 'Password Reset Request'

    context = {
        'username': first_name,
        'reset_link': reset_link,
    }

    message = render_to_string('emails/password_reset_email.txt', context=context)
    email_msg = EmailMessage(mail_subject, message, 'notifications@app.techbychoice.org', [email])
    email_msg.extra_headers = {
        'email_template': 'emails/password_reset_email.html',
        'username': first_name,
        'reset_link': reset_link,
    }

    try:
        email_msg.send()
    except Exception as e:
        logger.error(f"Error while sending password reset email: {str(e)}")
