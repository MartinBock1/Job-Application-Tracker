from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Company, Contact, Application, Note


class ApplicationAPITests(APITestCase):
    """
    Comprehensive test suite for the Application API endpoint.
    
    Follows the TDD approach with tests covering:
    1. List view tests (GET)
    2. Detail view tests (GET) 
    3. Creation tests (POST) - including validation errors
    4. Full update tests (PUT)
    5. Partial update tests (PATCH)
    6. Deletion tests (DELETE)
    7. Special relationship tests (nested notes, contact handling, etc.)
    8. Permission and security tests
    
    Tests ensure proper CRUD operations, data validation, user isolation,
    and complex nested resource management.
    """

    def setUp(self):
        """
        Set up test data for all test methods.
        
        Creates a test user, companies, contacts, applications, and notes
        to provide a consistent testing environment. This method runs
        before each individual test method.
        """
        # Create test user for authentication
        self.user = User.objects.create_user(username='testuser', password='password123')
        
        # Create test companies
        self.company1 = Company.objects.create(
            user=self.user,
            name="TechSolutions GmbH", 
            website="https://tech.sol"
        )
        self.company2 = Company.objects.create(
            user=self.user,
            name="Innovate AG", 
            website="https://innovate.ag"
        )

        # Create test contact associated with company1
        self.contact1 = Contact.objects.create(
            user=self.user,
            company=self.company1,
            first_name="Erika",
            last_name="Musterfrau",
            email="e.musterfrau@tech.sol"
        )

        # Create test applications with different statuses
        self.application1 = Application.objects.create(
            user=self.user,
            job_title="Senior Python Developer",
            company=self.company1,
            contact=self.contact1,
            status='APPLIED',
            applied_on='2023-10-26',
            salary_expectation=80000
        )

        # Create test note (linked to application, no direct user field)
        self.note1 = Note.objects.create(
            application=self.application1,
            text="Erstes Telefoninterview war sehr positiv."
        )

        # Create second test application without contact
        self.application2 = Application.objects.create(
            user=self.user,
            job_title="Frontend Entwickler",
            company=self.company2,
            status='DRAFT'
        )

    # === READ Tests (GET) ===
    def test_list_applications(self):
        """
        Test retrieving a list of applications for authenticated user.
        
        Verifies that the API returns all applications belonging to the user,
        includes nested company data, and properly displays status information.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Find the first application in response data
        first_app_data = response.data[0] if response.data[0]['id'] == self.application1.id else response.data[1]
        self.assertEqual(first_app_data['job_title'], self.application1.job_title)
        self.assertEqual(first_app_data['company']['name'], self.company1.name)
        self.assertEqual(first_app_data['status'], 'APPLIED')
        self.assertEqual(first_app_data['status_display'], 'Beworben')

    def test_retrieve_application_detail(self):
        """
        Test retrieving detailed information for a specific application.
        
        Verifies that the API returns complete application data including
        nested company, contact, and notes information.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['job_title'], self.application1.job_title)
        self.assertEqual(response.data['salary_expectation'], self.application1.salary_expectation)

        # Verify nested data is included
        self.assertEqual(response.data['company']['name'], self.company1.name)
        self.assertEqual(response.data['contact']['email'], self.contact1.email)
        self.assertIn('notes', response.data)
        self.assertEqual(len(response.data['notes']), 1)
        self.assertEqual(response.data['notes'][0]['text'], self.note1.text)

    def test_retrieve_non_existent_application_returns_404(self):
        """
        Test that requesting a non-existent application returns 404.
        
        Verifies proper error handling for invalid application IDs.
        """
        self.client.force_authenticate(user=self.user)
        non_existent_pk = Application.objects.latest('id').id + 100
        url = reverse('application-detail', kwargs={'pk': non_existent_pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_applications_fails_for_unauthenticated_user(self):
        """
        Test that unauthenticated users cannot access application data.
        
        Verifies that proper authentication is required for API access.
        """
        self.client.force_authenticate(user=None)

        url = reverse('application-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # === PERMISSION Tests ===
    def test_user_cannot_access_other_users_applications(self):
        """
        Test that users can only access their own applications.
        
        Verifies data isolation by ensuring users cannot see or access
        applications belonging to other users through both list and detail views.
        """
        # Create a second user and application for that user
        other_user = User.objects.create_user(username='otheruser', password='password123')
        other_company = Company.objects.create(user=other_user, name="Andere Firma")
        other_application = Application.objects.create(
            user=other_user,
            job_title="Job bei anderer Firma",
            company=other_company,
            status='APPLIED'
        )

        # Authenticate as the original user 'testuser'
        self.client.force_authenticate(user=self.user)

        # 1. Test list view: should only show own applications
        list_url = reverse('application-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return 2 applications from 'testuser', not 3
        self.assertEqual(len(response.data), 2) 
        application_ids = [app['id'] for app in response.data]
        self.assertNotIn(other_application.id, application_ids)

        # 2. Test detail view: access to other user's application must fail
        detail_url = reverse('application-detail', kwargs={'pk': other_application.pk})
        response = self.client.get(detail_url)
        # Expected 404 since the query for this user returns no results
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    # === CREATE Tests (POST) ===
    def test_create_application(self):
        """
        Test creating a new application with complete data.
        
        Verifies that applications can be created successfully with all
        required and optional fields, and that nested relationships work correctly.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-list')
        data = {
            "job_title": "Data Scientist",
            "company_id": self.company1.id,
            "contact_id": self.contact1.id,
            "status": "DRAFT",
            "applied_on": "2023-11-01",
            "job_posting_link": "https://jobs.tech.sol/data-scientist",
            "salary_expectation": 75000
        }

        initial_count = Application.objects.count()
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), initial_count + 1)

        # Verify response contains correct data with nested relationships
        self.assertEqual(response.data['job_title'], "Data Scientist")
        self.assertEqual(response.data['company']['name'], self.company1.name)
        self.assertEqual(response.data['contact']['first_name'], self.contact1.first_name)

    def test_create_application_without_contact(self):
        """
        Test creating an application without specifying a contact.
        
        Verifies that the contact field is truly optional and applications
        can be created without contact information.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-list')
        data = {
            "job_title": "Junior Backend Dev",
            "company_id": self.company2.id,
            "status": "DRAFT",
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['job_title'], "Junior Backend Dev")
        self.assertIsNone(response.data['contact'])

    def test_create_application_fails_without_company(self):
        """
        Test that application creation fails without required company field.
        
        Verifies proper validation for required fields and appropriate error responses.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-list')
        data = {"job_title": "Invalid Application"}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_id', response.data)

    def test_create_application_fails_with_invalid_status(self):
        """
        Test that application creation fails with invalid status values.
        
        Verifies that only predefined status choices are accepted and proper
        validation errors are returned for invalid values.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-list')
        data = {
            "job_title": "Manager",
            "company_id": self.company1.id,
            "status": "INVALID_STATUS_VALUE"
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)

    # === UPDATE Tests (PUT / PATCH) ===
    def test_full_update_application(self):
        """
        Test complete application update using PUT method.
        
        Verifies that all application fields can be updated simultaneously,
        including changing company relationships and removing optional contacts.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        update_data = {
            "job_title": "Senior DevOps Engineer",
            "company_id": self.company2.id,  # Change company
            "contact_id": None,  # Remove contact
            "status": "INTERVIEW",
            "applied_on": self.application1.applied_on,
            "salary_expectation": 90000
        }

        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify all changes were applied correctly
        self.application1.refresh_from_db()
        self.assertEqual(self.application1.job_title, "Senior DevOps Engineer")
        self.assertEqual(self.application1.status, "INTERVIEW")
        self.assertEqual(self.application1.company, self.company2)
        self.assertIsNone(self.application1.contact)
        self.assertEqual(self.application1.salary_expectation, 90000)

    def test_partial_update_application(self):
        """
        Test partial application update using PATCH method.
        
        Verifies that only specified fields are updated while leaving
        other fields unchanged. Tests the flexibility of partial updates.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        patch_data = {"status": "OFFER", "follow_up_on": "2023-12-24"}

        response = self.client.patch(url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify only specified fields changed, others remained the same
        self.application1.refresh_from_db()
        self.assertEqual(self.application1.status, "OFFER")
        self.assertEqual(str(self.application1.follow_up_on), "2023-12-24")
        self.assertEqual(self.application1.job_title, "Senior Python Developer")  # Unchanged

     # === DELETE Tests (DELETE) ===

    # === NESTED RESOURCE Tests (Notes) ===
    def test_update_application_with_nested_notes(self):
        """
        Test updating application with nested note management.
        
        Verifies the intelligent note handling during application updates:
        - Modifying existing notes by ID
        - Adding new notes without ID
        - Proper relationship management
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})

        # Scenario: Modify one note, add a new one
        update_data = {
            "job_title": self.application1.job_title, # Required field for PUT
            "company_id": self.application1.company.id, # Required field for PUT
            "status": self.application1.status, # Required field for PUT
            "notes": [
                {
                    "id": self.note1.id,
                    "text": "Das erste Interview war doch nicht so positiv." # Modify existing note
                },
                {
                    "text": "Neue Notiz: Rückmeldung für 28.11. versprochen." # Add new note
                }
            ]
        }
        
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify note changes were applied correctly
        self.application1.refresh_from_db()
        self.note1.refresh_from_db()

        self.assertEqual(self.application1.notes.count(), 2)
        self.assertEqual(self.note1.text, "Das erste Interview war doch nicht so positiv.")
        # Verify the new note exists
        self.assertTrue(self.application1.notes.filter(text__startswith="Neue Notiz").exists())

    def test_update_application_deletes_nested_note(self):
        """
        Test that notes not included in update request are deleted.
        
        Verifies the intelligent note deletion behavior where notes
        not present in the update data are automatically removed.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        
        # Create a second note that will be deleted
        Note.objects.create(application=self.application1, text="Diese Notiz wird gelöscht.")
        self.assertEqual(self.application1.notes.count(), 2)

        update_data = {
            "job_title": self.application1.job_title,
            "company_id": self.application1.company.id,
            "status": self.application1.status,
            "notes": [
                {
                    "id": self.note1.id, # Only include the first note
                    "text": self.note1.text
                }
            ]
        }

        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify second note was deleted
        self.application1.refresh_from_db()
        self.assertEqual(self.application1.notes.count(), 1)
        self.assertEqual(self.application1.notes.first().id, self.note1.id)

    def test_delete_application(self):
        """
        Test deleting an application.
        
        Verifies that applications can be successfully deleted and
        proper HTTP status codes are returned.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        initial_count = Application.objects.count()

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Application.objects.count(), initial_count - 1)

        # Verify application was actually deleted
        with self.assertRaises(Application.DoesNotExist):
            Application.objects.get(pk=self.application1.pk)

    def test_update_non_existent_application_returns_404(self):
        """
        Test that updating a non-existent application returns 404.
        
        Verifies proper error handling for invalid application IDs
        during update operations.
        """
        self.client.force_authenticate(user=self.user)
        # Use an ID that definitely doesn't exist
        non_existent_pk = Application.objects.latest('id').id + 100
        
        url = reverse('application-detail', kwargs={'pk': non_existent_pk})
        
        update_data = {
            "job_title": "Ghost Job",
            "company_id": self.company1.id,
            "status": "DRAFT"
        }
        
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)