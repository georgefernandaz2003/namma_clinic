import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { LabOrder } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  TestTube, CheckCircle2, FileCheck, QrCode, Layers, RefreshCw,
  ChevronLeft, ChevronRight, ArrowRight, Clock, Lock, ShieldAlert,
  Eye, X, CheckCircle, Plus, Edit2, Trash2
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { hasPermission } from '../utils/permissions';

export const Laboratory: React.FC = () => {
  const { activeFacility, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const canCreateTest = Boolean(
    (user?.permissions && user.permissions.includes('lab_test_master.create')) ||
    hasPermission(user?.role, 'lab_test_master.create')
  );
  const canUpdateTest = Boolean(
    (user?.permissions && user.permissions.includes('lab_test_master.update')) ||
    hasPermission(user?.role, 'lab_test_master.update')
  );
  const canDeleteTest = Boolean(
    (user?.permissions && user.permissions.includes('lab_test_master.delete')) ||
    hasPermission(user?.role, 'lab_test_master.delete')
  );

  // Helper for YYYY-MM-DD
  const getTodayStr = () => new Date().toISOString().split('T')[0];
  const initialDate = location.state?.selectedDate || getTodayStr();

  // Date Management State
  const [selectedDate, setSelectedDate] = useState<string>(initialDate);
  const [dateMode, setDateMode] = useState<'DATE' | 'ALL'>('DATE');
  const [activeTab, setActiveTab] = useState<'ALL' | 'ORDERED' | 'SAMPLE_COLLECTED' | 'VERIFIED'>('ALL');

  // Lab Data State
  const [orders, setOrders] = useState<LabOrder[]>([]);
  const [catalogue, setCatalogue] = useState<any[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<LabOrder | null>(null);
  const [viewingReportOrder, setViewingReportOrder] = useState<LabOrder | null>(null);

  // Result Form State
  const [resultVal, setResultVal] = useState('8.4');
  const [resultUnit, setResultUnit] = useState('');
  const [refRange, setRefRange] = useState('');
  const [interpFlag, setInterpFlag] = useState<'NORMAL' | 'HIGH' | 'LOW' | 'CRITICAL'>('HIGH');
  const [notes, setNotes] = useState('Specimen analyzed and verified by Laboratory Technician.');
  const [collectingId, setCollectingId] = useState<number | null>(null);
  const [savingResult, setSavingResult] = useState(false);

  const isToday = selectedDate === getTodayStr();
  const isPast = selectedDate < getTodayStr();

  // Date Navigation Handlers
  const handlePrevDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() - 1);
    setSelectedDate(d.toISOString().split('T')[0]);
    setDateMode('DATE');
  };

  const handleNextDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + 1);
    setSelectedDate(d.toISOString().split('T')[0]);
    setDateMode('DATE');
  };

  const handleSetToday = () => {
    setSelectedDate(getTodayStr());
    setDateMode('DATE');
  };

  const [labSummary, setLabSummary] = useState<any>(null);

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const dateParam = dateMode === 'DATE' ? `&date=${selectedDate}` : '';
      const [orderRes, summaryRes] = await Promise.all([
        api.get(`lab/orders/?facility=${activeFacility.id}${dateParam}`),
        dateMode === 'DATE'
          ? api.get(`dashboard/summary/?facility=${activeFacility.id}&date=${selectedDate}`).catch(() => null)
          : Promise.resolve(null)
      ]);
      setOrders(orderRes.data.results || orderRes.data || []);
      if (summaryRes?.data) setLabSummary(summaryRes.data);
    } catch (e) {
      console.error('Failed to load lab orders', e);
    }
  };

  const loadCatalogue = async () => {
    try {
      const res = await api.get('lab/tests/');
      setCatalogue(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load lab test catalogue', e);
    }
  };

  // Lab Test Master Management State & Handlers
  const [showAddTestModal, setShowAddTestModal] = useState(false);
  const [editingTest, setEditingTest] = useState<any | null>(null);
  const [testFormLoading, setTestFormLoading] = useState(false);
  const [testFormData, setTestFormData] = useState({
    code: '',
    name: '',
    category: 'General Biochemistry',
    reference_range: '',
    unit: ''
  });

  const handleCreateTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canCreateTest) return;
    setTestFormLoading(true);
    try {
      await api.post('lab/tests/', testFormData);
      setShowAddTestModal(false);
      setTestFormData({ code: '', name: '', category: 'General Biochemistry', reference_range: '', unit: '' });
      await loadCatalogue();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create lab test');
    } finally {
      setTestFormLoading(false);
    }
  };

  const handleUpdateTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canUpdateTest || !editingTest) return;
    setTestFormLoading(true);
    try {
      await api.patch(`lab/tests/${editingTest.id}/`, testFormData);
      setEditingTest(null);
      await loadCatalogue();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update lab test');
    } finally {
      setTestFormLoading(false);
    }
  };

  const handleDeleteTest = async (testId: number) => {
    if (!canDeleteTest) return;
    if (!window.confirm('Are you sure you want to delete this test master record?')) return;
    try {
      await api.delete(`lab/tests/${testId}/`);
      await loadCatalogue();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete lab test');
    }
  };

  useEffect(() => {
    loadData();
    loadCatalogue();
  }, [activeFacility, selectedDate, dateMode]);

  const handleOpenResultModal = (order: LabOrder) => {
    setSelectedOrder(order);
    const foundTest = catalogue.find(t => t.id === order.test_master || t.code === order.test_code || t.name === order.test_name);
    if (foundTest) {
      setResultUnit(foundTest.unit || '');
      setRefRange(foundTest.reference_range || '');
      const testNameLower = (order.test_name || '').toLowerCase();
      if (testNameLower.includes('urine') || testNameLower.includes('albumin')) {
        setResultVal('Negative (Normal)');
        setInterpFlag('NORMAL');
        setNotes('Urine specimen analysis negative for protein. Within normal parameters.');
      } else if (testNameLower.includes('glucose') || testNameLower.includes('fbg') || testNameLower.includes('rbg')) {
        setResultVal('95');
        setInterpFlag('NORMAL');
        setNotes('Blood glucose within normal reference limits.');
      } else if (testNameLower.includes('hemoglobin') || testNameLower.includes('hb')) {
        setResultVal('13.8');
        setInterpFlag('NORMAL');
        setNotes('Hemoglobin levels within normal physiological range.');
      } else if (testNameLower.includes('dengue')) {
        setResultVal('Negative');
        setInterpFlag('NORMAL');
        setNotes('Dengue NS1 antigen non-reactive.');
      } else {
        setResultVal(foundTest.reference_range?.split('-')[0]?.trim() || 'Normal');
        setInterpFlag('NORMAL');
        setNotes('Specimen analyzed and verified by Laboratory Technician.');
      }
    } else {
      setResultUnit('mg/dL');
      setRefRange('Normal');
      setResultVal('Normal');
      setInterpFlag('NORMAL');
      setNotes('Verified by Lab Tech.');
    }
  };

  const handleCollectSample = async (order: LabOrder) => {
    setCollectingId(order.id);
    try {
      let sampleType = 'Blood / Serum';
      const nameLower = (order.test_name || '').toLowerCase();
      if (nameLower.includes('urine')) {
        sampleType = 'Urine Specimen';
      } else if (nameLower.includes('sputum')) {
        sampleType = 'Sputum Specimen';
      } else if (nameLower.includes('stool')) {
        sampleType = 'Stool Specimen';
      } else if (nameLower.includes('swab')) {
        sampleType = 'Swab Specimen';
      }

      const barcode = `SMP-2026-${Math.floor(1000 + Math.random() * 9000)}`;
      const res = await api.post(`lab/orders/${order.id}/collect-sample/`, {
        sample_type: sampleType,
        sample_code: barcode
      });
      const generatedCode = res.data?.sample?.sample_code || barcode;
      alert(`Sample collected successfully!\n\nSpecimen Type: ${sampleType}\nBarcode Tag: ${generatedCode}\nOrder: #LAB-${String(order.id).padStart(4, '0')}\nOPD Queue updated to LAB_IN_PROGRESS.`);
      await loadData();
    } catch (e: any) {
      console.error('Failed to collect sample:', e);
      const errMsg = e.response?.data?.error || e.response?.data?.detail || e.message || 'Failed to collect sample.';
      alert(`Failed to collect sample: ${errMsg}`);
    } finally {
      setCollectingId(null);
    }
  };

  const handleSaveResult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;

    setSavingResult(true);
    try {
      await api.post(`lab/orders/${selectedOrder.id}/save-result/`, {
        result_value: resultVal,
        unit: resultUnit,
        reference_range: refRange,
        interpretation_flag: interpFlag,
        notes
      });
      alert(`Lab result verified and pushed to patient EMR timeline for ${selectedOrder.patient_name}!\nOPD Queue updated automatically.`);
      setSelectedOrder(null);
      await loadData();
    } catch (e: any) {
      console.error('Failed to save lab result:', e);
      const errMsg = e.response?.data?.error || e.response?.data?.detail || e.message || 'Failed to save lab result.';
      alert(`Failed to save lab result: ${errMsg}`);
    } finally {
      setSavingResult(false);
    }
  };

  // Authoritative KPI calculations from backend labSummary with table fallback
  const totalOrdersCount = labSummary?.lab_summary?.total_orders ?? labSummary?.laboratory?.total_orders ?? orders.length;
  const samplePendingCount = labSummary?.lab_summary?.ordered ?? labSummary?.laboratory?.ordered ?? labSummary?.laboratory?.pending ?? orders.filter(o => o.status === 'ORDERED').length;
  const resultPendingCount = labSummary?.lab_summary?.sample_collected ?? labSummary?.laboratory?.sample_collected ?? orders.filter(o => o.status === 'SAMPLE_COLLECTED').length;
  const verifiedCount = labSummary?.lab_summary?.verified ?? labSummary?.laboratory?.verified ?? orders.filter(o => o.status === 'VERIFIED').length;

  // Filtered orders for table
  const displayedOrders = activeTab === 'ALL'
    ? orders
    : orders.filter(o => o.status === activeTab);

  const formattedDate = new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Date Management Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <TestTube className="w-6 h-6 text-purple-600" />
            <h1 className="text-xl font-black text-slate-900">
              Diagnostic Laboratory — <span className="text-purple-700">{dateMode === 'ALL' ? 'All Historical Dates' : formattedDate}</span>
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Facility Lab Scope: <span className="font-bold text-slate-800">{activeFacility?.facility_name || 'Select Facility'}</span> • Specimen Lifecycle & OPD Queue Synchronized
          </p>
        </div>

        {/* Date Selector Navigation Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-300">
            <button
              onClick={handlePrevDay}
              title="Previous Day"
              className="p-1.5 rounded-lg text-slate-600 hover:bg-white hover:text-slate-900 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => {
                setSelectedDate(e.target.value);
                setDateMode('DATE');
              }}
              className="bg-transparent text-xs font-bold text-slate-900 px-2 focus:outline-none cursor-pointer"
            />
            <button
              onClick={handleNextDay}
              title="Next Day"
              className="p-1.5 rounded-lg text-slate-600 hover:bg-white hover:text-slate-900 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={handleSetToday}
            className={`px-3 py-2 rounded-xl text-xs font-bold border transition ${
              isToday && dateMode === 'DATE'
                ? 'bg-purple-600 text-white border-purple-600 shadow-sm'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'
            }`}
          >
            Today
          </button>

          <button
            onClick={() => setDateMode(dateMode === 'DATE' ? 'ALL' : 'DATE')}
            className={`px-3 py-2 rounded-xl text-xs font-bold border transition ${
              dateMode === 'ALL'
                ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-300'
            }`}
          >
            {dateMode === 'ALL' ? 'Showing All Dates' : 'View All Dates'}
          </button>

          <button
            onClick={() => {
              loadData();
              loadCatalogue();
            }}
            title="Refresh Orders"
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl border border-slate-300 transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Date Mode Status Banner */}
      <div className={`p-4 rounded-2xl border text-xs flex items-center justify-between shadow-xs ${
        dateMode === 'ALL'
          ? 'bg-indigo-50 border-indigo-300 text-indigo-950'
          : isToday
          ? 'bg-purple-50 border-purple-300 text-purple-950'
          : isPast
          ? 'bg-amber-50 border-amber-300 text-amber-950'
          : 'bg-rose-50 border-rose-300 text-rose-950'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-xl text-white flex items-center justify-center font-black shrink-0 ${
            dateMode === 'ALL' ? 'bg-indigo-600' : isToday ? 'bg-purple-600' : isPast ? 'bg-amber-600' : 'bg-rose-600'
          }`}>
            {dateMode === 'ALL' ? '📑' : isToday ? '🧪' : isPast ? <Lock className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
          </div>
          <div>
            <h2 className="font-bold text-sm">
              {dateMode === 'ALL'
                ? 'All Historical Diagnostic Orders Archive'
                : isToday
                ? 'Operational Diagnostic Laboratory (Live Queue Integrated)'
                : `Historical Diagnostic Records (${formattedDate})`}
            </h2>
            <p className="text-[11px] opacity-90 mt-0.5">
              {dateMode === 'ALL'
                ? 'Displaying all diagnostic orders ever issued across all dates for this facility.'
                : isToday
                ? 'Connected directly with OPD Queue tokens. Sample collection and result verification automatically route patient visits.'
                : 'Showing lab test orders and released reports recorded on this specific date.'}
            </p>
          </div>
        </div>

        <div className="text-right hidden sm:block">
          <span className="text-[10px] uppercase font-bold text-slate-500 block">Date Scope</span>
          <span className="font-black text-xs font-mono">{dateMode === 'ALL' ? 'Full Archive' : selectedDate}</span>
        </div>
      </div>

      {/* 4 KPI Summary Cards for Laboratory */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-slate-500 tracking-wider">Total Diagnostic Tests</p>
          <p className="text-xl font-black text-slate-900 mt-1">{totalOrdersCount}</p>
        </div>
        <div className="bg-white p-3.5 rounded-2xl border border-purple-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-purple-700 tracking-wider">Step 1: Sample Pending</p>
          <p className="text-xl font-black text-purple-800 mt-1">{samplePendingCount}</p>
        </div>
        <div className="bg-white p-3.5 rounded-2xl border border-blue-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-blue-700 tracking-wider">Step 2: Result Entry Pending</p>
          <p className="text-xl font-black text-blue-800 mt-1">{resultPendingCount}</p>
        </div>
        <div className="bg-white p-3.5 rounded-2xl border border-emerald-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-emerald-700 tracking-wider">Step 3: Verified & Synced</p>
          <p className="text-xl font-black text-emerald-800 mt-1">{verifiedCount}</p>
        </div>
      </div>

      {/* 6-Step Specimen Workflow Visual Pipeline */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-3">
        <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2">
          <Layers className="w-4 h-4 text-purple-600" />
          6-Step Specimen Diagnostic Lifecycle Pipeline
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-center text-xs">
          <div className="p-2.5 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-purple-600 uppercase">Step 1</span>
            <span className="font-bold block text-xs">1. Doctor Order</span>
            <span className="text-[10px] text-purple-700 block">Requested in OPD</span>
          </div>
          <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-blue-600 uppercase">Step 2</span>
            <span className="font-bold block text-xs">2. Sample Collect</span>
            <span className="text-[10px] text-blue-700 block">Blood/Urine/Sputum</span>
          </div>
          <div className="p-2.5 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-indigo-600 uppercase">Step 3</span>
            <span className="font-bold block text-xs">3. Barcode Tag</span>
            <span className="text-[10px] text-indigo-700 block">SMP-2026 Code</span>
          </div>
          <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-amber-600 uppercase">Step 4</span>
            <span className="font-bold block text-xs">4. Enter Result</span>
            <span className="text-[10px] text-amber-700 block">Value & Unit</span>
          </div>
          <div className="p-2.5 rounded-xl bg-teal-50 border border-teal-200 text-teal-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-teal-600 uppercase">Step 5</span>
            <span className="font-bold block text-xs">5. Verify</span>
            <span className="text-[10px] text-teal-700 block">Tech Sign-Off</span>
          </div>
          <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-emerald-600 uppercase">Step 6</span>
            <span className="font-bold block text-xs">6. EMR Sync</span>
            <span className="text-[10px] text-emerald-700 block">Live in Profile</span>
          </div>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="bg-white p-3 rounded-2xl border border-slate-200 flex flex-wrap items-center gap-2 shadow-xs text-xs font-bold">
        {[
          { id: 'ALL', label: 'All Orders', count: totalOrdersCount },
          { id: 'ORDERED', label: '1. Specimen Pending', count: samplePendingCount },
          { id: 'SAMPLE_COLLECTED', label: '2. Result Pending', count: resultPendingCount },
          { id: 'VERIFIED', label: '3. Verified & Synced', count: verifiedCount }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 ${
              activeTab === tab.id
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
          >
            <span>{tab.label}</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold ${
              activeTab === tab.id ? 'bg-slate-700 text-white' : 'bg-slate-200 text-slate-800'
            }`}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Main Grid: Orders Queue & Complete 14-Test Catalogue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lab Orders Queue Table */}
        <div className="lg:col-span-2 glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs space-y-0">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h2 className="text-sm font-bold text-slate-900">
              Laboratory Orders Queue — {activeTab.replace('_', ' ')} ({displayedOrders.length} Records)
            </h2>
            <button onClick={loadData} className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100">
              Refresh
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-3.5">Order ID</th>
                  <th className="p-3.5">Token & Patient</th>
                  <th className="p-3.5">Diagnostic Test</th>
                  <th className="p-3.5">Specimen & Barcode</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Result</th>
                  <th className="p-3.5">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {displayedOrders.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400 font-medium">
                      No diagnostic test orders found matching the selected filter ({activeTab}) for {dateMode === 'ALL' ? 'any date' : formattedDate}.
                    </td>
                  </tr>
                ) : (
                  displayedOrders.map((o) => (
                    <tr key={o.id} className="hover:bg-slate-50/80 transition">
                      <td className="p-3.5 font-mono text-purple-700 font-bold">#LAB-{String(o.id).padStart(4, '0')}</td>
                      
                      {/* Patient & OPD Token Connection */}
                      <td className="p-3.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-slate-900">{o.patient_name}</span>
                          {o.token_number && (
                            <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-purple-100 text-purple-800 border border-purple-200">
                              Token #{o.token_number}
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono block mt-0.5">{o.patient_mobile}</span>
                      </td>

                      {/* Test Name & Code */}
                      <td className="p-3.5">
                        <span className="text-slate-900 font-semibold block">{o.test_name}</span>
                        {o.test_code && (
                          <span className="text-[10px] font-mono text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded border border-purple-100 inline-block mt-0.5">
                            {o.test_code}
                          </span>
                        )}
                      </td>

                      {/* Barcode & Specimen */}
                      <td className="p-3.5">
                        {(o.sample_details?.sample_code || o.sample?.sample_code) ? (
                          <div className="space-y-0.5">
                            <span className="font-mono text-[10px] font-bold bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200 inline-flex items-center gap-1">
                              <QrCode className="w-3 h-3 text-purple-600" />
                              {o.sample_details?.sample_code || o.sample?.sample_code}
                            </span>
                            <span className="text-[10px] text-slate-500 block">
                              {o.sample_details?.sample_type || o.sample?.sample_type || 'Blood'}
                            </span>
                          </div>
                        ) : (
                          <span className="text-[10px] text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                            Specimen Pending
                          </span>
                        )}
                      </td>

                      {/* Status Badge */}
                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          o.status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800 border-emerald-300' :
                          o.status === 'SAMPLE_COLLECTED' ? 'bg-blue-100 text-blue-800 border-blue-300' :
                          'bg-amber-100 text-amber-900 border-amber-300'
                        }`}>
                          {o.status.replace(/_/g, ' ')}
                        </span>
                      </td>

                      {/* Result Value */}
                      <td className="p-3.5 font-mono text-slate-800 font-semibold">
                        {o.result ? (
                          <div className="space-y-0.5">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold inline-block ${
                              o.result.interpretation_flag === 'HIGH' || o.result.interpretation_flag === 'CRITICAL'
                                ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                : o.result.interpretation_flag === 'LOW'
                                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                : 'bg-slate-100 text-slate-800'
                            }`}>
                              {o.result.result_value} {o.result.unit}
                            </span>
                            <span className="text-[10px] text-slate-400 block font-normal">
                              Ref: {o.result.reference_range || 'Normal'}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 text-[10px]">Awaiting Result</span>
                        )}
                      </td>

                      {/* Action Buttons */}
                      <td className="p-3.5 space-x-2">
                        {o.status === 'ORDERED' && (
                          <button
                            onClick={() => handleCollectSample(o)}
                            disabled={collectingId === o.id}
                            className="px-2.5 py-1 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-300 text-white font-bold rounded-lg text-[10px] shadow-xs inline-flex items-center gap-1 transition cursor-pointer"
                          >
                            {collectingId === o.id ? (
                              <>
                                <RefreshCw className="w-3 h-3 animate-spin" />
                                <span>Collecting...</span>
                              </>
                            ) : (
                              <>
                                <span>Collect Sample</span>
                                <ArrowRight className="w-3 h-3" />
                              </>
                            )}
                          </button>
                        )}

                        {o.status === 'SAMPLE_COLLECTED' && (
                          <button
                            onClick={() => handleOpenResultModal(o)}
                            className="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg text-[10px] shadow-xs inline-flex items-center gap-1 transition cursor-pointer"
                          >
                            <span>Enter Result</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        )}

                        {o.status === 'VERIFIED' && (
                          <button
                            onClick={() => setViewingReportOrder(o)}
                            className="px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100 font-bold rounded-lg text-[10px] inline-flex items-center gap-1 transition cursor-pointer"
                          >
                            <Eye className="w-3 h-3 text-emerald-600" />
                            <span>View Report</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Complete Approved 14-Test Catalogue Panel */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-xs">
          <div className="border-b border-slate-100 pb-2 flex justify-between items-center">
            <h2 className="text-xs font-bold uppercase tracking-wider text-purple-900 flex items-center gap-1.5">
              <TestTube className="w-4 h-4 text-purple-600" />
              Approved 14 Diagnostic Test Catalogue
            </h2>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-mono text-[10px] font-bold">
                {catalogue.length} Tests
              </span>
              {canCreateTest && (
                <button
                  type="button"
                  onClick={() => {
                    setTestFormData({ code: '', name: '', category: 'General Biochemistry', reference_range: '', unit: '' });
                    setShowAddTestModal(true);
                  }}
                  className="px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white font-bold text-[10px] rounded-lg transition flex items-center gap-1 shadow-2xs cursor-pointer"
                >
                  <Plus className="w-3 h-3" />
                  Add Test
                </button>
              )}
            </div>
          </div>

          <p className="text-[11px] text-slate-500 font-medium">
            Government-approved essential point-of-care and laboratory test list for Urban Health & Wellness Clinics / Namma Clinics.
          </p>

          <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1 text-xs">
            {catalogue.map((test) => (
              <div
                key={test.id}
                className="p-3 rounded-xl border border-slate-200 bg-slate-50/70 space-y-1 hover:bg-white hover:border-purple-300 transition shadow-2xs"
              >
                <div className="flex justify-between items-start">
                  <span className="font-bold text-slate-900 text-xs">{test.name}</span>
                  <div className="flex items-center gap-1">
                    <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-100 text-purple-800">
                      {test.code}
                    </span>
                    {canUpdateTest && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditingTest(test);
                          setTestFormData({
                            code: test.code,
                            name: test.name,
                            category: test.category || 'General Biochemistry',
                            reference_range: test.reference_range || '',
                            unit: test.unit || ''
                          });
                        }}
                        className="p-1 text-slate-400 hover:text-purple-600 rounded transition cursor-pointer"
                        title="Edit Test Master"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                    {canDeleteTest && (
                      <button
                        type="button"
                        onClick={() => handleDeleteTest(test.id)}
                        className="p-1 text-slate-400 hover:text-rose-600 rounded transition cursor-pointer"
                        title="Delete Test Master"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
                <div className="flex justify-between items-center text-[10px] text-slate-500 pt-0.5">
                  <span className="font-semibold text-slate-700">Category: {test.category}</span>
                  <span className="font-mono">Ref: {test.reference_range}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Result Verification Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-md space-y-4 shadow-xl text-xs">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-purple-600" />
                Enter & Verify Result for {selectedOrder.patient_name}
              </h2>
              <button onClick={() => setSelectedOrder(null)} className="text-slate-400 font-bold hover:text-slate-700 cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleSaveResult} className="space-y-3">
              <div className="bg-purple-50 p-3 rounded-xl border border-purple-100 space-y-1 font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="text-purple-800 font-bold">Test: {selectedOrder.test_name}</span>
                  <span className="text-purple-600">ID: #LAB-{selectedOrder.id}</span>
                </div>
                <div className="text-purple-700 flex items-center gap-1">
                  <QrCode className="w-3 h-3 text-purple-600" />
                  Specimen Code: {selectedOrder.sample_details?.sample_code || selectedOrder.sample?.sample_code || 'SMP-2026-LOGGED'}
                </div>
                {selectedOrder.token_number && (
                  <div className="text-purple-900 font-bold">
                    Connected OPD Token: #{selectedOrder.token_number}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Result Value *</label>
                  <input
                    type="text"
                    value={resultVal}
                    onChange={(e) => setResultVal(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600 font-mono font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Unit</label>
                  <input
                    type="text"
                    value={resultUnit}
                    onChange={(e) => setResultUnit(e.target.value)}
                    placeholder="e.g. mg/dL, %"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600 font-mono font-bold"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Reference Range</label>
                <input
                  type="text"
                  value={refRange}
                  onChange={(e) => setRefRange(e.target.value)}
                  placeholder="e.g. 70 - 100 mg/dL"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600 font-mono text-[11px]"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Interpretation Flag</label>
                <select
                  value={interpFlag}
                  onChange={(e) => setInterpFlag(e.target.value as any)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600 font-medium"
                >
                  <option value="NORMAL">Normal / Within Reference Range</option>
                  <option value="HIGH">High / Above Reference Limit</option>
                  <option value="LOW">Low / Below Reference Limit</option>
                  <option value="CRITICAL">Critical Alert Value 🚨</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Technician Verification Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600"
                />
              </div>

              <button
                type="submit"
                disabled={savingResult}
                className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-300 text-white font-bold rounded-xl shadow-md transition cursor-pointer flex items-center justify-center gap-2"
              >
                {savingResult ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Verifying and Syncing EMR...</span>
                  </>
                ) : (
                  <span>Verify Result & Release to Patient EMR</span>
                )}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* View Diagnostic Report Detail Modal */}
      {viewingReportOrder && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl text-xs">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                Verified Diagnostic Test Report
              </h2>
              <button
                onClick={() => setViewingReportOrder(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="grid grid-cols-2 gap-2 text-slate-800">
                <p><span className="font-bold text-slate-900">Order ID:</span> #LAB-{String(viewingReportOrder.id).padStart(4, '0')}</p>
                <p><span className="font-bold text-slate-900">OPD Token:</span> #{viewingReportOrder.token_number || 'N/A'}</p>
                <p><span className="font-bold text-slate-900">Patient:</span> {viewingReportOrder.patient_name}</p>
                <p><span className="font-bold text-slate-900">Mobile:</span> {viewingReportOrder.patient_mobile}</p>
                <p><span className="font-bold text-slate-900">Test:</span> {viewingReportOrder.test_name}</p>
                <p><span className="font-bold text-slate-900">Code:</span> {viewingReportOrder.test_code}</p>
                <p><span className="font-bold text-slate-900">Specimen Code:</span> {viewingReportOrder.sample_details?.sample_code || viewingReportOrder.sample?.sample_code || 'SMP-2026'}</p>
                <p><span className="font-bold text-slate-900">Specimen Type:</span> {viewingReportOrder.sample_details?.sample_type || viewingReportOrder.sample?.sample_type || 'Blood'}</p>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/60 space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-900 text-sm">Report Result:</span>
                <span className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                  viewingReportOrder.result?.interpretation_flag === 'HIGH' || viewingReportOrder.result?.interpretation_flag === 'CRITICAL'
                    ? 'bg-rose-100 text-rose-800 border border-rose-200'
                    : viewingReportOrder.result?.interpretation_flag === 'LOW'
                    ? 'bg-amber-100 text-amber-800 border border-amber-200'
                    : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                }`}>
                  {viewingReportOrder.result?.interpretation_flag}
                </span>
              </div>
              <p className="text-xl font-black font-mono text-slate-900">
                {viewingReportOrder.result?.result_value} {viewingReportOrder.result?.unit}
              </p>
              <p className="text-slate-600 text-[11px]">
                Reference Range: <span className="font-mono font-bold text-slate-800">{viewingReportOrder.result?.reference_range || 'Normal'}</span>
              </p>
              {viewingReportOrder.result?.notes && (
                <p className="text-slate-700 italic border-t border-emerald-200/60 pt-1 mt-1">
                  &ldquo;{viewingReportOrder.result.notes}&rdquo;
                </p>
              )}
              <p className="text-[10px] text-slate-500 pt-1">
                Verified by: <span className="font-bold text-slate-700">{viewingReportOrder.result?.verified_by_name || 'Laboratory Staff'}</span>
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setViewingReportOrder(null)}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl text-xs cursor-pointer"
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Test Master Modal */}
      {showAddTestModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreateTest}
            className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-md space-y-4 shadow-xl text-xs"
          >
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Plus className="w-4 h-4 text-purple-600" />
                Add Diagnostic Test to Master Catalogue
              </h2>
              <button
                type="button"
                onClick={() => setShowAddTestModal(false)}
                className="text-slate-400 font-bold hover:text-slate-700 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Test Code *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. LBN-015"
                  value={testFormData.code}
                  onChange={(e) => setTestFormData({ ...testFormData, code: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500 font-mono font-bold"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Test Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Serum Creatinine"
                  value={testFormData.name}
                  onChange={(e) => setTestFormData({ ...testFormData, name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Category</label>
                <input
                  type="text"
                  placeholder="e.g. Renal Profile / Biochemistry"
                  value={testFormData.category}
                  onChange={(e) => setTestFormData({ ...testFormData, category: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Reference Range</label>
                  <input
                    type="text"
                    placeholder="e.g. 0.7 - 1.3 mg/dL"
                    value={testFormData.reference_range}
                    onChange={(e) => setTestFormData({ ...testFormData, reference_range: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Unit</label>
                  <input
                    type="text"
                    placeholder="e.g. mg/dL"
                    value={testFormData.unit}
                    onChange={(e) => setTestFormData({ ...testFormData, unit: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500 font-mono"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowAddTestModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl text-xs cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={testFormLoading}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl text-xs shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{testFormLoading ? 'Saving...' : 'Add Test'}</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Test Master Modal */}
      {editingTest && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleUpdateTest}
            className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-md space-y-4 shadow-xl text-xs"
          >
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-purple-600" />
                Edit Diagnostic Test Master
              </h2>
              <button
                type="button"
                onClick={() => setEditingTest(null)}
                className="text-slate-400 font-bold hover:text-slate-700 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Test Code *</label>
                <input
                  type="text"
                  required
                  value={testFormData.code}
                  onChange={(e) => setTestFormData({ ...testFormData, code: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500 font-mono font-bold"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Test Name *</label>
                <input
                  type="text"
                  required
                  value={testFormData.name}
                  onChange={(e) => setTestFormData({ ...testFormData, name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Category</label>
                <input
                  type="text"
                  value={testFormData.category}
                  onChange={(e) => setTestFormData({ ...testFormData, category: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Reference Range</label>
                  <input
                    type="text"
                    value={testFormData.reference_range}
                    onChange={(e) => setTestFormData({ ...testFormData, reference_range: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Unit</label>
                  <input
                    type="text"
                    value={testFormData.unit}
                    onChange={(e) => setTestFormData({ ...testFormData, unit: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs outline-none focus:border-purple-500 font-mono"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingTest(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl text-xs cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={testFormLoading}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl text-xs shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>{testFormLoading ? 'Saving...' : 'Update Test'}</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
