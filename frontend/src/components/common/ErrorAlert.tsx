import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface ErrorAlertProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title,
  message,
  onDismiss,
  className = '',
}) => {
  if (!message) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs shadow-xs flex items-start gap-3 ${className}`}
    >
      <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1 min-w-0">
        {title && <h4 className="font-bold text-rose-950 mb-0.5">{title}</h4>}
        <p className="font-medium text-rose-800 break-words leading-relaxed">{message}</p>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="p-1 -mr-1 -mt-1 text-rose-500 hover:text-rose-800 hover:bg-rose-100 rounded-lg transition cursor-pointer"
          aria-label="Dismiss error"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};

export default ErrorAlert;
