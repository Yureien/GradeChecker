import typing as t

from django.shortcuts import render
from django.views.generic import DetailView, View, ListView, RedirectView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.forms import ValidationError
from django.db.models import QuerySet

from core.forms import CreateStudentForm
from core.models import Student, StudentSemester


class HomeView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "core/home.html")


class StudentShowView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        try:
            student = Student.objects.get(
                roll_number=self.request.GET.get("rollno"),
                date_of_birth=self.request.GET.get("dob"),
            )
            return reverse_lazy("student-detail", kwargs={"pk": student.id})
        except Student.DoesNotExist:
            messages.error(
                self.request,
                "Invalid credentials. If the user is not added, add them first.",
            )
            return reverse_lazy("home")
        except ValidationError as e:
            messages.error(self.request, str(e))
            return reverse_lazy("home")


class StudentFormView(CreateView):
    template_name = "core/student/create.html"
    form_class = CreateStudentForm

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy("student-detail", kwargs={"pk": self.object.id})


class StudentDetailView(DetailView):
    model = Student
    template_name = "core/student/detail.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["semesters"] = StudentSemester.objects.filter(student=self.object).all()
        return context


class StudentUpdateView(View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        student = Student.objects.get(pk=pk)
        student.update()
        return redirect("student-detail", pk=pk)


class StudentListView(ListView):
    model = Student
    template_name = "core/student/list.html"
    context_object_name = "students"

    def get_ordering(self) -> t.Sequence[str]:
        ordering = []
        # TODO: Fix this abomination too
        if self.request.GET.get("sort_dept"):
            ordering.append("department")
        if self.request.GET.get("sort_rdept"):
            ordering.append("-department")
        if self.request.GET.get("sort_name"):
            ordering.append("name")
        if self.request.GET.get("sort_rname"):
            ordering.append("-name")
        if self.request.GET.get("sort_cgpa"):
            ordering.append("cgpa")
        if self.request.GET.get("sort_rcgpa"):
            ordering.append("-cgpa")
        if self.request.user.is_authenticated:
            if self.request.GET.get("sort_rollno"):
                ordering.append("roll_number")
            if self.request.GET.get("sort_rrrollno"):
                ordering.append("-roll_number")
        return ordering

    def get_queryset(self) -> QuerySet[t.Any]:
        queryset = super().get_queryset()
        if dept := self.request.GET.get("filter_dept"):
            if len(dept) == 2:
                queryset = queryset.filter(department=dept)
        if year := self.request.GET.get("filter_year"):
            if len(year) == 4 and year.isdigit():
                queryset = queryset.filter(year_enrolled=int(year))
            elif len(year) == 2 and year.isdigit():
                queryset = queryset.filter(year_enrolled=2000 + int(year))
        return queryset
