import React from 'react';

const ReportsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
          Reports & Analytics
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Generate compliance reports and view payroll analytics
        </p>
      </div>
      
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="text-center">
            <h3 className="mt-2 text-sm font-medium text-gray-900">Reports & Analytics</h3>
            <p className="mt-1 text-sm text-gray-500">
              This page is coming soon. Here you'll be able to generate P10, NSSF, and other compliance reports.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;