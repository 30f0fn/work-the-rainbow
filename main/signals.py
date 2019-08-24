from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from main.models import Period, ShiftPreference
from main import notifications

# import notifications

# @receiver(pre_save, sender=Period)
def solicit_prefs_for_period(sender, *args, **kwargs):
    """update"""
    period_instance = kwargs['instance']
    if getattr(period_instance, 'pk') is not None:
        print(f"period already saved!")
        saved_period = sender.objects.filter(pk=period_instance.pk).first()
        if saved_period and\
           (saved_period.solicits_preferences or\
            not period_instance.solicits_preferences):
            pass
        submitted_already = {pref.child for pref in
                             ShiftPreference.objects.filter(
                                 period_id=saved_period.id)}
        children = [child for child in saved_period.classroom.child_set.all()
                    if child not in submitted_already]
        print(children)
    else:
        print(f"period being created")
        children = period_instance.classroom.child_set.all()
    for child in children:
        print("hmmmmmmm")
        for parent in child.parent_set.all():
            # print(child.parent_set)
            print("hmmm", parent)
            notifications.solicit_shiftpreferences(parent, child, period_instance)


# @receiver(post_save, sender=Period)
def solicit_prefs_for_period(sender, instance, created, *args, **kwargs):
    if not create:
        return
    instance = kwargs['instance']
    submitted_already = {pref.child for pref in
                         ShiftPreference.objects.filter(
                             period_id=saved_period.id)}
    children = [child for child in saved_period.classroom.child_set.all()
                if child not in submitted_already]
    for child in children:
        print("hmmmmmmm")
        for parent in child.parent_set.all():
            # print(child.parent_set)
            print("hmmm", parent)
            notifications.solicit_shiftpreferences(parent, child, period_instance)
