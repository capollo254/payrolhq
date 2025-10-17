"""
Organization Models for PayrollHQ

This module handles the multi-tenant organization structure and user management.
Each organization represents a separate tenant with isolated data.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class Organization(models.Model):
    """
    Multi-tenant organization model.
    
    Each organization represents a separate company/tenant with completely
    isolated payroll data. This is the core of the multi-tenancy architecture.
    """
    
    ORGANIZATION_TYPES = [
        ('PRIVATE_LIMITED', 'Private Limited Company'),
        ('PUBLIC_LIMITED', 'Public Limited Company'),
        ('PARTNERSHIP', 'Partnership'),
        ('SOLE_PROPRIETOR', 'Sole Proprietorship'),
        ('NGO', 'Non-Governmental Organization'),
        ('GOVERNMENT', 'Government Entity'),
        ('OTHER', 'Other'),
    ]
    
    # Unique identifier for the organization
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic organization information
    name = models.CharField(
        max_length=200,
        help_text="Official registered name of the organization"
    )
    
    trading_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Trading or business name (if different from registered name)"
    )
    
    organization_type = models.CharField(
        max_length=20,
        choices=ORGANIZATION_TYPES,
        default='PRIVATE_LIMITED'
    )
    
    # Kenyan business registration details
    registration_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Company registration number from Registrar of Companies"
    )
    
    kra_pin = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^P\d{9}[A-Z]$',
                message='KRA PIN must be in format P000000000A'
            )
        ],
        unique=True,
        help_text="KRA PIN number for the organization"
    )
    
    nssf_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="NSSF employer registration number"
    )
    
    nhif_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="NHIF employer registration number"
    )
    
    # Contact information
    email = models.EmailField(help_text="Primary contact email")
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Address information
    physical_address = models.TextField(help_text="Physical business address")
    postal_address = models.TextField(blank=True, help_text="Postal address")
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Subscription and status
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(
        max_length=50,
        choices=[
            ('TRIAL', 'Trial'),
            ('BASIC', 'Basic'),
            ('STANDARD', 'Standard'),
            ('PREMIUM', 'Premium'),
        ],
        default='TRIAL'
    )
    
    subscription_expires = models.DateField(
        null=True,
        blank=True,
        help_text="Subscription expiry date"
    )
    
    max_employees = models.PositiveIntegerField(
        default=10,
        help_text="Maximum number of employees allowed"
    )
    
    # Payroll configuration
    default_pay_period = models.CharField(
        max_length=20,
        choices=[
            ('MONTHLY', 'Monthly'),
            ('WEEKLY', 'Weekly'),
            ('BIWEEKLY', 'Bi-weekly'),
        ],
        default='MONTHLY'
    )
    
    pay_day = models.PositiveIntegerField(
        default=25,
        help_text="Default pay day of the month (1-31)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['subscription_plan', 'subscription_expires']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_subscription_active(self):
        """Check if the organization's subscription is active."""
        if not self.subscription_expires:
            return True
        return self.subscription_expires >= timezone.now().date()
    
    @property
    def employee_count(self):
        """Get current active employee count."""
        return self.employees.filter(is_active=True).count()
    
    @property
    def can_add_employees(self):
        """Check if organization can add more employees."""
        return self.employee_count < self.max_employees
    
    def get_display_name(self):
        """Get the display name (trading name or registered name)."""
        return self.trading_name or self.name


