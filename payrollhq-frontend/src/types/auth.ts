export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: 'ADMIN' | 'HR_MANAGER' | 'EMPLOYEE';
  organization: {
    id: number;
    name: string;
    slug: string;
  };
  is_active: boolean;
  date_joined: string;
  last_login?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  organization_name: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  password: string;
}