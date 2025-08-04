from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound

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
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).prefetch_related(
            'notes').select_related('company', 'contact')
    
    def get_serializer_context(self):
        """
        Stellt sicher, dass der Serializer Zugriff auf das request-Objekt hat.
        """
        return {'request': self.request}
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(application__user=user)

    def perform_create(self, serializer):
        application_id = self.request.data.get('application')
        if not application_id:
            raise NotFound(detail="Application ID wurde nicht im Request gefunden.")

        try:
            # Finde die zugehörige Bewerbung und prüfe die Eigentümerschaft
            application_instance = Application.objects.get(id=application_id, user=self.request.user)
        except Application.DoesNotExist:
            # Wenn die Bewerbung nicht existiert ODER dem User nicht gehört, verweigere den Zugriff.
            raise PermissionDenied("Sie haben keine Berechtigung, eine Notiz zu dieser Bewerbung hinzuzufügen.")
        
        # Speichere die Notiz und übergebe die korrekte 'application'-Instanz.
        serializer.save(application=application_instance)
