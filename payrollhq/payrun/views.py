"""
API Views for Payrun module

This module provides the critical /api/payrun/calculate_batch/ endpoint
and other payroll batch management views.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.utils import timezone
from django.db import transaction
from datetime import date
import logging

from .models import PayrollBatch, PayslipRecord, PayrollAdjustment
from employees.models import Employee
from calculations.pay_engine import PayEngine, PayEngineError

logger = logging.getLogger(__name__)


class PayrollBatchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payroll batches.
    
    Provides the critical calculate_batch endpoint for payroll processing.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'pay_period_type']
    ordering_fields = ['pay_period_start', 'created_at', 'batch_number']
    ordering = ['-pay_period_start']
    
    def get_queryset(self):
        """Filter queryset by user's organization."""
        user = self.request.user
        if hasattr(user, 'organization'):
            return PayrollBatch.objects.filter(organization=user.organization)
        return PayrollBatch.objects.none()
    
    def perform_create(self, serializer):
        """Create payroll batch for user's organization."""
        user = self.request.user
        serializer.save(
            organization=user.organization,
            created_by=user.username
        )
    
    @action(detail=False, methods=['post'])
    def calculate_batch(self, request):
        """
        Calculate payroll for a batch of employees.
        
        This is the main endpoint for payroll processing. It:
        1. Creates or retrieves a PayrollBatch
        2. Runs the PayEngine for selected employees
        3. Creates PayslipRecord instances
        4. Updates batch totals
        
        Expected payload:
        {
            "pay_period_start": "2024-01-01",
            "pay_period_end": "2024-01-31",
            "pay_date": "2024-02-01",
            "batch_number": "PAY-2024-01",
            "include_all_employees": true,
            "selected_employee_ids": [],
            "variable_earnings": {
                "employee_id": {
                    "overtime_hours": "10.5",
                    "overtime_rate": "500.00",
                    "bonus_amount": "5000.00"
                }
            }
        }
        """
        try:
            user = request.user
            data = request.data
            
            # Validate required fields
            required_fields = ['pay_period_start', 'pay_period_end', 'pay_date', 'batch_number']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response(
                    {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse dates
            try:
                pay_period_start = date.fromisoformat(data['pay_period_start'])
                pay_period_end = date.fromisoformat(data['pay_period_end'])
                pay_date = date.fromisoformat(data['pay_date'])
            except ValueError as e:
                return Response(
                    {'error': f'Invalid date format: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate date logic
            if pay_period_start >= pay_period_end:
                return Response(
                    {'error': 'Pay period start must be before pay period end'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if pay_date <= pay_period_end:
                return Response(
                    {'error': 'Pay date must be after pay period end'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                # Create or get payroll batch
                payroll_batch, created = PayrollBatch.objects.get_or_create(
                    organization=user.organization,
                    batch_number=data['batch_number'],
                    defaults={
                        'pay_period_start': pay_period_start,
                        'pay_period_end': pay_period_end,
                        'pay_date': pay_date,
                        'include_all_employees': data.get('include_all_employees', True),
                        'status': 'CALCULATING',
                        'calculation_notes': data.get('notes', ''),
                    }
                )
                
                if not created and payroll_batch.is_locked:
                    return Response(
                        {'error': 'Payroll batch is locked and cannot be recalculated'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Update status to calculating
                payroll_batch.status = 'CALCULATING'
                payroll_batch.calculated_by = user.username
                payroll_batch.save()
                
                # Get employees to process
                if data.get('include_all_employees', True):
                    employees = user.organization.employees.filter(
                        is_active=True,
                        date_hired__lte=pay_period_end
                    )
                else:
                    employee_ids = data.get('selected_employee_ids', [])
                    employees = user.organization.employees.filter(
                        id__in=employee_ids,
                        is_active=True
                    )
                
                if not employees.exists():
                    return Response(
                        {'error': 'No eligible employees found for payroll calculation'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Initialize PayEngine
                try:
                    pay_engine = PayEngine(calculation_date=pay_period_end)
                except PayEngineError as e:
                    payroll_batch.status = 'DRAFT'
                    payroll_batch.save()
                    return Response(
                        {'error': f'PayEngine initialization failed: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Calculate payroll for each employee
                calculation_results = []
                calculation_errors = []
                variable_earnings_data = data.get('variable_earnings', {})
                
                # Clear existing payslips for this batch
                payroll_batch.payslip_records.all().delete()
                
                for employee in employees:
                    try:
                        # Get variable earnings for this employee
                        employee_variable_earnings = variable_earnings_data.get(str(employee.id), {})
                        
                        # Calculate payroll
                        calculation = pay_engine.calculate_employee_payroll(
                            employee=employee,
                            pay_period_start=pay_period_start,
                            pay_period_end=pay_period_end,
                            variable_earnings=employee_variable_earnings
                        )
                        
                        # Create PayslipRecord
                        payslip_record = PayslipRecord.objects.create(
                            payroll_batch=payroll_batch,
                            employee=employee,
                            
                            # Employee snapshot
                            employee_name=employee.get_full_name(),
                            employee_number=employee.employee_number,
                            employee_kra_pin=employee.kra_pin,
                            employee_nssf_number=employee.nssf_number,
                            employee_sha_number=employee.sha_number,
                            employee_job_title=employee.job_title,
                            employee_department=employee.department,
                            employee_bank_details={
                                'bank_name': employee.bank_name,
                                'bank_branch': employee.bank_branch,
                                'account_number': employee.account_number,
                                'account_name': employee.account_name,
                            },
                            
                            # Calculation results
                            basic_salary=calculation['basic_salary'],
                            house_allowance=calculation['house_allowance'],
                            transport_allowance=calculation['transport_allowance'],
                            medical_allowance=calculation['medical_allowance'],
                            other_allowances=calculation['other_allowances'],
                            overtime_hours=calculation.get('overtime_hours', 0),
                            overtime_amount=calculation.get('overtime_amount', 0),
                            bonus_amount=calculation.get('bonus_amount', 0),
                            commission_amount=calculation.get('commission_amount', 0),
                            gross_pay=calculation['gross_pay'],
                            
                            # NSSF
                            nssf_pensionable_pay=calculation['nssf_pensionable_pay'],
                            nssf_employee=calculation['nssf_employee'],
                            nssf_employer=calculation['nssf_employer'],
                            
                            # Tax calculation
                            taxable_income=calculation['taxable_income'],
                            gross_tax=calculation['gross_tax'],
                            personal_relief=calculation['personal_relief'],
                            insurance_relief=calculation['insurance_relief'],
                            pension_relief=calculation['pension_relief'],
                            mortgage_relief=calculation['mortgage_relief'],
                            disability_relief=calculation['disability_relief'],
                            paye_tax=calculation['paye_tax'],
                            
                            # Post-tax deductions
                            shif_deduction=calculation['shif_deduction'],
                            ahl_deduction=calculation['ahl_deduction'],
                            
                            # Voluntary deductions
                            sacco_deduction=calculation['sacco_deduction'],
                            loan_deductions=calculation['loan_deductions'],
                            advance_deductions=calculation['advance_deductions'],
                            welfare_deductions=calculation['welfare_deductions'],
                            other_deductions=calculation['other_deductions'],
                            
                            # Totals
                            total_statutory_deductions=calculation['total_statutory_deductions'],
                            total_voluntary_deductions=calculation['total_voluntary_deductions'],
                            total_deductions=calculation['total_deductions'],
                            net_pay=calculation['net_pay'],
                            
                            # Metadata
                            calculation_details=calculation['calculation_details'],
                            calculated_at=timezone.now(),
                            calculated_by=user.username,
                        )
                        
                        calculation_results.append({
                            'employee_id': str(employee.id),
                            'employee_name': employee.get_full_name(),
                            'gross_pay': str(calculation['gross_pay']),
                            'net_pay': str(calculation['net_pay']),
                            'status': 'success'
                        })
                        
                    except Exception as e:
                        error_msg = f"Failed to calculate payroll for {employee.get_full_name()}: {str(e)}"
                        logger.error(error_msg)
                        calculation_errors.append({
                            'employee_id': str(employee.id),
                            'employee_name': employee.get_full_name(),
                            'error': str(e),
                            'status': 'error'
                        })
                
                # Update batch totals
                payroll_batch.calculate_totals()
                
                # Update batch status
                if calculation_errors:
                    payroll_batch.status = 'DRAFT'
                    payroll_batch.calculation_notes = f"Calculation completed with {len(calculation_errors)} errors"
                else:
                    payroll_batch.status = 'CALCULATED'
                    payroll_batch.calculation_notes = f"Successfully calculated payroll for {len(calculation_results)} employees"
                
                payroll_batch.calculated_at = timezone.now()
                payroll_batch.save()
                
                response_data = {
                    'batch_id': str(payroll_batch.id),
                    'batch_number': payroll_batch.batch_number,
                    'status': payroll_batch.status,
                    'total_employees': len(calculation_results),
                    'successful_calculations': len(calculation_results),
                    'failed_calculations': len(calculation_errors),
                    'total_gross_pay': str(payroll_batch.total_gross_pay),
                    'total_net_pay': str(payroll_batch.total_net_pay),
                    'calculation_results': calculation_results,
                    'calculation_errors': calculation_errors,
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Payroll batch calculation failed: {str(e)}")
            return Response(
                {'error': f'Payroll calculation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def approve_batch(self, request, pk=None):
        """Approve a calculated payroll batch."""
        payroll_batch = self.get_object()
        user = request.user
        
        if payroll_batch.status != 'CALCULATED':
            return Response(
                {'error': 'Only calculated batches can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payroll_batch.status = 'APPROVED'
        payroll_batch.approved_by = user.username
        payroll_batch.approved_at = timezone.now()
        payroll_batch.approval_notes = request.data.get('notes', '')
        payroll_batch.save()
        
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def lock_batch(self, request, pk=None):
        """Lock a payroll batch, making payslips immutable."""
        payroll_batch = self.get_object()
        user = request.user
        
        if payroll_batch.status != 'APPROVED':
            return Response(
                {'error': 'Only approved batches can be locked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payroll_batch.status = 'LOCKED'
        payroll_batch.locked_by = user.username
        payroll_batch.locked_at = timezone.now()
        payroll_batch.save()
        
        return Response({'status': 'locked'})