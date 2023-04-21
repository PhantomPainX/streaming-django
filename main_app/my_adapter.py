from django.contrib.auth import get_user_model
from .models import UserExtra
User = get_user_model()
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework.response import Response


class MyAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # This isn't tested, but should work
        if sociallogin.is_existing:
            return

            # some social logins don't have an email address, e.g. facebook accounts
            # with mobile numbers only, but allauth takes care of this case so just
            # ignore it
        if 'email' not in sociallogin.account.extra_data:
            print('no email')
            return
        else:
            print('email found')
        try:
            user = User.objects.get(email=sociallogin.user.email)
            #get or create user_extra
            user_extra, created = UserExtra.objects.get_or_create(user=user)
            sociallogin.connect(request, user)
            # Create a response object
            raise ImmediateHttpResponse('hello')
        except User.DoesNotExist:
            pass