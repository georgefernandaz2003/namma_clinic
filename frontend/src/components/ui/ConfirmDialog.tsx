import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2, Info, Loader2, X } from 'lucide-react';

export type ConfirmVariant = 'danger' | 'warning' | 'info' | 'primary' | 'success';

export interface ConfirmDetailItem {
  label: string;
  value: React.ReactNode;
}

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: React.ReactNode;
  confirmText?: string;
  cancelText?: string;
  variant?: ConfirmVariant;
  details?: ConfirmDetailItem[];
  warning?: string;
  loading?: boolean;
  loadingText?: string;
  error?: string | null;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'primary',
  details,
  warning,
  loading = false,
  loadingText,
  error = null,
  onConfirm,
  onCancel,
}) => {
  if (!open) return null;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && !loading) {
      onCancel();
    }
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return {
          icon: <AlertTriangle className="w-6 h-6 text-rose-600" />,
          iconBg: 'bg-rose-100 border-rose-200 text-rose-600',
          btnBg: 'bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/20',
          border: 'border-rose-200',
          badge: 'bg-rose-50 text-rose-700 border-rose-200',
        };
      case 'warning':
        return {
          icon: <AlertCircle className="w-6 h-6 text-amber-600" />,
          iconBg: 'bg-amber-100 border-amber-200 text-amber-600',
          btnBg: 'bg-amber-600 hover:bg-amber-700 text-white shadow-amber-600/20',
          border: 'border-amber-200',
          badge: 'bg-amber-50 text-amber-800 border-amber-200',
        };
      case 'success':
        return {
          icon: <CheckCircle2 className="w-6 h-6 text-emerald-600" />,
          iconBg: 'bg-emerald-100 border-emerald-200 text-emerald-600',
          btnBg: 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20',
          border: 'border-emerald-200',
          badge: 'bg-emerald-50 text-emerald-800 border-emerald-200',
        };
      case 'info':
      case 'primary':
      default:
        return {
          icon: <Info className="w-6 h-6 text-blue-600" />,
          iconBg: 'bg-blue-100 border-blue-200 text-blue-600',
          btnBg: 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-600/20',
          border: 'border-blue-200',
          badge: 'bg-blue-50 text-blue-800 border-blue-200',
        };
    }
  };

  const vStyles = getVariantStyles();

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      tabIndex={-1}
      onKeyDown={handleKeyDown}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs transition-opacity duration-200"
    >
      <div
        className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full overflow-hidden transition-all transform duration-200 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 pb-4 flex items-start gap-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border ${vStyles.iconBg}`}>
            {vStyles.icon}
          </div>
          <div className="flex-1 min-w-0">
            <h2 id="confirm-dialog-title" className="text-lg font-black text-slate-900 tracking-tight leading-snug">
              {title}
            </h2>
            <div className="text-xs text-slate-600 mt-1 font-medium leading-relaxed">
              {message}
            </div>
          </div>
          {!loading && (
            <button
              onClick={onCancel}
              className="text-slate-400 hover:text-slate-600 rounded-lg p-1 transition cursor-pointer"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Contextual Details (if provided) */}
        {details && details.length > 0 && (
          <div className="px-6 py-2">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2 text-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                Operation Context & Parameters
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-700">
                {details.map((item, idx) => (
                  <div key={idx} className="flex flex-col">
                    <span className="text-[10px] text-slate-400 font-semibold">{item.label}</span>
                    <span className="font-bold text-slate-900 break-words">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Warning Callout for Destructive / Sensitive Actions */}
        {warning && (
          <div className="px-6 py-2">
            <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-xl p-3 text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="font-semibold">{warning}</div>
            </div>
          </div>
        )}

        {/* Error Callout if Mutation Failed */}
        {error && (
          <div className="px-6 py-2">
            <div className="bg-rose-50 border border-rose-200 text-rose-900 rounded-xl p-3 text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block">Operation Failed</span>
                <span className="font-medium text-rose-800">{error}</span>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="p-6 pt-4 bg-slate-50/80 border-t border-slate-100 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 font-bold text-xs rounded-xl transition shadow-xs disabled:opacity-50 cursor-pointer"
          >
            {cancelText}
          </button>

          <button
            type="button"
            onClick={() => onConfirm()}
            disabled={loading}
            className={`px-5 py-2.5 font-bold text-xs rounded-xl shadow-md transition flex items-center gap-2 disabled:opacity-60 cursor-pointer ${vStyles.btnBg}`}
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
            <span>{loading ? loadingText || 'Processing...' : confirmText}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
