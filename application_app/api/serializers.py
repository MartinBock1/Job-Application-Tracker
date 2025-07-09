from rest_framework import serializers
from ..models import Company, Contact, Application, Note


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'website',
            'industry'
        ]


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'position',
            'company'
        ]


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'text', 'created_at']
        read_only_fields = ['application']


class ApplicationSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True
    )

    contact = ContactSerializer(read_only=True, required=False)
    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        source='contact',
        write_only=True,
        required=False,
        allow_null=True
    )

    notes = NoteSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

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
            'follow_up_on',
            'job_posting_link',
            'salary_expectation',
            'created_at',
            'notes'
        ]
