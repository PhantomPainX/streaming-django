from django import template
from main_app.models import UserExtra

root_url = "http://127.0.0.1"

register = template.Library()

@register.simple_tag
def get_user_image(request): 
    if request.user.is_authenticated:
        #get or create user_extra
        user_extra, created = UserExtra.objects.get_or_create(user=request.user)
        _user_image = root_url + "/media/" + str(user_extra.avatar)
    else:
        _user_image = root_url + "/media/users/avatars/default.webp"

    return _user_image

def url_dofollow(text):
    return text.replace('rel="nofollow"', 'rel="dofollow" target="_blank"')
url_dofollow = register.filter(url_dofollow, is_safe = True)