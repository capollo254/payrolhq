import React, { useState, useEffect } from 'react';
import { 
  UsersIcon, 
  CurrencyDollarIcon, 
  ChartBarIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';
import { DashboardStats } from '../types';
import LoadingSpinner from '../components/ui/LoadingSpinner';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const dashboardStats = await apiService.getDashboardStats();
        setStats(dashboardStats);
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading dashboard</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const quickStats = [
    {
      name: 'Total Employees',
      value: stats?.total_employees || 0,
      icon: UsersIcon,
      color: 'bg-blue-500',
      href: '/employees',
    },
    {
      name: 'Active Employees',
      value: stats?.active_employees || 0,
      icon: UsersIcon,
      color: 'bg-green-500',
      href: '/employees?status=active',
    },
    {
      name: 'Payroll Batches',
      value: stats?.total_payroll_batches || 0,
      icon: CurrencyDollarIcon,
      color: 'bg-purple-500',
      href: '/payroll',
    },
    {
      name: 'This Month Gross',
      value: `KES ${(stats?.current_month_gross || 0).toLocaleString()}`,
      icon: ChartBarIcon,
      color: 'bg-indigo-500',
      href: '/reports',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Welcome back! Here's what's happening with your payroll.
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <Link
            to="/payroll/new"
            className="ml-3 inline-flex items-center rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
          >
            New Payroll
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {quickStats.map((stat) => (
          <Link
            key={stat.name}
            to={stat.href}
            className="relative overflow-hidden rounded-lg bg-white px-4 py-5 shadow hover:shadow-md transition-shadow sm:px-6 sm:py-6"
          >
            <div>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`inline-flex items-center justify-center rounded-md ${stat.color} p-3`}>
                    <stat.icon className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="truncate text-sm font-medium text-gray-500">{stat.name}</dt>
                    <dd className="text-lg font-semibold text-gray-900">{stat.value}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Recent Activity Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Payroll Runs */}
        <div className="rounded-lg bg-white shadow">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Recent Payroll Runs</h3>
              <Link
                to="/payroll"
                className="text-sm font-medium text-primary-600 hover:text-primary-500"
              >
                View all
              </Link>
            </div>
            <div className="mt-6">
              {stats?.recent_payroll_batches && stats.recent_payroll_batches.length > 0 ? (
                <div className="flow-root">
                  <ul className="-my-5 divide-y divide-gray-200">
                    {stats.recent_payroll_batches.map((batch) => (
                      <li key={batch.id} className="py-4">
                        <div className="flex items-center space-x-4">
                          <div className="flex-shrink-0">
                            <span className={`inline-flex h-8 w-8 items-center justify-center rounded-full ${
                              batch.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                              batch.status === 'CALCULATED' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              <CurrencyDollarIcon className="h-4 w-4" />
                            </span>
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium text-gray-900">
                              Payroll Batch #{batch.batch_number}
                            </p>
                            <p className="truncate text-sm text-gray-500">
                              {new Date(batch.pay_period_start).toLocaleDateString()} - {new Date(batch.pay_period_end).toLocaleDateString()}
                            </p>
                          </div>
                          <div>
                            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              batch.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                              batch.status === 'CALCULATED' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {batch.status}
                            </span>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="text-sm text-gray-500">No recent payroll runs</p>
              )}
            </div>
          </div>
        </div>

        {/* Compliance Status */}
        <div className="rounded-lg bg-white shadow">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Compliance Status</h3>
              <Link
                to="/compliance"
                className="text-sm font-medium text-primary-600 hover:text-primary-500"
              >
                View details
              </Link>
            </div>
            <div className="mt-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">PAYE Settings</span>
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    Current
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">NSSF Settings</span>
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    Current
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">SHIF Settings</span>
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    Current
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">AHL Settings</span>
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    Current
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="rounded-lg bg-white shadow">
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link
              to="/employees/new"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              <div>
                <span className="inline-flex items-center justify-center rounded-lg bg-blue-600 p-3">
                  <UsersIcon className="h-6 w-6 text-white" aria-hidden="true" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-900">Add Employee</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Add a new employee to your organization
                </p>
              </div>
            </Link>

            <Link
              to="/payroll/new"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              <div>
                <span className="inline-flex items-center justify-center rounded-lg bg-green-600 p-3">
                  <CurrencyDollarIcon className="h-6 w-6 text-white" aria-hidden="true" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-900">Run Payroll</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Process payroll for current period
                </p>
              </div>
            </Link>

            <Link
              to="/reports"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              <div>
                <span className="inline-flex items-center justify-center rounded-lg bg-purple-600 p-3">
                  <ChartBarIcon className="h-6 w-6 text-white" aria-hidden="true" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-900">View Reports</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Generate compliance and payroll reports
                </p>
              </div>
            </Link>

            <Link
              to="/compliance"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              <div>
                <span className="inline-flex items-center justify-center rounded-lg bg-indigo-600 p-3">
                  <ExclamationTriangleIcon className="h-6 w-6 text-white" aria-hidden="true" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-900">Compliance</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Manage tax and statutory settings
                </p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;