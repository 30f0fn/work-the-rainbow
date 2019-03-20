from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_invite_email(email, token):
    subject = 'bigelow worktime invitation'
    message = render_to_string('people/email/invite.txt',
                             {'email':email, 'token':token})
    email_from = settings.EMAIL_SENDER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)


