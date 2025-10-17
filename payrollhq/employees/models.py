"""
Employee Models for PayrollHQ

This module contains all employee-related models with strict Kenyan compliance
requirements including mandatory KRA PIN, NSSF Number, and SHA Number.
"""

from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class Employee(models.Model):
    """
    Core employee model with mandatory Kenyan identification numbers.
    
    This model enforces the entry of all mandatory Kenyan IDs:
    - KRA PIN (mandatory for tax compliance)
    - NSSF Number (mandatory for social security)
    - SHA Number (mandatory for health insurance)
    """
    
    EMPLOYMENT_TYPES = [
        ('PERMANENT', 'Permanent Employee'),
        ('CONTRACT', 'Contract Employee'),
        ('CASUAL', 'Casual Worker'),
        ('INTERN', 'Intern'),
        ('CONSULTANT', 'Consultant'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('SINGLE', 'Single'),
        ('MARRIED', 'Married'),
        ('DIVORCED', 'Divorced'),
        ('WIDOWED', 'Widowed'),
        ('SEPARATED', 'Separated'),
    ]
    
    # Multi-tenancy relationship
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='employees'
    )
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Employee identification
    employee_number = models.CharField(
        max_length=50,
        help_text="Internal employee identification number"
    )
    
    # Personal information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        default='SINGLE'
    )
    
    # Contact information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    
    # Address information
    residential_address = models.TextField()
    postal_address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # MANDATORY Kenyan identification numbers
    national_id = models.CharField(
        max_length=8,
        validators=[
            RegexValidator(
                regex=r'^\d{8}$',
                message='National ID must be 8 digits'
            )
        ],
        help_text="Kenyan National Identity Card number (8 digits)"
    )
    
    kra_pin = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^A\d{9}[A-Z]$',
                message='KRA PIN must be in format A000000000A'
            )
        ],
        help_text="KRA PIN number (MANDATORY for payroll)"
    )
    
    nssf_number = models.CharField(
        max_length=20,
        help_text="NSSF membership number (MANDATORY)"
    )
    
    sha_number = models.CharField(
        max_length=20,
        help_text="SHA (SHIF) number (MANDATORY for health insurance)"
    )
    
    # Optional identification numbers
    nhif_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="NHIF number (if applicable)"
    )
    
    passport_number = models.CharField(max_length=20, blank=True)
    driving_license = models.CharField(max_length=20, blank=True)
    
    # Employment information
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        default='PERMANENT'
    )
    
    date_hired = models.DateField()
    date_terminated = models.DateField(null=True, blank=True)
    
    probation_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date of probation period"
    )
    
    contract_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Contract end date (for contract employees)"
    )
    
    # Job information
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100, default='Head Office')
    
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports'
    )
    
    # Salary information
    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monthly basic salary in KES"
    )
    
    pay_frequency = models.CharField(
        max_length=20,
        choices=[
            ('MONTHLY', 'Monthly'),
            ('WEEKLY', 'Weekly'),
            ('DAILY', 'Daily'),
        ],
        default='MONTHLY'
    )
    
    # Bank information
    bank_name = models.CharField(max_length=100)
    bank_branch = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200)
    
    # Tax relief and exemptions
    has_disability_exemption = models.BooleanField(
        default=False,
        help_text="Qualifies for disability tax exemption"
    )
    
    insurance_relief_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Monthly insurance relief amount"
    )
    
    pension_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Monthly voluntary pension contribution"
    )
    
    mortgage_interest = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Monthly mortgage interest for relief"
    )
    
    # Employee status
    is_active = models.BooleanField(default=True)
    is_on_leave = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(max_length=20)
    emergency_contact_relationship = models.CharField(max_length=50)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['organization', 'employee_number']),
            models.Index(fields=['kra_pin']),
            models.Index(fields=['nssf_number']),
            models.Index(fields=['sha_number']),
        ]
        constraints = [
            # Ensure unique employee numbers within organization
            models.UniqueConstraint(
                fields=['organization', 'employee_number'],
                name='unique_employee_number_per_org'
            ),
            # Ensure unique national IDs across the system
            models.UniqueConstraint(
                fields=['national_id'],
                name='unique_national_id'
            ),
            # Ensure unique KRA PINs across the system
            models.UniqueConstraint(
                fields=['kra_pin'],
                name='unique_kra_pin'
            ),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_number})"
    
    def get_full_name(self):
        """Return the employee's full name."""
        names = [self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        names.append(self.last_name)
        return ' '.join(names)
    
    def get_short_name(self):
        """Return the employee's short name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate employee's age."""
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def years_of_service(self):
        """Calculate years of service."""
        end_date = self.date_terminated or timezone.now().date()
        return (end_date - self.date_hired).days / 365.25
    
    @property
    def is_on_probation(self):
        """Check if employee is on probation."""
        if not self.probation_end_date:
            return False
        return timezone.now().date() <= self.probation_end_date
    
    @property
    def contract_expired(self):
        """Check if contract has expired."""
        if not self.contract_end_date:
            return False
        return timezone.now().date() > self.contract_end_date
    
    def validate_kenyan_ids(self):
        """Validate all mandatory Kenyan identification numbers."""
        errors = []
        
        if not self.kra_pin:
            errors.append("KRA PIN is mandatory for all employees")
        
        if not self.nssf_number:
            errors.append("NSSF Number is mandatory for all employees")
        
        if not self.sha_number:
            errors.append("SHA Number is mandatory for all employees")
        
        return errors
    
    def get_monthly_basic_salary(self):
        """Get monthly basic salary regardless of pay frequency."""
        if self.pay_frequency == 'MONTHLY':
            return self.basic_salary
        elif self.pay_frequency == 'WEEKLY':
            return self.basic_salary * Decimal('4.33')  # Average weeks per month
        elif self.pay_frequency == 'DAILY':
            return self.basic_salary * Decimal('22')  # Average working days per month
        return self.basic_salary


class EmployeeAllowance(models.Model):
    """
    Fixed allowances for employees (house, transport, etc.).
    """
    
    ALLOWANCE_TYPES = [
        ('HOUSE', 'House Allowance'),
        ('TRANSPORT', 'Transport Allowance'),
        ('MEDICAL', 'Medical Allowance'),
        ('LUNCH', 'Lunch Allowance'),
        ('COMMUNICATION', 'Communication Allowance'),
        ('FUEL', 'Fuel Allowance'),
        ('ENTERTAINMENT', 'Entertainment Allowance'),
        ('OTHER', 'Other Allowance'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='allowances'
    )
    
    allowance_type = models.CharField(max_length=20, choices=ALLOWANCE_TYPES)
    description = models.CharField(max_length=200, blank=True)
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monthly allowance amount"
    )
    
    is_taxable = models.BooleanField(
        default=True,
        help_text="Whether this allowance is subject to PAYE tax"
    )
    
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['employee', 'allowance_type']
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'allowance_type'],
                condition=models.Q(is_active=True),
                name='unique_active_allowance_per_type'
            )
        ]
    
    def __str__(self):
        return f"{self.employee.get_short_name()} - {self.get_allowance_type_display()}"


