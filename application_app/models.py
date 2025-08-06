from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.


class Company(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Name des Unternehmens"
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Webseite"
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Branche"
    )

    class Meta:
        verbose_name = "Unternehmen"
        verbose_name_plural = "Unternehmen"
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name


class Contact(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    company = models.ForeignKey(
        Company,
        related_name='contacts',
        on_delete=models.CASCADE,
        verbose_name="Unternehmen"
    )
    
    first_name = models.CharField(
        max_length=100,
        verbose_name="Vorname"
    )
    
    last_name = models.CharField(
        max_length=100,
        verbose_name="Nachname"
    )
    
    email = models.EmailField(
        blank=True
    )
    
    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Telefon"
    )
    
    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Position"
    )

    class Meta:
        verbose_name = "Kontaktperson"
        verbose_name_plural = "Kontaktpersonen"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.company.name})"


class Application(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Benutzer",
    )

    STATUS_CHOICES = [
        ('DRAFT', 'Entwurf'),
        ('APPLIED', 'Beworben'),
        ('INTERVIEW', 'Interview'),
        ('OFFER', 'Angebot erhalten'),
        ('REJECTED', 'Abgelehnt'),
        ('WITHDRAWN', 'Zurückgezogen'),
    ]

    job_title = models.CharField(
        max_length=255,
        verbose_name="Jobtitel"
    )
    
    company = models.ForeignKey(
        Company,
        related_name='applications',
        on_delete=models.CASCADE,
        verbose_name="Unternehmen"
    )
    
    contact = models.ForeignKey(
        Contact,
        related_name='applications',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kontaktperson"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name="Status"
    )

    applied_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Beworben am"
    )

    interview_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Interview am"
    )

    offer_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Angebot erhalten am"
    )

    rejected_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Absage erhalten am"
    )

    follow_up_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Wiedervorlage am",
        help_text="Datum für die Wiedervorlage/Nachverfolgung"
    )

    job_posting_link = models.URLField(
        blank=True,
        verbose_name="Link zur Ausschreibung"
    )

    salary_expectation = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Gehaltsvorstellung",
        help_text="Jährliche Gehaltsvorstellung in EUR"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Aktualisiert am"
    )

    class Meta:
        verbose_name = "Bewerbung"
        verbose_name_plural = "Bewerbungen"

    def __str__(self):
        return f"{self.job_title} bei {self.company.name}"


class Note(models.Model):
    application = models.ForeignKey(
        Application,
        related_name='notes',
        on_delete=models.CASCADE,
        verbose_name="Bewerbung"
    )
    
    text = models.TextField(verbose_name="Notiztext")
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am"
    )

    class Meta:
        ordering = ['-created_at']  # Neueste Notizen zuerst
        verbose_name = "Notiz"
        verbose_name_plural = "Notizen"

    def __str__(self):
        return f"Notiz für {self.application.job_title} vom {self.created_at.strftime('%d.%m.%Y')}"
