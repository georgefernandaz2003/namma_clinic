import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { DistrictOfficerDashboard } from '../components/dashboards/DistrictOfficerDashboard';
import { HospitalAdminDashboard } from '../components/dashboards/HospitalAdminDashboard';
import { DoctorDashboard } from '../components/dashboards/DoctorDashboard';
import { NurseDashboard } from '../components/dashboards/NurseDashboard';
import { LabTechnicianDashboard } from '../components/dashboards/LabTechnicianDashboard';
import { PharmacistDashboard } from '../components/dashboards/PharmacistDashboard';
import { Calendar, ChevronLeft, ChevronRight, Lock, RotateCcw } from 'lucide-react';
import { getHumanRoleLabel } from '../utils/permissions';

export const Dashboard: React.FC = () => {
  const { activeFacility, user } = useAuth();
  
  // OPD Date Selector state (YYYY-MM-DD format)
  const getTodayStr = () => new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState<string>(getTodayStr());
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const isToday = selectedDate === getTodayStr();

  const fetchDashboardSummary = async () => {
    setLoading(true);
    try {
      const facQuery = activeFacility?.id ? `&facility=${activeFacility.id}` : '';
      const res = await api.get(`dashboard/summary/?date=${selectedDate}${facQuery}`);
      setSummary(res.data);
    } catch (err) {
      console.error('Failed to load dashboard summary', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardSummary();
  }, [activeFacility, selectedDate]);

  // Date Navigation Handlers
  const handlePrevDate = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() - 1);
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const handleNextDate = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + 1);
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const handleTodayClick = () => {
    setSelectedDate(getTodayStr());
  };

  if (loading && !summary) {
    return (
      <div className="p-12 text-center text-xs text-slate-500 font-semibold space-y-2">
        <div className="w-8 h-8 rounded-full bg-emerald-600 border border-emerald-400 animate-spin mx-auto" />
        <p>Loading Namma Clinic {getHumanRoleLabel(user?.role)} Dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Date Selector Header Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center font-bold">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">OPD Queue & Operational Date</h2>
            <p className="text-xs text-slate-500">
              Identity: <strong className="text-slate-800">{summary?.active_facility || 'District Network'}</strong> • <strong className="text-emerald-700 font-bold">{selectedDate}</strong>
            </p>
          </div>
        </div>

        {/* Date Selector Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevDate}
            className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
            title="Previous Day"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <button
            onClick={handleTodayClick}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
              isToday
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
          >
            Today
          </button>

          <button
            onClick={handleNextDate}
            className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
            title="Next Day"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <div className="relative">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => e.target.value && setSelectedDate(e.target.value)}
              className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 font-bold focus:outline-none focus:border-emerald-600 cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Historical Date Read-Only Banner */}
      {!isToday && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center gap-3 text-amber-900 shadow-xs">
          <Lock className="w-4 h-4 text-amber-700 shrink-0" />
          <p className="text-xs font-semibold">
            Viewing Historical OPD Date (<strong className="font-bold">{selectedDate}</strong>). Operational queues and vitals status modifications are read-only for historical records.
          </p>
        </div>
      )}

      {/* Automated Dashboard Dispatcher based on user.role */}
      {(() => {
        switch (user?.role) {
          case 'DISTRICT_OFFICER':
            return <DistrictOfficerDashboard summary={summary} date={selectedDate} isToday={isToday} />;
          case 'HOSPITAL_ADMIN':
            return <HospitalAdminDashboard summary={summary} date={selectedDate} isToday={isToday} />;
          case 'DOCTOR':
            return <DoctorDashboard summary={summary} date={selectedDate} isToday={isToday} />;
          case 'NURSE':
            return <NurseDashboard summary={summary} date={selectedDate} isToday={isToday} />;
          case 'LAB_TECHNICIAN':
            return <LabTechnicianDashboard summary={summary} date={selectedDate} isToday={isToday} />;
          case 'PHARMACIST':
            return <PharmacistDashboard summary={summary} date={selectedDate} isToday={isToday} />;
          default:
            return <DoctorDashboard summary={summary} date={selectedDate} isToday={isToday} />;
        }
      })()}
    </div>
  );
};
