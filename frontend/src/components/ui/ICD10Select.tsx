import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, ChevronDown, Check, X, Tag, PlusCircle, CheckCircle2 } from 'lucide-react';
import { COMMON_ICD10_DIAGNOSES, type ICD10Diagnosis } from '../../data/icd10Data';

export interface SelectedDiagnosis {
  code: string;
  name: string;
}

export interface ICD10SelectProps {
  value: string;
  code?: string;
  onChange: (code: string, name: string) => void;
  required?: boolean;
  label?: string;
  disabled?: boolean;
  className?: string;
}

export function parseDiagnosesFromProps(codeProp: string, valueProp: string): SelectedDiagnosis[] {
  const trimmedCode = (codeProp || '').trim();
  const trimmedValue = (valueProp || '').trim();

  if (!trimmedCode && !trimmedValue) return [];

  // Exact single match check (e.g., 'E11.9 / I10' in master list)
  const exactMatch = COMMON_ICD10_DIAGNOSES.find(
    (d) => d.code.toLowerCase() === trimmedCode.toLowerCase()
  );
  if (exactMatch && (!trimmedValue || trimmedValue.toLowerCase() === exactMatch.name.toLowerCase())) {
    return [{ code: exactMatch.code, name: exactMatch.name }];
  }

  // Split code by comma or slash
  let codeParts: string[] = [];
  if (trimmedCode) {
    if (COMMON_ICD10_DIAGNOSES.some((d) => d.code.toLowerCase() === trimmedCode.toLowerCase())) {
      codeParts = [trimmedCode];
    } else if (trimmedCode.includes(',')) {
      codeParts = trimmedCode.split(',').map((c) => c.trim()).filter(Boolean);
    } else if (trimmedCode.includes(' / ')) {
      codeParts = trimmedCode.split(' / ').map((c) => c.trim()).filter(Boolean);
    } else if (trimmedCode.includes('/')) {
      codeParts = trimmedCode.split('/').map((c) => c.trim()).filter(Boolean);
    } else {
      codeParts = [trimmedCode];
    }
  }

  // Split value by comma or slash
  let nameParts: string[] = [];
  if (trimmedValue) {
    if (trimmedValue.includes(', ')) {
      nameParts = trimmedValue.split(', ').map((n) => n.trim()).filter(Boolean);
    } else if (trimmedValue.includes(' / ')) {
      nameParts = trimmedValue.split(' / ').map((n) => n.trim()).filter(Boolean);
    } else if (trimmedValue.includes(',')) {
      nameParts = trimmedValue.split(',').map((n) => n.trim()).filter(Boolean);
    } else {
      nameParts = [trimmedValue];
    }
  }

  if (codeParts.length > 0) {
    return codeParts.map((codeItem, idx) => {
      const match = COMMON_ICD10_DIAGNOSES.find(
        (d) => d.code.toLowerCase() === codeItem.toLowerCase()
      );
      if (match) {
        const nameToUse = match.code === 'R69' && nameParts[idx] ? nameParts[idx] : match.name;
        return { code: match.code, name: nameToUse };
      }
      const nameFallback = nameParts[idx] || (nameParts.length === 1 && codeParts.length === 1 ? nameParts[0] : codeItem);
      return { code: codeItem, name: nameFallback };
    });
  }

  // If code is empty but value/name is present
  if (trimmedValue) {
    const match = COMMON_ICD10_DIAGNOSES.find(
      (d) => d.name.toLowerCase() === trimmedValue.toLowerCase()
    );
    if (match) {
      return [{ code: match.code, name: match.name }];
    }
    return [{ code: 'R69', name: trimmedValue }];
  }

  return [];
}

