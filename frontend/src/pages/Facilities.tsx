import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import type { Facility } from '../types';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { FacilityModal } from '../components/facilities/FacilityModal';
import { Building2, Search, Plus, Pencil, CheckCircle2, XCircle, AlertCircle, Phone, Clock, Users, X, UserCheck, UserPlus } from 'lucide-react';

export const Facilities: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const isDHO = Boolean(
    user?.role === 'DISTRICT_OFFICER' ||
    user?.roles?.includes('DISTRICT_OFFICER') ||
    user?.is_superuser
  );

  const loadData = useCallback(async () => {
    try {
      const res = await api.get('facilities/');
      setFacilities(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load facilities', e);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleOpenCreate = () => {
    setSelectedFacility(null);
    setModalMode('create');
    setIsModalOpen(true);
    setFeedback(null);
  };

  const handleOpenEdit = (f: Facility) => {
    setSelectedFacility(f);
    setModalMode('edit');
    setIsModalOpen(true);
    setFeedback(null);
  };

  const handleSaveFacility = async (payload: Partial<Facility>) => {
    if (modalMode === 'create') {
      await api.post('facilities/', payload);
      setFeedback({
        type: 'success',
        text: `Facility "${payload.facility_name}" has been successfully onboarded into the registry.`,
      });
    } else if (modalMode === 'edit' && selectedFacility) {
      await api.patch(`facilities/${selectedFacility.id}/`, payload);
      setFeedback({
        type: 'success',
        text: `Facility "${payload.facility_name || selectedFacility.facility_name}" details and operational status updated.`,
      });
    }
    await loadData();
  };

  const filtered = facilities.filter((f) => {
    const matchesSearch =
      f.facility_name.toLowerCase().includes(search.toLowerCase()) ||
      f.facility_code.toLowerCase().includes(search.toLowerCase()) ||
      (f.district_name && f.district_name.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus =
      statusFilter === 'ALL' ||
      (statusFilter === 'ACTIVE' && (f.status === 'ACTIVE' || !f.status)) ||
      (statusFilter === 'INACTIVE' && f.status === 'INACTIVE');

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-teal-600" />
            Healthcare Facilities Master Registry
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Database-driven registry of Main Hospitals, UPHCs, Namma Clinics, Rural Clinics & Satellites
            {user?.district_name ? ` • District: ${user.district_name}` : ''}
          </p>
        </div>

        {/* DHO-Only Action Button */}
        {isDHO && (
          <button
            onClick={handleOpenCreate}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold shadow-xs hover:shadow-md transition active:scale-98"
            data-testid="onboard-facility-btn"
          >
            <Plus className="w-4 h-4" />
            Onboard New Facility
          </button>
        )}
      </div>

      {/* Success / Error Feedback Alert */}
      {feedback && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs font-semibold ${
            feedback.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
          role="status"
          data-testid="facility-feedback-banner"
        >
          <div className="flex items-center gap-2">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{feedback.text}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
            aria-label="Dismiss message"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search & Status Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="glass-panel p-3 rounded-xl border border-slate-200 bg-white flex items-center gap-3 shadow-xs flex-1">
          <Search className="w-5 h-5 text-slate-400 shrink-0" />
          <input
            type="text"
            placeholder="Filter facilities by Code, Name, District..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-transparent text-sm text-slate-900 placeholder-slate-400 focus:outline-none font-medium"
            data-testid="search-facilities-input"
          />
        </div>

        <div className="flex items-center bg-white p-1 rounded-xl border border-slate-200 shadow-xs">
          {(['ALL', 'ACTIVE', 'INACTIVE'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setStatusFilter(filter)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                statusFilter === filter
                  ? 'bg-teal-50 text-teal-700 border border-teal-200 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
              data-testid={`filter-${filter.toLowerCase()}-btn`}
            >
              {filter === 'ALL' ? 'All Facilities' : filter === 'ACTIVE' ? 'Active' : 'Inactive'}
            </button>
          ))}
        </div>
      </div>

      {/* Facilities Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="facilities-grid">
        {filtered.map((f) => (
          <div
            key={f.id}
            className={`glass-card p-5 rounded-2xl border bg-white space-y-3 shadow-xs transition hover:shadow-md ${
              f.status === 'INACTIVE' ? 'border-slate-300 opacity-85 bg-slate-50/50' : 'border-slate-200'
            }`}
            data-testid={`facility-card-${f.facility_code}`}
          >
            <div className="flex justify-between items-start gap-2">
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                    {f.facility_type.replace('_', ' ')}
                  </span>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border inline-flex items-center gap-1 ${
                      f.status === 'ACTIVE' || !f.status
                        ? 'bg-teal-50 text-teal-700 border-teal-200'
                        : 'bg-rose-50 text-rose-700 border-rose-200'
                    }`}
                    data-testid={`facility-status-badge-${f.facility_code}`}
                  >
                    {f.status === 'ACTIVE' || !f.status ? (
                      <CheckCircle2 className="w-3 h-3 text-teal-600" />
                    ) : (
                      <XCircle className="w-3 h-3 text-rose-600" />
                    )}
                    {f.status || 'ACTIVE'}
                  </span>
                </div>
                <h3 className="font-bold text-slate-900 text-sm mt-1">{f.facility_name}</h3>
                <p className="text-[11px] text-slate-500 font-semibold">{f.district_name || 'BBMP Central'}</p>
                <div className="pt-1">
                  {f.has_hospital_admin ? (
                    <span
                      className="text-[10px] font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded inline-flex items-center gap-1"
                      data-testid={`facility-admin-badge-${f.facility_code}`}
                    >
                      <UserCheck className="w-3 h-3 text-emerald-600" />
                      Admin: <strong className="text-emerald-950 font-bold">{f.hospital_admin_name || 'Assigned'}</strong>
                    </span>
                  ) : (
                    <span
                      className="text-[10px] font-semibold text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded inline-flex items-center gap-1"
                      data-testid={`facility-unassigned-admin-badge-${f.facility_code}`}
                    >
                      <AlertCircle className="w-3 h-3 text-amber-600" />
                      No Administrator Assigned
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col items-end gap-2 shrink-0">
                <span className="text-[10px] font-mono text-slate-400 font-semibold">{f.facility_code}</span>
                <div className="flex items-center gap-1.5 flex-wrap justify-end">
                  {isDHO && !f.has_hospital_admin && (
                    <button
                      onClick={() => navigate(`/admin/staff?facilityId=${f.id}&appointAdmin=true`)}
                      className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 inline-flex items-center gap-1 transition shadow-2xs"
                      data-testid={`appoint-admin-btn-${f.facility_code}`}
                      aria-label={`Appoint Administrator for ${f.facility_name}`}
                    >
                      <UserPlus className="w-3.5 h-3.5 text-indigo-600" />
                      Appoint Admin
                    </button>
                  )}
                  {isDHO && (
                    <button
                      onClick={() => handleOpenEdit(f)}
                      className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 inline-flex items-center gap-1 transition"
                      data-testid={`edit-facility-btn-${f.facility_code}`}
                      aria-label={`Edit ${f.facility_name}`}
                    >
                      <Pencil className="w-3.5 h-3.5 text-slate-500" />
                      Edit
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-700 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
              <div>
                <span className="text-slate-500 block font-semibold">Population Served</span>
                <span className="font-bold text-emerald-700">{(f.population_served || 0).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-semibold">Vulnerable Target</span>
                <span className="font-bold text-amber-700">{(f.vulnerable_population || 0).toLocaleString()}</span>
              </div>
            </div>

            <div className="text-[11px] text-slate-600 space-y-1">
              {f.phone && (
                <p className="flex items-center gap-1.5 text-slate-500">
                  <Phone className="w-3 h-3 text-slate-400 shrink-0" />
                  <span>{f.phone}</span>
                </p>
              )}
              <p className="flex items-center gap-1.5 text-slate-500">
                <Clock className="w-3 h-3 text-slate-400 shrink-0" />
                <span>{f.opening_time || '09:00 AM'} - {f.closing_time || '04:30 PM'}</span>
              </p>
              {f.address && (
                <p className="text-slate-500 truncate" title={f.address}>
                  <strong>Location:</strong> {f.address}
                </p>
              )}
              {f.services && (
                <p className="line-clamp-2 text-slate-600 text-[10px]">
                  <strong>Services:</strong> {f.services}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 bg-white rounded-2xl border border-slate-200 p-6 space-y-2">
          <Building2 className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="text-sm font-bold text-slate-700">No Facilities Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            No healthcare facilities matched the current search or status filter criteria.
          </p>
        </div>
      )}

      {/* Onboard / Edit Facility Modal */}
      <FacilityModal
        isOpen={isModalOpen}
        mode={modalMode}
        initialData={selectedFacility}
        districtName={user?.district_name || 'Bengaluru Urban'}
        districtId={user?.assigned_district}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveFacility}
      />
    </div>
  );
};
