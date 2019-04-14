from django.forms import Form, CharField, EmailField, SlugField, ValidationError, ModelChoiceField, IntegerField, ModelForm, DateField

# from django.forms.widgets import HiddenInput


from people.models import Classroom, RelateEmailToObject, Child

# forms for initial classroom setup

class PersonForm(Form):
    first_name = CharField()
    last_name = CharField()


class RelateEmailToObjectForm(Form):
    email = EmailField()

    # class Meta:
        # model = RelateEmailToObject
        # fields = ['email']


class AddTeacherForm(Form):
    email = EmailField()


class AddChildForm(Form):

    nickname = CharField()
    shifts_per_month = IntegerField()
    parent_email_1 = EmailField(required=False)
    parent_email_2 = EmailField(required=False)

    def cleaned_emails(self):
        return [self.cleaned_data[email_field] for email_field in
                ['parent_email_1', 'parent_email_2'] if self.cleaned_data[email_field]]

    def clean_email(self):
        check_unique(self, 'nickname', Child)
        






class CreateClassroomForm(Form):
    scheduler_email_1 = EmailField(required=False)
    scheduler_email_2 = EmailField(required=False)
    slug = SlugField()
    name = CharField()
    def cleaned_emails(self):
        return [self.cleaned_data[email_field] for email_field in
                ['scheduler_email_1', 'scheduler_email_2'] if self.cleaned_data[email_field]]


    # def clean_slug(self):
        # check_unique(self, 'email', Classroom)
    # def clean_name(self):
        # check_unique(self, 'name', Classroom)


# maintenance forms

class UserProfileForm(PersonForm):
    email = EmailField()
    def clean_email(self):
        check_unique(self, 'email', User)


class ParentForm(UserProfileForm):
    pass


class TeacherProfileForm(UserProfileForm):
    classroom = ModelChoiceField(queryset=Classroom.objects.all())


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


class ChildUpdateForm(ModelForm):
    birthday = DateField(label="birthday (YYYY-MM-DD)", required=False)
    class Meta:
        model = Child
        fields = ['nickname', 'shifts_per_month', 'birthday', ]
    
