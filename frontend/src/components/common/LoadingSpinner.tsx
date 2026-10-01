import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  label = 'Loading...',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  }[size];

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-center justify-center gap-3 ${className}`}
    >
      <div
        className={`${sizeClasses} border-slate-200 border-t-emerald-600 rounded-full animate-spin`}
        aria-hidden="true"
      />
      {label && (
        <span className="text-xs font-semibold text-slate-600 select-none">
          {label}
        </span>
      )}
      <span className="sr-only">{label}</span>
    </div>
  );
};

export default LoadingSpinner;
