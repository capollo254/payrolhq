"""
Payrun Models for PayrollHQ

This module contains models for managing payroll runs and payslip records.
PayslipRecord data is treated as immutable once a payroll batch is locked.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class PayrollBatch(models.Model):
    """
    Represents a payroll batch/run for a specific period.
    
    Each batch groups multiple employees' payslips for a specific pay period
    and tracks the overall status of the payroll run.
    """
    
    BATCH_STATUS = [
        ('DRAFT', 'Draft'),
        ('CALCULATING', 'Calculating'),
        ('CALCULATED', 'Calculated'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
        ('LOCKED', 'Locked'),
        ('REMITTED', 'Remitted'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAY_PERIODS = [
        ('MONTHLY', 'Monthly'),
        ('WEEKLY', 'Weekly'),
        ('BIWEEKLY', 'Bi-weekly'),
    ]
    
    # Multi-tenancy relationship
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='payroll_batches'
    )
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Batch identification
    batch_number = models.CharField(
        max_length=50,
        help_text="Human-readable batch number (e.g., PAY-2024-01)"
    )
    
    # Pay period information
    pay_period_type = models.CharField(
        max_length=20,
        choices=PAY_PERIODS,
        default='MONTHLY'
    )
    
    pay_period_start = models.DateField(
        help_text="Start date of the pay period"
    )
    
    pay_period_end = models.DateField(
        help_text="End date of the pay period"
    )
    
    pay_date = models.DateField(
        help_text="Actual pay date for employees"
    )
    
    # Batch status and workflow
    status = models.CharField(
        max_length=20,
        choices=BATCH_STATUS,
        default='DRAFT'
    )
    
    # Employee selection
    include_all_employees = models.BooleanField(
        default=True,
        help_text="Include all active employees in this batch"
    )
    
    selected_employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        help_text="Specific employees to include (if not all)"
    )
    
    # Calculation summary
    total_employees = models.PositiveIntegerField(default=0)
    total_gross_pay = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )
    total_net_pay = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )
    total_paye_tax = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )
    total_nssf = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )
    total_shif = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )
    total_ahl = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0')
    )
    
    # Workflow tracking
    calculated_at = models.DateTimeField(null=True, blank=True)
    calculated_by = models.CharField(max_length=100, blank=True)
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.CharField(max_length=100, blank=True)
    
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=100, blank=True)
    
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=100, blank=True)
    
    remitted_at = models.DateTimeField(null=True, blank=True)
    remitted_by = models.CharField(max_length=100, blank=True)
    
    # Notes and comments
    calculation_notes = models.TextField(blank=True)
    review_notes = models.TextField(blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-pay_period_start']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'pay_period_start']),
            models.Index(fields=['batch_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'batch_number'],
                name='unique_batch_number_per_org'
            )
        ]
    
    def __str__(self):
        return f"{self.batch_number} ({self.pay_period_start} to {self.pay_period_end})"
    
    @property
    def is_locked(self):
        """Check if the batch is locked and immutable."""
        return self.status in ['LOCKED', 'REMITTED']
    
    @property
    def can_be_edited(self):
        """Check if the batch can still be edited."""
        return self.status in ['DRAFT', 'CALCULATING', 'CALCULATED']
    
    @property
    def period_display(self):
        """Get a human-readable pay period display."""
        return f"{self.pay_period_start.strftime('%b %Y')}"
    
    def get_employees_to_process(self):
        """Get the list of employees to process in this batch."""
        if self.include_all_employees:
            return self.organization.employees.filter(
                is_active=True,
                date_hired__lte=self.pay_period_end
            )
        else:
            return self.selected_employees.filter(is_active=True)
    
    def calculate_totals(self):
        """Calculate and update batch totals from payslip records."""
        payslips = self.payslip_records.all()
        
        self.total_employees = payslips.count()
        self.total_gross_pay = sum(p.gross_pay for p in payslips)
        self.total_net_pay = sum(p.net_pay for p in payslips)
        self.total_paye_tax = sum(p.paye_tax for p in payslips)
        self.total_nssf = sum(p.nssf_employee + p.nssf_employer for p in payslips)
        self.total_shif = sum(p.shif_deduction for p in payslips)
        self.total_ahl = sum(p.ahl_deduction for p in payslips)
        
        self.save(update_fields=[
            'total_employees', 'total_gross_pay', 'total_net_pay',
            'total_paye_tax', 'total_nssf', 'total_shif', 'total_ahl'
        ])


class PayslipRecord(models.Model):
    """
    Immutable payslip record for an employee in a specific pay period.
    
    Once a PayrollBatch is locked, these records become read-only and serve
    as the authoritative record of what was paid to each employee.
    """
    
    # Relationships
    payroll_batch = models.ForeignKey(
        PayrollBatch,
        on_delete=models.CASCADE,
        related_name='payslip_records'
    )
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='payslip_records'
    )
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Employee snapshot (for historical accuracy)
    employee_name = models.CharField(max_length=300)
    employee_number = models.CharField(max_length=50)
    employee_kra_pin = models.CharField(max_length=11)
    employee_nssf_number = models.CharField(max_length=20)
    employee_sha_number = models.CharField(max_length=20)
    employee_job_title = models.CharField(max_length=100)
    employee_department = models.CharField(max_length=100)
    employee_bank_details = models.JSONField(default=dict)
    
    # Basic salary and earnings
    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Basic salary for the period"
    )
    
    # Allowances (detailed breakdown)
    house_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    
    # Variable earnings
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0'))
    overtime_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    
    # Total gross earnings
    gross_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total gross pay before deductions"
    )
    
    # Statutory deductions calculation breakdown
    taxable_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Income subject to PAYE tax (after NSSF and pension)"
    )
    
    # NSSF deductions
    nssf_pensionable_pay = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    nssf_employee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    nssf_employer = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    
    # Tax calculation details
    gross_tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    personal_relief = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    insurance_relief = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    pension_relief = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    mortgage_relief = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    disability_relief = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    
    # Final PAYE tax
    paye_tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Final PAYE tax after reliefs"
    )
    
    # Post-tax statutory deductions
    shif_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        help_text="SHIF deduction (2.75% of gross)"
    )
    
    ahl_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        help_text="AHL deduction (1.5% of gross)"
    )
    
    # Voluntary deductions
    sacco_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    loan_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    advance_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    welfare_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    
    # Total deductions and net pay
    total_statutory_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total statutory deductions (PAYE, NSSF, SHIF, AHL)"
    )
    
    total_voluntary_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total voluntary deductions"
    )
    
    total_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total all deductions"
    )
    
    net_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Final net pay to employee"
    )
    
    # Detailed calculation data (for audit and debugging)
    calculation_details = models.JSONField(
        default=dict,
        help_text="Detailed breakdown of all calculations"
    )
    
    # Processing metadata
    calculated_at = models.DateTimeField()
    calculated_by = models.CharField(max_length=100)
    
    # Payslip delivery
    payslip_sent = models.BooleanField(default=False)
    payslip_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Payment processing
    payment_processed = models.BooleanField(default=False)
    payment_processed_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['employee_name']
        indexes = [
            models.Index(fields=['payroll_batch', 'employee']),
            models.Index(fields=['employee', '-created_at']),
            models.Index(fields=['employee_kra_pin']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['payroll_batch', 'employee'],
                name='unique_payslip_per_employee_per_batch'
            )
        ]
    
    def __str__(self):
        return f"{self.employee_name} - {self.payroll_batch.period_display}"
    
    @property
    def can_be_modified(self):
        """Check if this payslip can still be modified."""
        return self.payroll_batch.can_be_edited
    
    def get_total_earnings(self):
        """Calculate total earnings (basic + allowances + variable)."""
        return (
            self.basic_salary + 
            self.house_allowance + 
            self.transport_allowance + 
            self.medical_allowance + 
            self.other_allowances + 
            self.overtime_amount + 
            self.bonus_amount + 
            self.commission_amount
        )
    
    def get_employer_costs(self):
        """Calculate total employer costs."""
        return self.gross_pay + self.nssf_employer
    
    def validate_calculations(self):
        """Validate that calculations are mathematically correct."""
        errors = []
        
        # Validate gross pay calculation
        calculated_gross = self.get_total_earnings()
        if abs(calculated_gross - self.gross_pay) > Decimal('0.01'):
            errors.append(f"Gross pay mismatch: calculated {calculated_gross}, stored {self.gross_pay}")
        
        # Validate total deductions
        calculated_total_deductions = (
            self.total_statutory_deductions + self.total_voluntary_deductions
        )
        if abs(calculated_total_deductions - self.total_deductions) > Decimal('0.01'):
            errors.append("Total deductions calculation error")
        
        # Validate net pay
        calculated_net = self.gross_pay - self.total_deductions
        if abs(calculated_net - self.net_pay) > Decimal('0.01'):
            errors.append(f"Net pay mismatch: calculated {calculated_net}, stored {self.net_pay}")
        
        return errors
    
    def save(self, *args, **kwargs):
        """Override save to prevent modifications when batch is locked."""
        if self.pk and self.payroll_batch.is_locked:
            # Allow only specific fields to be updated when locked
            allowed_fields = [
                'payslip_sent', 'payslip_sent_at', 
                'payment_processed', 'payment_processed_at', 
                'payment_reference'
            ]
            
            if 'update_fields' not in kwargs or not all(
                field in allowed_fields for field in kwargs.get('update_fields', [])
            ):
                raise ValueError(
                    "PayslipRecord cannot be modified when payroll batch is locked"
                )
        
        super().save(*args, **kwargs)


class PayrollAdjustment(models.Model):
    """
    Post-calculation adjustments to payslips.
    
    Used for corrections or one-time adjustments that need to be applied
    after the main payroll calculation.
    """
    
    ADJUSTMENT_TYPES = [
        ('EARNINGS_ADJUSTMENT', 'Earnings Adjustment'),
        ('DEDUCTION_ADJUSTMENT', 'Deduction Adjustment'),
        ('TAX_ADJUSTMENT', 'Tax Adjustment'),
        ('CORRECTION', 'Correction'),
        ('BACKPAY', 'Back Pay'),
        ('RECOVERY', 'Recovery'),
    ]
    
    payslip_record = models.ForeignKey(
        PayslipRecord,
        on_delete=models.CASCADE,
        related_name='adjustments'
    )
    
    adjustment_type = models.CharField(max_length=30, choices=ADJUSTMENT_TYPES)
    description = models.CharField(max_length=200)
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Positive for additions, negative for deductions"
    )
    
    affects_tax = models.BooleanField(
        default=True,
        help_text="Whether this adjustment affects taxable income"
    )
    
    approved_by = models.CharField(max_length=100)
    approved_at = models.DateTimeField()
    
    reason = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payslip_record.employee_name} - {self.description}"
    
    def save(self, *args, **kwargs):
        """Prevent adjustments when batch is locked."""
        if self.payslip_record.payroll_batch.is_locked:
            raise ValueError(
                "Cannot add adjustments when payroll batch is locked"
            )
        super().save(*args, **kwargs)