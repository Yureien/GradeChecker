from django.urls import path
import api.views as views

urlpatterns = [
    path("student/", views.StudentViewSet.as_view(), name="student_api"),
]
