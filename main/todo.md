
split into separate modules for each role, plus "trunk module"
subclass views like "calendar" from trunk module correspondingly

distinguish admin from superuser

admin, teachers should get worktime attendance management

main worktime page
- present worktimes 
    - by month (shows ~16 results)
    - by family and last four months (shows ~ eight results)
- edit attendance

reduce use of property decorators

clean up DateMixin

*** CLASSROOM SETTINGS
- implement as model with 1-1 key to classroom
- values
    - toggle availability of batch-rescheduling of commitments by parents
    - require permission for commitment changes less than n days away
    - notify teachers of commitment changes less than n days away

** todo CONCURRENCY ISSUES
- what if two people simultaneously modify same commitment?
- ensure commitment.start on form submission equals commitment.start on form

* caredayassignments should be bounded by dates not datetimes
* this borks the super call to overlap from event

* pref submission page formatting

* home page for each classroom (to post pictures..., etc)*

* home views * 

* notification for shift preference request *

all roles need a home view, scheduler doesn't have one; 
teacher defaults to daily-calendar
give all roles an 'upcoming' page as default home

google calendar export
 
Preference API
--------------

- fields: shift, child, rank, period
- view all preferences:
    - grid: child * shift
        - seems very wide
    - generic-week calendar: 
        - for each shift, list all kids who rank it
- ShiftAssignment construction
    - try to generate shiftassignment
    - manual form over generic-week calendar
        - drag-and-drop onto calendar would be great
- commitment construction
    - try to generate commitments
    - manual form over monthly calendar
        - current form probably adequate starting point
        - drag-and-drop of child onto calendar would be great

PreferencesForSchedulerView
- solicitation toggle
- select period to view
    - for given period, show table with 
        - weekdays as columns, 
        - shift-times as rows
        - ranks-per-child in each cell
from prefs, generate shiftassignments
from shiftassignment, generate worktimeassignment

Period management
- add/delete edit assignment period

Roles, etc
----------

- make sure a user's roles are correctly identified, in user.roles etc
- maybe hook update of user's permissions fields into RelateEmailToObject (or to the add-to-teachers/schedulers/etc function) 

