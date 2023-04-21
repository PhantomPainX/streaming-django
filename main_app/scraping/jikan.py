import requests
import json
from main_app.models import Anime
import datetime

def get_str_day(n_day):
    if n_day == 0:
        return "Monday"
    elif n_day == 1:
        return "Tuesday"
    elif n_day == 2:
        return "Wednesday"
    elif n_day == 3:
        return "Thursday"
    elif n_day == 4:
        return "Friday"
    elif n_day == 5:
        return "Saturday"
    elif n_day == 6:
        return "Sunday"

def episodes_schedule():
    current_day = get_str_day(datetime.datetime.today().weekday())
    url = "https://api.jikan.moe/v4/schedules?filter=Monday"
    response = requests.get(url)
    html = response.text
    return json.loads(html)
