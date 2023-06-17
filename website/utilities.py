from django.core.mail import send_mail
from django.conf import settings

def send_challenge_email(to_email, from_name, applications_count):
    subject = 'Your Pingojo Challenge Invitation Awaits: Ignite your Job Hunting and Join the Competition!'
    message = f'Hello, {to_email}. I, {from_name}, have sent {applications_count} applications in the last 24 hours.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [to_email,]
    send_mail( subject, message, email_from, recipient_list )