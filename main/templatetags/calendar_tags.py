from django import template

register = template.Library()

# @register.simple_tag(takes_context=True)
# def worktime_commitment(context, date, hour, minute):
#     when = datetime.datetime.combine(date, datetime.time(hour, minute))
#     worktime = context['worktime_commitments_by_day'][when]
#     return worktime
    
@register.simple_tag(takes_context=True)
def worktime_commitment(classroom, date, hour, minute):
    when = datetime.datetime.combine(date, datetime.time(hour, minute))
    worktime = context['worktime_commitments_by_day'][when]
    return worktime

def worktime_commitment_by_date_hour_minute(classroom, date, hour, minute):
    return WorktimeCommitment.objects.get(classroom=classroom,
                                          shift_instance__date=date,
                                          time=datetime.time(hour, minute))
    worktime = context['worktime_commitments_by_day'][when]
    return worktime
