from collections import namedtuple

from notifications.signals import notify

DATETIME_FMT = '%-I:%M %A, %-d/%-m/%Y'

def announce_child_to_new_classroom(user, child,
                                   old_classroom,
                                   new_classroom):
    description = f"{child} has moved from {old_classroom.name} to {new_classroom.name}!"
    notify.send(user,
                recipient=child.parent_set.all(),
                verb='updated',
                description=description)
