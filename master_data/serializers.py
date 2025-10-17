"""
Serializers for Master Data models in PayrollHQ

This module contains DRF serializers for compliance settings and payroll constants.
The serializers handle validation, data transformation, and API representation
of the complex compliance data structures.
"""

from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from .models import ComplianceSetting, PayrollConstants, ComplianceAuditLog


class ComplianceSettingSerializer(serializers.ModelSerializer):
    """
    Serializer for ComplianceSetting model with comprehensive validation.
    
    This serializer handles the complex JSON structures for different compliance types
    and provides validation for Kenyan statutory requirements.
    """
    
    is_current = serializers.ReadOnlyField()
    compliance_type_display = serializers.CharField(
        source='get_compliance_type_display', 
        read_only=True
    )
    
    class Meta:
        model = ComplianceSetting
        fields = [
            'id', 'compliance_type', 'compliance_type_display', 'effective_date',
            'end_date', 'compliance_data', 'is_active', 'created_by',
            'created_at', 'updated_at', 'approved_by', 'approved_at',
            'notes', 'is_current'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_current']
    
    def validate_effective_date(self, value):
        """Validate that effective_date is not in the past for new records."""
        if not self.instance and value < timezone.now().date():
            raise serializers.ValidationError(
                "Effective date cannot be in the past for new compliance settings."
            )
        return value
    
    def validate_end_date(self, value):
        """Validate that end_date is after effective_date."""
        if value and self.initial_data.get('effective_date'):
            effective_date = self.initial_data['effective_date']
            if isinstance(effective_date, str):
                effective_date = timezone.datetime.strptime(effective_date, '%Y-%m-%d').date()
            
            if value <= effective_date:
                raise serializers.ValidationError(
                    "End date must be after the effective date."
                )
        return value
    
    def validate_compliance_data(self, value):
        """
        Validate compliance_data structure based on compliance_type.
        """
        compliance_type = self.initial_data.get('compliance_type')
        
        if compliance_type == 'PAYE_TAX_BANDS':
            return self._validate_paye_tax_bands(value)
        elif compliance_type == 'PERSONAL_RELIEF':
            return self._validate_personal_relief(value)
        elif compliance_type == 'NSSF_RATES':
            return self._validate_nssf_rates(value)
        elif compliance_type in ['SHIF_RATES', 'AHL_RATES']:
            return self._validate_percentage_rates(value, compliance_type)
        elif compliance_type == 'INSURANCE_RELIEF':
            return self._validate_relief_limits(value, compliance_type)
        
        return value
    
    def _validate_paye_tax_bands(self, data):
        """Validate PAYE tax bands structure and values."""
        if 'tax_bands' not in data:
            raise serializers.ValidationError(
                "PAYE tax bands must contain 'tax_bands' array."
            )
        
        tax_bands = data['tax_bands']
        if not isinstance(tax_bands, list) or not tax_bands:
            raise serializers.ValidationError(
                "Tax bands must be a non-empty array."
            )
        
        # Validate each tax band
        for i, band in enumerate(tax_bands):
            self._validate_tax_band(band, i)
        
        # Validate band progression (no gaps or overlaps)
        self._validate_band_progression(tax_bands)
        
        return data
    
    def _validate_tax_band(self, band, index):
        """Validate individual tax band structure."""
        required_fields = ['min_amount', 'max_amount', 'rate']
        
        for field in required_fields:
            if field not in band:
                raise serializers.ValidationError(
                    f"Tax band {index + 1} missing required field: {field}"
                )
        
        # Validate numeric values
        try:
            min_amount = Decimal(str(band['min_amount']))
            max_amount = Decimal(str(band['max_amount'])) if band['max_amount'] is not None else None
            rate = Decimal(str(band['rate']))
            
            if min_amount < 0:
                raise serializers.ValidationError(
                    f"Tax band {index + 1}: min_amount cannot be negative"
                )
            
            if max_amount is not None and max_amount <= min_amount:
                raise serializers.ValidationError(
                    f"Tax band {index + 1}: max_amount must be greater than min_amount"
                )
            
            if not (0 <= rate <= 100):
                raise serializers.ValidationError(
                    f"Tax band {index + 1}: rate must be between 0 and 100 percent"
                )
                
        except (ValueError, InvalidOperation):
            raise serializers.ValidationError(
                f"Tax band {index + 1}: Invalid numeric values"
            )
    
    def _validate_band_progression(self, bands):
        """Validate that tax bands have no gaps or overlaps."""
        sorted_bands = sorted(bands, key=lambda x: Decimal(str(x['min_amount'])))
        
        for i in range(len(sorted_bands) - 1):
            current_max = sorted_bands[i]['max_amount']
            next_min = Decimal(str(sorted_bands[i + 1]['min_amount']))
            
            if current_max is not None:
                current_max = Decimal(str(current_max))
                if current_max + Decimal('0.01') != next_min:
                    raise serializers.ValidationError(
                        f"Tax bands have gaps or overlaps between bands {i + 1} and {i + 2}"
                    )
    
    def _validate_personal_relief(self, data):
        """Validate personal relief structure."""
        if 'monthly_amount' not in data:
            raise serializers.ValidationError(
                "Personal relief must contain 'monthly_amount'"
            )
        
        try:
            amount = Decimal(str(data['monthly_amount']))
            if amount < 0:
                raise serializers.ValidationError(
                    "Personal relief amount cannot be negative"
                )
            
            # Kenya specific validation - personal relief should be reasonable
            if amount > Decimal('10000'):  # KES 10,000 seems unreasonably high
                raise serializers.ValidationError(
                    "Personal relief amount seems unreasonably high"
                )
                
        except (ValueError, InvalidOperation):
            raise serializers.ValidationError(
                "Personal relief amount must be a valid number"
            )
        
        return data
    
    def _validate_nssf_rates(self, data):
        """Validate NSSF rates structure."""
        required_fields = ['employee_rate', 'employer_rate', 'tiers']
        
        for field in required_fields:
            if field not in data:
                raise serializers.ValidationError(
                    f"NSSF rates must contain '{field}'"
                )
        
        # Validate rate percentages
        try:
            emp_rate = Decimal(str(data['employee_rate']))
            empr_rate = Decimal(str(data['employer_rate']))
            
            if not (0 <= emp_rate <= 100):
                raise serializers.ValidationError(
                    "Employee rate must be between 0 and 100 percent"
                )
            
            if not (0 <= empr_rate <= 100):
                raise serializers.ValidationError(
                    "Employer rate must be between 0 and 100 percent"
                )
                
        except (ValueError, InvalidOperation):
            raise serializers.ValidationError(
                "NSSF rates must be valid numbers"
            )
        
        # Validate tiers structure
        tiers = data['tiers']
        if not isinstance(tiers, list) or not tiers:
            raise serializers.ValidationError(
                "NSSF tiers must be a non-empty array"
            )
        
        for i, tier in enumerate(tiers):
            self._validate_nssf_tier(tier, i)
        
        return data
    
    def _validate_nssf_tier(self, tier, index):
        """Validate individual NSSF tier."""
        required_fields = ['min_salary', 'max_salary', 'max_contribution']
        
        for field in required_fields:
            if field not in tier:
                raise serializers.ValidationError(
                    f"NSSF tier {index + 1} missing required field: {field}"
                )
        
        try:
            min_sal = Decimal(str(tier['min_salary']))
            max_sal = Decimal(str(tier['max_salary'])) if tier['max_salary'] is not None else None
            max_contrib = Decimal(str(tier['max_contribution']))
            
            if min_sal < 0:
                raise serializers.ValidationError(
                    f"NSSF tier {index + 1}: min_salary cannot be negative"
                )
            
            if max_sal is not None and max_sal <= min_sal:
                raise serializers.ValidationError(
                    f"NSSF tier {index + 1}: max_salary must be greater than min_salary"
                )
            
            if max_contrib < 0:
                raise serializers.ValidationError(
                    f"NSSF tier {index + 1}: max_contribution cannot be negative"
                )
                
        except (ValueError, InvalidOperation):
            raise serializers.ValidationError(
                f"NSSF tier {index + 1}: Invalid numeric values"
            )
    
    def _validate_percentage_rates(self, data, compliance_type):
        """Validate percentage-based rates (SHIF, AHL)."""
        if 'rate_percentage' not in data:
            raise serializers.ValidationError(
                f"{compliance_type} must contain 'rate_percentage'"
            )
        
        try:
            rate = Decimal(str(data['rate_percentage']))
            if not (0 <= rate <= 100):
                raise serializers.ValidationError(
                    f"{compliance_type} rate must be between 0 and 100 percent"
                )
                
            # Kenya specific validations
            if compliance_type == 'SHIF_RATES' and rate > Decimal('5'):
                raise serializers.ValidationError(
                    "SHIF rate seems unreasonably high (>5%)"
                )
            
            if compliance_type == 'AHL_RATES' and rate > Decimal('3'):
                raise serializers.ValidationError(
                    "AHL rate seems unreasonably high (>3%)"
                )
                
        except (ValueError, InvalidOperation):
            raise serializers.ValidationError(
                f"{compliance_type} rate must be a valid number"
            )
        
        return data
    
    def _validate_relief_limits(self, data, compliance_type):
        """Validate relief limit structures."""
        if 'monthly_limit' not in data:
            raise serializers.ValidationError(
                f"{compliance_type} must contain 'monthly_limit'"
            )
        
        try:
            limit = Decimal(str(data['monthly_limit']))
            if limit < 0:
                raise serializers.ValidationError(
                    f"{compliance_type} monthly limit cannot be negative"
                )
                
        except (ValueError, InvalidOperation):
            raise serializers.ValidationError(
                f"{compliance_type} monthly limit must be a valid number"
            )
        
        return data
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Check for duplicate active settings of the same type for overlapping periods
        compliance_type = attrs.get('compliance_type')
        effective_date = attrs.get('effective_date')
        end_date = attrs.get('end_date')
        is_active = attrs.get('is_active', True)
        
        if is_active and compliance_type and effective_date:
            # Build query to check for overlapping periods
            overlapping_query = ComplianceSetting.objects.filter(
                compliance_type=compliance_type,
                is_active=True,
                effective_date__lte=end_date or '9999-12-31'
            )
            
            if end_date:
                overlapping_query = overlapping_query.filter(
                    models.Q(end_date__isnull=True) | 
                    models.Q(end_date__gte=effective_date)
                )
            else:
                overlapping_query = overlapping_query.filter(
                    models.Q(end_date__isnull=True) | 
                    models.Q(end_date__gte=effective_date)
                )
            
            # Exclude current instance if updating
            if self.instance:
                overlapping_query = overlapping_query.exclude(pk=self.instance.pk)
            
            if overlapping_query.exists():
                raise serializers.ValidationError(
                    f"An active {compliance_type} setting already exists for the specified date range."
                )
        
        return attrs


class PayrollConstantsSerializer(serializers.ModelSerializer):
    """Serializer for PayrollConstants model."""
    
    constant_type_display = serializers.CharField(
        source='get_constant_type_display',
        read_only=True
    )
    
    class Meta:
        model = PayrollConstants
        fields = [
            'id', 'constant_type', 'constant_type_display', 'constant_value',
            'effective_date', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_constant_value(self, value):
        """Validate constant_value based on constant_type."""
        constant_type = self.initial_data.get('constant_type')
        
        if constant_type == 'MINIMUM_WAGE':
            return self._validate_minimum_wage(value)
        elif constant_type == 'WORKING_DAYS':
            return self._validate_working_days(value)
        elif constant_type == 'CURRENCY':
            return self._validate_currency(value)
        elif constant_type == 'ROUNDING':
            return self._validate_rounding(value)
        
        return value
    
    def _validate_minimum_wage(self, data):
        """Validate minimum wage structure."""
        if 'monthly_amount' not in data:
            raise serializers.ValidationError(
                "Minimum wage must contain 'monthly_amount'"
            )
        
        try:
            amount = Decimal(str(data['monthly_amount']))
            if amount <= 0:
                raise serializers.ValidationError(
                    "Minimum wage must be positive"
                )
        except (ValueError, InvalidOperation):
            raise serializers.ValidationError(
                "Minimum wage amount must be a valid number"
            )
        
        return data
    
    def _validate_working_days(self, data):
        """Validate working days configuration."""
        required_fields = ['days_per_month', 'hours_per_day']
        
        for field in required_fields:
            if field not in data:
                raise serializers.ValidationError(
                    f"Working days config must contain '{field}'"
                )
        
        try:
            days = int(data['days_per_month'])
            hours = Decimal(str(data['hours_per_day']))
            
            if not (1 <= days <= 31):
                raise serializers.ValidationError(
                    "Days per month must be between 1 and 31"
                )
            
            if not (1 <= hours <= 24):
                raise serializers.ValidationError(
                    "Hours per day must be between 1 and 24"
                )
                
        except (ValueError, InvalidOperation):
            raise serializers.ValidationError(
                "Working days values must be valid numbers"
            )
        
        return data
    
    def _validate_currency(self, data):
        """Validate currency configuration."""
        if 'code' not in data:
            raise serializers.ValidationError(
                "Currency config must contain 'code'"
            )
        
        if data['code'] != 'KES':
            raise serializers.ValidationError(
                "Only KES currency is supported"
            )
        
        return data
    
    def _validate_rounding(self, data):
        """Validate rounding rules."""
        if 'decimal_places' not in data:
            raise serializers.ValidationError(
                "Rounding config must contain 'decimal_places'"
            )
        
        try:
            places = int(data['decimal_places'])
            if not (0 <= places <= 4):
                raise serializers.ValidationError(
                    "Decimal places must be between 0 and 4"
                )
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                "Decimal places must be a valid integer"
            )
        
        return data


class ComplianceAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for ComplianceAuditLog model."""
    
    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    
    compliance_setting_display = serializers.CharField(
        source='compliance_setting.__str__',
        read_only=True
    )
    
    class Meta:
        model = ComplianceAuditLog
        fields = [
            'id', 'compliance_setting', 'compliance_setting_display',
            'action', 'action_display', 'old_data', 'new_data',
            'changed_by', 'changed_at', 'ip_address', 'user_agent', 'reason'
        ]
        read_only_fields = ['changed_at']


class ComplianceSettingListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing compliance settings."""
    
    compliance_type_display = serializers.CharField(
        source='get_compliance_type_display',
        read_only=True
    )
    is_current = serializers.ReadOnlyField()
    
    class Meta:
        model = ComplianceSetting
        fields = [
            'id', 'compliance_type', 'compliance_type_display',
            'effective_date', 'end_date', 'is_active', 'is_current',
            'created_by', 'approved_by', 'approved_at'
        ]


class ComplianceSettingDetailSerializer(ComplianceSettingSerializer):
    """Detailed serializer with audit logs for compliance settings."""
    
    audit_logs = ComplianceAuditLogSerializer(many=True, read_only=True)
    
    class Meta(ComplianceSettingSerializer.Meta):
        fields = ComplianceSettingSerializer.Meta.fields + ['audit_logs']