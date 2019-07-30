import random
import datetime

from django.test import TestCase
from people.models import *
from django.utils import timezone
from django.db import models


def random_str(len=6):
    return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(len)])

def random_date(earliest=timezone.datetime(2018,6,1,0,0,0),
                latest=timezone.datetime(2019,6,1,0,0,0)):
    return timezone.make_aware(random.uniform(earliest, latest))

def random_daterange(earliest=timezone.datetime(2018,9,1,0,0,0),
                     latest=timezone.datetime(2019,6,1,0,0,0),
                     max_delta_days=60):
    start = random_date()
    delta = datetime.timedelta(days = random.randrange(max_delta_days))
    return start, start + delta

def offset(num_dates):
    return -num_dates // 2

def sign(n):
    return -1 if n < 0 else 1 

def to_date(days_delta):
    return timezone.now().date() + sign(days_delta) * datetime.timedelta(days_delta)

def date_pair_kwargs(num_dates):
    pairs = [(i + offset(num_dates), j + offset(num_dates))
                for i in range(num_dates) for j in range(i, num_dates)]
    return {pair : dict(zip(('start', 'end'), map(to_date, pair)))
                  for pair in pairs}

def date_range(num_dates):
    for delta in range(num_dates):
        yield to_date(delta)
