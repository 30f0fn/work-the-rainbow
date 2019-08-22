Scheduler workflow

once preferences have been collected:
    - generate assignables
    - tweak assignables based on notes
    - generate assignments
    - review generated assignments
    - either select generated assignment, or return to assignables

so, three views:

PreferenceDisplayView
- just review submitted preferences
- include links to generate assignables, and to generate assignments directly

AssignablesView
- a form, showing for each assignable an active/inactive toggle button
- include link to generate schedules

SchedulesView
- paginate assignments by NUM_ASSIGNMENTS=10
- include links to revise assignables and to generate assignments


