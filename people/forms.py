from django.forms import Form, CharField, EmailField, SlugField, ValidationError, ModelChoiceField, IntegerField
from django.forms.widgets import HiddenInput
from . import models

# forms for initial classroom setup

class PersonForm(Form):
    first_name = CharField()
    last_name = CharField()


class AddChildForm(PersonForm):
    short_name = CharField()
    shifts_per_month = IntegerField()
    parent_email_1 = EmailField()
    parent_email_2 = EmailField(required=False)




class AddTeacherForm(PersonForm):
    email = EmailField()


class CreateClassroomForm(Form):
    slug = SlugField()
    name = CharField()
    def clean_slug(self):
        check_unique(self, 'email', Classroom)
    def clean_name(self):
        check_unique(self, 'name', Classroom)


# maintenance forms

class UserProfileForm(PersonForm):
    email = EmailField()
    def clean_email(self):
        check_unique(self, 'email', User)


class ParentForm(UserProfileForm):
    pass


class TeacherProfileForm(UserProfileForm):
    classroom = ModelChoiceField(queryset=models.Classroom.objects.all())


def check_unique(form_instance, field_name, model, error_message=None):
    if not error_message:
        error_message = f"some {instance.model.__name__} already has a {field_name} with the value {value}"
    if not isinstance(value, six.text_type):
        return
    value = form_instance.cleaned_data['field_name'].normalize('NFKC', value)
    if hasattr(value, 'casefold'):
        value = value.casefold()  # pragma: no cover
    if model._default_manager.filter(**{f'{field_name}__iexact': value}).exists():
        raise ValidationError(error_message, code='unique')
