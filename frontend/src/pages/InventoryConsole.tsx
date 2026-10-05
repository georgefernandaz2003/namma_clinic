import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Package,
  ShoppingCart,
  Truck,
  ClipboardCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Search,
  Plus,
  RefreshCw,
  FileText,
  Boxes,
  Layers,
  ShieldCheck,
  ArrowRight,
  History,
  TrendingDown,
  Filter,
  X,
  ChevronDown,
  Building2,
  Calendar,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  getMedicines,
  getMedicineBatches,
  getInventoryLedger,
} from '../api/clinical';
import {
  getVendors,
  getPurchaseOrders,
  getPurchaseOrder,
  createPurchaseOrder,
  submitPurchaseOrderApproval,
  approvePurchaseOrder,
  placePurchaseOrder,
  getGoodsReceiptNotes,
  createGoodsReceiptNote,
  adjustMedicineBatch,
  type CreatePurchaseOrderItemPayload,
  type CreateGoodsReceiptItemPayload
} from '../api/procurement';
import { parseApiError } from '../api/client';
import type {
  MedicineMaster,
  MedicineBatch,
  InventoryLedger,
  Vendor,
  PurchaseOrder,
  GoodsReceiptNote
} from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';

type ConsoleTab = 'OVERVIEW' | 'PURCHASE_ORDERS' | 'GOODS_RECEIPT' | 'RECONCILIATION';

