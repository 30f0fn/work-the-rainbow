from django.forms import DateInput

class DatePickerInput(DateInput):
    template_name = 'main/datepicker.html'
