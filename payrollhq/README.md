# PayrollHQ - Kenyan Payroll Management SaaS

PayrollHQ is a comprehensive, secure, and scalable Software-as-a-Service (SaaS) platform designed specifically for calculating and managing Kenyan statutory payroll compliance. The system strictly adheres to current Kenyan tax and labor laws, including PAYE, NSSF, SHIF, and AHL calculations.

## 🏗️ System Architecture

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python 3.10+ with Django & Django REST Framework | API development, complex calculation logic, and security management |
| **Database** | PostgreSQL | Robust, reliable data storage for financial transactions and multi-tenancy |
| **Frontend** | React 18+ with TypeScript & Tailwind CSS | Dynamic user interface, responsiveness, and professional SaaS aesthetic |

### Core Features

- ✅ **Multi-tenant SaaS Architecture** - Complete data isolation per organization
- ✅ **Kenyan Tax Compliance** - PAYE, NSSF, SHIF, AHL calculations per current laws
- ✅ **Comprehensive PayEngine** - Sequential calculation logic following Kenyan requirements
- ✅ **Mandatory ID Validation** - Enforces KRA PIN, NSSF, and SHA numbers
- ✅ **Immutable Payroll Records** - Data integrity with locked payroll batches
- ✅ **Audit Trail** - Complete compliance setting change tracking
- ✅ **RESTful API** - Full API coverage for all operations

## 📁 Project Structure

```
payrollhq/
├── payrollhq/                 # Main Django project
│   ├── settings.py           # Configuration with multi-tenancy
│   ├── urls.py              # Main URL routing
│   └── ...
├── organizations/           # Multi-tenant organization management
│   ├── models.py           # Organization, User, Settings models
│   └── ...
├── employees/              # Employee management with Kenyan compliance
│   ├── models.py          # Employee model with mandatory IDs
│   └── ...
├── master_data/           # Compliance settings and statutory rates
│   ├── models.py         # ComplianceSetting model
│   ├── serializers.py    # DRF serializers with validation
│   ├── views.py          # API endpoints
│   ├── sample_data.py    # Current Kenyan rates (2024)
│   └── ...
├── calculations/          # PayEngine calculation logic
│   ├── pay_engine.py     # Main PayEngine class
│   └── ...
├── payrun/               # Payroll batch processing
│   ├── models.py        # PayrollBatch, PayslipRecord models
│   ├── views.py         # /api/payrun/calculate_batch/ endpoint
│   └── ...
├── earnings/            # Variable earnings (overtime, bonuses)
├── deductions/          # Voluntary deductions
├── reporting/           # Compliance reports (P10, NSSF returns)
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Node.js 18+ (for frontend)

### Backend Setup

1. **Clone and setup virtual environment:**
```bash
cd payrollhq
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
copy .env.example .env
# Edit .env with your database credentials
```

4. **Setup database:**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Load Kenyan compliance data:**
```bash
python manage.py shell
>>> from master_data.sample_data import create_compliance_settings, create_payroll_constants
>>> create_compliance_settings()
>>> create_payroll_constants()
>>> exit()
```

6. **Create superuser:**
```bash
python manage.py createsuperuser
```

7. **Run development server:**
```bash
python manage.py runserver
```

### API Endpoints

#### Core PayrollHQ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/payrun/batches/calculate_batch/` | POST | **Main payroll calculation endpoint** |
| `/api/master-data/compliance-settings/` | GET/POST | Manage compliance settings |
| `/api/master-data/compliance-settings/current_settings/` | GET | Get all current active settings |
| `/api/employees/` | GET/POST | Employee management |
| `/api/organizations/` | GET/POST | Organization management |

#### Critical Payroll Calculation API

**POST** `/api/payrun/batches/calculate_batch/`

Request payload:
```json
{
  "pay_period_start": "2024-01-01",
  "pay_period_end": "2024-01-31", 
  "pay_date": "2024-02-01",
  "batch_number": "PAY-2024-01",
  "include_all_employees": true,
  "variable_earnings": {
    "employee_uuid": {
      "overtime_hours": "10.5",
      "overtime_rate": "500.00",
      "bonus_amount": "5000.00"
    }
  }
}
```

## 🧮 PayEngine Calculation Logic

The PayEngine follows the **correct Kenyan payroll calculation sequence**:

### Calculation Flow

1. **Calculate Gross Pay**
   - Basic Salary + Allowances + Variable Earnings (Overtime, Bonuses)

2. **Calculate NSSF Employee Contribution**
   - Deducted from gross pay before tax calculation
   - Uses tiered rates (Tier I: 6% up to KES 7,000, Tier II: 6% from KES 7,001 to KES 36,000)

