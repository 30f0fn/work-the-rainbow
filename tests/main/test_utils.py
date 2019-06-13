import random
import datetime

from django.test import TestCase
from people.models import *
from django.utils import timezone
from django.db import models


def random_str(len=3):
    return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(len)])

def random_date(earliest=timezone.datetime(2018,6,1,0,0,0),
                latest=timezone.datetime(2019,6,1,0,0,0)):
    return random.uniform(earliest, latest)

def random_daterange(earliest=timezone.datetime(2018,6,1,0,0,0),
                     latest=timezone.datetime(2019,6,1,0,0,0),
                     max_delta_days=60):
    start = random_date()
    delta = datetime.timedelta(days = random.randrange(max_delta_days))
    return start, start + delta
