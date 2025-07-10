from django.contrib import admin
from .models import Company, Contact, Application, Note

# Register your models here.


class NoteInline(admin.TabularInline):
    model = Note
    extra = 1
    readonly_fields = ('created_at',)


class UserFilter(admin.SimpleListFilter):
    title = 'User Assignment'
    parameter_name = 'user_assigned'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Assigned'),
            ('no', 'Not Assigned (NULL)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(user__isnull=True)
        if self.value() == 'yes':
            return queryset.filter(user__isnull=False)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'website')
    search_fields = ('name', 'industry')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'company', 'position', 'email')
    list_filter = ('company',)
    search_fields = ('first_name', 'last_name', 'email', 'company__name')

# @admin.register(Application)
# class ApplicationAdmin(admin.ModelAdmin):
#     # Wir definieren nur die Felder, die wir sehen wollen.
#     # Wichtig: 'readonly_fields' werden hier NICHT aufgeführt.
#     fields = (
#         'user',
#         'job_title',
#         'company',
#         'contact',
#         'status',
#         'applied_on',
#         'follow_up_on',
#         'job_posting_link',
#         'salary_expectation'
#     )

#     # readonly_fields werden separat definiert.
#     readonly_fields = ('created_at', 'updated_at')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    # Diese Definitionen sind alle in Ordnung
    list_display = ('job_title', 'company', 'status', 'applied_on', 'created_at', 'user')
    list_filter = ('status', 'company', 'user', UserFilter)
    search_fields = ('job_title', 'company__name')
    date_hierarchy = 'created_at'

    # Die 'readonly_fields' müssen alle Felder enthalten, die nicht editierbar sein sollen.
    # Das ist korrekt so.
    readonly_fields = ('created_at', 'updated_at')

    # Die 'fieldsets' definieren das Layout. Wir stellen sicher, dass die readonly-Felder
    # hier aufgeführt sind. Django wird sie dann korrekt als reinen Text anzeigen.
    fieldsets = (
        (None, {
            'fields': ('user', 'job_title', 'company', 'contact')
        }),
        ('Status & Daten', {
            'fields': ('status', 'applied_on', 'follow_up_on')
        }),
        ('Weitere Informationen', {
            'fields': ('job_posting_link', 'salary_expectation')
        }),
        # Diese Sektion ist korrekt. Sie zeigt die als 'readonly' markierten Felder an.
        ('Zeitstempel', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [NoteInline]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'application', 'created_at')
    search_fields = ('text', 'application__job_title')
