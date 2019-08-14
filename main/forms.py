import datetime
from collections import defaultdict


from django.forms import Form, CharField, EmailField, SlugField, ValidationError, ModelChoiceField, IntegerField, ModelForm, ModelMultipleChoiceField, BooleanField, NullBooleanField, ChoiceField, DateField, DateTimeField
from django.forms.widgets import CheckboxSelectMultiple, RadioSelect, CheckboxInput
from django.utils import timezone

# import main.views
import main.scheduling_config
import main.models
import people.models
import main.notifications

from main.widgets import DatePickerInput


NA_YES_NO = ((None, 'N/A'), (True, 'Yes'), (False, 'No'))
SHIFT_RANKS = ((1, '1'), (2, '2'), (3, '3'), (None, 'No'))

"""
todo:

- adjust rescheduling boundaries from CLASSROOM_SETTINGS
"""

from django.utils.safestring import mark_safe

# class HorizontalRadioRenderer(RadioSelect.renderer):
#   def render(self):
#     return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))



class PreferenceSubmitForm(Form):
    def __init__(self, *args, **kwargs):
        for attr in ('shifts_dict',
                     'child',
                     'period',
                     'existing_prefs'):
            setattr(self, attr, kwargs.pop(attr))
        super().__init__(*args, **kwargs)
        self.fields.update({str(sh_pk) : ChoiceField(choices=SHIFT_RANKS,
                                                     widget=RadioSelect(
                                                         # renderer=HorizontalRadioRendere
                                                     ),
                                                     initial=None,
                                                     label=str(self.shifts_dict[sh_pk]),
                                                     required=False)
                            for sh_pk in self.shifts_dict})
        self.fields['note'] = CharField(max_length=1024)

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        num_ranked = sum(1 for value in self.cleaned_data.values()
                         if value != "")
        # print("self.cleaned_data.items()", self.cleaned_data.items())
        min_prefs = main.scheduling_config.SHIFTPREFERENCE_MIN
        if num_ranked < min_prefs:
            raise ValidationError(f"Please give at least {min_prefs} preferences!")

    def save(self):
        if 'note' in self.changed_data:
            contents = self.changed_data['note']
            try:
                self.existing_note.contents = contents
                self.existing_note.save()
            except AttributeError:
                ShiftPreferenceNoteForPeriod.objects.create(
                    period=self.period, child=self.child, contents=contents)
        for sh_pk_str in self.changed_data:
            if self.cleaned_data[sh_pk_str] == "":
                self.existing_prefs[int(sh_pk_str)].delete()
            else:
                try:
                    revised_pref = self.existing_prefs[int(sh_pk_str)]
                    revised_pref.rank = self.cleaned_data[sh_pk_str]
                    revised_pref.save()
                except KeyError:
                    main.models.ShiftPreference.objects.create(
                        child = self.child,
                        shift = self.shifts_dict[int(sh_pk_str)],
                        rank = self.cleaned_data[sh_pk_str],
                        period = self.period)




# class WorktimeAttendanceForm(Form):

#     def __init__(self, *args, **kwargs):
#         assignables = kwargs.pop('assignables')
#         super().__init__(*args, **kwargs)
#         # print(f"FORM_KWARGS : {kwargs}")
#         self.assignables = assignables
#         for assignable in self.assignables:
#             self.fields[str(assignable.pk)] = BooleanField(
#                 label=f"{commitment.child.nickname}, {commitment}",
#             )

#     def save(self):
#         for commitment in self.commitments:
#             if str(commitment.pk) in self.changed_data:
#                 commitment.completed = self.cleaned_data[str(commitment.pk)]
#                 commitment.save()
#         return self.changed_data



class MakeChildCommitmentsForm(Form):

    def __init__(self, *args, **kwargs):
        for attr in ('child',
                     # 'available_shifts',
                     'sh_occ_deserializer'):
            setattr(self, attr, kwargs.pop(attr))
        super().__init__(*args, **kwargs)
        self.fields.update({sh_occ_str : BooleanField(required=False)
                            for sh_occ_str in self.sh_occ_deserializer})

    def clean(self, *args, monthly=False, **kwargs):
        super().clean(*args, **kwargs)
        # make sure nobody else took the requested shift 
        # this is kind of crappy but not sure how to improve
        for sh_occ_str in self.changed_data:
            if self.cleaned_data[sh_occ_str]: # i.e. if it's to be created
                sh_occ = self.sh_occ_deserializer[sh_occ_str]
                if main.models.WorktimeCommitment.objects.filter(
                        shift = sh_occ.shift,
                        start = sh_occ.start).exists():
                    raise ValidationError(
                        f"somebody already has the {sh_occ} shift!")

    def save(self):
        for sh_occ_str in self.changed_data:
            sh_occ = self.sh_occ_deserializer[sh_occ_str]
            if self.cleaned_data[sh_occ_str]: # i.e., it's to be created
                sh_occ.create_commitment(self.child)
            else:
                existing_commitment = sh_occ.commitment
                existing_commitment.delete()




