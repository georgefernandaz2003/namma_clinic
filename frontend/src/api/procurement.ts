import apiClient from './client';
import type { PaginatedResponse } from '../types/api';
import type { Vendor, PurchaseOrder, GoodsReceiptNote, MedicineBatch } from '../types';

// ==========================================
// 1. Vendors
// ==========================================
export const getVendors = async (): Promise<Vendor[]> => {
  const res = await apiClient.get<PaginatedResponse<Vendor> | Vendor[]>('v1/procurement/vendors/');
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

// ==========================================
// 2. Purchase Orders
// ==========================================
export interface CreatePurchaseOrderItemPayload {
  medicine: number;
  ordered_quantity: number;
  unit_price: number;
}

export interface CreatePurchaseOrderPayload {
  facility: number;
  vendor: number;
  expected_delivery?: string | null;
  notes?: string;
  items: CreatePurchaseOrderItemPayload[];
}

export const getPurchaseOrders = async (params?: Record<string, string | number>): Promise<PurchaseOrder[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<PurchaseOrder> | PurchaseOrder[]>(`v1/procurement/purchase-orders/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const getPurchaseOrder = async (id: number): Promise<PurchaseOrder> => {
  const res = await apiClient.get<PurchaseOrder>(`v1/procurement/purchase-orders/${id}/`);
  return res.data;
};

export const createPurchaseOrder = async (payload: CreatePurchaseOrderPayload): Promise<PurchaseOrder> => {
  const res = await apiClient.post<PurchaseOrder>('v1/procurement/purchase-orders/', payload);
  return res.data;
};

export const submitPurchaseOrderApproval = async (id: number): Promise<PurchaseOrder> => {
  const res = await apiClient.post<PurchaseOrder>(`v1/procurement/purchase-orders/${id}/submit-approval/`);
  return res.data;
};

export const approvePurchaseOrder = async (id: number): Promise<PurchaseOrder> => {
  const res = await apiClient.post<PurchaseOrder>(`v1/procurement/purchase-orders/${id}/approve/`);
  return res.data;
};

export const placePurchaseOrder = async (id: number): Promise<PurchaseOrder> => {
  const res = await apiClient.post<PurchaseOrder>(`v1/procurement/purchase-orders/${id}/place-order/`);
  return res.data;
};

// ==========================================
// 3. Goods Receipt Notes (GRN)
// ==========================================
export interface CreateGoodsReceiptItemPayload {
  purchase_order_item?: number;
  medicine: number;
  batch_number: string;
  expiry_date: string;
  received_quantity: number;
  accepted_quantity: number;
  rejected_quantity?: number;
  rejection_reason?: string;
  unit_cost?: number;
}

export interface CreateGoodsReceiptPayload {
  facility: number;
  purchase_order: number;
  invoice_number?: string;
  notes?: string;
  items: CreateGoodsReceiptItemPayload[];
}

export const getGoodsReceiptNotes = async (params?: Record<string, string | number>): Promise<GoodsReceiptNote[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<GoodsReceiptNote> | GoodsReceiptNote[]>(`v1/procurement/grn/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const createGoodsReceiptNote = async (payload: CreateGoodsReceiptPayload): Promise<GoodsReceiptNote> => {
  const grnNumber = `GRN-${Date.now().toString().slice(-6)}`;
  const backendPayload = {
    facility_id: payload.facility,
    purchase_order_id: payload.purchase_order,
    grn_number: grnNumber,
    invoice_number: payload.invoice_number,
    notes: payload.notes,
    items_received: payload.items.map(i => ({
      medicine_id: i.medicine,
      batch_number: i.batch_number,
      expiry_date: i.expiry_date,
      unit_cost: i.unit_cost || 10,
      quantity_received: i.received_quantity,
      quantity_accepted: i.accepted_quantity,
      quantity_rejected: i.rejected_quantity || 0,
      rejection_reason: i.rejection_reason || ''
    }))
  };
  const res = await apiClient.post<GoodsReceiptNote>('v1/procurement/grn/', backendPayload);
  return res.data;
};

// ==========================================
// 4. Batch Stock Adjustment
// ==========================================
export interface AdjustBatchPayload {
  physical_count?: number;
  quantity_delta?: number;
  remarks?: string;
}

export const adjustMedicineBatch = async (batchId: number, payload: AdjustBatchPayload): Promise<MedicineBatch> => {
  const res = await apiClient.post<MedicineBatch>(`v1/pharmacy/batches/${batchId}/adjust/`, payload);
  return res.data;
};
