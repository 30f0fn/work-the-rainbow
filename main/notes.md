
todo 

- calendar functions need
    - concrete models by_day() method:
        - holiday should be just holiday per day
        - gatherings, etc should be the list of them per day
    - shift's by_day() class method should return
        - ordered dictionary per day, 
        - optionally with shiftassignments as values
    - careday's by_day() method should return
        - list of caredayassignmentinstances for that day
        - maybe trickier, depending on implementation


- shiftassignment has family, date and shift attributes
- caredayassignment has just family and careday attributes
  - maybe for now, add a date attribute to caredayassignments?
  - eventually, want some kind of repeatability abstraction
  - exception handling is too hard for me to deal with now



- FINISH MOVING TO MODELS THE METHODS TO GENERATE CONTENT FOR CALENDARVIEWS (E.G. SHIFTSBYDAY, SHIFTSBYWEEK, ETC.)
- CareDay Exceptions
- generate caredays programmatically
- generate shiftinstances programmatically

- want custom manager to generate e.g. Holiday.by_date(start=<start>, end=<end>)
- need managers for both one-off and repeatable (abstract) events
    - for abstract events, need to handle exceptions
    - maybe study django-scheduler again
- possibly multi-day events have start_date, end_date while necessarily single-day events just have date, yuck


refactoring the calendar contents

- want views to access events by date
- try several levels
    - caredays-by-date
        - use pure python class CareDayInstance
    - shiftinstances-by-date
        - CareDayInstance generates its ShiftInstances
    - holidays-by-date
    - different views want different amounts of this data
- to implement, try some abstract Event class
- want some general API which takes a data request and returns events indexed by date
    - events per date may be singular (careday, holiday) or maybe plural (shiftinstances)
    - how about Agenda class to package events of a given day
        - names of requested classes as fields, and corresponding instances as the values?
        - constructor might take the data itself, or might take the classes?
        - maybe each class should have a way to assemble its data for a date
            - maybe for_date() returns {'class_name':<class_name>, 'stuff':<stuff>}
- use generic wrapper to partition into weeks, if desired







interface
---------

- toggle between user perspectives: parent, scheduler, teacher, administrator
    - implement in templates
        - base template supplies perspective toggle
        - perspective supplied by perspective base template
            - base_parent.html, base_scheduler.html, etc
        - <perspective>_base.html supplies appropriate menu items

- data for each role
    - parent
        - links: parent-home, parent calendar, roster
        - home: upcoming
    - teacher
        - links: teacher-home, attendance, calendar, roster
        - home: today's shifts
    - scheduler
        - links: scheduler-home, edit class cal, edit roster, class config, prefs
        - home: 
    - admin
        - links: admin-home, admin cal, admin page, site config, scheduler panopticon


- need main splash page with some basic links plus info for people who aren't registered

- need CareDay exceptions: extra day, extended/de-extended day, cancelled day
- then want a generator or something which returns the caredayinstances for a child in some timespan
