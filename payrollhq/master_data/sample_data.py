"""
Sample Kenyan Compliance Data for PayrollHQ

This file contains the current (2024) Kenyan statutory rates and bands
for PAYE, NSSF, SHIF, and AHL. This data should be loaded into the
ComplianceSetting model for accurate payroll calculations.
"""

from decimal import Decimal
from datetime import date

# Current Kenyan PAYE Tax Bands (2024)
PAYE_TAX_BANDS_2024 = {
    "compliance_type": "PAYE_TAX_BANDS",
    "effective_date": date(2024, 1, 1),
    "compliance_data": {
        "tax_bands": [
            {
                "min_amount": "0.00",
                "max_amount": "24000.00",
                "rate": "10.00",
                "description": "First KES 24,000 - 10%"
            },
            {
                "min_amount": "24000.01",
                "max_amount": "32333.00",
                "rate": "25.00",
                "description": "Next KES 8,333 (24,001 to 32,333) - 25%"
            },
            {
                "min_amount": "32333.01",
                "max_amount": "500000.00",
                "rate": "30.00",
                "description": "Next KES 467,667 (32,334 to 500,000) - 30%"
            },
            {
                "min_amount": "500000.01",
                "max_amount": "800000.00",
                "rate": "32.50",
                "description": "Next KES 300,000 (500,001 to 800,000) - 32.5%"
            },
            {
                "min_amount": "800000.01",
                "max_amount": None,
                "rate": "35.00",
                "description": "Above KES 800,000 - 35%"
            }
        ]
    }
}

# Personal Relief (2024)
PERSONAL_RELIEF_2024 = {
    "compliance_type": "PERSONAL_RELIEF",
    "effective_date": date(2024, 1, 1),
    "compliance_data": {
        "monthly_amount": "2400.00",
        "annual_amount": "28800.00",
        "description": "Personal relief of KES 2,400 per month"
    }
}

# NSSF Rates and Tiers (2024)
NSSF_RATES_2024 = {
    "compliance_type": "NSSF_RATES",
    "effective_date": date(2024, 1, 1),
    "compliance_data": {
        "employee_rate": "6.00",
        "employer_rate": "6.00",
        "total_rate": "12.00",
        "tiers": [
            {
                "tier_name": "Tier I",
                "min_salary": "0.00",
                "max_salary": "7000.00",
                "max_contribution": "420.00",
                "description": "6% of pensionable pay up to KES 7,000 (max KES 420)"
            },
            {
                "tier_name": "Tier II",
                "min_salary": "7001.00",
                "max_salary": "36000.00",
                "max_contribution": "2160.00",
                "description": "6% of pensionable pay from KES 7,001 to KES 36,000 (max KES 2,160)"
            }
        ],
        "notes": "NSSF contribution is deducted from gross pay before calculating PAYE"
    }
}

# SHIF (Social Health Insurance Fund) Rates (2024)
SHIF_RATES_2024 = {
    "compliance_type": "SHIF_RATES",
    "effective_date": date(2024, 1, 1),
    "compliance_data": {
        "rate_percentage": "2.75",
        "description": "SHIF contribution at 2.75% of gross salary",
        "minimum_contribution": "0.00",
        "maximum_contribution": None,
        "notes": "SHIF is deducted post-tax from gross salary"
    }
}

# AHL (Affordable Housing Levy) Rates (2024)
AHL_RATES_2024 = {
    "compliance_type": "AHL_RATES",
    "effective_date": date(2024, 1, 1),
    "compliance_data": {
        "rate_percentage": "1.50",
        "description": "Affordable Housing Levy at 1.5% of gross salary",
        "minimum_contribution": "0.00",
        "maximum_contribution": None,
        "notes": "AHL is deducted post-tax from gross salary"
    }
}

# Insurance Relief Limits (2024)
INSURANCE_RELIEF_2024 = {
    "compliance_type": "INSURANCE_RELIEF",
    "effective_date": date(2024, 1, 1),
    "compliance_data": {
        "monthly_limit": "5000.00",
        "annual_limit": "60000.00",
        "description": "Insurance relief up to KES 5,000 per month",
        "qualifying_premiums": [
            "Life insurance premiums",
            "Education insurance premiums",
            "Medical insurance premiums"
        ]
    }
}

# Pension Relief Limits (2024)
PENSION_RELIEF_2024 = {
    "compliance_type": "PENSION_RELIEF",
    "effective_date": date(2024, 1, 1),
    "compliance_data": {
        "monthly_limit": "20000.00",
        "annual_limit": "240000.00",
        "percentage_limit": "20.00",
        "description": "Pension relief up to 20% of gross pay or KES 20,000 per month, whichever is lower",
        "qualifying_contributions": [
            "Registered pension scheme contributions",
            "Individual retirement benefits scheme contributions",
            "Provident fund contributions"
        ]
    }
}

