import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, ChevronDown, Check, X, Tag, PlusCircle } from 'lucide-react';
import { COMMON_ICD10_DIAGNOSES, type ICD10Diagnosis } from '../../data/icd10Data';

interface ICD10SelectProps {
  value: string;
  code?: string;
  onChange: (code: string, name: string) => void;
  required?: boolean;
  label?: string;
  disabled?: boolean;
  className?: string;
}

export const ICD10Select: React.FC<ICD10SelectProps> = ({
  value,
  code = '',
  onChange,
  required = false,
  label = 'ICD-10 Diagnosis Code & Name *',
  disabled = false,
  className = ''
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

  // Filter diagnoses based on query
  const filteredDiagnoses = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      // When empty query, show common diagnoses first, then the rest
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

  // Check if current input matches any predefined diagnosis exactly
  const exactMatch = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return null;
    return COMMON_ICD10_DIAGNOSES.find(
      (d) => d.name.toLowerCase() === q || d.code.toLowerCase() === q
    );
  }, [query]);

  const handleSelect = (diag: ICD10Diagnosis) => {
    onChange(diag.code, diag.name);
    setQuery('');
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const handleCustomSelect = () => {
    if (query.trim()) {
      onChange('R69', query.trim()); // R69 = Illness, unspecified
      setQuery('');
      setIsOpen(false);
      setHighlightedIndex(-1);
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange('', '');
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
        handleSelect(filteredDiagnoses[highlightedIndex]);
      } else if (highlightedIndex === filteredDiagnoses.length && query.trim() && !exactMatch) {
        handleCustomSelect();
      } else if (query.trim()) {
        if (filteredDiagnoses.length > 0) {
          handleSelect(filteredDiagnoses[0]);
        } else {
          handleCustomSelect();
        }
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setHighlightedIndex(-1);
    }
  };

  // Scroll highlighted element into view
  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll('li');
      if (items[highlightedIndex]) {
        items[highlightedIndex].scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex]);

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {label && (
        <div className="flex items-center justify-between mb-1">
          <label className="block text-slate-700 font-bold text-xs">
            {label}
          </label>
          {code && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-mono text-[11px] font-bold">
              <Tag className="w-3 h-3 text-blue-600" />
              ICD: {code}
            </span>
          )}
        </div>
      )}

      {/* Input container */}
      <div className="relative flex items-center">
        <div className="absolute left-3 pointer-events-none text-slate-400">
          <Search className="w-4 h-4" />
        </div>

        <input
          ref={inputRef}
          type="text"
          disabled={disabled}
          value={isOpen ? query : (value || '')}
          placeholder={isOpen ? 'Search by ICD code, disease name, or category...' : (value ? `${code ? `[${code}] ` : ''}${value}` : 'Select or type ICD-10 diagnosis...')}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
            setHighlightedIndex(0);
            // Also notify parent of text changes if needed
            onChange(code || 'R69', e.target.value);
          }}
          onFocus={() => {
            setIsOpen(true);
            setQuery(value || '');
          }}
          onKeyDown={handleKeyDown}
          required={required}
          className="w-full pl-9 pr-16 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-xs font-medium placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white focus:ring-1 focus:ring-blue-500 transition-colors"
        />

        <div className="absolute right-2 flex items-center gap-1">
          {(value || query) && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 hover:bg-slate-200 text-slate-400 hover:text-slate-600 rounded-full transition cursor-pointer"
              title="Clear diagnosis"
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

      {/* Floating Dropdown */}
      {isOpen && !disabled && (
        <div className="absolute z-50 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-xl overflow-hidden transition-all duration-200 animate-in fade-in slide-in-from-top-1">
          {/* Header indicator */}
          <div className="px-3 py-1.5 bg-slate-50 border-b border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span className="font-semibold">
              {query.trim()
                ? `Matching diagnoses (${filteredDiagnoses.length})`
                : `Common Primary Care / OPD Diagnoses (${filteredDiagnoses.length})`}
            </span>
            <span className="text-[10px] text-slate-400">Type code or name to filter</span>
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
                    <span className="font-bold text-slate-800">Use custom: </span>
                    <span className="text-slate-900 font-semibold italic">"{query.trim()}"</span>
                    <span className="text-[10px] text-slate-500 ml-2">(Unspecified ICD-10)</span>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 text-slate-700">R69</span>
              </li>
            )}

            {filteredDiagnoses.length > 0 ? (
              filteredDiagnoses.map((diag, idx) => {
                const isSelected = value === diag.name || code === diag.code;
                const isHighlighted = idx === highlightedIndex;

                return (
                  <li
                    key={`${diag.code}-${idx}`}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      handleSelect(diag);
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
                    <div className="flex items-center gap-2.5 min-w-0 pr-2">
                      <span className="shrink-0 font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 group-hover:bg-blue-200 transition">
                        {diag.code}
                      </span>
                      <span className="truncate text-xs text-slate-900 group-hover:text-blue-900 font-medium">
                        {diag.name}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-medium hidden sm:inline-block">
                        {diag.category}
                      </span>
                      {isSelected && (
                        <Check className="w-4 h-4 text-blue-600 shrink-0" />
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

            {filteredDiagnoses.length === 0 && !query.trim() && (
              <li className="p-4 text-center text-xs text-slate-400">
                No diagnoses available.
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};
