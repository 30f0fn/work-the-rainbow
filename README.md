# work-the-rainbow

This Django app implements a system for scheduling regular volunteer shifts (at a daycare).  It consists of two primary functionality groups, *People* and *Scheduling*.

## People

An instance of this application runs for a given daycare.  Each instance organizes the human participants in its use into: 
- application administrator per daycare
- teachers and schedulers per classroom
- children in a given classroom
- parents or caregivers of each child (who will be volunteers)

Each person playing one or more of these roles (other than that of child) is represented by the app as a User instance.  A User instance has specialized privileges and duties corresponding to their roles.

The application administrator initializes the application instance for a given daycare, creates classrooms and invites a scheduler for each classroom.  

The scheduler populates the classroom teachers, children and caregivers by entering an email address for each teacher, a name (or nickname) for each child, and email addresses for the child's caregivers.  If the email address corresponds already to a site user instance, the user assumes the new role (as teacher of the classroom, or as caregiver of the child).  Otherwise, the site generates an signup invite message, so that signup licensed by the corresponding token attaches (through the Django Signals framework) the roles to the resulting new user instance.

## Scheduling

Before each period of shifts to be scheduled, the classroom scheduler creates the new period (by entering its date boundaries and holidays), and generates a shift preference solicitation email to the caregivers.
This email links to a web form to rank the family's preferred shifts; all caregivers of a given child share the same preference set.  
Once all responsible families have submitted preferences, the scheduler can assign shifts to families in a two-step process.

1. Choose from the resulting generated ranked list of optimal assignments to families of weekly repeating times (say, Wednesday afternoons).  

2. Choose, from the corresponding possible assignment of repeating times, an assignment of time instances to families.

After any final manual tweaks, the scheduler sends the calendar to families.  Throughout the scheduled period, the families can reschedule any of their shift instances; the scheduler can choose (upon consulting with teachers) whether to set a deadline for schedule changes and whether the schedule requires teacher approval.
