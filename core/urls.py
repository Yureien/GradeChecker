from django.urls import path
import core.views as views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("student/add/", views.StudentFormView.as_view(), name="student-add"),
    path("student/show/", views.StudentShowView.as_view(), name="student-show"),
    path(
        "student/<pk>/",
        views.StudentDetailView.as_view(),
        name="student-detail",
    ),
    path(
        "student/<pk>/update/",
        views.StudentUpdateView.as_view(),
        name="student-update",
    ),
    path(
        "student/",
        views.StudentListView.as_view(),
        name="student-list",
    ),
    path("statistics/", views.StatisticsView.as_view(), name="statistics"),
]
