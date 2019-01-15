from django import template

register = template.Library()

# @register.simple_tag(takes_context=True)
# def worktime_commitment(context, date, hour, minute):
#     when = datetime.datetime.combine(date, datetime.time(hour, minute))
#     worktime = context['worktime_commitments_by_day'][when]
#     return worktime


    
