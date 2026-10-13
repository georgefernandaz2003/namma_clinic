import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, ChevronDown, Check, X, FileText, CheckCircle2, FlaskConical, Stethoscope, Sparkles } from 'lucide-react';

export interface LabTestItem {
  id: number;
  code: string;
  name: string;
  category?: string;
  reference_range?: string;
  unit?: string;
}

export interface LabTestSelectProps {
  availableTests: LabTestItem[];
  selectedIds: number[];
  onChange: (selectedIds: number[]) => void;
  disabled?: boolean;
  className?: string;
  label?: string;
}

/**
 * Determine if a test is Point-of-Care (POCT rapid card/strip) or Hub Lab autoanalyzer/microscopy.
 */
export function isPoctTest(test: LabTestItem): boolean {
  const code = (test.code || '').toUpperCase();
  const name = (test.name || '').toLowerCase();
  const cat = (test.category || '').toLowerCase();

  if (
    code.includes('RAPID') ||
    code.includes('STRIP') ||
    code.includes('CARD') ||
    code.includes('UPT') ||
    code.includes('RBG') ||
    code.includes('MALARIA') ||
    code.includes('DENGUE') ||
    code.includes('HIV') ||
    code.includes('HBSAG') ||
    code.includes('URINE')
  ) {
    return true;
  }

  if (
    name.includes('rapid') ||
    name.includes('strip') ||
    name.includes('card') ||
    name.includes('upt') ||
    name.includes('benedict') ||
    name.includes('random blood glucose') ||
    name.includes('urine sugar') ||
    name.includes('urine albumin') ||
    name.includes('malaria') ||
    name.includes('dengue') ||
    name.includes('hiv') ||
    name.includes('hepatitis')
  ) {
    return true;
  }

  if (cat.includes('maternal') || cat.includes('urinalysis') || cat.includes('serology')) {
    return true;
  }

  return false;
}

