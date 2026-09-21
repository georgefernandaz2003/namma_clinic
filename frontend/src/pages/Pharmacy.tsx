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
        api.get(`pharmacy/medicines/`).catch(() => ({ data: [] })),
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

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-amber-100 rounded-xl text-amber-700">
            <Pill className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">Pharmacy & Drug Stock Ledger</h1>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">
                FEFO Mandatory Engine
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Controlled FEFO stock dispensing, vendor management, PO goods receiving, and real-time inventory ledger for{' '}
              <strong className="text-slate-700">{activeFacility?.facility_name || 'Facility Store'}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddVendorModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition"
          >
            <Building2 className="w-4 h-4 text-slate-600" />
            <span>+ Add Vendor</span>
          </button>
          <button
            onClick={() => setShowCreatePOModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-amber-50 border border-amber-300 text-amber-900 hover:bg-amber-100 font-bold text-xs rounded-xl transition"
          >
            <ShoppingCart className="w-4 h-4 text-amber-700" />
            <span>+ Create PO</span>
          </button>
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-3 py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xs transition"
          >
            <PackageCheck className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Dynamic Nav Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('DASHBOARD')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'DASHBOARD'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Boxes className="w-3.5 h-3.5" /> Dashboard
        </button>

        <button
          onClick={() => setActiveTab('PRESCRIPTIONS')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'PRESCRIPTIONS'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <ClipboardList className="w-3.5 h-3.5" /> Prescriptions Queue ({prescriptions.length})
        </button>

        <button
          onClick={() => setActiveTab('INVENTORY')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'INVENTORY'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Pill className="w-3.5 h-3.5" /> Inventory Ledger ({medicines.length})
        </button>

        <button
          onClick={() => setActiveTab('BATCHES')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'BATCHES'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Layers className="w-3.5 h-3.5" /> Batches ({batches.length})
        </button>

        <button
          onClick={() => setActiveTab('TRANSACTIONS')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'TRANSACTIONS'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <History className="w-3.5 h-3.5" /> Stock Transactions ({transactions.length})
        </button>

        <button
          onClick={() => setActiveTab('VENDORS')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'VENDORS'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" /> Vendors ({vendors.length})
        </button>

        <button
          onClick={() => setActiveTab('PURCHASE_ORDERS')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'PURCHASE_ORDERS'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Truck className="w-3.5 h-3.5" /> Purchase Orders ({purchaseOrders.length})
        </button>

        <button
          onClick={() => setActiveTab('ALERTS')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'ALERTS'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-red-300" /> Alerts ({alerts.length})
        </button>

        <button
          onClick={() => setActiveTab('REPORTS')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'REPORTS'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <FileSpreadsheet className="w-3.5 h-3.5" /> Reports & Analytics
        </button>
      </div>

      {/* TAB 1: DASHBOARD */}
      {activeTab === 'DASHBOARD' && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-4">
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Total Stock Qty</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-slate-900">{kpis?.total_available_stock ?? 0}</span>
                <Pill className="w-5 h-5 text-amber-600" />
              </div>
              <span className="text-[10px] text-slate-400 block">{kpis?.total_medicines ?? 0} EDL Medicines</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-amber-200 shadow-xs space-y-1">
              <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">Low Stock Alert</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-amber-800">{kpis?.low_stock_count ?? 0}</span>
                <AlertTriangle className="w-5 h-5 text-amber-600" />
              </div>
              <span className="text-[10px] text-amber-600 block">{kpis?.out_of_stock_count ?? 0} Out of Stock</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-red-200 shadow-xs space-y-1">
              <span className="text-[11px] font-bold text-red-700 uppercase tracking-wider block">Expiring Soon</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-red-800">{kpis?.expiring_soon_count ?? 0}</span>
                <Clock className="w-5 h-5 text-red-600" />
              </div>
              <span className="text-[10px] text-red-600 block">{kpis?.expired_count ?? 0} Expired Batches</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-emerald-200 shadow-xs space-y-1">
              <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">Dispensed Today</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-emerald-800">{kpis?.dispensed_today_count ?? 0}</span>
                <PackageCheck className="w-5 h-5 text-emerald-600" />
              </div>
              <span className="text-[10px] text-emerald-600 block">{kpis?.pending_prescriptions_count ?? 0} Rx Pending</span>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-blue-200 shadow-xs space-y-1">
              <span className="text-[11px] font-bold text-blue-700 uppercase tracking-wider block">Pending POs</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-blue-800">{kpis?.pending_purchase_orders_count ?? 0}</span>
                <Truck className="w-5 h-5 text-blue-600" />
              </div>
              <span className="text-[10px] text-blue-600 block">{kpis?.total_vendors_count ?? 0} Registered Vendors</span>
            </div>
          </div>

          {/* Callout Banners */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="bg-gradient-to-r from-amber-900 via-yellow-900 to-slate-900 p-4 rounded-2xl text-white space-y-1 shadow-md">
              <div className="flex items-center gap-2 font-black uppercase tracking-wider text-amber-400 text-[11px]">
                <ShieldCheck className="w-4 h-4" />
                <span>Government FEFO Dispensing Mandate</span>
              </div>
              <p className="text-amber-100 font-medium leading-relaxed text-[11px]">
                &ldquo;The Government guidelines explicitly require near-expiry medicines to be dispensed first and maintain drug stock/issue/dispense/expiry records.&rdquo;
              </p>
            </div>

            <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 p-4 rounded-2xl text-white space-y-1 shadow-md">
              <div className="flex items-center gap-2 font-black uppercase tracking-wider text-emerald-400 text-[11px]">
                <TrendingDown className="w-4 h-4" />
                <span>High Impact Business Value</span>
              </div>
              <p className="text-emerald-100 font-bold leading-relaxed text-xs">
                Less Expiry <span className="text-emerald-300">→</span> Less Wastage <span className="text-emerald-300">→</span> Better Stock Availability <span className="text-emerald-300">→</span> Optimized Procurement Planning
              </p>
            </div>
          </div>

          {/* Recent Alerts & FEFO Matrix Preview */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Realtime Stock Alerts */}
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" /> Real-time Pharmacy Stock Alerts
                </h3>
                <button onClick={() => setActiveTab('ALERTS')} className="text-xs text-amber-700 font-bold hover:underline">
                  View All ({alerts.length})
                </button>
              </div>

              {alerts.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-4 text-center">No active inventory warnings for this facility.</p>
              ) : (
                <div className="space-y-2">
                  {alerts.slice(0, 4).map((alt) => (
                    <div
                      key={alt.id}
                      className={`p-3 rounded-xl border flex items-start justify-between ${
                        alt.severity === 'CRITICAL'
                          ? 'bg-red-50 border-red-200 text-red-900'
                          : alt.severity === 'HIGH'
                          ? 'bg-amber-50 border-amber-200 text-amber-900'
                          : 'bg-blue-50 border-blue-200 text-blue-900'
                      }`}
                    >
                      <div className="space-y-0.5">
                        <span className="font-bold text-xs flex items-center gap-1.5">
                          <AlertCircle className="w-3.5 h-3.5" />
                          {alt.title}
                        </span>
                        <p className="text-[11px] opacity-80">{alt.description}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider bg-white/80 border border-current">
                        {alt.severity}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* FEFO Matrix Quick Summary */}
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-4 h-4 text-amber-600" /> Active Batches FEFO Order
                </h3>
                <button onClick={() => setActiveTab('BATCHES')} className="text-xs text-amber-700 font-bold hover:underline">
                  Manage Batches
                </button>
              </div>

              <div className="space-y-2">
                {Object.keys(groupedBatches).slice(0, 3).map((medName) => {
                  const medBatches = groupedBatches[medName];
                  const earliest = medBatches[0];

                  return (
                    <div key={medName} className="p-3 rounded-xl border border-slate-100 bg-slate-50 space-y-1.5">
                      <div className="flex justify-between items-center text-xs">
                        <strong className="text-slate-900 font-bold">{medName}</strong>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {medBatches.reduce((s, b) => s + b.quantity, 0)} Units Available
                        </span>
                      </div>

                      {earliest && (
                        <div className="flex justify-between items-center text-[11px] bg-white p-2 rounded-lg border border-amber-300">
                          <span className="font-mono font-bold text-amber-900">🎯 FEFO Target: {earliest.batch_number}</span>
                          <span className="text-[10px] font-bold text-red-600">Expires: {earliest.expiry_date}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PRESCRIPTIONS QUEUE */}
      {activeTab === 'PRESCRIPTIONS' && (
        <div className="space-y-4">
          {/* Controls */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search patient or Rx ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Status Filter:</span>
              <select
                value={prescriptionStatusFilter}
                onChange={(e) => setPrescriptionStatusFilter(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-700"
              >
                <option value="ALL">All Statuses</option>
                <option value="PENDING">PENDING</option>
                <option value="PARTIALLY_DISPENSED">PARTIALLY DISPENSED</option>
                <option value="DISPENSED">DISPENSED</option>
              </select>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">Rx ID</th>
                    <th className="p-4">Patient Name</th>
                    <th className="p-4">Doctor</th>
                    <th className="p-4">Prescribed Items</th>
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
                      String(p.id).includes(searchQuery);
                    const matchStatus =
                      prescriptionStatusFilter === 'ALL' ||
                      (prescriptionStatusFilter === 'PENDING'
                        ? p.status === 'PENDING' || p.status === 'ACTIVE'
                        : p.status === prescriptionStatusFilter);
                    return matchSearch && matchStatus;
                  }).length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-400 font-medium">
                        No prescriptions found matching search criteria.
                      </td>
                    </tr>
                  ) : (
                    prescriptions
                      .filter((p) => {
                        const matchSearch =
                          !searchQuery ||
                          p.patient_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          String(p.id).includes(searchQuery);
                        const matchStatus =
                          prescriptionStatusFilter === 'ALL' ||
                          (prescriptionStatusFilter === 'PENDING'
                            ? p.status === 'PENDING' || p.status === 'ACTIVE'
                            : p.status === prescriptionStatusFilter);
                        return matchSearch && matchStatus;
                      })
                      .map((p) => (
                        <tr key={p.id} className="hover:bg-slate-50/80 transition">
                          <td className="p-4 font-mono font-bold text-amber-700">
                            <div>#RX-{String(p.id).padStart(4, '0')}</div>
                            {(p as any).token_number && (
                              <span className="inline-block mt-1 px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 text-[10px] font-mono font-bold border border-emerald-200">
                                Token #{(p as any).token_number}
                              </span>
                            )}
                          </td>
                          <td className="p-4 font-bold text-slate-900">{p.patient_name}</td>
                          <td className="p-4 text-slate-600">{p.doctor_name || 'Staff Doctor'}</td>
                          <td className="p-4 space-y-1">
                            {p.items?.map((item, i) => (
                              <div key={i} className="text-slate-800 text-[11px] flex items-center justify-between gap-2">
                                <span>
                                  <strong>{item.medicine_name}</strong> - {item.dosage} ({item.quantity} units)
                                </span>
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[9px] font-black ${
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
                            <span className="px-2.5 py-1 rounded bg-amber-50 text-amber-900 border border-amber-200 font-mono text-[10px] font-bold block">
                              🎯 FEFO Engine Auto-Selection Target
                            </span>
                          </td>
                          <td className="p-4">
                            <span
                              className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                                p.status === 'DISPENSED'
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                  : p.status === 'PARTIALLY_DISPENSED'
                                  ? 'bg-blue-100 text-blue-800 border border-blue-200'
                                  : 'bg-amber-100 text-amber-900 border border-amber-200'
                              }`}
                            >
                              {p.status}
                            </span>
                          </td>
                          <td className="p-4">
                            {p.status !== 'DISPENSED' ? (
                              <button
                                onClick={() => openDispenseModal(p)}
                                className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition"
                              >
                                <PackageCheck className="w-3.5 h-3.5" /> Controlled Dispense
                              </button>
                            ) : (
                              <button
                                onClick={() => navigate(`/patients/${p.patient}`)}
                                className="text-emerald-700 font-bold text-[11px] hover:underline"
                              >
                                Dispensed & Logged
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
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Essential Drug List (EDL) Master Inventory Ledger
            </h2>
            <span className="text-xs text-slate-500">{medicines.length} Medicines Registered</span>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">Drug Code</th>
                    <th className="p-4">Generic Name</th>
                    <th className="p-4">Brand Name</th>
                    <th className="p-4">Category</th>
                    <th className="p-4">Form & Strength</th>
                    <th className="p-4">Min Stock / Reorder</th>
                    <th className="p-4">Available Qty</th>
                    <th className="p-4">Stock Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {medicines.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-50 transition">
                      <td className="p-4 font-mono font-bold text-slate-600">{m.code}</td>
                      <td className="p-4 font-bold text-slate-900">{m.generic_name}</td>
                      <td className="p-4 text-slate-600">{m.brand_name || '-'}</td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                          {m.category}
                        </span>
                      </td>
                      <td className="p-4 text-slate-600">
                        {m.dosage_form} ({m.strength})
                      </td>
                      <td className="p-4 font-mono text-slate-600">
                        Min: {m.minimum_stock} | Reorder: {m.reorder_level}
                      </td>
                      <td className="p-4 font-mono font-bold text-slate-900">
                        {m.total_available_stock ?? 0} {m.unit}s
                      </td>
                      <td className="p-4">
                        <span
                          className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                            m.stock_status === 'OUT_OF_STOCK'
                              ? 'bg-red-100 text-red-800 border border-red-200'
                              : m.stock_status === 'LOW_STOCK'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          }`}
                        >
                          {m.stock_status || 'NORMAL'}
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
                className="px-3.5 py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition self-start md:self-auto"
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
                className="px-3.5 py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition self-start md:self-auto"
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
                    {reportSummary?.stock_valuation.total_batches ?? 0}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-500">Total Stock Quantity:</span>
                  <span className="font-bold text-slate-900 font-mono">
                    {reportSummary?.stock_valuation.total_quantity ?? 0} Units
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm pt-2 border-t border-slate-100">
                  <span className="font-bold text-slate-700">Total Stock Valuation:</span>
                  <span className="font-black text-emerald-700 font-mono text-base">
                    ₹{Number(reportSummary?.stock_valuation.total_value ?? 0).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2">
                Top Consumed Essential Medicines
              </h3>
              <div className="space-y-2">
                {reportSummary?.consumption_summary.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No consumption records available.</p>
                ) : (
                  reportSummary?.consumption_summary.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center p-2 rounded-xl bg-slate-50 text-xs">
                      <div>
                        <strong className="text-slate-900 font-bold block">{item.batch__medicine__generic_name}</strong>
                        <span className="text-[10px] text-slate-400">{item.batch__medicine__brand_name}</span>
                      </div>
                      <span className="font-mono font-bold text-amber-800 bg-amber-100 px-2.5 py-0.5 rounded">
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
    </div>
  );
};
