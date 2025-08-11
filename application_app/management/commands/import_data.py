import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model

from ...models import Application, Company, Contact, Note

class Command(BaseCommand):
    """
    Django management command for importing application data from JSON.
    
    This command imports data from a comprehensive JSON file into the database.
    It handles the complete restoration of Companies, Contacts, Applications, and Notes
    with proper relationship management and data integrity.
    
    Usage:
        python manage.py import_data [--filename FILENAME]
    
    The command expects a JSON file with the structure created by the export_data command.
    It performs imports in the correct order to maintain foreign key relationships.
    """
    help = 'Imports data from a comprehensive JSON file into the database.'

    def add_arguments(self, parser):
        """
        Add command-line arguments for the import command.
        
        Args:
            parser: The argument parser instance to add arguments to
            
        Arguments:
            --filename: Optional filename for the input JSON file (default: 'full_export.json')
        """
        parser.add_argument(
            '--filename',
            type=str,
            default='full_export.json',
            help='The name of the JSON file to be imported from the project root directory.'
        )

    def handle(self, *args, **options):
        """
        Execute the data import process.
        
        This method performs the complete import workflow:
        1. Validates that the input file exists
        2. Loads and parses the JSON data
        3. Imports data in the correct order to maintain relationships
        4. Handles foreign key relationships and data type conversions
        
        Args:
            *args: Variable length argument list (not used)
            **options: Keyword arguments containing command options
            
        The import order is critical:
        1. Companies (no dependencies)
        2. Contacts (depend on Companies)
        3. Applications (depend on Companies and Contacts)
        4. Notes (depend on Applications)
        """
        filename = options['filename']
        filepath = os.path.join(settings.BASE_DIR, filename)

        # Validate that the input file exists
        if not os.path.exists(filepath):
            self.stderr.write(self.style.ERROR(f'File not found: {filepath}'))
            return

        # Load and parse the JSON data
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        User = get_user_model()

        # --- IMPORT IN CORRECT ORDER TO MAINTAIN RELATIONSHIPS ---

        # 1. Companies (no foreign key dependencies)
        self.stdout.write("\nImporting companies...")
        for item in data.get('companies', []):
            # Handle user relationship: .values() returns user_id instead of user object
            user_id = item.pop('user_id', None)
            item['user'] = User.objects.get(pk=user_id) if user_id else None
            Company.objects.update_or_create(id=item['id'], defaults=item)
        self.stdout.write(self.style.SUCCESS('Companies imported.'))

        # 2. Contacts (depend on Companies)
        self.stdout.write("\nImporting contacts...")
        for item in data.get('contacts', []):
            # Handle foreign key relationships
            user_id = item.pop('user_id', None)
            company_id = item.pop('company_id', None)
            item['user'] = User.objects.get(pk=user_id) if user_id else None
            item['company'] = Company.objects.get(pk=company_id) if company_id else None
            Contact.objects.update_or_create(id=item['id'], defaults=item)
        self.stdout.write(self.style.SUCCESS('Contacts imported.'))

        # 3. Applications (depend on Companies and Contacts)
        self.stdout.write("\nImporting applications...")
        for item in data.get('applications', []):
            # Handle foreign key relationships
            user_id = item.pop('user_id', None)
            company_id = item.pop('company_id', None)
            contact_id = item.pop('contact_id', None)

            item['user'] = User.objects.get(pk=user_id) if user_id else None
            item['company'] = Company.objects.get(pk=company_id) if company_id else None
            item['contact'] = Contact.objects.get(pk=contact_id) if contact_id else None

            # Convert empty date strings to None for proper database storage
            for field in ['applied_on', 'interview_on', 'offer_on', 'rejected_on', 'follow_up_on']:
                if item.get(field) == '':
                    item[field] = None

            Application.objects.update_or_create(id=item['id'], defaults=item)
        self.stdout.write(self.style.SUCCESS('Applications imported.'))

        # 4. Notes (depend on Applications)
        self.stdout.write("\nImporting notes...")
        for item in data.get('notes', []):
            # Handle application relationship
            application_id = item.pop('application_id', None)
            item['application'] = Application.objects.get(
                pk=application_id) if application_id else None
            Note.objects.update_or_create(id=item['id'], defaults=item)
        self.stdout.write(self.style.SUCCESS('Notes imported.'))

        self.stdout.write(self.style.SUCCESS('\n--- Import process completed successfully! ---'))
