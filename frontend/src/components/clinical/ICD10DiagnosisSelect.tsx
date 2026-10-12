import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, ChevronDown, Check, X, BookOpen, AlertCircle } from 'lucide-react';
import { searchICD10, ICD10_METADATA } from '../../data/icd10_who.ts';
import type { ICD10Entry } from '../../data/icd10_who.ts';

interface ICD10DiagnosisSelectProps {
  value: string; // The selected or current diagnosis code (e.g., "I10")
  onChangeCode: (code: string) => void;
  onSelectDiagnosis: (code: string, name: string) => void;
  required?: boolean;
  disabled?: boolean;
  id?: string;
  className?: string;
}

export const ICD10DiagnosisSelect: React.FC<ICD10DiagnosisSelectProps> = ({
  value,
  onChangeCode,
  onSelectDiagnosis,
  required = true,
  disabled = false,
  id = 'diagnosis-code',
  className = ''
}) => {
  const [query, setQuery] = useState<string>(value || '');
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listboxRef = useRef<HTMLUListElement>(null);

  // Sync external value changes (e.g. when loading an existing consultation)
  useEffect(() => {
    setQuery(value || '');
  }, [value]);

  // Search results based on user query
  const results: ICD10Entry[] = useMemo(() => {
    if (!query.trim()) {
      // When empty or on focus, provide common primary care conditions
      return searchICD10('fever', 15).concat(searchICD10('hypertension', 10));
    }
    return searchICD10(query, 30);
  }, [query]);

  // Reset highlight index when results change
  useEffect(() => {
    setHighlightedIndex(results.length > 0 ? 0 : -1);
  }, [results]);

  // Click outside listener to dismiss dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        // If current query doesn't match selected value, restore selected value
        if (value && query !== value) {
          setQuery(value);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [value, query]);

  // Scroll highlighted item into view
  useEffect(() => {
    if (isOpen && highlightedIndex >= 0 && listboxRef.current) {
      const items = listboxRef.current.querySelectorAll('li');
      if (items[highlightedIndex]) {
        items[highlightedIndex].scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex, isOpen]);

  const handleSelect = (entry: ICD10Entry) => {
    setQuery(entry.code);
    onChangeCode(entry.code);
    onSelectDiagnosis(entry.code, entry.name);
    setIsOpen(false);
    inputRef.current?.focus();
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setQuery('');
    onChangeCode('');
    setIsOpen(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;

    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && results[highlightedIndex]) {
          handleSelect(results[highlightedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        if (value) {
          setQuery(value);
        }
        break;
      case 'Tab':
        setIsOpen(false);
        break;
    }
  };

  // Helper to highlight matching text
  const highlightMatch = (text: string, term: string) => {
    if (!term.trim()) return text;
    const parts = text.split(new RegExp(`(${term.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&')})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === term.toLowerCase() ? (
        <span key={index} className="bg-amber-100 text-amber-900 font-bold underline">
          {part}
        </span>
      ) : (
        part
      )
    );
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Search Input Container */}
      <div className="relative flex items-center">
        <div className="absolute left-2.5 text-slate-400 pointer-events-none">
          <Search className="w-3.5 h-3.5" aria-hidden="true" />
        </div>
        
        <input
          ref={inputRef}
          id={id}
          type="text"
          role="combobox"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          aria-controls={`${id}-listbox`}
          value={query}
          required={required}
          disabled={disabled}
          autoComplete="off"
          onChange={(e) => {
            setQuery(e.target.value);
            onChangeCode(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => {
            if (!disabled) setIsOpen(true);
          }}
          placeholder="e.g. I10, R50.9, or search name..."
          className="w-full text-xs pl-8 pr-16 py-2 bg-white border border-slate-300 rounded-lg font-mono focus:outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 transition-colors"
        />

        {/* Clear & Dropdown Toggle Buttons */}
        <div className="absolute right-2 flex items-center gap-1">
          {query && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              title="Clear selection"
              aria-label="Clear ICD-10 diagnosis code"
              className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-sm transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          )}
          <button
            type="button"
            tabIndex={-1}
            onClick={() => !disabled && setIsOpen(!isOpen)}
            aria-label="Toggle ICD-10 dropdown"
            className="p-1 text-slate-400 hover:text-slate-600 rounded-sm transition-colors"
          >
            <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Dataset Version & Standard Indicator */}
      <div className="mt-1 flex items-center justify-between text-[10px] text-slate-500">
        <span className="flex items-center gap-1 font-medium">
          <BookOpen className="w-2.5 h-2.5 text-emerald-600" aria-hidden="true" />
          <span>WHO ICD-10 ({ICD10_METADATA.edition}) · MoHFW Standard</span>
        </span>
        <span className="text-slate-400">Offline Dataset ({ICD10_METADATA.total_entries} codes)</span>
      </div>

      {/* Searchable Dropdown Listbox */}
      {isOpen && (
        <div
          className="absolute z-50 left-0 right-0 mt-1.5 bg-white border border-slate-200 rounded-xl shadow-xl max-h-72 flex flex-col overflow-hidden animate-in fade-in-0 duration-150"
          style={{ minWidth: '320px', width: '100%' }}
        >
          {/* Header */}
          <div className="px-3 py-1.5 bg-slate-50 border-b border-slate-100 flex items-center justify-between text-[11px] font-semibold text-slate-600">
            <span>Select Diagnosis Code</span>
            <span className="text-[10px] text-slate-400">
              {results.length} condition{results.length === 1 ? '' : 's'} available
            </span>
          </div>

          {/* Listbox Options */}
          <ul
            ref={listboxRef}
            id={`${id}-listbox`}
            role="listbox"
            tabIndex={-1}
            className="overflow-y-auto divide-y divide-slate-100 py-1"
          >
            {results.length > 0 ? (
              results.map((item, index) => {
                const isSelected = Boolean(value && item.code.toLowerCase() === value.toLowerCase());
                const isHighlighted = index === highlightedIndex;

                return (
                  <li
                    key={item.code}
                    id={`${id}-option-${index}`}
                    role="option"
                    aria-selected={isSelected}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    onClick={() => handleSelect(item)}
                    className={`px-3 py-2 text-xs cursor-pointer flex flex-col gap-0.5 transition-colors ${
                      isHighlighted
                        ? 'bg-emerald-50 text-emerald-950'
                        : isSelected
                        ? 'bg-slate-50 text-slate-900 font-semibold'
                        : 'text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-baseline justify-between gap-2">
                      <div className="flex items-center gap-1.5 flex-1 min-w-0">
                        {/* Strictly formatted: ICD code — Diagnosis name */}
                        <span className="font-mono font-bold text-emerald-700 shrink-0">
                          {highlightMatch(item.code, query)}
                        </span>
                        <span className="text-slate-400 shrink-0">—</span>
                        <span className="text-slate-900 font-medium truncate">
                          {highlightMatch(item.name, query)}
                        </span>
                      </div>

                      {isSelected && (
                        <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" aria-label="Currently selected" />
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-[10px] text-slate-500 pl-0.5">
                      <span className="bg-slate-100 px-1.5 py-0.2 rounded text-slate-600">
                        {item.category}
                      </span>
                      {item.keywords && item.keywords.length > 0 && query && (
                        <span className="text-slate-400 truncate italic">
                          Matches: {item.keywords.slice(0, 3).join(', ')}
                        </span>
                      )}
                    </div>
                  </li>
                );
              })
            ) : (
              <li className="px-4 py-6 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
                <AlertCircle className="w-5 h-5 text-amber-500" aria-hidden="true" />
                <div>
                  <p className="font-semibold text-slate-800">No matching ICD-10 diagnoses found</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Search by code (e.g. I10), condition name, or keyword. The doctor must select a valid diagnosis.
                  </p>
                </div>
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};
