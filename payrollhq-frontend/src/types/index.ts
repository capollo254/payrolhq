// API Types for PayrollHQ SaaS Platform

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'OWNER' | 'ADMIN' | 'HR_MANAGER' | 'PAYROLL_CLERK' | 'VIEWER';
  organization: Organization;
  is_organization_admin: boolean;
  last_login?: string;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  trading_name?: string;
  organization_type: 'PRIVATE_LIMITED' | 'PUBLIC_LIMITED' | 'PARTNERSHIP' | 'SOLE_PROPRIETOR' | 'NGO' | 'GOVERNMENT' | 'OTHER';
  registration_number: string;
  kra_pin: string;
  nssf_number?: string;
  nhif_number?: string;
  email: string;
  phone?: string;
  physical_address: string;
  city: string;
  county: string;
  is_active: boolean;
  subscription_plan: 'TRIAL' | 'BASIC' | 'STANDARD' | 'PREMIUM';
  subscription_expires?: string;
  max_employees: number;
  employee_count: number;
  created_at: string;
}

export interface Employee {
  id: string;
  organization: string;
  employee_number: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  date_of_birth: string;
  gender: 'M' | 'F' | 'O';
  marital_status: 'SINGLE' | 'MARRIED' | 'DIVORCED' | 'WIDOWED' | 'SEPARATED';
  email?: string;
  phone: string;
  residential_address: string;
  city: string;
  county: string;
  
  // Mandatory Kenyan IDs
  national_id: string;
  kra_pin: string;
  nssf_number: string;
  sha_number: string;
  
  // Employment details
  employment_type: 'PERMANENT' | 'CONTRACT' | 'CASUAL' | 'INTERN' | 'CONSULTANT';
  date_hired: string;
  date_terminated?: string;
  job_title: string;
  department: string;
  basic_salary: string; // Decimal as string
  
  // Bank details
  bank_name: string;
  bank_branch: string;
  account_number: string;
  account_name: string;
  
  // Status
  is_active: boolean;
  is_on_leave: boolean;
  
  created_at: string;
  updated_at: string;
}

export interface ComplianceSetting {
  id: string;
  compliance_type: 'PAYE_TAX_BANDS' | 'PERSONAL_RELIEF' | 'NSSF_RATES' | 'SHIF_RATES' | 'AHL_RATES' | 'INSURANCE_RELIEF' | 'PENSION_RELIEF' | 'MORTGAGE_RELIEF' | 'DISABILITY_EXEMPTION';
  compliance_type_display: string;
  effective_date: string;
  end_date?: string;
  compliance_data: any; // JSON object
  is_active: boolean;
  is_current: boolean;
  created_by: string;
  approved_by?: string;
  approved_at?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PayrollBatch {
  id: string;
  organization: string;
  batch_number: string;
  pay_period_type: 'MONTHLY' | 'WEEKLY' | 'BIWEEKLY';
  pay_period_start: string;
  pay_period_end: string;
  pay_date: string;
  status: 'DRAFT' | 'CALCULATING' | 'CALCULATED' | 'REVIEWED' | 'APPROVED' | 'LOCKED' | 'REMITTED' | 'CANCELLED';
  total_employees: number;
  total_gross_pay: string;
  total_net_pay: string;
  total_paye_tax: string;
  total_nssf: string;
  total_shif: string;
  total_ahl: string;
  calculated_at?: string;
  calculated_by?: string;
  approved_at?: string;
  approved_by?: string;
  locked_at?: string;
  locked_by?: string;
  created_at: string;
  updated_at: string;
}

export interface PayslipRecord {
  id: string;
  payroll_batch: string;
  employee: string;
  employee_name: string;
  employee_number: string;
  employee_kra_pin: string;
  basic_salary: string;
  gross_pay: string;
  taxable_income: string;
  paye_tax: string;
  nssf_employee: string;
  nssf_employer: string;
  shif_deduction: string;
  ahl_deduction: string;
  total_deductions: string;
  net_pay: string;
  calculated_at: string;
  calculated_by: string;
  created_at: string;
}

// API Request/Response Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface PayrollCalculationRequest {
  pay_period_start: string;
  pay_period_end: string;
  pay_date: string;
  batch_number: string;
  include_all_employees: boolean;
  selected_employee_ids?: string[];
  variable_earnings?: {
    [employee_id: string]: {
      overtime_hours?: string;
      overtime_rate?: string;
      bonus_amount?: string;
      commission_amount?: string;
    };
  };
  notes?: string;
}

export interface PayrollCalculationResponse {
  batch_id: string;
  batch_number: string;
  status: string;
  total_employees: number;
  successful_calculations: number;
  failed_calculations: number;
  total_gross_pay: string;
  total_net_pay: string;
  calculation_results: Array<{
    employee_id: string;
    employee_name: string;
    gross_pay: string;
    net_pay: string;
    status: 'success' | 'error';
  }>;
  calculation_errors: Array<{
    employee_id: string;
    employee_name: string;
    error: string;
    status: 'error';
  }>;
}

// Dashboard KPIs
export interface DashboardStats {
  total_employees: number;
  active_employees: number;
  total_payroll_batches: number;
  current_month_gross: number;
  next_pay_run_date: string;
  last_pay_run_date?: string;
  pending_approvals: number;
  urgent_alerts: UrgentAlert[];
  recent_payroll_batches: PayrollBatch[];
  monthly_payroll_summary: {
    gross_pay: string;
    net_pay: string;
    total_tax: string;
    total_statutory: string;
  };
}

export interface UrgentAlert {
  id: string;
  type: 'MISSING_KRA_PIN' | 'MISSING_NSSF' | 'MISSING_SHA' | 'EXPIRED_CONTRACT' | 'COMPLIANCE_UPDATE';
  title: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  employee_id?: string;
  employee_name?: string;
  created_at: string;
}

// Form Types
export interface EmployeeFormData {
  employee_number: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  date_of_birth: string;
  gender: 'M' | 'F' | 'O';
  marital_status: 'SINGLE' | 'MARRIED' | 'DIVORCED' | 'WIDOWED' | 'SEPARATED';
  email?: string;
  phone: string;
  residential_address: string;
  city: string;
  county: string;
  national_id: string;
  kra_pin: string;
  nssf_number: string;
  sha_number: string;
  employment_type: 'PERMANENT' | 'CONTRACT' | 'CASUAL' | 'INTERN' | 'CONSULTANT';
  date_hired: string;
  job_title: string;
  department: string;
  basic_salary: string;
  bank_name: string;
  bank_branch: string;
  account_number: string;
  account_name: string;
}

// API Error Response
export interface ApiError {
  error: string;
  details?: string[];
  field_errors?: {
    [field: string]: string[];
  };
}