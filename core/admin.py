from django.contrib import admin
from .models import Student, Semester, Subject, StudentSemester, StudentSubject

admin.site.register(Student)
admin.site.register(Semester)
admin.site.register(Subject)
admin.site.register(StudentSemester)
admin.site.register(StudentSubject)