export function serializeDiagnoses(items: SelectedDiagnosis[]): { code: string; name: string } {
  if (items.length === 0) {
    return { code: '', name: '' };
  }
  const codeStr = items.map((i) => i.code).join(', ');
  const nameStr = items.map((i) => i.name).join(', ');

  // Protect against database max_length (diagnosis_code max_length=50, diagnosis_name max_length=200)
  const safeCode = codeStr.length > 50 ? codeStr.slice(0, 47) + '...' : codeStr;
  const safeName = nameStr.length > 200 ? nameStr.slice(0, 196) + '...' : nameStr;

  return { code: safeCode, name: safeName };
}

export const ICD10Select: React.FC<ICD10SelectProps> = ({
  value,
  code = '',
  onChange,
  required = false,
  label = 'ICD-10 Diagnosis Code & Name (Select One or More) *',
  disabled = false,
  className = ''
}) => {
  const [selected, setSelected] = useState<SelectedDiagnosis[]>(() =>
    parseDiagnosesFromProps(code, value)
  );
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Synchronize internal state when parent props change externally
  useEffect(() => {
    const { code: currentCode, name: currentName } = serializeDiagnoses(selected);
    if (code === currentCode && value === currentName) {
      return;
    }
    const parsed = parseDiagnosesFromProps(code, value);
    setSelected(parsed);
  }, [code, value]);

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

  // Filter diagnoses based on query
  const filteredDiagnoses = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      // Sort common first, then alphabetical
      return [...COMMON_ICD10_DIAGNOSES].sort((a, b) => {
        if (a.common && !b.common) return -1;
        if (!a.common && b.common) return 1;
        return a.name.localeCompare(b.name);
      });
    }

    return COMMON_ICD10_DIAGNOSES.filter((d) => {
      const codeMatch = d.code.toLowerCase().includes(q);
      const nameMatch = d.name.toLowerCase().includes(q);
      const catMatch = d.category.toLowerCase().includes(q);
      return codeMatch || nameMatch || catMatch;
    });
  }, [query]);

  // Exact match check for query
  const exactMatch = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return null;
    return COMMON_ICD10_DIAGNOSES.find(
      (d) => d.name.toLowerCase() === q || d.code.toLowerCase() === q
    );
  }, [query]);

  const updateSelected = (newSelected: SelectedDiagnosis[]) => {
    setSelected(newSelected);
    const { code: newCode, name: newName } = serializeDiagnoses(newSelected);
    onChange(newCode, newName);
  };

  const handleToggleDiagnosis = (diag: ICD10Diagnosis) => {
    const existsIndex = selected.findIndex(
      (s) => s.code.toLowerCase() === diag.code.toLowerCase()
    );

    let newSelected: SelectedDiagnosis[];
    if (existsIndex >= 0) {
      // Remove already selected
      newSelected = selected.filter((_, i) => i !== existsIndex);
    } else {
      // Add to selected list
      newSelected = [...selected, { code: diag.code, name: diag.name }];
    }

    updateSelected(newSelected);
    setQuery('');
    setHighlightedIndex(0);
  };

  const handleRemoveItem = (codeToRemove: string, nameToRemove: string) => {
    if (disabled) return;
    const newSelected = selected.filter(
      (s) => !(s.code === codeToRemove && s.name === nameToRemove)
    );
    updateSelected(newSelected);
  };

  const handleCustomSelect = () => {
    const trimmed = query.trim();
    if (!trimmed) return;

    if (!selected.some((s) => s.name.toLowerCase() === trimmed.toLowerCase())) {
      const newSelected = [...selected, { code: 'R69', name: trimmed }];
      updateSelected(newSelected);
    }
    setQuery('');
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const handleClearAll = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (disabled) return;
    updateSelected([]);
    setQuery('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;

    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        return;
      }
    }

    // Backspace on empty query removes last selected chip
    if (e.key === 'Backspace' && query === '' && selected.length > 0) {
      const newSelected = selected.slice(0, selected.length - 1);
      updateSelected(newSelected);
      return;
    }

    const totalOptions = filteredDiagnoses.length + (query.trim() && !exactMatch ? 1 : 0);

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev < totalOptions - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : totalOptions - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (highlightedIndex >= 0 && highlightedIndex < filteredDiagnoses.length) {
        handleToggleDiagnosis(filteredDiagnoses[highlightedIndex]);
      } else if (highlightedIndex === filteredDiagnoses.length && query.trim() && !exactMatch) {
        handleCustomSelect();
      } else if (query.trim()) {
        if (filteredDiagnoses.length > 0) {
          handleToggleDiagnosis(filteredDiagnoses[0]);
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

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {/* Label and Selected Counter */}
      {label && (
        <div className="flex items-center justify-between mb-1">
          <label className="block text-slate-700 font-bold text-xs">
            {label}
          </label>
          {selected.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-[11px] font-semibold">
              <CheckCircle2 className="w-3 h-3 text-blue-600" />
              {selected.length} {selected.length === 1 ? 'diagnosis' : 'diagnoses'} selected
            </span>
          )}
        </div>
      )}

      {/* Selected Diagnoses Chips */}
      {selected.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 mb-2">
          {selected.map((item, idx) => (
            <span
              key={`${item.code}-${idx}`}
              className="inline-flex items-center gap-1.5 pl-2 pr-1.5 py-1 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 text-xs font-medium shadow-2xs group transition hover:bg-blue-100"
            >
              <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-200/90 text-blue-900">
                {item.code}
              </span>
              <span className="max-w-[200px] sm:max-w-[280px] truncate" title={item.name}>
                {item.name}
              </span>
              {!disabled && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveItem(item.code, item.name);
                  }}
                  className="p-0.5 hover:bg-blue-200 text-blue-500 hover:text-rose-600 rounded transition cursor-pointer"
                  title={`Remove ${item.name}`}
                  aria-label={`Remove ${item.name}`}
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </span>
          ))}

          {selected.length > 1 && !disabled && (
            <button
              type="button"
              onClick={handleClearAll}
              className="text-[11px] text-slate-400 hover:text-rose-600 font-medium px-1.5 py-1 transition cursor-pointer"
              title="Clear all selected diagnoses"
            >
              Clear all
            </button>
          )}
        </div>
      )}

      {/* Search Input Box */}
      <div className="relative flex items-center">
        <div className="absolute left-3 pointer-events-none text-slate-400">
          <Search className="w-4 h-4" />
        </div>

        <input
          ref={inputRef}
          type="text"
          disabled={disabled}
          value={query}
          placeholder={
            selected.length === 0
              ? 'Search & select ICD-10 diagnosis (select one or more)...'
              : 'Search & add another diagnosis (by code or name)...'
          }
          onChange={(e) => {
            setQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
            setHighlightedIndex(0);
          }}
          onFocus={() => {
            setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          className="w-full pl-9 pr-16 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-xs font-medium placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white focus:ring-1 focus:ring-blue-500 transition-colors"
        />

        {/* Hidden input for HTML5 form required validation */}
        {required && (
          <input
            type="text"
            tabIndex={-1}
            autoComplete="off"
            aria-hidden="true"
            value={selected.length > 0 ? 'valid' : ''}
            required={required && selected.length === 0}
            onChange={() => {}}
            className="sr-only opacity-0 h-0 w-0 absolute pointer-events-none"
          />
        )}

        <div className="absolute right-2 flex items-center gap-1">
          {query && !disabled && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setQuery('');
                inputRef.current?.focus();
              }}
              className="p-1 hover:bg-slate-200 text-slate-400 hover:text-slate-600 rounded-full transition cursor-pointer"
              title="Clear search"
            >
              <X className="w-3.5 h-3.5" />
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
            title="Toggle diagnosis list"
          >
            <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Floating Multi-Select Dropdown */}
      {isOpen && !disabled && (
        <div className="absolute z-50 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-xl overflow-hidden transition-all duration-200 animate-in fade-in slide-in-from-top-1">
          {/* Header indicator */}
          <div className="px-3 py-1.5 bg-slate-50 border-b border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span className="font-semibold text-slate-700">
              {query.trim()
                ? `Matching diagnoses (${filteredDiagnoses.length})`
                : `Common ICD-10 Diagnoses (${filteredDiagnoses.length})`}
            </span>
            <span className="text-[10px] text-slate-400">Click item to toggle selection</span>
          </div>

          <ul
            ref={listRef}
            className="max-h-60 overflow-y-auto divide-y divide-slate-100 text-xs focus:outline-none"
          >
            {/* Custom entry option if query has typed text and not an exact match */}
            {query.trim() && !exactMatch && (
              <li
                onMouseDown={(e) => {
                  e.preventDefault();
                  handleCustomSelect();
                }}
                className={`px-3 py-2.5 flex items-center justify-between cursor-pointer transition ${
                  highlightedIndex === filteredDiagnoses.length
                    ? 'bg-blue-50 text-blue-900 font-semibold'
                    : 'bg-emerald-50/50 hover:bg-emerald-100/60 text-emerald-900'
                }`}
              >
                <div className="flex items-center gap-2">
                  <PlusCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                  <div>
                    <span className="font-bold text-slate-800">Add custom: </span>
                    <span className="text-slate-900 font-semibold italic">"{query.trim()}"</span>
                    <span className="text-[10px] text-slate-500 ml-2">(Unspecified ICD-10)</span>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-semibold">
                  R69
                </span>
              </li>
            )}

            {filteredDiagnoses.length > 0 ? (
              filteredDiagnoses.map((diag, idx) => {
                const isSelected = selected.some(
                  (s) => s.code.toLowerCase() === diag.code.toLowerCase()
                );
                const isHighlighted = idx === highlightedIndex;

                return (
                  <li
                    key={`${diag.code}-${idx}`}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      handleToggleDiagnosis(diag);
                    }}
                    onMouseEnter={() => setHighlightedIndex(idx)}
                    className={`px-3 py-2 cursor-pointer flex items-center justify-between transition group ${
                      isSelected
                        ? 'bg-blue-50/80 text-blue-900 font-medium'
                        : isHighlighted
                        ? 'bg-slate-100 text-slate-900 font-medium'
                        : 'hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0 pr-2">
                      {/* Checkbox indicator */}
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 transition ${
                          isSelected
                            ? 'bg-blue-600 border-blue-600 text-white'
                            : 'border-slate-300 bg-white group-hover:border-slate-400'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>

                      <span
                        className={`shrink-0 font-mono text-[11px] font-bold px-2 py-0.5 rounded transition ${
                          isSelected
                            ? 'bg-blue-200/90 text-blue-900'
                            : 'bg-blue-100 text-blue-800 group-hover:bg-blue-200'
                        }`}
                      >
                        {diag.code}
                      </span>

                      <span
                        className={`truncate text-xs ${
                          isSelected
                            ? 'font-bold text-blue-950'
                            : 'text-slate-900 group-hover:text-blue-900 font-medium'
                        }`}
                      >
                        {diag.name}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-medium hidden sm:inline-block">
                        {diag.category}
                      </span>
                      {isSelected && (
                        <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">
                          Selected
                        </span>
                      )}
                    </div>
                  </li>
                );
              })
            ) : (
              !query.trim() && (
                <li className="p-4 text-center text-xs text-slate-400">
                  No matching ICD-10 diagnoses found.
                </li>
              )
            )}
          </ul>

          {/* Footer with summary and Done button */}
          <div className="px-3 py-2 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500 text-[11px]">
              {selected.length === 0 ? 'Click diagnoses to select' : `${selected.length} selected`}
            </span>
            <button
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                setIsOpen(false);
              }}
              className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white font-semibold text-[11px] transition cursor-pointer shadow-xs"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
