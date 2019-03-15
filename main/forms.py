import datetime
from collections import defaultdict

from django.forms import Form, CharField, EmailField, SlugField, ValidationError, ModelChoiceField, IntegerField, ModelForm, ModelMultipleChoiceField, BooleanField, NullBooleanField
from django.forms.widgets import CheckboxSelectMultiple, RadioSelect


# import main.views
import main.schedule_settings
import main.models
import people.models

"""
todo:

- adjust rescheduling boundaries from CLASSROOM_SETTINGS
"""


class PreferenceSubmitForm(Form):
    # override in init to restrict choices
    # should be on contracted days for child
    # maybe also relative to classroom

    ranks = ['first_ranked', 'second_ranked', 'third_ranked']
    rank_labels = ["best", "second-best", "third-best"]

    def __init__(self, child, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child = child
        for rank, label in zip(self.ranks, self.rank_labels): 
            self.fields[rank] = ModelMultipleChoiceField(
                queryset=self.child.shifts,
                label=label,
                widget=CheckboxSelectMultiple)

    def submitted_prefs(self):
        return [self.cleaned_data[rank] for rank in self.ranks]

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        prefs = self.submitted_prefs()
        prefs_flattened = [shift for rank in prefs for shift in rank]
        num_prefs = len(set(prefs_flattened))
        min_prefs = main.schedule_settings.SHIFTPREFERENCE_MIN
        if num_prefs < min_prefs:
            raise ValidationError("Please suggest at least {min_prefs} preferences!",
                                  params={'min_prefs'})
        if num_prefs < len(prefs_flattened):
            raise ValidationError("You must have assigned multiple ranks to some shift.  I wouldn't know what to do with that...")
        if len(prefs[0]) == 0:
            raise ValidationError("Please assign at least one shift the rank 1.  Else you'd be less likely to get any of your favorite shifts.")
        if len(prefs[1]) == 0 and len(prefs[2]) > 0:
            raise ValidationError("Please move at least one of your 3-ranked slots to the rank 2.  Else you'd be less likely to get any of your listed slots.")

    def save_prefs(self):
        for rank, prefs in enumerate(self.submitted_prefs()):
            for pref in prefs:
                main.models.ShiftPreference.objects.create(family=self.child,
                                                           shift=pref,
                                                           rank=rank)


# class WorktimeCommitmentRescheduleForm(Form):

#     def __init__(self, *args, **kwargs):
#         # earliest, latest should be adjustable in CLASSROOM_SETTINGS
#         super().__init__(*args, **kwargs)
#         earliest = max(datetime.datetime.now().date() + datetime.timedelta(days=1),
#                        self.instance.date - datetime.timedelta(days=7))
#         latest = self.instance.date + datetime.timedelta(days=7)
#         family = self.instance.family
#         queryset = main.models.ShiftInstance.objects.filter(
#             date__range=(earliest, latest),
#             commitment=None,
#             shift__in=family.shifts)
#         self.fields['shift_instance'] = ModelChoiceField(queryset=queryset,
#                                                          widget=RadioSelect,
#                                                          empty_label=None)
    
# scheduling form
# for each family, select multiple shiftinstances


class MakeFamilyCommitmentsForm(Form):

    def __init__(self, family, available_shifts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        self.available_shifts = available_shifts
        print("HHEELLOO!")
        print(available_shifts)
        self.fields.update({sh.serialize() : BooleanField(required=False)
                            for sh in self.available_shifts})

    def clean(self, *args, monthly=False, **kwargs):
        super().clean(*args, **kwargs)
        # todo: verify that no commitment exists for each newly added shift
        num_shifts = len([pk for pk in self.cleaned_data
                          if self.cleaned_data[pk]])
        if monthly and num_shifts > self.family.shifts_per_month:
            # maybe only a warning here? 
            raise ValidationError(f"The family of {self.family} needs only {self.family.shifts_per_month}, but this assigns them {num_shifts}")
    
    def revise_commitments(self):
        revisions = defaultdict(list)
        for sh_field in self.changed_data:
            sh = main.models.ShiftOccurrence.deserialize(sh_field)
            if self.cleaned_data[sh_field]:
                revisions['added'].append(sh)
                # current deserializing hits db; avoid this?
                sh.create_commitment(self.family)
            else:
                main.models.WorktimeCommitment.objects.get(
                    family=self.family,
                    start=sh.start).delete()
                revisions['removed'].append(sh)
        return revisions




class RescheduleWorktimeCommitmentForm(Form):

    def __init__(self, family, current_shift, available_shifts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        self.current_shift = current_shift
        self.fields['new_shift'] = ModelChoiceField(
            queryset=available_shifts,
            widget=RadioSelect,
            empty_label=None)

    def execute(self, *args, **kwargs):
        new_shift = self.cleaned_data.get('new_shift')
        if new_shift != self.current_shift:
            self.current_shift.commitment = None
            self.current_shift.save()
            new_shift.commitment = self.family
            new_shift.save()
            return {'removed' : self.current_shift,
                    'added' : new_shift}




class CommitmentCompletionForm(Form):

    def __init__(self, *args, **kwargs):
        commitments = kwargs.pop('commitments')
        super().__init__(*args, **kwargs)
        print(f"FORM_KWARGS : {kwargs}")
        self.commitments = commitments
        for commitment in self.commitments:
            self.fields[str(commitment.pk)] = NullBooleanField()


    def save(self):
        # print("FORM SAVE METHOD CALLED!")
        # raise Exception("form save method called")
        #todo message if changed
        for commitment in self.commitments:
            if str(commitment.pk) in self.changed_data:
                commitment.completed = self.cleaned_data[str(commitment.pk)]
                commitment.save()
