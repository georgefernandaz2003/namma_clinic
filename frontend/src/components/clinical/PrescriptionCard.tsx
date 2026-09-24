import React from 'react';
import type { MedicineMaster } from '../../types';
import { Pill } from 'lucide-react';

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
  medicines
}) => {
  const handleAddMedicine = () => {
    if (!selectedMedicineId) return;
    const med = medicines.find((m) => m.id === Number(selectedMedicineId));
    if (!med) return;

    const medDetail = med.strength || med.dosage_form || '';
    const line = `${med.generic_name}${medDetail ? ` (${medDetail})` : ''}: ${dosageInstructions}`;
    setPrescriptionNotes((prev) => (prev ? `${prev}\n• ${line}` : `• ${line}`));
    setSelectedMedicineId('');
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
            <div className="sm:col-span-5">
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

            <div className="sm:col-span-5">
              <label htmlFor="dosage-inst" className="block text-[11px] font-bold text-slate-700 mb-1">
                Dosage & Timing Directions
              </label>
              <input
                id="dosage-inst"
                type="text"
                value={dosageInstructions}
                onChange={(e) => setDosageInstructions(e.target.value)}
                placeholder="e.g. 1 tab thrice daily after meals for 3 days"
                className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
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

          <div>
            <label htmlFor="rx-notes" className="block text-xs font-bold text-slate-700 mb-1">
              Prescription Directions & Dispensing Orders <span className="text-rose-500">*</span>
            </label>
            <textarea
              id="rx-notes"
              rows={3}
              value={prescriptionNotes}
              onChange={(e) => setPrescriptionNotes(e.target.value)}
              placeholder="Enter medicine names, dosages, durations, and instructions"
              required={orderPrescription}
              className="w-full text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-lg font-mono focus:outline-none focus:border-emerald-600"
            />
            <span className="text-[11px] text-slate-500 block mt-1">
              Note: Prescriptions will be submitted in <strong>PENDING_VERIFICATION</strong> status. Pharmacy verifies and dispenses medications separately.
            </span>
          </div>
        </div>
      )}
    </section>
  );
};

export default PrescriptionCard;
