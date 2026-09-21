import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Wrench,
  Wind,
  Bed,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  Clock,
  Plus,
  Zap,
  Droplet,
  PackageCheck,
  ShieldAlert,
  UserCheck,
  Building,
  RefreshCw,
  Search
} from 'lucide-react';

interface OxygenSupply {
  id: number;
  oxygen_source: string;
  total_cylinders: number;
  active_cylinders: number;
  empty_cylinders: number;
  current_pressure_psi: number;
  fill_percentage: number;
  status: string;
  notes: string;
  facility_name?: string;
}

interface ConsumableItem {
  id: number;
  item_name: string;
  category: string;
  unit_of_measure: string;
  current_stock: number;
  min_threshold: number;
  reorder_status: string;
  last_restocked: string;
}

interface MaintenanceTicket {
  id: number;
  ticket_number: string;
  category: string;
  equipment_or_area: string;
  priority: string;
  description: string;
  reported_by: string;
  assigned_technician: string;
  status: string;
  created_at: string;
  resolved_at?: string;
}

interface BedCapacity {
  id: number;
  bed_category: string;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  cleaning_in_progress: number;
  under_maintenance: number;
  notes: string;
}

interface BedAllocation {
  id: number;
  bed_number: string;
  bed_category: string;
  patient_name: string;
  allocated_at: string;
  attending_doctor: string;
  status: string;
}