3. **Calculate Allowable Pension Relief**
   - Up to 20% of gross pay or KES 20,000 monthly (whichever is lower)

4. **Calculate Taxable Income**
   - Gross Pay - NSSF Employee - Pension Contributions

5. **Calculate PAYE Tax**
   - Progressive tax bands (10%, 25%, 30%, 32.5%, 35%)
   - Apply Personal Relief (KES 2,400/month)
   - Apply other reliefs (Insurance, Mortgage, Disability)

6. **Calculate Post-Tax Statutory Deductions**
   - SHIF: 2.75% of gross salary
   - AHL: 1.5% of gross salary

7. **Calculate Voluntary Deductions**
   - SACCO, loans, welfare contributions, etc.

8. **Calculate Net Pay**
   - Gross Pay - All Deductions

### Current Kenyan Rates (2024)

#### PAYE Tax Bands
- **KES 0 - 24,000**: 10%
- **KES 24,001 - 32,333**: 25%  
- **KES 32,334 - 500,000**: 30%
- **KES 500,001 - 800,000**: 32.5%
- **Above KES 800,000**: 35%

#### Statutory Contributions
- **Personal Relief**: KES 2,400/month
- **NSSF**: 6% employee + 6% employer (tiered)
- **SHIF**: 2.75% of gross salary
- **AHL**: 1.5% of gross salary

## 🏢 Multi-Tenancy Architecture

PayrollHQ implements **strict multi-tenancy** to ensure complete data isolation:

### Organization-Level Isolation
- Every model includes `organization` foreign key
- All API queries filter by authenticated user's organization
- No cross-tenant data access possible

### User Management
- Each user belongs to exactly one organization
- Role-based permissions (Owner, Admin, HR Manager, Payroll Clerk, Viewer)
- Organization-scoped authentication

### Data Integrity
- PayslipRecord becomes **immutable** when PayrollBatch is locked
- Complete audit trail for all compliance setting changes
- Secure payroll workflow with approval gates

## 📊 Compliance & Reporting

### Kenyan Statutory Requirements

The system supports generation of:

- **KRA P10 Returns** - Monthly PAYE filing
- **NSSF Remittance Schedules** - Monthly NSSF contributions
- **SHIF Remittance Reports** - Monthly health insurance contributions
- **AHL Remittance Reports** - Monthly housing levy contributions

### Mandatory Employee Data

All employees **must** have:
- ✅ **KRA PIN** (Format: A000000000A)
- ✅ **NSSF Number** (Social Security)
- ✅ **SHA Number** (Health Insurance)
- ✅ **National ID** (8 digits)

## 🔒 Security Features

- **Multi-tenant data isolation** - Zero cross-organization data access
- **Role-based access control** - Granular permissions per user role
- **Audit logging** - Complete compliance setting change tracking
- **Immutable payroll records** - Locked batches prevent tampering
- **Token-based authentication** - Secure API access
- **Input validation** - Comprehensive data validation at all levels

## 🧪 Development & Testing

### Running Tests
```bash
python manage.py test
```

### Code Quality
```bash
# Format code
black .

# Check code style
flake8 .

# Sort imports
isort .
```

### API Testing
Use the Django REST Framework browsable API at:
- http://localhost:8000/api/

Or test with curl:
```bash
# Get current compliance settings
curl -H "Authorization: Token your_token" \
     http://localhost:8000/api/master-data/compliance-settings/current_settings/

# Calculate payroll batch
curl -X POST \
     -H "Authorization: Token your_token" \
     -H "Content-Type: application/json" \
     -d @payroll_batch.json \
     http://localhost:8000/api/payrun/batches/calculate_batch/
```

## 📋 Production Deployment

### Environment Setup
1. Set `DEBUG=False` in production
2. Configure proper `SECRET_KEY`
3. Set up PostgreSQL with SSL
4. Configure static file serving (WhiteNoise or CDN)
5. Set up monitoring (Sentry recommended)

### Database Migration
```bash
python manage.py migrate --settings=payrollhq.settings.production
```

### Static Files
```bash
python manage.py collectstatic --noinput
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the coding standards (Black, Flake8)
4. Add comprehensive tests
5. Submit a pull request

## 📄 License

This project is proprietary software for PayrollHQ SaaS platform.

## 📞 Support

For technical support or questions about Kenyan payroll compliance:
- Documentation: [Internal Wiki]
- Issues: [GitHub Issues]
- Email: support@payrollhq.com

---

**PayrollHQ** - *Simplifying Kenyan Payroll Compliance*