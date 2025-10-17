# PayrollHQ - Kenyan Payroll Management System

A comprehensive SaaS payroll management platform designed specifically for Kenyan businesses, featuring full compliance with Kenyan tax laws and statutory requirements.

## 🏗️ Architecture

### Backend (Django + DRF)
- **Django 4.2+** with REST Framework
- **PostgreSQL** database with multi-tenant architecture
- **Kenyan Compliance Engine** with PAYE, NSSF, SHIF, and AHL calculations
- **Modular Design** with 8 specialized Django apps

### Frontend (React + TypeScript)
- **React 18+** with TypeScript for type safety
- **React Router** for SPA navigation
- **Tailwind CSS** for responsive UI design
- **Axios** for API communication with interceptors

## 🇰🇪 Kenyan Compliance Features

### Tax Calculations (2024 Rates)
- **PAYE (Pay As You Earn)** with progressive tax bands
- **Personal Relief** - KES 2,400/month
- **Insurance Relief** - Up to KES 5,000/month
- **NSSF** - Tiered contributions (Tier I & II)
- **SHIF (SHA)** - 2.75% of gross salary
- **AHL (Affordable Housing Levy)** - 1.5% of gross salary

### Statutory Compliance
- **KRA PIN** validation and management
- **NSSF Number** tracking
- **SHA Number** management
- **P10 Tax Reports** generation
- **Payslip** generation with statutory breakdowns

## 📁 Project Structure

```
payrollhq/                     # Django Backend
├── payrollhq/                 # Main project settings
├── organizations/             # Multi-tenant organization management
├── employees/                 # Employee data management
├── master_data/               # Compliance settings & rates
├── calculations/              # PayEngine - Core calculation logic
├── payrun/                    # Payroll batch processing
├── reporting/                 # Report generation (P10, NSSF, etc.)
├── earnings/                  # Earnings management
├── deductions/                # Deductions management
└── manage.py

payrollhq-frontend/            # React Frontend
├── src/
│   ├── components/            # Reusable UI components
│   ├── pages/                 # Page components
│   ├── contexts/              # React contexts (Auth, etc.)
│   ├── services/              # API service layer
│   ├── types/                 # TypeScript type definitions
│   └── hooks/                 # Custom React hooks
├── public/
└── package.json
```

## 🚀 Quick Start

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/capollo254/payrolhq.git
   cd payrolhq
   ```

2. **Set up Python environment**
   ```bash
   cd payrollhq
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database and secret key settings
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Start the backend server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd payrollhq-frontend
   npm install
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API URL
   ```

3. **Start the frontend server**
   ```bash
   npm start
   ```

## 🔧 Core Components

### PayEngine (Calculation Service)
Located in `calculations/pay_engine.py`, this is the heart of the payroll system:

- **Progressive PAYE calculation** following KRA guidelines
- **Statutory deductions** with proper sequencing
- **Relief calculations** including personal and insurance relief
- **Gross-to-net** salary computation

### ComplianceSetting Model
Located in `master_data/models.py`:

- **Dynamic tax rates** with versioning
- **Historical compliance** data tracking
- **Validation logic** for Kenyan tax rules
- **JSON storage** for flexible rate structures

### Multi-Tenant Architecture
- **Organization-based** data segregation
- **User role management** (Owner, Admin, HR Manager, etc.)
- **Isolated payroll** processing per organization

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/user/` - Current user info

### Organizations
- `GET /api/organizations/` - List organizations
- `GET /api/organizations/current/` - Current organization

### Employees
- `GET /api/employees/` - List employees
- `POST /api/employees/` - Create employee
- `GET /api/employees/{id}/` - Employee details
- `PUT /api/employees/{id}/` - Update employee

### Payroll Processing
- `POST /api/payrun/batches/calculate_batch/` - Calculate payroll batch
- `GET /api/payrun/batches/` - List payroll batches
- `POST /api/payrun/batches/{id}/approve_batch/` - Approve batch

### Compliance
- `GET /api/master-data/compliance-settings/` - List compliance settings
- `GET /api/master-data/compliance-settings/current_settings/` - Current rates

### Reports
- `GET /api/reporting/p10/{batch_id}/` - Generate P10 report
- `GET /api/reporting/nssf/{batch_id}/` - Generate NSSF report
- `GET /api/reporting/payslip/{payslip_id}/pdf/` - Generate payslip PDF

## 🚀 Deployment on Railway

### Backend Deployment

1. **Create a new Railway project** from your GitHub repository
2. **Add environment variables**:
   ```
   DJANGO_SECRET_KEY=your-secret-key
   DEBUG=False
   DATABASE_URL=postgresql://... (Railway will provide this)
   ALLOWED_HOSTS=your-app.railway.app
   ```

3. **Create a Procfile** in the root directory:
   ```
   web: cd payrollhq && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn payrollhq.wsgi:application --bind 0.0.0.0:$PORT
   ```

4. **Add gunicorn to requirements.txt**:
   ```
   pip install gunicorn
   pip freeze > payrollhq/requirements.txt
   ```

### Frontend Deployment

1. **Create a separate Railway service** for the frontend
2. **Add build command**:
   ```
   cd payrollhq-frontend && npm install && npm run build
   ```

3. **Add start command**:
   ```
   cd payrollhq-frontend && npx serve -s build -l $PORT
   ```

4. **Add serve dependency**:
   ```bash
   cd payrollhq-frontend
   npm install --save serve
   ```

## 🔐 Security Features

- **JWT Authentication** with refresh tokens
- **Multi-tenant data isolation**
- **Role-based access control**
- **Input validation** and sanitization
- **CORS configuration** for cross-origin requests

## 📊 Kenyan Tax Compliance (2024)

### PAYE Tax Bands
| Monthly Income (KES) | Rate |
|---------------------|------|
| 0 - 24,000          | 10%  |
| 24,001 - 32,333     | 25%  |
| 32,334 - 500,000    | 30%  |
| 500,001 - 800,000   | 32.5%|
| Above 800,000       | 35%  |

### Statutory Deductions
- **Personal Relief**: KES 2,400/month
- **Insurance Relief**: Up to KES 5,000/month
- **NSSF**: Tiered contributions
- **SHIF**: 2.75% of gross salary
- **AHL**: 1.5% of gross salary

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, email support@payrollhq.co.ke or create an issue in this repository.

---

**Built with ❤️ for Kenyan businesses**