class User(AbstractUser):
    """
    Extended user model with organization relationship for multi-tenancy.
    
    Each user belongs to one organization, ensuring data segregation.
    """
    
    USER_ROLES = [
        ('OWNER', 'Organization Owner'),
        ('ADMIN', 'Administrator'),
        ('HR_MANAGER', 'HR Manager'),
        ('PAYROLL_CLERK', 'Payroll Clerk'),
        ('VIEWER', 'View Only'),
    ]
    
    # Organization relationship for multi-tenancy
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='users',
        help_text="Organization this user belongs to"
    )
    
    # User role and permissions
    role = models.CharField(
        max_length=20,
        choices=USER_ROLES,
        default='VIEWER'
    )
    
    # Additional user information
    phone = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Employee ID if this user is also an employee"
    )
    
    # Account status
    is_organization_admin = models.BooleanField(
        default=False,
        help_text="Whether this user has admin rights for their organization"
    )
    
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Fix related_name conflicts with default Django User model
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='org_users',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='org_users',
        help_text='Specific permissions for this user.'
    )
    
    class Meta:
        ordering = ['organization', 'username']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'username'],
                name='unique_username_per_organization'
            ),
            models.UniqueConstraint(
                fields=['organization', 'email'],
                name='unique_email_per_organization'
            ),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.organization.name})"
    
    @property
    def can_manage_employees(self):
        """Check if user can manage employees."""
        return self.role in ['OWNER', 'ADMIN', 'HR_MANAGER']
    
    @property
    def can_run_payroll(self):
        """Check if user can run payroll."""
        return self.role in ['OWNER', 'ADMIN', 'HR_MANAGER', 'PAYROLL_CLERK']
    
    @property
    def can_view_reports(self):
        """Check if user can view reports."""
        return self.role in ['OWNER', 'ADMIN', 'HR_MANAGER', 'PAYROLL_CLERK', 'VIEWER']
    
    def get_permissions(self):
        """Get list of permissions for this user role."""
        permission_map = {
            'OWNER': [
                'manage_organization', 'manage_users', 'manage_employees',
                'run_payroll', 'view_reports', 'manage_compliance'
            ],
            'ADMIN': [
                'manage_users', 'manage_employees', 'run_payroll',
                'view_reports', 'manage_compliance'
            ],
            'HR_MANAGER': [
                'manage_employees', 'run_payroll', 'view_reports'
            ],
            'PAYROLL_CLERK': [
                'run_payroll', 'view_reports'
            ],
            'VIEWER': [
                'view_reports'
            ],
        }
        
        return permission_map.get(self.role, [])


class OrganizationSettings(models.Model):
    """
    Organization-specific settings and preferences.
    
    This model stores customizable settings for each organization's
    payroll processing and system behavior.
    """
    
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Payroll settings
    auto_calculate_overtime = models.BooleanField(
        default=True,
        help_text="Automatically calculate overtime for hours worked beyond standard"
    )
    
    overtime_threshold_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40,
        help_text="Hours threshold after which overtime applies"
    )
    
    overtime_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.5,
        help_text="Overtime pay multiplier (e.g., 1.5 for time and half)"
    )
    
    # Tax settings
    use_custom_paye_bands = models.BooleanField(
        default=False,
        help_text="Use organization-specific PAYE bands instead of statutory"
    )
    
    auto_submit_returns = models.BooleanField(
        default=False,
        help_text="Automatically submit tax returns to KRA"
    )
    
    # Notification settings
    send_payslip_emails = models.BooleanField(
        default=True,
        help_text="Send payslips to employees via email"
    )
    
    notify_compliance_deadlines = models.BooleanField(
        default=True,
        help_text="Send notifications for compliance deadlines"
    )
    
    # Report settings
    default_report_currency = models.CharField(
        max_length=3,
        default='KES',
        help_text="Default currency for reports"
    )
    
    include_inactive_employees = models.BooleanField(
        default=False,
        help_text="Include inactive employees in reports by default"
    )
    
    # Security settings
    require_payroll_approval = models.BooleanField(
        default=True,
        help_text="Require approval before finalizing payroll"
    )
    
    allow_payroll_editing = models.BooleanField(
        default=False,
        help_text="Allow editing of finalized payroll"
    )
    
    session_timeout_minutes = models.PositiveIntegerField(
        default=120,
        help_text="User session timeout in minutes"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Organization Settings"
        verbose_name_plural = "Organization Settings"
    
    def __str__(self):
        return f"Settings for {self.organization.name}"