import React, { useState, useEffect, useMemo } from 'react';
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
  Building2,
  ShoppingCart,
  History,
  FileSpreadsheet,
  AlertCircle,
  Plus,
  Search,
  CheckCircle2,
  Clock,
  DollarSign,
  Boxes,
  Truck,
  ClipboardList,
  Eye,
  Check,
  X,
  Filter,
  Edit2,
  Trash2,
  ChevronRight,
  RefreshCw,
  ArrowRight,
  Info,
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useConfirm } from '../context/ConfirmContext';
import { hasPermission } from '../utils/permissions';

type ActiveTab =
  | 'DASHBOARD'
  | 'PRESCRIPTIONS'
  | 'INVENTORY'
  | 'PURCHASE_ORDERS'
  | 'VENDORS'
  | 'ALERTS'
  | 'REPORTS';

type InventorySubTab = 'CURRENT_STOCK' | 'BATCHES' | 'STOCK_HISTORY';

export const Pharmacy: React.FC = () => {
  const { activeFacility, user } = useAuth();
  const { confirm } = useConfirm();
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

  // Main 7 Sections
  const [activeTab, setActiveTab] = useState<ActiveTab>('DASHBOARD');
  const [inventorySubTab, setInventorySubTab] = useState<InventorySubTab>('CURRENT_STOCK');
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

  // Total record counts (from backend metadata)
  const [prescriptionsTotalCount, setPrescriptionsTotalCount] = useState<number>(0);
  const [medicinesTotalCount, setMedicinesTotalCount] = useState<number>(0);
  const [batchesTotalCount, setBatchesTotalCount] = useState<number>(0);
  const [transactionsTotalCount, setTransactionsTotalCount] = useState<number>(0);
  const [vendorsTotalCount, setVendorsTotalCount] = useState<number>(0);
  const [purchaseOrdersTotalCount, setPurchaseOrdersTotalCount] = useState<number>(0);

  // Defensive date formatters (zero "Invalid Date" guarantee)
  const formatDateTime = (dateVal?: string | null): string => {
    if (!dateVal) return '-';
    const d = new Date(dateVal);
    if (isNaN(d.getTime())) {
      return typeof dateVal === 'string' && dateVal.trim() ? dateVal : '-';
    }
    return d.toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDateOnly = (dateVal?: string | null): string => {
    if (!dateVal) return '-';
    const d = new Date(dateVal);
    if (isNaN(d.getTime())) {
      return typeof dateVal === 'string' && dateVal.trim() ? dateVal : '-';
    }
    return d.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Filters & Searches
  const [prescriptionSearch, setPrescriptionSearch] = useState('');
  const [prescriptionStatusFilter, setPrescriptionStatusFilter] = useState<string>('ALL');

  const [medicineSearchQuery, setMedicineSearchQuery] = useState('');
  const [medicineCategoryFilter, setMedicineCategoryFilter] = useState<string>('ALL');

  const [batchSearchQuery, setBatchSearchQuery] = useState('');
  const [batchStatusFilter, setBatchStatusFilter] = useState<string>('ALL');

  const [txSearchQuery, setTxSearchQuery] = useState('');
  const [txTypeFilter, setTxTypeFilter] = useState<string>('ALL');

  const [vendorSearch, setVendorSearch] = useState('');
  const [vendorStatusFilter, setVendorStatusFilter] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL');

  const [poSearchQuery, setPoSearchQuery] = useState('');
  const [poStatusFilter, setPoStatusFilter] = useState<string>('ALL');

  const [alertTypeFilter, setAlertTypeFilter] = useState<string>('ALL');

  // Modals & Details states
  const [dispenseModalRx, setDispenseModalRx] = useState<Prescription | null>(null);
  const [dispenseItems, setDispenseItems] = useState<
    Array<{ item_id: number; medicine_name: string; target_qty: number; batch_id: number; qty_to_dispense: number }>
  >([]);
  const [dispensingError, setDispensingError] = useState<string>('');

  const [selectedMedicineForDetails, setSelectedMedicineForDetails] = useState<MedicineMaster | null>(null);
  const [selectedVendorForDetails, setSelectedVendorForDetails] = useState<Vendor | null>(null);
  const [selectedPOForDetails, setSelectedPOForDetails] = useState<PurchaseOrder | null>(null);

  const [vendorHistory, setVendorHistory] = useState<PurchaseOrder[]>([]);
  const [loadingVendorHistory, setLoadingVendorHistory] = useState(false);

  // Forms states
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

  const [editingVendor, setEditingVendor] = useState<Vendor | null>(null);
  const [editVendorData, setEditVendorData] = useState({
    name: '',
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    gstin: '',
  });

  const [showCreatePOModal, setShowCreatePOModal] = useState(false);
  const [newPOData, setNewPOData] = useState({
    vendor: 0,
    expected_delivery: '',
    notes: '',
    items: [{ medicine: 0, requested_quantity: 100, unit_cost: 10.0 }],
  });

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

  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [poActionLoading, setPoActionLoading] = useState(false);
  const [medicineActionLoading, setMedicineActionLoading] = useState(false);

  // API Loader
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
        api.get(`pharmacy/vendors/?facility=${facilityId}`).catch(() => ({ data: [] })),
        api.get(`pharmacy/purchase-orders/?facility=${facilityId}`).catch(() => ({ data: [] })),
        api.get(`pharmacy/alerts/?facility=${facilityId}`).catch(() => ({ data: [] })),
        api.get(`pharmacy/reports/?facility=${facilityId}`).catch(() => ({ data: null })),
        api.get(`pharmacy/purchase-orders/procurement_summary/?facility=${facilityId}`).catch(() => ({ data: null })),
      ]);

      const rxList: Prescription[] = pRes.data?.results || pRes.data || [];
      const medList: MedicineMaster[] = mRes.data?.results || mRes.data || [];
      const batchList: MedicineBatch[] = bRes.data?.results || bRes.data || [];
      const txList: InventoryTransaction[] = tRes.data?.results || tRes.data || [];
      const vendorList: Vendor[] = vRes.data?.results || vRes.data || [];
      const poList: PurchaseOrder[] = poRes.data?.results || poRes.data || [];

      // Extract authoritative total counts (from backend metadata, never page-length only)
      const rxCount = typeof pRes.data?.count === 'number' ? pRes.data.count : (Array.isArray(rxList) ? rxList.length : 0);
      const medCount = typeof mRes.data?.count === 'number' ? mRes.data.count : (Array.isArray(medList) ? medList.length : 0);
      const batchCount = typeof bRes.data?.count === 'number' ? bRes.data.count : (Array.isArray(batchList) ? batchList.length : 0);
      const txCount = typeof tRes.data?.count === 'number' ? tRes.data.count : (Array.isArray(txList) ? txList.length : 0);
      const vendorCount = typeof vRes.data?.count === 'number' ? vRes.data.count : (Array.isArray(vendorList) ? vendorList.length : 0);
      const poCount = typeof poRes.data?.count === 'number' ? poRes.data.count : (Array.isArray(poList) ? poList.length : 0);

      setPrescriptionsTotalCount(rxCount);
      setMedicinesTotalCount(medCount);
      setBatchesTotalCount(batchCount);
      setTransactionsTotalCount(txCount);
      setVendorsTotalCount(vendorCount);
      setPurchaseOrdersTotalCount(poCount);

      // Unified calculation
      const totalStock = batchList.reduce((acc: number, b: MedicineBatch) => acc + (Number(b.quantity) || 0), 0);
      const expiredCount = batchList.filter((b: MedicineBatch) => b.is_expired || (b.expiry_date && new Date(b.expiry_date) <= new Date())).length;
      const expiringCount = batchList.filter(
        (b: MedicineBatch) =>
          !b.is_expired &&
          (b.status === 'EXPIRING_SOON' ||
            (b.days_to_expiry !== undefined && b.days_to_expiry <= 60 && b.days_to_expiry > 0) ||
            (new Date(b.expiry_date) > new Date() && new Date(b.expiry_date).getTime() - Date.now() < 60 * 24 * 60 * 60 * 1000))
      ).length;
      const pendingRx = rxList.filter((r: Prescription) => ['PENDING', 'ACTIVE', 'PARTIALLY_DISPENSED'].includes(r.status)).length;
      const pendingPOs = poList.filter((po: PurchaseOrder) =>
        ['DRAFT', 'PENDING_APPROVAL', 'PENDING', 'APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED'].includes(po.status)
      ).length;

      const mergedKPIs: PharmacyDashboardKPIs = {
        total_medicines: kpiRes.data?.total_medicines ?? medCount,
        medicine_master_count: kpiRes.data?.medicine_master_count ?? medCount,
        stocked_medicine_count: kpiRes.data?.stocked_medicine_count,
        total_available_stock: kpiRes.data?.total_available_stock ?? totalStock,
        low_stock_count: kpiRes.data?.low_stock_count ?? kpiRes.data?.low_stock ?? 0,
        out_of_stock_count: kpiRes.data?.out_of_stock_count ?? kpiRes.data?.out_of_stock ?? 0,
        expiring_soon_count: kpiRes.data?.expiring_soon_count ?? kpiRes.data?.expiring_soon ?? expiringCount,
        expired_count: kpiRes.data?.expired_count ?? expiredCount,
        pending_prescriptions_count: kpiRes.data?.pending_prescriptions_count ?? kpiRes.data?.prescriptions_waiting ?? pendingRx,
        dispensed_today_count: kpiRes.data?.dispensed_today_count ?? kpiRes.data?.dispensed_today ?? 0,
        pending_purchase_orders_count: kpiRes.data?.pending_purchase_orders_count ?? kpiRes.data?.pending_purchase_orders ?? pendingPOs,
        total_vendors_count: kpiRes.data?.total_vendors_count ?? vendorCount,
        total_batches_count: kpiRes.data?.total_batches_count ?? batchCount,
      };

      const procData: ProcurementSummaryKPIs = procRes.data || {
        draft: poList.filter((p) => p.status === 'DRAFT').length,
        pending_approval: poList.filter((p) => ['PENDING_APPROVAL', 'PENDING'].includes(p.status)).length,
        approved: poList.filter((p) => p.status === 'APPROVED').length,
        ordered: poList.filter((p) => p.status === 'ORDERED').length,
        partially_received: poList.filter((p) => p.status === 'PARTIALLY_RECEIVED').length,
        received: poList.filter((p) => p.status === 'RECEIVED').length,
        cancelled: poList.filter((p) => p.status === 'CANCELLED').length,
        total_orders: poCount,
        pending_orders: kpiRes.data?.pending_purchase_orders_count ?? pendingPOs,
        completed_orders: poList.filter((p) => p.status === 'RECEIVED').length,
        total_spend: poList
          .filter((p) => ['APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED'].includes(p.status))
          .reduce((sum: number, p) => sum + (Number(p.total_amount) || 0), 0),
      };

      setKpis(mergedKPIs);
      setProcurementKpis(procData);
      setPrescriptions(rxList);
      setMedicines(medList);
      setBatches(batchList);
      setTransactions(txList);
      setVendors(vendorList);
      setPurchaseOrders(poList);
      setAlerts(alertRes.data?.alerts || alertRes.data || []);
      setReportSummary(rptRes.data);

      // Keep detail modals synced if currently open
      setSelectedPOForDetails((curr) => {
        if (!curr) return null;
        return poList.find((p) => p.id === curr.id) || curr;
      });
      setSelectedMedicineForDetails((curr) => {
        if (!curr) return null;
        return medList.find((m) => m.id === curr.id) || curr;
      });

      // Handle direct queue dispatch
      if (location.state?.visitId) {
        const targetRx = rxList.find(
          (r: any) => r.visit_id === location.state.visitId || r.consultation?.visit === location.state.visitId
        );
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
      setActiveTab(location.state.activeTab as ActiveTab);
    } else if (location.state?.visitId || location.state?.patientId) {
      setActiveTab('PRESCRIPTIONS');
    }
  }, [location.state]);

  // FEFO helper to match batches
  const matchMedicineBatch = (batchMedName?: string, itemMedName?: string) => {
    if (!batchMedName || !itemMedName) return false;
    const b = batchMedName.toLowerCase();
    const i = itemMedName.toLowerCase();
    const bWord = b.split(/[\s-]+/)[0];
    const iWord = i.split(/[\s-]+/)[0];
    return b.includes(i) || i.includes(b) || b.includes(iWord) || i.includes(bWord) || bWord === iWord;
  };

  // Nearest expiry date calculator for Current Stock table
  const getNearestExpiry = (medId: number, medName: string) => {
    const medBatches = batches.filter(
      (b) =>
        (b.medicine === medId || matchMedicineBatch(b.medicine_name || b.generic_name, medName)) &&
        b.quantity > 0 &&
        new Date(b.expiry_date) > new Date()
    );
    if (medBatches.length === 0) return '-';
    medBatches.sort((a, b) => new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime());
    const earliest = medBatches[0];
    const d = new Date(earliest.expiry_date);
    return isNaN(d.getTime()) ? earliest.expiry_date : d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
  };

  // Open Dispense Modal with automatic FEFO batch selection
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
      // FEFO Sort: Earliest valid expiry first
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

  // Confirm Dispense with Global Confirmation Dialog
  const handleConfirmDispense = async () => {
    if (!dispenseModalRx) return;
    setDispensingError('');

    await confirm({
      title: 'Confirm Medicine Dispensing',
      message: `Are you sure you want to dispense prescription ${dispenseModalRx.prescription_number || `#${dispenseModalRx.id}`} for ${dispenseModalRx.patient_name}?`,
      confirmText: 'Dispense Medicine',
      variant: 'primary',
      details: [
        { label: 'Patient', value: dispenseModalRx.patient_name || `Patient #${dispenseModalRx.patient || ''}` },
        { label: 'Prescription #', value: dispenseModalRx.prescription_number || `#${dispenseModalRx.id}` },
        { label: 'Doctor', value: dispenseModalRx.doctor_name || 'Attending Physician' },
        { label: 'Items to Dispense', value: dispenseItems.map((it) => `${it.medicine_name} (${it.qty_to_dispense} units)`).join(', ') },
      ],
      warning: 'Stock will be deducted automatically in real-time according to FEFO batch allocations.',
      onConfirm: async () => {
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
          setDispenseModalRx(null);
          await loadData();
          alert(res.data?.message || 'Prescription successfully dispensed! Stock deducted in real-time.');
        } catch (e: any) {
          const msg = e.response?.data?.error || 'Failed to dispense prescription.';
          setDispensingError(msg);
        }
      },
    });
  };

  // Medicine Master Handlers
  const handleAddMedicine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canCreateMedicine) return;

    await confirm({
      title: 'Confirm Medicine Registration',
      message: `Are you sure you want to register "${newMedicineData.generic_name}" in the master drug catalog?`,
      confirmText: 'Register Medicine',
      variant: 'primary',
      details: [
        { label: 'Generic Name', value: newMedicineData.generic_name },
        { label: 'Brand Name', value: newMedicineData.brand_name || 'N/A' },
        { label: 'Strength & Form', value: `${newMedicineData.strength} - ${newMedicineData.dosage_form}` },
        { label: 'Category', value: newMedicineData.category },
        { label: 'Min Stock / Reorder', value: `${newMedicineData.minimum_stock} / ${newMedicineData.reorder_level}` },
      ],
      onConfirm: async () => {
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
          await loadData();
          alert('Medicine registered successfully!');
        } catch (err: any) {
          alert(err.response?.data?.message || err.response?.data?.generic_name?.[0] || 'Failed to register medicine');
        } finally {
          setMedicineActionLoading(false);
        }
      },
    });
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

    await confirm({
      title: 'Confirm Medicine Update',
      message: `Are you sure you want to save changes to medicine "${editingMedicine.generic_name}"?`,
      confirmText: 'Save Changes',
      variant: 'primary',
      details: [
        { label: 'Generic Name', value: editMedicineData.generic_name },
        { label: 'Brand Name', value: editMedicineData.brand_name || 'N/A' },
        { label: 'Strength & Form', value: `${editMedicineData.strength} - ${editMedicineData.dosage_form}` },
        { label: 'Min Stock / Reorder', value: `${editMedicineData.minimum_stock} / ${editMedicineData.reorder_level}` },
      ],
      onConfirm: async () => {
        setMedicineActionLoading(true);
        try {
          const res = await api.patch(`pharmacy/medicines/${editingMedicine.id}/`, editMedicineData);
          setMedicines((prev) => prev.map((m) => (m.id === editingMedicine.id ? res.data : m)));
          setEditingMedicine(null);
          await loadData();
          alert('Medicine updated successfully!');
        } catch (err: any) {
          alert(err.response?.data?.message || err.response?.data?.generic_name?.[0] || 'Failed to update medicine');
        } finally {
          setMedicineActionLoading(false);
        }
      },
    });
  };

  const handleDeleteMedicine = async (id: number) => {
    if (!canDeleteMedicine) return;
    const med = medicines.find((m) => m.id === id);

    await confirm({
      title: 'Confirm Medicine Deletion',
      message: `Are you sure you want to remove "${med?.generic_name || `Medicine #${id}`}" from the master catalog?`,
      confirmText: 'Delete Medicine',
      variant: 'danger',
      details: [
        { label: 'Generic Name', value: med?.generic_name || `#${id}` },
        { label: 'Brand Name', value: med?.brand_name || 'N/A' },
        { label: 'Category', value: med?.category || 'N/A' },
      ],
      warning: 'Warning: This action will permanently remove this medicine and affects linked inventory records.',
      onConfirm: async () => {
        try {
          await api.delete(`pharmacy/medicines/${id}/`);
          setMedicines((prev) => prev.filter((m) => m.id !== id));
          if (selectedMedicineForDetails?.id === id) {
            setSelectedMedicineForDetails(null);
          }
          await loadData();
          alert('Medicine deleted successfully!');
        } catch (err: any) {
          alert(err.response?.data?.message || 'Failed to delete medicine');
        }
      },
    });
  };

  // Vendor Handlers
  const handleAddVendor = async (e: React.FormEvent) => {
    e.preventDefault();
    await confirm({
      title: 'Confirm Vendor Registration',
      message: `Are you sure you want to register vendor "${newVendorData.name}"?`,
      confirmText: 'Register Vendor',
      variant: 'primary',
      details: [
        { label: 'Vendor Name', value: newVendorData.name },
        { label: 'Contact Person', value: newVendorData.contact_person || 'N/A' },
        { label: 'Phone', value: newVendorData.phone },
        { label: 'GSTIN', value: newVendorData.gstin || 'N/A' },
      ],
      onConfirm: async () => {
        try {
          await api.post('pharmacy/vendors/', newVendorData);
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
          await loadData();
          alert('Vendor registered successfully!');
        } catch (e: any) {
          alert(e.response?.data?.error || 'Failed to create vendor');
        }
      },
    });
  };

  const handleToggleVendorStatus = async (vendor: Vendor) => {
    const isDeactivating = vendor.status === 'ACTIVE';
    await confirm({
      title: isDeactivating ? 'Confirm Vendor Deactivation' : 'Confirm Vendor Activation',
      message: isDeactivating
        ? `Are you sure you want to deactivate vendor "${vendor.vendor_name || vendor.name}"? Inactive vendors cannot be selected for new purchase orders.`
        : `Are you sure you want to activate vendor "${vendor.vendor_name || vendor.name}"?`,
      confirmText: isDeactivating ? 'Deactivate Vendor' : 'Activate Vendor',
      variant: isDeactivating ? 'warning' : 'primary',
      details: [
        { label: 'Vendor', value: vendor.vendor_name || vendor.name || '' },
        { label: 'Current Status', value: vendor.status || 'ACTIVE' },
        { label: 'New Status', value: isDeactivating ? 'INACTIVE' : 'ACTIVE' },
      ],
      onConfirm: async () => {
        try {
          const res = await api.post(`pharmacy/vendors/${vendor.id}/toggle_status/`);
          await loadData();
          if (selectedVendorForDetails?.id === vendor.id) {
            setSelectedVendorForDetails((prev) =>
              prev ? { ...prev, status: res.data?.status || (prev.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE') } : null
            );
          }
          alert(res.data?.message || 'Vendor status updated.');
        } catch (err: any) {
          alert(err.response?.data?.error || 'Failed to toggle vendor status.');
        }
      },
    });
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

    await confirm({
      title: 'Confirm Vendor Update',
      message: `Are you sure you want to update details for vendor "${editingVendor.vendor_name || editingVendor.name}"?`,
      confirmText: 'Save Vendor',
      variant: 'primary',
      details: [
        { label: 'Vendor Name', value: editVendorData.name },
        { label: 'Contact Person', value: editVendorData.contact_person || 'N/A' },
        { label: 'Phone', value: editVendorData.phone },
        { label: 'GSTIN', value: editVendorData.gstin || 'N/A' },
      ],
      onConfirm: async () => {
        try {
          await api.patch(`pharmacy/vendors/${editingVendor.id}/`, {
            vendor_name: editVendorData.name,
            contact_person: editVendorData.contact_person,
            phone: editVendorData.phone,
            email: editVendorData.email,
            address: editVendorData.address,
            gst_number: editVendorData.gstin,
          });
          setEditingVendor(null);
          await loadData();
          alert('Vendor details updated successfully!');
        } catch (err: any) {
          alert(err.response?.data?.error || 'Failed to update vendor.');
        }
      },
    });
  };

  const handleDeleteVendor = async (vendor: Vendor) => {
    await confirm({
      title: 'Confirm Vendor Deletion',
      message: `Are you sure you want to delete vendor "${vendor.vendor_name || vendor.name}"?`,
      confirmText: 'Delete Vendor',
      variant: 'danger',
      details: [
        { label: 'Vendor Name', value: vendor.vendor_name || vendor.name || '' },
        { label: 'Vendor Code', value: vendor.vendor_code || 'N/A' },
        { label: 'Contact', value: vendor.phone || vendor.email || 'N/A' },
      ],
      warning: 'Warning: Vendors with existing purchase orders or batch records cannot be deleted.',
      onConfirm: async () => {
        try {
          await api.delete(`pharmacy/vendors/${vendor.id}/`);
          if (selectedVendorForDetails?.id === vendor.id) {
            setSelectedVendorForDetails(null);
          }
          await loadData();
          alert('Vendor deleted successfully.');
        } catch (err: any) {
          alert(err.response?.data?.error || 'Cannot delete vendor. It has historical orders or inventory batches linked to it.');
        }
      },
    });
  };

  // Purchase Order Handlers
  const handleOpenCreatePOForMedicine = (medId: number) => {
    const med = medicines.find((m) => m.id === medId);
    const activeVendors = vendors.filter((v) => v.status === 'ACTIVE');
    const preferredVendor = activeVendors[0] || vendors[0];

    setNewPOData({
      vendor: preferredVendor?.id || 0,
      expected_delivery: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      notes: `Restock procurement for ${med?.generic_name || 'medicine'}`,
      items: [{ medicine: medId, requested_quantity: med ? Math.max(50, med.reorder_level * 2) : 100, unit_cost: 10.0 }],
    });
    setShowCreatePOModal(true);
  };

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
    const chosenVendor = vendors.find((v) => v.id === newPOData.vendor);
    const estTotal = validItems.reduce((acc, it) => acc + Number(it.requested_quantity) * Number(it.unit_cost || 0), 0);

    await confirm({
      title: 'Confirm Purchase Order Creation',
      message: 'Are you sure you want to create this purchase order in DRAFT mode?',
      confirmText: 'Create Purchase Order',
      variant: 'primary',
      details: [
        { label: 'Vendor', value: chosenVendor?.vendor_name || chosenVendor?.name || `Vendor #${newPOData.vendor}` },
        { label: 'Total Items', value: `${validItems.length} item(s)` },
        { label: 'Estimated Total', value: `₹${estTotal.toFixed(2)}` },
        { label: 'Expected Delivery', value: newPOData.expected_delivery || 'Not specified' },
      ],
      onConfirm: async () => {
        try {
          await api.post('pharmacy/purchase-orders/', {
            vendor: newPOData.vendor,
            expected_delivery: newPOData.expected_delivery || null,
            notes: newPOData.notes,
            items: validItems,
          });
          setShowCreatePOModal(false);
          setNewPOData({
            vendor: 0,
            expected_delivery: '',
            notes: '',
            items: [{ medicine: 0, requested_quantity: 100, unit_cost: 10.0 }],
          });
          await loadData();
          alert('Purchase Order created successfully in DRAFT mode!');
        } catch (e: any) {
          alert(e.response?.data?.error || 'Failed to create Purchase Order');
        }
      },
    });
  };

  const handleSubmitPOForApproval = async (poId: number) => {
    const po = purchaseOrders.find((p) => p.id === poId) || selectedPOForDetails;
    await confirm({
      title: 'Confirm PO Submission for Approval',
      message: `Are you sure you want to submit Purchase Order ${po?.po_number || `#${poId}`} for administrative approval?`,
      confirmText: 'Submit for Approval',
      variant: 'primary',
      details: [
        { label: 'PO Number', value: po?.po_number || `#${poId}` },
        { label: 'Vendor', value: po?.vendor_name || 'N/A' },
        { label: 'Total Amount', value: `₹${Number(po?.total_amount || 0).toFixed(2)}` },
      ],
      onConfirm: async () => {
        setPoActionLoading(true);
        try {
          const res = await api.post(`pharmacy/purchase-orders/${poId}/submit_approval/`);
          await loadData();
          if (selectedPOForDetails?.id === poId) {
            setSelectedPOForDetails(res.data?.po || null);
          }
          alert(res.data?.message || 'PO submitted for administrative approval.');
        } catch (err: any) {
          alert(err.response?.data?.error || 'Failed to submit PO for approval.');
        } finally {
          setPoActionLoading(false);
        }
      },
    });
  };

  const handleApprovePO = async (poId: number) => {
    const po = purchaseOrders.find((p) => p.id === poId) || selectedPOForDetails;
    await confirm({
      title: 'Confirm Purchase Order Approval',
      message: `Are you sure you want to approve Purchase Order ${po?.po_number || `#${poId}`}?`,
      confirmText: 'Approve PO',
      variant: 'primary',
      details: [
        { label: 'PO Number', value: po?.po_number || `#${poId}` },
        { label: 'Vendor', value: po?.vendor_name || 'N/A' },
        { label: 'Total Amount', value: `₹${Number(po?.total_amount || 0).toFixed(2)}` },
      ],
      onConfirm: async () => {
        setPoActionLoading(true);
        try {
          const res = await api.post(`pharmacy/purchase-orders/${poId}/approve/`);
          await loadData();
          if (selectedPOForDetails?.id === poId) {
            setSelectedPOForDetails(res.data?.po || null);
          }
          alert(res.data?.message || 'PO approved successfully.');
        } catch (err: any) {
          alert(err.response?.data?.error || 'Failed to approve PO.');
        } finally {
          setPoActionLoading(false);
        }
      },
    });
  };

  const handleConfirmRejectPO = async () => {
    if (!selectedPOForDetails) return;
    if (!rejectionReason.trim()) {
      alert('Please provide a reason for rejecting the Purchase Order.');
      return;
    }
    await confirm({
      title: 'Confirm Purchase Order Rejection',
      message: `Are you sure you want to reject Purchase Order ${selectedPOForDetails.po_number || `#${selectedPOForDetails.id}`} and return it to Draft?`,
      confirmText: 'Reject Purchase Order',
      variant: 'danger',
      details: [
        { label: 'PO Number', value: selectedPOForDetails.po_number || `#${selectedPOForDetails.id}` },
        { label: 'Vendor', value: selectedPOForDetails.vendor_name || 'N/A' },
        { label: 'Reason', value: rejectionReason.trim() },
      ],
      warning: 'Warning: The purchase order will be moved back to Draft status and will require resubmission.',
      onConfirm: async () => {
        setPoActionLoading(true);
        try {
          const res = await api.post(`pharmacy/purchase-orders/${selectedPOForDetails.id}/reject/`, {
            reason: rejectionReason.trim(),
          });
          setShowRejectModal(false);
          setRejectionReason('');
          await loadData();
          setSelectedPOForDetails(res.data?.po || null);
          alert(res.data?.message || 'Purchase Order returned to Draft.');
        } catch (err: any) {
          alert(err.response?.data?.error || 'Failed to reject PO.');
        } finally {
          setPoActionLoading(false);
        }
      },
    });
  };

  const handlePlaceOrder = async (poId: number) => {
    const po = purchaseOrders.find((p) => p.id === poId) || selectedPOForDetails;
    await confirm({
      title: 'Confirm Placing Order with Supplier',
      message: `Are you sure you want to mark Purchase Order ${po?.po_number || `#${poId}`} as ORDERED with the vendor?`,
      confirmText: 'Place Order',
      variant: 'primary',
      details: [
        { label: 'PO Number', value: po?.po_number || `#${poId}` },
        { label: 'Vendor', value: po?.vendor_name || 'N/A' },
        { label: 'Total Amount', value: `₹${Number(po?.total_amount || 0).toFixed(2)}` },
      ],
      onConfirm: async () => {
        setPoActionLoading(true);
        try {
          const res = await api.post(`pharmacy/purchase-orders/${poId}/place_order/`);
          await loadData();
          if (selectedPOForDetails?.id === poId) {
            setSelectedPOForDetails(res.data?.po || null);
          }
          alert(res.data?.message || 'Purchase order marked as ORDERED with supplier.');
        } catch (err: any) {
          alert(err.response?.data?.error || 'Failed to place order.');
        } finally {
          setPoActionLoading(false);
        }
      },
    });
  };

  const handleCancelPO = async (poId: number) => {
    const po = purchaseOrders.find((p) => p.id === poId) || selectedPOForDetails;
    await confirm({
      title: 'Confirm Purchase Order Cancellation',
      message: `Are you sure you want to cancel Purchase Order ${po?.po_number || `#${poId}`}?`,
      confirmText: 'Cancel Purchase Order',
      variant: 'danger',
      details: [
        { label: 'PO Number', value: po?.po_number || `#${poId}` },
        { label: 'Vendor', value: po?.vendor_name || 'N/A' },
        { label: 'Current Status', value: po?.status || 'N/A' },
      ],
      warning: 'Warning: This cancellation is permanent. The order will be closed.',
      onConfirm: async () => {
        setPoActionLoading(true);
        try {
          const res = await api.post(`pharmacy/purchase-orders/${poId}/cancel/`);
          await loadData();
          if (selectedPOForDetails?.id === poId) {
            setSelectedPOForDetails(res.data?.po || null);
          }
          alert(res.data?.message || 'Purchase order cancelled.');
        } catch (err: any) {
          alert(err.response?.data?.error || 'Failed to cancel PO.');
        } finally {
          setPoActionLoading(false);
        }
      },
    });
  };

  // Goods Receiving Modal & Logic
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
        alert(
          `Received quantity (${it.received_quantity}) cannot exceed remaining ordered quantity (${it.requested_quantity}) for ${it.medicine_name}.`
        );
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
      }
    }

    const itemsToReceive = receiveItemsData.filter((it) => it.received_quantity > 0);
    if (itemsToReceive.length === 0) {
      alert('Please specify at least 1 unit to receive.');
      return;
    }

    await confirm({
      title: 'Confirm Goods Receipt into Inventory',
      message: `Are you sure you want to receive these goods into inventory for PO ${receivingPO.po_number || `#${receivingPO.id}`}?`,
      confirmText: 'Receive Goods',
      variant: 'primary',
      details: [
        { label: 'PO Number', value: receivingPO.po_number || `#${receivingPO.id}` },
        { label: 'Vendor', value: receivingPO.vendor_name || 'N/A' },
        {
          label: 'Items Received',
          value: itemsToReceive.map((it) => `${it.medicine_name} (${it.received_quantity} units, Batch: ${it.batch_number})`).join(', '),
        },
      ],
      warning: 'Stock levels, batches, and inventory transaction logs will be updated immediately.',
      onConfirm: async () => {
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
          setReceivingPO(null);
          await loadData();
          if (selectedPOForDetails?.id === receivingPO.id) {
            setSelectedPOForDetails(res.data?.po || null);
          }
          alert(res.data?.message || 'Goods received! Inventory batches and transactions updated.');
        } catch (e: any) {
          alert(e.response?.data?.error || 'Failed to receive goods');
        }
      },
    });
  };

  // CSV Report Export
  const exportCSVReport = async () => {
    if (!reportSummary) return;

    await confirm({
      title: 'Confirm Pharmacy Report Export',
      message: 'Are you sure you want to export the Pharmacy Analytics & Stock Valuation report as a CSV file?',
      confirmText: 'Export CSV',
      variant: 'info',
      details: [
        { label: 'Report Type', value: 'Pharmacy Analytics & Stock Valuation' },
        { label: 'Facility', value: activeFacility?.facility_name || 'All Facilities' },
        { label: 'Generated Date', value: new Date().toLocaleDateString() },
      ],
      onConfirm: async () => {
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
      },
    });
  };

  // Derived counts
  const pendingPrescriptionsCount =
    kpis?.pending_prescriptions_count ??
    prescriptions.filter((p) => ['PENDING', 'ACTIVE', 'PARTIALLY_DISPENSED'].includes(p.status)).length;

  const totalValuation =
    reportSummary?.stock_valuation?.total_value ??
    batches.reduce((sum, b) => sum + (Number(b.quantity) || 0) * (Number(b.unit_cost) || 0), 0);

  // Filtered lists
  const filteredPrescriptions = useMemo(() => {
    return prescriptions.filter((p) => {
      const matchSearch =
        !prescriptionSearch ||
        p.patient_name?.toLowerCase().includes(prescriptionSearch.toLowerCase()) ||
        String(p.id).includes(prescriptionSearch) ||
        String((p as any).token_number || '').includes(prescriptionSearch);
      const matchStatus =
        prescriptionStatusFilter === 'ALL' ||
        (prescriptionStatusFilter === 'PENDING'
          ? p.status === 'PENDING' || p.status === 'ACTIVE'
          : p.status === prescriptionStatusFilter);
      return matchSearch && matchStatus;
    });
  }, [prescriptions, prescriptionSearch, prescriptionStatusFilter]);

  const filteredMedicines = useMemo(() => {
    return medicines.filter((m) => {
      const query = medicineSearchQuery.toLowerCase();
      const matchSearch =
        !medicineSearchQuery ||
        m.generic_name?.toLowerCase().includes(query) ||
        m.brand_name?.toLowerCase().includes(query) ||
        m.code?.toLowerCase().includes(query);
      const matchCategory = medicineCategoryFilter === 'ALL' || m.category === medicineCategoryFilter;
      return matchSearch && matchCategory;
    });
  }, [medicines, medicineSearchQuery, medicineCategoryFilter]);

  const medicineCategories = useMemo(() => {
    return Array.from(new Set(medicines.map((m) => m.category).filter(Boolean)));
  }, [medicines]);

  // Batches sorted by expiry ASC for strict FEFO visibility
  const sortedAndFilteredBatches = useMemo(() => {
    const list = batches.filter((b) => {
      const query = batchSearchQuery.toLowerCase();
      const matchSearch =
        !batchSearchQuery ||
        b.batch_number?.toLowerCase().includes(query) ||
        b.medicine_name?.toLowerCase().includes(query) ||
        b.generic_name?.toLowerCase().includes(query);
      const matchStatus = batchStatusFilter === 'ALL' || b.status === batchStatusFilter;
      return matchSearch && matchStatus;
    });
    // FEFO Sort: Earliest expiry date first
    return list.sort((a, b) => new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime());
  }, [batches, batchSearchQuery, batchStatusFilter]);

  const filteredTransactions = useMemo(() => {
    return transactions.filter((t) => {
      const query = txSearchQuery.toLowerCase();
      const matchSearch =
        !txSearchQuery ||
        t.medicine_name?.toLowerCase().includes(query) ||
        t.batch_number?.toLowerCase().includes(query) ||
        t.reference_id?.toLowerCase().includes(query) ||
        (t.performed_by_name || '').toLowerCase().includes(query);
      const matchType = txTypeFilter === 'ALL' || t.transaction_type === txTypeFilter;
      return matchSearch && matchType;
    });
  }, [transactions, txSearchQuery, txTypeFilter]);

  const filteredVendors = useMemo(() => {
    return vendors.filter((v) => {
      const query = vendorSearch.toLowerCase();
      const matchSearch =
        !vendorSearch ||
        (v.vendor_name || v.name || '').toLowerCase().includes(query) ||
        (v.contact_person || '').toLowerCase().includes(query) ||
        (v.phone || '').toLowerCase().includes(query) ||
        (v.gst_number || v.gstin || '').toLowerCase().includes(query);
      const matchStatus = vendorStatusFilter === 'ALL' || v.status === vendorStatusFilter;
      return matchSearch && matchStatus;
    });
  }, [vendors, vendorSearch, vendorStatusFilter]);

  const filteredPOs = useMemo(() => {
    return purchaseOrders.filter((po) => {
      const query = poSearchQuery.toLowerCase();
      const matchSearch =
        !poSearchQuery ||
        po.po_number?.toLowerCase().includes(query) ||
        (po.vendor_name || '').toLowerCase().includes(query) ||
        (po.notes || '').toLowerCase().includes(query);
      const matchStatus =
        poStatusFilter === 'ALL' ||
        (poStatusFilter === 'PENDING_APPROVAL'
          ? ['PENDING_APPROVAL', 'PENDING'].includes(po.status)
          : po.status === poStatusFilter);
      return matchSearch && matchStatus;
    });
  }, [purchaseOrders, poSearchQuery, poStatusFilter]);

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alt) => {
      if (alertTypeFilter === 'ALL') return true;
      return alt.alert_type === alertTypeFilter || alt.type === alertTypeFilter;
    });
  }, [alerts, alertTypeFilter]);

  // Action Required Data for Dashboard
  const lowStockActionItems = useMemo(() => {
    return medicines
      .filter((m) => {
        const stock = m.available_stock ?? m.total_available_stock ?? 0;
        return m.stock_status === 'LOW_STOCK' || m.stock_status === 'OUT_OF_STOCK' || stock <= m.reorder_level;
      })
      .slice(0, 4);
  }, [medicines]);

  const expiringActionItems = useMemo(() => {
    return batches
      .filter((b) => {
        if (b.quantity <= 0) return false;
        const d = new Date(b.expiry_date);
        const days = (d.getTime() - Date.now()) / (1000 * 60 * 60 * 24);
        return days > 0 && days <= 60;
      })
      .sort((a, b) => new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime())
      .slice(0, 4);
  }, [batches]);

  const pendingReceiptActionItems = useMemo(() => {
    return purchaseOrders
      .filter((po) => ['ORDERED', 'PARTIALLY_RECEIVED', 'APPROVED'].includes(po.status))
      .slice(0, 4);
  }, [purchaseOrders]);

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
              <h1 className="text-xl font-black text-slate-900 tracking-tight">Pharmacy & Dispensing</h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                FEFO Engine Active
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-2">
              <span>
                Facility: <strong className="text-slate-800 font-semibold">{activeFacility?.facility_name || 'Central Store'}</strong>
              </span>
              <span className="text-slate-300">•</span>
              <span>Prescription Queue → Dispense (FEFO) → Auto Stock Deduct</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {!isReadOnly && (
            <>
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
            </>
          )}
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

      {/* Primary Simplified 7-Section Navigation */}
      <div className="bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200/80 flex flex-wrap items-center gap-1 shadow-xs">
        {[
          { id: 'DASHBOARD', label: 'Dashboard', icon: Boxes, badge: null, badgeColor: '' },
          {
            id: 'PRESCRIPTIONS',
            label: 'Prescriptions',
            icon: ClipboardList,
            badge: pendingPrescriptionsCount > 0 ? `${pendingPrescriptionsCount} Waiting` : null,
            badgeColor: 'bg-amber-100 text-amber-800 border-amber-300 animate-pulse',
          },
          {
            id: 'INVENTORY',
            label: 'Inventory',
            icon: Pill,
            badge: `${medicinesTotalCount}`,
            badgeColor: 'bg-slate-200/80 text-slate-700 border-slate-300',
          },
          {
            id: 'PURCHASE_ORDERS',
            label: 'Purchase Orders',
            icon: Truck,
            badge: (kpis?.pending_purchase_orders_count ?? 0) > 0 ? `${kpis?.pending_purchase_orders_count}` : null,
            badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
          },
          {
            id: 'VENDORS',
            label: 'Vendors',
            icon: Building2,
            badge: `${vendorsTotalCount}`,
            badgeColor: 'bg-slate-200/80 text-slate-700 border-slate-300',
          },
          {
            id: 'ALERTS',
            label: 'Alerts',
            icon: AlertTriangle,
            badge: alerts.length > 0 ? `${alerts.length}` : null,
            badgeColor: 'bg-rose-100 text-rose-800 border-rose-300',
          },
          {
            id: 'REPORTS',
            label: 'Reports',
            icon: FileSpreadsheet,
            badge: null,
            badgeColor: '',
          },
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

      {/* ========================================================= */}
      {/* 1. PHARMACY DASHBOARD                                    */}
      {/* ========================================================= */}
      {activeTab === 'DASHBOARD' && (
        <div className="space-y-6">
          {/* Exactly 6 Lean KPI Cards: TODAY */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Today's Key Metrics</h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
              <div
                onClick={() => setActiveTab('PRESCRIPTIONS')}
                className="p-4 rounded-2xl bg-white border border-amber-200/90 shadow-xs space-y-1 hover:border-amber-400 transition cursor-pointer"
              >
                <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">Prescriptions Waiting</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-black text-amber-900">{kpis?.pending_prescriptions_count ?? 0}</span>
                  <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
                    <ClipboardList className="w-4 h-4" />
                  </div>
                </div>
                <span className="text-[10px] text-amber-600 font-medium block">Waiting for Dispense</span>
              </div>

              <div className="p-4 rounded-2xl bg-white border border-teal-200/90 shadow-xs space-y-1 hover:border-teal-400 transition">
                <span className="text-[11px] font-bold text-teal-700 uppercase tracking-wider block">Medicines Dispensed</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-black text-teal-900">{kpis?.dispensed_today_count ?? 0}</span>
                  <div className="p-1.5 rounded-lg bg-teal-50 text-teal-600">
                    <PackageCheck className="w-4 h-4" />
                  </div>
                </div>
                <span className="text-[10px] text-teal-600 font-medium block">Today's completed Rx</span>
              </div>

              <div
                onClick={() => {
                  setActiveTab('INVENTORY');
                  setInventorySubTab('CURRENT_STOCK');
                }}
                className="p-4 rounded-2xl bg-white border border-amber-200/90 shadow-xs space-y-1 hover:border-amber-400 transition cursor-pointer"
              >
                <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">Low Stock</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-black text-amber-900">{kpis?.low_stock_count ?? 0}</span>
                  <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                </div>
                <span className="text-[10px] text-amber-600 font-medium block">Below reorder level</span>
              </div>

              <div
                onClick={() => {
                  setActiveTab('INVENTORY');
                  setInventorySubTab('BATCHES');
                  setBatchStatusFilter('EXPIRING_SOON');
                }}
                className="p-4 rounded-2xl bg-white border border-rose-200/90 shadow-xs space-y-1 hover:border-rose-400 transition cursor-pointer"
              >
                <span className="text-[11px] font-bold text-rose-700 uppercase tracking-wider block">Expiring Soon</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-black text-rose-900">{kpis?.expiring_soon_count ?? 0}</span>
                  <div className="p-1.5 rounded-lg bg-rose-50 text-rose-600">
                    <Clock className="w-4 h-4" />
                  </div>
                </div>
                <span className="text-[10px] text-rose-600 font-medium block">Next 60 days</span>
              </div>

              <div
                onClick={() => {
                  setActiveTab('INVENTORY');
                  setInventorySubTab('CURRENT_STOCK');
                }}
                className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1 hover:border-slate-300 transition cursor-pointer"
              >
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Out of Stock</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-black text-slate-900">{kpis?.out_of_stock_count ?? 0}</span>
                  <div className="p-1.5 rounded-lg bg-slate-100 text-slate-600">
                    <Pill className="w-4 h-4" />
                  </div>
                </div>
                <span className="text-[10px] text-slate-400 font-medium block">0 units on shelf</span>
              </div>

              <div
                onClick={() => setActiveTab('PURCHASE_ORDERS')}
                className="p-4 rounded-2xl bg-white border border-blue-200/90 shadow-xs space-y-1 hover:border-blue-400 transition cursor-pointer"
              >
                <span className="text-[11px] font-bold text-blue-700 uppercase tracking-wider block">Pending POs</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-black text-blue-900">{kpis?.pending_purchase_orders_count ?? 0}</span>
                  <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                    <Truck className="w-4 h-4" />
                  </div>
                </div>
                <span className="text-[10px] text-blue-600 font-medium block">Orders in progress</span>
              </div>
            </div>
          </div>

          {/* TODAY'S PHARMACY WORK: Simple Workflow */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Boxes className="w-4 h-4 text-emerald-600" /> Today's Pharmacy Workflow
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Track real-time progress from incoming prescription to completed dispensing.
                </p>
              </div>
              <button
                onClick={() => setActiveTab('PRESCRIPTIONS')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer"
              >
                <span>Open Prescription Queue</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">1. Prescriptions Waiting</span>
                  <span className="text-xl font-black text-slate-900 mt-1 block">
                    {kpis?.pending_prescriptions_count ?? 0}
                  </span>
                </div>
                <div className="p-2 rounded-xl bg-amber-100 text-amber-700 font-bold text-xs">Queue</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">2. Ready to Dispense</span>
                  <span className="text-xl font-black text-slate-900 mt-1 block">
                    {prescriptions.filter((p) => p.status === 'PENDING').length}
                  </span>
                </div>
                <div className="p-2 rounded-xl bg-blue-100 text-blue-700 font-bold text-xs">FEFO Batch Ready</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">3. Dispensed Today</span>
                  <span className="text-xl font-black text-emerald-800 mt-1 block">
                    {kpis?.dispensed_today_count ?? 0}
                  </span>
                </div>
                <div className="p-2 rounded-xl bg-emerald-100 text-emerald-700 font-bold text-xs">Completed</div>
              </div>
            </div>
          </div>

          {/* ACTION REQUIRED: Low Stock, Expiring, Pending Receipt */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" /> Action Required
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Only tasks requiring immediate pharmacist action are listed below.
                </p>
              </div>
              <span className="text-xs text-slate-400 font-medium">
                {lowStockActionItems.length + expiringActionItems.length + pendingReceiptActionItems.length} Actions
              </span>
            </div>

            {lowStockActionItems.length === 0 && expiringActionItems.length === 0 && pendingReceiptActionItems.length === 0 ? (
              <div className="py-10 text-center text-slate-400 text-xs">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                <p className="font-semibold text-slate-700 text-sm">No Immediate Actions Required</p>
                <p className="text-[11px] mt-1">All medicine stock levels are healthy, batches are valid, and orders are processed.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* 1. Low Stock Card Column */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between text-xs font-bold text-amber-800 uppercase tracking-wider px-1">
                    <span>Low Stock Medicines</span>
                    <span className="text-[10px] bg-amber-100 px-2 py-0.5 rounded-full">{lowStockActionItems.length}</span>
                  </div>

                  {lowStockActionItems.length === 0 ? (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-center text-[11px] text-slate-400">
                      All medicines are sufficiently stocked.
                    </div>
                  ) : (
                    lowStockActionItems.map((med) => {
                      const stock = med.available_stock ?? med.total_available_stock ?? 0;
                      return (
                        <div key={med.id} className="p-3.5 rounded-xl border border-amber-200 bg-amber-50/40 space-y-2 text-xs">
                          <div>
                            <strong className="text-slate-900 font-bold text-sm block">{med.generic_name}</strong>
                            <span className="text-[11px] text-slate-500">
                              {med.strength} • {med.dosage_form}
                            </span>
                          </div>
                          <div className="flex justify-between text-[11px] text-slate-600 font-medium">
                            <span>
                              Current: <strong className="text-amber-900 font-bold">{stock}</strong> {med.unit}
                            </span>
                            <span>
                              Reorder Level: <strong className="text-slate-800">{med.reorder_level}</strong>
                            </span>
                          </div>
                          {!isReadOnly && (
                            <button
                              onClick={() => handleOpenCreatePOForMedicine(med.id)}
                              className="w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg transition shadow-2xs cursor-pointer flex items-center justify-center gap-1.5"
                            >
                              <ShoppingCart className="w-3.5 h-3.5" />
                              <span>Create PO</span>
                            </button>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>

                {/* 2. Expiring Batches Column */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between text-xs font-bold text-rose-800 uppercase tracking-wider px-1">
                    <span>Expiring Soon Batches</span>
                    <span className="text-[10px] bg-rose-100 px-2 py-0.5 rounded-full">{expiringActionItems.length}</span>
                  </div>

                  {expiringActionItems.length === 0 ? (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-center text-[11px] text-slate-400">
                      No batches expiring within the next 60 days.
                    </div>
                  ) : (
                    expiringActionItems.map((b) => (
                      <div key={b.id} className="p-3.5 rounded-xl border border-rose-200 bg-rose-50/40 space-y-2 text-xs">
                        <div>
                          <strong className="text-slate-900 font-bold text-sm block">
                            {b.medicine_name || b.generic_name || 'Drug'}
                          </strong>
                          <span className="text-[11px] text-slate-500 font-mono">
                            Batch: <strong className="text-slate-800">{b.batch_number}</strong> ({b.quantity} left)
                          </span>
                        </div>
                        <div className="flex justify-between text-[11px] text-slate-600 font-medium">
                          <span>
                            Expires: <strong className="text-rose-700 font-bold">{formatDateOnly(b.expiry_date)}</strong>
                          </span>
                        </div>
                        <button
                          onClick={() => {
                            setActiveTab('INVENTORY');
                            setInventorySubTab('BATCHES');
                            setBatchSearchQuery(b.batch_number);
                          }}
                          className="w-full py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5"
                        >
                          <Eye className="w-3.5 h-3.5 text-slate-600" />
                          <span>View Batch</span>
                        </button>
                      </div>
                    ))
                  )}
                </div>

                {/* 3. Pending Receipt POs Column */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between text-xs font-bold text-blue-800 uppercase tracking-wider px-1">
                    <span>Pending Receipt POs</span>
                    <span className="text-[10px] bg-blue-100 px-2 py-0.5 rounded-full">{pendingReceiptActionItems.length}</span>
                  </div>

                  {pendingReceiptActionItems.length === 0 ? (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-center text-[11px] text-slate-400">
                      No purchase orders pending goods receipt.
                    </div>
                  ) : (
                    pendingReceiptActionItems.map((po) => (
                      <div key={po.id} className="p-3.5 rounded-xl border border-blue-200 bg-blue-50/40 space-y-2 text-xs">
                        <div>
                          <div className="flex justify-between items-center">
                            <strong className="text-slate-900 font-mono font-bold text-sm block">{po.po_number}</strong>
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-blue-100 text-blue-800">
                              {po.status}
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-600 block mt-0.5">
                            Vendor: <strong className="text-slate-800">{po.vendor_name}</strong>
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Expected: {formatDateOnly(po.expected_delivery || po.expected_delivery_date)}
                        </div>
                        {!isReadOnly && (
                          <button
                            onClick={() => openReceivingModal(po)}
                            className="w-full py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition shadow-2xs cursor-pointer flex items-center justify-center gap-1.5"
                          >
                            <Truck className="w-3.5 h-3.5" />
                            <span>Receive Stock</span>
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 2. PRESCRIPTIONS (PRIMARY DISPENSING SCREEN)             */}
      {/* ========================================================= */}
      {activeTab === 'PRESCRIPTIONS' && (
        <div className="space-y-4">
          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search patient, token, or Rx ID..."
                value={prescriptionSearch}
                onChange={(e) => setPrescriptionSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
              />
            </div>

            <div className="flex items-center gap-2 self-stretch sm:self-auto justify-end">
              <span className="text-xs text-slate-500 font-medium">Filter Status:</span>
              <select
                value={prescriptionStatusFilter}
                onChange={(e) => setPrescriptionStatusFilter(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="ALL">All Prescriptions ({prescriptionsTotalCount})</option>
                <option value="PENDING">Waiting for Dispense ({pendingPrescriptionsCount})</option>
                <option value="PARTIALLY_DISPENSED">Partially Dispensed</option>
                <option value="DISPENSED">Completed & Dispensed</option>
              </select>
            </div>
          </div>

          {/* Prescriptions Table */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">Patient</th>
                    <th className="p-4">Prescription</th>
                    <th className="p-4">Doctor</th>
                    <th className="p-4">Medicines</th>
                    <th className="p-4">Quantity</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredPrescriptions.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-12 text-center text-slate-400 font-medium">
                        <PackageCheck className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                        <p className="font-semibold text-slate-600">No prescriptions waiting for dispensing.</p>
                        <p className="text-[11px] mt-1">Prescriptions issued by doctors in OPD will appear here in real-time.</p>
                      </td>
                    </tr>
                  ) : (
                    filteredPrescriptions.map((p) => {
                      const totalQty = (p.items || []).reduce((acc, it) => acc + (it.quantity || 0), 0);
                      const isPending = p.status !== 'DISPENSED';

                      return (
                        <tr key={p.id} className="hover:bg-slate-50/80 transition">
                          <td className="p-4">
                            <div className="font-bold text-slate-900 text-sm">{p.patient_name}</div>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className="text-[10px] text-slate-400 font-mono">ID #{p.patient}</span>
                              {(p as any).token_number && (
                                <span className="px-1.5 py-0.2 rounded-full bg-emerald-50 text-emerald-800 text-[10px] font-mono font-bold border border-emerald-200">
                                  Token #{(p as any).token_number}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="p-4 font-mono font-bold">
                            <div className="text-emerald-800">{p.prescription_number || `#RX-${String(p.id).padStart(4, '0')}`}</div>
                            {p.date && (
                              <span className="block text-[10px] text-slate-400 font-sans font-normal mt-0.5">
                                {formatDateOnly(p.date)}
                              </span>
                            )}
                          </td>
                          <td className="p-4 text-slate-600 font-medium">{p.doctor_name || 'Dr. Kumar'}</td>
                          <td className="p-4 space-y-1">
                            {p.items?.map((item, i) => (
                              <div
                                key={i}
                                className="text-slate-800 text-[11px] flex items-center justify-between gap-3 bg-slate-50 px-2 py-0.5 rounded border border-slate-200/60"
                              >
                                <span>
                                  <strong className="text-slate-900">{item.medicine_name}</strong>
                                </span>
                                <span className="font-mono text-slate-600 font-bold">× {item.quantity}</span>
                              </div>
                            ))}
                          </td>
                          <td className="p-4 font-mono font-bold text-slate-700">
                            {totalQty} {totalQty === 1 ? 'unit' : 'units'}
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
                              {isPending && <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>}
                              {p.status === 'DISPENSED' ? 'COMPLETED' : p.status}
                            </span>
                          </td>
                          <td className="p-4 text-right">
                            {isPending ? (
                              <button
                                onClick={() => openDispenseModal(p)}
                                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs inline-flex items-center gap-1.5 transition cursor-pointer"
                              >
                                <PackageCheck className="w-3.5 h-3.5" />
                                <span>Dispense</span>
                              </button>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 px-3 py-1 rounded-lg bg-emerald-50 border border-emerald-200">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>Dispensed</span>
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 3. INVENTORY (ABSORBS CURRENT STOCK, BATCHES, HISTORY)   */}
      {/* ========================================================= */}
      {activeTab === 'INVENTORY' && (
        <div className="space-y-4">
          {/* Inventory Sub-navigation */}
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
            {[
              { id: 'CURRENT_STOCK', label: 'Current Stock', icon: Pill, count: medicinesTotalCount },
              { id: 'BATCHES', label: 'Batches', icon: Layers, count: batchesTotalCount },
              { id: 'STOCK_HISTORY', label: 'Stock History', icon: History, count: transactionsTotalCount },
            ].map((sub) => {
              const Icon = sub.icon;
              const isSubActive = inventorySubTab === sub.id;
              return (
                <button
                  key={sub.id}
                  onClick={() => setInventorySubTab(sub.id as InventorySubTab)}
                  className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                    isSubActive
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isSubActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <span>{sub.label}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                      isSubActive ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {sub.count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* SUB-TAB 1: CURRENT STOCK */}
          {inventorySubTab === 'CURRENT_STOCK' && (
            <div className="space-y-4">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                <div className="relative w-full md:w-80">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search medicine name..."
                    value={medicineSearchQuery}
                    onChange={(e) => setMedicineSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
                  />
                </div>

                <div className="flex flex-wrap items-center gap-1.5 self-stretch md:self-auto">
                  {canCreateMedicine && (
                    <button
                      onClick={() => setShowAddMedicineModal(true)}
                      className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition cursor-pointer mr-2"
                    >
                      <Plus className="w-3.5 h-3.5" /> Add Medicine
                    </button>
                  )}
                  <button
                    onClick={() => setMedicineCategoryFilter('ALL')}
                    className={`px-3 py-1 rounded-xl text-xs font-bold transition cursor-pointer ${
                      medicineCategoryFilter === 'ALL'
                        ? 'bg-slate-900 text-white shadow-2xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    All ({medicinesTotalCount})
                  </button>
                  {medicineCategories.slice(0, 4).map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setMedicineCategoryFilter(cat)}
                      className={`px-3 py-1 rounded-xl text-xs font-bold transition cursor-pointer ${
                        medicineCategoryFilter === cat
                          ? 'bg-slate-900 text-white shadow-2xs'
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
                        <th className="p-4">Medicine</th>
                        <th className="p-4">Current Stock</th>
                        <th className="p-4">Reorder Level</th>
                        <th className="p-4">Status</th>
                        <th className="p-4">Nearest Expiry</th>
                        <th className="p-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredMedicines.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="p-10 text-center text-slate-400 font-medium">
                            <Pill className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                            No medicines found matching the current search.
                          </td>
                        </tr>
                      ) : (
                        filteredMedicines.map((m) => {
                          const stock = m.available_stock ?? m.total_available_stock ?? 0;
                          const nearestExp = getNearestExpiry(m.id, m.generic_name);

                          return (
                            <tr key={m.id} className="hover:bg-slate-50/80 transition">
                              <td className="p-4">
                                <div className="font-bold text-slate-900 text-sm">{m.generic_name}</div>
                                <div className="text-[11px] text-slate-500">
                                  {m.brand_name ? `${m.brand_name} • ` : ''}
                                  {m.strength} {m.dosage_form}
                                </div>
                              </td>
                              <td className="p-4 font-mono font-black text-slate-900 text-sm">
                                {stock} {m.unit}
                              </td>
                              <td className="p-4 font-mono font-bold text-slate-600">
                                {m.reorder_level} {m.unit}
                              </td>
                              <td className="p-4">
                                <span
                                  className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                                    m.stock_status === 'OUT_OF_STOCK' || stock <= 0
                                      ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                      : m.stock_status === 'LOW_STOCK' || stock <= m.reorder_level
                                      ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                      : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                  }`}
                                >
                                  {stock <= 0 ? 'OUT OF STOCK' : stock <= m.reorder_level ? 'LOW STOCK' : 'NORMAL'}
                                </span>
                              </td>
                              <td className="p-4 font-mono font-bold text-slate-700">{nearestExp}</td>
                              <td className="p-4 text-right">
                                <div className="inline-flex items-center gap-1.5">
                                  <button
                                    onClick={() => setSelectedMedicineForDetails(m)}
                                    className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition cursor-pointer inline-flex items-center gap-1"
                                  >
                                    <Eye className="w-3.5 h-3.5 text-slate-500" />
                                    <span>View</span>
                                  </button>
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
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* SUB-TAB 2: BATCHES (SORTED BY EXPIRY ASC FOR FEFO VISIBILITY) */}
          {inventorySubTab === 'BATCHES' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                <div className="relative w-full sm:w-80">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search batch number or medicine..."
                    value={batchSearchQuery}
                    onChange={(e) => setBatchSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
                  />
                </div>

                <div className="flex items-center gap-2 self-stretch sm:self-auto justify-end">
                  <span className="text-xs text-slate-500 font-medium">Batch Status:</span>
                  <select
                    value={batchStatusFilter}
                    onChange={(e) => setBatchStatusFilter(e.target.value)}
                    className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="ALL">All Batches ({batchesTotalCount})</option>
                    <option value="ACTIVE">Active & Available</option>
                    <option value="EXPIRING_SOON">Expiring Soon</option>
                    <option value="EXPIRED">Expired</option>
                    <option value="EXHAUSTED">Exhausted (0 Qty)</option>
                  </select>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50/80 text-slate-600 font-bold border-b border-slate-200">
                      <tr>
                        <th className="p-4">Medicine</th>
                        <th className="p-4">Batch Number</th>
                        <th className="p-4">Quantity</th>
                        <th className="p-4">Expiry</th>
                        <th className="p-4">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {sortedAndFilteredBatches.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="p-10 text-center text-slate-400 font-medium">
                            <Layers className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                            No batches found matching filter.
                          </td>
                        </tr>
                      ) : (
                        sortedAndFilteredBatches.map((b) => (
                          <tr key={b.id} className="hover:bg-slate-50/80 transition">
                            <td className="p-4">
                              <strong className="text-slate-900 font-bold text-sm block">
                                {b.medicine_name || b.generic_name}
                              </strong>
                              <span className="text-[11px] text-slate-500">{b.supplier || 'Standard Supplier'}</span>
                            </td>
                            <td className="p-4 font-mono font-bold text-slate-800">{b.batch_number}</td>
                            <td className="p-4 font-mono font-black text-slate-900">{b.quantity} units</td>
                            <td className="p-4 font-mono font-bold text-slate-700">{formatDateOnly(b.expiry_date)}</td>
                            <td className="p-4">
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                                  b.is_expired || b.status === 'EXPIRED'
                                    ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                    : b.status === 'EXPIRING_SOON'
                                    ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                    : b.status === 'EXHAUSTED'
                                    ? 'bg-slate-100 text-slate-600 border border-slate-200'
                                    : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                }`}
                              >
                                {b.status}
                              </span>
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

          {/* SUB-TAB 3: STOCK HISTORY (USES created_at & performed_by_name) */}
          {inventorySubTab === 'STOCK_HISTORY' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                <div className="relative w-full sm:w-80">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search transaction, drug, reference..."
                    value={txSearchQuery}
                    onChange={(e) => setTxSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
                  />
                </div>

                <div className="flex items-center gap-2 self-stretch sm:self-auto justify-end">
                  <span className="text-xs text-slate-500 font-medium">Type:</span>
                  <select
                    value={txTypeFilter}
                    onChange={(e) => setTxTypeFilter(e.target.value)}
                    className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="ALL">All Transactions ({transactionsTotalCount})</option>
                    <option value="DISPENSED">Dispensed to Patient</option>
                    <option value="PURCHASE_RECEIVED">Purchase Received</option>
                    <option value="ADJUSTMENT">Stock Audit Adjustment</option>
                    <option value="EXPIRED">Expired Stock</option>
                    <option value="DAMAGED">Damaged / Wastage</option>
                  </select>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50/80 text-slate-600 font-bold border-b border-slate-200">
                      <tr>
                        <th className="p-4">Date & Time</th>
                        <th className="p-4">Transaction</th>
                        <th className="p-4">Medicine</th>
                        <th className="p-4">Batch</th>
                        <th className="p-4">Quantity</th>
                        <th className="p-4">Reference</th>
                        <th className="p-4">Performed By</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredTransactions.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="p-10 text-center text-slate-400 font-medium">
                            <History className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                            No stock transactions found.
                          </td>
                        </tr>
                      ) : (
                        filteredTransactions.map((tx) => (
                          <tr key={tx.id} className="hover:bg-slate-50/80 transition">
                            <td className="p-4 font-mono text-slate-600 whitespace-nowrap">
                              {formatDateTime(tx.created_at || (tx as any).timestamp)}
                            </td>
                            <td className="p-4">
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                                  tx.transaction_type === 'DISPENSED'
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : tx.transaction_type === 'PURCHASE_RECEIVED'
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-slate-100 text-slate-700'
                                }`}
                              >
                                {tx.transaction_type.replace('_', ' ')}
                              </span>
                            </td>
                            <td className="p-4 font-bold text-slate-900">{tx.medicine_name || 'Medicine'}</td>
                            <td className="p-4 font-mono font-medium text-slate-600">{tx.batch_number || 'N/A'}</td>
                            <td className="p-4 font-mono font-bold text-slate-800">
                              {tx.transaction_type === 'DISPENSED' ? `-${tx.quantity}` : `+${tx.quantity}`}
                            </td>
                            <td className="p-4 font-mono text-[11px] text-slate-500">{tx.reference_id || '-'}</td>
                            <td className="p-4 text-slate-700 font-medium">
                              {tx.performed_by_name || tx.created_by_name || 'Pharmacist'}
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
        </div>
      )}

      {/* ========================================================= */}
      {/* 4. PURCHASE ORDERS                                       */}
      {/* ========================================================= */}
      {activeTab === 'PURCHASE_ORDERS' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <Truck className="w-4 h-4 text-blue-600" /> Purchase Orders
              </h2>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Manage drug procurement: Create PO → Administrative Approval → Place Order → Receive Stock into Batches.
              </p>
            </div>
            {!isReadOnly && (
              <button
                onClick={() => setShowCreatePOModal(true)}
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition self-start md:self-auto cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Purchase Order</span>
              </button>
            )}
          </div>

          {/* Status Filters & Search */}
          <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-center justify-between gap-3">
            <div className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search PO number or vendor..."
                value={poSearchQuery}
                onChange={(e) => setPoSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div className="flex items-center gap-1 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
              {[
                { id: 'ALL', label: 'All' },
                { id: 'DRAFT', label: 'Draft' },
                { id: 'PENDING_APPROVAL', label: 'Pending Approval' },
                { id: 'APPROVED', label: 'Approved' },
                { id: 'ORDERED', label: 'Ordered' },
                { id: 'PARTIALLY_RECEIVED', label: 'Partially Received' },
                { id: 'RECEIVED', label: 'Received' },
                { id: 'CANCELLED', label: 'Cancelled' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setPoStatusFilter(tab.id)}
                  className={`px-3 py-1 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                    poStatusFilter === tab.id
                      ? 'bg-slate-900 text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* PO Table */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">PO Number</th>
                    <th className="p-4">Vendor</th>
                    <th className="p-4">Items</th>
                    <th className="p-4">Total Amount</th>
                    <th className="p-4">Expected Date</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredPOs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-10 text-center text-slate-400 font-medium">
                        <Truck className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                        No purchase orders require attention.
                      </td>
                    </tr>
                  ) : (
                    filteredPOs.map((po) => {
                      const canReceive = ['ORDERED', 'PARTIALLY_RECEIVED', 'APPROVED'].includes(po.status);
                      const isDraft = po.status === 'DRAFT';
                      const isPendingApproval = ['PENDING_APPROVAL', 'PENDING'].includes(po.status);
                      const isApproved = po.status === 'APPROVED';

                      return (
                        <tr key={po.id} className="hover:bg-slate-50/80 transition">
                          <td className="p-4 font-mono font-bold text-slate-900">
                            {po.po_number}
                            <span className="block text-[10px] text-slate-400 font-sans font-normal mt-0.5">
                              {formatDateOnly(po.order_date)}
                            </span>
                          </td>
                          <td className="p-4">
                            <strong className="text-slate-900 font-bold text-sm block">{po.vendor_name}</strong>
                            <span className="text-[10px] text-slate-400 font-mono">{po.vendor_code || 'Supplier'}</span>
                          </td>
                          <td className="p-4">
                            <span className="font-bold text-slate-800">{po.items?.length || 0} item(s)</span>
                          </td>
                          <td className="p-4 font-mono font-black text-slate-900">
                            ₹{Number(po.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="p-4 font-mono text-slate-600">
                            {formatDateOnly(po.expected_delivery || po.expected_delivery_date)}
                          </td>
                          <td className="p-4">
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                                po.status === 'RECEIVED'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : po.status === 'ORDERED' || po.status === 'PARTIALLY_RECEIVED'
                                  ? 'bg-blue-100 text-blue-800'
                                  : po.status === 'PENDING_APPROVAL' || po.status === 'PENDING'
                                  ? 'bg-amber-100 text-amber-800'
                                  : po.status === 'CANCELLED'
                                  ? 'bg-slate-100 text-slate-500'
                                  : 'bg-slate-100 text-slate-700'
                              }`}
                            >
                              {po.status.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="p-4 text-right">
                            <div className="inline-flex items-center gap-1.5">
                              <button
                                onClick={() => setSelectedPOForDetails(po)}
                                className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-lg transition cursor-pointer"
                              >
                                View
                              </button>

                              {!isReadOnly && (
                                <>
                                  {isDraft && (
                                    <button
                                      onClick={() => handleSubmitPOForApproval(po.id)}
                                      disabled={poActionLoading}
                                      className="px-2.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs rounded-lg transition cursor-pointer"
                                    >
                                      Submit
                                    </button>
                                  )}

                                  {isPendingApproval && isHospitalAdmin && (
                                    <button
                                      onClick={() => handleApprovePO(po.id)}
                                      disabled={poActionLoading}
                                      className="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg transition cursor-pointer"
                                    >
                                      Approve
                                    </button>
                                  )}

                                  {isApproved && (
                                    <button
                                      onClick={() => handlePlaceOrder(po.id)}
                                      disabled={poActionLoading}
                                      className="px-2.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition cursor-pointer"
                                    >
                                      Place Order
                                    </button>
                                  )}

                                  {canReceive && (
                                    <button
                                      onClick={() => openReceivingModal(po)}
                                      className="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg transition shadow-2xs cursor-pointer inline-flex items-center gap-1"
                                    >
                                      <Truck className="w-3 h-3" />
                                      <span>Receive</span>
                                    </button>
                                  )}
                                </>
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
        </div>
      )}

      {/* ========================================================= */}
      {/* 5. VENDORS                                               */}
      {/* ========================================================= */}
      {activeTab === 'VENDORS' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search vendor name, contact, phone..."
                value={vendorSearch}
                onChange={(e) => setVendorSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
              />
            </div>

            <div className="flex items-center gap-2">
              {!isReadOnly && (
                <button
                  onClick={() => setShowAddVendorModal(true)}
                  className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Vendor
                </button>
              )}
            </div>
          </div>

          {/* Vendors Table */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">Vendor</th>
                    <th className="p-4">Contact</th>
                    <th className="p-4">Active Status</th>
                    <th className="p-4">Open POs</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredVendors.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-10 text-center text-slate-400 font-medium">
                        <Building2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                        No vendors found matching search.
                      </td>
                    </tr>
                  ) : (
                    filteredVendors.map((v) => {
                      const isActive = v.status === 'ACTIVE';

                      return (
                        <tr key={v.id} className="hover:bg-slate-50/80 transition">
                          <td className="p-4">
                            <strong className="text-slate-900 font-bold text-sm block">
                              {v.vendor_name || v.name}
                            </strong>
                            <span className="text-[10px] text-slate-400 font-mono">{v.vendor_code || `VEND-${v.id}`}</span>
                          </td>
                          <td className="p-4 text-slate-600">
                            <div className="font-medium text-slate-800">{v.contact_person || 'N/A'}</div>
                            <div className="text-[11px] text-slate-500">{v.phone || v.email || '-'}</div>
                          </td>
                          <td className="p-4">
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                                isActive ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {v.status || 'ACTIVE'}
                            </span>
                          </td>
                          <td className="p-4 font-mono font-bold text-slate-800">
                            {v.pending_orders ?? 0}
                          </td>
                          <td className="p-4 text-right">
                            <div className="inline-flex items-center gap-1.5">
                              <button
                                onClick={() => handleViewVendorDetails(v)}
                                className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-lg transition cursor-pointer"
                              >
                                View
                              </button>
                              {!isReadOnly && (
                                <>
                                  <button
                                    onClick={() => handleOpenEditVendor(v)}
                                    className="p-1.5 hover:bg-slate-100 text-slate-600 rounded-lg transition cursor-pointer"
                                    title="Edit Vendor"
                                  >
                                    <Edit2 className="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    onClick={() => handleToggleVendorStatus(v)}
                                    className={`px-2 py-1 rounded-lg text-[11px] font-bold border transition cursor-pointer ${
                                      isActive
                                        ? 'border-amber-200 text-amber-700 hover:bg-amber-50'
                                        : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                                    }`}
                                  >
                                    {isActive ? 'Deactivate' : 'Activate'}
                                  </button>
                                  {isHospitalAdmin && (
                                    <button
                                      onClick={() => handleDeleteVendor(v)}
                                      className="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition cursor-pointer"
                                      title="Delete Vendor"
                                    >
                                      <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                  )}
                                </>
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
        </div>
      )}

      {/* ========================================================= */}
      {/* 6. ALERTS (ACTIONABLE ONLY)                              */}
      {/* ========================================================= */}
      {activeTab === 'ALERTS' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" /> Actionable Pharmacy Alerts
              </h2>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Every alert corresponds to a real operational condition with an instant 1-click action button.
              </p>
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto">
              {[
                { id: 'ALL', label: 'All Alerts' },
                { id: 'LOW_STOCK', label: 'Low Stock' },
                { id: 'OUT_OF_STOCK', label: 'Out of Stock' },
                { id: 'EXPIRING_SOON', label: 'Expiring Soon' },
                { id: 'EXPIRED', label: 'Expired' },
                { id: 'PENDING_PURCHASE_ORDER', label: 'Pending PO' },
              ].map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setAlertTypeFilter(cat.id)}
                  className={`px-3 py-1 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                    alertTypeFilter === cat.id
                      ? 'bg-slate-900 text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {filteredAlerts.length === 0 ? (
            <div className="p-12 rounded-2xl bg-white border border-slate-200 text-center text-slate-400">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
              <p className="font-bold text-slate-700 text-sm">No pharmacy alerts.</p>
              <p className="text-xs text-slate-400 mt-1">All stock and procurement parameters are within normal ranges.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {filteredAlerts.map((alt) => {
                const isLow = alt.alert_type === 'LOW_STOCK' || alt.alert_type === 'OUT_OF_STOCK';
                const isExp = alt.alert_type === 'EXPIRING_SOON' || alt.alert_type === 'EXPIRED';
                const isPO = alt.alert_type === 'PENDING_PURCHASE_ORDER';

                return (
                  <div
                    key={alt.id}
                    className={`p-4 rounded-2xl border shadow-2xs flex flex-col justify-between gap-3 ${
                      alt.severity === 'CRITICAL'
                        ? 'bg-rose-50/70 border-rose-200'
                        : alt.severity === 'HIGH'
                        ? 'bg-amber-50/70 border-amber-200'
                        : 'bg-blue-50/70 border-blue-200'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="font-bold text-xs text-slate-900 flex items-center gap-1.5">
                          <AlertCircle
                            className={`w-4 h-4 ${
                              alt.severity === 'CRITICAL'
                                ? 'text-rose-600'
                                : alt.severity === 'HIGH'
                                ? 'text-amber-600'
                                : 'text-blue-600'
                            }`}
                          />
                          {alt.title}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-white border border-current text-slate-700 shrink-0">
                          {alt.severity}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{alt.description}</p>
                    </div>

                    <div className="pt-2 border-t border-slate-200/50 flex justify-end">
                      {isLow && alt.medicine_id && !isReadOnly && (
                        <button
                          onClick={() => handleOpenCreatePOForMedicine(alt.medicine_id!)}
                          className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer flex items-center gap-1.5"
                        >
                          <ShoppingCart className="w-3.5 h-3.5" />
                          <span>Create PO</span>
                        </button>
                      )}

                      {isExp && (
                        <button
                          onClick={() => {
                            setActiveTab('INVENTORY');
                            setInventorySubTab('BATCHES');
                            if (alt.batch_id) {
                              const b = batches.find((x) => x.id === alt.batch_id);
                              if (b) setBatchSearchQuery(b.batch_number);
                            }
                          }}
                          className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer flex items-center gap-1.5"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View Batch</span>
                        </button>
                      )}

                      {isPO && (
                        <button
                          onClick={() => {
                            setActiveTab('PURCHASE_ORDERS');
                            if (alt.po_id) {
                              const p = purchaseOrders.find((x) => x.id === alt.po_id);
                              if (p) setSelectedPOForDetails(p);
                            }
                          }}
                          className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer flex items-center gap-1.5"
                        >
                          <Truck className="w-3.5 h-3.5" />
                          <span>View PO</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================= */}
      {/* 7. REPORTS (CLEAN ANALYTICS & EXPORT)                    */}
      {/* ========================================================= */}
      {activeTab === 'REPORTS' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" /> Pharmacy Analytics & Reports
              </h2>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Authoritative summary of drug consumption, current stock valuation, and procurement expenditure.
              </p>
            </div>
            <button
              onClick={exportCSVReport}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-2 transition cursor-pointer"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Export CSV Report</span>
            </button>
          </div>

          {/* Simple Report Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Dispensed Today</span>
              <span className="text-2xl font-black text-slate-900 font-mono">
                {reportSummary?.dispensing_summary?.dispensed_today ?? kpis?.dispensed_today_count ?? 0}
              </span>
              <span className="text-[10px] text-slate-400 block">Units issued</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Prescriptions Count</span>
              <span className="text-2xl font-black text-teal-800 font-mono">
                {reportSummary?.dispensing_summary?.prescriptions_count ?? kpis?.dispensed_today_count ?? 0}
              </span>
              <span className="text-[10px] text-slate-400 block">Fulfilled today</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Stock Value</span>
              <span className="text-xl font-black text-emerald-900 font-mono">
                ₹{Number(totalValuation).toLocaleString('en-IN')}
              </span>
              <span className="text-[10px] text-slate-400 block">Current shelf inventory</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Low Stock Items</span>
              <span className="text-2xl font-black text-amber-700 font-mono">
                {kpis?.low_stock_count ?? 0}
              </span>
              <span className="text-[10px] text-slate-400 block">Below minimum</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Expired Items</span>
              <span className="text-2xl font-black text-rose-700 font-mono">
                {kpis?.expired_count ?? 0}
              </span>
              <span className="text-[10px] text-slate-400 block">Blocked batches</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Purchase Amount</span>
              <span className="text-xl font-black text-blue-900 font-mono">
                ₹{Number(reportSummary?.total_procurement_spend ?? procurementKpis?.total_spend ?? 0).toLocaleString('en-IN')}
              </span>
              <span className="text-[10px] text-slate-400 block">Total procurement</span>
            </div>
          </div>

          {/* Top Consumed Medicines Table */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Top Consumed Medicines</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-3">Medicine</th>
                    <th className="p-3">Brand</th>
                    <th className="p-3 font-mono text-right">Units Consumed</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {reportSummary?.consumption_summary?.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="p-6 text-center text-slate-400">
                        No dispensing consumption recorded yet.
                      </td>
                    </tr>
                  ) : (
                    reportSummary?.consumption_summary?.map((c, i) => (
                      <tr key={i} className="hover:bg-slate-50/80">
                        <td className="p-3 font-bold text-slate-900">{c.batch__medicine__generic_name}</td>
                        <td className="p-3 text-slate-600">{c.batch__medicine__brand_name || '-'}</td>
                        <td className="p-3 font-mono font-bold text-emerald-800 text-right">{c.total_consumed}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODALS                                                   */}
      {/* ========================================================= */}

      {/* 1. DISPENSE MODAL */}
      {dispenseModalRx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-xl rounded-2xl border border-slate-200 shadow-2xl overflow-hidden p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <span className="font-mono text-xs font-bold text-emerald-700 block">
                  {dispenseModalRx.prescription_number || `#RX-${String(dispenseModalRx.id).padStart(4, '0')}`}
                </span>
                <h2 className="text-base font-bold text-slate-900">
                  Dispense Medicines for {dispenseModalRx.patient_name}
                </h2>
              </div>
              <button
                onClick={() => setDispenseModalRx(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-sm cursor-pointer"
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
              <div className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
                <span>Prescribed Medicines (FEFO Auto-Selected)</span>
                <span className="text-[10px] text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  Earliest Expiry Prioritized
                </span>
              </div>

              {dispenseItems.map((item, idx) => {
                const availableBatches = batches.filter(
                  (b) =>
                    matchMedicineBatch(b.medicine_name || b.generic_name, item.medicine_name) &&
                    b.quantity > 0 &&
                    new Date(b.expiry_date) > new Date()
                );
                // Sort FEFO
                availableBatches.sort((a, b) => new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime());
                const selectedBatchObj = batches.find((b) => b.id === item.batch_id);

                return (
                  <div key={idx} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <strong className="text-slate-900 font-bold text-sm">{item.medicine_name}</strong>
                      <span className="text-slate-600 font-mono font-bold">Required: {item.target_qty} units</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                      <div>
                        <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                          Selected Batch (FEFO)
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
                          {availableBatches.length === 0 && <option value={0}>No valid batches available</option>}
                          {availableBatches.map((b) => (
                            <option key={b.id} value={b.id}>
                              {b.batch_number} (Avail: {b.quantity} | Exp: {formatDateOnly(b.expiry_date)})
                            </option>
                          ))}
                        </select>
                        {selectedBatchObj && (
                          <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                            <span>Available Stock: {selectedBatchObj.quantity}</span>
                            <span className="font-bold text-rose-700">Expires: {formatDateOnly(selectedBatchObj.expiry_date)}</span>
                          </div>
                        )}
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
                type="button"
                onClick={() => setDispenseModalRx(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDispense}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer"
              >
                Confirm Dispense
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. MEDICINE DETAILS MODAL (ACCESSED VIA [VIEW] IN INVENTORY) */}
      {selectedMedicineForDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-2xl rounded-2xl border border-slate-200 shadow-2xl overflow-hidden p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">
                  {selectedMedicineForDetails.generic_name}
                </h2>
                <p className="text-xs text-slate-500">
                  {selectedMedicineForDetails.strength} • {selectedMedicineForDetails.dosage_form} • {selectedMedicineForDetails.category}
                </p>
              </div>
              <button
                onClick={() => setSelectedMedicineForDetails(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Medicine Information & Stock Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200/80 text-xs">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Total Available Stock</span>
                <span className="text-lg font-black text-slate-900 font-mono mt-0.5 block">
                  {selectedMedicineForDetails.available_stock ?? selectedMedicineForDetails.total_available_stock ?? 0}{' '}
                  {selectedMedicineForDetails.unit}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Reorder Level</span>
                <span className="text-lg font-black text-slate-700 font-mono mt-0.5 block">
                  {selectedMedicineForDetails.reorder_level} {selectedMedicineForDetails.unit}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Minimum Stock</span>
                <span className="text-lg font-black text-slate-700 font-mono mt-0.5 block">
                  {selectedMedicineForDetails.minimum_stock} {selectedMedicineForDetails.unit}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Stock Status</span>
                <span className="inline-block mt-1 font-bold text-xs">
                  {selectedMedicineForDetails.stock_status || 'NORMAL'}
                </span>
              </div>
            </div>

            {/* Batches Table for this medicine */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-emerald-600" /> Active Batches (FEFO Order)
              </h3>
              {(() => {
                const medBatches = batches.filter(
                  (b) =>
                    b.medicine === selectedMedicineForDetails.id ||
                    matchMedicineBatch(b.medicine_name || b.generic_name, selectedMedicineForDetails.generic_name)
                );
                medBatches.sort((a, b) => new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime());

                return medBatches.length === 0 ? (
                  <p className="text-xs text-slate-400 py-3 text-center bg-slate-50 rounded-xl">
                    No active batches found for this medicine.
                  </p>
                ) : (
                  <div className="border border-slate-200 rounded-xl overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                        <tr>
                          <th className="p-2.5">Batch</th>
                          <th className="p-2.5">Quantity</th>
                          <th className="p-2.5">Expiry</th>
                          <th className="p-2.5">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {medBatches.map((b) => (
                          <tr key={b.id}>
                            <td className="p-2.5 font-mono font-bold text-slate-800">{b.batch_number}</td>
                            <td className="p-2.5 font-mono font-bold">{b.quantity} units</td>
                            <td className="p-2.5 font-mono text-slate-600">{formatDateOnly(b.expiry_date)}</td>
                            <td className="p-2.5">
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100">
                                {b.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              })()}
            </div>

            {/* Recent Stock History for this medicine */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <History className="w-3.5 h-3.5 text-blue-600" /> Recent Stock History
              </h3>
              {(() => {
                const medTxs = transactions
                  .filter(
                    (t) =>
                      t.medicine_name?.toLowerCase() === selectedMedicineForDetails.generic_name.toLowerCase() ||
                      (t as any).medicine === selectedMedicineForDetails.id
                  )
                  .slice(0, 5);

                return medTxs.length === 0 ? (
                  <p className="text-xs text-slate-400 py-3 text-center bg-slate-50 rounded-xl">
                    No stock transaction history for this medicine.
                  </p>
                ) : (
                  <div className="border border-slate-200 rounded-xl overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                        <tr>
                          <th className="p-2.5">Date & Time</th>
                          <th className="p-2.5">Transaction</th>
                          <th className="p-2.5">Quantity</th>
                          <th className="p-2.5">Reference</th>
                          <th className="p-2.5">Performed By</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {medTxs.map((tx) => (
                          <tr key={tx.id}>
                            <td className="p-2.5 font-mono text-slate-500 whitespace-nowrap">
                              {formatDateTime(tx.created_at)}
                            </td>
                            <td className="p-2.5 font-bold text-slate-800">{tx.transaction_type}</td>
                            <td className="p-2.5 font-mono font-bold">
                              {tx.transaction_type === 'DISPENSED' ? `-${tx.quantity}` : `+${tx.quantity}`}
                            </td>
                            <td className="p-2.5 font-mono text-[11px] text-slate-500">{tx.reference_id || '-'}</td>
                            <td className="p-2.5 text-slate-700">
                              {tx.performed_by_name || tx.created_by_name || 'Pharmacist'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              })()}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <button
                onClick={() => setSelectedMedicineForDetails(null)}
                className="px-4 py-2 bg-slate-900 text-white font-bold text-xs rounded-xl cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. GOODS RECEIVING MODAL */}
      {receivingPO && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-2xl rounded-2xl border border-slate-200 shadow-2xl overflow-hidden p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <span className="font-mono text-xs font-bold text-blue-700 block">{receivingPO.po_number}</span>
                <h2 className="text-base font-bold text-slate-900">
                  Receive Stock from {receivingPO.vendor_name}
                </h2>
              </div>
              <button onClick={() => setReceivingPO(null)} className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">
                ✕
              </button>
            </div>

            <div className="space-y-4 text-xs">
              {receiveItemsData.map((item, idx) => (
                <div key={idx} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 space-y-2.5">
                  <div className="flex justify-between items-center">
                    <strong className="text-slate-900 font-bold text-sm">{item.medicine_name}</strong>
                    <span className="text-slate-500 font-mono">
                      Ordered: {item.ordered_quantity} | Recv'd: {item.already_received} | Remaining: {item.requested_quantity}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                    <div>
                      <label className="font-bold text-slate-600 block mb-1">Receiving Now</label>
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
                        className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-bold"
                      />
                    </div>

                    <div>
                      <label className="font-bold text-slate-600 block mb-1">Batch Number</label>
                      <input
                        type="text"
                        value={item.batch_number}
                        onChange={(e) => {
                          const val = e.target.value;
                          setReceiveItemsData((prev) =>
                            prev.map((it, i) => (i === idx ? { ...it, batch_number: val } : it))
                          );
                        }}
                        className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-mono"
                      />
                    </div>

                    <div>
                      <label className="font-bold text-slate-600 block mb-1">Expiry Date</label>
                      <input
                        type="date"
                        value={item.expiry_date}
                        onChange={(e) => {
                          const val = e.target.value;
                          setReceiveItemsData((prev) =>
                            prev.map((it, i) => (i === idx ? { ...it, expiry_date: val } : it))
                          );
                        }}
                        className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs font-mono"
                      />
                    </div>

                    <div>
                      <label className="font-bold text-slate-600 block mb-1">Unit Cost (₹)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={item.unit_cost}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setReceiveItemsData((prev) =>
                            prev.map((it, i) => (i === idx ? { ...it, unit_cost: val } : it))
                          );
                        }}
                        className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-mono"
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
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmGoodsReceiving}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer"
              >
                Confirm Receipt
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4. CREATE PO MODAL */}
      {showCreatePOModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleCreatePO}
            className="bg-white w-full max-w-xl rounded-2xl border border-slate-200 shadow-2xl overflow-hidden p-6 space-y-4 max-h-[90vh] overflow-y-auto"
          >
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <ShoppingCart className="w-4 h-4 text-emerald-600" /> Create Purchase Order
              </h2>
              <button type="button" onClick={() => setShowCreatePOModal(false)} className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Select Vendor *</label>
                <select
                  required
                  value={newPOData.vendor}
                  onChange={(e) => setNewPOData({ ...newPOData, vendor: Number(e.target.value) })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-bold text-slate-800"
                >
                  <option value={0}>-- Select Vendor --</option>
                  {vendors.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.vendor_name || v.name} {v.status === 'INACTIVE' ? '(Inactive)' : ''}
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
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 font-mono"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="font-bold text-slate-700 block mb-1">Procurement Notes</label>
                <input
                  type="text"
                  placeholder="Optional procurement instructions..."
                  value={newPOData.notes}
                  onChange={(e) => setNewPOData({ ...newPOData, notes: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2"
                />
              </div>
            </div>

            {/* Medicine Items in PO */}
            <div className="space-y-3 pt-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-800 uppercase tracking-wider">Order Items</span>
                <button
                  type="button"
                  onClick={() =>
                    setNewPOData({
                      ...newPOData,
                      items: [...newPOData.items, { medicine: 0, requested_quantity: 100, unit_cost: 10.0 }],
                    })
                  }
                  className="text-emerald-700 hover:text-emerald-800 font-bold flex items-center gap-1 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Medicine Item
                </button>
              </div>

              {newPOData.items.map((it, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
                  <div className="sm:col-span-2">
                    <label className="font-bold text-slate-500 block mb-1">Medicine *</label>
                    <select
                      value={it.medicine}
                      onChange={(e) => {
                        const val = Number(e.target.value);
                        setNewPOData({
                          ...newPOData,
                          items: newPOData.items.map((x, i) => (i === idx ? { ...x, medicine: val } : x)),
                        });
                      }}
                      className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 font-bold text-slate-800"
                    >
                      <option value={0}>-- Select Medicine --</option>
                      {medicines.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.generic_name} ({m.strength})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="font-bold text-slate-500 block mb-1">Quantity</label>
                    <input
                      type="number"
                      min={1}
                      value={it.requested_quantity}
                      onChange={(e) => {
                        const val = Number(e.target.value);
                        setNewPOData({
                          ...newPOData,
                          items: newPOData.items.map((x, i) => (i === idx ? { ...x, requested_quantity: val } : x)),
                        });
                      }}
                      className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 font-bold"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-slate-500 block mb-1">Unit Cost (₹)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={it.unit_cost}
                      onChange={(e) => {
                        const val = Number(e.target.value);
                        setNewPOData({
                          ...newPOData,
                          items: newPOData.items.map((x, i) => (i === idx ? { ...x, unit_cost: val } : x)),
                        });
                      }}
                      className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1 font-bold"
                    />
                  </div>
                </div>
              ))}

              <div className="p-3 bg-emerald-50/70 border border-emerald-200 rounded-xl flex justify-between items-center text-xs">
                <span className="font-bold text-emerald-900">Total Purchase Order Estimate:</span>
                <span className="text-base font-black text-emerald-900 font-mono">
                  ₹
                  {newPOData.items
                    .reduce((sum, it) => sum + Number(it.requested_quantity) * Number(it.unit_cost || 0), 0)
                    .toFixed(2)}
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowCreatePOModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer"
              >
                Create Purchase Order
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 5. PO DETAILS & WORKFLOW MODAL */}
      {selectedPOForDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-2xl rounded-2xl border border-slate-200 shadow-2xl overflow-hidden p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <span className="font-mono text-xs font-bold text-blue-700 block">{selectedPOForDetails.po_number}</span>
                <h2 className="text-base font-bold text-slate-900">Purchase Order Details</h2>
              </div>
              <button
                onClick={() => setSelectedPOForDetails(null)}
                className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Vendor</span>
                <strong className="text-slate-900 block mt-0.5">{selectedPOForDetails.vendor_name}</strong>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Status</span>
                <span className="inline-block mt-1 font-bold text-xs">{selectedPOForDetails.status}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Total Amount</span>
                <span className="font-mono font-black text-slate-900 text-sm mt-0.5 block">
                  ₹{Number(selectedPOForDetails.total_amount).toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Order Date</span>
                <span className="font-mono text-slate-700 mt-0.5 block">{formatDateOnly(selectedPOForDetails.order_date)}</span>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Ordered Items</h3>
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Medicine</th>
                      <th className="p-2.5">Ordered</th>
                      <th className="p-2.5">Received</th>
                      <th className="p-2.5">Unit Price</th>
                      <th className="p-2.5 text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {selectedPOForDetails.items?.map((it, i) => (
                      <tr key={i}>
                        <td className="p-2.5 font-bold text-slate-900">{it.medicine_name || `Medicine #${it.medicine}`}</td>
                        <td className="p-2.5 font-mono">{it.ordered_quantity ?? it.requested_quantity ?? 0}</td>
                        <td className="p-2.5 font-mono font-bold text-emerald-800">{it.received_quantity ?? 0}</td>
                        <td className="p-2.5 font-mono">₹{Number(it.unit_price ?? it.unit_cost ?? 0).toFixed(2)}</td>
                        <td className="p-2.5 font-mono font-bold text-right">
                          ₹{Number(it.total_price ?? (it.ordered_quantity || 0) * (it.unit_price || 0)).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-between items-center pt-3 border-t border-slate-100 text-xs">
              {!isReadOnly && selectedPOForDetails.status !== 'CANCELLED' && selectedPOForDetails.status !== 'RECEIVED' && (
                <button
                  onClick={() => handleCancelPO(selectedPOForDetails.id)}
                  className="px-3 py-1.5 text-rose-600 hover:bg-rose-50 font-bold rounded-lg transition cursor-pointer"
                >
                  Cancel PO
                </button>
              )}
              <div className="flex gap-2 ml-auto">
                <button
                  onClick={() => setSelectedPOForDetails(null)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl cursor-pointer"
                >
                  Close
                </button>
                {['ORDERED', 'PARTIALLY_RECEIVED', 'APPROVED'].includes(selectedPOForDetails.status) && !isReadOnly && (
                  <button
                    onClick={() => {
                      const po = selectedPOForDetails;
                      setSelectedPOForDetails(null);
                      openReceivingModal(po);
                    }}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs cursor-pointer inline-flex items-center gap-1.5"
                  >
                    <Truck className="w-3.5 h-3.5" />
                    <span>Receive Stock</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6. VENDOR DETAILS MODAL */}
      {selectedVendorForDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-xl rounded-2xl border border-slate-200 shadow-2xl overflow-hidden p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <span className="font-mono text-xs font-bold text-slate-500 block">
                  {selectedVendorForDetails.vendor_code || `VEND-${selectedVendorForDetails.id}`}
                </span>
                <h2 className="text-base font-bold text-slate-900">
                  {selectedVendorForDetails.vendor_name || selectedVendorForDetails.name}
                </h2>
              </div>
              <button
                onClick={() => setSelectedVendorForDetails(null)}
                className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Contact Person</span>
                <strong className="text-slate-800">{selectedVendorForDetails.contact_person || 'N/A'}</strong>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Phone</span>
                <span className="text-slate-700 font-mono">{selectedVendorForDetails.phone || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Email</span>
                <span className="text-slate-700">{selectedVendorForDetails.email || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">GSTIN</span>
                <span className="text-slate-700 font-mono">{selectedVendorForDetails.gst_number || selectedVendorForDetails.gstin || 'N/A'}</span>
              </div>
              <div className="col-span-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Address</span>
                <span className="text-slate-700">{selectedVendorForDetails.address || 'N/A'}</span>
              </div>
            </div>

            {/* Vendor Purchase History */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Purchase Orders History</h3>
              {loadingVendorHistory ? (
                <p className="text-xs text-slate-400 py-3 text-center">Loading orders...</p>
              ) : vendorHistory.length === 0 ? (
                <p className="text-xs text-slate-400 py-3 text-center bg-slate-50 rounded-xl">
                  No historical purchase orders found for this vendor.
                </p>
              ) : (
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                      <tr>
                        <th className="p-2.5">PO Number</th>
                        <th className="p-2.5">Date</th>
                        <th className="p-2.5">Amount</th>
                        <th className="p-2.5">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {vendorHistory.map((po) => (
                        <tr key={po.id}>
                          <td className="p-2.5 font-mono font-bold text-slate-900">{po.po_number}</td>
                          <td className="p-2.5 font-mono text-slate-500">{formatDateOnly(po.order_date)}</td>
                          <td className="p-2.5 font-mono font-bold">₹{Number(po.total_amount).toFixed(2)}</td>
                          <td className="p-2.5">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100">
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

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <button
                onClick={() => setSelectedVendorForDetails(null)}
                className="px-4 py-2 bg-slate-900 text-white font-bold text-xs rounded-xl cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 7. ADD VENDOR MODAL */}
      {showAddVendorModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleAddVendor}
            className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4"
          >
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-emerald-600" /> Register New Supplier / Vendor
              </h2>
              <button
                type="button"
                onClick={() => setShowAddVendorModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer"
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
                <label className="font-bold text-slate-700 block mb-1">Company / Vendor Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. KSMSCL Supplies"
                  value={newVendorData.name}
                  onChange={(e) => setNewVendorData({ ...newVendorData, name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold"
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
                  placeholder="+91 98765 43210"
                  value={newVendorData.phone}
                  onChange={(e) => setNewVendorData({ ...newVendorData, phone: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Email Address</label>
                <input
                  type="email"
                  placeholder="orders@supplier.in"
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
                  placeholder="Full office or depot address..."
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
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs cursor-pointer"
              >
                Register Vendor
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 8. EDIT VENDOR MODAL */}
      {editingVendor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleSaveEditVendor}
            className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4"
          >
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-blue-600" /> Edit Vendor Details
              </h2>
              <button
                type="button"
                onClick={() => setEditingVendor(null)}
                className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="col-span-2">
                <label className="font-bold text-slate-700 block mb-1">Company / Vendor Name *</label>
                <input
                  type="text"
                  required
                  value={editVendorData.name}
                  onChange={(e) => setEditVendorData({ ...editVendorData, name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold"
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
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-xs cursor-pointer"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 9. ADD MEDICINE MODAL */}
      {showAddMedicineModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleAddMedicine}
            className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4"
          >
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Pill className="w-4 h-4 text-emerald-600" /> Register Drug in Medicine Catalog
              </h2>
              <button
                type="button"
                onClick={() => setShowAddMedicineModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="col-span-2">
                <label className="font-bold text-slate-700 block mb-1">Generic Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Paracetamol"
                  value={newMedicineData.generic_name}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, generic_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Brand Name (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Dolo 650"
                  value={newMedicineData.brand_name}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, brand_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Strength</label>
                <input
                  type="text"
                  placeholder="e.g. 500 mg"
                  value={newMedicineData.strength}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, strength: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Dosage Form</label>
                <select
                  value={newMedicineData.dosage_form}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, dosage_form: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold"
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
                <label className="font-bold text-slate-700 block mb-1">Unit of Measurement</label>
                <input
                  type="text"
                  placeholder="e.g. Tablets"
                  value={newMedicineData.unit}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, unit: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Minimum Stock Threshold</label>
                <input
                  type="number"
                  min={0}
                  value={newMedicineData.minimum_stock}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, minimum_stock: Number(e.target.value) })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-mono"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Reorder Level Threshold</label>
                <input
                  type="number"
                  min={0}
                  value={newMedicineData.reorder_level}
                  onChange={(e) => setNewMedicineData({ ...newMedicineData, reorder_level: Number(e.target.value) })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-mono"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowAddMedicineModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={medicineActionLoading}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs cursor-pointer"
              >
                Register Medicine
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 10. EDIT MEDICINE MODAL */}
      {editingMedicine && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <form
            onSubmit={handleSaveEditMedicine}
            className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden p-6 space-y-4"
          >
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-blue-600" /> Edit Medicine Catalog Entry
              </h2>
              <button
                type="button"
                onClick={() => setEditingMedicine(null)}
                className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="col-span-2">
                <label className="font-bold text-slate-700 block mb-1">Generic Name *</label>
                <input
                  type="text"
                  required
                  value={editMedicineData.generic_name}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, generic_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Brand Name</label>
                <input
                  type="text"
                  value={editMedicineData.brand_name}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, brand_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Strength</label>
                <input
                  type="text"
                  value={editMedicineData.strength}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, strength: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Dosage Form</label>
                <input
                  type="text"
                  value={editMedicineData.dosage_form}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, dosage_form: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Unit</label>
                <input
                  type="text"
                  value={editMedicineData.unit}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, unit: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Minimum Stock</label>
                <input
                  type="number"
                  min={0}
                  value={editMedicineData.minimum_stock}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, minimum_stock: Number(e.target.value) })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-mono"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Reorder Level</label>
                <input
                  type="number"
                  min={0}
                  value={editMedicineData.reorder_level}
                  onChange={(e) => setEditMedicineData({ ...editMedicineData, reorder_level: Number(e.target.value) })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-mono"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingMedicine(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={medicineActionLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-xs cursor-pointer"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
