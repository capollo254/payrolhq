# PayrollHQ Directory Structure for Railway Deployment

## Root Directory Files (Required for Railway Detection)
- manage.py ✓ (Django management script)
- requirements.txt ✓ (Python dependencies) 
- runtime.txt ✓ (Python version specification)
- nixpacks.toml ✓ (Explicit Nixpacks configuration)
- Procfile ✓ (Railway deployment commands)
- railway.json ✓ (Railway configuration)

## Django Apps
- organizations/ (Multi-tenant organizations)
- employees/ (Employee management)
- master_data/ (Compliance settings)
- calculations/ (PayEngine - payroll calculations)
- payrun/ (Payroll batch processing)
- reporting/ (P10, NSSF reports)
- earnings/ (Earnings management)
- deductions/ (Deductions management)

## Django Project Settings
- payrollhq/ (Main Django project directory)
  - settings.py
  - urls.py
  - wsgi.py
  - asgi.py

## Frontend
- payrollhq-frontend/ (React TypeScript frontend)

This is a Django web application ready for Railway deployment.