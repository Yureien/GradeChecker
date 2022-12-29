from rest_framework.generics import CreateAPIView
from rest_framework import authentication, permissions

from core.models import Student
from api.serializers import StudentSerializer


class StudentViewSet(CreateAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    serializer_class = StudentSerializer

    def perform_create(self, serializer):
        student: Student = serializer.save()
        student.update()