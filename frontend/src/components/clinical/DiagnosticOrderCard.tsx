import React from 'react';
import type { DiagnosticTestMaster, DiagnosticResult, DiagnosticOrder } from '../../types';
import { TestTube, CheckCircle2, Clock, Plus, Trash2, Lock, AlertCircle } from 'lucide-react';

export interface DiagnosticOrderCardProps {
  orderDiagnostics: boolean;
  setOrderDiagnostics: (val: boolean) => void;
  selectedTestMasterId: number | '';
  setSelectedTestMasterId: (val: number | '') => void;
  selectedTestMasterIds?: number[];
  setSelectedTestMasterIds?: (ids: number[]) => void;
  diagPriority: 'ROUTINE' | 'URGENT' | 'STAT';
  setDiagPriority: (val: 'ROUTINE' | 'URGENT' | 'STAT') => void;
  diagIndication: string;
  setDiagIndication: (val: string) => void;
  testMasters: DiagnosticTestMaster[];
  existingOrders?: DiagnosticOrder[];
  existingResults: DiagnosticResult[];
  hasPendingLabOrders?: boolean;
  allLabOrdersCompleted?: boolean;
}

export const DiagnosticOrderCard: React.FC<DiagnosticOrderCardProps> = ({
  orderDiagnostics,
  setOrderDiagnostics,
  selectedTestMasterId,
  setSelectedTestMasterId,
  selectedTestMasterIds = [],
  setSelectedTestMasterIds,
  diagPriority,
  setDiagPriority,
  diagIndication,
  setDiagIndication,
  testMasters,
  existingOrders = [],
  existingResults,
  hasPendingLabOrders = false,
  allLabOrdersCompleted = false
}) => {
  const handleAddTest = () => {
    if (!selectedTestMasterId || !setSelectedTestMasterIds) return;
    const numId = Number(selectedTestMasterId);
    if (!selectedTestMasterIds.includes(numId)) {
      setSelectedTestMasterIds([...selectedTestMasterIds, numId]);
    }
    setSelectedTestMasterId('');
  };

  const handleRemoveTest = (idToRemove: number) => {
    if (!setSelectedTestMasterIds) return;
    setSelectedTestMasterIds(selectedTestMasterIds.filter((id) => id !== idToRemove));
  };

  // Find added test master objects for rendering chips
  const addedTestObjects = testMasters.filter((tm) => selectedTestMasterIds.includes(tm.id));

  return (
    <section aria-labelledby="lab-orders-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
      {/* Header with Title and State-Aware Status Indicators */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-50 rounded-xl text-purple-700">
            <TestTube className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 id="lab-orders-heading" className="text-sm font-bold text-slate-900 flex items-center gap-2">
              Laboratory Diagnostic Orders
            </h2>
            <p className="text-[11px] text-slate-500">
              Manage clinical lab requisitions, test accession, and verified pathology results.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Small status indicator near the lab section */}
          {hasPendingLabOrders && (
            <span
              id="lab-status-badge"
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300 shadow-2xs"
            >
              <Clock className="w-3.5 h-3.5 text-amber-600 animate-spin" aria-hidden="true" />
              <span>Lab Ordered — Awaiting Results</span>
            </span>
          )}

          {allLabOrdersCompleted && (
            <span
              id="lab-status-badge"
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-300 shadow-2xs"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
              <span>Lab Results Available — Review & Complete</span>
            </span>
          )}

          <label className="flex items-center gap-2 text-xs font-bold text-slate-700 cursor-pointer select-none ml-2">
            <input
              type="checkbox"
              id="order-diagnostics-checkbox"
              checked={orderDiagnostics}
              onChange={(e) => setOrderDiagnostics(e.target.checked)}
              className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 cursor-pointer"
            />
            <span>Order Diagnostic Test</span>
          </label>
        </div>
      </div>

      {/* Existing Orders Information (Pending or Verified) */}
      {existingOrders.length > 0 && (
        <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2">
          <div className="flex items-center justify-between text-slate-700 font-bold">
            <span className="flex items-center gap-1.5">
              <TestTube className="w-3.5 h-3.5 text-purple-600" />
              Active Lab Orders for Encounter ({existingOrders.length}):
            </span>
            <span className="text-[11px] text-slate-500 font-mono">
              Encounter Linked
            </span>
          </div>

          <div className="space-y-2">
            {existingOrders.map((ord) => (
              <div key={ord.id} className="p-2.5 bg-white rounded-lg border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="font-bold text-slate-900 font-mono flex items-center gap-2">
                    <span>Order #{ord.order_number}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      ord.status === 'VERIFIED'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : 'bg-amber-100 text-amber-800 border border-amber-200'
                    }`}>
                      {ord.status === 'VERIFIED' ? 'RESULTS VERIFIED' : ord.status}
                    </span>
                  </div>
                  {ord.clinical_indication && (
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Indication: {ord.clinical_indication}
                    </div>
                  )}
                  {ord.test_requests && ord.test_requests.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {ord.test_requests.map((tr) => (
                        <span key={tr.id} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-mono border border-slate-200 flex items-center gap-1">
                          <strong>{tr.test_code || `TR-${tr.id}`}</strong>: {tr.test_master_name || 'Investigation'}
                          <span className={`ml-1 font-bold ${tr.status === 'COMPLETED' ? 'text-emerald-700' : 'text-amber-700'}`}>
                            [{tr.diagnostic_result?.status || tr.status}]
                          </span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="text-right text-[11px] text-slate-500 font-mono shrink-0">
                  Priority: <strong>{ord.priority}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Authoritative Lab Results (Doctor Clinical Review Context) */}
      {existingResults.length > 0 && (
        <div id="lab-results-review-section" className="p-4 bg-purple-50/70 rounded-xl border border-purple-200 text-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-purple-950 flex items-center gap-1.5 text-sm">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />
              Verified Laboratory Results (Clinical Review Context):
            </span>
            <span className="text-[11px] text-purple-700 font-mono flex items-center gap-1 bg-purple-100 px-2 py-0.5 rounded border border-purple-200">
              <Lock className="w-3 h-3" /> Read-Only EMR
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {existingResults.map((r) => (
              <div key={r.id} className="bg-white p-3 rounded-xl border border-purple-200 shadow-2xs space-y-2">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <div className="font-bold text-slate-900">
                    {r.test_name ? (
                      <span>{r.test_name} <span className="text-slate-400 font-mono font-normal">({r.test_code})</span></span>
                    ) : (
                      <span>Test Request #{r.test_request}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5">
                    {r.is_abnormal && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                        ABNORMAL
                      </span>
                    )}
                    {r.is_critical_panic && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-100 text-rose-800 border border-rose-300 animate-pulse">
                        CRITICAL
                      </span>
                    )}
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      {r.status}
                    </span>
                  </div>
                </div>

                <div className="flex items-baseline justify-between">
                  <div className="text-base font-bold text-slate-900 font-mono">
                    {r.result_value_text || r.result_value_numeric}
                    {r.default_unit && <span className="text-xs font-normal text-slate-500 ml-1">{r.default_unit}</span>}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {r.reference_range_applied ? `Reference: ${r.reference_range_applied}` : 'Standard reference range'}
                  </div>
                </div>

                {r.verified_at && (
                  <div className="text-[10px] text-slate-500 font-mono border-t border-slate-50 pt-1.5 flex justify-between">
                    <span>Verified: {new Date(r.verified_at).toLocaleDateString()} {new Date(r.verified_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    <span className="text-emerald-700 font-bold">Authorized</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lab Order Input Section */}
      {orderDiagnostics && (
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
          <div className="text-xs font-bold text-slate-800 flex items-center justify-between">
            <span>New Laboratory Requisition</span>
            <span className="text-[11px] text-slate-500 font-normal">Add one or more investigations to this order</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
            <div className="sm:col-span-6">
              <label htmlFor="lab-test" className="block text-[11px] font-bold text-slate-700 mb-1">
                Investigation Master <span className="text-rose-500">*</span>
              </label>
              <div className="flex gap-2">
                <select
                  id="lab-test"
                  value={selectedTestMasterId}
                  onChange={(e) => setSelectedTestMasterId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600 font-medium"
                >
                  <option value="">-- Choose Diagnostic Test --</option>
                  {testMasters.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.test_code} - {t.test_name} ({t.category})
                    </option>
                  ))}
                </select>
                {setSelectedTestMasterIds && (
                  <button
                    type="button"
                    onClick={handleAddTest}
                    disabled={!selectedTestMasterId}
                    className="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-bold inline-flex items-center gap-1 transition disabled:opacity-40 cursor-pointer shrink-0"
                    title="Add test to investigation list"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add</span>
                  </button>
                )}
              </div>
            </div>

            <div className="sm:col-span-3">
              <label htmlFor="diag-priority" className="block text-[11px] font-bold text-slate-700 mb-1">
                Order Priority
              </label>
              <select
                id="diag-priority"
                value={diagPriority}
                onChange={(e) => setDiagPriority(e.target.value as 'ROUTINE' | 'URGENT' | 'STAT')}
                className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600 font-medium"
              >
                <option value="ROUTINE">Routine</option>
                <option value="URGENT">Urgent</option>
                <option value="STAT">STAT / Emergency</option>
              </select>
            </div>

            <div className="sm:col-span-3">
              <label htmlFor="diag-indication" className="block text-[11px] font-bold text-slate-700 mb-1">
                Clinical Indication
              </label>
              <input
                id="diag-indication"
                type="text"
                value={diagIndication}
                onChange={(e) => setDiagIndication(e.target.value)}
                placeholder="e.g. Fever workup, CBC"
                className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
              />
            </div>
          </div>

          {/* List of Added Multi-Investigations */}
          {addedTestObjects.length > 0 && (
            <div className="pt-2 border-t border-slate-200">
              <span className="text-[11px] font-bold text-slate-700 block mb-1.5">
                Investigations Selected for Requisition ({addedTestObjects.length}):
              </span>
              <div className="flex flex-wrap gap-2">
                {addedTestObjects.map((tm) => (
                  <span
                    key={tm.id}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-purple-100 text-purple-900 border border-purple-200"
                  >
                    <span className="font-mono font-bold text-purple-800">{tm.test_code}</span>
                    <span>- {tm.test_name}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveTest(tm.id)}
                      className="text-purple-600 hover:text-rose-600 p-0.5 rounded transition cursor-pointer"
                      title="Remove investigation"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
};

export default DiagnosticOrderCard;

