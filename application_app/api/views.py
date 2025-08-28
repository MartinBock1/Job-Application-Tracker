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
    """
    ViewSet for managing Company objects.

    Provides CRUD operations for companies with user-based filtering.
    Only authenticated users can access their own companies.
    Companies are automatically ordered by name for consistent listing.
    """
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter companies to only return those belonging to the authenticated user.

        Returns:
            QuerySet: Companies filtered by the current user
        """
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Save a new company with the authenticated user as the owner.

        Args:
            serializer: The company serializer with validated data
        """
        serializer.save(user=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Contact objects.

    Provides CRUD operations for contacts with user-based filtering.
    Contacts are linked to companies and can only be accessed by their owner.
    Ensures data isolation between different users.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter contacts to only return those belonging to the authenticated user.
        Optionally filters contacts by a company ID if provided as a query parameter.
        """
        queryset = self.queryset.filter(user=self.request.user)
        company_id = self.request.query_params.get('company_id')

        if company_id:
            try:
                queryset = queryset.filter(company_id=int(company_id))
            except (ValueError, TypeError):
                pass

        return queryset

    def perform_create(self, serializer):
        """
        Save a new contact with the authenticated user as the owner.

        Args:
            serializer: The contact serializer with validated data
        """
        serializer.save(user=self.request.user)


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Application objects.

    Provides CRUD operations for job applications with optimized database queries.
    Includes related data (notes, company, contact) for efficient data retrieval.
    All applications are filtered by user ownership for security.
    """
    serializer_class = ApplicationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get applications for the authenticated user with optimized queries.

        Uses prefetch_related for notes and select_related for company/contact
        to minimize database queries when retrieving application data.

        Returns:
            QuerySet: Applications with related data, filtered by current user
        """
        return Application.objects.filter(user=self.request.user).prefetch_related(
            'notes').select_related('company', 'contact')

    def get_serializer_context(self):
        """
        Provide request context to the serializer.

        Ensures that the serializer has access to the request object,
        which is needed for user-based queryset filtering in the serializer.

        Returns:
            dict: Context dictionary containing the request object
        """
        return {'request': self.request}

    def perform_create(self, serializer):
        """
        Save a new application with the authenticated user as the owner.

        Args:
            serializer: The application serializer with validated data
        """
        serializer.save(user=self.request.user)


class NoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Note objects.

    Provides CRUD operations for notes attached to job applications.
    Implements strict security by ensuring users can only access notes
    for applications they own. Validates application ownership during creation.
    """
    serializer_class = NoteSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get notes for applications belonging to the authenticated user.

        Uses a double filter through the application relationship to ensure
        users can only see notes for their own applications.

        Returns:
            QuerySet: Notes filtered by application ownership
        """
        user = self.request.user
        return Note.objects.filter(application__user=user)

    def perform_create(self, serializer):
        """
        Create a new note with strict application ownership validation.

        Validates that the specified application exists and belongs to the
        authenticated user before creating the note. Raises appropriate
        exceptions for missing or unauthorized applications.

        Args:
            serializer: The note serializer with validated data

        Raises:
            NotFound: If no application ID is provided in the request
            PermissionDenied: If the application doesn't exist or doesn't belong to the user
        """
        application_id = self.request.data.get('application')
        if not application_id:
            raise NotFound(detail="Application ID was not found in the request.")

        try:
            # Find the related application and verify ownership
            application_instance = Application.objects.get(
                id=application_id, user=self.request.user)
        except Application.DoesNotExist:
            # If the application doesn't exist OR doesn't belong to the user, deny access
            raise PermissionDenied("You do not have permission to add a note to this application.")

        # Save the note with the correct application instance
        serializer.save(application=application_instance)
