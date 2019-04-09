import datetime
from collections import defaultdict


from django.forms import Form, CharField, EmailField, SlugField, ValidationError, ModelChoiceField, IntegerField, ModelForm, ModelMultipleChoiceField, BooleanField, NullBooleanField, ChoiceField, DateField
from django.forms.widgets import CheckboxSelectMultiple, RadioSelect
from django.utils import timezone

# import main.views
import main.scheduling_config
import main.models
import people.models

NA_YES_NO = ((None, 'N/A'), (True, 'Yes'), (False, 'No'))
SHIFT_RANKS = ((1, '1'), (2, '2'), (3, '3'), (None, 'No'))

"""
todo:

- adjust rescheduling boundaries from CLASSROOM_SETTINGS
"""


class PreferenceSubmitForm(Form):
    def __init__(self, *args, **kwargs):
        for attr in ('shifts_dict',
                     'child',
                     'period',
                     'existing_prefs'):
            setattr(self, attr, kwargs.pop(attr))
        super().__init__(*args, **kwargs)
        self.fields.update({str(sh_pk) : ChoiceField(choices=SHIFT_RANKS,
                                                     widget=RadioSelect,
                                                     initial=None,
                                                     label=str(self.shifts_dict[sh_pk]),
                                                     required=False)
                            for sh_pk in self.shifts_dict})


    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        num_ranked = sum(1 for value in self.cleaned_data.items()
                         if value is not None)
        min_prefs = main.scheduling_config.SHIFTPREFERENCE_MIN
        if num_ranked < min_prefs:
            raise ValidationError(f"Please give at least {min_prefs} preferences!")

    def save(self):
        print("CHANGED_DATA: ", self.changed_data)
        print("CLEANED_DATA: ", self.cleaned_data)
        print("EXISTING_PREFS: ", self.existing_prefs)
        for sh_pk_str in self.changed_data:
            if self.cleaned_data[sh_pk_str] == "":
                self.existing_prefs[int(sh_pk_str)].delete()
                # print("deleted something")
            else:
                # print("trying to change something")
                try:
                    # print("self.existing_prefs[int(sh_pk_str)] :" , self.existing_prefs[int(sh_pk_str)])
                    # print("self.cleaned_data[sh_pk_str]", self.cleaned_data[sh_pk_str])
                    new_pref = self.existing_prefs[int(sh_pk_str)]
                    new_pref.rank = self.cleaned_data[sh_pk_str]
                    new_pref.save()
                    # self.existing_prefs[int(sh_pk_str)].rank\
                        # = self.cleaned_data[sh_pk_str]
                except KeyError:
                    # print("creating a new preference")
                    main.models.ShiftPreference.objects.create(
                        child = self.child,
                        shift = self.shifts_dict[int(sh_pk_str)],
                        rank = self.cleaned_data[sh_pk_str],
                        period = self.period)




class MakeChildCommitmentsForm(Form):

    def __init__(self, child, available_shifts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child = child
        self.available_shifts = available_shifts
        self.fields.update({sh.serialize() : BooleanField(required=False)
                            for sh in self.available_shifts})

    def clean(self, *args, monthly=False, **kwargs):
        super().clean(*args, **kwargs)
        # todo: verify that no commitment exists for each newly added shift
        # todo: below check is buggy
        # num_shifts = len([pk for pk in self.cleaned_data
        #                   if self.cleaned_data[pk]])
        # if monthly and num_shifts > self.child.shifts_per_month:
        #     # maybe only a warning here? 
        #     raise ValidationError(f"The child of {self.child} needs only {self.child.shifts_per_month}, but this assigns them {num_shifts}")

    # todo reduce db hits?
    def revise_commitments(self):
        revisions = defaultdict(list)
        for sh_field in self.changed_data:
            sh = main.models.ShiftOccurrence.deserialize(sh_field)
            if self.cleaned_data[sh_field]:
                revisions['added'].append(sh)
                # current deserializing hits db; avoid this?
                sh.create_commitment(self.child)
            else:
                main.models.WorktimeCommitment.objects.get(
                    child=self.child,
                    start=sh.start).delete()
                revisions['removed'].append(sh)
        return revisions


class RescheduleWorktimeCommitmentForm(Form):

    def __init__(self, child, current_commitment, available_shifts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child = child
        self.current_commitment = current_commitment
        self.available_shifts = available_shifts
        # todo can't i just use pk instead of serialize?
        choices = ((sh.serialize(), str(sh)) for sh in available_shifts)
        # for choice in choices:
        #     print(choice)
        self.fields.update({'shift_occ' : ChoiceField(
            choices=choices,
            widget=RadioSelect,
            label="")})
        # print('initial: ', kwargs.get('initial'))
        # for ch in self.fields['shift_occ'].choices:
            # print(ch[0])
        # print(self.fields['shift_occ'].choices)


    def execute(self, *args, **kwargs):
        data = self.cleaned_data
        new_shift = main.models.ShiftOccurrence.deserialize(
            self.cleaned_data.get('shift_occ'))
        old_start = self.current_commitment.start
        if new_shift.start != old_start:
            new_start = timezone.make_aware(new_shift.start)
            self.current_commitment.start = new_start
            self.current_commitment.end = new_shift.end
            self.current_commitment.save()
            return {'old_start' : old_start,
                    'new_start' : new_start}




class WorktimeAttendanceForm(Form):

    def __init__(self, *args, **kwargs):
        commitments = kwargs.pop('commitments')
        super().__init__(*args, **kwargs)
        print(f"FORM_KWARGS : {kwargs}")
        self.commitments = commitments
        for commitment in self.commitments:
            self.fields[str(commitment.pk)] = NullBooleanField(
                label=commitment.child.nickname
                # widget=RadioSelect(choices=NA_YES_NO)
            )


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
        child = kwargs.pop('child')
        super().__init__(*args, **kwargs)
        self.child = child
        self.fields['caredays'] = ModelMultipleChoiceField(
            queryset=main.models.CareDay.objects.filter(
                classroom=self.child.classroom),
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
            print("CAREDAY", careday)

class GenerateShiftAssignmentsForm(Form):
    worst_rank_choices = ((1, '1'), (2, '2'), (3, '3'))
    no_worse_than = ChoiceField(choices=worst_rank_choices,
                                initial=1,
                                label="require each rank to be no worse than")

    def __init__(self, *args, **kwargs):
        period = kwargs.pop('period')
        super().__init__(*args, **kwargs)
        self.period = period

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        all_assignments = ShiftAssignmentCollection.objects.create_optimal(self.period,
                                                                           no_worse_than)
        if len(all_assignments) == 0:
            raise ValidationError(f"There is no way to assign everybody a shift they rank no worse than {self.cleaned_data['no_worse_than']}")
            

class PeriodForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.classroom = kwargs.pop('classroom')
        super().__init__(*args, **kwargs)

    def clean(self):
        self.instance.classroom = self.classroom
        # print(self.instance)
        # print(self.instance.start)
        # print(self.instance.end)
        # overlaps = main.models.Period.objects.overlaps(
        #     self.instance.start, self.instance.end).filter(
        #         classroom=self.classroom)
        # print(overlaps)
        # if main.models.Period.objects.overlaps(
        #         self.instance.start, self.instance.end).filter(
        #             classroom=self.classroom).exists():
        #     raise ValidationError("an existing period for that classroom overlaps with the proposed one")
        super().clean()

    class Meta:
        model = main.models.Period
        fields = ['start', 'end', 'solicits_preferences']