class EditWorktimeCommitmentForm(Form):

    def __init__(self, *args, **kwargs):
        print(kwargs)
        self.commitment = kwargs.pop('instance')
        self.user = kwargs.pop('user')
        self.sh_occ_deserializer = kwargs.pop('sh_occ_deserializer')
        super().__init__(*args, **kwargs)
        # html_attr = {'onclick' : 'selectOnlyThis(this)'}
        widget = CheckboxInput()
        self.fields.update({sh_occ_str :
                            BooleanField(required=False,
                                         widget=widget)
                            for sh_occ_str in self.sh_occ_deserializer})


    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        yesses = [key for key, val in self.cleaned_data.items()
                  if val==True]
        if len(yesses) != 1:
            raise ValidationError("Please select exactly one new shift occurrence!");
        new_shift = main.models.ShiftOccurrence.deserialize(
            yesses[0])
        data.update({'new_shift' : new_shift})
        return data
        

    def save(self, *args, **kwargs):
        new_shiftoccurrence = self.cleaned_data['new_shift']
        if new_shiftoccurrence.start != self.commitment.start or\
           new_shiftoccurrence.shift != self.commitment.shift:
            # print("commitment hmm", self.commitment.shift, self.commitment.start, self.commitment.pk)
            old_shiftoccurrence = self.commitment.shift_occurrence()
            self.commitment.move_to(new_shiftoccurrence)
            self.commitment.save()
            main.notifications.announce_commitment_change(
                self.user, self.commitment, old_shiftoccurrence)
            return {'old_shiftoccurrence' : old_shiftoccurrence,
                    'new_shiftoccurrence' : new_shiftoccurrence}
        



class WorktimeAttendanceForm(Form):

    def __init__(self, *args, **kwargs):
        commitments = kwargs.pop('commitments')
        super().__init__(*args, **kwargs)
        # print(f"FORM_KWARGS : {kwargs}")
        self.commitments = commitments
        for commitment in self.commitments:
            self.fields[str(commitment.pk)] = NullBooleanField(
                label=f"{commitment.child.nickname}, {commitment}",
            )

    def save(self):
        for commitment in self.commitments:
            if str(commitment.pk) in self.changed_data:
                commitment.completed = self.cleaned_data[str(commitment.pk)]
                commitment.save()
        return self.changed_data



class CreateCareDayAssignmentsForm(Form):
    
    def __init__(self, *args, **kwargs):
        child = kwargs.pop('child')
        super().__init__(*args, **kwargs)
        self.child = child
        self.fields['caredays'] = ModelMultipleChoiceField(
            queryset=main.models.CareDay.objects.filter(
                classroom=self.child.classroom),
            widget=CheckboxSelectMultiple)
        self.fields['start'] = DateField(label="From (YYYY-MM-DD)")
        self.fields['end'] = DateField(label="Until (YYYY-MM-DD, inclusive)")

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
        no_worse_than = self.cleaned_data['no_worse_than']
        all_assignments = main.models.ShiftAssignmentCollection.objects.generate(
            self.period,
            no_worse_than=no_worse_than)
        if len(all_assignments) == 0:
            raise ValidationError(f"There is no way to assign everybody a shift they rank no worse than {self.cleaned_data['no_worse_than']}")
            

class PeriodForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.classroom = kwargs.pop('classroom')
        super().__init__(*args, **kwargs)

    def clean(self):
        self.instance.classroom = self.classroom
        super().clean()

    class Meta:
        model = main.models.Period
        fields = ['start', 'end', 'solicits_preferences']


class CareDayAssignmentUpdateForm(ModelForm):
    start = DateField(label="From (YYYY-MM-DD)")
    end = DateField(label="Until (YYYY-MM-DD, inclusive)")
    class Meta:
        model = main.models.Period
        fields = ['start', 'end']
    
    
