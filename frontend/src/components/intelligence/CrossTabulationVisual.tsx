import React, { useState, useMemo } from 'react';
import { HelpCircle } from 'lucide-react';
import type { SeasonalityData } from '../../types/intelligence';

interface CrossTabulationVisualProps {
  seasonalityData: SeasonalityData | null;
}

const AGE_GROUPS_ALL = ['0-5', '6-14', '15-24', '25-44', '45-59', '60+'];
const GENDERS_ALL = ['MALE', 'FEMALE', 'OTHER'];

export const CrossTabulationVisual: React.FC<CrossTabulationVisualProps> = ({ seasonalityData }) => {
  const [selectedSeverity, setSelectedSeverity] = useState<'MILD' | 'MODERATE' | 'SEVERE'>('MILD');
  const [selectedVulnerability, setSelectedVulnerability] = useState<string>('PREGNANT');

  // Check if UNKNOWN age group has any cases in matrix
  const hasUnknownAge = useMemo(() => {
    const matrix = seasonalityData?.seasonal_age_gender;
    if (!matrix?.['UNKNOWN']) return false;
    return Object.values(matrix['UNKNOWN']).some(c => (c?.total_cases ?? 0) > 0);
  }, [seasonalityData]);

  const activeAgeGroups = useMemo(() => {
    return hasUnknownAge ? [...AGE_GROUPS_ALL, 'UNKNOWN'] : AGE_GROUPS_ALL;
  }, [hasUnknownAge]);

  // Check if UNKNOWN gender has any cases
  const hasUnknownGender = useMemo(() => {
    const matrix = seasonalityData?.seasonal_age_gender;
    if (!matrix) return false;
    for (const ag of activeAgeGroups) {
      if ((matrix[ag]?.['UNKNOWN']?.total_cases ?? 0) > 0) return true;
    }
    return false;
  }, [seasonalityData, activeAgeGroups]);

  const activeGenders = useMemo(() => {
    return hasUnknownGender ? [...GENDERS_ALL, 'UNKNOWN'] : GENDERS_ALL;
  }, [hasUnknownGender]);

  // 10. Base Age × Gender Matrix counts & max cell value
  const { ageGenderCells, maxAgeGenderCount, totalHeatmapCases } = useMemo(() => {
    const matrix = seasonalityData?.seasonal_age_gender;
    let maxVal = 0;
    let total = 0;
    const cells: Record<string, Record<string, number>> = {};

    activeAgeGroups.forEach(ag => {
      cells[ag] = {};
      activeGenders.forEach(g => {
        const cnt = matrix?.[ag]?.[g]?.total_cases ?? 0;
        cells[ag][g] = cnt;
        if (cnt > maxVal) maxVal = cnt;
        total += cnt;
      });
    });

    return { ageGenderCells: cells, maxAgeGenderCount: maxVal, totalHeatmapCases: total };
  }, [seasonalityData, activeAgeGroups, activeGenders]);

  // Color intensity helper
  const getCellBgClass = (cnt: number, max: number) => {
    if (cnt === 0 || max === 0) return 'bg-slate-50 text-slate-400';
    const ratio = cnt / max;
    if (ratio < 0.25) return 'bg-indigo-100 text-indigo-900 font-semibold';
    if (ratio < 0.5) return 'bg-indigo-200 text-indigo-950 font-bold';
    if (ratio < 0.75) return 'bg-indigo-400 text-white font-black';
    return 'bg-indigo-600 text-white font-black';
  };

  // 11. Age × Gender × Severity Matrix
  const severityMatrix = useMemo(() => {
    const multiMatrix = seasonalityData?.seasonal_age_gender_severity;
    let maxVal = 0;
    const cells: Record<string, Record<string, number>> = {};

    activeAgeGroups.forEach(ag => {
      cells[ag] = {};
      activeGenders.forEach(g => {
        const cnt = multiMatrix?.[ag]?.[g]?.[selectedSeverity]?.total_cases ?? 0;
        cells[ag][g] = cnt;
        if (cnt > maxVal) maxVal = cnt;
      });
    });

    return { cells, maxVal };
  }, [seasonalityData, activeAgeGroups, activeGenders, selectedSeverity]);

  // 12. Age × Gender × Vulnerability Matrix
  const vulnerabilityMatrix = useMemo(() => {
    const multiMatrix = seasonalityData?.seasonal_age_gender_vulnerability;
    let maxVal = 0;
    const cells: Record<string, Record<string, number>> = {};

    activeAgeGroups.forEach(ag => {
      cells[ag] = {};
      activeGenders.forEach(g => {
        const cnt = multiMatrix?.[ag]?.[g]?.[selectedVulnerability]?.total_cases ?? 0;
        cells[ag][g] = cnt;
        if (cnt > maxVal) maxVal = cnt;
      });
    });

    return { cells, maxVal };
  }, [seasonalityData, activeAgeGroups, activeGenders, selectedVulnerability]);

  // 13. New vs Follow-up Comparison
  const patientTypeComparison = useMemo(() => {
    const list = seasonalityData?.seasonal_patient_types || [];
    const newCases = list.find(p => p.patient_type === 'NEW')?.total_cases ?? 0;
    const followUpCases = list.find(p => p.patient_type === 'FOLLOW_UP')?.total_cases ?? 0;
    const total = newCases + followUpCases;
    const newPct = total > 0 ? ((newCases / total) * 100).toFixed(0) : '0';
    const followUpPct = total > 0 ? ((followUpCases / total) * 100).toFixed(0) : '0';
    return { newCases, followUpCases, total, newPct, followUpPct };
  }, [seasonalityData]);

  return (
    <div className="space-y-6" data-testid="crosstab-section">
      {/* Section 10: 🔲 Age & Gender Distribution (Heatmap) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="age-gender-heatmap-card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>🔲 Age & Gender Distribution</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Cross-tabulation heatmap of case volumes across demographic cohorts.
            </p>
          </div>
          {/* Scale Legend */}
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-600">
            <span>0</span>
            <span className="w-5 h-3.5 rounded bg-slate-100 border border-slate-200" />
            <span className="w-5 h-3.5 rounded bg-indigo-100" />
            <span className="w-5 h-3.5 rounded bg-indigo-300" />
            <span className="w-5 h-3.5 rounded bg-indigo-600" />
            <span>{maxAgeGenderCount}</span>
          </div>
        </div>

        {totalHeatmapCases === 0 ? (
          <div className="h-40 flex flex-col items-center justify-center text-slate-400 text-xs">
            <HelpCircle className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
            <span>No cases found in this cross-tabulation matrix.</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-center text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-600 font-bold">
                  <th className="p-3 text-left w-24">Age Bracket</th>
                  {activeGenders.map(g => (
                    <th key={g} className="p-3">
                      {g === 'MALE' ? 'Male' : g === 'FEMALE' ? 'Female' : g === 'OTHER' ? 'Other' : 'Unknown'}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {activeAgeGroups.map(ag => (
                  <tr key={ag} className="hover:bg-slate-50/50 transition">
                    <td className="p-3 text-left font-bold text-slate-800 font-mono">{ag}</td>
                    {activeGenders.map(g => {
                      const count = ageGenderCells[ag]?.[g] ?? 0;
                      return (
                        <td key={g} className="p-2">
                          <div
                            className={`py-2 px-3 rounded-lg transition-colors duration-150 ${getCellBgClass(
                              count,
                              maxAgeGenderCount
                            )}`}
                          >
                            {count}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <p className="text-xs text-slate-500 font-medium">
          Dark/stronger cells indicate more reported cases.
        </p>
      </div>

      {/* Row 2: Age × Gender × Severity and Age × Gender × Vulnerability */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Section 11: Age, Gender & Severity */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="age-gender-severity-card">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Age, Gender & Severity
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Demographic matrix segmented by patient severity.
              </p>
            </div>

            {/* Severity Tabs */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
              {(['MILD', 'MODERATE', 'SEVERE'] as const).map(sev => (
                <button
                  key={sev}
                  onClick={() => setSelectedSeverity(sev)}
                  className={`px-3 py-1 rounded-lg font-bold transition cursor-pointer ${
                    selectedSeverity === sev
                      ? 'bg-white text-slate-900 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {sev === 'MILD' ? 'Mild' : sev === 'MODERATE' ? 'Moderate' : 'Severe'}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-center text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-600 font-bold">
                  <th className="p-2.5 text-left w-20">Age</th>
                  {activeGenders.map(g => (
                    <th key={g} className="p-2.5">
                      {g === 'MALE' ? 'Male' : g === 'FEMALE' ? 'Female' : g === 'OTHER' ? 'Other' : 'Unknown'}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {activeAgeGroups.map(ag => (
                  <tr key={ag}>
                    <td className="p-2.5 text-left font-bold text-slate-800 font-mono">{ag}</td>
                    {activeGenders.map(g => {
                      const count = severityMatrix.cells[ag]?.[g] ?? 0;
                      return (
                        <td key={g} className="p-1.5">
                          <div
                            className={`py-1.5 px-2 rounded-md ${getCellBgClass(
                              count,
                              severityMatrix.maxVal
                            )}`}
                          >
                            {count}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 12: Age, Gender & Vulnerability */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="age-gender-vulnerability-card">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Age, Gender & Vulnerability
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Demographic matrix segmented by vulnerable group.
              </p>
            </div>

            {/* Vulnerability Dropdown/Selector */}
            <select
              value={selectedVulnerability}
              onChange={e => setSelectedVulnerability(e.target.value)}
              className="text-xs font-semibold bg-slate-50 border border-slate-300 rounded-xl px-2.5 py-1 text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="PREGNANT">Pregnant</option>
              <option value="ELDERLY">Elderly</option>
              <option value="DISABILITY">Disability</option>
              <option value="CHRONIC_CONDITION">Chronic Condition</option>
              <option value="LOW_INCOME_SLUM">Low Income / Slum</option>
              <option value="GENERAL">General</option>
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-center text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-600 font-bold">
                  <th className="p-2.5 text-left w-20">Age</th>
                  {activeGenders.map(g => (
                    <th key={g} className="p-2.5">
                      {g === 'MALE' ? 'Male' : g === 'FEMALE' ? 'Female' : g === 'OTHER' ? 'Other' : 'Unknown'}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {activeAgeGroups.map(ag => (
                  <tr key={ag}>
                    <td className="p-2.5 text-left font-bold text-slate-800 font-mono">{ag}</td>
                    {activeGenders.map(g => {
                      const count = vulnerabilityMatrix.cells[ag]?.[g] ?? 0;
                      return (
                        <td key={g} className="p-1.5">
                          <div
                            className={`py-1.5 px-2 rounded-md ${getCellBgClass(
                              count,
                              vulnerabilityMatrix.maxVal
                            )}`}
                          >
                            {count}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Section 13: 🔄 New vs Follow-up Cases Comparison */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="new-vs-followup-card">
        <div className="pb-3 border-b border-slate-100">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>🔄 New vs Follow-up Cases</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Direct comparison of primary diagnosed presentations versus ongoing clinical follow-ups.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-200 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-bold text-indigo-700 uppercase tracking-wider block">
                New Cases
              </span>
              <span className="text-3xl font-black text-indigo-950 mt-1 block">
                {patientTypeComparison.newCases}
              </span>
            </div>
            <div className="mt-3">
              <div className="flex justify-between text-xs font-semibold text-indigo-900 mb-1">
                <span>Share: {patientTypeComparison.newPct}%</span>
              </div>
              <div className="w-full bg-indigo-100 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-indigo-600 h-2 rounded-full"
                  style={{ width: `${patientTypeComparison.newPct}%` }}
                />
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-cyan-50/70 border border-cyan-200 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-bold text-cyan-800 uppercase tracking-wider block">
                Follow-up Cases
              </span>
              <span className="text-3xl font-black text-cyan-950 mt-1 block">
                {patientTypeComparison.followUpCases}
              </span>
            </div>
            <div className="mt-3">
              <div className="flex justify-between text-xs font-semibold text-cyan-900 mb-1">
                <span>Share: {patientTypeComparison.followUpPct}%</span>
              </div>
              <div className="w-full bg-cyan-100 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-cyan-600 h-2 rounded-full"
                  style={{ width: `${patientTypeComparison.followUpPct}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
