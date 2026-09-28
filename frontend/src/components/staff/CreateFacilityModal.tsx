import React, { useState } from 'react';
import { X, Building2, AlertCircle } from 'lucide-react';
import type { CreateFacilityPayload } from '../../types/staff';

interface CreateFacilityModalProps {
  isOpen: boolean;
  districtId?: number | null;
  districtName?: string;
  isLoading?: boolean;
  onCreate: (payload: CreateFacilityPayload) => Promise<void>;
  onClose: () => void;
}

export const CreateFacilityModal: React.FC<CreateFacilityModalProps> = ({
  isOpen,
  districtId,
  districtName,
  isLoading = false,
  onCreate,
  onClose,
}) => {
  const [formData, setFormData] = useState<{
    facility_name: string;
    facility_code: string;
    facility_type: string;
    address: string;
  }>({
    facility_name: '',
    facility_code: '',
    facility_type: 'CLINIC',
    address: '',
  });

  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.facility_name.trim()) {
      setError('Facility Name is required.');
      return;
    }
    if (!formData.facility_code.trim()) {
      setError('Facility Code is required.');
      return;
    }

    try {
      const payload: CreateFacilityPayload = {
        facility_name: formData.facility_name.trim(),
        facility_code: formData.facility_code.trim().toUpperCase(),
        facility_type: formData.facility_type,
        state: 1, // Default state (Karnataka)
        district: districtId || 1,
        address: formData.address.trim() || undefined,
        status: 'ACTIVE',
      };
      await onCreate(payload);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to create clinic facility. Please check fields and retry.');
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-facility-title"
    >
      <div className="relative bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h3 id="create-facility-title" className="text-base font-bold text-slate-900">
                Register New Clinic Facility
              </h3>
              <p className="text-xs text-slate-500 font-medium">
                District Health Officer Facility Provisioning
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-2 text-xs text-rose-700 font-medium">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Facility Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.facility_name}
              onChange={(e) => setFormData({ ...formData, facility_name: e.target.value })}
              placeholder="e.g. Namma Clinic - Ward 42"
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              data-testid="facility-name-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Facility Code <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.facility_code}
                onChange={(e) => setFormData({ ...formData, facility_code: e.target.value.toUpperCase() })}
                placeholder="e.g. NC-W42"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none uppercase font-mono"
                data-testid="facility-code-input"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Facility Type <span className="text-rose-500">*</span>
              </label>
              <select
                value={formData.facility_type}
                onChange={(e) => setFormData({ ...formData, facility_type: e.target.value })}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="CLINIC">Namma Clinic</option>
                <option value="UPHC">Urban PHC</option>
                <option value="DISPENSARY">Dispensary</option>
                <option value="HOSPITAL">General Hospital</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Assigned District</label>
            <input
              type="text"
              disabled
              value={districtName || 'Authorized Administrative District'}
              className="w-full text-sm border border-slate-200 bg-slate-50 text-slate-500 rounded-lg p-2.5 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Address / Location</label>
            <textarea
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              placeholder="e.g. 5th Main, Near Bus Terminal, Ward 42"
              rows={2}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition disabled:opacity-50 inline-flex items-center gap-2"
              data-testid="submit-create-facility-btn"
            >
              {isLoading ? 'Registering...' : 'Register Facility'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateFacilityModal;