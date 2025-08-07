from django.db import models
from django.contrib.auth.models import User


class Company(models.Model):
    """
    Model representing a company where users can apply for jobs.
    Each company belongs to a specific user and contains basic company information.
    """
    # User who owns this company record
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    # Company name
    name = models.CharField(
        max_length=200,
        verbose_name="Name des Unternehmens"
    )
    # Company website URL
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Webseite"
    )
    # Industry sector of the company
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
    """
    Model representing a contact person at a company.
    Used to store information about people who might be involved 
    in the application process.
    """
    # User who owns this contact record
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # Company this contact works for
    company = models.ForeignKey(
        Company,
        related_name='contacts',
        on_delete=models.CASCADE,
        verbose_name="Unternehmen"
    )
    
    # Contact's first name
    first_name = models.CharField(
        max_length=100,
        verbose_name="Vorname"
    )
    
    # Contact's last name
    last_name = models.CharField(
        max_length=100,
        verbose_name="Nachname"
    )
    
    # Contact's email address
    email = models.EmailField(
        blank=True
    )
    
    # Contact's phone number
    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Telefon"
    )
    
    # Contact's position/job title
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
    """
    Model representing a job application.
    Tracks the complete application process from draft to final outcome,
    including dates, status changes, and related information.
    """
    # User who created this application
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Benutzer",
    )

    # Available status choices for the application
    STATUS_CHOICES = [
        ('DRAFT', 'Entwurf'),           # Application is being prepared
        ('APPLIED', 'Beworben'),        # Application has been submitted
        ('INTERVIEW', 'Interview'),      # Interview scheduled/completed
        ('OFFER', 'Angebot erhalten'),  # Job offer received
        ('REJECTED', 'Abgelehnt'),      # Application was rejected
        ('WITHDRAWN', 'Zurückgezogen'), # Application was withdrawn
    ]

    # Title of the job position
    job_title = models.CharField(
        max_length=255,
        verbose_name="Jobtitel"
    )
    
    # Company where the application is submitted
    company = models.ForeignKey(
        Company,
        related_name='applications',
        on_delete=models.CASCADE,
        verbose_name="Unternehmen"
    )
    
    # Contact person for this application (optional)
    contact = models.ForeignKey(
        Contact,
        related_name='applications',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kontaktperson"
    )

    # Current status of the application
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name="Status"
    )

    # Date when the application was submitted
    applied_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Beworben am"
    )

    # Date of the interview
    interview_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Interview am"
    )

    # Date when job offer was received
    offer_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Angebot erhalten am"
    )

    # Date when rejection was received
    rejected_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Absage erhalten am"
    )

    # Date for follow-up or reminder
    follow_up_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Wiedervorlage am",
        help_text="Datum für die Wiedervorlage/Nachverfolgung"
    )

    # URL to the original job posting
    job_posting_link = models.URLField(
        blank=True,
        verbose_name="Link zur Ausschreibung"
    )

    # Expected salary for this position
    salary_expectation = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Gehaltsvorstellung",
        help_text="Jährliche Gehaltsvorstellung in EUR"
    )

    # Timestamp when the application record was created
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am"
    )

    # Timestamp when the application record was last updated
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
    """
    Model representing notes attached to job applications.
    Allows users to add timestamped notes for tracking thoughts,
    conversations, or important details about applications.
    """
    # Application this note belongs to
    application = models.ForeignKey(
        Application,
        related_name='notes',
        on_delete=models.CASCADE,
        verbose_name="Bewerbung"
    )
    
    # Content of the note
    text = models.TextField(verbose_name="Notiztext")
    
    # Timestamp when the note was created
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am"
    )

    class Meta:
        ordering = ['-created_at']  # Show newest notes first
        verbose_name = "Notiz"
        verbose_name_plural = "Notizen"

    def __str__(self):
        return f"Notiz für {self.application.job_title} vom {self.created_at.strftime('%d.%m.%Y')}"
