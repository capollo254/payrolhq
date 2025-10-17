"""
Voluntary Deductions Models for PayrollHQ

This module handles voluntary deductions that are not statutory requirements.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class VoluntaryDeduction(models.Model):
    """
    One-time or variable voluntary deductions.
    
    This complements the fixed deductions in the Employee model
    and handles variable deductions per pay period.
    """
    
    DEDUCTION_TYPES = [
        ('SACCO_VARIABLE', 'Variable SACCO Contribution'),
        ('LOAN_PAYMENT', 'Loan Payment'),
        ('ADVANCE_RECOVERY', 'Advance Recovery'),
        ('INSURANCE_PREMIUM', 'Insurance Premium'),
        ('WELFARE_CONTRIBUTION', 'Welfare Contribution'),
        ('TRAINING_FEE', 'Training Fee'),
        ('UNIFORM_DEDUCTION', 'Uniform Deduction'),
        ('DAMAGE_RECOVERY', 'Damage Recovery'),
        ('OTHER', 'Other Deduction'),
    ]
    
    # Multi-tenancy
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='voluntary_deductions'
    )
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='voluntary_deductions'
    )
    
    # Pay period
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    
    # Deduction details
    deduction_type = models.CharField(max_length=30, choices=DEDUCTION_TYPES)
    description = models.CharField(max_length=200)
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Deduction amount"
    )
    
    # Reference information
    reference_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Reference number for loan, advance, etc."
    )
    
    # Approval workflow
    is_approved = models.BooleanField(default=False)
    approved_by = models.CharField(max_length=100, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Processing status
    is_processed = models.BooleanField(
        default=False,
        help_text="Whether this has been included in payroll"
    )
    
    processed_in_batch = models.ForeignKey(
        'payrun.PayrollBatch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voluntary_deductions'
    )
    
    # Metadata
    created_by = models.CharField(max_length=100)
    reason = models.TextField(help_text="Reason for deduction")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-pay_period_start', 'employee__last_name']
        indexes = [
            models.Index(fields=['organization', 'pay_period_start']),
            models.Index(fields=['employee', 'pay_period_start']),
            models.Index(fields=['is_processed', 'is_approved']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_short_name()} - {self.description} ({self.amount})"
    
    def approve(self, approved_by: str):
        """Mark this deduction as approved."""
        self.is_approved = True
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at'])
    
    def mark_processed(self, batch):
        """Mark this deduction as processed in a payroll batch."""
        self.is_processed = True
        self.processed_in_batch = batch
        self.save(update_fields=['is_processed', 'processed_in_batch'])