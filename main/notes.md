
todo 

- CareDay Exceptions
- generate caredays programmatically
- generate shiftinstances programmatically

- refactorings with ModelManagers

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
