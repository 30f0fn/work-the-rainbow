
todo rename CareDay to CareSession

todo standardize __repr__ 

todo subclass CareDayAssignment with ContractedCareDayAssignment, for preferences etc

todo check for timezone awareness... timezone.datetime.combine seems to return non-aware datetimes (?)

todo clarify which items have meaningful datetime, which have only meaningful date

"""
for generic __str__ method:
str_attrs_list = ['attr1', 'attr2']
str_attrs = ",".join([f"{attr}={getattr(self, attr)}" for attr in self.display_attrs])
return f"<{self.__class__.__name__} {self.pk}: " + str_attrs + ">"
"""
    
"""
todo
all events have start_date
one-day events have computed property date
maybe all events have an iterator dates?  ---not useful for queries
"""

"""
what contents need to get indexed by date?

shift, careday, holiday, worktimecommitment, 
"""






what is the event API required by view functions?

kinds of event
--------------

careday, caredayassignment, shift, shiftcommitment, holiday, happening

views
-----

parent
- upcoming, calendar, edit commitments, preferences
scheduler
- assign worktimes, edit commitments...
teacher
- calendar, worktime completion

overall: 
- calendar: commitment per shift, shifts per day, maybe also kids per ShiftOccurrence
- edit-commitments: possible-shifts-per-(fixed)-child, commitments-per-shift
- upcoming: worktimes, happenings
- worktime completion: commitments per day

- todo
    - kids per shiftoccurrence; derive from kids per caredayoccurrence



the tricky one is possible-shifts-per-child
- this is built from caredays-per-child and shifts-per-careday
- two ways to access caredays of child
    - generate all caredays of child (within range)
    - check directly, using careday and date, whether child has careday
- use caredayassignment
        - to check whether child has careday, run through careday assignments in order of dt_created
- two kinds of access of possible shifts:
    - generator (presumably from caredaygenerator)
    - boolean lookup (by shiftoccurrence)
        - here, just lookup whether child has careday of shift
        - trickiness here with extended day shifts
    - need possible shifts just in generating edit-commitments form

    


each (weekly)shift has a generator for all of its actual instances; implement this as a rrule
this requires getting the holidays from the db
so, (weekly)shift generator should allow omitting holidays (use parameter forget_holidays)
then, bigelowshift has a manager, which collects together all rule from each (weekly)shift, and combines them with the holiday exclusion rule to generate all actual shiftinstances

ditto caredays

data model structure
- weeklyshift inherits from weeklyevent
- weeklycareday inherits from weeklyevent
- classroomshiftschedule has a method which calls weeklyshiftmanager
- childcaredayschedule has a method which calls weeklycaredaymanager


child -> caredayinstances of child (now ok, as intervals)
caredayinstance -> shiftinstances 
child -> available_shiftinstances

how will I need to access shifts available for child?
mainly in family's and scheduler's edit-worktime-calendar views
(also in edit-worktime-commitment view, which is less important, and just needs generator)
for calendar views, it might be helpful to have a dictionary, e.g., by filtering on the by_date_and_time manager method of the Shift class
another option is to map each time to a ShiftInstance object (or maybe just namedtuple), with the list of kids and the commitment as (optional) fields

(maybe better to call ShiftInstance maybe DatedShift)



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
