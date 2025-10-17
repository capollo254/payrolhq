"""
PayEngine - Kenyan Payroll Calculation Engine

This module contains the core PayEngine class that orchestrates all payroll
calculations according to Kenyan tax and labor laws. The engine follows
the correct calculation sequence and applies all statutory requirements.

Calculation Flow:
1. Calculate Gross Pay (Basic + Allowances + Variable Earnings)
2. Calculate NSSF Employee Contribution (deducted from gross)
3. Calculate Allowable Pension Contributions
4. Calculate Taxable Income (Gross - NSSF - Pension)
5. Calculate Gross Tax using progressive tax bands
6. Apply Personal Relief and other reliefs
7. Calculate Final PAYE Tax
8. Calculate Post-Tax Deductions (SHIF, AHL)
9. Calculate Voluntary Deductions
10. Calculate Net Pay
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple, Optional
from datetime import date
import logging
from django.db import models

from master_data.models import ComplianceSetting
from employees.models import Employee, EmployeeAllowance, EmployeeDeduction

logger = logging.getLogger(__name__)


class PayEngineError(Exception):
    """Custom exception for PayEngine errors."""
    pass


class PayEngine:
    """
    Comprehensive Kenyan payroll calculation engine.
    
    This class handles all aspects of Kenyan payroll calculation including:
    - PAYE tax using progressive bands
    - NSSF contributions (employee and employer)
    - SHIF (SHA) health insurance contributions
    - AHL (Affordable Housing Levy)
    - Personal and other tax reliefs
    - Voluntary deductions
    """
    
    def __init__(self, calculation_date: date = None):
        """
        Initialize the PayEngine with compliance settings for a specific date.
        
        Args:
            calculation_date: Date for which to retrieve compliance settings
        """
        self.calculation_date = calculation_date or date.today()
        self.compliance_cache = {}
        self._load_compliance_settings()
    
    def _load_compliance_settings(self):
        """Load all compliance settings for the calculation date."""
        try:
            # Load PAYE tax bands
            paye_setting = ComplianceSetting.get_current_setting(
                'PAYE_TAX_BANDS', 
                self.calculation_date
            )
            if not paye_setting:
                raise PayEngineError("PAYE tax bands not configured for calculation date")
            
            self.compliance_cache['paye_bands'] = paye_setting.get_paye_tax_bands()
            
            # Load Personal Relief
            relief_setting = ComplianceSetting.get_current_setting(
                'PERSONAL_RELIEF',
                self.calculation_date
            )
            if not relief_setting:
                raise PayEngineError("Personal relief not configured for calculation date")
            
            self.compliance_cache['personal_relief'] = relief_setting.get_personal_relief_amount()
            
            # Load NSSF rates
            nssf_setting = ComplianceSetting.get_current_setting(
                'NSSF_RATES',
                self.calculation_date
            )
            if not nssf_setting:
                raise PayEngineError("NSSF rates not configured for calculation date")
            
            self.compliance_cache['nssf_config'] = nssf_setting.get_nssf_rates()
            
            # Load SHIF rates
            shif_setting = ComplianceSetting.get_current_setting(
                'SHIF_RATES',
                self.calculation_date
            )
            if not shif_setting:
                raise PayEngineError("SHIF rates not configured for calculation date")
            
            self.compliance_cache['shif_rate'] = shif_setting.get_shif_rate()
            
            # Load AHL rates
            ahl_setting = ComplianceSetting.get_current_setting(
                'AHL_RATES',
                self.calculation_date
            )
            if not ahl_setting:
                raise PayEngineError("AHL rates not configured for calculation date")
            
            self.compliance_cache['ahl_rate'] = ahl_setting.get_ahl_rate()
            
            logger.info(f"Loaded compliance settings for {self.calculation_date}")
            
        except Exception as e:
            logger.error(f"Failed to load compliance settings: {str(e)}")
            raise PayEngineError(f"Cannot initialize PayEngine: {str(e)}")
    
    def calculate_employee_payroll(
        self, 
        employee: Employee, 
        pay_period_start: date,
        pay_period_end: date,
        variable_earnings: Dict[str, Decimal] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate complete payroll for a single employee.
        
        Args:
            employee: Employee instance
            pay_period_start: Start date of pay period
            pay_period_end: End date of pay period
            variable_earnings: Dict of variable earnings (overtime, bonus, etc.)
        
        Returns:
            Dict containing all calculated payroll components
        """
        try:
            logger.info(f"Calculating payroll for {employee.get_full_name()}")
            
            if variable_earnings is None:
                variable_earnings = {}
            
            # Initialize calculation result
            calculation = {
                'employee_id': str(employee.id),
                'employee_name': employee.get_full_name(),
                'employee_number': employee.employee_number,
                'pay_period_start': pay_period_start,
                'pay_period_end': pay_period_end,
                'calculation_date': self.calculation_date,
            }
            
            # Step 1: Calculate Gross Pay
            gross_components = self._calculate_gross_pay(
                employee, 
                pay_period_start, 
                pay_period_end,
                variable_earnings
            )
            calculation.update(gross_components)
            
            # Step 2: Calculate NSSF Employee Contribution
            nssf_components = self._calculate_nssf_contributions(
                calculation['gross_pay']
            )
            calculation.update(nssf_components)
            
            # Step 3: Calculate Allowable Pension Relief
            pension_relief = self._calculate_pension_relief(
                employee, 
                calculation['gross_pay']
            )
            calculation['pension_relief'] = pension_relief
            
            # Step 4: Calculate Taxable Income
            calculation['taxable_income'] = (
                calculation['gross_pay'] - 
                calculation['nssf_employee'] - 
                pension_relief
            )
            
            # Step 5: Calculate PAYE Tax
            tax_components = self._calculate_paye_tax(
                employee,
                calculation['taxable_income']
            )
            calculation.update(tax_components)
            
            # Step 6: Calculate Post-Tax Statutory Deductions
            statutory_components = self._calculate_post_tax_statutory_deductions(
                calculation['gross_pay']
            )
            calculation.update(statutory_components)
            
            # Step 7: Calculate Voluntary Deductions
            voluntary_components = self._calculate_voluntary_deductions(
                employee,
                pay_period_start,
                pay_period_end
            )
            calculation.update(voluntary_components)
            
            # Step 8: Calculate Totals and Net Pay
            final_components = self._calculate_final_totals(calculation)
            calculation.update(final_components)
            
            # Step 9: Add calculation metadata
            calculation['calculation_details'] = self._build_calculation_details(calculation)
            
            logger.info(f"Payroll calculation completed for {employee.get_full_name()}")
            return calculation
            
        except Exception as e:
            logger.error(f"Payroll calculation failed for {employee.get_full_name()}: {str(e)}")
            raise PayEngineError(f"Calculation failed for {employee.get_full_name()}: {str(e)}")
    
    def _calculate_gross_pay(
        self, 
        employee: Employee, 
        period_start: date,
        period_end: date,
        variable_earnings: Dict[str, Decimal]
    ) -> Dict[str, Decimal]:
        """Calculate gross pay including basic salary, allowances, and variable earnings."""
        
        # Basic salary (prorated if needed)
        basic_salary = employee.get_monthly_basic_salary()
        
        # Get fixed allowances
        allowances = employee.allowances.filter(
            is_active=True,
            effective_date__lte=period_end
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=period_start)
        )
        
        house_allowance = Decimal('0')
        transport_allowance = Decimal('0')
        medical_allowance = Decimal('0')
        other_allowances = Decimal('0')
        
        for allowance in allowances:
            if allowance.allowance_type == 'HOUSE':
                house_allowance += allowance.amount
            elif allowance.allowance_type == 'TRANSPORT':
                transport_allowance += allowance.amount
            elif allowance.allowance_type == 'MEDICAL':
                medical_allowance += allowance.amount
            else:
                other_allowances += allowance.amount
        
        # Variable earnings
        overtime_hours = variable_earnings.get('overtime_hours', Decimal('0'))
        overtime_rate = variable_earnings.get('overtime_rate', Decimal('0'))
        overtime_amount = overtime_hours * overtime_rate
        
        bonus_amount = variable_earnings.get('bonus_amount', Decimal('0'))
        commission_amount = variable_earnings.get('commission_amount', Decimal('0'))
        
        # Calculate gross pay
        gross_pay = (
            basic_salary + 
            house_allowance + 
            transport_allowance + 
            medical_allowance + 
            other_allowances + 
            overtime_amount + 
            bonus_amount + 
            commission_amount
        )
        
        return {
            'basic_salary': self._round_amount(basic_salary),
            'house_allowance': self._round_amount(house_allowance),
            'transport_allowance': self._round_amount(transport_allowance),
            'medical_allowance': self._round_amount(medical_allowance),
            'other_allowances': self._round_amount(other_allowances),
            'overtime_hours': overtime_hours,
            'overtime_amount': self._round_amount(overtime_amount),
            'bonus_amount': self._round_amount(bonus_amount),
            'commission_amount': self._round_amount(commission_amount),
            'gross_pay': self._round_amount(gross_pay),
        }
    
    def _calculate_nssf_contributions(self, gross_pay: Decimal) -> Dict[str, Decimal]:
        """Calculate NSSF employee and employer contributions."""
        
        nssf_config = self.compliance_cache['nssf_config']
        employee_rate = Decimal(str(nssf_config['employee_rate'])) / 100
        employer_rate = Decimal(str(nssf_config['employer_rate'])) / 100
        
        # Determine pensionable pay and applicable tier
        pensionable_pay = gross_pay
        employee_contribution = Decimal('0')
        employer_contribution = Decimal('0')
        
        for tier in nssf_config['tiers']:
            min_salary = Decimal(str(tier['min_salary']))
            max_salary = Decimal(str(tier['max_salary'])) if tier['max_salary'] else None
            max_contribution = Decimal(str(tier['max_contribution']))
            
            if pensionable_pay >= min_salary:
                if max_salary is None or pensionable_pay <= max_salary:
                    # Employee falls in this tier
                    contributable_amount = min(pensionable_pay, max_salary) if max_salary else pensionable_pay
                    calculated_contribution = contributable_amount * employee_rate
                    employee_contribution = min(calculated_contribution, max_contribution)
                    employer_contribution = min(calculated_contribution, max_contribution)
                    break
        
        return {
            'nssf_pensionable_pay': self._round_amount(pensionable_pay),
            'nssf_employee': self._round_amount(employee_contribution),
            'nssf_employer': self._round_amount(employer_contribution),
        }
    
    def _calculate_pension_relief(self, employee: Employee, gross_pay: Decimal) -> Decimal:
        """Calculate allowable pension contribution relief."""
        # Get employee's voluntary pension contribution
        pension_contribution = employee.pension_contribution
        
        # Maximum allowable pension relief is 20,000 KES per month or 20% of gross pay
        max_relief_amount = min(Decimal('20000'), gross_pay * Decimal('0.20'))
        
        # Actual relief is the lesser of contribution and maximum allowable
        pension_relief = min(pension_contribution, max_relief_amount)
        
        return self._round_amount(pension_relief)
    
    def _calculate_paye_tax(self, employee: Employee, taxable_income: Decimal) -> Dict[str, Decimal]:
        """Calculate PAYE tax using progressive tax bands and reliefs."""
        
        if taxable_income <= 0:
            return {
                'gross_tax': Decimal('0'),
                'personal_relief': Decimal('0'),
                'insurance_relief': Decimal('0'),
                'mortgage_relief': Decimal('0'),
                'disability_relief': Decimal('0'),
                'paye_tax': Decimal('0'),
            }
        
        # Calculate gross tax using progressive bands
        gross_tax = self._calculate_progressive_tax(taxable_income)
        
        # Apply reliefs
        personal_relief = self.compliance_cache['personal_relief']
        
        # Insurance relief (max 5,000 KES per month)
        insurance_relief = min(employee.insurance_relief_amount, Decimal('5000'))
        
        # Mortgage interest relief (max 25,000 KES per month)
        mortgage_relief = min(employee.mortgage_interest, Decimal('25000'))
        
        # Disability exemption (150% of personal relief)
        disability_relief = Decimal('0')
        if employee.has_disability_exemption:
            disability_relief = personal_relief * Decimal('1.5')
        
        # Calculate total reliefs
        total_reliefs = (
            personal_relief + 
            insurance_relief + 
            mortgage_relief + 
            disability_relief
        )
        
        # Final PAYE tax (cannot be negative)
        paye_tax = max(gross_tax - total_reliefs, Decimal('0'))
        
        return {
            'gross_tax': self._round_amount(gross_tax),
            'personal_relief': self._round_amount(personal_relief),
            'insurance_relief': self._round_amount(insurance_relief),
            'mortgage_relief': self._round_amount(mortgage_relief),
            'disability_relief': self._round_amount(disability_relief),
            'paye_tax': self._round_amount(paye_tax),
        }
    
    def _calculate_progressive_tax(self, taxable_income: Decimal) -> Decimal:
        """Calculate tax using progressive tax bands."""
        
        tax_bands = self.compliance_cache['paye_bands']
        total_tax = Decimal('0')
        remaining_income = taxable_income
        
        for band in tax_bands:
            min_amount = Decimal(str(band['min_amount']))
            max_amount = Decimal(str(band['max_amount'])) if band['max_amount'] else None
            rate = Decimal(str(band['rate'])) / 100
            
            if remaining_income <= 0:
                break
            
            # Calculate taxable amount in this band
            if max_amount is None:
                # Highest band with no upper limit
                taxable_in_band = remaining_income
            else:
                band_width = max_amount - min_amount + Decimal('0.01')
                taxable_in_band = min(remaining_income, band_width)
            
            # Calculate tax for this band
            tax_in_band = taxable_in_band * rate
            total_tax += tax_in_band
            
            # Reduce remaining income
            remaining_income -= taxable_in_band
        
        return total_tax
    
    def _calculate_post_tax_statutory_deductions(self, gross_pay: Decimal) -> Dict[str, Decimal]:
        """Calculate SHIF and AHL deductions (post-tax)."""
        
        shif_rate = self.compliance_cache['shif_rate'] / 100
        ahl_rate = self.compliance_cache['ahl_rate'] / 100
        
        # SHIF deduction (2.75% of gross pay)
        shif_deduction = gross_pay * shif_rate
        
        # AHL deduction (1.5% of gross pay)
        ahl_deduction = gross_pay * ahl_rate
        
        return {
            'shif_deduction': self._round_amount(shif_deduction),
            'ahl_deduction': self._round_amount(ahl_deduction),
        }
    
    def _calculate_voluntary_deductions(
        self, 
        employee: Employee, 
        period_start: date,
        period_end: date
    ) -> Dict[str, Decimal]:
        """Calculate all voluntary deductions for the employee."""
        
        # Get active deductions for the period
        deductions = employee.deductions.filter(
            is_active=True,
            start_date__lte=period_end
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=period_start)
        )
        
        sacco_deduction = Decimal('0')
        loan_deductions = Decimal('0')
        advance_deductions = Decimal('0')
        welfare_deductions = Decimal('0')
        other_deductions = Decimal('0')
        
        for deduction in deductions:
            amount = deduction.amount
            
            if deduction.deduction_type == 'SACCO':
                sacco_deduction += amount
            elif deduction.deduction_type in ['LOAN', 'HELB']:
                loan_deductions += amount
            elif deduction.deduction_type == 'ADVANCE':
                advance_deductions += amount
            elif deduction.deduction_type == 'WELFARE':
                welfare_deductions += amount
            else:
                other_deductions += amount
        
        return {
            'sacco_deduction': self._round_amount(sacco_deduction),
            'loan_deductions': self._round_amount(loan_deductions),
            'advance_deductions': self._round_amount(advance_deductions),
            'welfare_deductions': self._round_amount(welfare_deductions),
            'other_deductions': self._round_amount(other_deductions),
        }
    
    def _calculate_final_totals(self, calculation: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Calculate final totals and net pay."""
        
        # Total statutory deductions
        total_statutory_deductions = (
            calculation['paye_tax'] +
            calculation['nssf_employee'] +
            calculation['shif_deduction'] +
            calculation['ahl_deduction']
        )
        
        # Total voluntary deductions
        total_voluntary_deductions = (
            calculation['sacco_deduction'] +
            calculation['loan_deductions'] +
            calculation['advance_deductions'] +
            calculation['welfare_deductions'] +
            calculation['other_deductions']
        )
        
        # Total all deductions
        total_deductions = total_statutory_deductions + total_voluntary_deductions
        
        # Net pay
        net_pay = calculation['gross_pay'] - total_deductions
        
        return {
            'total_statutory_deductions': self._round_amount(total_statutory_deductions),
            'total_voluntary_deductions': self._round_amount(total_voluntary_deductions),
            'total_deductions': self._round_amount(total_deductions),
            'net_pay': self._round_amount(net_pay),
        }
    
    def _build_calculation_details(self, calculation: Dict[str, Decimal]) -> Dict:
        """Build detailed calculation breakdown for audit purposes."""
        
        return {
            'compliance_settings_used': {
                'paye_bands': self.compliance_cache['paye_bands'],
                'personal_relief': str(self.compliance_cache['personal_relief']),
                'nssf_config': self.compliance_cache['nssf_config'],
                'shif_rate': str(self.compliance_cache['shif_rate']),
                'ahl_rate': str(self.compliance_cache['ahl_rate']),
            },
            'calculation_sequence': [
                'gross_pay_calculation',
                'nssf_calculation',
                'pension_relief_calculation',
                'taxable_income_calculation',
                'paye_tax_calculation',
                'post_tax_statutory_deductions',
                'voluntary_deductions',
                'final_totals'
            ],
            'engine_version': '1.0.0',
            'calculation_timestamp': self.calculation_date.isoformat(),
        }
    
    def _round_amount(self, amount: Decimal) -> Decimal:
        """Round amount to 2 decimal places using banker's rounding."""
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def validate_calculation(self, calculation: Dict[str, Decimal]) -> List[str]:
        """Validate that a calculation is mathematically correct."""
        
        errors = []
        tolerance = Decimal('0.01')
        
        # Validate gross pay calculation
        calculated_gross = (
            calculation['basic_salary'] +
            calculation['house_allowance'] +
            calculation['transport_allowance'] +
            calculation['medical_allowance'] +
            calculation['other_allowances'] +
            calculation['overtime_amount'] +
            calculation['bonus_amount'] +
            calculation['commission_amount']
        )
        
        if abs(calculated_gross - calculation['gross_pay']) > tolerance:
            errors.append(f"Gross pay validation failed: {calculated_gross} != {calculation['gross_pay']}")
        
        # Validate taxable income
        calculated_taxable = (
            calculation['gross_pay'] -
            calculation['nssf_employee'] -
            calculation['pension_relief']
        )
        
        if abs(calculated_taxable - calculation['taxable_income']) > tolerance:
            errors.append(f"Taxable income validation failed: {calculated_taxable} != {calculation['taxable_income']}")
        
        # Validate total deductions
        calculated_total_deductions = (
            calculation['total_statutory_deductions'] +
            calculation['total_voluntary_deductions']
        )
        
        if abs(calculated_total_deductions - calculation['total_deductions']) > tolerance:
            errors.append(f"Total deductions validation failed: {calculated_total_deductions} != {calculation['total_deductions']}")
        
        # Validate net pay
        calculated_net = calculation['gross_pay'] - calculation['total_deductions']
        
        if abs(calculated_net - calculation['net_pay']) > tolerance:
            errors.append(f"Net pay validation failed: {calculated_net} != {calculation['net_pay']}")
        
        return errors
    
    def calculate_batch_payroll(
        self, 
        employees: List[Employee],
        pay_period_start: date,
        pay_period_end: date,
        variable_earnings_data: Dict[str, Dict[str, Decimal]] = None
    ) -> List[Dict[str, Decimal]]:
        """
        Calculate payroll for a batch of employees.
        
        Args:
            employees: List of Employee instances
            pay_period_start: Start date of pay period
            pay_period_end: End date of pay period
            variable_earnings_data: Dict mapping employee IDs to their variable earnings
        
        Returns:
            List of calculation results for each employee
        """
        
        if variable_earnings_data is None:
            variable_earnings_data = {}
        
        results = []
        errors = []
        
        for employee in employees:
            try:
                variable_earnings = variable_earnings_data.get(str(employee.id), {})
                
                calculation = self.calculate_employee_payroll(
                    employee,
                    pay_period_start,
                    pay_period_end,
                    variable_earnings
                )
                
                # Validate calculation
                validation_errors = self.validate_calculation(calculation)
                if validation_errors:
                    logger.warning(f"Validation errors for {employee.get_full_name()}: {validation_errors}")
                    calculation['validation_errors'] = validation_errors
                
                results.append(calculation)
                
            except Exception as e:
                error_msg = f"Failed to calculate payroll for {employee.get_full_name()}: {str(e)}"
                logger.error(error_msg)
                errors.append({
                    'employee_id': str(employee.id),
                    'employee_name': employee.get_full_name(),
                    'error': error_msg
                })
        
        if errors:
            logger.error(f"Batch calculation completed with {len(errors)} errors")
        
        return results, errors