export const LabTestSelect: React.FC<LabTestSelectProps> = ({
  availableTests,
  selectedIds,
  onChange,
  disabled = false,
  className = '',
  label = 'Order 14 Essential Diagnostic Tests (Point-of-Care & Hub Lab)'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeCategoryFilter, setActiveCategoryFilter] = useState<string>('ALL');

  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 50);
    } else {
      setQuery('');
      setActiveCategoryFilter('ALL');
    }
  }, [isOpen]);

  // Distinct categories available in tests list
  const availableCategories = useMemo(() => {
    const cats = new Set<string>();
    availableTests.forEach((t) => {
      if (t.category) cats.add(t.category);
    });
    return Array.from(cats);
  }, [availableTests]);

  // Counts
  const poctCount = useMemo(() => availableTests.filter(isPoctTest).length, [availableTests]);
  const hubCount = useMemo(() => availableTests.length - poctCount, [availableTests, poctCount]);

  // Filtered test items
  const filteredTests = useMemo(() => {
    let result = availableTests;

    // Filter by category tab
    if (activeCategoryFilter === 'POCT') {
      result = result.filter(isPoctTest);
    } else if (activeCategoryFilter === 'HUB') {
      result = result.filter((t) => !isPoctTest(t));
    } else if (activeCategoryFilter === 'SELECTED') {
      result = result.filter((t) => selectedIds.includes(t.id));
    } else if (activeCategoryFilter !== 'ALL') {
      result = result.filter((t) => (t.category || '').toLowerCase() === activeCategoryFilter.toLowerCase());
    }

    // Filter by search query
    const q = query.trim().toLowerCase();
    if (q) {
      result = result.filter((t) => {
        const nameMatch = (t.name || '').toLowerCase().includes(q);
        const codeMatch = (t.code || '').toLowerCase().includes(q);
        const catMatch = (t.category || '').toLowerCase().includes(q);
        const poctMatch = isPoctTest(t) ? 'poct point of care rapid strip card'.includes(q) : 'hub lab autoanalyzer'.includes(q);
        return nameMatch || codeMatch || catMatch || poctMatch;
      });
    }

    return result;
  }, [availableTests, activeCategoryFilter, query, selectedIds]);

  // Selected test objects
  const selectedTests = useMemo(() => {
    return availableTests.filter((t) => selectedIds.includes(t.id));
  }, [availableTests, selectedIds]);

  // Toggle single test
  const handleToggleTest = (id: number) => {
    if (disabled) return;
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((testId) => testId !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  // Remove test from chip
  const handleRemoveTest = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (disabled) return;
    onChange(selectedIds.filter((testId) => testId !== id));
  };

  // Select all visible / Select all 14
  const handleSelectAllVisible = () => {
    if (disabled) return;
    const visibleIds = filteredTests.map((t) => t.id);
    const combined = Array.from(new Set([...selectedIds, ...visibleIds]));
    onChange(combined);
  };

  // Clear all selections
  const handleClearAll = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (disabled) return;
    onChange([]);
  };

  return (
    <div ref={containerRef} className={`space-y-2.5 ${className}`} data-testid="lab-test-select-container">
      {/* Header with Title and Badges */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <label className="font-bold text-slate-900 flex items-center gap-1.5 text-xs">
          <FileText className="w-4 h-4 text-teal-600" />
          <span>{label}</span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 border border-teal-200">
            {selectedIds.length} / {availableTests.length || 14} Selected
          </span>
        </label>

        <div className="flex items-center gap-2">
          {selectedIds.length > 0 && (
            <button
              type="button"
              onClick={handleClearAll}
              disabled={disabled}
              className="text-[11px] text-rose-600 hover:text-rose-700 font-semibold flex items-center gap-1 px-2 py-0.5 rounded-md hover:bg-rose-50 transition"
              title="Clear all selected diagnostic tests"
            >
              <X className="w-3.5 h-3.5" />
              Clear All
            </button>
          )}

          <button
            type="button"
            onClick={() => {
              if (selectedIds.length === availableTests.length && availableTests.length > 0) {
                onChange([]);
              } else {
                onChange(availableTests.map((t) => t.id));
              }
            }}
            disabled={disabled || availableTests.length === 0}
            className="text-[11px] text-teal-700 hover:text-teal-800 font-bold flex items-center gap-1 px-2 py-0.5 rounded-md bg-teal-50 hover:bg-teal-100 border border-teal-200 transition"
          >
            <Sparkles className="w-3 h-3 text-teal-600" />
            {selectedIds.length === availableTests.length && availableTests.length > 0
              ? 'Deselect All'
              : `Select All 14`}
          </button>
        </div>
      </div>

      {/* Dropdown Combobox Trigger Box */}
      <div className="relative">
        <div
          role="button"
          tabIndex={disabled ? -1 : 0}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              !disabled && setIsOpen(!isOpen);
            }
          }}
          className={`w-full min-h-[42px] px-3 py-2 bg-white border rounded-xl flex items-center justify-between cursor-pointer transition select-none ${
            isOpen
              ? 'border-teal-500 ring-2 ring-teal-500/20 shadow-sm'
              : 'border-slate-300 hover:border-slate-400'
          } ${disabled ? 'opacity-60 cursor-not-allowed bg-slate-50' : ''}`}
          data-testid="lab-test-dropdown-trigger"
        >
          <div className="flex items-center gap-2 flex-1 min-w-0 pr-2">
            <FlaskConical className="w-4 h-4 text-teal-600 shrink-0" />
            {selectedIds.length === 0 ? (
              <span className="text-xs text-slate-400 font-normal">
                Click to open dropdown & select essential lab tests (POCT Rapid & Hub Lab)...
              </span>
            ) : (
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-xs font-bold text-teal-900">
                  {selectedIds.length} {selectedIds.length === 1 ? 'diagnostic test' : 'diagnostic tests'} ordered:
                </span>
                <span className="text-xs text-slate-600 truncate">
                  {selectedTests.slice(0, 3).map((t) => t.name).join(', ')}
                  {selectedTests.length > 3 && ` +${selectedTests.length - 3} more`}
                </span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <div className={`p-1 rounded-md text-slate-500 hover:text-slate-800 transition ${isOpen ? 'rotate-180' : ''}`}>
              <ChevronDown className="w-4 h-4" />
            </div>
          </div>
        </div>

        {/* Selected Test Badges / Dismissible Chips */}
        {selectedTests.length > 0 && (
          <div className="pt-2 flex flex-wrap gap-1.5" data-testid="selected-tests-chips">
            {selectedTests.map((t) => {
              const isPoct = isPoctTest(t);
              return (
                <span
                  key={t.id}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border shadow-2xs transition ${
                    isPoct
                      ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                      : 'bg-blue-50 text-blue-900 border-blue-200'
                  }`}
                >
                  <span
                    className={`font-mono text-[10px] px-1 py-0.2 rounded font-bold ${
                      isPoct ? 'bg-emerald-200/70 text-emerald-950' : 'bg-blue-200/70 text-blue-950'
                    }`}
                  >
                    {t.code}
                  </span>
                  <span className="font-semibold">{t.name}</span>
                  <span className="text-[10px] text-slate-500 hidden sm:inline">
                    ({isPoct ? 'POCT' : 'Hub Lab'})
                  </span>
                  <button
                    type="button"
                    onClick={(e) => handleRemoveTest(t.id, e)}
                    className="ml-0.5 text-slate-400 hover:text-rose-600 rounded-full hover:bg-white/80 p-0.5 transition"
                    title={`Remove ${t.name}`}
                    aria-label={`Remove ${t.name}`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              );
            })}
          </div>
        )}

        {/* Dropdown Menu Overlay */}
        {isOpen && (
          <div
            className="absolute left-0 right-0 top-full mt-1.5 bg-white border border-slate-200 rounded-xl shadow-xl z-50 overflow-hidden flex flex-col max-h-[460px] animate-in fade-in slide-in-from-top-2 duration-150"
            data-testid="lab-test-dropdown-menu"
          >
            {/* Search Input Box */}
            <div className="p-2.5 bg-slate-50 border-b border-slate-200 space-y-2">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search 14 tests by name, code (e.g. L-HB), or type (POCT / Hub)..."
                  className="w-full pl-9 pr-8 py-2 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                  data-testid="lab-test-search-input"
                />
                {query && (
                  <button
                    type="button"
                    onClick={() => setQuery('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Category & Tier Quick Filters */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] scrollbar-thin">
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter('ALL')}
                  className={`px-2 py-0.5 rounded-full font-bold transition whitespace-nowrap ${
                    activeCategoryFilter === 'ALL'
                      ? 'bg-teal-600 text-white shadow-xs'
                      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  All ({availableTests.length})
                </button>

                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter('POCT')}
                  className={`px-2 py-0.5 rounded-full font-bold flex items-center gap-1 transition whitespace-nowrap ${
                    activeCategoryFilter === 'POCT'
                      ? 'bg-emerald-600 text-white shadow-xs'
                      : 'bg-white text-emerald-800 border border-emerald-200 hover:bg-emerald-50'
                  }`}
                >
                  <span>🧪 POCT Rapid ({poctCount})</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter('HUB')}
                  className={`px-2 py-0.5 rounded-full font-bold flex items-center gap-1 transition whitespace-nowrap ${
                    activeCategoryFilter === 'HUB'
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-white text-blue-800 border border-blue-200 hover:bg-blue-50'
                  }`}
                >
                  <span>🏥 Hub Lab ({hubCount})</span>
                </button>

                {selectedIds.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setActiveCategoryFilter('SELECTED')}
                    className={`px-2 py-0.5 rounded-full font-bold transition whitespace-nowrap ${
                      activeCategoryFilter === 'SELECTED'
                        ? 'bg-purple-600 text-white shadow-xs'
                        : 'bg-white text-purple-800 border border-purple-200 hover:bg-purple-50'
                    }`}
                  >
                    Selected ({selectedIds.length})
                  </button>
                )}

                {availableCategories.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setActiveCategoryFilter(cat)}
                    className={`px-2 py-0.5 rounded-full font-medium transition whitespace-nowrap ${
                      activeCategoryFilter.toLowerCase() === cat.toLowerCase()
                        ? 'bg-slate-800 text-white'
                        : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Test Selection List */}
            <div className="overflow-y-auto max-h-64 divide-y divide-slate-100 p-1.5 space-y-1">
              {filteredTests.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500">
                  <p className="font-semibold">No diagnostic tests matching your search.</p>
                  <p className="text-[11px] text-slate-400 mt-1">Try clearing your search query or filter tags.</p>
                </div>
              ) : (
                filteredTests.map((test) => {
                  const isSelected = selectedIds.includes(test.id);
                  const isPoct = isPoctTest(test);

                  return (
                    <div
                      key={test.id}
                      onClick={() => handleToggleTest(test.id)}
                      data-testid={`lab-test-option-${test.id}`}
                      className={`p-2.5 rounded-lg flex items-center justify-between gap-3 cursor-pointer transition select-none ${
                        isSelected
                          ? 'bg-teal-50/80 border border-teal-400/80 text-teal-950 font-medium'
                          : 'hover:bg-slate-50 border border-transparent text-slate-800'
                      }`}
                    >
                      {/* Checkbox & Test Info */}
                      <div className="flex items-start gap-2.5 min-w-0 flex-1">
                        <div
                          className={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center shrink-0 transition ${
                            isSelected
                              ? 'bg-teal-600 border-teal-600 text-white'
                              : 'border-slate-300 bg-white hover:border-slate-400'
                          }`}
                        >
                          {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-bold text-slate-900">
                              {test.name}
                            </span>
                            <span
                              className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${
                                isPoct
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {test.code}
                            </span>
                          </div>

                          <div className="flex items-center gap-2 mt-0.5 flex-wrap text-[11px]">
                            {/* POCT or Hub Lab Indicator */}
                            <span
                              className={`inline-flex items-center gap-0.5 text-[10px] font-bold px-1.5 py-0.2 rounded-full ${
                                isPoct
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : 'bg-blue-50 text-blue-700 border border-blue-200'
                              }`}
                            >
                              {isPoct ? '🧪 POCT Rapid' : '🏥 Hub Lab'}
                            </span>

                            {test.category && (
                              <span className="text-slate-500 font-medium">
                                Category: {test.category}
                              </span>
                            )}

                            {test.reference_range && (
                              <span className="text-slate-400 text-[10px] truncate">
                                • Ref: {test.reference_range} {test.unit ? `(${test.unit})` : ''}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Status indicator on the right */}
                      <div className="shrink-0 text-right">
                        {isSelected ? (
                          <span className="text-[11px] font-bold text-teal-700 flex items-center gap-1 bg-teal-100/80 px-2 py-0.5 rounded-md">
                            <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
                            Ordered
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-400 group-hover:text-slate-600">
                            + Add
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Bottom Footer Actions */}
            <div className="p-2.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between flex-wrap gap-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-700">
                  {selectedIds.length} of {availableTests.length} tests selected
                </span>
                {filteredTests.length > 0 && (
                  <button
                    type="button"
                    onClick={handleSelectAllVisible}
                    className="text-teal-700 hover:text-teal-800 font-bold text-[11px] underline"
                  >
                    Select visible ({filteredTests.length})
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg shadow-sm transition"
                  data-testid="lab-test-done-button"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
