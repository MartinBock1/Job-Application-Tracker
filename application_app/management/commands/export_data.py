import json
import os

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings

from ...models import Application, Company, Contact, Note


class Command(BaseCommand):
    """
    Django management command for exporting application data to JSON.
    
    This command exports all relevant data (Companies, Contacts, Applications, Notes)
    from the database into a single JSON file. The exported data can be used for
    backups, data migration, or analysis purposes.
    
    Usage:
        python manage.py export_data [--filename FILENAME]
    
    The command creates a JSON file in the project root directory containing
    all records from the specified models in a structured format.
    """
    help = 'Exports all relevant data (Companies, Contacts, Applications, Notes) into a single JSON file.'

    def add_arguments(self, parser):
        """
        Add command-line arguments for the export command.
        
        Args:
            parser: The argument parser instance to add arguments to
            
        Arguments:
            --filename: Optional filename for the output JSON file (default: 'full_export.json')
        """
        parser.add_argument(
            '--filename',
            type=str,
            default='full_export.json',
            help='The name of the JSON file to be created in the project root directory.'
        )

    def handle(self, *args, **options):
        """
        Execute the data export process.
        
        This method performs the complete export workflow:
        1. Retrieves all data from the database models
        2. Organizes data into a structured dictionary
        3. Serializes data to JSON format
        4. Writes the JSON data to a file
        
        Args:
            *args: Variable length argument list (not used)
            **options: Keyword arguments containing command options
            
        The method provides progress feedback and handles file I/O errors gracefully.
        """
        output_filename = options['filename']

        self.stdout.write("Starting export process...")

        # Create a dictionary containing all our data organized by model type
        data_to_export = {
            'companies': list(Company.objects.all().values()),
            'contacts': list(Contact.objects.all().values()),
            'applications': list(Application.objects.all().values()),
            'notes': list(Note.objects.all().values()),
        }

        # Display statistics about the data being exported
        self.stdout.write(f"- {len(data_to_export['companies'])} companies found.")
        self.stdout.write(f"- {len(data_to_export['contacts'])} contacts found.")
        self.stdout.write(f"- {len(data_to_export['applications'])} applications found.")
        self.stdout.write(f"- {len(data_to_export['notes'])} notes found.")

        # Serialize data to JSON with proper formatting and Django-compatible encoding
        json_output = json.dumps(data_to_export, cls=DjangoJSONEncoder, indent=4)
        output_path = os.path.join(settings.BASE_DIR, output_filename)

        try:
            # Write JSON data to file with UTF-8 encoding
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_output)
            self.stdout.write(self.style.SUCCESS(
                f'All data has been successfully exported to "{output_path}".'
            ))
        except IOError as e:
            # Handle file writing errors gracefully
            self.stderr.write(self.style.ERROR(f'Error writing file: {e}'))
