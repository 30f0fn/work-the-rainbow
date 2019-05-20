from notifications.signals import notify

"""
todo

figure out how to display these things
currently the default method of display is the hardcoded description string
the intended idea seems to be to use the inherent logical structure of activity object
but it's not clear how to make this work generally - e.g., sometimes we should print the action_object instance, sometimes we shoud just render the name of the action object class
I can only see to do it by building special Notification subclasses, adding extra data fields, and building custom render methods; would then need to override the notify() function

develop mechanism for recipient to post a response to a notification
(per source of the Notification model)
might then want to crosscut read/unread with responded/unresponded (e.g., if the notification requires response, define read as responded)
"""


DATETIME_FMT = '%-I:%M %A, %-d/%-m/%Y'

def announce_commitment_change(user,
                               commitment,
                               old_shiftoccurrence):
    other_parents = [u for u in commitment.child.parent_set.all() if u!=user]
    teachers = list(commitment.child.classroom.teacher_set.all())
    description = f"{user} moved {commitment.child}'s worktime commitment from {old_shiftoccurrence.start.strftime(DATETIME_FMT)} to {commitment.start.strftime(DATETIME_FMT)}"
    notify.send(user,
                recipient=other_parents+teachers,
                verb='updated',
                description=description)

# not in use
def announce_commitment_change_request(user,
                                       change_request):
    teachers = change_request.commitment.child.classroom.teacher_set.all()
    for teacher in teachers:
        notify.send(user,
                    recipient=teachers,
                    verb='requested',
                    action_object=preference_request)

# not in use
def solicit_shiftpreferences(user, preference_request):
    parents = preference_request.period.classroom.parent_set.all()
    notify.send(user,
                recipient=parents,
                verb='requested',
                action_object=preference_request)


