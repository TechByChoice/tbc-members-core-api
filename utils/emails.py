import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_dynamic_email(email_data):
    """
    Sends an email using SendGrid API with dynamic data.

    :param email_data: A dictionary containing the email details.
                       Required keys are 'subject', 'recipient_emails', 'template_id', and 'dynamic_template_data'.
    """
    # Set up the API key
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    if sendgrid_api_key is None:
        raise ValueError("The SendGrid API key is not set in the environment variables.")

    # Create a Mail object
    message = Mail(
        from_email=os.getenv("SENDGRID_FROM_EMAIL"),
        to_emails=email_data['recipient_emails']
    )
    message.template_id = email_data['template_id']
    message.dynamic_template_data = email_data['dynamic_template_data']

    try:
        # Create SendGrid client and send the email
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"Email sent with status code: {response.status_code}")
        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
