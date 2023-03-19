from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.conf import settings
import requests

@receiver(user_signed_up)
def send_slack_webhook(sender, **kwargs):
    user = kwargs['user']
    webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
    
    if webhook_url:
        message = f"New user signed up: {user.email} ({user.first_name} {user.last_name})"
        payload = {
            "text": message,
            "username": "Signup Notification",
            "icon_emoji": ":tada:"
        }
        requests.post(webhook_url, json=payload)
