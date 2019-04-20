





ESSENTIAL



Future

- settings for classroom... how to implement?  as model class with FK to classroom?
- post for teacher a message of commitment change history whenever commitment is changed
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
