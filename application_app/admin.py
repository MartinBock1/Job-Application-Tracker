from django.contrib import admin
from .models import Company, Contact, Application, Note


class NoteInline(admin.TabularInline):
    """
    Inline admin interface for Notes.
    
    Allows editing notes directly within the Application admin page.
    Provides one extra empty form for quick note addition and makes
    the creation timestamp read-only for data integrity.
    """
    model = Note
    extra = 1  # Show one extra empty form for new notes
    readonly_fields = ('created_at',)  # Prevent modification of creation timestamp


class UserFilter(admin.SimpleListFilter):
    """
    Custom admin filter for user assignment status.
    
    Provides filtering options to show records that are either assigned
    to a user or have null user values. Useful for identifying orphaned
    records or checking data integrity.
    """
    title = 'User Assignment'
    parameter_name = 'user_assigned'

    def lookups(self, request, model_admin):
        """
        Define the filter options available in the admin interface.
        
        Returns:
            tuple: Filter choices for assigned/unassigned users
        """
        return (
            ('yes', 'Assigned'),
            ('no', 'Not Assigned (NULL)'),
        )

    def queryset(self, request, queryset):
        """
        Filter the queryset based on user assignment status.
        
        Args:
            request: The HTTP request object
            queryset: The original queryset to filter
            
        Returns:
            QuerySet: Filtered queryset based on user assignment
        """
        if self.value() == 'no':
            return queryset.filter(user__isnull=True)
        if self.value() == 'yes':
            return queryset.filter(user__isnull=False)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Company model.
    
    Provides a clean interface for managing companies with search
    functionality by name and industry. Displays key company information
    in the list view for quick overview.
    """
    # Display these fields in the company list view
    list_display = ('name', 'industry', 'website')
    # Enable search functionality for these fields
    search_fields = ('name', 'industry')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Contact model.
    
    Enables comprehensive contact management with filtering by company
    and search across contact details. Displays essential contact
    information for efficient contact management.
    """
    # Display these fields in the contact list view
    list_display = ('first_name', 'last_name', 'company', 'position', 'email')
    # Add filter sidebar for company selection
    list_filter = ('company',)
    # Enable search across contact and related company fields
    search_fields = ('first_name', 'last_name', 'email', 'company__name')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Application model.
    
    Provides comprehensive application management with advanced filtering,
    searching, and organized field layout. Includes inline note editing
    and hierarchical date navigation for efficient application tracking.
    """
    
    # Display these fields in the application list view
    list_display = ('job_title', 'company', 'status', 'applied_on', 'created_at', 'user')
    
    # Add filter sidebar with multiple filtering options
    list_filter = ('status', 'company', 'user', UserFilter)
    
    # Enable search functionality across job and company fields
    search_fields = ('job_title', 'company__name')
    
    # Add date-based navigation hierarchy
    date_hierarchy = 'created_at'

    # Fields that should be read-only (not editable)
    readonly_fields = ('created_at', 'updated_at')

    # Organize fields into logical sections with collapsible layout
    fieldsets = (
        (None, {
            'fields': ('user', 'job_title', 'company', 'contact')
        }),
        ('Status & Dates', {
            'fields': ('status', 'applied_on', 'follow_up_on')
        }),
        ('Additional Information', {
            'fields': ('job_posting_link', 'salary_expectation')
        }),
        # Collapsible section for timestamp information
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Make this section collapsible
        }),
    )

    # Include inline note editing within the application form
    inlines = [NoteInline]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Note model.
    
    Provides note management with clear display of note content,
    associated application, and creation timestamp. Enables searching
    through note content and related application details.
    """
    # Display note summary, related application, and creation time
    list_display = ('__str__', 'application', 'created_at')
    
    # Enable search through note text and related application job titles
    search_fields = ('text', 'application__job_title')
