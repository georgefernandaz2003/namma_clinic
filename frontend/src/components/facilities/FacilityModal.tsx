import React, { useState, useEffect } from 'react';
import { X, Building2, AlertCircle, Save, Check } from 'lucide-react';
import type { Facility, FacilityType } from '../../types';

interface FacilityModalProps {
  isOpen: boolean;
  mode: 'create' | 'edit';
  initialData?: Facility | null;
  districtName?: string;
  districtId?: number | null;
  isLoading?: boolean;
  onClose: () => void;
  onSave: (payload: Partial<Facility>) => Promise<void>;
}

export const FacilityModal: React.FC<FacilityModalProps> = ({
  isOpen,
  mode,
  initialData,
  districtName,
  districtId,
  isLoading = false,
  onClose,
  onSave,
}) => {
  const [formData, setFormData] = useState<{
    facility_name: string;
    facility_code: string;
    facility_type: FacilityType;
    status: string;
    address: string;
    phone: string;
    email: string;
    opening_time: string;
    closing_time: string;
    population_served: number;
    vulnerable_population: number;
    services: string;
  }>({
    facility_name: '',
    facility_code: '',
    facility_type: 'NAMMA_CLINIC',
    status: 'ACTIVE',
    address: '',
    phone: '',
    email: '',
    opening_time: '09:00 AM',
    closing_time: '04:30 PM',
    population_served: 20000,
    vulnerable_population: 5000,
    services: 'General OPD, NCD Screening, ANC/PNC Care, Immunization, Basic Diagnostics, Pharmacy',
  });

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mode === 'edit' && initialData) {
      setFormData({
        facility_name: initialData.facility_name || '',
        facility_code: initialData.facility_code || '',
        facility_type: initialData.facility_type || 'NAMMA_CLINIC',
        status: initialData.status || 'ACTIVE',
        address: initialData.address || '',
        phone: initialData.phone || '',
        email: initialData.email || '',
        opening_time: initialData.opening_time || '09:00 AM',
        closing_time: initialData.closing_time || '04:30 PM',
        population_served: initialData.population_served ?? 20000,
        vulnerable_population: initialData.vulnerable_population ?? 5000,
        services: initialData.services || 'General OPD, NCD Screening, Basic Diagnostics, Pharmacy',
      });
    } else if (mode === 'create') {
      setFormData({
        facility_name: '',
        facility_code: '',
        facility_type: 'NAMMA_CLINIC',
        status: 'ACTIVE',
        address: '',
        phone: '',
        email: '',
        opening_time: '09:00 AM',
        closing_time: '04:30 PM',
        population_served: 20000,
        vulnerable_population: 5000,
        services: 'General OPD, NCD Screening, Basic Diagnostics, Pharmacy',
      });
    }
    setError(null);
  }, [mode, initialData, isOpen]);

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
      const payload: Partial<Facility> = {
        facility_name: formData.facility_name.trim(),
        facility_code: formData.facility_code.trim().toUpperCase(),
        facility_type: formData.facility_type,
        status: formData.status,
        address: formData.address.trim(),
        phone: formData.phone.trim(),
        email: formData.email.trim(),
        opening_time: formData.opening_time.trim(),
        closing_time: formData.closing_time.trim(),
        population_served: Number(formData.population_served) || 0,
        vulnerable_population: Number(formData.vulnerable_population) || 0,
        services: formData.services.trim(),
      };

      if (mode === 'create' && districtId) {
        payload.district = districtId;
      }

      await onSave(payload);
      onClose();
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.response?.data?.error || err?.message || 'Failed to save facility details. Please check values and retry.';
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="facility-modal-title"
    >
      <div className="relative bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-teal-50 text-teal-700 rounded-xl border border-teal-100">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <h2 id="facility-modal-title" className="text-lg font-bold text-slate-900">
                {mode === 'create' ? 'Onboard New Healthcare Facility' : 'Edit Facility Details & Status'}
              </h2>
              <p className="text-xs text-slate-500 font-medium">
                District Health Officer Facility Management & Governance
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-2.5 text-xs text-rose-700 font-medium" role="alert">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Facility Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.facility_name}
                onChange={(e) => setFormData({ ...formData, facility_name: e.target.value })}
                placeholder="e.g. Namma Clinic - Ward 101 Indiranagar"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                data-testid="facility-name-input"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Facility Code <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                disabled={mode === 'edit'}
                value={formData.facility_code}
                onChange={(e) => setFormData({ ...formData, facility_code: e.target.value.toUpperCase() })}
                placeholder="e.g. NC-BLR-101"
                className={`w-full text-sm border rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none font-mono uppercase ${
                  mode === 'edit' ? 'bg-slate-50 text-slate-500 border-slate-200 cursor-not-allowed' : 'border-slate-300'
                }`}
                data-testid="facility-code-input"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Facility Type <span className="text-rose-500">*</span>
              </label>
              <select
                value={formData.facility_type}
                onChange={(e) => setFormData({ ...formData, facility_type: e.target.value as FacilityType })}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none bg-white"
                data-testid="facility-type-select"
              >
                <option value="NAMMA_CLINIC">Namma Clinic (Urban HWC)</option>
                <option value="UPHC">Urban Primary Health Centre (UPHC)</option>
                <option value="MAIN_HOSPITAL">Main Hospital</option>
                <option value="SECONDARY_HOSPITAL">Secondary Hospital</option>
                <option value="REFERRAL_HOSPITAL">Referral Hospital</option>
                <option value="DIAGNOSTIC_CENTER">Diagnostic Center</option>
                <option value="URBAN_CLINIC">Urban Clinic</option>
                <option value="RURAL_CLINIC">Rural Clinic</option>
                <option value="VILLAGE_CLINIC">Village Clinic</option>
                <option value="OTHER">Other Health Facility</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Operational Status <span className="text-rose-500">*</span>
              </label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none bg-white font-medium"
                data-testid="facility-status-select"
              >
                <option value="ACTIVE">ACTIVE (Operational)</option>
                <option value="INACTIVE">INACTIVE (Decommissioned)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Assigned District
              </label>
              <input
                type="text"
                disabled
                value={districtName || 'Bengaluru Urban'}
                className="w-full text-sm border border-slate-200 bg-slate-50 text-slate-600 rounded-lg p-2.5 cursor-not-allowed font-medium"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Contact Phone
              </label>
              <input
                type="text"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="e.g. 080-25251234"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                data-testid="facility-phone-input"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Official Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="e.g. ward101@nammaclinic.karnataka.gov.in"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                data-testid="facility-email-input"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Opening Time
              </label>
              <input
                type="text"
                value={formData.opening_time}
                onChange={(e) => setFormData({ ...formData, opening_time: e.target.value })}
                placeholder="09:00 AM"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                data-testid="facility-opening-time-input"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Closing Time
              </label>
              <input
                type="text"
                value={formData.closing_time}
                onChange={(e) => setFormData({ ...formData, closing_time: e.target.value })}
                placeholder="04:30 PM"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                data-testid="facility-closing-time-input"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Population Served
              </label>
              <input
                type="number"
                value={formData.population_served}
                onChange={(e) => setFormData({ ...formData, population_served: Number(e.target.value) })}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none font-mono"
                data-testid="facility-population-input"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Vulnerable Population
              </label>
              <input
                type="number"
                value={formData.vulnerable_population}
                onChange={(e) => setFormData({ ...formData, vulnerable_population: Number(e.target.value) })}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none font-mono"
                data-testid="facility-vulnerable-input"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Address / Physical Location
            </label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              placeholder="e.g. 12th Cross, 4th Main, Indiranagar Ward 101, Bengaluru"
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"
              data-testid="facility-address-input"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Services Summary
            </label>
            <input
              type="text"
              value={formData.services}
              onChange={(e) => setFormData({ ...formData, services: e.target.value })}
              placeholder="e.g. General OPD, NCD Screening, Basic Diagnostics, Pharmacy"
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"
              data-testid="facility-services-input"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2.5 text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
              data-testid="cancel-facility-btn"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-2.5 text-sm font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-xl shadow-xs transition disabled:opacity-50 inline-flex items-center gap-2"
              data-testid="submit-facility-btn"
            >
              {isLoading ? (
                'Saving...'
              ) : mode === 'create' ? (
                <>
                  <Check className="w-4 h-4" />
                  Onboard Facility
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FacilityModal;
