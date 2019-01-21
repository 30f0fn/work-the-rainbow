worktime commitment representation
----------------------------------

- strategy: model WorktimeCommitment as Occurrence of a WorktimeAssignment Event; generate the Occurrences from the Event by a rule; then override manually for exceptions.

- each WorktimeCommitment has this data:
    - classroom
    - family
    - date and starttime, endtime

- in turn, WorktimeAssignment event has this data:
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

- edit WorktimeCommitments
    - offer WorktimeCommitments to swap
    - return form with available options




formview vs updateview

    FormView
    TemplateResponseMixin
    BaseFormView
    FormMixin
    ContextMixin
    ProcessFormView
    View


    UpdateView
    SingleObjectTemplateResponseMixin <don't need>
    <!-- TemplateResponseMixin -->
    BaseUpdateView <don't want>
    ModelFormMixin <don't want>
    <!-- FormMixin -->
    <!-- SingleObjectMixin -->
    <!-- ContextMixin -->
    <!-- ProcessFormView -->
    <!-- View -->

