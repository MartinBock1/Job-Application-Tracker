from rest_framework import serializers
from ..models import Company, Contact, Application, Note


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'website', 'industry']


class ContactSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
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
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Note
        fields = ['id', 'text', 'created_at']


class ApplicationSerializer(serializers.ModelSerializer):
    # Lese-Felder (für die Anzeige)
    company = CompanySerializer(read_only=True)
    contact = ContactSerializer(read_only=True, required=False, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    notes = NoteSerializer(many=True, required=False)  # 'read_only=True' ist hier nicht mehr nötig

    # Schreib-Felder (für create/update)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True
    )

    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(), source='contact',
        write_only=True,
        required=False,
        allow_null=True
    )

    # Optionales Feld für das Datum
    applied_on = serializers.DateField(required=False, allow_null=True)

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

    # Die intelligente UPDATE-Logik für Notizen bleibt erhalten, da sie funktioniert.
    def update(self, instance, validated_data):
        notes_data = validated_data.pop('notes', [])
        existing_notes = {note.id: note for note in instance.notes.all()}
        incoming_note_ids = set()

        for note_data in notes_data:
            note_id = note_data.get('id', None)
            if note_id:
                incoming_note_ids.add(note_id)
                if note_id in existing_notes:
                    note = existing_notes[note_id]
                    note.text = note_data.get('text', note.text)
                    note.save()
            else:
                Note.objects.create(application=instance, text=note_data.get('text', ''))

        notes_to_delete_ids = set(existing_notes.keys()) - incoming_note_ids
        if notes_to_delete_ids:
            Note.objects.filter(application=instance, id__in=notes_to_delete_ids).delete()

        return super().update(instance, validated_data)
