import datetime
from collections import defaultdict

from django.forms import Form, CharField, EmailField, SlugField, ValidationError, ModelChoiceField, IntegerField, ModelForm, ModelMultipleChoiceField, BooleanField, NullBooleanField, ChoiceField, DateField
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




class MakeFamilyCommitmentsForm(Form):

    def __init__(self, family, available_shifts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        self.available_shifts = available_shifts
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

    def __init__(self, family, current_commitment, available_shifts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        self.current_commitment = current_commitment
        self.available_shifts = available_shifts
        choices = ((sh.serialize(), str(sh)) for sh in available_shifts)
        # for choice in choices:
        #     print(choice)
        self.fields.update({'shift_occ' : ChoiceField(
            choices=choices,
            widget=RadioSelect)})
        print('initial: ', kwargs.get('initial'))
        for ch in self.fields['shift_occ'].choices:
            print(ch[0])
        # print(self.fields['shift_occ'].choices)


    def execute(self, *args, **kwargs):
        data = self.cleaned_data
        new_shift = main.models.ShiftOccurrence.deserialize(
            self.cleaned_data.get('shift_occ'))
        old_start = self.current_commitment.start
        if new_shift.start != old_start:
            self.current_commitment.start = new_shift.start
            self.current_commitment.end = new_shift.end
            self.current_commitment.save()
            return {'old_start' : old_start,
                    'new_start' : new_shift.start}




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

class CreateCareDayAssignmentsForm(Form):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child = kwargs.get('child')
        self.fields['caredays'] = ModelMultipleChoiceField(
                queryset=CareDay.objects.filter(
                    classroom=child.classroom),
                label=label,
                widget=CheckboxSelectMultiple)
        self.fields['start'] = DateField()
        self.fields['end'] = DateField()

    def save(self):
        caredays = self.cleaned_data['caredays']
        start = self.cleaned_data['start']
        end = self.cleaned_data['end']
        for careday in caredays:
            main.models.CareDayAssignment.objects.create(
                child=self.child,
                careday=careday,
                start=start,
                end=end)

