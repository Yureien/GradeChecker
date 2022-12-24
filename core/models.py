import uuid

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

from core.utils import get_data


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roll_number = models.CharField(max_length=10, unique=True)
    year_enrolled = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )
    department = models.CharField(max_length=3, blank=True, null=True)
    date_of_birth = models.DateField()
    name = models.CharField(max_length=128, blank=True, null=True)
    course = models.CharField(max_length=128, blank=True, null=True)
    cgpa = models.DecimalField(decimal_places=2, max_digits=4, null=True)
    acgpa = models.DecimalField(decimal_places=2, max_digits=4, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.roll_number})"
        else:
            return f"{self.roll_number}"

    @property
    def sgpa_latest(self):
        return self.studentsemester_set.latest("number").sgpa

    def save(self):
        if self.department is None:
            dept = self.roll_number[2:4]
            # TODO: Use a dict, and hopefully get rid of this abomination
            # Use a choice list
            if dept == "IE":
                dept = "EE"
            if dept == "MF":
                dept = "ME"
            self.department = dept
        if self.year_enrolled is None:
            self.year_enrolled = 2000 + int(self.roll_number[:2])
        super().save()

    def update(self):
        data = get_data(self.roll_number, self.date_of_birth)
        self.name = data["name"]
        self.course = data["course"]
        self.cgpa = data["cgpa"]
        self.acgpa = data["acgpa"]
        self.save()

        for semester in data["semesters"]:
            semester_obj, _ = Semester.objects.get_or_create(
                year=semester["year"],
                period=semester["period"],
            )
            try:
                student_semester = StudentSemester.objects.get(
                    student=self,
                    semester=semester_obj,
                )
            except StudentSemester.DoesNotExist:
                student_semester = StudentSemester(student=self, semester=semester_obj)
            student_semester.number = semester["number"]
            student_semester.ncgpa = semester["ncgpa"]
            student_semester.cgpa = semester["cgpa"]
            student_semester.sgpa = semester["sgpa"]
            student_semester.acgpa = semester["acgpa"]
            student_semester.asgpa = semester["asgpa"]
            student_semester.credits_taken = semester["credits_taken"]
            student_semester.credits_cleared = semester["credits_cleared"]
            student_semester.total_credits_taken = semester["total_credits_taken"]
            student_semester.total_credits_cleared = semester["total_credits_cleared"]
            student_semester.addn_credits_taken = semester["addn_credits_taken"]
            student_semester.addn_credits_cleared = semester["addn_credits_cleared"]
            student_semester.addn_total_credits_taken = semester[
                "addn_total_credits_taken"
            ]
            student_semester.addn_total_credits_cleared = semester[
                "addn_total_credits_cleared"
            ]
            student_semester.save()

            for subject in semester["subjects"]:
                try:
                    subject_obj = Subject.objects.get(code=subject["code"])
                except Subject.DoesNotExist:
                    subject_obj = Subject(code=subject["code"])
                subject_obj.name = subject["name"]
                subject_obj.credits = subject["credits"]
                subject_obj.lectures = subject["lectures"]
                subject_obj.tutorials = subject["tutorials"]
                subject_obj.practicals = subject["practicals"]
                subject_obj.save()
                try:
                    student_subject = StudentSubject.objects.get(
                        student=self,
                        subject=subject_obj,
                        semester=student_semester,
                    )
                except StudentSubject.DoesNotExist:
                    student_subject = StudentSubject(
                        student=self,
                        subject=subject_obj,
                        semester=student_semester,
                    )
                student_subject.sub_type = subject["sub_type"]
                student_subject.assign_grade(subject["grade"])
                student_subject.save()


class Semester(models.Model):
    class SemesterPeriod(models.IntegerChoices):
        SPRING = 1, "Spring"
        AUTUMN = 2, "Autumn"

    year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )
    period = models.IntegerField(choices=SemesterPeriod.choices)

    class Meta:
        unique_together = ("year", "period")

    def __str__(self):
        return f"{self.year} {self.get_period_display()}"


class StudentSemester(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    number = models.IntegerField()
    ncgpa = models.DecimalField(decimal_places=2, max_digits=4)
    cgpa = models.DecimalField(decimal_places=2, max_digits=4)
    sgpa = models.DecimalField(decimal_places=2, max_digits=4)
    acgpa = models.DecimalField(decimal_places=2, max_digits=4)
    asgpa = models.DecimalField(decimal_places=2, max_digits=4)
    credits_taken = models.IntegerField()
    credits_cleared = models.IntegerField()
    total_credits_taken = models.IntegerField()
    total_credits_cleared = models.IntegerField()
    addn_credits_taken = models.IntegerField()
    addn_credits_cleared = models.IntegerField()
    addn_total_credits_taken = models.IntegerField()
    addn_total_credits_cleared = models.IntegerField()

    class Meta:
        unique_together = ("student", "semester")

    def __str__(self):
        return f"{self.student} - Semester {self.number}"


class Subject(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    credits = models.IntegerField()
    lectures = models.IntegerField()
    tutorials = models.IntegerField()
    practicals = models.IntegerField()

    def __str__(self):
        return f"{self.code} | {self.name}"


class StudentSubject(models.Model):
    class Grade(models.IntegerChoices):
        EX = 10, "EX"
        A = 9, "A"
        B = 8, "B"
        C = 7, "C"
        D = 6, "D"
        P = 5, "P"
        F = 0, "F"
        U = -1, "Unknown"

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.ForeignKey(
        StudentSemester, on_delete=models.CASCADE, related_name="subjects"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    sub_type = models.CharField(max_length=32)
    grade = models.IntegerField(choices=Grade.choices)

    class Meta:
        unique_together = ("student", "semester", "subject")

    def __str__(self):
        return f"{self.student} - {self.subject}"

    def assign_grade(self, grade):
        if grade not in self.Grade.values:
            self.grade = self.Grade.U
        self.grade = self.Grade(getattr(self.Grade, grade))

    @property
    def grade_letter(self):
        return self.Grade(self.grade).label
