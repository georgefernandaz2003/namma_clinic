import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, ChevronDown, Check, X, Pill, CheckCircle2, AlertTriangle, XCircle, PlusCircle } from 'lucide-react';
import type { MedicineMaster } from '../../types';

export interface MedicineSelectProps {
  value: string;
  medicineId?: number;
  medicines: MedicineMaster[];
  onChange: (medicine: { medicine_id?: number; medicine_name: string; unit?: string; category?: string }) => void;
  disabled?: boolean;
  className?: string;
  placeholder?: string;
}

export const MedicineSelect: React.FC<MedicineSelectProps> = ({
  value,
  medicineId,
  medicines,
  onChange,
  disabled = false,
  className = '',
  placeholder = 'Search & select EDL medicine from inventory...'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Find currently matched medicine from inventory
  const selectedMed = useMemo(() => {
    if (medicineId) {
      const byId = medicines.find((m) => m.id === medicineId);
      if (byId) return byId;
    }
    if (value) {
      const valLower = value.trim().toLowerCase();
      return medicines.find(
        (m) =>
          m.generic_name.toLowerCase() === valLower ||
          `${m.generic_name} ${m.strength} ${m.dosage_form}`.toLowerCase() === valLower ||
          `${m.generic_name} (${m.brand_name})`.toLowerCase() === valLower
      );
    }
    return null;
  }, [medicineId, value, medicines]);

  // Filtered medicines based on search query
  const filteredMedicines = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      // Prioritize in-stock medicines first, then alphabetical
      return [...medicines].sort((a, b) => {
        const stockA = Number(a.available_stock ?? a.total_available_stock ?? 0);
        const stockB = Number(b.available_stock ?? b.total_available_stock ?? 0);
        if (stockA > 0 && stockB <= 0) return -1;
        if (stockA <= 0 && stockB > 0) return 1;
        return a.generic_name.localeCompare(b.generic_name);
      });
    }

    return medicines.filter((m) => {
      const genMatch = m.generic_name.toLowerCase().includes(q);
      const brandMatch = (m.brand_name || '').toLowerCase().includes(q);
      const strengthMatch = (m.strength || '').toLowerCase().includes(q);
      const formMatch = (m.dosage_form || '').toLowerCase().includes(q);
      const catMatch = (m.category || '').toLowerCase().includes(q);
      return genMatch || brandMatch || strengthMatch || formMatch || catMatch;
    });
  }, [query, medicines]);

  const exactMatch = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return null;
    return medicines.find(
      (m) =>
        m.generic_name.toLowerCase() === q ||
        m.brand_name?.toLowerCase() === q ||
        `${m.generic_name} ${m.strength} ${m.dosage_form}`.toLowerCase() === q
    );
  }, [query, medicines]);

  const handleSelectMedicine = (med: MedicineMaster) => {
    const formattedName = `${med.generic_name} ${med.strength} ${med.dosage_form}`.trim();
    onChange({
      medicine_id: med.id,
      medicine_name: formattedName,
      unit: med.unit,
      category: med.category
    });
    setQuery('');
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const handleCustomSelect = () => {
    const trimmed = query.trim();
    if (!trimmed) return;
    onChange({
      medicine_name: trimmed
    });
    setQuery('');
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange({
      medicine_name: ''
    });
    setQuery('');
    inputRef.current?.focus();
    setIsOpen(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;

    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        return;
      }
    }

    const totalOptions = filteredMedicines.length + (query.trim() && !exactMatch ? 1 : 0);

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev < totalOptions - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : totalOptions - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (highlightedIndex >= 0 && highlightedIndex < filteredMedicines.length) {
        handleSelectMedicine(filteredMedicines[highlightedIndex]);
      } else if (highlightedIndex === filteredMedicines.length && query.trim() && !exactMatch) {
        handleCustomSelect();
      } else if (query.trim()) {
        if (filteredMedicines.length > 0) {
          handleSelectMedicine(filteredMedicines[0]);
        } else {
          handleCustomSelect();
        }
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setHighlightedIndex(-1);
    }
  };

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll('li');
      if (items[highlightedIndex] && typeof items[highlightedIndex].scrollIntoView === 'function') {
        items[highlightedIndex].scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex]);

  const displayStock = selectedMed
    ? Number(selectedMed.available_stock ?? selectedMed.total_available_stock ?? 0)
    : null;

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {/* Input container */}
      <div className="relative flex items-center">
        <div className="absolute left-2.5 pointer-events-none text-amber-600">
          <Pill className="w-3.5 h-3.5" />
        </div>

        <input
          ref={inputRef}
          type="text"
          disabled={disabled}
          value={isOpen ? query : (value || '')}
          placeholder={isOpen ? 'Search generic, brand name, strength...' : placeholder}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
            setHighlightedIndex(0);
            onChange({ medicine_name: e.target.value });
          }}
          onFocus={() => {
            setIsOpen(true);
            setQuery(value || '');
          }}
          onKeyDown={handleKeyDown}
          className="w-full pl-8 pr-16 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-xs font-semibold placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white focus:ring-1 focus:ring-blue-500 transition-colors"
        />

        {/* Action icons right */}
        <div className="absolute right-1.5 flex items-center gap-1">
          {(value || query) && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 hover:bg-slate-200 text-slate-400 hover:text-slate-600 rounded-full transition cursor-pointer"
              title="Clear medicine"
            >
              <X className="w-3 h-3" />
            </button>
          )}

          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              if (isOpen) {
                setIsOpen(false);
              } else {
                setIsOpen(true);
                inputRef.current?.focus();
              }
            }}
            className="p-1 hover:bg-slate-200 text-slate-500 hover:text-slate-800 rounded-md transition cursor-pointer"
            title="Toggle EDL medicine list"
          >
            <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Stock status indicator badge below or next to input when selected */}
      {selectedMed && !isOpen && (
        <div className="mt-1 flex items-center gap-2 text-[10px]">
          {displayStock !== null && displayStock > 0 ? (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              In Stock: {displayStock} {selectedMed.unit || 'units'} (FEFO Ready)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 font-bold">
              <XCircle className="w-3 h-3 text-rose-600" />
              Out of Stock in Facility Pharmacy
            </span>
          )}
          {selectedMed.category && (
            <span className="text-slate-500 font-medium">
              {selectedMed.category}
            </span>
          )}
        </div>
      )}

      {/* Floating Dropdown */}
      {isOpen && !disabled && (
        <div className="absolute z-50 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-xl overflow-hidden transition-all duration-200 animate-in fade-in slide-in-from-top-1 max-w-lg min-w-[280px]">
          {/* Header indicator */}
          <div className="px-3 py-1.5 bg-slate-50 border-b border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span className="font-semibold text-slate-700">
              {query.trim()
                ? `Matching EDL Medicines (${filteredMedicines.length})`
                : `Facility EDL Medicines Inventory (${filteredMedicines.length})`}
            </span>
            <span className="text-[10px] text-slate-400">Live FEFO Stock Connected</span>
          </div>

          <ul
            ref={listRef}
            className="max-h-56 overflow-y-auto divide-y divide-slate-100 text-xs focus:outline-none"
          >
            {/* Custom unlisted medicine option */}
            {query.trim() && !exactMatch && (
              <li
                onMouseDown={(e) => {
                  e.preventDefault();
                  handleCustomSelect();
                }}
                className={`px-3 py-2 flex items-center justify-between cursor-pointer transition ${
                  highlightedIndex === filteredMedicines.length
                    ? 'bg-amber-50 text-amber-900 font-semibold'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-800'
                }`}
              >
                <div className="flex items-center gap-2">
                  <PlusCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <div>
                    <span className="font-bold text-slate-800">Prescribe custom / non-EDL: </span>
                    <span className="text-slate-900 italic font-semibold">"{query.trim()}"</span>
                  </div>
                </div>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-600 font-medium">
                  Custom
                </span>
              </li>
            )}

            {filteredMedicines.length > 0 ? (
              filteredMedicines.map((med, idx) => {
                const isSelected = selectedMed?.id === med.id;
                const isHighlighted = idx === highlightedIndex;
                const stockQty = Number(med.available_stock ?? med.total_available_stock ?? 0);
                const hasStock = stockQty > 0;

                return (
                  <li
                    key={`${med.id}-${idx}`}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      handleSelectMedicine(med);
                    }}
                    onMouseEnter={() => setHighlightedIndex(idx)}
                    className={`px-3 py-2 cursor-pointer flex items-center justify-between transition group ${
                      isSelected
                        ? 'bg-blue-50/80 font-bold text-blue-900'
                        : isHighlighted
                        ? 'bg-slate-100 text-slate-900 font-medium'
                        : 'hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    <div className="flex flex-col min-w-0 pr-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-bold text-slate-900 text-xs group-hover:text-blue-900">
                          {med.generic_name}
                        </span>
                        {med.strength && (
                          <span className="font-mono text-[11px] font-bold px-1.5 py-0.2 rounded bg-slate-100 text-slate-700">
                            {med.strength}
                          </span>
                        )}
                        {med.dosage_form && (
                          <span className="text-[10px] text-slate-500 font-medium">
                            • {med.dosage_form}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-0.5">
                        {med.brand_name && (
                          <span className="font-semibold text-slate-600">
                            Brand: {med.brand_name}
                          </span>
                        )}
                        {med.category && (
                          <span className="text-slate-400">
                            • {med.category}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Stock badge */}
                    <div className="flex items-center gap-1.5 shrink-0">
                      {hasStock ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          <Check className="w-3 h-3 text-emerald-600 stroke-[3]" />
                          {stockQty} {med.unit || 'units'}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                          <AlertTriangle className="w-3 h-3 text-rose-600" />
                          Out of stock
                        </span>
                      )}
                    </div>
                  </li>
                );
              })
            ) : (
              !query.trim() && (
                <li className="p-4 text-center text-xs text-slate-400">
                  No EDL medicines configured in facility inventory.
                </li>
              )
            )}

            {filteredMedicines.length === 0 && query.trim() && (
              <li className="p-3 text-center text-xs text-slate-500">
                No matching EDL medicine found. You can prescribe it as custom above.
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};
