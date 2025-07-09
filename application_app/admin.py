from django.contrib import admin
from .models import Company, Contact, Application, Note

# Register your models here.
class NoteInline(admin.TabularInline):
    model = Note
    extra = 1
    readonly_fields = ('created_at',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'website')
    search_fields = ('name', 'industry')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'company', 'position', 'email')
    list_filter = ('company',)
    search_fields = ('first_name', 'last_name', 'email', 'company__name')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company', 'status', 'applied_on', 'follow_up_on', 'created_at')
    list_filter = ('status', 'company', 'follow_up_on')
    search_fields = ('job_title', 'company__name', 'contact__first_name', 'contact__last_name')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Job Details', {
            'fields': ('job_title', 'company', 'contact', 'job_posting_link')
        }),
        ('Status & Dates', {
            'fields': ('status', 'applied_on', 'follow_up_on', 'salary_expectation')
        }),
    )
    
    inlines = [NoteInline]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'application', 'created_at')
    search_fields = ('text', 'application__job_title')