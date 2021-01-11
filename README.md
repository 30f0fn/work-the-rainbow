# work-the-rainbow

This Django app implements a system for scheduling regular volunteer shifts (at a daycare).  It consists of two primary functionality groups, *People* and *Scheduling*.

## People

An instance of this application runs for a given daycare.  The instance organizes its human participants like so: 
- Administrator per daycare
- classrooms per daycare
- Teachers per classroom
- Schedulers per classroom
- children per classroom
- Parents per child (who will be volunteers)

The app represents a person playing any of the capitalized roles as a User.  A User may play any number of these roles; and can play a given role more than once (e.g., be a teacher in one classroom and a parent of two children in other classrooms).  

Each role affords the User a new "perspective" on the site accessible through a menu tab.

The app subsequently presents to the User a corresponding "perspective" for each role. 

To begin populating the app, the Administrator initializes the application instance for a given daycare, creates classrooms and invites a Scheduler for each classroom.  The Scheduler begins adding Teachers, children and Parents to their classroom by entering an email address for each Teacher, a name (or nickname) for each child, and email addresses for the child's Caregivers.  If the email address already corresponds to a User, the user accepts  their new role (as teacher or parent).  Otherwise, the site generates an signup invite message, so that signup licensed by the corresponding token attaches (through the Django Signals framework) the roles to the resulting new user instance.

## Scheduling

Before each period of shifts to be scheduled, the classroom scheduler creates the new period (by entering its date boundaries and holidays), and generates a shift preference solicitation email to the caregivers.
This email links to a web form to rank the family's preferred shifts; all caregivers of a given child share the same preference set.  Having collected preferences from all responsible families, the scheduler assigns shifts to families in a two-step process.

1. Choose from the resulting generated ranked list of optimal assignments of repeating time slots (say, alternate Wednesday afternoons).  

2. Given the chosen time slot assignment, choose an assignment of shift commitments for each family (say, 2pm on Sept 5, Sep 19, ...).

After any final manual tweaks, the scheduler sends the calendar to families.  Throughout the scheduled period, the families can revise any of their individual commitments; the scheduler can choose (upon consulting with teachers) whether to set a deadline for schedule changes and whether the schedule requires teacher approval.  Revisions to a family's schedule generate notifications (through the Signals framework) for all users in the family.
