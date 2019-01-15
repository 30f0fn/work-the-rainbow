worktime commitment representation
----------------------------------

- strategy: model FamilyCommitment as Occurrence of a FamilyAssignment Event; generate the Occurrences from the Event by a rule; then override manually for exceptions.

- each FamilyCommitment has this data:
    - classroom
    - family
    - date and starttime, endtime

- in turn, FamilyAssignment event has this data:
    - classroom
    - family
    - weekday
    - shiftnumber
    - period (start and end of four-month cycle) and within-period parity

calendars
---------

- calendars for bigelow, for classroom and for each family
- seems natural to use inheritance

interface
---------

- edit FamilyCommitments
    - offer FamilyCommitments to swap
    - return form with available options


