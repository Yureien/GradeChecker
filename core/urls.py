from django.urls import path
from django.contrib.auth import views as auth_views

import core.views as views

urlpatterns = [
    # Logged-in users only
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
    # Authentication
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/auth/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