export const InventoryConsole: React.FC = () => {
  const { activeFacility, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Active Tab
  const tabParam = searchParams.get('tab') as ConsoleTab | null;
  const [activeTab, setActiveTab] = useState<ConsoleTab>(tabParam || 'OVERVIEW');

  // Handle Tab Change
  const handleTabChange = (tab: ConsoleTab) => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  // Global Data State
  const [medicines, setMedicines] = useState<MedicineMaster[]>([]);
  const [batches, setBatches] = useState<MedicineBatch[]>([]);
  const [ledgerEntries, setLedgerEntries] = useState<InventoryLedger[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [goodsReceipts, setGoodsReceipts] = useState<GoodsReceiptNote[]>([]);

  // UI State
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Search & Filters
  const [stockSearch, setStockSearch] = useState<string>('');
  const [poFilter, setPoFilter] = useState<string>('ALL');
  const [poSearch, setPoSearch] = useState<string>('');
  const [reconcileSearch, setReconcileSearch] = useState<string>('');

  // Modals
  const [showCreatePOModal, setShowCreatePOModal] = useState<boolean>(false);
  const [showCreateGRNModal, setShowCreateGRNModal] = useState<boolean>(false);
  const [showReconcileModal, setShowReconcileModal] = useState<boolean>(false);
  const [selectedBatchForReconcile, setSelectedBatchForReconcile] = useState<MedicineBatch | null>(null);
  const [selectedPOForDetail, setSelectedPOForDetail] = useState<PurchaseOrder | null>(null);

  // Modal In-Dialog Error States (UI-28A-01)
  const [poModalError, setPoModalError] = useState<string | null>(null);
  const [grnModalError, setGrnModalError] = useState<string | null>(null);
  const [reconcileModalError, setReconcileModalError] = useState<string | null>(null);

  // Form State: Create PO
  const [newPOVendor, setNewPOVendor] = useState<number | ''>('');
  const [newPODeliveryDate, setNewPODeliveryDate] = useState<string>('');
  const [newPONotes, setNewPONotes] = useState<string>('');
  const [newPOItems, setNewPOItems] = useState<CreatePurchaseOrderItemPayload[]>([
    { medicine: 0, ordered_quantity: 100, unit_price: 10.0 }
  ]);
  const [submittingPO, setSubmittingPO] = useState<boolean>(false);

  // Form State: Create GRN
  const [grnPOId, setGrnPOId] = useState<number | ''>('');
  const [grnInvoiceNumber, setGrnInvoiceNumber] = useState<string>('');
  const [grnNotes, setGrnNotes] = useState<string>('');
  const [grnItems, setGrnItems] = useState<CreateGoodsReceiptItemPayload[]>([]);
  const [submittingGRN, setSubmittingGRN] = useState<boolean>(false);

  // Form State: Physical Count Reconciliation
  const [reconcileMode, setReconcileMode] = useState<'COUNT' | 'DELTA'>('COUNT');
  const [reconcilePhysicalCount, setReconcilePhysicalCount] = useState<number | ''>('');
  const [reconcileDelta, setReconcileDelta] = useState<number | ''>('');
  const [reconcileRemarks, setReconcileRemarks] = useState<string>('Physical count reconciliation audit');
  const [submittingReconcile, setSubmittingReconcile] = useState<boolean>(false);

  // Load All Inventory Data
  const loadData = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    else setLoading(true);
    setError(null);

    const facilityId = activeFacility?.id;
    try {
      const [medRes, batchRes, ledgerRes, vendorRes, poRes, grnRes] = await Promise.all([
        getMedicines(),
        getMedicineBatches(facilityId ? { facility: facilityId } : undefined),
        getInventoryLedger(facilityId ? { facility: facilityId } : undefined),
        getVendors(),
        getPurchaseOrders(facilityId ? { facility: facilityId } : undefined),
        getGoodsReceiptNotes(facilityId ? { facility: facilityId } : undefined)
      ]);

      setMedicines(medRes);
      if (medRes.length > 0) {
        setNewPOItems(prev => prev.map(item => item.medicine === 0 ? { ...item, medicine: medRes[0].id } : item));
      }
      setBatches(batchRes);
      setLedgerEntries(ledgerRes);
      setVendors(vendorRes);
      setPurchaseOrders(poRes);
      setGoodsReceipts(grnRes);
    } catch (err: any) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeFacility?.id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Derived KPI Stats
  const totalStockQuantity = useMemo(() => {
    return batches.reduce((sum, b) => sum + (b.available_quantity ?? b.quantity ?? 0), 0);
  }, [batches]);

  const lowStockBatches = useMemo(() => {
    return batches.filter(b => (b.available_quantity ?? b.quantity ?? 0) <= 50 && (b.available_quantity ?? b.quantity ?? 0) > 0);
  }, [batches]);

  const criticalOrExpiringBatches = useMemo(() => {
    return batches.filter(b => b.is_expired || b.expiry_bucket === 'EXPIRED' || b.expiry_bucket === 'CRITICAL' || b.expiry_bucket === 'EXPIRING_SOON');
  }, [batches]);

  const activePurchaseOrdersCount = useMemo(() => {
    return purchaseOrders.filter(p => ['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED'].includes(p.status)).length;
  }, [purchaseOrders]);

  // ==========================================
  // PO Operations
  // ==========================================
  const handleAddItemToPO = () => {
    setNewPOItems(prev => [...prev, { medicine: medicines[0]?.id || 0, ordered_quantity: 50, unit_price: 15.0 }]);
  };

  const handleRemovePOItem = (idx: number) => {
    setNewPOItems(prev => prev.filter((_, i) => i !== idx));
  };

  const handlePOItemChange = (idx: number, field: keyof CreatePurchaseOrderItemPayload, val: any) => {
    setNewPOItems(prev => {
      const copy = [...prev];
      copy[idx] = { ...copy[idx], [field]: val };
      return copy;
    });
  };

  const handleCreatePO = async (e: React.FormEvent) => {
    e.preventDefault();
    setPoModalError(null);
    if (!activeFacility?.id) {
      setPoModalError('Please select an active facility before creating purchase orders.');
      return;
    }
    if (!newPOVendor) {
      setPoModalError('Please select a supplier / vendor.');
      return;
    }
    if (newPOItems.length === 0 || newPOItems.some(i => !i.medicine || i.ordered_quantity <= 0)) {
      setPoModalError('Please specify valid line items with medicine and quantity > 0.');
      return;
    }

    setSubmittingPO(true);
    try {
      await createPurchaseOrder({
        facility: activeFacility.id,
        vendor: Number(newPOVendor),
        expected_delivery: newPODeliveryDate || null,
        notes: newPONotes,
        items: newPOItems
      });
      setSuccessMsg('Purchase Order created successfully in DRAFT status.');
      setShowCreatePOModal(false);
      setPoModalError(null);
      setNewPOItems([{ medicine: medicines[0]?.id || 0, ordered_quantity: 100, unit_price: 10.0 }]);
      setNewPONotes('');
      setNewPODeliveryDate('');
      await loadData(true);
    } catch (err: any) {
      setPoModalError(parseApiError(err));
    } finally {
      setSubmittingPO(false);
    }
  };

  const handleSubmitForApproval = async (poId: number) => {
    setError(null);
    try {
      await submitPurchaseOrderApproval(poId);
      setSuccessMsg(`PO #${poId} submitted for administrative approval.`);
      await loadData(true);
    } catch (err: any) {
      setError(parseApiError(err));
    }
  };

  const handleApprovePO = async (poId: number) => {
    setError(null);
    try {
      await approvePurchaseOrder(poId);
      setSuccessMsg(`PO #${poId} approved successfully.`);
      await loadData(true);
    } catch (err: any) {
      setError(parseApiError(err));
    }
  };

  const handlePlaceOrder = async (poId: number) => {
    setError(null);
    try {
      await placePurchaseOrder(poId);
      setSuccessMsg(`PO #${poId} marked as ORDERED with vendor.`);
      await loadData(true);
    } catch (err: any) {
      setError(parseApiError(err));
    }
  };

  // ==========================================
  // GRN Operations
  // ==========================================
  const handleOpenGRNModal = (preselectedPO?: PurchaseOrder) => {
    setGrnModalError(null);
    if (preselectedPO) {
      setGrnPOId(preselectedPO.id);
      // Pre-fill line items from PO
      const items: CreateGoodsReceiptItemPayload[] = (preselectedPO.items || []).map(item => ({
        purchase_order_item: item.id,
        medicine: item.medicine,
        batch_number: `BATCH-${Date.now().toString().slice(-6)}`,
        expiry_date: new Date(Date.now() + 365 * 24 * 3600 * 1000).toISOString().split('T')[0],
        received_quantity: (item.ordered_quantity || 0) - (item.received_quantity || 0),
        accepted_quantity: (item.ordered_quantity || 0) - (item.received_quantity || 0),
        rejected_quantity: 0,
        rejection_reason: '',
        unit_cost: item.unit_price || item.unit_cost || 10
      }));
      setGrnItems(items.length > 0 ? items : [{
        medicine: medicines[0]?.id || 0,
        batch_number: 'BATCH-001',
        expiry_date: '2027-12-31',
        received_quantity: 100,
        accepted_quantity: 100,
        rejected_quantity: 0,
        unit_cost: 10
      }]);
    } else {
      setGrnPOId('');
      setGrnItems([]);
    }
    setGrnInvoiceNumber(`INV-${Date.now().toString().slice(-6)}`);
    setGrnNotes('Standard shipment intake inspection');
    setShowCreateGRNModal(true);
  };

  const handleGRNPOSelect = (poId: number) => {
    setGrnPOId(poId);
    const found = purchaseOrders.find(p => p.id === poId);
    if (found && found.items) {
      const items: CreateGoodsReceiptItemPayload[] = found.items.map(item => ({
        purchase_order_item: item.id,
        medicine: item.medicine,
        batch_number: `BATCH-${Date.now().toString().slice(-6)}`,
        expiry_date: new Date(Date.now() + 365 * 24 * 3600 * 1000).toISOString().split('T')[0],
        received_quantity: Math.max(1, (item.ordered_quantity || 0) - (item.received_quantity || 0)),
        accepted_quantity: Math.max(1, (item.ordered_quantity || 0) - (item.received_quantity || 0)),
        rejected_quantity: 0,
        rejection_reason: '',
        unit_cost: item.unit_price || item.unit_cost || 10
      }));
      setGrnItems(items);
    }
  };

  const handleCreateGRN = async (e: React.FormEvent) => {
    e.preventDefault();
    setGrnModalError(null);
    if (!activeFacility?.id) {
      setGrnModalError('Please select an active facility.');
      return;
    }
    if (!grnPOId) {
      setGrnModalError('Please select an eligible Purchase Order.');
      return;
    }
    if (grnItems.length === 0 || grnItems.some(i => !i.batch_number || !i.expiry_date || i.received_quantity <= 0)) {
      setGrnModalError('Please provide valid batch details, expiry date, and received quantity for all items.');
      return;
    }

    setSubmittingGRN(true);
    try {
      await createGoodsReceiptNote({
        facility: activeFacility.id,
        purchase_order: Number(grnPOId),
        invoice_number: grnInvoiceNumber,
        notes: grnNotes,
        items: grnItems
      });
      setSuccessMsg('Goods Receipt Note processed! Stock increased and posted to Inventory Ledger.');
      setShowCreateGRNModal(false);
      setGrnModalError(null);
      await loadData(true);
    } catch (err: any) {
      setGrnModalError(parseApiError(err));
    } finally {
      setSubmittingGRN(false);
    }
  };

  // ==========================================
  // Stock Adjustment Operations
  // ==========================================
  const handleOpenReconcileModal = (batch: MedicineBatch) => {
    setSelectedBatchForReconcile(batch);
    setReconcileMode('COUNT');
    setReconcilePhysicalCount(batch.available_quantity ?? batch.quantity ?? 0);
    setReconcileDelta('');
    setReconcileRemarks('Physical inventory count verification audit');
    setReconcileModalError(null);
    setShowReconcileModal(true);
  };

  const handlePerformAdjustment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatchForReconcile) return;

    setReconcileModalError(null);
    setSubmittingReconcile(true);
    try {
      const payload: { physical_count?: number; quantity_delta?: number; remarks: string } = {
        remarks: reconcileRemarks
      };

      if (reconcileMode === 'COUNT') {
        if (reconcilePhysicalCount === '' || Number(reconcilePhysicalCount) < 0) {
          setReconcileModalError('Please provide a valid non-negative physical count.');
          setSubmittingReconcile(false);
          return;
        }
        payload.physical_count = Number(reconcilePhysicalCount);
      } else {
        if (reconcileDelta === '' || Number(reconcileDelta) === 0) {
          setReconcileModalError('Please provide a non-zero adjustment delta.');
          setSubmittingReconcile(false);
          return;
        }
        payload.quantity_delta = Number(reconcileDelta);
      }

      await adjustMedicineBatch(selectedBatchForReconcile.id, payload);
      setSuccessMsg(`Stock reconciled for batch ${selectedBatchForReconcile.batch_number}. Ledger updated.`);
      setShowReconcileModal(false);
      setReconcileModalError(null);
      await loadData(true);
    } catch (err: any) {
      setReconcileModalError(parseApiError(err));
    } finally {
      setSubmittingReconcile(false);
    }
  };

  // Filtered Lists
  const filteredBatches = useMemo(() => {
    return batches.filter(b => {
      const search = stockSearch.toLowerCase();
      const medName = (b.medicine_name || '').toLowerCase();
      const batchNum = (b.batch_number || '').toLowerCase();
      const brand = (b.medicine_brand || '').toLowerCase();
      return medName.includes(search) || batchNum.includes(search) || brand.includes(search);
    });
  }, [batches, stockSearch]);

  const filteredPOs = useMemo(() => {
    return purchaseOrders.filter(p => {
      if (poFilter !== 'ALL' && p.status !== poFilter) return false;
      const search = poSearch.toLowerCase();
      const poNum = (p.po_number || '').toLowerCase();
      const vendorName = (p.vendor_name || '').toLowerCase();
      return poNum.includes(search) || vendorName.includes(search);
    });
  }, [purchaseOrders, poFilter, poSearch]);

  const filteredReconcileBatches = useMemo(() => {
    return batches.filter(b => {
      const search = reconcileSearch.toLowerCase();
      const medName = (b.medicine_name || '').toLowerCase();
      const batchNum = (b.batch_number || '').toLowerCase();
      return medName.includes(search) || batchNum.includes(search);
    });
  }, [batches, reconcileSearch]);

  const eligiblePOsForGRN = useMemo(() => {
    return purchaseOrders.filter(p => ['APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED'].includes(p.status));
  }, [purchaseOrders]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* 1. Header Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-teal-50 text-teal-700 rounded-xl border border-teal-200">
            <Package className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Inventory & Procurement Workstation</h1>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                Phase 27.2 Production
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Facility procurement orders, Goods Receipt Notes (GRN), batch tracking, and physical stock reconciliation.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Facility Scope</div>
            <div className="text-sm font-semibold text-slate-800">
              {activeFacility ? `${activeFacility.facility_name} (${activeFacility.facility_code})` : 'All Assigned Facilities'}
            </div>
          </div>
          <button
            onClick={() => loadData(true)}
            disabled={loading || refreshing}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-300 transition-colors disabled:opacity-50"
            title="Refresh All Records"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Alert Banners */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start justify-between text-rose-800 text-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-600 hover:text-rose-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start justify-between text-emerald-800 text-sm">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 2. Key Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Boxes className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Available Units</div>
            <div className="text-2xl font-bold text-slate-900">{totalStockQuantity.toLocaleString()}</div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Low-Stock Batches</div>
            <div className="text-2xl font-bold text-amber-700">{lowStockBatches.length}</div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-rose-50 text-rose-600 rounded-lg">
            <Calendar className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Critical / Expiring</div>
            <div className="text-2xl font-bold text-rose-700">{criticalOrExpiringBatches.length}</div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <ShoppingCart className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active POs</div>
            <div className="text-2xl font-bold text-indigo-700">{activePurchaseOrdersCount}</div>
          </div>
        </div>
      </div>

      {/* 3. Primary Navigation Tabs */}
      <div className="flex border-b border-slate-200 bg-white px-4 pt-2 rounded-t-xl">
        <button
          onClick={() => handleTabChange('OVERVIEW')}
          className={`flex items-center gap-2 py-3 px-4 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === 'OVERVIEW'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
          }`}
        >
          <Layers className="w-4 h-4" />
          Stock & Audit Ledger
        </button>

        <button
          onClick={() => handleTabChange('PURCHASE_ORDERS')}
          className={`flex items-center gap-2 py-3 px-4 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === 'PURCHASE_ORDERS'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
          }`}
        >
          <ShoppingCart className="w-4 h-4" />
          Purchase Orders ({purchaseOrders.length})
        </button>

        <button
          onClick={() => handleTabChange('GOODS_RECEIPT')}
          className={`flex items-center gap-2 py-3 px-4 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === 'GOODS_RECEIPT'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
          }`}
        >
          <Truck className="w-4 h-4" />
          Goods Receipts / GRN ({goodsReceipts.length})
        </button>

        <button
          onClick={() => handleTabChange('RECONCILIATION')}
          className={`flex items-center gap-2 py-3 px-4 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === 'RECONCILIATION'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
          }`}
        >
          <ClipboardCheck className="w-4 h-4" />
          Physical Reconciliation
        </button>
      </div>

      {/* 4. Tab Body Content */}
      {loading ? (
        <div className="py-20 flex justify-center bg-white rounded-b-xl border border-t-0 border-slate-200">
          <LoadingSpinner size="lg" label="Loading inventory records..." />
        </div>
      ) : (
        <div className="bg-white rounded-b-xl border border-t-0 border-slate-200 p-6 space-y-6">

          {/* TAB 1: STOCK & AUDIT LEDGER */}
          {activeTab === 'OVERVIEW' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="relative flex-1 max-w-md">
                  <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search medicine, batch number, brand..."
                    value={stockSearch}
                    onChange={(e) => setStockSearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
                <div className="text-xs text-slate-500">
                  Showing {filteredBatches.length} active batches across facility inventory
                </div>
              </div>

              {/* Batches Table */}
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-sm text-slate-700">
                  <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Medicine</th>
                      <th className="px-4 py-3">Batch #</th>
                      <th className="px-4 py-3">Expiry Date</th>
                      <th className="px-4 py-3">Available Stock</th>
                      <th className="px-4 py-3">Supplier / Vendor</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {filteredBatches.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                          No matching medicine batches found.
                        </td>
                      </tr>
                    ) : (
                      filteredBatches.map((b) => (
                        <tr key={b.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-medium text-slate-900">
                            <div>{b.medicine_name || `Medicine #${b.medicine}`}</div>
                            {b.medicine_brand && <div className="text-xs text-slate-400">{b.medicine_brand}</div>}
                          </td>
                          <td className="px-4 py-3 font-mono text-xs">{b.batch_number}</td>
                          <td className="px-4 py-3">
                            <span className={b.is_expired ? 'text-rose-600 font-semibold' : 'text-slate-600'}>
                              {b.expiry_date}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="font-semibold text-slate-900">
                              {(b.available_quantity ?? b.quantity).toLocaleString()}
                            </span>
                            {b.medicine_unit && <span className="text-xs text-slate-400 ml-1">{b.medicine_unit}</span>}
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-500">{b.vendor_name || b.supplier || '—'}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                              b.status === 'AVAILABLE' || b.status === 'ACTIVE'
                                ? 'bg-emerald-100 text-emerald-800'
                                : b.status === 'EXPIRING_SOON' || b.status === 'LOW_STOCK'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}>
                              {b.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => handleOpenReconcileModal(b)}
                              className="px-2.5 py-1 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-md border border-teal-200 transition-colors"
                            >
                              Reconcile
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Immutable Inventory Movements Audit Trail */}
              <div className="pt-6 border-t border-slate-200 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <History className="w-5 h-5 text-teal-600" />
                    <h3 className="text-base font-bold text-slate-800">Immutable Inventory Movement Ledger</h3>
                  </div>
                  <span className="text-xs text-slate-400">Ledger entries: {ledgerEntries.length}</span>
                </div>

                <div className="overflow-x-auto border border-slate-200 rounded-lg max-h-80">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead className="bg-slate-50 sticky top-0 font-semibold text-slate-500 border-b border-slate-200">
                      <tr>
                        <th className="px-3 py-2.5">Timestamp</th>
                        <th className="px-3 py-2.5">Transaction Type</th>
                        <th className="px-3 py-2.5">Batch / Medicine</th>
                        <th className="px-3 py-2.5 text-right">Delta</th>
                        <th className="px-3 py-2.5 text-right">Balance After</th>
                        <th className="px-3 py-2.5">Performed By</th>
                        <th className="px-3 py-2.5">Remarks</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {ledgerEntries.slice(0, 50).map((l) => (
                        <tr key={l.id} className="hover:bg-slate-50">
                          <td className="px-3 py-2 whitespace-nowrap text-slate-500 font-mono">
                            {new Date(l.transaction_timestamp).toLocaleString()}
                          </td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                              l.transaction_type === 'PURCHASE_RECEIPT'
                                ? 'bg-blue-100 text-blue-800'
                                : l.transaction_type === 'DISPENSE'
                                ? 'bg-purple-100 text-purple-800'
                                : l.transaction_type === 'AUDIT_CORRECTION'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-slate-100 text-slate-700'
                            }`}>
                              {l.transaction_type}
                            </span>
                          </td>
                          <td className="px-3 py-2">
                            <span className="font-mono text-slate-800">{l.batch_number || `Batch #${l.batch}`}</span>
                            {l.medicine_name && <span className="text-slate-400 ml-1">({l.medicine_name})</span>}
                          </td>
                          <td className={`px-3 py-2 text-right font-bold font-mono ${
                            l.quantity_delta > 0 ? 'text-emerald-600' : 'text-rose-600'
                          }`}>
                            {l.quantity_delta > 0 ? `+${l.quantity_delta}` : l.quantity_delta}
                          </td>
                          <td className="px-3 py-2 text-right font-semibold font-mono text-slate-900">
                            {l.balance_after}
                          </td>
                          <td className="px-3 py-2 text-slate-600">
                            {l.performed_by_name || `Staff #${l.performed_by_staff}`}
                          </td>
                          <td className="px-3 py-2 text-slate-500 italic max-w-xs truncate">
                            {l.remarks || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: PURCHASE ORDERS */}
          {activeTab === 'PURCHASE_ORDERS' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3 flex-1 max-w-lg">
                  <div className="relative flex-1">
                    <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search PO number or vendor..."
                      value={poSearch}
                      onChange={(e) => setPoSearch(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                  <select
                    value={poFilter}
                    onChange={(e) => setPoFilter(e.target.value)}
                    className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none"
                  >
                    <option value="ALL">All Statuses</option>
                    <option value="DRAFT">Draft</option>
                    <option value="PENDING_APPROVAL">Pending Approval</option>
                    <option value="APPROVED">Approved</option>
                    <option value="ORDERED">Ordered</option>
                    <option value="PARTIALLY_RECEIVED">Partially Received</option>
                    <option value="RECEIVED">Received</option>
                  </select>
                </div>

                <button
                  onClick={() => setShowCreatePOModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  New Purchase Order
                </button>
              </div>

              {/* Purchase Orders Table */}
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-sm text-slate-700">
                  <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">PO Number</th>
                      <th className="px-4 py-3">Supplier / Vendor</th>
                      <th className="px-4 py-3">Order Date</th>
                      <th className="px-4 py-3">Total Amount</th>
                      <th className="px-4 py-3">Progress</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Workflow Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {filteredPOs.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                          No purchase orders matching criteria.
                        </td>
                      </tr>
                    ) : (
                      filteredPOs.map((po) => {
                        const totalOrdered = (po.items || []).reduce((acc, i) => acc + (i.ordered_quantity || 0), 0);
                        const totalReceived = (po.items || []).reduce((acc, i) => acc + (i.received_quantity || 0), 0);
                        return (
                          <tr key={po.id} className="hover:bg-slate-50">
                            <td className="px-4 py-3 font-mono font-bold text-slate-900">
                              <button
                                onClick={() => setSelectedPOForDetail(po)}
                                className="text-teal-700 hover:underline"
                              >
                                {po.po_number}
                              </button>
                            </td>
                            <td className="px-4 py-3">
                              <div className="font-medium text-slate-800">{po.vendor_name || `Vendor #${po.vendor}`}</div>
                            </td>
                            <td className="px-4 py-3 text-xs text-slate-500">{po.order_date}</td>
                            <td className="px-4 py-3 font-semibold text-slate-900">
                              ₹{Number(po.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </td>
                            <td className="px-4 py-3 text-xs">
                              <span className="font-semibold">{totalReceived}</span> / {totalOrdered} units
                            </td>
                            <td className="px-4 py-3">
                              <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full ${
                                po.status === 'RECEIVED'
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                  : po.status === 'PARTIALLY_RECEIVED' || po.status === 'ORDERED'
                                  ? 'bg-blue-100 text-blue-800 border border-blue-200'
                                  : po.status === 'APPROVED'
                                  ? 'bg-teal-100 text-teal-800 border border-teal-200'
                                  : po.status === 'PENDING_APPROVAL'
                                  ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                  : 'bg-slate-100 text-slate-700 border border-slate-200'
                              }`}>
                                {po.status}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right space-x-2">
                              {po.status === 'DRAFT' && (
                                <button
                                  onClick={() => handleSubmitForApproval(po.id)}
                                  className="px-2.5 py-1 text-xs font-medium bg-amber-50 text-amber-800 hover:bg-amber-100 rounded border border-amber-300"
                                >
                                  Submit Approval
                                </button>
                              )}
                              {po.status === 'PENDING_APPROVAL' && (
                                <button
                                  onClick={() => handleApprovePO(po.id)}
                                  className="px-2.5 py-1 text-xs font-medium bg-teal-50 text-teal-800 hover:bg-teal-100 rounded border border-teal-300"
                                >
                                  Approve
                                </button>
                              )}
                              {po.status === 'APPROVED' && (
                                <button
                                  onClick={() => handlePlaceOrder(po.id)}
                                  className="px-2.5 py-1 text-xs font-medium bg-blue-50 text-blue-800 hover:bg-blue-100 rounded border border-blue-300"
                                >
                                  Place Order
                                </button>
                              )}
                              {['ORDERED', 'PARTIALLY_RECEIVED'].includes(po.status) && (
                                <button
                                  onClick={() => handleOpenGRNModal(po)}
                                  className="px-2.5 py-1 text-xs font-medium bg-emerald-50 text-emerald-800 hover:bg-emerald-100 rounded border border-emerald-300"
                                >
                                  Receive GRN
                                </button>
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
          )}

          {/* TAB 3: GOODS RECEIPTS / GRN */}
          {activeTab === 'GOODS_RECEIPT' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-800">Goods Receipt Notes (GRN) Registry</h3>
                  <p className="text-xs text-slate-500">
                    Shipment verification and inventory intake ledger. Receiving goods automatically updates batch stock.
                  </p>
                </div>
                <button
                  onClick={() => handleOpenGRNModal()}
                  className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Receive Goods / New GRN
                </button>
              </div>

              {/* GRN Table */}
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-sm text-slate-700">
                  <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">GRN Number</th>
                      <th className="px-4 py-3">Purchase Order</th>
                      <th className="px-4 py-3">Received Date</th>
                      <th className="px-4 py-3">Invoice #</th>
                      <th className="px-4 py-3">Received By</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Line Items</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {goodsReceipts.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                          No Goods Receipt Notes registered for this facility.
                        </td>
                      </tr>
                    ) : (
                      goodsReceipts.map((grn) => (
                        <tr key={grn.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-mono font-bold text-slate-900">{grn.grn_number}</td>
                          <td className="px-4 py-3 font-mono text-teal-700">PO #{grn.purchase_order}</td>
                          <td className="px-4 py-3 text-xs text-slate-500">{grn.received_date}</td>
                          <td className="px-4 py-3 font-mono text-xs">{grn.invoice_number || '—'}</td>
                          <td className="px-4 py-3 text-xs text-slate-600">{grn.received_by_name || `Staff #${grn.received_by}`}</td>
                          <td className="px-4 py-3">
                            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                              {grn.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-600">
                            {grn.items ? `${grn.items.length} items verified` : 'Verified'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: PHYSICAL RECONCILIATION */}
          {activeTab === 'RECONCILIATION' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-base font-bold text-slate-800">Physical Stock Reconciliation Workstation</h3>
                  <p className="text-xs text-slate-500">
                    Conduct physical cycle counts against recorded system stock. Adjustments post immutable AUDIT_CORRECTION records to the Inventory Ledger.
                  </p>
                </div>
                <div className="relative max-w-xs">
                  <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search batch or medicine..."
                    value={reconcileSearch}
                    onChange={(e) => setReconcileSearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Batches Reconciliation Table */}
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-sm text-slate-700">
                  <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Medicine Master</th>
                      <th className="px-4 py-3">Batch Number</th>
                      <th className="px-4 py-3">Expiry Date</th>
                      <th className="px-4 py-3 text-right">System Recorded Stock</th>
                      <th className="px-4 py-3 text-center">Batch Status</th>
                      <th className="px-4 py-3 text-right">Reconciliation Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {filteredReconcileBatches.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                          No batches found for reconciliation.
                        </td>
                      </tr>
                    ) : (
                      filteredReconcileBatches.map((b) => (
                        <tr key={b.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-medium text-slate-900">
                            <div>{b.medicine_name || `Medicine #${b.medicine}`}</div>
                            {b.medicine_brand && <div className="text-xs text-slate-400">{b.medicine_brand}</div>}
                          </td>
                          <td className="px-4 py-3 font-mono text-xs">{b.batch_number}</td>
                          <td className="px-4 py-3 text-xs text-slate-600">{b.expiry_date}</td>
                          <td className="px-4 py-3 text-right font-bold text-slate-900 font-mono text-base">
                            {(b.available_quantity ?? b.quantity).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-100 text-slate-800">
                              {b.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => handleOpenReconcileModal(b)}
                              className="px-3 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm transition-colors"
                            >
                              Audit / Reconcile
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 1: CREATE PURCHASE ORDER */}
      {/* ========================================================================= */}
      {showCreatePOModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-4">
              <div className="flex items-center gap-3">
                <ShoppingCart className="w-6 h-6 text-teal-600" />
                <h3 className="text-lg font-bold text-slate-900">Create Procurement Purchase Order</h3>
              </div>
              <button onClick={() => { setShowCreatePOModal(false); setPoModalError(null); }} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {poModalError && (
              <ErrorAlert message={poModalError} onDismiss={() => setPoModalError(null)} />
            )}

            <form onSubmit={handleCreatePO} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Supplier / Vendor</label>
                  <select
                    value={newPOVendor}
                    onChange={(e) => setNewPOVendor(e.target.value ? Number(e.target.value) : '')}
                    required
                    className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  >
                    <option value="">-- Select Vendor --</option>
                    {vendors.map(v => (
                      <option key={v.id} value={v.id}>
                        {v.vendor_name || v.name} ({v.vendor_code || `ID #${v.id}`})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Expected Delivery Date</label>
                  <input
                    type="date"
                    value={newPODeliveryDate}
                    onChange={(e) => setNewPODeliveryDate(e.target.value)}
                    className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Notes / Instructions</label>
                <input
                  type="text"
                  placeholder="e.g. Urgent stock replenishment for OPD"
                  value={newPONotes}
                  onChange={(e) => setNewPONotes(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              {/* Order Items */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 uppercase">Order Line Items</span>
                  <button
                    type="button"
                    onClick={handleAddItemToPO}
                    className="text-xs font-semibold text-teal-600 hover:text-teal-800 flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Medicine
                  </button>
                </div>

                {newPOItems.map((item, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg grid grid-cols-12 gap-3 items-center">
                    <div className="col-span-6">
                      <label className="block text-[10px] text-slate-500 mb-0.5">Medicine</label>
                      <select
                        value={item.medicine}
                        onChange={(e) => handlePOItemChange(idx, 'medicine', Number(e.target.value))}
                        required
                        className="w-full border border-slate-300 rounded p-1.5 text-xs bg-white"
                      >
                        <option value={0}>-- Select Medicine --</option>
                        {medicines.map(m => (
                          <option key={m.id} value={m.id}>
                            {m.brand_name || m.generic_name} ({m.strength || m.unit})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="col-span-3">
                      <label className="block text-[10px] text-slate-500 mb-0.5">Quantity</label>
                      <input
                        type="number"
                        min="1"
                        value={item.ordered_quantity}
                        onChange={(e) => handlePOItemChange(idx, 'ordered_quantity', Number(e.target.value))}
                        required
                        className="w-full border border-slate-300 rounded p-1.5 text-xs"
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="block text-[10px] text-slate-500 mb-0.5">Unit Price (₹)</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={item.unit_price}
                        onChange={(e) => handlePOItemChange(idx, 'unit_price', Number(e.target.value))}
                        required
                        className="w-full border border-slate-300 rounded p-1.5 text-xs"
                      />
                    </div>

                    <div className="col-span-1 text-right pt-4">
                      {newPOItems.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemovePOItem(idx)}
                          className="text-rose-500 hover:text-rose-700"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => { setShowCreatePOModal(false); setPoModalError(null); }}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingPO}
                  className="px-5 py-2 text-sm font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded-lg shadow-sm disabled:opacity-50"
                >
                  {submittingPO ? 'Creating...' : 'Create Purchase Order'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: RECEIVE GOODS NOTE (GRN) */}
      {/* ========================================================================= */}
      {showCreateGRNModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-3xl w-full p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-4">
              <div className="flex items-center gap-3">
                <Truck className="w-6 h-6 text-teal-600" />
                <h3 className="text-lg font-bold text-slate-900">Goods Receipt Note (GRN) Intake</h3>
              </div>
              <button onClick={() => { setShowCreateGRNModal(false); setGrnModalError(null); }} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {grnModalError && (
              <ErrorAlert message={grnModalError} onDismiss={() => setGrnModalError(null)} />
            )}

            <form onSubmit={handleCreateGRN} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Associated Purchase Order</label>
                  <select
                    value={grnPOId}
                    onChange={(e) => handleGRNPOSelect(Number(e.target.value))}
                    required
                    className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  >
                    <option value="">-- Select Approved / Ordered PO --</option>
                    {eligiblePOsForGRN.map(po => (
                      <option key={po.id} value={po.id}>
                        {po.po_number} ({po.status}) - {po.vendor_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Supplier Invoice Number</label>
                  <input
                    type="text"
                    value={grnInvoiceNumber}
                    onChange={(e) => setGrnInvoiceNumber(e.target.value)}
                    required
                    className="w-full border border-slate-300 rounded-lg p-2 text-sm font-mono focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Receipt Inspection Notes</label>
                <input
                  type="text"
                  value={grnNotes}
                  onChange={(e) => setGrnNotes(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              {/* GRN Items */}
              <div className="space-y-3 pt-2">
                <span className="text-xs font-bold text-slate-700 uppercase">Incoming Shipment Line Items</span>

                {grnItems.length === 0 ? (
                  <div className="p-6 bg-slate-50 border border-dashed border-slate-300 rounded-lg text-center text-xs text-slate-500">
                    Select a Purchase Order above to populate expected line items for receiving.
                  </div>
                ) : (
                  grnItems.map((item, idx) => (
                    <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div>
                          <label className="block text-[10px] text-slate-500 mb-0.5">Medicine</label>
                          <select
                            value={item.medicine}
                            onChange={(e) => {
                              const copy = [...grnItems];
                              copy[idx].medicine = Number(e.target.value);
                              setGrnItems(copy);
                            }}
                            className="w-full border border-slate-300 rounded p-1.5 text-xs bg-white"
                          >
                            {medicines.map(m => (
                              <option key={m.id} value={m.id}>{m.brand_name || m.generic_name}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-500 mb-0.5">Assigned Batch #</label>
                          <input
                            type="text"
                            value={item.batch_number}
                            onChange={(e) => {
                              const copy = [...grnItems];
                              copy[idx].batch_number = e.target.value;
                              setGrnItems(copy);
                            }}
                            required
                            className="w-full border border-slate-300 rounded p-1.5 text-xs font-mono"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-500 mb-0.5">Expiry Date</label>
                          <input
                            type="date"
                            value={item.expiry_date}
                            onChange={(e) => {
                              const copy = [...grnItems];
                              copy[idx].expiry_date = e.target.value;
                              setGrnItems(copy);
                            }}
                            required
                            className="w-full border border-slate-300 rounded p-1.5 text-xs"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <label className="block text-[10px] text-slate-500 mb-0.5">Received Qty</label>
                          <input
                            type="number"
                            min="1"
                            value={item.received_quantity}
                            onChange={(e) => {
                              const copy = [...grnItems];
                              const qty = Number(e.target.value);
                              copy[idx].received_quantity = qty;
                              copy[idx].accepted_quantity = qty;
                              setGrnItems(copy);
                            }}
                            required
                            className="w-full border border-slate-300 rounded p-1.5 text-xs font-semibold"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-500 mb-0.5">Accepted Qty</label>
                          <input
                            type="number"
                            min="0"
                            max={item.received_quantity}
                            value={item.accepted_quantity}
                            onChange={(e) => {
                              const copy = [...grnItems];
                              const accepted = Number(e.target.value);
                              copy[idx].accepted_quantity = accepted;
                              copy[idx].rejected_quantity = Math.max(0, copy[idx].received_quantity - accepted);
                              setGrnItems(copy);
                            }}
                            required
                            className="w-full border border-slate-300 rounded p-1.5 text-xs text-emerald-700 font-semibold"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-500 mb-0.5">Rejected Qty</label>
                          <input
                            type="number"
                            min="0"
                            value={item.rejected_quantity || 0}
                            readOnly
                            className="w-full border border-slate-300 rounded p-1.5 text-xs bg-slate-100 text-rose-600 font-semibold"
                          />
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => { setShowCreateGRNModal(false); setGrnModalError(null); }}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingGRN || grnItems.length === 0}
                  className="px-5 py-2 text-sm font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded-lg shadow-sm disabled:opacity-50"
                >
                  {submittingGRN ? 'Processing Intake...' : 'Submit GRN & Receive Goods'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 3: STOCK AUDIT & RECONCILIATION */}
      {/* ========================================================================= */}
      {showReconcileModal && selectedBatchForReconcile && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 space-y-6">
            <div className="flex items-center justify-between border-b pb-4">
              <div className="flex items-center gap-3">
                <ClipboardCheck className="w-6 h-6 text-teal-600" />
                <h3 className="text-lg font-bold text-slate-900">Physical Count Reconciliation</h3>
              </div>
              <button onClick={() => { setShowReconcileModal(false); setReconcileModalError(null); }} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {reconcileModalError && (
              <ErrorAlert message={reconcileModalError} onDismiss={() => setReconcileModalError(null)} />
            )}

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
              <div className="text-xs text-slate-500 uppercase font-semibold">Target Batch</div>
              <div className="text-base font-bold text-slate-900">
                {selectedBatchForReconcile.medicine_name}
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-600 font-mono">
                <span>Batch: {selectedBatchForReconcile.batch_number}</span>
                <span>Expiry: {selectedBatchForReconcile.expiry_date}</span>
              </div>
              <div className="pt-2 flex items-baseline justify-between border-t border-slate-200">
                <span className="text-xs font-semibold text-slate-600">Current Recorded Stock:</span>
                <span className="text-xl font-bold font-mono text-slate-900">
                  {(selectedBatchForReconcile.available_quantity ?? selectedBatchForReconcile.quantity).toLocaleString()} units
                </span>
              </div>
            </div>

            <form onSubmit={handlePerformAdjustment} className="space-y-4">
              <div className="flex rounded-lg bg-slate-100 p-1">
                <button
                  type="button"
                  onClick={() => setReconcileMode('COUNT')}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                    reconcileMode === 'COUNT' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600'
                  }`}
                >
                  Enter Actual Physical Count
                </button>
                <button
                  type="button"
                  onClick={() => setReconcileMode('DELTA')}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                    reconcileMode === 'DELTA' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600'
                  }`}
                >
                  Enter Adjustment Delta (+ / -)
                </button>
              </div>

              {reconcileMode === 'COUNT' ? (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                    Verified Physical Count
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={reconcilePhysicalCount}
                    onChange={(e) => setReconcilePhysicalCount(e.target.value ? Number(e.target.value) : '')}
                    required
                    className="w-full border border-slate-300 rounded-lg p-2.5 text-lg font-mono font-bold focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                  {reconcilePhysicalCount !== '' && (
                    <div className="mt-1 text-xs text-slate-500">
                      Calculated Delta:{' '}
                      <span className="font-bold font-mono">
                        {Number(reconcilePhysicalCount) - (selectedBatchForReconcile.available_quantity ?? selectedBatchForReconcile.quantity)} units
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                    Adjustment Delta (+ for increase, - for reduction)
                  </label>
                  <input
                    type="number"
                    value={reconcileDelta}
                    onChange={(e) => setReconcileDelta(e.target.value ? Number(e.target.value) : '')}
                    required
                    placeholder="e.g. -5 or +10"
                    className="w-full border border-slate-300 rounded-lg p-2.5 text-lg font-mono font-bold focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
                  Reason & Audit Remarks
                </label>
                <input
                  type="text"
                  value={reconcileRemarks}
                  onChange={(e) => setReconcileRemarks(e.target.value)}
                  required
                  placeholder="e.g. Monthly physical stock audit reconciliation"
                  className="w-full border border-slate-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-teal-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => { setShowReconcileModal(false); setReconcileModalError(null); }}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReconcile}
                  className="px-5 py-2 text-sm font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded-lg shadow-sm disabled:opacity-50"
                >
                  {submittingReconcile ? 'Posting Adjustment...' : 'Commit Reconciliation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 4: PURCHASE ORDER DETAIL VIEW */}
      {/* ========================================================================= */}
      {selectedPOForDetail && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-bold text-slate-900">{selectedPOForDetail.po_number}</h3>
                  <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-slate-100 text-slate-700">
                    {selectedPOForDetail.status}
                  </span>
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Vendor: {selectedPOForDetail.vendor_name || `Vendor #${selectedPOForDetail.vendor}`} | Order Date: {selectedPOForDetail.order_date}
                </div>
              </div>
              <button onClick={() => setSelectedPOForDetail(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-xs text-slate-700">
                  <thead className="bg-slate-50 font-semibold text-slate-500 border-b">
                    <tr>
                      <th className="px-3 py-2">Medicine</th>
                      <th className="px-3 py-2 text-right">Ordered</th>
                      <th className="px-3 py-2 text-right">Received</th>
                      <th className="px-3 py-2 text-right">Unit Price</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(selectedPOForDetail.items || []).map((item, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2 font-medium">{item.medicine_name || `Medicine #${item.medicine}`}</td>
                        <td className="px-3 py-2 text-right font-mono">{item.ordered_quantity}</td>
                        <td className="px-3 py-2 text-right font-mono font-semibold text-teal-700">{item.received_quantity}</td>
                        <td className="px-3 py-2 text-right font-mono">₹{item.unit_price || item.unit_cost || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {selectedPOForDetail.notes && (
                <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-600">
                  <span className="font-semibold text-slate-700">Notes: </span>
                  {selectedPOForDetail.notes}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-4 border-t">
              <button
                type="button"
                onClick={() => setSelectedPOForDetail(null)}
                className="px-4 py-2 text-sm text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default InventoryConsole;
