import re

from django import forms

from bootstrap_datepicker_plus.widgets import DatePickerInput

from core.models import Student
from core.utils import test_credentials
from core.errors import ScraperException


class CreateStudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ("roll_number", "date_of_birth")
        widgets = {
            "date_of_birth": DatePickerInput(),
        }

    def clean_roll_number(self):
        roll_number = self.cleaned_data["roll_number"]

        if not re.match(r"[1-2][0-9][A-Z]{2}[0-9][A-Z0-9]{2}[0-9]{2}", roll_number):
            raise forms.ValidationError("Invalid roll number")

        try:
            Student.objects.get(roll_number=roll_number)
            raise forms.ValidationError("Roll number already exists")
        except Student.DoesNotExist:
            pass

        return roll_number

    def clean(self):
        cleaned_data = super().clean()
        roll_number = cleaned_data.get("roll_number")
        date_of_birth = cleaned_data.get("date_of_birth")

        if roll_number is None:
            raise forms.ValidationError("Invalid roll number")

        if date_of_birth is None:
            raise forms.ValidationError("Invalid date of birth")

        try:
            if not test_credentials(roll_number, date_of_birth):
                raise forms.ValidationError("Invalid Roll Number/Date of Birth")
        except ScraperException as e:
            raise forms.ValidationError(str(e))
