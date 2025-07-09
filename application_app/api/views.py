from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ..models import (
    Company,
    Contact,
    Application,
    Note
)
from .serializers import (
    CompanySerializer,
    ContactSerializer,
    ApplicationSerializer,
    NoteSerializer
)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.prefetch_related(
        'notes').select_related('company', 'contact').all()
    serializer_class = ApplicationSerializer
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
