from django import template
from django.db.models import F

from core.models import StudentSubject, StudentSemester


register = template.Library()


@register.simple_tag
def get_fail_subjects_count(student_semester_id: int, department: str) -> int:
    return StudentSubject.objects.filter(
        student__department=department,
        grade=StudentSubject.Grade.F,
        semester__semester__id=student_semester_id,
    ).count()


@register.simple_tag
def get_fail_students_count(student_semester_id: int, department: str) -> int:
    return StudentSemester.objects.filter(
        semester__id=student_semester_id,
        student__department=department,
        credits_cleared__lt=F("credits_taken"),
    ).count()
