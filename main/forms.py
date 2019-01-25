import datetime

from django.forms import Form, CharField, EmailField, SlugField, ValidationError, ModelChoiceField, IntegerField, ModelForm, ModelMultipleChoiceField, BooleanField
from django.forms.widgets import CheckboxSelectMultiple, RadioSelect


# import main.views
import main.schedule_settings
import main.models
from main.models import ClassroomWorktimeMixin, ShiftInstance, WorktimeCommitment
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


class WorktimeCommitmentRescheduleForm(ClassroomWorktimeMixin, ModelForm):

    def __init__(self, *args, **kwargs):
        # earliest, latest should be adjustable in CLASSROOM_SETTINGS
        super().__init__(*args, **kwargs)
        earliest = max(datetime.datetime.now().date() + datetime.timedelta(days=1),
                       self.instance.date - datetime.timedelta(days=7))
        latest = self.instance.date + datetime.timedelta(days=7)
        family = self.instance.family
        queryset = main.models.ShiftInstance.objects.filter(
            date__range=(earliest, latest),
            worktimecommitment=None,
            shift__in=family.shifts)
        self.fields['shift_instance'] = ModelChoiceField(queryset=queryset,
                                                         widget=RadioSelect,
                                                         empty_label=None)

    class Meta:
        model = main.models.WorktimeCommitment
        fields = ['shift_instance']

    
# scheduling form
# for each family, select multiple shiftinstances

# show a range of weeks, and all shifts for each day in each week
# give a checkbox option for each shift available to a given family
# indicate preferences at each available shift

# a single selectmultiple field with options = shifts available to family
# in view, list all families with nonzero obligations, with remaining needed commitments

class MakeFamilyCommitmentsForm(Form):

    def __init__(self, family, start_date, end_date, existing_commitments, available_shifts,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        self.family = family
        self.existing_commitments = existing_commitments
        self.shift_instances = available_shifts
        self.fields.update({str(si.pk) : BooleanField(required=False)
                            for si in self.shift_instances})

    def clean(self, *args, monthly=True, **kwargs):
        super().clean(*args, **kwargs)
        # todo: verify that no commitment exists for each newly added shift
        num_shifts = len([pk for pk in self.cleaned_data
                          if self.cleaned_data[pk]])
        if monthly and num_shifts > self.family.shifts_per_month:
            # maybe only a warning here? 
            raise ValidationError(f"The family of {self.family} needs only {self.family.shifts_per_month}, but this assigns them {num_shifts}")

    # for each shiftinstance option in the shiftinstancesfield,
    # if it is checked but no commitment yet exists, create a corresponding commitment
    # if it is unchecked, delete corresponding commitment

    def shifts_to_add(self):
        return [ShiftInstance.objects.get(pk=int(si_pk))
                for si_pk in self.cleaned_data 
                if (self.cleaned_data[si_pk] and
                    int(si_pk) not in [si.pk for si in self.existing_commitments])]

    def shifts_to_remove(self):
        return [si for si in self.existing_commitments
                  if (str(si.pk) in self.cleaned_data and
                      not self.cleaned_data[str(si.pk)])]
        
    def revise_commitments(self, to_add, to_remove):
        for si in to_add:
            WorktimeCommitment.objects.create(
                shift_instance=si, family=self.family)
        for si in to_remove:
            si.worktimecommitment_set.filter(family=self.family).delete()


