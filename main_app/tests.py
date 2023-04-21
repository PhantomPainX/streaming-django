from django.test import TestCase

from push_notifications.models import GCMDevice

def push_notifications_view():
    try:
        devices = GCMDevice.objects.all()
        devices.send_message({"message": "Hi Android!"})
        print("Sent to Android devices")
    except:
        print("No Android devices")