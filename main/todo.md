
# *** CHANGING COMMITMENT VIEW ***
# weekly calendar, with radioselect of available dates (with choice mandatory)
# navigate forward/backward by week


*** use enum for roles ***

*** RELATIVIZE PERMISSIONS TO ACTIVE ROLE
- so e.g. if somebody is in parent mode, they have only parent permissions, etc

*** CLASSROOM SETTINGS
- implement as model with 1-1 key to classroom
- values
    - toggle availability of batch-rescheduling of commitments by parents
    - require permission for commitment changes less than n days away
    - notify teachers of commitment changes less than n days away



*** SHIFTASSIGNMENT INTEGRITY
- now it is possible to assign two children to the same shift occurrence...
- the auto generator assigned eleanor to the same shift occurrences as tate, so the calendar didn\'t show them but the profile page did, very confusing

** NOTIFICATIONS

- django-notifications
- use 


** TEACHER NOTIFICATION OF SHIFT CHANGE
 
- allow parent to change or request-to-teacher a change to worktime commitment
- generate for teacher either change notifier, or a request handler
- create only one notifier/handler per commitment
- notifier/handler needs to show "previous" date and "new" date
- how to define "previous", if commitment has been changed several times?
  - if parent changes several times quickly, teacher shouldn't see superseded changes
  - "previous" could be "time last viewed by any teacher in the classroom, or failing that, time commitment was created"?
  - so teacher's viewing the notice would write to the database
      - set viewed to True
      - set previous_shift_and_date to actual shift_and_date
- post for teacher a notification of commitment change history whenever commitment is changed
- to change worktime commitment, create commitmentchange object.  execution of the change object simply changes the commitment.  if its creation date is at least min_notice days from commitment date, simply execute.  Else, expose to teachers as commitmentchange_request, and execute once the request is granted.

* caredayassignments should be bounded by dates not datetimes
* this borks the super call to overlap from event

* pref submission page formatting

home page for each classroom (to post pictures...)

all roles need a home view, scheduler doesn't have one; teacher defaults to daily-calendar
give all role an 'upcoming' page as default home




preference request / submission
-----



dates
-----

make sure conversion between date and datetime makes sense...


Scheduler views
-------------------

- calendar
- edit commitments
- view/solicit classroom preferences
- try to generate commitments
- manage classroom roster

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
- fix synchronization of user's role set... way too expensive now
- maybe hook update of user's permissions fields into RelateEmailToObject (or to the add-to-teachers/schedulers/etc function) 

worktime assignment scheduling
------------------------------

- try to autogenerate
- revision ok as it stands
- what about for manual?
