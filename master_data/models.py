"""
Master Data Models for PayrollHQ

This module contains the core compliance and configuration models that drive
the Kenyan payroll calculations. All statutory rates and thresholds are
stored here to ensure easy updates and compliance management.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import json


class ComplianceSetting(models.Model):
    """
    Central repository for all Kenyan statutory payroll compliance settings.
    
    This model stores all dynamic rates and thresholds required for:
    - PAYE Tax Bands and rates
    - Personal Relief amounts
    - NSSF contribution tiers and rates
    - SHIF (SHA) contribution rates
    - AHL (Affordable Housing Levy) rates
    - Other statutory deductions and reliefs
    
    The model supports versioning to maintain historical compliance data
    and easy updates when government rates change.
    """
    
    COMPLIANCE_TYPES = [
        ('PAYE_TAX_BANDS', 'PAYE Tax Bands'),
        ('PERSONAL_RELIEF', 'Personal Relief'),
        ('NSSF_RATES', 'NSSF Contribution Rates'),
        ('SHIF_RATES', 'SHIF Contribution Rates'),
        ('AHL_RATES', 'Affordable Housing Levy Rates'),
        ('INSURANCE_RELIEF', 'Insurance Relief'),
        ('PENSION_RELIEF', 'Pension Relief'),
        ('MORTGAGE_RELIEF', 'Mortgage Interest Relief'),
        ('DISABILITY_EXEMPTION', 'Disability Exemption'),
    ]
    
    # Core identification fields
    compliance_type = models.CharField(
        max_length=50,
        choices=COMPLIANCE_TYPES,
        help_text="Type of compliance setting"
    )
    
    effective_date = models.DateField(
        help_text="Date when this setting becomes effective"
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this setting expires (null for current settings)"
    )
    
    # Structured compliance data stored as JSON
    compliance_data = models.JSONField(
        help_text="Structured data containing rates, bands, and thresholds"
    )
    
    # Administrative fields
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this setting is currently active"
    )
    
    created_by = models.CharField(
        max_length=100,
        default='system',
        help_text="User who created this setting"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Audit and approval fields
    approved_by = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="User who approved this compliance setting"
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this setting was approved"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this compliance setting"
    )
    
    class Meta:
        ordering = ['-effective_date', 'compliance_type']
        indexes = [
            models.Index(fields=['compliance_type', 'effective_date']),
            models.Index(fields=['is_active', 'effective_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['compliance_type', 'effective_date'],
                name='unique_compliance_per_date'
            )
        ]
    
    def __str__(self):
        return f"{self.get_compliance_type_display()} - {self.effective_date}"
    
    @classmethod
    def get_current_setting(cls, compliance_type, as_of_date=None):
        """
        Retrieve the current active compliance setting for a given type.
        
        Args:
            compliance_type (str): The type of compliance setting
            as_of_date (date, optional): Date to check against. Defaults to today.
        
        Returns:
            ComplianceSetting: The active setting or None if not found
        """
        if as_of_date is None:
            as_of_date = timezone.now().date()
        
        return cls.objects.filter(
            compliance_type=compliance_type,
            effective_date__lte=as_of_date,
            is_active=True
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=as_of_date)
        ).first()
    
    @property
    def is_current(self):
        """Check if this setting is currently effective."""
        today = timezone.now().date()
        return (
            self.is_active and 
            self.effective_date <= today and 
            (self.end_date is None or self.end_date >= today)
        )
    
    def get_paye_tax_bands(self):
        """
        Extract PAYE tax bands from compliance_data.
        
        Returns:
            list: List of tax band dictionaries with min_amount, max_amount, rate
        """
        if self.compliance_type != 'PAYE_TAX_BANDS':
            return []
        
        return self.compliance_data.get('tax_bands', [])
    
    def get_personal_relief_amount(self):
        """
        Get the personal relief amount.
        
        Returns:
            Decimal: Personal relief amount in KES
        """
        if self.compliance_type != 'PERSONAL_RELIEF':
            return Decimal('0')
        
        return Decimal(str(self.compliance_data.get('monthly_amount', '2400')))
    
    def get_nssf_rates(self):
        """
        Extract NSSF contribution rates and tiers.
        
        Returns:
            dict: NSSF configuration with tiers and rates
        """
        if self.compliance_type != 'NSSF_RATES':
            return {}
        
        return self.compliance_data
    
    def get_shif_rate(self):
        """
        Get SHIF contribution rate.
        
        Returns:
            Decimal: SHIF rate as a percentage
        """
        if self.compliance_type != 'SHIF_RATES':
            return Decimal('0')
        
        return Decimal(str(self.compliance_data.get('rate_percentage', '2.75')))
    
    def get_ahl_rate(self):
        """
        Get AHL (Affordable Housing Levy) rate.
        
        Returns:
            Decimal: AHL rate as a percentage
        """
        if self.compliance_type != 'AHL_RATES':
            return Decimal('0')
        
        return Decimal(str(self.compliance_data.get('rate_percentage', '1.5')))
    
    def validate_compliance_data(self):
        """
        Validate the structure of compliance_data based on compliance_type.
        
        Raises:
            ValueError: If the data structure is invalid
        """
        validators = {
            'PAYE_TAX_BANDS': self._validate_paye_data,
            'PERSONAL_RELIEF': self._validate_personal_relief_data,
            'NSSF_RATES': self._validate_nssf_data,
            'SHIF_RATES': self._validate_percentage_data,
            'AHL_RATES': self._validate_percentage_data,
        }
        
        validator = validators.get(self.compliance_type)
        if validator:
            validator()
    
    def _validate_paye_data(self):
        """Validate PAYE tax bands structure."""
        if 'tax_bands' not in self.compliance_data:
            raise ValueError("PAYE tax bands must contain 'tax_bands' key")
        
        bands = self.compliance_data['tax_bands']
        if not isinstance(bands, list) or not bands:
            raise ValueError("Tax bands must be a non-empty list")
        
        for i, band in enumerate(bands):
            required_keys = ['min_amount', 'max_amount', 'rate']
            for key in required_keys:
                if key not in band:
                    raise ValueError(f"Tax band {i} missing required key: {key}")
    
    def _validate_personal_relief_data(self):
        """Validate personal relief structure."""
        if 'monthly_amount' not in self.compliance_data:
            raise ValueError("Personal relief must contain 'monthly_amount'")
        
        try:
            amount = Decimal(str(self.compliance_data['monthly_amount']))
            if amount < 0:
                raise ValueError("Personal relief amount cannot be negative")
        except (ValueError, TypeError):
            raise ValueError("Personal relief amount must be a valid number")
    
    def _validate_nssf_data(self):
        """Validate NSSF rates structure."""
        required_keys = ['employee_rate', 'employer_rate', 'tiers']
        for key in required_keys:
            if key not in self.compliance_data:
                raise ValueError(f"NSSF data missing required key: {key}")
    
    def _validate_percentage_data(self):
        """Validate percentage-based rates (SHIF, AHL)."""
        if 'rate_percentage' not in self.compliance_data:
            raise ValueError("Percentage rate must contain 'rate_percentage'")
        
        try:
            rate = Decimal(str(self.compliance_data['rate_percentage']))
            if not (0 <= rate <= 100):
                raise ValueError("Percentage rate must be between 0 and 100")
        except (ValueError, TypeError):
            raise ValueError("Rate percentage must be a valid number")
    
    def save(self, *args, **kwargs):
        """Override save to validate compliance data."""
        self.validate_compliance_data()
        super().save(*args, **kwargs)


class PayrollConstants(models.Model):
    """
    Static payroll constants and configuration values.
    
    This model stores non-rate based configuration such as:
    - Minimum wage thresholds
    - Working days per month
    - Currency settings
    - Rounding rules
    """
    
    CONSTANT_TYPES = [
        ('MINIMUM_WAGE', 'Minimum Wage'),
        ('WORKING_DAYS', 'Working Days Configuration'),
        ('CURRENCY', 'Currency Settings'),
        ('ROUNDING', 'Rounding Rules'),
        ('OVERTIME', 'Overtime Configuration'),
    ]
    
    constant_type = models.CharField(
        max_length=50,
        choices=CONSTANT_TYPES,
        unique=True
    )
    
    constant_value = models.JSONField(
        help_text="Configuration value(s) for this constant"
    )
    
    effective_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['constant_type']
    
    def __str__(self):
        return f"{self.get_constant_type_display()}"
    
    @classmethod
    def get_constant(cls, constant_type):
        """
        Retrieve a payroll constant value.
        
        Args:
            constant_type (str): The type of constant to retrieve
        
        Returns:
            dict: The constant value or empty dict if not found
        """
        try:
            constant = cls.objects.get(
                constant_type=constant_type,
                is_active=True
            )
            return constant.constant_value
        except cls.DoesNotExist:
            return {}


class ComplianceAuditLog(models.Model):
    """
    Audit log for compliance setting changes.
    
    This model tracks all changes to compliance settings for
    audit purposes and regulatory compliance.
    """
    
    ACTION_TYPES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('APPROVE', 'Approved'),
        ('REJECT', 'Rejected'),
    ]
    
    compliance_setting = models.ForeignKey(
        ComplianceSetting,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    old_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Previous state of the compliance setting"
    )
    
    new_data = models.JSONField(
        null=True,
        blank=True,
        help_text="New state of the compliance setting"
    )
    
    changed_by = models.CharField(max_length=100)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    reason = models.TextField(
        blank=True,
        help_text="Reason for the change"
    )
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['compliance_setting', '-changed_at']),
            models.Index(fields=['changed_by', '-changed_at']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.compliance_setting} by {self.changed_by}"