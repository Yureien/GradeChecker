import re

from core.models import Student
from rest_framework import serializers

from core.utils import test_credentials
from core.errors import ScraperException, CaptchaException


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ("roll_number", "date_of_birth")

    def validate_roll_number(self, roll_number):
        if not re.match(r"[1-2][0-9][A-Z]{2}[0-9][A-Z0-9]{2}[0-9]{2}", roll_number):
            raise serializers.ValidationError("Invalid roll number")
        return roll_number

    def validate(self, data):
        roll_number = data["roll_number"]
        date_of_birth = data["date_of_birth"]

        if roll_number is None:
            raise serializers.ValidationError("Invalid roll number")

        if date_of_birth is None:
            raise serializers.ValidationError("Invalid date of birth")

        try:
            if not test_credentials(roll_number, date_of_birth):
                raise serializers.ValidationError("Invalid Roll Number/Date of Birth")
        except CaptchaException:
            raise serializers.ValidationError("Captcha failed")
        except ScraperException as e:
            raise serializers.ValidationError(str(e))
