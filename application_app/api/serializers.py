from rest_framework import serializers
from ..models import Company, Contact, Application, Note


class CompanySerializer(serializers.ModelSerializer):
    """
    Serializer for Company model.
    Handles serialization and deserialization of company data.
    The user field is read-only and automatically set based on the authenticated user.
    """
    class Meta:
        model = Company
        fields = ['id', 'name', 'website', 'industry']
        read_only_fields = ['user']


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for Contact model.
    Includes nested company information for reading and separate company_id for writing.
    This allows displaying full company details while accepting just the company ID for updates.
    """
    # Nested company data for display purposes
    company = CompanySerializer(read_only=True)
    # Company ID field for creating/updating contacts
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), source='company', write_only=True
    )

    class Meta:
        model = Contact
        fields = [
            'id',
            'company',
            'company_id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'position'
        ]


class NoteSerializer(serializers.ModelSerializer):
    """
    Serializer for Note model.
    Handles notes that can be attached to job applications.
    The ID field allows for optional identification during updates.
    """
    # Optional ID field for note identification during updates
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Note
        fields = ['id', 'text', 'created_at']
        read_only_fields = ['created_at']


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for Application model.
    Handles the complete job application data including nested relationships.
    
    Features:
    - Nested serializers for display (company, contact, notes)
    - Separate ID fields for writing relationships
    - User-filtered querysets for security
    - Intelligent note management during updates
    """
    
    # Read-only fields for displaying nested data
    company = CompanySerializer(read_only=True)
    contact = ContactSerializer(read_only=True, required=False, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    notes = NoteSerializer(many=True, required=False)  # Allows note management

    # Write-only fields for creating/updating relationships
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.none(), # Queryset is dynamically set in __init__
        source='company',
        write_only=True
    )

    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(), source='contact',
        write_only=True,
        required=False,
        allow_null=True
    )

    # Optional date field for application submission
    applied_on = serializers.DateField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer with user-filtered querysets.
        
        Filters the company_id and contact_id querysets to only include
        objects that belong to the authenticated user, ensuring data security.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request and hasattr(request, 'user'):
            user = request.user
            # Filter companies and contacts to only show user's own data
            self.fields['company_id'].queryset = Company.objects.filter(user=user)
            self.fields['contact_id'].queryset = Contact.objects.filter(user=user)
            
            
    class Meta:
        model = Application
        fields = [
            'id',
            'job_title',
            'company',
            'company_id',
            'contact',
            'contact_id',
            'status',
            'status_display',
            'applied_on',
            'interview_on',
            'offer_on',
            'rejected_on',
            'applied_on',
            'follow_up_on',
            'job_posting_link',
            'salary_expectation',
            'created_at',
            'notes'
        ]
        read_only_fields = ['created_at']

    def update(self, instance, validated_data):
        """
        Custom update method with intelligent note management.
        
        Handles updating application data along with its associated notes.
        Supports creating new notes, updating existing ones, and deleting
        notes that are no longer present in the request data.
        
        Args:
            instance (Application): The application instance to update
            validated_data (dict): The validated data from the request
            
        Returns:
            Application: The updated application instance
        """
        # Extract notes data for separate processing
        notes_data = validated_data.pop('notes', [])
        existing_notes = {note.id: note for note in instance.notes.all()}
        incoming_note_ids = set()

        # Process each note in the incoming data
        for note_data in notes_data:
            note_id = note_data.get('id', None)
            if note_id:
                # Track which notes are being updated
                incoming_note_ids.add(note_id)
                if note_id in existing_notes:
                    # Update existing note
                    note = existing_notes[note_id]
                    note.text = note_data.get('text', note.text)
                    note.save()
            else:
                # Create new note (no ID provided)
                Note.objects.create(application=instance, text=note_data.get('text', ''))

        # Delete notes that are no longer in the incoming data
        notes_to_delete_ids = set(existing_notes.keys()) - incoming_note_ids
        if notes_to_delete_ids:
            Note.objects.filter(application=instance, id__in=notes_to_delete_ids).delete()

        # Update the main application instance
        return super().update(instance, validated_data)
