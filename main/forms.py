from django.forms import Form, CharField, EmailField, SlugField, ValidationError, ModelChoiceField, IntegerField, ModelForm, ModelMultipleChoiceField

# import main.views
import main.schedule_settings
import main.models

# from django.forms.widgets import HiddenInput

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
                queryset=self.child.shifts, label=label)

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

# class WorktimeCommitmentRescheduleForm(main.views.ClassroomWorktimeMixin, Form):
    # pass
    
