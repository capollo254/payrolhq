import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  Employee, 
  Organization, 
  ComplianceSetting, 
  PayrollBatch, 
  PayslipRecord,
  PayrollCalculationRequest,
  PayrollCalculationResponse,
  DashboardStats,
  ApiError 
} from '../types';
import { 
  User,
  LoginRequest, 
  AuthResponse, 
  RegisterRequest,
  PasswordResetRequest,
  PasswordResetConfirm 
} from '../types/auth';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Token ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearAuthToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth token management
  private getAuthToken(): string | null {
    return localStorage.getItem('payrollhq_token');
  }

  private setAuthToken(token: string): void {
    localStorage.setItem('payrollhq_token', token);
  }

  private clearAuthToken(): void {
    localStorage.removeItem('payrollhq_token');
    localStorage.removeItem('payrollhq_user');
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await this.api.post('/auth/login/', credentials);
    this.setAuthToken(response.data.access);
    localStorage.setItem('payrollhq_user', JSON.stringify(response.data.user));
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout/');
    } finally {
      this.clearAuthToken();
    }
  }

  async getCurrentUser(): Promise<User> {
    const response: AxiosResponse<User> = await this.api.get('/auth/user/');
    return response.data;
  }

  getCurrentUserFromStorage(): User | null {
    const userJson = localStorage.getItem('payrollhq_user');
    return userJson ? JSON.parse(userJson) : null;
  }

  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }

  // Organizations
  async getOrganization(): Promise<Organization> {
    const response: AxiosResponse<Organization> = await this.api.get('/organizations/current/');
    return response.data;
  }

  async updateOrganization(data: Partial<Organization>): Promise<Organization> {
    const response: AxiosResponse<Organization> = await this.api.patch('/organizations/current/', data);
    return response.data;
  }

  // Employees
  async getEmployees(params?: { 
    page?: number; 
    search?: string; 
    is_active?: boolean;
    department?: string;
  }): Promise<{ results: Employee[]; count: number; next?: string; previous?: string }> {
    const response = await this.api.get('/employees/', { params });
    return response.data;
  }

  async getEmployee(id: string): Promise<Employee> {
    const response: AxiosResponse<Employee> = await this.api.get(`/employees/${id}/`);
    return response.data;
  }

  async createEmployee(data: Partial<Employee>): Promise<Employee> {
    const response: AxiosResponse<Employee> = await this.api.post('/employees/', data);
    return response.data;
  }

  async updateEmployee(id: string, data: Partial<Employee>): Promise<Employee> {
    const response: AxiosResponse<Employee> = await this.api.patch(`/employees/${id}/`, data);
    return response.data;
  }

  async deleteEmployee(id: string): Promise<void> {
    await this.api.delete(`/employees/${id}/`);
  }

  // Compliance Settings
  async getComplianceSettings(): Promise<ComplianceSetting[]> {
    const response: AxiosResponse<{ results: ComplianceSetting[] }> = await this.api.get('/master-data/compliance-settings/');
    return response.data.results;
  }

  async getCurrentComplianceSettings(): Promise<{ [key: string]: ComplianceSetting }> {
    const response = await this.api.get('/master-data/compliance-settings/current_settings/');
    return response.data;
  }

  async createComplianceSetting(data: Partial<ComplianceSetting>): Promise<ComplianceSetting> {
    const response: AxiosResponse<ComplianceSetting> = await this.api.post('/master-data/compliance-settings/', data);
    return response.data;
  }

  async updateComplianceSetting(id: string, data: Partial<ComplianceSetting>): Promise<ComplianceSetting> {
    const response: AxiosResponse<ComplianceSetting> = await this.api.patch(`/master-data/compliance-settings/${id}/`, data);
    return response.data;
  }

  async approveComplianceSetting(id: string): Promise<ComplianceSetting> {
    const response: AxiosResponse<ComplianceSetting> = await this.api.post(`/master-data/compliance-settings/${id}/approve/`);
    return response.data;
  }

  async validateComplianceSetup(): Promise<{
    is_valid: boolean;
    missing_settings: string[];
    warnings: string[];
  }> {
    const response = await this.api.get('/master-data/compliance-settings/validate_current_setup/');
    return response.data;
  }

  // Payroll Batches
  async getPayrollBatches(params?: { 
    page?: number; 
    status?: string;
    pay_period_start?: string;
  }): Promise<{ results: PayrollBatch[]; count: number }> {
    const response = await this.api.get('/payrun/batches/', { params });
    return response.data;
  }

  async getPayrollBatch(id: string): Promise<PayrollBatch> {
    const response: AxiosResponse<PayrollBatch> = await this.api.get(`/payrun/batches/${id}/`);
    return response.data;
  }

  async calculatePayrollBatch(data: PayrollCalculationRequest): Promise<PayrollCalculationResponse> {
    const response: AxiosResponse<PayrollCalculationResponse> = await this.api.post('/payrun/batches/calculate_batch/', data);
    return response.data;
  }

  async approvePayrollBatch(id: string, notes?: string): Promise<{ status: string }> {
    const response = await this.api.post(`/payrun/batches/${id}/approve_batch/`, { notes });
    return response.data;
  }

  async lockPayrollBatch(id: string): Promise<{ status: string }> {
    const response = await this.api.post(`/payrun/batches/${id}/lock_batch/`);
    return response.data;
  }

  // Payslips
  async getPayslips(batchId: string): Promise<PayslipRecord[]> {
    const response: AxiosResponse<{ results: PayslipRecord[] }> = await this.api.get(`/payrun/batches/${batchId}/payslips/`);
    return response.data.results;
  }

  async getPayslip(id: string): Promise<PayslipRecord> {
    const response: AxiosResponse<PayslipRecord> = await this.api.get(`/payrun/payslips/${id}/`);
    return response.data;
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response: AxiosResponse<DashboardStats> = await this.api.get('/dashboard/stats/');
    return response.data;
  }

  // Reports
  async generateP10Report(batchId: string): Promise<Blob> {
    const response = await this.api.get(`/reporting/p10/${batchId}/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async generateNSSFReport(batchId: string): Promise<Blob> {
    const response = await this.api.get(`/reporting/nssf/${batchId}/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async generatePayslipPDF(payslipId: string): Promise<Blob> {
    const response = await this.api.get(`/reporting/payslip/${payslipId}/pdf/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Error handling helper
  handleApiError(error: any): ApiError {
    if (error.response?.data) {
      return error.response.data as ApiError;
    }
    return {
      error: error.message || 'An unexpected error occurred',
    };
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Auth-specific API methods
export const authApi = {
  login: (credentials: LoginRequest) => apiService.login(credentials),
  logout: () => apiService.logout(),
  getCurrentUser: () => apiService.getCurrentUser(),
  getCurrentUserFromStorage: () => apiService.getCurrentUserFromStorage(),
};

export default apiService;