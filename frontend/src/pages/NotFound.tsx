import React from 'react';
import { Link } from 'react-router-dom';
import { FileQuestion } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import DashboardLayout from '../layouts/DashboardLayout';

export const NotFound: React.FC = () => {
  const { user } = useAuth();

  const cardContent = (
    <div
      role="region"
      aria-label="Page Not Found"
      className="bg-white border border-slate-200 rounded-2xl p-8 max-w-xl mx-auto my-12 text-center shadow-lg"
    >
      <div className="w-16 h-16 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mx-auto mb-4 border border-slate-200 shadow-xs">
        <FileQuestion className="w-8 h-8 text-slate-500" aria-hidden="true" />
      </div>
      <h2 className="text-xl font-bold text-slate-900 mb-2">Page Not Found (HTTP 404)</h2>
      <p className="text-xs text-slate-600 mb-6">
        The requested clinical or operational route does not exist in this deployment.
      </p>
      <Link
        to={user ? '/dashboard' : '/login'}
        className="inline-block px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition"
      >
        {user ? 'Return to Role Dashboard' : 'Return to Login'}
      </Link>
    </div>
  );

  if (user) {
    return <DashboardLayout>{cardContent}</DashboardLayout>;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      {cardContent}
    </div>
  );
};

export default NotFound;
