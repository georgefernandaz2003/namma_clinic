import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type {
  Prescription,
  MedicineMaster,
  MedicineBatch,
  Vendor,
  PurchaseOrder,
  InventoryTransaction,
  PharmacyDashboardKPIs,
  PharmacyAlert,
  PharmacyReportSummary,
  ProcurementSummaryKPIs,
} from '../types';
import { useAuth } from '../context/AuthContext';
import {
  Pill,
  PackageCheck,
  AlertTriangle,
  Layers,
  ShieldCheck,
  TrendingDown,
  Building2,
  ShoppingCart,
  History,
  FileSpreadsheet,
  AlertCircle,
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRightLeft,
  DollarSign,
  Download,
  Boxes,
  Truck,
  ClipboardList,
  Eye,
  Check,
  X,
  Filter,
  Send,
  Edit2,
  Ban,
  Trash2,
  ChevronRight,
  Info,
  RefreshCw,
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { hasPermission } from '../utils/permissions';

type ActiveTab =
  | 'DASHBOARD'
  | 'PRESCRIPTIONS'
  | 'INVENTORY'
  | 'BATCHES'
  | 'TRANSACTIONS'
  | 'VENDORS'
  | 'PURCHASE_ORDERS'
  | 'ALERTS'
  | 'REPORTS';

export const Pharmacy: React.FC = () => {
  const { activeFacility, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isHospitalAdmin = user?.role === 'HOSPITAL_ADMIN';
  const isPharmacist = user?.role === 'PHARMACIST' || isHospitalAdmin;
  const isReadOnly =
    user?.role === 'DISTRICT_OFFICER' ||
    user?.role === 'DOCTOR' ||
    user?.role === 'NURSE' ||
    user?.role === 'LAB_TECHNICIAN';

  const canCreateMedicine = Boolean(
    (user?.permissions && user.permissions.includes('medicine_master.create')) ||
    hasPermission(user?.role, 'medicine_master.create')
  );
  const canUpdateMedicine = Boolean(
    (user?.permissions && user.permissions.includes('medicine_master.update')) ||
    hasPermission(user?.role, 'medicine_master.update')
  );
  const canDeleteMedicine = Boolean(
    (user?.permissions && user.permissions.includes('medicine_master.delete')) ||
    hasPermission(user?.role, 'medicine_master.delete')
  );

  const [activeTab, setActiveTab] = useState<ActiveTab>('DASHBOARD');
  const [loading, setLoading] = useState<boolean>(false);

  // Data states
  const [kpis, setKpis] = useState<PharmacyDashboardKPIs | null>(null);
  const [procurementKpis, setProcurementKpis] = useState<ProcurementSummaryKPIs | null>(null);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [medicines, setMedicines] = useState<MedicineMaster[]>([]);
  const [batches, setBatches] = useState<MedicineBatch[]>([]);
  const [transactions, setTransactions] = useState<InventoryTransaction[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [alerts, setAlerts] = useState<PharmacyAlert[]>([]);
  const [reportSummary, setReportSummary] = useState<PharmacyReportSummary | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [prescriptionStatusFilter, setPrescriptionStatusFilter] = useState<string>('ALL');
  const [batchStatusFilter, setBatchStatusFilter] = useState<string>('ALL');
  const [medicineSearchQuery, setMedicineSearchQuery] = useState('');
  const [medicineCategoryFilter, setMedicineCategoryFilter] = useState<string>('ALL');

  // Vendor Management States
  const [vendorSearch, setVendorSearch] = useState('');
  const [vendorStatusFilter, setVendorStatusFilter] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL');
  const [selectedVendorForDetails, setSelectedVendorForDetails] = useState<Vendor | null>(null);
  const [vendorHistory, setVendorHistory] = useState<PurchaseOrder[]>([]);
  const [loadingVendorHistory, setLoadingVendorHistory] = useState(false);
  const [editingVendor, setEditingVendor] = useState<Vendor | null>(null);
  const [editVendorData, setEditVendorData] = useState({
    name: '',
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    gstin: '',
  });

  // Purchase Order Management States
  const [poStatusFilter, setPoStatusFilter] = useState<string>('ALL');
  const [poSearchQuery, setPoSearchQuery] = useState('');
  const [selectedPOForDetails, setSelectedPOForDetails] = useState<PurchaseOrder | null>(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [poActionLoading, setPoActionLoading] = useState(false);

  // Modal states
  const [dispenseModalRx, setDispenseModalRx] = useState<Prescription | null>(null);
  const [dispenseItems, setDispenseItems] = useState<
    Array<{ item_id: number; medicine_name: string; target_qty: number; batch_id: number; qty_to_dispense: number }>
  >([]);
  const [dispensingError, setDispensingError] = useState<string>('');

  // Add Vendor Modal
  const [showAddVendorModal, setShowAddVendorModal] = useState(false);
  const [newVendorData, setNewVendorData] = useState({
    vendor_code: '',
    name: '',
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    gstin: '',
  });

  // Create PO Modal
  const [showCreatePOModal, setShowCreatePOModal] = useState(false);
  const [newPOData, setNewPOData] = useState({
    vendor: 0,
    expected_delivery: '',
    notes: '',
    items: [{ medicine: 0, requested_quantity: 100, unit_cost: 10.0 }],
  });

  // Medicine Master Management States
  const [showAddMedicineModal, setShowAddMedicineModal] = useState(false);
  const [newMedicineData, setNewMedicineData] = useState({
    generic_name: '',
    brand_name: '',
    strength: '500 mg',
    dosage_form: 'Tablet',
    unit: 'Tablets',
    category: 'Essential Medicines',
    minimum_stock: 25,
    reorder_level: 50,
    description: '',
  });
  const [editingMedicine, setEditingMedicine] = useState<MedicineMaster | null>(null);
  const [editMedicineData, setEditMedicineData] = useState({
    generic_name: '',
    brand_name: '',
    strength: '',
    dosage_form: '',
    unit: '',
    category: '',
    minimum_stock: 25,
    reorder_level: 50,
    description: '',
  });
  const [medicineActionLoading, setMedicineActionLoading] = useState(false);

  // Goods Receiving Modal
  const [receivingPO, setReceivingPO] = useState<PurchaseOrder | null>(null);
  const [receiveItemsData, setReceiveItemsData] = useState<
    Array<{
      po_item_id: number;
      medicine_name: string;
      ordered_quantity: number;
      already_received: number;
      requested_quantity: number;
      received_quantity: number;
      batch_number: string;
      mfg_date: string;
      expiry_date: string;
      unit_cost: number;
    }>
  >([]);

  const loadData = async () => {
    if (!activeFacility) return;
    setLoading(true);
    try {
      const facilityId = activeFacility.id;

      const [kpiRes, pRes, mRes, bRes, tRes, vRes, poRes, alertRes, rptRes, procRes] = await Promise.all([
        api.get(`pharmacy/dashboard/?facility=${facilityId}`).catch(() => ({ data: null })),
        api.get(`pharmacy/prescriptions/?facility=${facilityId}`).catch(() => ({ data: [] })),
        api.get(`pharmacy/medicines/?facility=${facilityId}`).catch(() => ({ data: [] })),
        api.get(`pharmacy/batches/?facility=${facilityId}`).catch(() => ({ data: [] })),
        api.get(`pharmacy/transactions/?facility=${facilityId}`).catch(() => ({ data: [] })),
        api.get(`pharmacy/vendors/`).catch(() => ({ data: [] })),
        api.get(`pharmacy/purchase-orders/?facility=${facilityId}`).catch(() => ({ data: [] })),
        api.get(`pharmacy/alerts/?facility=${facilityId}`).catch(() => ({ data: [] })),
        api.get(`pharmacy/reports/?facility=${facilityId}`).catch(() => ({ data: null })),
        api.get(`pharmacy/purchase-orders/procurement_summary/?facility=${facilityId}`).catch(() => ({ data: null })),
      ]);

      const rxList = pRes.data.results || pRes.data || [];
      const medList = mRes.data.results || mRes.data || [];
      const batchList = bRes.data.results || bRes.data || [];
      const txList = tRes.data.results || tRes.data || [];
      const vendorList = vRes.data.results || vRes.data || [];
      const poList = poRes.data.results || poRes.data || [];

      // Calculate real-time fallbacks from loaded data
      const totalStock = batchList.reduce((acc: number, b: any) => acc + (Number(b.quantity) || 0), 0);
      const expiredCount = batchList.filter((b: any) => b.is_expired || (b.expiry_date && new Date(b.expiry_date) <= new Date())).length;
      const expiringCount = batchList.filter((b: any) => !b.is_expired && (b.status === 'EXPIRING_SOON' || (b.days_to_expiry !== undefined && b.days_to_expiry <= 60 && b.days_to_expiry > 0))).length;
      const pendingRx = rxList.filter((r: any) => ['PENDING', 'ACTIVE', 'PARTIALLY_DISPENSED'].includes(r.status)).length;
      const pendingPOs = poList.filter((po: any) => ['DRAFT', 'PENDING_APPROVAL', 'PENDING', 'APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED'].includes(po.status)).length;

      const mergedKPIs: PharmacyDashboardKPIs = {
        total_medicines: kpiRes.data?.total_medicines ?? medList.length,
        total_available_stock: kpiRes.data?.total_available_stock ?? totalStock,
        low_stock_count: kpiRes.data?.low_stock_count ?? kpiRes.data?.low_stock ?? 0,
        out_of_stock_count: kpiRes.data?.out_of_stock_count ?? kpiRes.data?.out_of_stock ?? 0,
        expiring_soon_count: kpiRes.data?.expiring_soon_count ?? kpiRes.data?.expiring_soon ?? expiringCount,
        expired_count: kpiRes.data?.expired_count ?? expiredCount,
        pending_prescriptions_count: kpiRes.data?.pending_prescriptions_count ?? kpiRes.data?.prescriptions_waiting ?? pendingRx,
        dispensed_today_count: kpiRes.data?.dispensed_today_count ?? kpiRes.data?.dispensed_today ?? 0,
        pending_purchase_orders_count: kpiRes.data?.pending_purchase_orders_count ?? kpiRes.data?.pending_purchase_orders ?? pendingPOs,
        total_vendors_count: kpiRes.data?.total_vendors_count ?? vendorList.length,
      };

      // Procurement Summary Fallback
      const procData: ProcurementSummaryKPIs = procRes.data || {
        draft: poList.filter((p: any) => p.status === 'DRAFT').length,
        pending_approval: poList.filter((p: any) => ['PENDING_APPROVAL', 'PENDING'].includes(p.status)).length,
        approved: poList.filter((p: any) => p.status === 'APPROVED').length,
        ordered: poList.filter((p: any) => p.status === 'ORDERED').length,
        partially_received: poList.filter((p: any) => p.status === 'PARTIALLY_RECEIVED').length,
        received: poList.filter((p: any) => p.status === 'RECEIVED').length,
        cancelled: poList.filter((p: any) => p.status === 'CANCELLED').length,
        total_orders: poList.length,
        total_spend: poList
          .filter((p: any) => ['APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED'].includes(p.status))
          .reduce((sum: number, p: any) => sum + (Number(p.total_amount) || 0), 0),
      };

      setKpis(mergedKPIs);
      setProcurementKpis(procData);
      setPrescriptions(rxList);
      setMedicines(medList);
      setBatches(batchList);
      setTransactions(txList);
      setVendors(vendorList);
      setPurchaseOrders(poList);
      setAlerts(alertRes.data.alerts || alertRes.data || []);
      setReportSummary(rptRes.data);

      // Keep detail modals synced if currently open
      setSelectedPOForDetails((curr) => {
        if (!curr) return null;
        return poList.find((p: any) => p.id === curr.id) || curr;
      });

      // Handle direct queue dispatch
      if (location.state?.visitId) {
        const targetRx = rxList.find((r: any) => r.visit_id === location.state.visitId || r.consultation?.visit === location.state.visitId);
        if (targetRx && targetRx.status !== 'DISPENSED') {
          setActiveTab('PRESCRIPTIONS');
          setTimeout(() => openDispenseModal(targetRx), 150);
        }
      }
    } catch (e) {
      console.error('Failed to load pharmacy module data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  useEffect(() => {
    if (location.state?.activeTab) {
      setActiveTab(location.state.activeTab);
    } else if (location.state?.visitId || location.state?.patientId) {
      setActiveTab('PRESCRIPTIONS');
    }
  }, [location.state]);

  // Helper to match medicine names between batch records and prescriptions
  const matchMedicineBatch = (batchMedName?: string, itemMedName?: string) => {
    if (!batchMedName || !itemMedName) return false;
    const b = batchMedName.toLowerCase();
    const i = itemMedName.toLowerCase();
    const bWord = b.split(/[\s-]+/)[0];
    const iWord = i.split(/[\s-]+/)[0];
    return b.includes(i) || i.includes(b) || b.includes(iWord) || i.includes(bWord) || bWord === iWord;
  };

  // Open Dispense Modal with precalculated FEFO batches
  const openDispenseModal = (rx: Prescription) => {
    setDispenseModalRx(rx);
    setDispensingError('');

    const initialItems = (rx.items || []).map((item) => {
      const matchingBatches = batches.filter(
        (b) =>
          matchMedicineBatch(b.medicine_name || b.generic_name, item.medicine_name) &&
          b.quantity > 0 &&
          new Date(b.expiry_date) > new Date()
      );
      matchingBatches.sort((a, b) => new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime());
      const fefoBatch = matchingBatches[0];

      return {
        item_id: item.id || 0,
        medicine_name: item.medicine_name,
        target_qty: item.quantity,
        batch_id: fefoBatch ? fefoBatch.id : 0,
        qty_to_dispense: item.quantity,
      };
    });

    setDispenseItems(initialItems);
  };

  const handleConfirmDispense = async () => {
    if (!dispenseModalRx) return;
    setDispensingError('');
    try {
      const payload = {
        prescription_id: dispenseModalRx.id,
        items: dispenseItems.map((it) => ({
          item_id: it.item_id,
          medicine_name: it.medicine_name,
          batch_id: it.batch_id > 0 ? it.batch_id : null,
          qty: it.qty_to_dispense,
          qty_to_dispense: it.qty_to_dispense,
        })),
      };
      const res = await api.post('pharmacy/dispense/', payload);
      alert(res.data?.message || 'Prescription successfully dispensed! Stock deducted in real-time.');
      setDispenseModalRx(null);
      loadData();
    } catch (e: any) {
      const msg = e.response?.data?.error || 'Failed to dispense prescription.';
      setDispensingError(msg);
    }
  };

  // Medicine Master Action Handlers
  const handleAddMedicine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canCreateMedicine) return;
    setMedicineActionLoading(true);
    try {
      const res = await api.post('pharmacy/medicines/', newMedicineData);
      setMedicines((prev) => [...prev, res.data]);
      setShowAddMedicineModal(false);
      setNewMedicineData({
        generic_name: '',
        brand_name: '',
        strength: '500 mg',
        dosage_form: 'Tablet',
        unit: 'Tablets',
        category: 'Essential Medicines',
        minimum_stock: 25,
        reorder_level: 50,
        description: '',
      });
      alert('Medicine registered successfully!');
    } catch (err: any) {
      alert(err.response?.data?.message || err.response?.data?.generic_name?.[0] || 'Failed to register medicine');
    } finally {
      setMedicineActionLoading(false);
    }
  };

  const handleOpenEditMedicine = (med: MedicineMaster) => {
    if (!canUpdateMedicine) return;
    setEditingMedicine(med);
    setEditMedicineData({
      generic_name: med.generic_name,
      brand_name: med.brand_name || '',
      strength: med.strength,
      dosage_form: med.dosage_form,
      unit: med.unit,
      category: med.category,
      minimum_stock: med.minimum_stock,
      reorder_level: med.reorder_level,
      description: (med as any).description || '',
    });
  };

  const handleSaveEditMedicine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canUpdateMedicine || !editingMedicine) return;
    setMedicineActionLoading(true);
    try {
      const res = await api.patch(`pharmacy/medicines/${editingMedicine.id}/`, editMedicineData);
      setMedicines((prev) => prev.map((m) => (m.id === editingMedicine.id ? res.data : m)));
      setEditingMedicine(null);
      alert('Medicine updated successfully!');
    } catch (err: any) {
      alert(err.response?.data?.message || err.response?.data?.generic_name?.[0] || 'Failed to update medicine');
    } finally {
      setMedicineActionLoading(false);
    }
  };

  const handleDeleteMedicine = async (id: number) => {
    if (!canDeleteMedicine) return;
    if (!window.confirm('Are you sure you want to remove this medicine from the master catalog?')) return;
    try {
      await api.delete(`pharmacy/medicines/${id}/`);
      setMedicines((prev) => prev.filter((m) => m.id !== id));
      alert('Medicine deleted successfully!');
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to delete medicine');
    }
  };

  // Vendor Action Handlers
  const handleAddVendor = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('pharmacy/vendors/', newVendorData);
      alert('Vendor registered successfully!');
      setShowAddVendorModal(false);
      setNewVendorData({
        vendor_code: '',
        name: '',
        contact_person: '',
        phone: '',
        email: '',
        address: '',
        gstin: '',
      });
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.error || 'Failed to create vendor');
    }
  };

  const handleToggleVendorStatus = async (vendor: Vendor) => {
    try {
      const res = await api.post(`pharmacy/vendors/${vendor.id}/toggle_status/`);
      alert(res.data?.message || `Vendor status updated.`);
      loadData();
      if (selectedVendorForDetails?.id === vendor.id) {
        setSelectedVendorForDetails((prev) =>
          prev ? { ...prev, status: res.data?.status || (prev.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE') } : null
        );
      }
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to toggle vendor status.');
    }
  };

  const handleViewVendorDetails = async (vendor: Vendor) => {
    setSelectedVendorForDetails(vendor);
    setLoadingVendorHistory(true);
    try {
      const res = await api.get(`pharmacy/vendors/${vendor.id}/purchase_history/`);
      setVendorHistory(res.data || []);
    } catch (err) {
      console.error('Failed to load vendor history', err);
      setVendorHistory([]);
    } finally {
      setLoadingVendorHistory(false);
    }
  };

  const handleOpenEditVendor = (vendor: Vendor) => {
    setEditingVendor(vendor);
    setEditVendorData({
      name: vendor.vendor_name || vendor.name || '',
      contact_person: vendor.contact_person || '',
      phone: vendor.phone || '',
      email: vendor.email || '',
      address: vendor.address || '',
      gstin: vendor.gst_number || vendor.gstin || '',
    });
  };

  const handleSaveEditVendor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingVendor) return;
    try {
      await api.patch(`pharmacy/vendors/${editingVendor.id}/`, {
        vendor_name: editVendorData.name,
        contact_person: editVendorData.contact_person,
        phone: editVendorData.phone,
        email: editVendorData.email,
        address: editVendorData.address,
        gst_number: editVendorData.gstin,
      });
      alert('Vendor details updated successfully!');
      setEditingVendor(null);
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to update vendor.');
    }
  };

  const handleDeleteVendor = async (vendor: Vendor) => {
    if (!window.confirm(`Are you sure you want to delete vendor "${vendor.vendor_name || vendor.name}"?`)) return;
    try {
      await api.delete(`pharmacy/vendors/${vendor.id}/`);
      alert('Vendor deleted successfully.');
      if (selectedVendorForDetails?.id === vendor.id) {
        setSelectedVendorForDetails(null);
      }
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Cannot delete vendor. It has historical orders or inventory batches linked to it.');
    }
  };

  // PO Lifecycle Handlers
  const handleCreatePO = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPOData.vendor) {
      alert('Please select a vendor.');
      return;
    }
    const validItems = newPOData.items.filter((it) => it.medicine > 0 && it.requested_quantity > 0);
    if (validItems.length === 0) {
      alert('Please add at least one medicine item with quantity > 0.');
      return;
    }
    try {
      await api.post('pharmacy/purchase-orders/', {
        vendor: newPOData.vendor,
        expected_delivery: newPOData.expected_delivery || null,
        notes: newPOData.notes,
        items: validItems,
      });
      alert('Purchase Order created successfully in DRAFT mode!');
      setShowCreatePOModal(false);
      setNewPOData({
        vendor: 0,
        expected_delivery: '',
        notes: '',
        items: [{ medicine: 0, requested_quantity: 100, unit_cost: 10.0 }],
      });
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.error || 'Failed to create Purchase Order');
    }
  };

  const handleSubmitPOForApproval = async (poId: number) => {
    setPoActionLoading(true);
    try {
      const res = await api.post(`pharmacy/purchase-orders/${poId}/submit_approval/`);
      alert(res.data?.message || 'PO submitted for administrative approval.');
      loadData();
      if (selectedPOForDetails?.id === poId) {
        setSelectedPOForDetails(res.data?.po || null);
      }
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to submit PO for approval.');
    } finally {
      setPoActionLoading(false);
    }
  };

  const handleApprovePO = async (poId: number) => {
    setPoActionLoading(true);
    try {
      const res = await api.post(`pharmacy/purchase-orders/${poId}/approve/`);
      alert(res.data?.message || 'PO approved successfully.');
      loadData();
      if (selectedPOForDetails?.id === poId) {
        setSelectedPOForDetails(res.data?.po || null);
      }
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to approve PO.');
    } finally {
      setPoActionLoading(false);
    }
  };

  const handleConfirmRejectPO = async () => {
    if (!selectedPOForDetails) return;
    if (!rejectionReason.trim()) {
      alert('Please provide a reason for rejecting the Purchase Order.');
      return;
    }
    setPoActionLoading(true);
    try {
      const res = await api.post(`pharmacy/purchase-orders/${selectedPOForDetails.id}/reject/`, {
        reason: rejectionReason.trim(),
      });
      alert(res.data?.message || 'Purchase Order returned to Draft.');
      setShowRejectModal(false);
      setRejectionReason('');
      loadData();
      setSelectedPOForDetails(res.data?.po || null);
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to reject PO.');
    } finally {
      setPoActionLoading(false);
    }
  };

  const handlePlaceOrder = async (poId: number) => {
    setPoActionLoading(true);
    try {
      const res = await api.post(`pharmacy/purchase-orders/${poId}/place_order/`);
      alert(res.data?.message || 'Purchase order marked as ORDERED with supplier.');
      loadData();
      if (selectedPOForDetails?.id === poId) {
        setSelectedPOForDetails(res.data?.po || null);
      }
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to place order.');
    } finally {
      setPoActionLoading(false);
    }
  };

  const handleCancelPO = async (poId: number) => {
    if (!window.confirm('Are you sure you want to cancel this Purchase Order?')) return;
    setPoActionLoading(true);
    try {
      const res = await api.post(`pharmacy/purchase-orders/${poId}/cancel/`);
      alert(res.data?.message || 'Purchase order cancelled.');
      loadData();
      if (selectedPOForDetails?.id === poId) {
        setSelectedPOForDetails(res.data?.po || null);
      }
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to cancel PO.');
    } finally {
      setPoActionLoading(false);
    }
  };

  // Goods Receiving Handler with Over-receiving & Expired batch guards
  const openReceivingModal = (po: PurchaseOrder) => {
    setReceivingPO(po);
    const initial = (po.items || []).map((item) => {
      const orderedQty = item.ordered_quantity ?? item.requested_quantity ?? 0;
      const recQty = item.received_quantity ?? 0;
      const remainingQty = item.remaining_quantity !== undefined ? item.remaining_quantity : Math.max(0, orderedQty - recQty);
      return {
        po_item_id: item.id || 0,
        medicine_name: item.medicine_name || `Medicine #${item.medicine}`,
        ordered_quantity: orderedQty,
        already_received: recQty,
        requested_quantity: remainingQty,
        received_quantity: remainingQty,
        batch_number: `BATCH-${Math.floor(1000 + Math.random() * 9000)}`,
        mfg_date: new Date().toISOString().split('T')[0],
        expiry_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        unit_cost: item.unit_price ?? item.unit_cost ?? 0,
      };
    });
    setReceiveItemsData(initial);
  };

  const handleConfirmGoodsReceiving = async () => {
    if (!receivingPO) return;

    for (const it of receiveItemsData) {
      if (it.received_quantity < 0) {
        alert(`Received quantity cannot be negative for ${it.medicine_name}`);
        return;
      }
      if (it.received_quantity > it.requested_quantity) {
        alert(`Received quantity (${it.received_quantity}) cannot exceed remaining ordered quantity (${it.requested_quantity}) for ${it.medicine_name}.`);
        return;
      }
      if (it.received_quantity > 0) {
        if (!it.batch_number.trim()) {
          alert(`Batch Number is required for ${it.medicine_name}`);
          return;
        }
        if (!it.expiry_date) {
          alert(`Expiry Date is required for ${it.medicine_name}`);
          return;
        }
        if (new Date(it.expiry_date) <= new Date()) {
          alert(`Expiry Date must be in the future for ${it.medicine_name}. Received batch cannot be expired.`);
          return;
        }
        if (it.mfg_date && new Date(it.mfg_date) > new Date()) {
          alert(`Manufacturing Date cannot be in the future for ${it.medicine_name}`);
          return;
        }
      }
    }

    const itemsToReceive = receiveItemsData.filter((it) => it.received_quantity > 0);
    if (itemsToReceive.length === 0) {
      alert('Please specify at least 1 unit to receive.');
      return;
    }

    try {
      const payload = {
        received_items: itemsToReceive.map((it) => ({
          item_id: it.po_item_id,
          batch_number: it.batch_number.trim(),
          mfg_date: it.mfg_date || null,
          expiry_date: it.expiry_date,
          received_qty: Number(it.received_quantity),
          unit_cost: Number(it.unit_cost),
        })),
        items: itemsToReceive.map((it) => ({
          po_item_id: it.po_item_id,
          batch_number: it.batch_number.trim(),
          mfg_date: it.mfg_date || null,
          expiry_date: it.expiry_date,
          received_quantity: Number(it.received_quantity),
          unit_cost: Number(it.unit_cost),
        })),
      };
      const res = await api.post(`pharmacy/purchase-orders/${receivingPO.id}/receive_items/`, payload);
      alert(res.data?.message || 'Goods received! Inventory batches and transactions updated.');
      setReceivingPO(null);
      loadData();
      if (selectedPOForDetails?.id === receivingPO.id) {
        setSelectedPOForDetails(res.data?.po || null);
      }
    } catch (e: any) {
      alert(e.response?.data?.error || 'Failed to receive goods');
    }
  };

  // CSV Export Report
  const exportCSVReport = () => {
    if (!reportSummary) return;
    let csvContent = 'data:text/csv;charset=utf-8,';

    csvContent += 'PHARMACY ANALYTICS & STOCK VALUATION REPORT\n';
    csvContent += `Facility,${activeFacility?.facility_name || 'All Facilities'}\n`;
    csvContent += `Generated Date,${new Date().toLocaleDateString()}\n\n`;

    csvContent += 'DISPENSING SUMMARY\n';
    csvContent += `Dispensed Today (Units),${reportSummary.dispensing_summary.dispensed_today}\n`;
    csvContent += `Prescriptions Count,${reportSummary.dispensing_summary.prescriptions_count}\n\n`;

    csvContent += 'STOCK VALUATION SUMMARY\n';
    csvContent += `Total Batches,${reportSummary.stock_valuation.total_batches}\n`;
    csvContent += `Total Quantity in Stock,${reportSummary.stock_valuation.total_quantity}\n`;
    csvContent += `Total Valuation (INR),${reportSummary.stock_valuation.total_value}\n\n`;

    csvContent += 'TOP CONSUMED MEDICINES\n';
    csvContent += 'Generic Name,Brand Name,Total Consumed Units\n';
    reportSummary.consumption_summary.forEach((item) => {
      csvContent += `"${item.batch__medicine__generic_name}","${item.batch__medicine__brand_name}",${item.total_consumed}\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `pharmacy_report_${activeFacility?.facility_code || 'export'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Group batches for FEFO comparison display
  const groupedBatches = batches.reduce((acc: Record<string, MedicineBatch[]>, b) => {
    const key = b.medicine_name || b.generic_name || 'Generic Drug';
    if (!acc[key]) acc[key] = [];
    acc[key].push(b);
    return acc;
  }, {});

  Object.keys(groupedBatches).forEach((key) => {
    groupedBatches[key].sort((a, b) => new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime());
  });

  const totalValuation =
    reportSummary?.stock_valuation?.total_value ??
    batches.reduce((sum, b) => sum + (Number(b.quantity) || 0) * (Number(b.unit_cost) || 0), 0);

  const pendingPrescriptionsCount = prescriptions.filter((p) =>
    ['PENDING', 'ACTIVE', 'PARTIALLY_DISPENSED'].includes(p.status)
  ).length;

  const activeAlertsCount = alerts.length;
  const activePOCount = purchaseOrders.filter((p) => ['ORDERED', 'PENDING', 'DRAFT'].includes(p.status)).length;

  const filteredMedicines = medicines.filter((m) => {
    const query = medicineSearchQuery.toLowerCase();
    const matchSearch =
      !medicineSearchQuery ||
      m.generic_name?.toLowerCase().includes(query) ||
      m.brand_name?.toLowerCase().includes(query) ||
      m.code?.toLowerCase().includes(query);
    const matchCategory = medicineCategoryFilter === 'ALL' || m.category === medicineCategoryFilter;
    return matchSearch && matchCategory;
  });

  const medicineCategories = Array.from(new Set(medicines.map((m) => m.category).filter(Boolean)));

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs">
        <div className="flex items-center gap-3.5">
          <div className="p-3 bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-2xl shadow-sm flex items-center justify-center">
            <Pill className="w-6 h-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-black text-slate-900 tracking-tight">Pharmacy & Drug Inventory</h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                FEFO Engine Active
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-2">
              <span>Facility: <strong className="text-slate-800 font-semibold">{activeFacility?.facility_name || 'Central Store'}</strong></span>
              <span className="text-slate-300">•</span>
              <span>First-Expiry Controlled Dispensing & Real-Time Stock Ledger</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setShowAddVendorModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border border-slate-200 transition shadow-2xs cursor-pointer"
          >
            <Building2 className="w-3.5 h-3.5 text-slate-500" />
            <span>+ Add Vendor</span>
          </button>
          <button
            onClick={() => setShowCreatePOModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-bold text-xs rounded-xl border border-emerald-300 transition shadow-2xs cursor-pointer"
          >
            <ShoppingCart className="w-3.5 h-3.5 text-emerald-600" />
            <span>+ Create PO</span>
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Modern Segmented Navigation Tabs */}
      <div className="bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200/80 flex flex-wrap items-center gap-1 shadow-xs">
        {[
          { id: 'DASHBOARD', label: 'Overview', icon: Boxes, badge: null, badgeColor: '' },
          {
            id: 'PRESCRIPTIONS',
            label: 'Prescriptions Queue',
            icon: ClipboardList,
            badge: pendingPrescriptionsCount > 0 ? `${pendingPrescriptionsCount} Pending` : `${prescriptions.length}`,
            badgeColor: pendingPrescriptionsCount > 0 ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-slate-200/80 text-slate-700 border-slate-300'
          },
          { id: 'INVENTORY', label: 'Inventory Ledger', icon: Pill, badge: `${medicines.length}`, badgeColor: 'bg-slate-200/80 text-slate-700 border-slate-300' },
          { id: 'BATCHES', label: 'Batches', icon: Layers, badge: `${batches.length}`, badgeColor: 'bg-slate-200/80 text-slate-700 border-slate-300' },
          { id: 'TRANSACTIONS', label: 'Stock Transactions', icon: History, badge: `${transactions.length}`, badgeColor: 'bg-slate-200/80 text-slate-700 border-slate-300' },
          {
            id: 'PURCHASE_ORDERS',
            label: 'Purchase Orders',
            icon: Truck,
            badge: activePOCount > 0 ? `${activePOCount}` : null,
            badgeColor: 'bg-blue-100 text-blue-800 border-blue-200'
          },
          { id: 'VENDORS', label: 'Vendors', icon: Building2, badge: `${vendors.length}`, badgeColor: 'bg-slate-200/80 text-slate-700 border-slate-300' },
          {
            id: 'ALERTS',
            label: 'Stock Alerts',
            icon: AlertTriangle,
            badge: activeAlertsCount > 0 ? `${activeAlertsCount}` : null,
            badgeColor: 'bg-rose-100 text-rose-800 border-rose-300 animate-pulse'
          },
          { id: 'REPORTS', label: 'Reports & Export', icon: FileSpreadsheet, badge: null, badgeColor: '' },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ActiveTab)}
              className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                isActive
                  ? 'bg-white text-emerald-900 shadow-xs border border-slate-200/80 ring-1 ring-slate-900/5'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-700' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-black border ${tab.badgeColor}`}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* TAB 1: DASHBOARD */}
      {activeTab === 'DASHBOARD' && (
        <div className="space-y-6">
          {/* 6 Responsive KPI Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1 hover:border-slate-300 transition">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Total Available Stock</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-slate-900">{kpis?.total_available_stock ?? 0}</span>
                <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                  <Pill className="w-4 h-4" />
                </div>
              </div>
              <span className="text-[10px] text-slate-400 block">{kpis?.total_medicines ?? medicines.length} EDL Drugs</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-emerald-200/80 shadow-xs space-y-1 hover:border-emerald-300 transition">
              <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">Stock Valuation</span>
              <div className="flex items-baseline justify-between">
                <span className="text-xl font-black text-emerald-900">
                  ₹{Number(totalValuation).toLocaleString('en-IN')}
                </span>
                <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
                  <DollarSign className="w-4 h-4" />
                </div>
              </div>
              <span className="text-[10px] text-emerald-600 block">{batches.length} Active Batches</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-teal-200/80 shadow-xs space-y-1 hover:border-teal-300 transition">
              <span className="text-[11px] font-bold text-teal-700 uppercase tracking-wider block">Dispensed Today</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-teal-900">{kpis?.dispensed_today_count ?? 0}</span>
                <div className="p-1.5 rounded-lg bg-teal-50 text-teal-600">
                  <PackageCheck className="w-4 h-4" />
                </div>
              </div>
              <span className="text-[10px] text-teal-600 block">{pendingPrescriptionsCount} Waiting in Queue</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-amber-200 shadow-xs space-y-1 hover:border-amber-300 transition">
              <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">Low Stock Items</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-amber-900">{kpis?.low_stock_count ?? 0}</span>
                <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
                  <AlertTriangle className="w-4 h-4" />
                </div>
              </div>
              <span className="text-[10px] text-amber-600 block">{kpis?.out_of_stock_count ?? 0} Out of Stock</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-rose-200 shadow-xs space-y-1 hover:border-rose-300 transition">
              <span className="text-[11px] font-bold text-rose-700 uppercase tracking-wider block">Expiring Batches</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-rose-900">{kpis?.expiring_soon_count ?? 0}</span>
                <div className="p-1.5 rounded-lg bg-rose-50 text-rose-600">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
              <span className="text-[10px] text-rose-600 block">{kpis?.expired_count ?? 0} Expired (Blocked)</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-purple-200 shadow-xs space-y-1 hover:border-purple-300 transition">
              <span className="text-[11px] font-bold text-purple-700 uppercase tracking-wider block">Procurement</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-purple-900">{kpis?.pending_purchase_orders_count ?? activePOCount}</span>
                <div className="p-1.5 rounded-lg bg-purple-50 text-purple-600">
                  <Truck className="w-4 h-4" />
                </div>
              </div>
              <span className="text-[10px] text-purple-600 block">{vendors.length} Active Suppliers</span>
            </div>
          </div>

          {/* Operational Intelligence Strip */}
          <div className="bg-gradient-to-r from-emerald-950 via-teal-950 to-slate-950 p-4 rounded-2xl text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-400/30">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-black uppercase tracking-wider text-emerald-400">
                  FEFO Automated Quality & Expiry Protection
                </h4>
                <p className="text-[11px] text-emerald-100/90 mt-0.5">
                  Near-expiry drugs are prioritized automatically. Expired batches are blocked at the database level to ensure 100% patient safety.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => setActiveTab('PRESCRIPTIONS')}
                className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs rounded-xl transition shadow-xs cursor-pointer"
              >
                Go to Rx Queue ({pendingPrescriptionsCount})
              </button>
            </div>
          </div>

          {/* Two-Column Analytics & Alerts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Realtime Stock Alerts */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" /> Critical Inventory Alerts
                </h3>
                <button onClick={() => setActiveTab('ALERTS')} className="text-xs text-emerald-700 font-bold hover:underline cursor-pointer">
                  View All ({alerts.length})
                </button>
              </div>

              {alerts.length === 0 ? (
                <div className="py-8 text-center text-slate-400 text-xs">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                  <p className="font-semibold text-slate-600">All drug stock levels are currently healthy.</p>
                  <p className="text-[11px]">No low stock or expiry warnings at this time.</p>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {alerts.slice(0, 4).map((alt) => (
                    <div
                      key={alt.id}
                      className={`p-3 rounded-xl border flex items-start justify-between gap-3 ${
                        alt.severity === 'CRITICAL'
                          ? 'bg-rose-50/80 border-rose-200 text-rose-900'
                          : alt.severity === 'HIGH'
                          ? 'bg-amber-50/80 border-amber-200 text-amber-900'
                          : 'bg-blue-50/80 border-blue-200 text-blue-900'
                      }`}
                    >
                      <div className="space-y-0.5">
                        <span className="font-bold text-xs flex items-center gap-1.5">
                          <AlertCircle className="w-3.5 h-3.5" />
                          {alt.title}
                        </span>
                        <p className="text-[11px] opacity-85 leading-relaxed">{alt.description}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-white/90 border border-current shrink-0">
                        {alt.severity}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* FEFO Matrix Quick Summary */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-4 h-4 text-emerald-600" /> Active Batches (FEFO Priority Order)
                </h3>
                <button onClick={() => setActiveTab('BATCHES')} className="text-xs text-emerald-700 font-bold hover:underline cursor-pointer">
                  Manage Batches ({batches.length})
                </button>
              </div>

              <div className="space-y-2.5">
                {Object.keys(groupedBatches).slice(0, 4).map((medName) => {
                  const medBatches = groupedBatches[medName];
                  const earliest = medBatches[0];

                  return (
                    <div key={medName} className="p-3 rounded-xl border border-slate-100 bg-slate-50/70 space-y-1.5">
                      <div className="flex justify-between items-center text-xs">
                        <strong className="text-slate-900 font-bold">{medName}</strong>
                        <span className="text-[10px] text-slate-500 font-mono font-bold">
                          {medBatches.reduce((s, b) => s + b.quantity, 0)} Units on Shelf
                        </span>
                      </div>

                      {earliest && (
                        <div className="flex justify-between items-center text-[11px] bg-white p-2 rounded-lg border border-emerald-200 shadow-2xs">
                          <span className="font-mono font-bold text-emerald-900 flex items-center gap-1">
                            🎯 Next Target: <span className="text-slate-800">{earliest.batch_number}</span>
                          </span>
                          <span className="text-[10px] font-bold text-rose-600">Expires: {earliest.expiry_date}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Quick Actions Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <button
              onClick={() => setActiveTab('PRESCRIPTIONS')}
              className="p-3 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-left font-bold text-slate-800 flex items-center justify-between transition shadow-2xs cursor-pointer"
            >
              <span>1. Dispense Prescriptions</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </button>
            <button
              onClick={() => setActiveTab('INVENTORY')}
              className="p-3 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-left font-bold text-slate-800 flex items-center justify-between transition shadow-2xs cursor-pointer"
            >
              <span>2. Check Drug Stock Levels</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </button>
            <button
              onClick={() => setActiveTab('PURCHASE_ORDERS')}
              className="p-3 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-left font-bold text-slate-800 flex items-center justify-between transition shadow-2xs cursor-pointer"
            >
              <span>3. Review Purchase Orders</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </button>
            <button
              onClick={() => setActiveTab('REPORTS')}
              className="p-3 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-left font-bold text-slate-800 flex items-center justify-between transition shadow-2xs cursor-pointer"
            >
              <span>4. Export Consumption Report</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>
      )}

      {/* TAB 2: PRESCRIPTIONS QUEUE */}
      {activeTab === 'PRESCRIPTIONS' && (
        <div className="space-y-4">
          {/* Controls */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search patient, token, or Rx ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div className="flex items-center gap-2 self-stretch sm:self-auto justify-end">
              <span className="text-xs text-slate-500 font-medium">Filter Status:</span>
              <select
                value={prescriptionStatusFilter}
                onChange={(e) => setPrescriptionStatusFilter(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="ALL">All Prescriptions ({prescriptions.length})</option>
                <option value="PENDING">Waiting for Dispense ({pendingPrescriptionsCount})</option>
                <option value="PARTIALLY_DISPENSED">Partially Dispensed</option>
                <option value="DISPENSED">Completed & Dispensed</option>
              </select>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">Rx & Token</th>
                    <th className="p-4">Patient Name</th>
                    <th className="p-4">Consulting Doctor</th>
                    <th className="p-4">Prescribed Medicines</th>
                    <th className="p-4">FEFO Target Batch</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {prescriptions.filter((p) => {
                    const matchSearch =
                      !searchQuery ||
                      p.patient_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      String(p.id).includes(searchQuery) ||
                      String((p as any).token_number || '').includes(searchQuery);
                    const matchStatus =
                      prescriptionStatusFilter === 'ALL' ||
                      (prescriptionStatusFilter === 'PENDING'
                        ? p.status === 'PENDING' || p.status === 'ACTIVE'
                        : p.status === prescriptionStatusFilter);
                    return matchSearch && matchStatus;
                  }).length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-10 text-center text-slate-400 font-medium">
                        <PackageCheck className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                        No prescriptions found matching your current filter.
                      </td>
                    </tr>
                  ) : (
                    prescriptions
                      .filter((p) => {
                        const matchSearch =
                          !searchQuery ||
                          p.patient_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          String(p.id).includes(searchQuery) ||
                          String((p as any).token_number || '').includes(searchQuery);
                        const matchStatus =
                          prescriptionStatusFilter === 'ALL' ||
                          (prescriptionStatusFilter === 'PENDING'
                            ? p.status === 'PENDING' || p.status === 'ACTIVE'
                            : p.status === prescriptionStatusFilter);
                        return matchSearch && matchStatus;
                      })
                      .map((p) => (
                        <tr key={p.id} className="hover:bg-slate-50/80 transition">
                          <td className="p-4 font-mono font-bold">
                            <div className="text-emerald-800">#RX-{String(p.id).padStart(4, '0')}</div>
                            {(p as any).token_number && (
                              <span className="inline-block mt-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[10px] font-mono font-bold border border-emerald-200">
                                Token #{(p as any).token_number}
                              </span>
                            )}
                          </td>
                          <td className="p-4">
                            <div className="font-bold text-slate-900 text-sm">{p.patient_name}</div>
                            <span className="text-[10px] text-slate-400 font-mono">Patient #{p.patient}</span>
                          </td>
                          <td className="p-4 text-slate-600 font-medium">{p.doctor_name || 'Staff Doctor'}</td>
                          <td className="p-4 space-y-1.5">
                            {p.items?.map((item, i) => (
                              <div key={i} className="text-slate-800 text-[11px] flex items-center justify-between gap-3 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200/60">
                                <span>
                                  <strong className="text-slate-900">{item.medicine_name}</strong> • {item.dosage} ({item.quantity} units)
                                </span>
                                <span
                                  className={`px-1.5 py-0.2 rounded text-[9px] font-black uppercase ${
                                    item.status === 'DISPENSED'
                                      ? 'bg-emerald-100 text-emerald-800'
                                      : 'bg-amber-100 text-amber-800'
                                  }`}
                                >
                                  {item.status}
                                </span>
                              </div>
                            ))}
                          </td>
                          <td className="p-4">
                            <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-900 border border-emerald-200 font-mono text-[10px] font-bold inline-block">
                              🎯 FEFO Auto-Selected
                            </span>
                          </td>
                          <td className="p-4">
                            <span
                              className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider inline-flex items-center gap-1 ${
                                p.status === 'DISPENSED'
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                  : p.status === 'PARTIALLY_DISPENSED'
                                  ? 'bg-blue-100 text-blue-800 border border-blue-200'
                                  : 'bg-amber-100 text-amber-900 border border-amber-200'
                              }`}
                            >
                              {p.status !== 'DISPENSED' && <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>}
                              {p.status}
                            </span>
                          </td>
                          <td className="p-4">
                            {p.status !== 'DISPENSED' ? (
                              <button
                                onClick={() => openDispenseModal(p)}
                                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition cursor-pointer"
                              >
                                <PackageCheck className="w-3.5 h-3.5" /> Dispense Rx
                              </button>
                            ) : (
                              <button
                                onClick={() => navigate(`/patients/${p.patient}`)}
                                className="inline-flex items-center gap-1 px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-[11px] rounded-lg transition cursor-pointer"
                              >
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                <span>Fulfilled</span>
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
        </div>
      )}

      {/* TAB 3: INVENTORY LEDGER */}
      {activeTab === 'INVENTORY' && (
        <div className="space-y-4">
          {/* Search & Category Filter Bar */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <div className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search medicine name or code..."
                value={medicineSearchQuery}
                onChange={(e) => setMedicineSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div className="flex flex-wrap items-center gap-1.5 self-stretch md:self-auto">
              {canCreateMedicine && (
                <button
                  onClick={() => setShowAddMedicineModal(true)}
                  className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition cursor-pointer self-start md:self-auto mr-2"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Medicine
                </button>
              )}
              <button
                onClick={() => setMedicineCategoryFilter('ALL')}
                className={`px-3 py-1 rounded-xl text-xs font-bold transition cursor-pointer ${
                  medicineCategoryFilter === 'ALL'
                    ? 'bg-emerald-600 text-white shadow-2xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                All Categories ({medicines.length})
              </button>
              {medicineCategories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setMedicineCategoryFilter(cat)}
                  className={`px-3 py-1 rounded-xl text-xs font-bold transition cursor-pointer ${
                    medicineCategoryFilter === cat
                      ? 'bg-emerald-600 text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">Drug Code</th>
                    <th className="p-4">Generic Name</th>
                    <th className="p-4">Brand Name</th>
                    <th className="p-4">Category</th>
                    <th className="p-4">Form & Strength</th>
                    <th className="p-4">Min / Reorder</th>
                    <th className="p-4">Available Qty</th>
                    <th className="p-4">Status</th>
                    {(canUpdateMedicine || canDeleteMedicine) && (
                      <th className="p-4 text-right">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredMedicines.length === 0 ? (
                    <tr>
                      <td colSpan={(canUpdateMedicine || canDeleteMedicine) ? 9 : 8} className="p-8 text-center text-slate-400 font-medium">
                        No medicines found matching the search criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredMedicines.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-50/80 transition">
                        <td className="p-4 font-mono font-bold text-slate-500">{m.code}</td>
                        <td className="p-4 font-bold text-slate-900 text-sm">{m.generic_name}</td>
                        <td className="p-4 text-slate-600 font-medium">{m.brand_name || '-'}</td>
                        <td className="p-4">
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                            {m.category}
                          </span>
                        </td>
                        <td className="p-4 text-slate-600">
                          {m.dosage_form} ({m.strength})
                        </td>
                        <td className="p-4 font-mono text-slate-600">
                          Min: {m.minimum_stock} | Reorder: {m.reorder_level}
                        </td>
                        <td className="p-4 font-mono font-black text-slate-900 text-sm">
                          {m.total_available_stock ?? 0} {m.unit}s
                        </td>
                        <td className="p-4">
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                              m.stock_status === 'OUT_OF_STOCK'
                                ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                : m.stock_status === 'LOW_STOCK'
                                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                            }`}
                          >
                            {m.stock_status || 'NORMAL'}
                          </span>
                        </td>
                        {(canUpdateMedicine || canDeleteMedicine) && (
                          <td className="p-4 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              {canUpdateMedicine && (
                                <button
                                  onClick={() => handleOpenEditMedicine(m)}
                                  title="Edit Medicine"
                                  className="p-1.5 hover:bg-slate-100 text-slate-500 hover:text-slate-800 rounded-lg transition cursor-pointer"
                                >
                                  <Edit2 className="w-3.5 h-3.5" />
                                </button>
                              )}
                              {canDeleteMedicine && (
                                <button
                                  onClick={() => handleDeleteMedicine(m.id)}
                                  title="Delete Medicine"
                                  className="p-1.5 hover:bg-rose-50 text-slate-400 hover:text-rose-600 rounded-lg transition cursor-pointer"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </div>
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}


      {/* TAB 4: BATCHES LEDGER */}
      {activeTab === 'BATCHES' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-4">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2">
              <Layers className="w-4 h-4 text-amber-600" />
              FEFO Priority Batch Comparison Matrix (Earliest Expiry First)
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.keys(groupedBatches).map((medName) => {
                const medBatches = groupedBatches[medName];

                return (
                  <div key={medName} className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-3">
                    <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                      <span className="font-bold text-slate-900 text-xs">{medName}</span>
                      <span className="text-[10px] font-bold text-slate-500 font-mono">
                        {medBatches.reduce((sum, b) => sum + b.quantity, 0)} Units Available
                      </span>
                    </div>

                    <div className="space-y-2">
                      {medBatches.map((b, idx) => {
                        const isEarliest = idx === 0;

                        return (
                          <div
                            key={b.id}
                            className={`p-3 rounded-lg border flex justify-between items-center transition ${
                              isEarliest
                                ? 'bg-amber-50 border-amber-400 text-slate-900 shadow-2xs'
                                : 'bg-white border-slate-200 text-slate-700'
                            }`}
                          >
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-bold text-xs">{b.batch_number}</span>
                                {isEarliest && (
                                  <span className="px-2 py-0.5 rounded text-[9px] font-black bg-amber-600 text-white uppercase tracking-wider">
                                    FEFO Auto-Selected (Expires First)
                                  </span>
                                )}
                              </div>
                              <span className="text-[10px] text-slate-500 block font-medium mt-0.5">
                                Vendor: {b.vendor_name || b.supplier} • Mfg: {b.mfg_date || 'N/A'} • Qty:{' '}
                                <strong className="text-slate-900">{b.quantity} units</strong>
                              </span>
                            </div>

                            <div className="text-right">
                              <span
                                className={`font-mono text-xs font-bold block ${
                                  isEarliest ? 'text-amber-800' : 'text-slate-700'
                                }`}
                              >
                                Exp: {b.expiry_date}
                              </span>
                              <span
                                className={`px-2 py-0.5 rounded text-[9px] font-bold mt-1 inline-block ${
                                  b.status === 'EXPIRED'
                                    ? 'bg-red-100 text-red-800'
                                    : b.status === 'EXPIRING_SOON'
                                    ? 'bg-amber-100 text-amber-800'
                                    : 'bg-emerald-100 text-emerald-800'
                                }`}
                              >
                                {b.status}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: TRANSACTIONS HISTORY */}
      {activeTab === 'TRANSACTIONS' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <History className="w-4 h-4 text-amber-600" /> Stock Audit & Transaction Log
            </h2>
            <span className="text-xs text-slate-500">{transactions.length} Total Audit Entries</span>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">Timestamp</th>
                    <th className="p-4">Type</th>
                    <th className="p-4">Medicine & Batch</th>
                    <th className="p-4">Quantity</th>
                    <th className="p-4">Reference</th>
                    <th className="p-4">Logged By</th>
                    <th className="p-4">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transactions.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-400 font-medium">
                        No transactions logged yet.
                      </td>
                    </tr>
                  ) : (
                    transactions.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-50 transition">
                        <td className="p-4 font-mono text-slate-500 text-[11px]">
                          {new Date(t.timestamp).toLocaleString()}
                        </td>
                        <td className="p-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[9px] font-black ${
                              t.transaction_type === 'DISPENSED'
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                : t.transaction_type === 'PURCHASE_RECEIVED'
                                ? 'bg-blue-100 text-blue-800 border border-blue-200'
                                : 'bg-slate-100 text-slate-800 border border-slate-200'
                            }`}
                          >
                            {t.transaction_type}
                          </span>
                        </td>
                        <td className="p-4 font-bold text-slate-900">
                          {t.medicine_name || 'Drug Item'}
                          <span className="block font-mono text-[10px] text-slate-400 font-normal">
                            Batch: {t.batch_number}
                          </span>
                        </td>
                        <td className="p-4 font-mono font-bold text-slate-900">
                          {t.quantity > 0 ? `+${t.quantity}` : t.quantity}
                        </td>
                        <td className="p-4 font-mono text-slate-500">{t.reference_id || '-'}</td>
                        <td className="p-4 text-slate-600">{t.created_by_name || 'System User'}</td>
                        <td className="p-4 text-slate-500 max-w-xs truncate">{t.notes || '-'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: VENDORS */}
      {activeTab === 'VENDORS' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <Building2 className="w-4 h-4 text-amber-600" /> Pharmaceutical Suppliers & Vendor Directory
              </h2>
              <p className="text-[11px] text-slate-500">
                Manage registered pharmaceutical vendors, order history, and procurement relationships.
              </p>
            </div>
            {!isReadOnly && (
              <button
                onClick={() => setShowAddVendorModal(true)}
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition self-start md:self-auto cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" /> Register Vendor
              </button>
            )}
          </div>

          {/* Search & Status Filters */}
          <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search vendor name, code, contact, GSTIN..."
                value={vendorSearch}
                onChange={(e) => setVendorSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
              />
            </div>

            <div className="flex items-center gap-1.5 self-start sm:self-auto">
              <span className="text-[11px] font-bold text-slate-500 mr-1 flex items-center gap-1">
                <Filter className="w-3 h-3" /> Status:
              </span>
              {(['ALL', 'ACTIVE', 'INACTIVE'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setVendorStatusFilter(st)}
                  className={`px-3 py-1 rounded-xl text-xs font-bold transition ${
                    vendorStatusFilter === st
                      ? 'bg-amber-600 text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Vendors Grid */}
          {(() => {
            const filteredVendors = vendors.filter((v) => {
              const matchesSearch =
                !vendorSearch ||
                (v.vendor_name || v.name || '').toLowerCase().includes(vendorSearch.toLowerCase()) ||
                (v.vendor_code || '').toLowerCase().includes(vendorSearch.toLowerCase()) ||
                (v.contact_person || '').toLowerCase().includes(vendorSearch.toLowerCase()) ||
                (v.phone || '').includes(vendorSearch) ||
                (v.email || '').toLowerCase().includes(vendorSearch.toLowerCase()) ||
                (v.gst_number || v.gstin || '').toLowerCase().includes(vendorSearch.toLowerCase());

              const isActive = v.status === 'ACTIVE' || v.active !== false;
              const matchesStatus =
                vendorStatusFilter === 'ALL' ||
                (vendorStatusFilter === 'ACTIVE' && isActive) ||
                (vendorStatusFilter === 'INACTIVE' && !isActive);

              return matchesSearch && matchesStatus;
            });

            if (filteredVendors.length === 0) {
              return (
                <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-2">
                  <Building2 className="w-10 h-10 text-slate-300 mx-auto" />
                  <h3 className="text-sm font-bold text-slate-700">No vendors found</h3>
                  <p className="text-xs text-slate-400">
                    {vendorSearch ? 'Try clearing your search query.' : 'No vendors registered yet for this facility.'}
                  </p>
                </div>
              );
            }

            return (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredVendors.map((v) => {
                  const isActive = v.status === 'ACTIVE' || v.active !== false;
                  return (
                    <div
                      key={v.id}
                      className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs hover:border-amber-300 transition space-y-3 flex flex-col justify-between"
                    >
                      <div className="space-y-2.5">
                        <div className="flex justify-between items-start">
                          <div>
                            <span className="font-mono text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                              {v.vendor_code || `VEND-${v.id}`}
                            </span>
                            <h3 className="font-bold text-slate-900 text-sm mt-1">{v.vendor_name || v.name}</h3>
                          </div>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              isActive ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}
                          >
                            {isActive ? 'ACTIVE' : 'INACTIVE'}
                          </span>
                        </div>

                        <div className="space-y-1 text-xs text-slate-600">
                          <p>
                            <strong className="text-slate-700">Contact:</strong> {v.contact_person || 'N/A'}
                          </p>
                          <p className="truncate">
                            <strong className="text-slate-700">Phone:</strong> {v.phone || 'N/A'} |{' '}
                            <strong className="text-slate-700">Email:</strong> {v.email || 'N/A'}
                          </p>
                          <p>
                            <strong className="text-slate-700">GSTIN:</strong>{' '}
                            <span className="font-mono">{v.gst_number || v.gstin || 'N/A'}</span>
                          </p>
                          <p className="text-[11px] text-slate-400 truncate">{v.address || 'N/A'}</p>
                        </div>

                        {/* Order Performance Strip */}
                        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 grid grid-cols-3 text-center text-xs">
                          <div>
                            <span className="text-[10px] text-slate-400 font-bold block uppercase">Total POs</span>
                            <span className="font-mono font-bold text-slate-800">{v.po_count ?? v.purchase_orders_count ?? 0}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 font-bold block uppercase">Completed</span>
                            <span className="font-mono font-bold text-emerald-700">{v.completed_orders ?? 0}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 font-bold block uppercase">Total Spend</span>
                            <span className="font-mono font-bold text-slate-900">₹{Number(v.total_spend ?? 0).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>

                      {/* Card Actions */}
                      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs gap-2">
                        <button
                          onClick={() => handleViewVendorDetails(v)}
                          className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-lg flex items-center gap-1 transition"
                        >
                          <Eye className="w-3.5 h-3.5" /> Details & History
                        </button>

                        {!isReadOnly && (
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => handleToggleVendorStatus(v)}
                              title={isActive ? 'Deactivate Vendor' : 'Activate Vendor'}
                              className={`px-2 py-1 rounded-lg text-[11px] font-bold border transition ${
                                isActive
                                  ? 'border-amber-200 text-amber-700 hover:bg-amber-50'
                                  : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                              }`}
                            >
                              {isActive ? 'Deactivate' : 'Activate'}
                            </button>
                            <button
                              onClick={() => handleOpenEditVendor(v)}
                              title="Edit Vendor Details"
                              className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                            {isHospitalAdmin && (
                              <button
                                onClick={() => handleDeleteVendor(v)}
                                title="Delete Vendor"
                                className="p-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })()}
        </div>
      )}

      {/* TAB 7: PURCHASE ORDERS */}
      {activeTab === 'PURCHASE_ORDERS' && (
        <div className="space-y-4">
          {/* Header */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <Truck className="w-4 h-4 text-amber-600" /> Purchase Orders & Procurement Ledger
              </h2>
              <p className="text-[11px] text-slate-500">
                End-to-end drug procurement workflow: Draft → Submit for Approval → Order Placement → Goods Receiving with Batch Ledger.
              </p>
            </div>
            {!isReadOnly && (
              <button
                onClick={() => setShowCreatePOModal(true)}
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition self-start md:self-auto cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" /> Create New PO
              </button>
            )}
          </div>

          {/* Procurement KPI Summary Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Total Orders</span>
              <span className="text-xl font-black text-slate-900 font-mono">
                {procurementKpis?.total_orders ?? purchaseOrders.length}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Drafts</span>
              <span className="text-xl font-black text-slate-700 font-mono">
                {procurementKpis?.draft ?? purchaseOrders.filter((p) => p.status === 'DRAFT').length}
              </span>
            </div>

            <div className={`p-3 rounded-xl bg-white shadow-2xs space-y-1 border ${
              (procurementKpis?.pending_approval ?? 0) > 0 ? 'border-amber-400 bg-amber-50/40' : 'border-slate-200'
            }`}>
              <span className="text-[10px] font-bold text-amber-800 uppercase block">Pending Approval</span>
              <span className="text-xl font-black text-amber-700 font-mono">
                {procurementKpis?.pending_approval ?? purchaseOrders.filter((p) => ['PENDING_APPROVAL', 'PENDING'].includes(p.status)).length}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white border border-blue-200 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold text-blue-800 uppercase block">In Transit</span>
              <span className="text-xl font-black text-blue-700 font-mono">
                {(procurementKpis?.ordered ?? 0) + (procurementKpis?.approved ?? 0)}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white border border-purple-200 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold text-purple-800 uppercase block">Partially Recv</span>
              <span className="text-xl font-black text-purple-700 font-mono">
                {procurementKpis?.partially_received ?? purchaseOrders.filter((p) => p.status === 'PARTIALLY_RECEIVED').length}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white border border-emerald-200 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold text-emerald-800 uppercase block">Completed</span>
              <span className="text-xl font-black text-emerald-700 font-mono">
                {procurementKpis?.received ?? purchaseOrders.filter((p) => p.status === 'RECEIVED').length}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1 col-span-2 sm:col-span-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Total Spend</span>
              <span className="text-base font-black text-emerald-800 font-mono">
                ₹{Number(procurementKpis?.total_spend ?? 0).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Status Filter Tabs & Search */}
          <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-center justify-between gap-3">
            <div className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search PO number, vendor, drug item..."
                value={poSearchQuery}
                onChange={(e) => setPoSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
              />
            </div>

            <div className="flex items-center gap-1 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
              {(
                [
                  { id: 'ALL', label: 'All' },
                  { id: 'DRAFT', label: 'Draft' },
                  { id: 'PENDING_APPROVAL', label: 'Pending Approval' },
                  { id: 'APPROVED', label: 'Approved' },
                  { id: 'ORDERED', label: 'Ordered' },
                  { id: 'PARTIALLY_RECEIVED', label: 'Partially Recv' },
                  { id: 'RECEIVED', label: 'Received' },
                  { id: 'CANCELLED', label: 'Cancelled' },
                ] as const
              ).map((tab) => {
                const count =
                  tab.id === 'ALL'
                    ? purchaseOrders.length
                    : tab.id === 'PENDING_APPROVAL'
                    ? purchaseOrders.filter((p) => ['PENDING_APPROVAL', 'PENDING'].includes(p.status)).length
                    : purchaseOrders.filter((p) => p.status === tab.id).length;

                return (
                  <button
                    key={tab.id}
                    onClick={() => setPoStatusFilter(tab.id)}
                    className={`px-3 py-1 rounded-xl text-xs font-bold whitespace-nowrap transition flex items-center gap-1.5 ${
                      poStatusFilter === tab.id
                        ? 'bg-amber-600 text-white shadow-2xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    <span>{tab.label}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                        poStatusFilter === tab.id ? 'bg-amber-800/60 text-white' : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* PO Table */}
          {(() => {
            const filteredPOs = purchaseOrders.filter((po) => {
              const matchesStatus =
                poStatusFilter === 'ALL' ||
                po.status === poStatusFilter ||
                (poStatusFilter === 'PENDING_APPROVAL' && po.status === 'PENDING');

              const matchesSearch =
                !poSearchQuery ||
                po.po_number.toLowerCase().includes(poSearchQuery.toLowerCase()) ||
                (po.vendor_name || '').toLowerCase().includes(poSearchQuery.toLowerCase()) ||
                (po.notes || '').toLowerCase().includes(poSearchQuery.toLowerCase()) ||
                (po.items || []).some((it) => (it.medicine_name || '').toLowerCase().includes(poSearchQuery.toLowerCase()));

              return matchesStatus && matchesSearch;
            });

            return (
              <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                      <tr>
                        <th className="p-4">PO Number</th>
                        <th className="p-4">Vendor</th>
                        <th className="p-4">Dates</th>
                        <th className="p-4">Total Amount</th>
                        <th className="p-4">Items Summary</th>
                        <th className="p-4">Status</th>
                        <th className="p-4">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredPOs.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="p-12 text-center text-slate-400 font-medium">
                            No purchase orders found matching the filter criteria.
                          </td>
                        </tr>
                      ) : (
                        filteredPOs.map((po) => {
                          const statusColor =
                            po.status === 'RECEIVED'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : po.status === 'PARTIALLY_RECEIVED'
                              ? 'bg-purple-100 text-purple-800 border-purple-200'
                              : po.status === 'ORDERED'
                              ? 'bg-blue-100 text-blue-800 border-blue-200'
                              : po.status === 'APPROVED'
                              ? 'bg-teal-100 text-teal-800 border-teal-200'
                              : po.status === 'PENDING_APPROVAL' || po.status === 'PENDING'
                              ? 'bg-amber-100 text-amber-800 border-amber-300'
                              : po.status === 'CANCELLED'
                              ? 'bg-red-100 text-red-800 border-red-200'
                              : 'bg-slate-100 text-slate-700 border-slate-300';

                          return (
                            <tr key={po.id} className="hover:bg-slate-50/80 transition">
                              <td className="p-4">
                                <button
                                  onClick={() => setSelectedPOForDetails(po)}
                                  className="font-mono font-bold text-amber-700 hover:text-amber-800 hover:underline flex items-center gap-1"
                                >
                                  {po.po_number}
                                </button>
                                <span className="text-[10px] text-slate-400 block font-sans">
                                  Created by: {po.created_by_name || 'Pharmacist'}
                                </span>
                              </td>
                              <td className="p-4">
                                <span className="font-bold text-slate-900 block">{po.vendor_name}</span>
                                <span className="font-mono text-[10px] text-slate-400">{po.vendor_code || `VEND-${po.vendor}`}</span>
                              </td>
                              <td className="p-4 space-y-0.5 text-slate-600">
                                <div>
                                  <span className="text-[10px] text-slate-400 block">Ordered:</span>
                                  <span>{po.order_date}</span>
                                </div>
                                {po.expected_delivery && (
                                  <div className="text-[10px] text-slate-500">
                                    Expected: <span className="font-mono">{po.expected_delivery}</span>
                                  </div>
                                )}
                              </td>
                              <td className="p-4 font-mono font-bold text-slate-900 text-sm">
                                ₹{Number(po.total_amount).toLocaleString()}
                              </td>
                              <td className="p-4 space-y-1 max-w-xs">
                                <span className="font-bold text-slate-700 text-[11px] block">
                                  {po.items?.length || 0} item{(po.items?.length || 0) !== 1 ? 's' : ''} requested:
                                </span>
                                {po.items?.slice(0, 2).map((it, idx) => (
                                  <div key={idx} className="text-[11px] text-slate-600 truncate">
                                    • {it.medicine_name} ({it.ordered_quantity ?? it.requested_quantity ?? 0} units)
                                  </div>
                                ))}
                                {(po.items?.length || 0) > 2 && (
                                  <span className="text-[10px] text-amber-700 font-bold block">
                                    + {(po.items?.length || 0) - 2} more item(s)...
                                  </span>
                                )}
                              </td>
                              <td className="p-4">
                                <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border ${statusColor}`}>
                                  {po.status}
                                </span>
                              </td>
                              <td className="p-4">
                                <div className="flex items-center gap-1.5">
                                  <button
                                    onClick={() => setSelectedPOForDetails(po)}
                                    className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition flex items-center gap-1"
                                  >
                                    <Eye className="w-3.5 h-3.5" /> Details
                                  </button>

                                  {/* Quick Actions */}
                                  {po.status === 'DRAFT' && !isReadOnly && (
                                    <button
                                      onClick={() => handleSubmitPOForApproval(po.id)}
                                      className="px-2.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl transition flex items-center gap-1 shadow-2xs"
                                    >
                                      <Send className="w-3 h-3" /> Submit
                                    </button>
                                  )}

                                  {(po.status === 'PENDING_APPROVAL' || po.status === 'PENDING') && isHospitalAdmin && (
                                    <button
                                      onClick={() => setSelectedPOForDetails(po)}
                                      className="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl transition flex items-center gap-1 shadow-2xs"
                                    >
                                      <Check className="w-3.5 h-3.5" /> Review
                                    </button>
                                  )}

                                  {po.status === 'APPROVED' && !isReadOnly && (
                                    <button
                                      onClick={() => handlePlaceOrder(po.id)}
                                      className="px-2.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl transition flex items-center gap-1 shadow-2xs"
                                    >
                                      <Truck className="w-3.5 h-3.5" /> Order
                                    </button>
                                  )}

                                  {(po.status === 'ORDERED' || po.status === 'PARTIALLY_RECEIVED') && !isReadOnly && (
                                    <button
                                      onClick={() => openReceivingModal(po)}
                                      className="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl transition flex items-center gap-1 shadow-2xs"
                                    >
                                      <PackageCheck className="w-3.5 h-3.5" /> Receive
                                    </button>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })()}
        </div>
      )}

      {/* TAB 8: ALERTS */}
      {activeTab === 'ALERTS' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600" /> Active Pharmacy Inventory & Expiry Alerts
              </h2>
              <p className="text-[11px] text-slate-500">
                Automated stock surveillance: Low-stock triggers, near-expiry alerts, and procurement reminders.
              </p>
            </div>
            <span className="text-xs text-slate-500 font-bold bg-slate-100 px-3 py-1 rounded-xl">
              {alerts.length} Warnings Active
            </span>
          </div>

          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center text-slate-400 font-medium space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                <p>No active stock or expiry alerts for this facility! Inventory levels are optimal.</p>
              </div>
            ) : (
              alerts.map((alt) => (
                <div
                  key={alt.id}
                  className={`p-4 rounded-2xl border flex items-start justify-between shadow-xs ${
                    alt.severity === 'CRITICAL'
                      ? 'bg-red-50 border-red-200 text-red-900'
                      : alt.severity === 'HIGH'
                      ? 'bg-amber-50 border-amber-200 text-amber-900'
                      : 'bg-blue-50 border-blue-200 text-blue-900'
                  }`}
                >
                  <div className="space-y-1">
                    <span className="font-bold text-sm flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" /> {alt.title}
                    </span>
                    <p className="text-xs opacity-90">{alt.description}</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-wider bg-white/90 border border-current shadow-2xs">
                      {alt.severity}
                    </span>
                    {(alt.type === 'LOW_STOCK' || alt.type === 'OUT_OF_STOCK') && !isReadOnly && (
                      <button
                        onClick={() => {
                          const medId = alt.medicine_id || 0;
                          const med = medicines.find((m) => m.id === medId);
                          setActiveTab('PURCHASE_ORDERS');
                          setNewPOData({
                            vendor: vendors[0]?.id || 0,
                            expected_delivery: '',
                            notes: `Restock triggered from inventory alert: ${alt.title}`,
                            items: [
                              {
                                medicine: medId,
                                requested_quantity: med ? Math.max(100, (med.reorder_level || 50) * 2) : 100,
                                unit_cost: 10.0,
                              },
                            ],
                          });
                          setShowCreatePOModal(true);
                        }}
                        className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl transition shadow-xs flex items-center gap-1"
                      >
                        <Truck className="w-3.5 h-3.5" /> Reorder Now
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 9: REPORTS */}
      {activeTab === 'REPORTS' && (
        <div className="space-y-6">
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-amber-600" /> Pharmacy Analytics & Stock Valuation
              </h2>
              <p className="text-[11px] text-slate-500">Government compliance reports and stock consumption analytics</p>
            </div>
            <button
              onClick={exportCSVReport}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-2 transition"
            >
              <Download className="w-4 h-4" /> Export CSV Report
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2">
                Real-time Stock Valuation
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-500">Total Active Batches:</span>
                  <span className="font-bold text-slate-900 font-mono">
                    {reportSummary?.stock_valuation?.total_batches ?? batches.length}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-500">Total Stock Quantity:</span>
                  <span className="font-bold text-slate-900 font-mono">
                    {reportSummary?.stock_valuation?.total_quantity ?? kpis?.total_available_stock ?? 0} Units
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm pt-2 border-t border-slate-100">
                  <span className="font-bold text-slate-700">Total Stock Valuation:</span>
                  <span className="font-black text-emerald-700 font-mono text-base">
                    ₹{Number(reportSummary?.stock_valuation?.total_value ?? totalValuation ?? 0).toLocaleString('en-IN')}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2">
                Top Consumed Essential Medicines
              </h3>
              <div className="space-y-2">
                {(!reportSummary?.consumption_summary || reportSummary.consumption_summary.length === 0) ? (
                  <p className="text-xs text-slate-400 italic">No consumption records available.</p>
                ) : (
                  reportSummary.consumption_summary.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center p-2 rounded-xl bg-slate-50 text-xs">
                      <div>
                        <strong className="text-slate-900 font-bold block">{item.batch__medicine__generic_name}</strong>
                        <span className="text-[10px] text-slate-400">{item.batch__medicine__brand_name}</span>
                      </div>
                      <span className="font-mono font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded">
                        {item.total_consumed} Units Consumed
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DISPENSE MODAL */}
      {dispenseModalRx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-2xl rounded-2xl border border-slate-200 shadow-xl overflow-hidden space-y-4 p-6">
            <div className="flex justify-between items-start border-b border-slate-100 pb-3">
              <div>
                <span className="font-mono font-bold text-xs text-amber-700">
                  #RX-{String(dispenseModalRx.id).padStart(4, '0')}
                </span>
                <h2 className="text-base font-bold text-slate-900">
                  Controlled FEFO Dispense for {dispenseModalRx.patient_name}
                </h2>
              </div>
              <button
                onClick={() => setDispenseModalRx(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-sm"
              >
                ✕
              </button>
            </div>

            {dispensingError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-800 rounded-xl text-xs font-medium">
                {dispensingError}
              </div>
            )}

            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Prescribed Items & FEFO Batch Selection</h3>

              {dispenseItems.map((item, idx) => {
                // Get non-expired batches for dropdown option
                const availableBatches = batches.filter(
                  (b) =>
                    matchMedicineBatch(b.medicine_name || b.generic_name, item.medicine_name) &&
                    b.quantity > 0 &&
                    new Date(b.expiry_date) > new Date()
                );

                return (
                  <div key={idx} className="p-3 rounded-xl border border-slate-200 bg-slate-50 space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <strong className="text-slate-900 font-bold text-sm">{item.medicine_name}</strong>
                      <span className="text-slate-500 font-mono">Prescribed: {item.target_qty} units</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                          Select Batch (FEFO Auto-Ranked)
                        </label>
                        <select
                          value={item.batch_id}
                          onChange={(e) => {
                            const val = Number(e.target.value);
                            setDispenseItems((prev) =>
                              prev.map((it, i) => (i === idx ? { ...it, batch_id: val } : it))
                            );
                          }}
                          className="w-full bg-white border border-slate-200 rounded-xl px-2.5 py-1.5 text-xs font-bold text-slate-800"
                        >
                          <option value={0}>-- Select Valid Batch --</option>
                          {availableBatches.map((b) => (
                            <option key={b.id} value={b.id}>
                              {b.batch_number} (Exp: {b.expiry_date} | Avail: {b.quantity})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                          Quantity to Dispense
                        </label>
                        <input
                          type="number"
                          min={1}
                          max={item.target_qty}
                          value={item.qty_to_dispense}
                          onChange={(e) => {
                            const val = Number(e.target.value);
                            setDispenseItems((prev) =>
                              prev.map((it, i) => (i === idx ? { ...it, qty_to_dispense: val } : it))
                            );
                          }}
                          className="w-full bg-white border border-slate-200 rounded-xl px-2.5 py-1.5 text-xs font-bold text-slate-800"
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                onClick={() => setDispenseModalRx(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDispense}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xs transition"
              >
                Confirm & Dispense Stock
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ADD VENDOR MODAL */}
      {showAddVendorModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleAddVendor}
            className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4"
          >
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-amber-600" /> Register New Supplier / Vendor
              </h2>
              <button
                type="button"
                onClick={() => setShowAddVendorModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Vendor Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. VEND-KSMSCL"
                  value={newVendorData.vendor_code}
                  onChange={(e) => setNewVendorData({ ...newVendorData, vendor_code: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-mono"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Company / Vendor Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. KSMSCL Pharma Supplies"
                  value={newVendorData.name}
                  onChange={(e) => setNewVendorData({ ...newVendorData, name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Contact Person</label>
                <input
                  type="text"
                  placeholder="e.g. Rajesh Kumar"
                  value={newVendorData.contact_person}
                  onChange={(e) => setNewVendorData({ ...newVendorData, contact_person: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Phone Number</label>
                <input
                  type="text"
                  placeholder="e.g. +91 98765 43210"
                  value={newVendorData.phone}
                  onChange={(e) => setNewVendorData({ ...newVendorData, phone: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Email Address</label>
                <input
                  type="email"
                  placeholder="orders@ksmscl.in"
                  value={newVendorData.email}
                  onChange={(e) => setNewVendorData({ ...newVendorData, email: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">GSTIN</label>
                <input
                  type="text"
                  placeholder="29AAAAA0000A1Z5"
                  value={newVendorData.gstin}
                  onChange={(e) => setNewVendorData({ ...newVendorData, gstin: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-mono"
                />
              </div>

              <div className="col-span-2">
                <label className="font-bold text-slate-700 block mb-1">Office Address</label>
                <textarea
                  rows={2}
                  placeholder="Enter full vendor address..."
                  value={newVendorData.address}
                  onChange={(e) => setNewVendorData({ ...newVendorData, address: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowAddVendorModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xs transition"
              >
                Save Vendor
              </button>
            </div>
          </form>
        </div>
      )}

      {/* EDIT VENDOR MODAL */}
      {editingVendor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleSaveEditVendor}
            className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4"
          >
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <span className="font-mono text-xs font-bold text-amber-700">{editingVendor.vendor_code || `VEND-${editingVendor.id}`}</span>
                <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Edit2 className="w-4 h-4 text-amber-600" /> Edit Vendor Information
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setEditingVendor(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="col-span-2">
                <label className="font-bold text-slate-700 block mb-1">Company / Vendor Name</label>
                <input
                  type="text"
                  required
                  value={editVendorData.name}
                  onChange={(e) => setEditVendorData({ ...editVendorData, name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Contact Person</label>
                <input
                  type="text"
                  value={editVendorData.contact_person}
                  onChange={(e) => setEditVendorData({ ...editVendorData, contact_person: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Phone Number</label>
                <input
                  type="text"
                  value={editVendorData.phone}
                  onChange={(e) => setEditVendorData({ ...editVendorData, phone: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Email Address</label>
                <input
                  type="email"
                  value={editVendorData.email}
                  onChange={(e) => setEditVendorData({ ...editVendorData, email: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">GSTIN</label>
                <input
                  type="text"
                  value={editVendorData.gstin}
                  onChange={(e) => setEditVendorData({ ...editVendorData, gstin: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-mono"
                />
              </div>

              <div className="col-span-2">
                <label className="font-bold text-slate-700 block mb-1">Office Address</label>
                <textarea
                  rows={2}
                  value={editVendorData.address}
                  onChange={(e) => setEditVendorData({ ...editVendorData, address: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingVendor(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xs transition"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      )}

      {/* VENDOR DETAILS & HISTORY MODAL */}
      {selectedVendorForDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-3xl rounded-2xl border border-slate-200 shadow-2xl overflow-hidden p-6 space-y-4 max-h-[90vh] flex flex-col justify-between">
            <div className="flex justify-between items-start border-b border-slate-100 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded border border-amber-200">
                    {selectedVendorForDetails.vendor_code || `VEND-${selectedVendorForDetails.id}`}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      selectedVendorForDetails.status === 'ACTIVE' || selectedVendorForDetails.active !== false
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {selectedVendorForDetails.status || (selectedVendorForDetails.active !== false ? 'ACTIVE' : 'INACTIVE')}
                  </span>
                </div>
                <h2 className="text-base font-bold text-slate-900 mt-1">
                  {selectedVendorForDetails.vendor_name || selectedVendorForDetails.name}
                </h2>
              </div>
              <button
                onClick={() => setSelectedVendorForDetails(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-lg"
              >
                ✕
              </button>
            </div>

            <div className="overflow-y-auto space-y-4 pr-1">
              {/* Contact and Metadata */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Contact Person</span>
                  <span className="font-bold text-slate-800">{selectedVendorForDetails.contact_person || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Phone</span>
                  <span className="font-mono text-slate-800">{selectedVendorForDetails.phone || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Email</span>
                  <span className="text-slate-800 truncate block">{selectedVendorForDetails.email || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">GSTIN</span>
                  <span className="font-mono font-bold text-slate-800">{selectedVendorForDetails.gst_number || selectedVendorForDetails.gstin || 'N/A'}</span>
                </div>
                <div className="col-span-2 sm:col-span-4 pt-2 border-t border-slate-200">
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Office Address</span>
                  <span className="text-slate-700">{selectedVendorForDetails.address || 'N/A'}</span>
                </div>
              </div>

              {/* Financial & Procurement Metrics */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center">
                  <span className="text-[10px] text-slate-500 font-bold uppercase block">Total Orders</span>
                  <span className="text-xl font-bold font-mono text-slate-900">
                    {selectedVendorForDetails.po_count ?? selectedVendorForDetails.purchase_orders_count ?? vendorHistory.length}
                  </span>
                </div>
                <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-xl text-center">
                  <span className="text-[10px] text-emerald-800 font-bold uppercase block">Completed Deliveries</span>
                  <span className="text-xl font-bold font-mono text-emerald-700">
                    {selectedVendorForDetails.completed_orders ?? vendorHistory.filter((p) => p.status === 'RECEIVED').length}
                  </span>
                </div>
                <div className="p-3 bg-amber-50/60 border border-amber-200 rounded-xl text-center">
                  <span className="text-[10px] text-amber-800 font-bold uppercase block">Total Spend</span>
                  <span className="text-xl font-bold font-mono text-amber-900">
                    ₹{Number(selectedVendorForDetails.total_spend ?? 0).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Purchase History Ledger */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <History className="w-3.5 h-3.5 text-amber-600" /> Historical Purchase Orders
                </h3>

                {loadingVendorHistory ? (
                  <div className="p-8 text-center text-xs text-slate-400 font-medium">Loading purchase order ledger...</div>
                ) : vendorHistory.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-400 font-medium bg-slate-50 rounded-xl border border-slate-200">
                    No purchase orders recorded for this supplier yet.
                  </div>
                ) : (
                  <div className="rounded-xl border border-slate-200 overflow-hidden text-xs">
                    <table className="w-full text-left">
                      <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                        <tr>
                          <th className="p-2.5">PO Number</th>
                          <th className="p-2.5">Order Date</th>
                          <th className="p-2.5">Items</th>
                          <th className="p-2.5">Total Amount</th>
                          <th className="p-2.5">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {vendorHistory.map((po) => (
                          <tr key={po.id} className="hover:bg-slate-50">
                            <td className="p-2.5 font-mono font-bold text-amber-700">{po.po_number}</td>
                            <td className="p-2.5 text-slate-600">{po.order_date}</td>
                            <td className="p-2.5 text-slate-600">{po.items?.length || 0} items</td>
                            <td className="p-2.5 font-mono font-bold text-slate-900">₹{Number(po.total_amount).toLocaleString()}</td>
                            <td className="p-2.5">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  po.status === 'RECEIVED'
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : po.status === 'ORDERED' || po.status === 'PARTIALLY_RECEIVED'
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-amber-100 text-amber-800'
                                }`}
                              >
                                {po.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <button
                onClick={() => setSelectedVendorForDetails(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CREATE PO MODAL (WITH DRUG GUIDANCE) */}
      {showCreatePOModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleCreatePO}
            className="bg-white w-full max-w-2xl rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4 max-h-[90vh] flex flex-col justify-between"
          >
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Truck className="w-4 h-4 text-amber-600" /> Create New Purchase Order (Draft)
                </h2>
                <p className="text-[11px] text-slate-400">
                  Facility: <strong className="text-slate-700">{activeFacility?.facility_name}</strong>
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowCreatePOModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3.5 text-xs overflow-y-auto pr-1">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Select Supplier / Vendor *</label>
                  <select
                    required
                    value={newPOData.vendor}
                    onChange={(e) => setNewPOData({ ...newPOData, vendor: Number(e.target.value) })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold"
                  >
                    <option value={0}>-- Select Vendor --</option>
                    {vendors.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.vendor_name || v.name || `Vendor #${v.id}`} ({v.vendor_code || `VEND-${v.id}`})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Expected Delivery Date</label>
                  <input
                    type="date"
                    value={newPOData.expected_delivery}
                    onChange={(e) => setNewPOData({ ...newPOData, expected_delivery: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                  />
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">PO Remarks / Requisition Notes</label>
                <input
                  type="text"
                  placeholder="Emergency replenishment for outpatient demand..."
                  value={newPOData.notes}
                  onChange={(e) => setNewPOData({ ...newPOData, notes: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              {/* Items List with Drug Stock Guidance */}
              <div className="space-y-2 border-t border-slate-100 pt-3">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px] block">
                      Requested EDL Medicines & Quantities
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Live stock balance & threshold guidance is automatically computed per medicine.
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setNewPOData({
                        ...newPOData,
                        items: [...newPOData.items, { medicine: 0, requested_quantity: 100, unit_cost: 10.0 }],
                      })
                    }
                    className="text-[11px] font-bold text-amber-700 hover:text-amber-800 bg-amber-50 hover:bg-amber-100 px-2.5 py-1 rounded-lg border border-amber-200 flex items-center gap-1 transition"
                  >
                    <Plus className="w-3 h-3" /> Add Drug Row
                  </button>
                </div>

                {newPOData.items.map((item, idx) => {
                  const selectedMed = medicines.find((m) => m.id === item.medicine);
                  const currentStock = batches
                    .filter((b) => b.medicine === item.medicine && !b.is_expired && new Date(b.expiry_date) > new Date())
                    .reduce((acc, b) => acc + (Number(b.quantity) || 0), 0);

                  return (
                    <div
                      key={idx}
                      className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-2 hover:border-slate-300 transition"
                    >
                      <div className="grid grid-cols-12 gap-2 items-center">
                        <div className="col-span-6">
                          <label className="text-[10px] font-bold text-slate-500 uppercase block mb-0.5">Medicine *</label>
                          <select
                            value={item.medicine}
                            onChange={(e) => {
                              const val = Number(e.target.value);
                              setNewPOData({
                                ...newPOData,
                                items: newPOData.items.map((it, i) => (i === idx ? { ...it, medicine: val } : it)),
                              });
                            }}
                            className="w-full bg-white border border-slate-200 rounded-xl px-2 py-1.5 text-xs font-bold"
                          >
                            <option value={0}>-- Select Medicine --</option>
                            {medicines.map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.generic_name} ({m.brand_name || m.strength})
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="col-span-3">
                          <label className="text-[10px] font-bold text-slate-500 uppercase block mb-0.5">Quantity *</label>
                          <input
                            type="number"
                            min={1}
                            placeholder="Qty"
                            value={item.requested_quantity}
                            onChange={(e) => {
                              const val = Number(e.target.value);
                              setNewPOData({
                                ...newPOData,
                                items: newPOData.items.map((it, i) => (i === idx ? { ...it, requested_quantity: val } : it)),
                              });
                            }}
                            className="w-full bg-white border border-slate-200 rounded-xl px-2 py-1.5 text-xs font-bold font-mono"
                          />
                        </div>

                        <div className="col-span-2">
                          <label className="text-[10px] font-bold text-slate-500 uppercase block mb-0.5">Unit Cost (₹)</label>
                          <input
                            type="number"
                            step="0.1"
                            placeholder="Cost"
                            value={item.unit_cost}
                            onChange={(e) => {
                              const val = Number(e.target.value);
                              setNewPOData({
                                ...newPOData,
                                items: newPOData.items.map((it, i) => (i === idx ? { ...it, unit_cost: val } : it)),
                              });
                            }}
                            className="w-full bg-white border border-slate-200 rounded-xl px-2 py-1.5 text-xs font-bold font-mono"
                          />
                        </div>

                        <div className="col-span-1 text-center pt-3">
                          {newPOData.items.length > 1 && (
                            <button
                              type="button"
                              onClick={() =>
                                setNewPOData({
                                  ...newPOData,
                                  items: newPOData.items.filter((_, i) => i !== idx),
                                })
                              }
                              title="Remove item"
                              className="text-red-400 hover:text-red-600 font-bold text-sm"
                            >
                              ✕
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Stock Guidance Pill */}
                      {selectedMed && (
                        <div className="pt-1.5 border-t border-slate-200 flex items-center justify-between text-[11px]">
                          <span className="text-slate-500">
                            Current Stock: <strong className="font-mono text-slate-800">{currentStock}</strong> | Min: {selectedMed.minimum_stock ?? 50} | Reorder: {selectedMed.reorder_level ?? 100}
                          </span>
                          {currentStock <= (selectedMed.minimum_stock ?? 50) ? (
                            <span className="px-1.5 py-0.2 rounded bg-red-100 text-red-800 font-bold text-[10px] border border-red-200">
                              CRITICAL LOW
                            </span>
                          ) : currentStock <= (selectedMed.reorder_level ?? 100) ? (
                            <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 font-bold text-[10px] border border-amber-200">
                              REORDER NEEDED
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px] border border-emerald-200">
                              ADEQUATE STOCK
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowCreatePOModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xs transition"
              >
                Create Draft PO
              </button>
            </div>
          </form>
        </div>
      )}

      {/* PO DETAILS & WORKFLOW MODAL */}
      {selectedPOForDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-3xl rounded-2xl border border-slate-200 shadow-2xl overflow-hidden p-6 space-y-4 max-h-[90vh] flex flex-col justify-between">
            {/* Modal Header */}
            <div className="flex justify-between items-start border-b border-slate-100 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded border border-amber-200">
                    {selectedPOForDetails.po_number}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      selectedPOForDetails.status === 'RECEIVED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : selectedPOForDetails.status === 'ORDERED' || selectedPOForDetails.status === 'PARTIALLY_RECEIVED'
                        ? 'bg-blue-100 text-blue-800'
                        : selectedPOForDetails.status === 'APPROVED'
                        ? 'bg-teal-100 text-teal-800'
                        : selectedPOForDetails.status === 'PENDING_APPROVAL' || selectedPOForDetails.status === 'PENDING'
                        ? 'bg-amber-100 text-amber-800'
                        : selectedPOForDetails.status === 'CANCELLED'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {selectedPOForDetails.status}
                  </span>
                </div>
                <h2 className="text-base font-bold text-slate-900 mt-1">
                  Procurement Order for {selectedPOForDetails.vendor_name}
                </h2>
              </div>
              <button
                onClick={() => setSelectedPOForDetails(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-lg"
              >
                ✕
              </button>
            </div>

            <div className="overflow-y-auto space-y-4 pr-1 text-xs">
              {/* Rejection Alert Banner (if rejected previously) */}
              {selectedPOForDetails.rejection_reason && selectedPOForDetails.status === 'DRAFT' && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-red-800 text-xs">
                    <AlertCircle className="w-4 h-4 text-red-600" />
                    Returned for Revision by Admin ({selectedPOForDetails.rejected_by_name || 'Hospital Admin'})
                  </div>
                  <p className="text-xs text-red-700 font-medium">{selectedPOForDetails.rejection_reason}</p>
                </div>
              )}

              {/* Approval Banner */}
              {selectedPOForDetails.approved_by && (
                <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-900">
                  <span className="flex items-center gap-1.5 font-bold">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Approved by {selectedPOForDetails.approved_by_name || 'Hospital Admin'}
                  </span>
                  {selectedPOForDetails.approved_at && (
                    <span className="font-mono text-[11px] text-emerald-700">
                      {new Date(selectedPOForDetails.approved_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              )}

              {/* Visual Workflow Stepper */}
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                  Procurement Lifecycle Progress
                </span>
                <div className="flex items-center justify-between text-center relative">
                  {(
                    [
                      { key: 'DRAFT', label: '1. Draft' },
                      { key: 'PENDING_APPROVAL', label: '2. Approval' },
                      { key: 'APPROVED', label: '3. Approved' },
                      { key: 'ORDERED', label: '4. Ordered' },
                      { key: 'RECEIVED', label: '5. Received' },
                    ] as const
                  ).map((step, idx) => {
                    const statusOrder = ['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'ORDERED', 'RECEIVED'];
                    const currentStatus =
                      selectedPOForDetails.status === 'PENDING'
                        ? 'PENDING_APPROVAL'
                        : selectedPOForDetails.status === 'PARTIALLY_RECEIVED'
                        ? 'ORDERED'
                        : selectedPOForDetails.status;

                    const currentIdx = statusOrder.indexOf(currentStatus);
                    const isDone = currentIdx >= idx;
                    const isCurrent = currentIdx === idx;

                    return (
                      <div key={step.key} className="flex-1 flex flex-col items-center">
                        <div
                          className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs transition ${
                            selectedPOForDetails.status === 'CANCELLED'
                              ? 'bg-slate-200 text-slate-500'
                              : isDone
                              ? 'bg-amber-600 text-white shadow-xs'
                              : 'bg-slate-200 text-slate-500'
                          }`}
                        >
                          {isDone ? '✓' : idx + 1}
                        </div>
                        <span
                          className={`text-[10px] font-bold mt-1 ${
                            isCurrent ? 'text-amber-700' : isDone ? 'text-slate-800' : 'text-slate-400'
                          }`}
                        >
                          {step.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Order Metadata */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Supplier</span>
                  <span className="font-bold text-slate-800">{selectedPOForDetails.vendor_name}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Order Date</span>
                  <span className="text-slate-800">{selectedPOForDetails.order_date}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Expected Delivery</span>
                  <span className="text-slate-800">{selectedPOForDetails.expected_delivery || 'Not specified'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Created By</span>
                  <span className="text-slate-800">{selectedPOForDetails.created_by_name || 'Pharmacist'}</span>
                </div>
                {selectedPOForDetails.notes && (
                  <div className="col-span-2 sm:col-span-4 pt-1.5 border-t border-slate-200">
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Remarks / Notes</span>
                    <span className="text-slate-700">{selectedPOForDetails.notes}</span>
                  </div>
                )}
              </div>

              {/* Items Ledger Table */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Requested Medicines & Quantities</h3>
                <div className="rounded-xl border border-slate-200 overflow-hidden">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                      <tr>
                        <th className="p-2.5">Medicine</th>
                        <th className="p-2.5 text-center">Ordered</th>
                        <th className="p-2.5 text-center">Received</th>
                        <th className="p-2.5 text-center">Remaining</th>
                        <th className="p-2.5 text-right">Unit Price</th>
                        <th className="p-2.5 text-right">Line Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedPOForDetails.items?.map((it, idx) => {
                        const ordered = it.ordered_quantity ?? it.requested_quantity ?? 0;
                        const rec = it.received_quantity ?? 0;
                        const rem = it.remaining_quantity !== undefined ? it.remaining_quantity : Math.max(0, ordered - rec);
                        const price = it.unit_price ?? it.unit_cost ?? 0;

                        return (
                          <tr key={idx} className="hover:bg-slate-50">
                            <td className="p-2.5">
                              <strong className="text-slate-900 block">{it.medicine_name}</strong>
                              <span className="text-[10px] text-slate-400">{it.medicine_brand || it.medicine_strength}</span>
                            </td>
                            <td className="p-2.5 text-center font-mono font-bold text-slate-700">{ordered}</td>
                            <td className="p-2.5 text-center font-mono font-bold text-emerald-700">{rec}</td>
                            <td className="p-2.5 text-center font-mono font-bold text-amber-700">{rem}</td>
                            <td className="p-2.5 text-right font-mono text-slate-600">₹{Number(price).toFixed(2)}</td>
                            <td className="p-2.5 text-right font-mono font-bold text-slate-900">
                              ₹{(ordered * price).toFixed(2)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot className="bg-slate-50/80 font-bold border-t border-slate-200">
                      <tr>
                        <td colSpan={5} className="p-2.5 text-right text-slate-700 uppercase">
                          Total PO Amount:
                        </td>
                        <td className="p-2.5 text-right font-mono font-black text-amber-800 text-sm">
                          ₹{Number(selectedPOForDetails.total_amount).toLocaleString()}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            </div>

            {/* Role-Scoped Lifecycle Actions Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100 text-xs">
              <div>
                {selectedPOForDetails.status === 'PENDING_APPROVAL' && !isHospitalAdmin && (
                  <span className="text-amber-700 font-bold flex items-center gap-1.5">
                    <Clock className="w-4 h-4" /> Awaiting Hospital Admin Review & Approval
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedPOForDetails(null)}
                  className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition"
                >
                  Close
                </button>

                {/* Cancel Action */}
                {!isReadOnly && selectedPOForDetails.status !== 'RECEIVED' && selectedPOForDetails.status !== 'CANCELLED' && (
                  <button
                    disabled={poActionLoading}
                    onClick={() => handleCancelPO(selectedPOForDetails.id)}
                    className="px-3 py-2 border border-red-200 text-red-700 hover:bg-red-50 font-bold rounded-xl transition"
                  >
                    Cancel PO
                  </button>
                )}

                {/* Draft: Submit for Approval */}
                {selectedPOForDetails.status === 'DRAFT' && !isReadOnly && (
                  <button
                    disabled={poActionLoading}
                    onClick={() => handleSubmitPOForApproval(selectedPOForDetails.id)}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-xl shadow-xs transition flex items-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" /> Submit for Approval
                  </button>
                )}

                {/* Pending Approval: Admin Approve / Reject */}
                {(selectedPOForDetails.status === 'PENDING_APPROVAL' || selectedPOForDetails.status === 'PENDING') && isHospitalAdmin && (
                  <>
                    <button
                      disabled={poActionLoading}
                      onClick={() => setShowRejectModal(true)}
                      className="px-3.5 py-2 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl shadow-xs transition flex items-center gap-1"
                    >
                      <X className="w-3.5 h-3.5" /> Reject PO
                    </button>
                    <button
                      disabled={poActionLoading}
                      onClick={() => handleApprovePO(selectedPOForDetails.id)}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-xs transition flex items-center gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" /> Approve Purchase Order
                    </button>
                  </>
                )}

                {/* Approved: Place Order */}
                {selectedPOForDetails.status === 'APPROVED' && !isReadOnly && (
                  <button
                    disabled={poActionLoading}
                    onClick={() => handlePlaceOrder(selectedPOForDetails.id)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-xs transition flex items-center gap-1.5"
                  >
                    <Truck className="w-3.5 h-3.5" /> Place Order with Vendor
                  </button>
                )}

                {/* Ordered / Partially Received: Receive Goods */}
                {(selectedPOForDetails.status === 'ORDERED' || selectedPOForDetails.status === 'PARTIALLY_RECEIVED') && !isReadOnly && (
                  <button
                    disabled={poActionLoading}
                    onClick={() => openReceivingModal(selectedPOForDetails)}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-xs transition flex items-center gap-1.5"
                  >
                    <PackageCheck className="w-3.5 h-3.5" /> Receive Physical Goods
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* REJECT PO MODAL */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-md rounded-2xl border border-slate-200 shadow-2xl p-5 space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5 text-red-700">
                <AlertCircle className="w-4 h-4" /> Reject Purchase Order & Return to Draft
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Provide an administrative reason explaining what corrections or budget revisions the pharmacist must make.
              </p>
            </div>

            <div>
              <label className="text-[11px] font-bold text-slate-700 block mb-1">Rejection Reason *</label>
              <textarea
                rows={3}
                required
                placeholder="e.g. Excessive requested quantity exceeding monthly budget allocation..."
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800 focus:ring-2 focus:ring-red-500/20"
              />
            </div>

            <div className="flex justify-end gap-2.5 pt-2 border-t border-slate-100 text-xs">
              <button
                type="button"
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectionReason('');
                }}
                className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={poActionLoading || !rejectionReason.trim()}
                onClick={handleConfirmRejectPO}
                className="px-4 py-1.5 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold rounded-xl shadow-xs transition"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* GOODS RECEIVING MODAL */}
      {receivingPO && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-2xl rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4 max-h-[90vh] flex flex-col justify-between">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <span className="font-mono text-xs font-bold text-amber-700">{receivingPO.po_number}</span>
                <h2 className="text-base font-bold text-slate-900">Goods Receiving & Batch Creation</h2>
                <p className="text-[11px] text-slate-500">
                  Supplier: <strong>{receivingPO.vendor_name}</strong> | All received batches will be added to the inventory ledger.
                </p>
              </div>
              <button onClick={() => setReceivingPO(null)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs max-h-96 overflow-y-auto pr-1">
              {receiveItemsData.map((item, idx) => (
                <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                  <div className="flex justify-between items-center font-bold text-slate-900">
                    <span>{item.medicine_name}</span>
                    <span className="text-slate-500 font-mono text-[11px]">
                      Ordered: {item.ordered_quantity} | Previously Received: {item.already_received} | Remaining:{' '}
                      <strong className="text-amber-700">{item.requested_quantity}</strong>
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <div>
                      <label className="text-[10px] font-bold text-slate-500 block mb-0.5">
                        Received Qty (Max: {item.requested_quantity}) *
                      </label>
                      <input
                        type="number"
                        min={0}
                        max={item.requested_quantity}
                        value={item.received_quantity}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setReceiveItemsData((prev) =>
                            prev.map((it, i) => (i === idx ? { ...it, received_quantity: val } : it))
                          );
                        }}
                        className="w-full bg-white border border-slate-200 rounded-xl px-2 py-1 text-xs font-bold font-mono"
                      />
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-slate-500 block mb-0.5">Batch Number *</label>
                      <input
                        type="text"
                        value={item.batch_number}
                        onChange={(e) => {
                          const val = e.target.value;
                          setReceiveItemsData((prev) =>
                            prev.map((it, i) => (i === idx ? { ...it, batch_number: val } : it))
                          );
                        }}
                        className="w-full bg-white border border-slate-200 rounded-xl px-2 py-1 text-xs font-bold font-mono"
                      />
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-slate-500 block mb-0.5">Mfg Date</label>
                      <input
                        type="date"
                        max={new Date().toISOString().split('T')[0]}
                        value={item.mfg_date}
                        onChange={(e) => {
                          const val = e.target.value;
                          setReceiveItemsData((prev) =>
                            prev.map((it, i) => (i === idx ? { ...it, mfg_date: val } : it))
                          );
                        }}
                        className="w-full bg-white border border-slate-200 rounded-xl px-2 py-1 text-xs"
                      />
                    </div>

                    <div>
                      <label className="text-[10px] font-bold text-slate-500 block mb-0.5">Expiry Date *</label>
                      <input
                        type="date"
                        min={new Date(Date.now() + 86400000).toISOString().split('T')[0]}
                        value={item.expiry_date}
                        onChange={(e) => {
                          const val = e.target.value;
                          setReceiveItemsData((prev) =>
                            prev.map((it, i) => (i === idx ? { ...it, expiry_date: val } : it))
                          );
                        }}
                        className="w-full bg-white border border-slate-200 rounded-xl px-2 py-1 text-xs"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setReceivingPO(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmGoodsReceiving}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5"
              >
                <PackageCheck className="w-4 h-4" /> Confirm Receipt & Update Stock
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Medicine Modal */}
      {showAddMedicineModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleAddMedicine}
            className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Pill className="w-4 h-4 text-emerald-600" />
                Add Medicine to Master Catalog
              </h3>
              <button
                type="button"
                onClick={() => setShowAddMedicineModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="md:col-span-2">
                <label className="font-bold text-slate-600 block mb-1">Generic Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Paracetamol"
                  value={newMedicineData.generic_name}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, generic_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Brand Name</label>
                <input
                  type="text"
                  placeholder="e.g. Dolo 650"
                  value={newMedicineData.brand_name}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, brand_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Category</label>
                <input
                  type="text"
                  placeholder="e.g. Essential Medicines"
                  value={newMedicineData.category}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, category: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Strength</label>
                <input
                  type="text"
                  placeholder="e.g. 500 mg"
                  value={newMedicineData.strength}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, strength: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Dosage Form</label>
                <select
                  value={newMedicineData.dosage_form}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, dosage_form: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                >
                  <option value="Tablet">Tablet</option>
                  <option value="Capsule">Capsule</option>
                  <option value="Syrup">Syrup</option>
                  <option value="Injection">Injection</option>
                  <option value="Ointment">Ointment</option>
                  <option value="Drops">Drops</option>
                  <option value="Inhaler">Inhaler</option>
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Unit</label>
                <input
                  type="text"
                  placeholder="e.g. Tablets"
                  value={newMedicineData.unit}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, unit: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Reorder Level</label>
                <input
                  type="number"
                  min="0"
                  value={newMedicineData.reorder_level}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, reorder_level: Number(e.target.value) })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowAddMedicineModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={medicineActionLoading}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{medicineActionLoading ? 'Saving...' : 'Save Medicine'}</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Medicine Modal */}
      {editingMedicine && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleSaveEditMedicine}
            className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-emerald-600" />
                Edit Medicine Master
              </h3>
              <button
                type="button"
                onClick={() => setEditingMedicine(null)}
                className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="md:col-span-2">
                <label className="font-bold text-slate-600 block mb-1">Generic Name *</label>
                <input
                  type="text"
                  required
                  value={editMedicineData.generic_name}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, generic_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Brand Name</label>
                <input
                  type="text"
                  value={editMedicineData.brand_name}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, brand_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Category</label>
                <input
                  type="text"
                  value={editMedicineData.category}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, category: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Strength</label>
                <input
                  type="text"
                  value={editMedicineData.strength}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, strength: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Dosage Form</label>
                <select
                  value={editMedicineData.dosage_form}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, dosage_form: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                >
                  <option value="Tablet">Tablet</option>
                  <option value="Capsule">Capsule</option>
                  <option value="Syrup">Syrup</option>
                  <option value="Injection">Injection</option>
                  <option value="Ointment">Ointment</option>
                  <option value="Drops">Drops</option>
                  <option value="Inhaler">Inhaler</option>
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Unit</label>
                <input
                  type="text"
                  value={editMedicineData.unit}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, unit: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="font-bold text-slate-600 block mb-1">Reorder Level</label>
                <input
                  type="number"
                  min="0"
                  value={editMedicineData.reorder_level}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, reorder_level: Number(e.target.value) })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingMedicine(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={medicineActionLoading}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>{medicineActionLoading ? 'Saving...' : 'Update Medicine'}</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
