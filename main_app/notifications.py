from push_notifications.models import GCMDevice

def android_all_notification(title, message, image, extra):
    devices = GCMDevice.objects.filter(active=True)
    devices.send_message(
        title=title,
        message=message,
        image=image,
        extra=extra
    )

def android_admin_notification(title, message, image, extra):
    devices = GCMDevice.objects.filter(user__is_superuser=True)
    devices.send_message(
        title=title,
        message=message,
        image=image,
        extra=extra
    )

def android_user_notification(user, title, message, image, extra):
    devices = GCMDevice.objects.filter(user=user, active=True)
    devices.send_message(
        title=title,
        message=message,
        image=image,
        extra=extra
    )