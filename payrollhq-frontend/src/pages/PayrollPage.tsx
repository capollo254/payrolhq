import React from 'react';

const PayrollPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
          Payroll Management
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Manage payroll batches and process employee payments
        </p>
      </div>
      
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="text-center">
            <h3 className="mt-2 text-sm font-medium text-gray-900">Payroll Management</h3>
            <p className="mt-1 text-sm text-gray-500">
              This page is coming soon. Here you'll be able to create and manage payroll batches.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PayrollPage;