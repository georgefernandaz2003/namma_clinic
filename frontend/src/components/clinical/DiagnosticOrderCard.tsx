import React from 'react';
import type { DiagnosticTestMaster, DiagnosticResult } from '../../types';
import { TestTube, CheckCircle2 } from 'lucide-react';

interface DiagnosticOrderCardProps {
  orderDiagnostics: boolean;
  setOrderDiagnostics: (val: boolean) => void;
  selectedTestMasterId: number | '';
  setSelectedTestMasterId: (val: number | '') => void;
  diagPriority: 'ROUTINE' | 'URGENT' | 'STAT';
  setDiagPriority: (val: 'ROUTINE' | 'URGENT' | 'STAT') => void;
  diagIndication: string;
  setDiagIndication: (val: string) => void;
  testMasters: DiagnosticTestMaster[];
  existingResults: DiagnosticResult[];
}

export const DiagnosticOrderCard: React.FC<DiagnosticOrderCardProps> = ({
  orderDiagnostics,
  setOrderDiagnostics,
  selectedTestMasterId,
  setSelectedTestMasterId,
  diagPriority,
  setDiagPriority,
  diagIndication,
  setDiagIndication,
  testMasters,
  existingResults
}) => {
  return (
    <section aria-labelledby="lab-orders-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center gap-2">
          <TestTube className="w-4 h-4 text-purple-600" aria-hidden="true" />
          <h2 id="lab-orders-heading" className="text-sm font-bold text-slate-900">
            Laboratory Diagnostic Orders
          </h2>
        </div>
        <label className="flex items-center gap-2 text-xs font-bold text-slate-700 cursor-pointer">
          <input
            type="checkbox"
            checked={orderDiagnostics}
            onChange={(e) => setOrderDiagnostics(e.target.checked)}
            className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 cursor-pointer"
          />
          <span>Order Diagnostic Test</span>
        </label>
      </div>

      {/* Verified results view */}
      {existingResults.length > 0 && (
        <div className="p-3 bg-purple-50/60 rounded-xl border border-purple-200 text-xs space-y-2">
          <span className="font-bold text-purple-900 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-purple-700" aria-hidden="true" />
            Verified Lab Results Available for this Patient:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {existingResults.map((r) => (
              <div key={r.id} className="bg-white p-2 rounded border border-purple-200">
                <div className="font-bold text-slate-900">
                  Result: {r.result_value_text || r.result_value_numeric}
                </div>
                <div className="text-[11px] text-slate-500">
                  Status: <strong className="text-purple-700">{r.status}</strong>
                  {r.reference_range_applied && ` • Ref: ${r.reference_range_applied}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {orderDiagnostics && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
          <div>
            <label htmlFor="lab-test" className="block text-[11px] font-bold text-slate-700 mb-1">
              Select Investigation <span className="text-rose-500">*</span>
            </label>
            <select
              id="lab-test"
              value={selectedTestMasterId}
              onChange={(e) => setSelectedTestMasterId(e.target.value ? Number(e.target.value) : '')}
              required={orderDiagnostics}
              className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
            >
              <option value="">-- Choose Diagnostic Test --</option>
              {testMasters.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.test_code} - {t.test_name} ({t.category})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="diag-priority" className="block text-[11px] font-bold text-slate-700 mb-1">
              Order Priority
            </label>
            <select
              id="diag-priority"
              value={diagPriority}
              onChange={(e) => setDiagPriority(e.target.value as 'ROUTINE' | 'URGENT' | 'STAT')}
              className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
            >
              <option value="ROUTINE">Routine</option>
              <option value="URGENT">Urgent</option>
              <option value="STAT">STAT / Emergency</option>
            </select>
          </div>

          <div>
            <label htmlFor="diag-indication" className="block text-[11px] font-bold text-slate-700 mb-1">
              Clinical Indication
            </label>
            <input
              id="diag-indication"
              type="text"
              value={diagIndication}
              onChange={(e) => setDiagIndication(e.target.value)}
              placeholder="e.g. Check antigen titer for fever"
              className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
            />
          </div>
        </div>
      )}
    </section>
  );
};

export default DiagnosticOrderCard;
