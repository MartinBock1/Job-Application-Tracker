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
            user=self.user,
            name="TechSolutions GmbH", 
            website="https://tech.sol"
        )
        self.company2 = Company.objects.create(
            user=self.user,
            name="Innovate AG", 
            website="https://innovate.ag"
        )

        self.contact1 = Contact.objects.create(
            user=self.user,
            company=self.company1,
            first_name="Erika",
            last_name="Musterfrau",
            email="e.musterfrau@tech.sol"
        )

        self.application1 = Application.objects.create(
            user=self.user,
            job_title="Senior Python Developer",
            company=self.company1,
            contact=self.contact1,
            status='APPLIED',
            applied_on='2023-10-26',
            salary_expectation=80000
        )

        # Note hat kein direktes user-Feld, ist aber über die Application verknüpft
        self.note1 = Note.objects.create(
            application=self.application1,
            text="Erstes Telefoninterview war sehr positiv."
        )

        self.application2 = Application.objects.create(
            user=self.user,
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

    # === PERMISSION Tests ===
    def test_user_cannot_access_other_users_applications(self):
        # Erstelle einen zweiten Benutzer und eine Bewerbung für diesen
        other_user = User.objects.create_user(username='otheruser', password='password123')
        other_company = Company.objects.create(user=other_user, name="Andere Firma")
        other_application = Application.objects.create(
            user=other_user,
            job_title="Job bei anderer Firma",
            company=other_company,
            status='APPLIED'
        )

        # Authentifiziere als der ursprüngliche Benutzer 'testuser'
        self.client.force_authenticate(user=self.user)

        # 1. Test der Listenansicht: Es dürfen nur die eigenen Bewerbungen erscheinen
        list_url = reverse('application-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Es sollten nur 2 Bewerbungen von 'testuser' sein, nicht 3
        self.assertEqual(len(response.data), 2) 
        application_ids = [app['id'] for app in response.data]
        self.assertNotIn(other_application.id, application_ids)

        # 2. Test der Detailansicht: Zugriff auf fremde Bewerbung muss fehlschlagen
        detail_url = reverse('application-detail', kwargs={'pk': other_application.pk})
        response = self.client.get(detail_url)
        # Erwartet wird 404, da die Query für den User kein Ergebnis liefert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
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

    # === NESTED RESOURCE Tests (Notes) ===
    def test_update_application_with_nested_notes(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})

        # Szenario: Eine Notiz ändern, eine neue hinzufügen, eine alte bleibt unberührt
        update_data = {
            "job_title": self.application1.job_title, # Pflichtfeld bei PUT
            "company_id": self.application1.company.id, # Pflichtfeld bei PUT
            "status": self.application1.status, # Pflichtfeld bei PUT
            "notes": [
                {
                    "id": self.note1.id,
                    "text": "Das erste Interview war doch nicht so positiv." # Text ändern
                },
                {
                    "text": "Neue Notiz: Rückmeldung für 28.11. versprochen." # Neue Notiz hinzufügen
                }
            ]
        }
        
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.application1.refresh_from_db()
        self.note1.refresh_from_db()

        self.assertEqual(self.application1.notes.count(), 2)
        self.assertEqual(self.note1.text, "Das erste Interview war doch nicht so positiv.")
        # Prüfen, ob die neue Notiz existiert
        self.assertTrue(self.application1.notes.filter(text__startswith="Neue Notiz").exists())

    def test_update_application_deletes_nested_note(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('application-detail', kwargs={'pk': self.application1.pk})
        
        # Erstelle eine zweite Notiz zum Löschen
        Note.objects.create(application=self.application1, text="Diese Notiz wird gelöscht.")
        self.assertEqual(self.application1.notes.count(), 2)

        update_data = {
            "job_title": self.application1.job_title,
            "company_id": self.application1.company.id,
            "status": self.application1.status,
            "notes": [
                {
                    "id": self.note1.id, # Nur die erste Notiz wird mitgesendet
                    "text": self.note1.text
                }
            ]
        }

        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.application1.refresh_from_db()
        self.assertEqual(self.application1.notes.count(), 1)
        self.assertEqual(self.application1.notes.first().id, self.note1.id)

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
        # Eine ID, die sicher nicht existiert
        non_existent_pk = Application.objects.latest('id').id + 100
        
        url = reverse('application-detail', kwargs={'pk': non_existent_pk})
        
        update_data = {
            "job_title": "Ghost Job",
            "company_id": self.company1.id,
            "status": "DRAFT"
        }
        
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)