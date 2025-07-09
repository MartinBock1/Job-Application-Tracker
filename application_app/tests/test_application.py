from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Company, Contact, Application, Note

# Deutsche Kommentare, um den Kontext der Originaldateien beizubehalten.


class ApplicationAPITests(APITestCase):
    """
    Test-Suite für den Application-Endpunkt.
    Folgt dem TDD-Ansatz:
    1. Test für die Listenansicht (GET)
    2. Test für die Detailansicht (GET)
    3. Test für die Erstellung (POST) - inkl. Validierungsfehler
    4. Test für die vollständige Aktualisierung (PUT)
    5. Test für die teilweise Aktualisierung (PATCH)
    6. Test für das Löschen (DELETE)
    7. Tests für spezielle Beziehungen (nested notes, contact handling, etc.)
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        
        self.company1 = Company.objects.create(
            name="TechSolutions GmbH", website="https://tech.sol")
        self.company2 = Company.objects.create(name="Innovate AG", website="https://innovate.ag")

        self.contact1 = Contact.objects.create(
            company=self.company1,
            first_name="Erika",
            last_name="Musterfrau",
            email="e.musterfrau@tech.sol"
        )

        self.application1 = Application.objects.create(
            job_title="Senior Python Developer",
            company=self.company1,
            contact=self.contact1,
            status='APPLIED',
            applied_on='2023-10-26',
            salary_expectation=80000
        )

        self.note1 = Note.objects.create(
            application=self.application1,
            text="Erstes Telefoninterview war sehr positiv."
        )

        self.application2 = Application.objects.create(
            job_title="Frontend Entwickler",
            company=self.company2,
            status='DRAFT'
        )

    # === READ Tests (GET) ===
    def test_list_applications(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('application-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        first_app_data = response.data[0] if response.data[0]['id'] == self.application1.id else response.data[1]
        self.assertEqual(first_app_data['job_title'], self.application1.job_title)
        self.assertEqual(first_app_data['company']['name'], self.company1.name)
        self.assertEqual(first_app_data['status'], 'APPLIED')
        self.assertEqual(first_app_data['status_display'], 'Beworben')

    def test_retrieve_application_detail(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['job_title'], self.application1.job_title)
        self.assertEqual(response.data['salary_expectation'], self.application1.salary_expectation)

        self.assertEqual(response.data['company']['name'], self.company1.name)
        self.assertEqual(response.data['contact']['email'], self.contact1.email)
        self.assertIn('notes', response.data)
        self.assertEqual(len(response.data['notes']), 1)
        self.assertEqual(response.data['notes'][0]['text'], self.note1.text)

    def test_retrieve_non_existent_application_returns_404(self):
        self.client.force_authenticate(user=self.user)
        non_existent_pk = Application.objects.latest('id').id + 100
        url = reverse('application-detail', kwargs={'pk': non_existent_pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_applications_fails_for_unauthenticated_user(self):
        self.client.force_authenticate(user=None)

        url = reverse('application-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # === CREATE Tests (POST) ===
    def test_create_application(self):
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

        self.assertEqual(response.data['job_title'], "Data Scientist")
        self.assertEqual(response.data['company']['name'], self.company1.name)
        self.assertEqual(response.data['contact']['first_name'], self.contact1.first_name)

    def test_create_application_without_contact(self):
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
        self.client.force_authenticate(user=self.user)
        url = reverse('application-list')
        data = {"job_title": "Invalid Application"}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_id', response.data)

    def test_create_application_fails_with_invalid_status(self):
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
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        update_data = {
            "job_title": "Senior DevOps Engineer",
            "company_id": self.company2.id,  # Unternehmen ändern
            "contact_id": None,  # Kontakt entfernen
            "status": "INTERVIEW",
            "applied_on": self.application1.applied_on,
            "salary_expectation": 90000
        }

        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.application1.refresh_from_db()
        self.assertEqual(self.application1.job_title, "Senior DevOps Engineer")
        self.assertEqual(self.application1.status, "INTERVIEW")
        self.assertEqual(self.application1.company, self.company2)
        self.assertIsNone(self.application1.contact)
        self.assertEqual(self.application1.salary_expectation, 90000)

    def test_partial_update_application(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        patch_data = {"status": "OFFER", "follow_up_on": "2023-12-24"}

        response = self.client.patch(url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.application1.refresh_from_db()
        self.assertEqual(self.application1.status, "OFFER")
        self.assertEqual(str(self.application1.follow_up_on), "2023-12-24")
        self.assertEqual(self.application1.job_title, "Senior Python Developer")

     # === DELETE Tests (DELETE) ===

    def test_delete_application(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        initial_count = Application.objects.count()

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Application.objects.count(), initial_count - 1)

        with self.assertRaises(Application.DoesNotExist):
            Application.objects.get(pk=self.application1.pk)

    def test_update_non_existent_application_returns_404(self):
        self.client.force_authenticate(user=self.user)
        last_app_id = Application.objects.last().id if Application.objects.exists() else 0
        non_existent_pk = last_app_id + 100
        
        url = reverse('application-detail', kwargs={'pk': non_existent_pk})
        
        update_data = {
            "job_title": "Ghost Job",
            "company_id": self.company1.id,
            "status": "DRAFT"
        }
        
        response = self.client.put(url, update_data, format='json')
