import os

from django.contrib.auth.tokens import default_token_generator
from django.core.mail.backends.base import BaseEmailBackend
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from python_http_client import HTTPError
from sendgrid import SendGridAPIClient, Mail

# Define a custom email backend that uses SendGrid
from apps.core.models import CustomUser


class SendGridPasswordResetEmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        sendgrid_client = SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))

        for message in email_messages:
            message_dict = message.message()
            user = CustomUser.objects.get(email=message_dict['To'])
            # token = default_token_generator.make_token(user)
            token = message.extra_headers.get('token')
            if not token:
                # create the token for password reset
                context = {
                    'username': message_dict['username'],
                    'reset_link': message_dict['reset_link'],
                    'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                }
            else:
                context = {
                    'username': message_dict['username'],
                    'activation_link': message_dict['activation_link'],
                    'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                }
            template_path = message.extra_headers.get('email_template', 'core/new/password_reset_email.html')
            html_content = render_to_string(template_path, context)
            mail = Mail(
                from_email='notifications@app.techbychoice.org',
                to_emails=message_dict['To'],
                subject=message_dict['Subject'],
                plain_text_content=message_dict['body'],
                html_content=html_content,
            )
            try:
                sendgrid_client.send(mail)
            except HTTPError as e:
                print(e.to_dict)

    # def send_messages(self, email_messages):
    #     sendgrid_client = SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
    #
    #     for email in email_messages:
    #         user = CustomUser.objects.get(email=email.to[0])  # Assuming email.to is a list with at least one recipient
    #         context = email.extra_headers.get('context', {})  # Ensure 'context' is passed in extra_headers
    #
    #         if not context.get('token'):
    #             # Create the token if not provided in context
    #             context['token'] = default_token_generator.make_token(user)
    #
    #         # Update 'uidb64' in context for consistency
    #         context['uidb64'] = urlsafe_base64_encode(force_bytes(user.pk))
    #
    #         # Template ID for using SendGrid's dynamic templates
    #         template_id = email.extra_headers.get('template_id')
    #         if template_id:
    #             # Prepare the SendGrid Mail object with dynamic template
    #             mail = Mail(
    #                 from_email='notifications@app.techbychoice.org',
    #                 to_emails=email.to,
    #                 subject=email.subject,
    #             )
    #             mail.template_id = template_id
    #             mail.dynamic_template_data = context
    #         else:
    #             # Fallback to using custom HTML content
    #             template_path = email.extra_headers.get('email_template', 'emails/default_email.html')
    #             html_content = render_to_string(template_path, context)
    #             mail = Mail(
    #                 from_email='notifications@app.techbychoice.org',
    #                 to_emails=email.to,
    #                 subject=email.subject,
    #                 html_content=html_content,
    #             )
    #
    #         try:
    #             response = sendgrid_client.send(mail)
    #             print(f"Email sent. Status code: {response.status_code}")
    #         except Exception as e:
    #             print(f"Error sending email through SendGrid: {e}")
