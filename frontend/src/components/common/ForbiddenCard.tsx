import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';

interface ForbiddenCardProps {
  role?: string;
  roleDisplay?: string;
  requestedPath?: string;
  onReturn?: () => void;
}

export const ForbiddenCard: React.FC<ForbiddenCardProps> = ({
  role = 'User',
  roleDisplay,
  requestedPath = '/',
  onReturn,
}) => {
  return (
    <div
      role="region"
      aria-label="Access Denied"
      className="bg-white border border-rose-200 rounded-2xl p-8 max-w-xl mx-auto my-12 text-center shadow-lg"
    >
      <div className="w-16 h-16 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-4 border border-rose-200 shadow-xs">
        <ShieldAlert className="w-8 h-8 text-rose-600" aria-hidden="true" />
      </div>
      <h2 className="text-xl font-black text-rose-950 mb-2">Access Denied (HTTP 403)</h2>
      <p className="text-sm font-semibold text-rose-700 mb-6">
        You do not have permission to access this resource or perform this action.
      </p>
      <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-left text-xs space-y-2 mb-6 font-mono text-slate-700">
        <p>
          <span className="font-bold text-slate-900">Assigned Role:</span>{' '}
          {roleDisplay || role}
        </p>
        <p>
          <span className="font-bold text-slate-900">Requested Path:</span> {requestedPath}
        </p>
        <p>
          <span className="font-bold text-slate-900">Authorization Status:</span> Rejected by Backend Authorization Guard
        </p>
      </div>
      {onReturn ? (
        <button
          type="button"
          onClick={onReturn}
          className="inline-block px-5 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-xl shadow-md transition cursor-pointer"
        >
          Return to Dashboard
        </button>
      ) : (
        <Link
          to="/"
          className="inline-block px-5 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-xl shadow-md transition"
        >
          Return to Dashboard
        </Link>
      )}
    </div>
  );
};

export default ForbiddenCard;