# Mortgage Interest Relief (2024)
MORTGAGE_RELIEF_2024 = {
    "compliance_type": "MORTGAGE_RELIEF",
    "effective_date": date(2024, 1, 1),
    "compliance_data": {
        "monthly_limit": "25000.00",
        "annual_limit": "300000.00",
        "description": "Mortgage interest relief up to KES 25,000 per month",
        "conditions": [
            "Must be for owner-occupied residential house",
            "Only interest portion qualifies",
            "House must be in Kenya"
        ]
    }
}

# Disability Exemption (2024)
DISABILITY_EXEMPTION_2024 = {
    "compliance_type": "DISABILITY_EXEMPTION",
    "effective_date": date(2024, 1, 1),
    "compliance_data": {
        "exemption_amount": "3600.00",
        "calculation_method": "150% of personal relief",
        "description": "Additional relief of KES 3,600 per month for persons with disability",
        "eligibility": [
            "Must have valid certificate of disability",
            "Applies to both employee and employer of disabled person"
        ]
    }
}

# Compile all compliance settings
KENYAN_COMPLIANCE_SETTINGS_2024 = [
    PAYE_TAX_BANDS_2024,
    PERSONAL_RELIEF_2024,
    NSSF_RATES_2024,
    SHIF_RATES_2024,
    AHL_RATES_2024,
    INSURANCE_RELIEF_2024,
    PENSION_RELIEF_2024,
    MORTGAGE_RELIEF_2024,
    DISABILITY_EXEMPTION_2024,
]

def create_compliance_settings():
    """
    Create compliance settings in the database.
    This function should be called during initial setup or data migration.
    """
    from master_data.models import ComplianceSetting
    
    created_settings = []
    
    for setting_data in KENYAN_COMPLIANCE_SETTINGS_2024:
        compliance_setting, created = ComplianceSetting.objects.get_or_create(
            compliance_type=setting_data["compliance_type"],
            effective_date=setting_data["effective_date"],
            defaults={
                'compliance_data': setting_data["compliance_data"],
                'is_active': True,
                'created_by': 'system',
                'notes': f'Initial {setting_data["compliance_type"]} settings for 2024'
            }
        )
        
        if created:
            created_settings.append(compliance_setting)
            print(f"Created: {compliance_setting}")
        else:
            print(f"Already exists: {compliance_setting}")
    
    return created_settings

# Sample Payroll Constants
PAYROLL_CONSTANTS = {
    "MINIMUM_WAGE": {
        "constant_type": "MINIMUM_WAGE",
        "constant_value": {
            "monthly_amount": "15000.00",
            "daily_amount": "500.00",
            "hourly_amount": "62.50",
            "description": "Minimum wage rates as per Kenya labor laws"
        }
    },
    "WORKING_DAYS": {
        "constant_type": "WORKING_DAYS",
        "constant_value": {
            "days_per_month": 22,
            "hours_per_day": 8,
            "hours_per_week": 40,
            "description": "Standard working days and hours"
        }
    },
    "CURRENCY": {
        "constant_type": "CURRENCY",
        "constant_value": {
            "code": "KES",
            "symbol": "KSh",
            "name": "Kenyan Shilling",
            "decimal_places": 2
        }
    },
    "ROUNDING": {
        "constant_type": "ROUNDING",
        "constant_value": {
            "decimal_places": 2,
            "rounding_method": "ROUND_HALF_UP",
            "description": "Standard rounding rules for payroll calculations"
        }
    },
    "OVERTIME": {
        "constant_type": "OVERTIME",
        "constant_value": {
            "normal_rate_multiplier": "1.00",
            "overtime_rate_multiplier": "1.50",
            "weekend_rate_multiplier": "2.00",
            "holiday_rate_multiplier": "2.00",
            "threshold_hours_per_day": 8,
            "threshold_hours_per_week": 40
        }
    }
}

def create_payroll_constants():
    """Create payroll constants in the database."""
    from master_data.models import PayrollConstants
    
    created_constants = []
    
    for constant_key, constant_data in PAYROLL_CONSTANTS.items():
        constant, created = PayrollConstants.objects.get_or_create(
            constant_type=constant_data["constant_type"],
            defaults={
                'constant_value': constant_data["constant_value"],
                'is_active': True
            }
        )
        
        if created:
            created_constants.append(constant)
            print(f"Created: {constant}")
        else:
            print(f"Already exists: {constant}")
    
    return created_constants