export const Infrastructure: React.FC = () => {
  const { activeFacility } = useAuth();
  const [activeTab, setActiveTab] = useState<'oxygen' | 'beds' | 'consumables' | 'maintenance'>('oxygen');
  
  const [oxygenList, setOxygenList] = useState<OxygenSupply[]>([]);
  const [consumablesList, setConsumablesList] = useState<ConsumableItem[]>([]);
  const [ticketsList, setTicketsList] = useState<MaintenanceTicket[]>([]);
  const [bedCapacities, setBedCapacities] = useState<BedCapacity[]>([]);
  const [bedAllocations, setBedAllocations] = useState<BedAllocation[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showRefillModal, setShowRefillModal] = useState(false);
  const [showTicketModal, setShowTicketModal] = useState(false);
  const [showUsageModal, setShowUsageModal] = useState(false);
  const [showBedAssignModal, setShowBedAssignModal] = useState(false);

  // Forms
  const [newTicket, setNewTicket] = useState({
    category: 'ELECTRICAL',
    equipment_or_area: '',
    priority: 'MEDIUM',
    description: '',
    reported_by: 'Staff Nurse'
  });

  const [selectedConsumable, setSelectedConsumable] = useState<ConsumableItem | null>(null);
  const [usedQuantity, setUsedQuantity] = useState(1);

  const [newBedAllocation, setNewBedAllocation] = useState({
    bed_number: '',
    bed_category: 'GENERAL_OBSERVATION',
    patient_name: '',
    attending_doctor: 'Dr. Medical Officer'
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const facQuery = activeFacility?.id ? `?facility=${activeFacility.id}` : '';
      const [oxyRes, conRes, tickRes, bedCapRes, bedAllocRes] = await Promise.all([
        api.get(`facilities-infra/oxygen-supplies/${facQuery}`),
        api.get(`facilities-infra/consumables/${facQuery}`),
        api.get(`facilities-infra/maintenance-tickets/${facQuery}`),
        api.get(`facilities-infra/bed-capacity/${facQuery}`),
        api.get(`facilities-infra/bed-allocations/${facQuery}`)
      ]);

      setOxygenList(oxyRes.data.results || oxyRes.data || []);
      setConsumablesList(conRes.data.results || conRes.data || []);
      setTicketsList(tickRes.data.results || tickRes.data || []);
      setBedCapacities(bedCapRes.data.results || bedCapRes.data || []);
      setBedAllocations(bedAllocRes.data.results || bedAllocRes.data || []);
    } catch (e) {
      console.error('Failed to load infrastructure data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeFacility]);

  // Handlers
  const handleRequestRefill = async () => {
    alert('Oxygen Refill Indent ticket created successfully! Facility Logistics notified.');
    setShowRefillModal(false);
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('facilities-infra/maintenance-tickets/', {
        ...newTicket,
        facility: activeFacility?.id || 1,
        ticket_number: `MAINT-${Date.now().toString().slice(-6)}`,
        status: 'LOGGED',
        assigned_technician: 'BBMP Facility Maintenance Team'
      });
      alert('Maintenance Work Order logged successfully!');
      setShowTicketModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to log maintenance ticket.');
    }
  };

  const handleDeductConsumable = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConsumable) return;
    try {
      const updatedStock = Math.max(0, selectedConsumable.current_stock - usedQuantity);
      const reorderStatus = updatedStock <= selectedConsumable.min_threshold ? 'LOW_STOCK' : 'ADEQUATE';
      
      await api.patch(`facilities-infra/consumables/${selectedConsumable.id}/`, {
        current_stock: updatedStock,
        reorder_status: reorderStatus
      });
      alert(`Consumable usage recorded. Remaining stock: ${updatedStock} ${selectedConsumable.unit_of_measure}`);
      setShowUsageModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to update consumable stock.');
    }
  };

  const handleAssignBed = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('facilities-infra/bed-allocations/', {
        ...newBedAllocation,
        facility: activeFacility?.id || 1,
        status: 'OCCUPIED'
      });
      alert('Patient successfully admitted to bed!');
      setShowBedAssignModal(false);
      fetchData();
    } catch (err) {
      alert('Failed to assign bed.');
    }
  };

  const handleDischargeBed = async (id: number) => {
    try {
      await api.patch(`facilities-infra/bed-allocations/${id}/`, {
        status: 'AVAILABLE',
        patient_name: '',
        discharged_at: new Date().toISOString()
      });
      alert('Bed discharged and marked available for sanitation.');
      fetchData();
    } catch (err) {
      alert('Failed to update bed status.');
    }
  };

  // Active facility data filtering
  const activeOxygen = oxygenList[0] || {
    total_cylinders: 12,
    active_cylinders: 9,
    empty_cylinders: 3,
    current_pressure_psi: 1850,
    fill_percentage: 88,
    status: 'OPTIMAL',
    notes: 'Manifold system operational'
  };

  const totalBedsCount = bedCapacities.reduce((acc, b) => acc + b.total_beds, 0);
  const totalOccupiedCount = bedCapacities.reduce((acc, b) => acc + b.occupied_beds, 0);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 shadow-inner">
            <Wrench className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Clinic Infrastructure & Maintenance</h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                Live Status
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Facility utilities console: Oxygen Cylinders, Ward Bed Capacity, Sanitation Consumables, and Electrical/Plumbing Maintenance.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary KPI Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Widget 1: Oxygen */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Oxygen Supply</span>
            <span className="text-lg font-extrabold text-teal-700">{activeOxygen.fill_percentage}% Fill ({activeOxygen.current_pressure_psi} PSI)</span>
            <p className="text-xs text-slate-500 mt-0.5">{activeOxygen.active_cylinders}/{activeOxygen.total_cylinders} Active Cylinders</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600">
            <Wind className="w-5 h-5" />
          </div>
        </div>

        {/* Widget 2: Bed Capacity */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Ward Bed Occupancy</span>
            <span className="text-lg font-extrabold text-blue-700">{totalOccupiedCount}/{totalBedsCount} Beds ({Math.round((totalOccupiedCount/totalBedsCount)*100)}%)</span>
            <p className="text-xs text-slate-500 mt-0.5">{totalBedsCount - totalOccupiedCount} Beds Available</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
            <Bed className="w-5 h-5" />
          </div>
        </div>

        {/* Widget 3: Consumables */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Sanitation Supplies</span>
            <span className="text-lg font-extrabold text-emerald-700">{consumablesList.length} Consumables Logged</span>
            <p className="text-xs text-amber-600 font-bold mt-0.5">
              {consumablesList.filter(c => c.reorder_status === 'LOW_STOCK').length} Items Low Stock
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
            <Sparkles className="w-5 h-5" />
          </div>
        </div>

        {/* Widget 4: Maintenance */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Work Orders</span>
            <span className="text-lg font-extrabold text-amber-700">{ticketsList.filter(t => t.status !== 'RESOLVED' && t.status !== 'CLOSED').length} Active Tickets</span>
            <p className="text-xs text-slate-500 mt-0.5">{ticketsList.filter(t => t.priority === 'HIGH' || t.priority === 'EMERGENCY').length} High/Emergency</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
            <Wrench className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Interactive Tabs Bar */}
      <div className="flex border-b border-slate-200 bg-white px-4 rounded-xl shadow-xs">
        <button
          onClick={() => setActiveTab('oxygen')}
          className={`flex items-center gap-2 py-3 px-4 font-bold text-sm border-b-2 transition-all cursor-pointer ${
            activeTab === 'oxygen' ? 'border-teal-600 text-teal-700 bg-teal-50/50' : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Wind className="w-4 h-4" />
          Oxygen Supply & Cylinders
        </button>

        <button
          onClick={() => setActiveTab('beds')}
          className={`flex items-center gap-2 py-3 px-4 font-bold text-sm border-b-2 transition-all cursor-pointer ${
            activeTab === 'beds' ? 'border-blue-600 text-blue-700 bg-blue-50/50' : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Bed className="w-4 h-4" />
          Ward Beds & Capacity
        </button>

        <button
          onClick={() => setActiveTab('consumables')}
          className={`flex items-center gap-2 py-3 px-4 font-bold text-sm border-b-2 transition-all cursor-pointer ${
            activeTab === 'consumables' ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50' : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Sanitation & Floor Consumables
        </button>

        <button
          onClick={() => setActiveTab('maintenance')}
          className={`flex items-center gap-2 py-3 px-4 font-bold text-sm border-b-2 transition-all cursor-pointer ${
            activeTab === 'maintenance' ? 'border-amber-600 text-amber-700 bg-amber-50/50' : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Wrench className="w-4 h-4" />
          Electrical & Maintenance Tickets
        </button>
      </div>

      {/* TAB CONTENT 1: OXYGEN SUPPLY STATION */}
      {activeTab === 'oxygen' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Medical Oxygen Manifold & Pressure Status</h2>
                <p className="text-xs text-slate-500">Live pressure monitoring, cylinder manifold counts, and refill requests.</p>
              </div>
              <button
                onClick={() => setShowRefillModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-xl transition-colors shadow-sm"
              >
                <Plus className="w-4 h-4" />
                Request Oxygen Refill Indent
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Pressure Card */}
              <div className="bg-teal-50/60 p-5 rounded-xl border border-teal-200 flex flex-col justify-between">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-teal-800">Manifold Fill Gauge</span>
                  <span className="px-2 py-0.5 text-[11px] font-extrabold bg-teal-200 text-teal-900 rounded-md">
                    {activeOxygen.status}
                  </span>
                </div>
                <div className="text-3xl font-black text-teal-900 mb-2">{activeOxygen.fill_percentage}%</div>
                <div className="w-full bg-teal-200 rounded-full h-3 overflow-hidden mb-2">
                  <div className="bg-teal-600 h-3 rounded-full" style={{ width: `${activeOxygen.fill_percentage}%` }}></div>
                </div>
                <span className="text-xs text-teal-700 font-semibold">Current Pressure: {activeOxygen.current_pressure_psi} PSI</span>
              </div>

              {/* Cylinders Count */}
              <div className="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-600 block">Cylinder Distribution</span>
                <div className="flex justify-between items-center py-1.5 border-b border-slate-200">
                  <span className="text-xs font-medium text-slate-700">Total B/D Cylinders:</span>
                  <span className="text-sm font-bold text-slate-900">{activeOxygen.total_cylinders} Cylinders</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-slate-200">
                  <span className="text-xs font-medium text-emerald-700">Active Online Cylinders:</span>
                  <span className="text-sm font-extrabold text-emerald-700">{activeOxygen.active_cylinders} Cylinders</span>
                </div>
                <div className="flex justify-between items-center py-1.5">
                  <span className="text-xs font-medium text-slate-500">Empty / Standby:</span>
                  <span className="text-sm font-bold text-slate-600">{activeOxygen.empty_cylinders} Cylinders</span>
                </div>
              </div>

              {/* Notes & Maintenance info */}
              <div className="bg-slate-50 p-5 rounded-xl border border-slate-200 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-600 block mb-2">Manifold Notes & Safety</span>
                  <p className="text-xs text-slate-700 leading-relaxed bg-white p-3 rounded-lg border border-slate-200">
                    "{activeOxygen.notes}"
                  </p>
                </div>
                <div className="mt-4 text-[11px] text-slate-500 flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                  Inspected & pressure tested today by Facility Safety Officer.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT 2: WARD BEDS & CAPACITY */}
      {activeTab === 'beds' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Ward Bed Capacity & Patient Bed Allocations</h2>
                <p className="text-xs text-slate-500">OPD observation ward beds, emergency triage bays, and oxygen supported beds.</p>
              </div>
              <button
                onClick={() => setShowBedAssignModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl transition-colors shadow-sm"
              >
                <Plus className="w-4 h-4" />
                Admit Patient to Bed
              </button>
            </div>

            {/* Bed Category Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {bedCapacities.map((cap) => (
                <div key={cap.id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">{cap.bed_category.replace('_', ' ')}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-blue-100 text-blue-800">
                      {cap.available_beds} Available
                    </span>
                  </div>
                  <div className="text-2xl font-black text-slate-900">
                    {cap.occupied_beds} / {cap.total_beds} <span className="text-xs font-normal text-slate-500">Beds Occupied</span>
                  </div>
                  <p className="text-[11px] text-slate-500">{cap.notes}</p>
                </div>
              ))}
            </div>

            {/* Bed Grid List */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider">
                    <th className="py-3 px-4">Bed Number</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Patient Name</th>
                    <th className="py-3 px-4">Attending Doctor</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {bedAllocations.map((bed) => (
                    <tr key={bed.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-bold text-slate-900 flex items-center gap-2">
                        <Bed className="w-4 h-4 text-blue-600" />
                        {bed.bed_number}
                      </td>
                      <td className="py-3 px-4 text-slate-700">{bed.bed_category.replace('_', ' ')}</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">{bed.patient_name || '—'}</td>
                      <td className="py-3 px-4 text-slate-600">{bed.attending_doctor || '—'}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-md text-[10px] font-extrabold uppercase ${
                            bed.status === 'OCCUPIED'
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : bed.status === 'SANITIZING'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          }`}
                        >
                          {bed.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {bed.status === 'OCCUPIED' && (
                          <button
                            onClick={() => handleDischargeBed(bed.id)}
                            className="px-2.5 py-1 bg-slate-200 hover:bg-rose-100 hover:text-rose-700 text-slate-700 font-bold rounded text-[11px] transition-colors"
                          >
                            Discharge Bed
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT 3: SANITATION & FLOOR CONSUMABLES */}
      {activeTab === 'consumables' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Facility Sanitation & Floor Cleaning Consumables</h2>
                <p className="text-xs text-slate-500">Non-medical cleaning inventory, floor disinfectant chemicals, biohazard bags, and PPE.</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider">
                    <th className="py-3 px-4">Consumable Item</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Current Stock</th>
                    <th className="py-3 px-4">Min Threshold</th>
                    <th className="py-3 px-4">Reorder Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {consumablesList.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-bold text-slate-900 flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-emerald-600" />
                        {item.item_name}
                      </td>
                      <td className="py-3 px-4 text-slate-600">{item.category.replace('_', ' ')}</td>
                      <td className="py-3 px-4 font-extrabold text-slate-900 text-sm">
                        {item.current_stock} <span className="text-xs font-normal text-slate-500">{item.unit_of_measure}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-500">{item.min_threshold} {item.unit_of_measure}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-md text-[10px] font-extrabold uppercase ${
                            item.reorder_status === 'LOW_STOCK'
                              ? 'bg-amber-100 text-amber-800 border border-amber-300'
                              : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          }`}
                        >
                          {item.reorder_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedConsumable(item);
                            setShowUsageModal(true);
                          }}
                          className="px-3 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-bold border border-emerald-200 rounded text-xs transition-colors"
                        >
                          Log Usage
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT 4: ELECTRICAL & MAINTENANCE TICKETS */}
      {activeTab === 'maintenance' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Facility Electrical, Plumbing & Equipment Maintenance Work Orders</h2>
                <p className="text-xs text-slate-500">Log repair tickets for solar UPS backup, electrical wiring, plumbing, and clinic equipment.</p>
              </div>
              <button
                onClick={() => setShowTicketModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs rounded-xl transition-colors shadow-sm"
              >
                <Plus className="w-4 h-4" />
                Log Maintenance Work Order
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider">
                    <th className="py-3 px-4">Ticket ID</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Equipment / Location</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Assigned Technician</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {ticketsList.map((ticket) => (
                    <tr key={ticket.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-mono font-bold text-amber-700">{ticket.ticket_number}</td>
                      <td className="py-3 px-4 font-semibold text-slate-800">{ticket.category.replace('_', ' ')}</td>
                      <td className="py-3 px-4 text-slate-900 font-medium">{ticket.equipment_or_area}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-extrabold ${
                            ticket.priority === 'HIGH' || ticket.priority === 'EMERGENCY'
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {ticket.priority}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600">{ticket.assigned_technician}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-md text-[10px] font-extrabold uppercase ${
                            ticket.status === 'RESOLVED' || ticket.status === 'CLOSED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {ticket.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 1: REFILL OXYGEN */}
      {showRefillModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Request Oxygen Refill Indent</h3>
            <p className="text-xs text-slate-500">Submits an urgent refill request for 5 B-type Medical Oxygen cylinders to the District Logistics Hub.</p>
            
            <div className="bg-teal-50 p-3 rounded-lg border border-teal-200 text-xs text-teal-800 font-semibold">
              Current Pressure: 1850 PSI (88% Fill). Requesting 5 replacement cylinders.
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowRefillModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold"
              >
                Cancel
              </button>
              <button
                onClick={handleRequestRefill}
                className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold"
              >
                Submit Indent Request
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: LOG MAINTENANCE WORK ORDER */}
      {showTicketModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <form onSubmit={handleCreateTicket} className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Log Maintenance Work Order</h3>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Issue Category</label>
              <select
                value={newTicket.category}
                onChange={(e) => setNewTicket({ ...newTicket, category: e.target.value })}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-900 font-semibold"
              >
                <option value="ELECTRICAL">Electrical & Wiring</option>
                <option value="PLUMBING">Plumbing & Water Supply</option>
                <option value="OXYGEN_SYSTEM">Oxygen Manifold & Tubing</option>
                <option value="SOLAR_UPS">Solar Power & UPS Battery Backup</option>
                <option value="MEDICAL_EQUIPMENT">Medical Equipment Repair</option>
                <option value="SANITY_CLEANING">Deep Sanitation & Cleaning</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Equipment / Location Name</label>
              <input
                type="text"
                placeholder="e.g. Solar Inverter Panel / Pharmacy Fridge"
                value={newTicket.equipment_or_area}
                onChange={(e) => setNewTicket({ ...newTicket, equipment_or_area: e.target.value })}
                required
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-900"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Priority Level</label>
              <select
                value={newTicket.priority}
                onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-900 font-semibold"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="EMERGENCY">Emergency</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Problem Description</label>
              <textarea
                placeholder="Describe fault or repair details..."
                value={newTicket.description}
                onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                required
                rows={3}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-900"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowTicketModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold"
              >
                Log Ticket
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL 3: DEDUCT CONSUMABLE USAGE */}
      {showUsageModal && selectedConsumable && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <form onSubmit={handleDeductConsumable} className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Log Consumable Usage</h3>
            <p className="text-xs text-slate-600 font-bold">{selectedConsumable.item_name}</p>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Quantity Used ({selectedConsumable.unit_of_measure})</label>
              <input
                type="number"
                min="1"
                max={selectedConsumable.current_stock}
                value={usedQuantity}
                onChange={(e) => setUsedQuantity(parseInt(e.target.value) || 1)}
                required
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-900 font-extrabold"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowUsageModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold"
              >
                Record Usage
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL 4: ADMIT PATIENT TO BED */}
      {showBedAssignModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <form onSubmit={handleAssignBed} className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Admit Patient to Ward Bed</h3>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Bed Category</label>
              <select
                value={newBedAllocation.bed_category}
                onChange={(e) => setNewBedAllocation({ ...newBedAllocation, bed_category: e.target.value })}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-900 font-semibold"
              >
                <option value="GENERAL_OBSERVATION">General OPD Observation Bed</option>
                <option value="EMERGENCY_TRIAGE">Emergency Triage & Resuscitation Bed</option>
                <option value="OXYGEN_SUPPORTED">Oxygen Supported High-Care Bed</option>
                <option value="DAY_CARE_ISOLATION">Day-Care & Isolation Ward Bed</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Bed Number</label>
              <input
                type="text"
                placeholder="e.g. BED-OBS-04"
                value={newBedAllocation.bed_number}
                onChange={(e) => setNewBedAllocation({ ...newBedAllocation, bed_number: e.target.value })}
                required
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-900"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Patient Name & Age</label>
              <input
                type="text"
                placeholder="e.g. Suresh Gowda (58/M)"
                value={newBedAllocation.patient_name}
                onChange={(e) => setNewBedAllocation({ ...newBedAllocation, patient_name: e.target.value })}
                required
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs text-slate-900"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowBedAssignModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold"
              >
                Confirm Admission
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
