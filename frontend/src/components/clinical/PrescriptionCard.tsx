import React, { useState } from 'react';
import type { MedicineMaster } from '../../types';
import { Pill, Trash2 } from 'lucide-react';

export interface RxItemInput {
  medicine_id: number;
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration_days: number;
  quantity: number;
}

interface PrescriptionCardProps {
  orderPrescription: boolean;
  setOrderPrescription: (val: boolean) => void;
  prescriptionNotes: string;
  setPrescriptionNotes: React.Dispatch<React.SetStateAction<string>>;
  selectedMedicineId: number | '';
  setSelectedMedicineId: (val: number | '') => void;
  dosageInstructions: string;
  setDosageInstructions: (val: string) => void;
  medicines: MedicineMaster[];
  prescriptionItems?: RxItemInput[];
  setPrescriptionItems?: React.Dispatch<React.SetStateAction<RxItemInput[]>>;
}

export const PrescriptionCard: React.FC<PrescriptionCardProps> = ({
  orderPrescription,
  setOrderPrescription,
  prescriptionNotes,
  setPrescriptionNotes,
  selectedMedicineId,
  setSelectedMedicineId,
  dosageInstructions,
  setDosageInstructions,
  medicines,
  prescriptionItems = [],
  setPrescriptionItems
}) => {
  const [itemQuantity, setItemQuantity] = useState<number>(10);
  const [durationDays, setDurationDays] = useState<number>(3);

  const handleAddMedicine = () => {
    if (!selectedMedicineId) return;
    const med = medicines.find((m) => m.id === Number(selectedMedicineId));
    if (!med) return;

    const medDetail = med.strength || med.dosage_form || '';
    const fullName = `${med.generic_name}${medDetail ? ` (${medDetail})` : ''}`;
    const line = `${fullName}: ${dosageInstructions} (Qty: ${itemQuantity})`;

    if (setPrescriptionItems) {
      setPrescriptionItems((prev) => [
        ...prev,
        {
          medicine_id: med.id,
          medicine_name: fullName,
          dosage: dosageInstructions,
          frequency: 'TDS',
          duration_days: durationDays || 3,
          quantity: itemQuantity || 10
        }
      ]);
    }

    setPrescriptionNotes((prev) => (prev ? `${prev}\n• ${line}` : `• ${line}`));
    setSelectedMedicineId('');
  };

  const handleRemoveItem = (index: number) => {
    if (setPrescriptionItems) {
      setPrescriptionItems((prev) => prev.filter((_, i) => i !== index));
    }
  };

  return (
    <section aria-labelledby="prescription-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center gap-2">
          <Pill className="w-4 h-4 text-emerald-600" aria-hidden="true" />
          <h2 id="prescription-heading" className="text-sm font-bold text-slate-900">
            Prescription & Medication Order
          </h2>
        </div>
        <label className="flex items-center gap-2 text-xs font-bold text-slate-700 cursor-pointer">
          <input
            type="checkbox"
            id="prescribe-medications-checkbox"
            checked={orderPrescription}
            onChange={(e) => setOrderPrescription(e.target.checked)}
            className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 cursor-pointer"
          />
          <span>Issue Prescription</span>
        </label>
      </div>

      {orderPrescription && (
        <div className="space-y-3">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 grid grid-cols-1 sm:grid-cols-12 gap-2 items-end">
            <div className="sm:col-span-4">
              <label htmlFor="med-select" className="block text-[11px] font-bold text-slate-700 mb-1">
                Select Formulary Medicine
              </label>
              <select
                id="med-select"
                value={selectedMedicineId}
                onChange={(e) => setSelectedMedicineId(e.target.value ? Number(e.target.value) : '')}
                className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
              >
                <option value="">-- Choose Medicine --</option>
                {medicines.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.generic_name} ({m.strength || m.dosage_form || ''})
                  </option>
                ))}
              </select>
            </div>

            <div className="sm:col-span-4">
              <label htmlFor="dosage-inst" className="block text-[11px] font-bold text-slate-700 mb-1">
                Dosage & Directions
              </label>
              <input
                id="dosage-inst"
                type="text"
                value={dosageInstructions}
                onChange={(e) => setDosageInstructions(e.target.value)}
                placeholder="e.g. 1 tab thrice daily after meals"
                className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
              />
            </div>

            <div className="sm:col-span-2">
              <label htmlFor="med-qty" className="block text-[11px] font-bold text-slate-700 mb-1">
                Prescribe Qty
              </label>
              <input
                id="med-qty"
                type="number"
                min={1}
                value={itemQuantity}
                onChange={(e) => setItemQuantity(Math.max(1, Number(e.target.value)))}
                className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg font-bold text-slate-800 focus:outline-none focus:border-emerald-600"
              />
            </div>

            <div className="sm:col-span-2">
              <button
                type="button"
                onClick={handleAddMedicine}
                disabled={!selectedMedicineId}
                className="w-full py-2 bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs rounded-lg transition disabled:opacity-50 cursor-pointer"
              >
                + Add Item
              </button>
            </div>
          </div>

          {/* Structured Prescribed Items List */}
          {prescriptionItems.length > 0 && (
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
              <div className="bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700 flex justify-between items-center">
                <span>Prescribed Medications ({prescriptionItems.length})</span>
                <span className="text-[11px] text-slate-500 font-normal">Structured Pharmacy Order</span>
              </div>
              <div className="divide-y divide-slate-100">
                {prescriptionItems.map((item, idx) => (
                  <div key={idx} className="p-2.5 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold text-slate-900">{item.medicine_name}</span>
                      <div className="text-[11px] text-slate-500">
                        {item.dosage} • {item.duration_days} days
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="px-2 py-0.5 rounded bg-teal-50 border border-teal-200 text-teal-800 font-bold text-xs">
                        Qty: {item.quantity}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(idx)}
                        className="text-slate-400 hover:text-rose-600 transition p-1 cursor-pointer"
                        title="Remove Item"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <label htmlFor="prescription-notes" className="block text-xs font-bold text-slate-700 mb-1">
              Prescription Directions & Dispensing Orders <span className="text-rose-500">*</span>
            </label>
            <textarea
              id="prescription-notes"
              rows={3}
              value={prescriptionNotes}
              onChange={(e) => setPrescriptionNotes(e.target.value)}
              placeholder="Enter medicine names, dosages, durations, and instructions"
              required={orderPrescription}
              className="w-full text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-lg font-mono focus:outline-none focus:border-emerald-600"
            />
            <span className="text-[11px] text-slate-500 block mt-1">
              Note: Prescriptions will be submitted in <strong>PENDING_VERIFICATION</strong> status. Pharmacy directly dispenses medications upon clinical stock review.
            </span>
          </div>
        </div>
      )}
    </section>
  );
};

export default PrescriptionCard;
