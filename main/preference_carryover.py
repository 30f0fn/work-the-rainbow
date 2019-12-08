from people.models import Classroom, Child
from main.models import ShiftPreference


def corresponding_shift(new_classroom, old_shift):
    return Shift.objects.get(
        classroom=new_classroom,
        start_time=old_shift.start_time,
        weekday=old_shift.weekday)

def for_child(child, old_period, new_period):
    new_prefs = ShiftPreference.objects.filter(child=child, period=new_period)
    if new_prefs.exists():
        print(f"{child} submitted shift preferences for {new_period} already")
        return
    for old_preference in ShiftPreference.objects.filter(period=old_period,
                                                         child=child):
        sp = ShiftPreference.objects.create(child=child,
                                       shift=corresponding_shift(new_period.classroom,
                                                                 old_preference.shift),
                                       rank=old_preference.rank,
                                       period=new_period)
        print(f"created {sp}")

    if not old_period:
        try:
            latest_pref = ShiftPreference.objects.filter(
                child=child).order_by('period').last()
            old_period = latest_pref.period
        except AttributeError:
            print(f"fond no latest pref")
            return
    if not new_period:
        new_period = Period.objects.filter(
            classroom=child.classroom,
            shiftpreference__child=child).order_by('start').first()
        if not new_period:
            print(f"{child} already submitted shift preferences for all existing periods in the new classroom") 
            return



def for_classroom(classroom, old_period, new_period):
    for child in Child.objects.filter(classroom=classroom):
        print(f"creating shiftpreferences for {child}")
        for_child(child, old_period, new_period)

    

# def for_classroom(new_classroom, old_classroom):
#     old_period = ShiftPreference.objects.filter(
#         child__in=new_classroom,
#         period__classroom=old_classroom).order_by('start').last().period
#     old_prefs = ShiftPreference.objects.filter(period=old_period)

rb1 = Classroom.objects.get(slug='rb1')
    
