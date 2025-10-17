"""
Variable Earnings Models for PayrollHQ

This module handles variable earnings such as overtime, bonuses, and commissions
that are captured for each pay period.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class MonthlyEarningRecord(models.Model):
    """
    Variable earnings for employees per pay period.
    
    This model captures overtime, bonuses, commissions and other variable
    pay components that change from period to period.
    """
    
    EARNING_TYPES = [
        ('OVERTIME', 'Overtime'),
        ('BONUS', 'Bonus'),
        ('COMMISSION', 'Commission'),
        ('ALLOWANCE_ONCE_OFF', 'One-off Allowance'),
        ('BACKPAY', 'Back Pay'),
        ('ACTING_ALLOWANCE', 'Acting Allowance'),
        ('OTHER', 'Other Earning'),
    ]
    
    # Multi-tenancy
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='earning_records'
    )
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='earning_records'
    )
    
    # Pay period
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    
    # Earning details
    earning_type = models.CharField(max_length=30, choices=EARNING_TYPES)
    description = models.CharField(max_length=200)
    
    # Overtime specific fields
    overtime_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Number of overtime hours worked"
    )
    
    overtime_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Overtime rate per hour"
    )
    
    # Amount fields
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Total earning amount"
    )
    
    # Tax treatment
    is_taxable = models.BooleanField(
        default=True,
        help_text="Whether this earning is subject to PAYE"
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
        related_name='earning_records'
    )
    
    # Metadata
    created_by = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    
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
    
    @property
    def calculated_amount(self):
        """Calculate amount from overtime hours and rate if applicable."""
        if self.earning_type == 'OVERTIME' and self.overtime_hours and self.overtime_rate:
            return self.overtime_hours * self.overtime_rate
        return self.amount
    
    def approve(self, approved_by: str):
        """Mark this earning as approved."""
        self.is_approved = True
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at'])
    
    def mark_processed(self, batch):
        """Mark this earning as processed in a payroll batch."""
        self.is_processed = True
        self.processed_in_batch = batch
        self.save(update_fields=['is_processed', 'processed_in_batch'])
    
    def save(self, *args, **kwargs):
        """Override save to calculate overtime amount."""
        if self.earning_type == 'OVERTIME' and self.overtime_hours and self.overtime_rate:
            self.amount = self.overtime_hours * self.overtime_rate
        super().save(*args, **kwargs)