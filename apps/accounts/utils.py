from django.urls import reverse

from .models import UserNotification


def notify_user(user, title, message, notification_type='system', url=''):
    if not user or not getattr(user, 'is_authenticated', False):
        return None

    return UserNotification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        url=url,
    )


def notification_url(name, *args, **kwargs):
    try:
        return reverse(name, args=args, kwargs=kwargs)
    except Exception:
        return ''
