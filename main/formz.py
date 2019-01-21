from django.forms import Form, CharField, EmailField, SlugField, ValidationError, ModelChoiceField, IntegerField, ModelForm, ModelMultipleChoiceField
# from django.forms.widgets import HiddenInput

class PreferenceSubmitForm(Form):
    # override in init to restrict choices
    # should be on contracted days for child
    # maybe also relative to classroom

    first_ranked = ModelMultipleChoiceField(queryset=None)
    second_ranked = ModelMultipleChoiceField(queryset=None)
    third_ranked = ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        child = self.kwargs.pop('child')
        for rank in ['first_ranked', 'second_ranked', 'third_ranked']:
            self.fields['rank'] = ModelMultipleChoiceField(
                queryset=child.shifts)
