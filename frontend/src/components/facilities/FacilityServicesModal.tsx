import React, { useState, useEffect, useCallback } from 'react';
import type { Facility, FacilityService } from '../../types';
import { fetchFacilityServices, toggleFacilityService } from '../../api/facilityServices';
import { parseApiError } from '../../api/client';
import {
  Activity,
  X,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Power,
  RefreshCw,
} from 'lucide-react';

interface FacilityServicesModalProps {
  isOpen: boolean;
  facility: Facility | null;
  onClose: () => void;
}

export const FacilityServicesModal: React.FC<FacilityServicesModalProps> = ({
  isOpen,
  facility,
  onClose,
}) => {
  const [services, setServices] = useState<FacilityService[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const loadServices = useCallback(async () => {
    if (!facility) return;
    setLoading(true);
    try {
      const data = await fetchFacilityServices(facility.id);
      setServices(data);
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.message || 'Failed to load facility services.',
      });
    } finally {
      setLoading(false);
    }
  }, [facility]);

  useEffect(() => {
    if (isOpen && facility) {
      setFeedback(null);
      loadServices();
    } else {
      setServices([]);
      setFeedback(null);
    }
  }, [isOpen, facility, loadServices]);

  const handleToggle = async (fs: FacilityService) => {
    setActionLoadingId(fs.id);
    const newStatus = !fs.is_available;
    try {
      const updated = await toggleFacilityService(fs.id, newStatus);
      setServices((prev) =>
        prev.map((s) => (s.id === fs.id ? { ...s, is_available: updated.is_available } : s))
      );
      setFeedback({
        type: 'success',
        message: `Service "${fs.service_name}" is now ${newStatus ? 'ENABLED' : 'DISABLED'}.`,
      });
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: parseApiError(err),
      });
    } finally {
      setActionLoadingId(null);
    }
  };

  if (!isOpen || !facility) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150"
      data-testid="facility-services-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="services-modal-title"
    >
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200/80 w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100/60">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h2 id="services-modal-title" className="text-base font-bold text-slate-800">
                Facility Services Configuration
              </h2>
              <p className="text-xs text-slate-500">
                {facility.facility_name} ({facility.facility_code})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`mx-6 mt-4 p-3 rounded-xl border text-xs font-medium flex items-center justify-between ${
              feedback.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
            data-testid="service-feedback-banner"
            role="status"
          >
            <div className="flex items-center gap-2">
              {feedback.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              )}
              <span>{feedback.message}</span>
            </div>
            <button
              onClick={() => setFeedback(null)}
              className="text-slate-400 hover:text-slate-600 p-0.5 rounded"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Body / Services Table */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-400 space-y-2">
              <RefreshCw className="w-6 h-6 animate-spin text-emerald-600" />
              <p className="text-xs font-semibold">Loading configured services...</p>
            </div>
          ) : services.length === 0 ? (
            <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200 p-4">
              <AlertCircle className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-xs font-bold text-slate-600">No Services Configured</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Standard services have not yet been provisioned for this facility.
              </p>
            </div>
          ) : (
            <div className="border border-slate-200/80 rounded-xl overflow-hidden shadow-2xs" data-testid="services-list">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 border-b border-slate-100 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-4">Service</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-4 text-right">Operational State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {services.map((fs) => {
                    const rowKey = fs.service_code.toLowerCase();
                    return (
                      <tr
                        key={fs.id}
                        className="hover:bg-slate-50/60 transition"
                        data-testid={`service-row-${rowKey}`}
                      >
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-800">{fs.service_name}</div>
                          <div className="font-mono text-[10px] text-slate-400">{fs.service_code}</div>
                        </td>
                        <td className="py-3 px-3">
                          <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                            {fs.service_category}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                              fs.is_available
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : 'bg-rose-50 text-rose-700 border-rose-200'
                            }`}
                            data-testid={`service-status-badge-${rowKey}`}
                          >
                            {fs.is_available ? (
                              <>
                                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                                Available
                              </>
                            ) : (
                              <>
                                <XCircle className="w-3 h-3 text-rose-600" />
                                Disabled
                              </>
                            )}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            type="button"
                            onClick={() => handleToggle(fs)}
                            disabled={actionLoadingId === fs.id}
                            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition shadow-2xs cursor-pointer disabled:opacity-50 ${
                              fs.is_available
                                ? 'bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200'
                                : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                            }`}
                            data-testid={`toggle-service-btn-${rowKey}`}
                            aria-label={`Toggle service ${fs.service_name}`}
                          >
                            <Power className="w-3.5 h-3.5" />
                            {actionLoadingId === fs.id ? 'Updating...' : fs.is_available ? 'Disable' : 'Enable'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs text-slate-500">
          <span>Active services are available for patient queueing and clinical orders.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl border border-slate-300 font-semibold text-slate-700 hover:bg-slate-100 transition shadow-2xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