class EmployeeDeduction(models.Model):
    """
    Fixed deductions for employees (loans, advance payments, etc.).
    """
    
    DEDUCTION_TYPES = [
        ('LOAN', 'Loan Repayment'),
        ('ADVANCE', 'Salary Advance'),
        ('SACCO', 'SACCO Contribution'),
        ('HELB', 'HELB Loan'),
        ('WELFARE', 'Welfare Contribution'),
        ('UNIFORM', 'Uniform Deduction'),
        ('TRAINING', 'Training Fee'),
        ('OTHER', 'Other Deduction'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='deductions'
    )
    
    deduction_type = models.CharField(max_length=20, choices=DEDUCTION_TYPES)
    description = models.CharField(max_length=200)
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monthly deduction amount"
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total amount to be deducted (for loans/advances)"
    )
    
    balance_remaining = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        help_text="Remaining balance to be deducted"
    )
    
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['employee', 'deduction_type']
    
    def __str__(self):
        return f"{self.employee.get_short_name()} - {self.description}"
    
    @property
    def is_completed(self):
        """Check if deduction is completed (for loans/advances)."""
        if self.total_amount:
            return self.balance_remaining <= 0
        return False
    
    def calculate_remaining_months(self):
        """Calculate remaining months for loan/advance repayment."""
        if self.total_amount and self.amount > 0:
            return int(self.balance_remaining / self.amount)
        return 0


class EmploymentHistory(models.Model):
    """
    Track employment history and changes for audit purposes.
    """
    
    CHANGE_TYPES = [
        ('HIRE', 'Hired'),
        ('PROMOTION', 'Promoted'),
        ('TRANSFER', 'Transferred'),
        ('SALARY_CHANGE', 'Salary Change'),
        ('DEPARTMENT_CHANGE', 'Department Change'),
        ('TERMINATION', 'Terminated'),
        ('SUSPENSION', 'Suspended'),
        ('REINSTATEMENT', 'Reinstated'),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='employment_history'
    )
    
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    change_date = models.DateField()
    
    # Previous values
    previous_job_title = models.CharField(max_length=100, blank=True)
    previous_department = models.CharField(max_length=100, blank=True)
    previous_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # New values
    new_job_title = models.CharField(max_length=100, blank=True)
    new_department = models.CharField(max_length=100, blank=True)
    new_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    changed_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-change_date', '-created_at']
        verbose_name_plural = "Employment Histories"
    
    def __str__(self):
        return f"{self.employee.get_short_name()} - {self.get_change_type_display()}"