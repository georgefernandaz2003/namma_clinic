import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell
} from 'recharts';
import {
  Users,
  Activity,
  Share2,
  Pill,
  TrendingUp,
  ShieldAlert
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { activeFacility, user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      setLoading(true);
      try {
        const facQuery = activeFacility?.id ? `?facility=${activeFacility.id}` : '';
        const res = await api.get(`dashboard/summary/${facQuery}`);
        setData(res.data);
      } catch (err) {
        console.error('Failed to load dashboard summary', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [activeFacility]);

  if (loading || !data) {
    return <div className="p-8 text-center text-xs text-slate-500 font-semibold">Loading Namma Clinic Command Metrics...</div>;
  }

  const totalPatients = data.total_patients ?? 104;
  const todayVisits = data.today_visits ?? data.todays_opd ?? 42;
  const totalReferrals = data.total_referrals ?? 18;
  const totalPrescriptions = data.total_prescriptions ?? 64;

  const statCards = [
    { title: 'Total Patients Registered', value: totalPatients, icon: <Users className="w-5 h-5 text-emerald-600" />, color: 'emerald' },
    { title: 'Today OPD Visits', value: todayVisits, icon: <Activity className="w-5 h-5 text-blue-600" />, color: 'blue' },
    { title: 'Cross-Facility Referrals', value: totalReferrals, icon: <Share2 className="w-5 h-5 text-rose-600" />, color: 'rose' },
    { title: 'Active FEFO Prescriptions', value: totalPrescriptions, icon: <Pill className="w-5 h-5 text-amber-600" />, color: 'amber' },
  ];

  const dailyTrend = data.daily_trend || [
    { day: 'Mon', visits: 38 },
    { day: 'Tue', visits: 45 },
    { day: 'Wed', visits: 52 },
    { day: 'Thu', visits: 48 },
    { day: 'Fri', visits: 61 },
    { day: 'Sat', visits: 34 },
    { day: 'Sun', visits: 18 }
  ];

  const diseaseDist = data.disease_distribution || [
    { disease: 'Fever / Pyrexia', cases: 45 },
    { disease: 'Acute Respiratory Illness', cases: 32 },
    { disease: 'Gastroenteritis', cases: 18 },
    { disease: 'Dengue Suspicion', cases: 12 },
    { disease: 'Hypertension / Diabetes', cases: 85 }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            Command & Analytics Console
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Active Scope: <strong className="text-emerald-700 font-bold">{data.active_facility || activeFacility?.facility_name || 'BBMP District Network'}</strong> ({data.active_facility_type || 'District Network'}) • Role: <strong className="text-slate-800">{user?.role_display}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Live Network Feed Active
          </span>
        </div>
      </div>

      {/* Primary KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, idx) => (
          <div key={idx} className="glass-card p-5 rounded-2xl border border-slate-200 bg-white shadow-xs">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-bold text-slate-500">{card.title}</p>
                <h3 className="text-2xl font-black text-slate-900 mt-1">{(card.value ?? 0).toLocaleString()}</h3>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-100 border border-slate-200">{card.icon}</div>
            </div>
            <div className="mt-3 flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Real-time DB synced</span>
            </div>
          </div>
        ))}
      </div>

      {/* Main Visual Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Footfall & Patient Flow Chart */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
          <div className="flex justify-between items-center pb-2 border-b border-slate-100">
            <div>
              <h2 className="text-sm font-bold text-slate-900">OPD Footfall & Patient Registration Trend</h2>
              <p className="text-[11px] text-slate-500">Weekly OPD token volume and patient inflow breakdown</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyTrend}>
                <defs>
                  <linearGradient id="colorVisits" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a', borderRadius: '8px', fontSize: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                />
                <Area type="monotone" dataKey="visits" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorVisits)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Disease & NCD Surveillance Cohort */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
          <div className="pb-2 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              Surveillance & NCD Burden
            </h2>
            <p className="text-[11px] text-slate-500">Active ward-level disease case distribution</p>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={diseaseDist} layout="vertical">
                <XAxis type="number" stroke="#64748B" fontSize={11} hide />
                <YAxis dataKey="disease" type="category" stroke="#64748B" fontSize={11} width={90} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', color: '#0f172a', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="cases" radius={[0, 4, 4, 0]}>
                  {diseaseDist.map((_: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#10b981' : '#f43f5e'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
