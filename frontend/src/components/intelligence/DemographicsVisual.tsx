import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { Info, HelpCircle } from 'lucide-react';
import type {
  SeasonalityData,
  HistoricalDiseaseResponse
} from '../../types/intelligence';

interface DemographicsVisualProps {
  seasonalityData: SeasonalityData | null;
  historicalData: HistoricalDiseaseResponse | null;
}

const GENDER_COLORS: Record<string, string> = {
  Male: '#3b82f6',
  Female: '#ec4899',
  Other: '#8b5cf6',
  Unknown: '#94a3b8',
};

const PATIENT_TYPE_COLORS: Record<string, string> = {
  New: '#6366f1',
  'Follow-up': '#06b6d4',
  Unknown: '#94a3b8',
};

export const DemographicsVisual: React.FC<DemographicsVisualProps> = ({
  seasonalityData,
  historicalData
}) => {
  // 1. Age Distribution Data: 0-5, 6-14, 15-24, 25-44, 45-59, 60+, UNKNOWN (only if > 0)
  const ageData = useMemo(() => {
    const list = seasonalityData?.seasonal_age_groups || [];
    if (list.length === 0) return [];
    const standardOrder = ['0-5', '6-14', '15-24', '25-44', '45-59', '60+'];
    const map = new Map<string, number>();
    list.forEach(item => map.set(item.age_group, item.total_cases));

    const result = standardOrder.map(ag => ({
      age_group: ag,
      cases: map.get(ag) ?? 0,
    }));

    const unknownCount = map.get('UNKNOWN') ?? 0;
    if (unknownCount > 0) {
      result.push({ age_group: 'UNKNOWN', cases: unknownCount });
    }

    return result;
  }, [seasonalityData]);

  const topAgeGroup = useMemo(() => {
    if (ageData.length === 0) return null;
    const sorted = [...ageData].sort((a, b) => b.cases - a.cases);
    return sorted[0]?.cases > 0 ? sorted[0] : null;
  }, [ageData]);

  // 2. Gender Distribution Data
  const genderData = useMemo(() => {
    const list = seasonalityData?.seasonal_gender || [];
    if (list.length === 0) return [];
    return list
      .map(item => {
        const name =
          item.gender === 'MALE'
            ? 'Male'
            : item.gender === 'FEMALE'
            ? 'Female'
            : item.gender === 'OTHER'
            ? 'Other'
            : 'Unknown';
        return {
          name,
          rawGender: item.gender,
          value: item.total_cases,
        };
      })
      .filter(g => g.name !== 'Unknown' || g.value > 0);
  }, [seasonalityData]);

  const totalGenderCases = useMemo(() => {
    return genderData.reduce((acc, item) => acc + item.value, 0);
  }, [genderData]);

  const topGender = useMemo(() => {
    if (genderData.length === 0) return null;
    const sorted = [...genderData].sort((a, b) => b.value - a.value);
    return sorted[0]?.value > 0 ? sorted[0] : null;
  }, [genderData]);

  // 3. Clinical Severity Data: MILD, MODERATE, SEVERE
  const severityData = useMemo(() => {
    if (seasonalityData?.seasonal_severity && seasonalityData.seasonal_severity.length > 0) {
      const map = new Map<string, number>();
      seasonalityData.seasonal_severity.forEach(s => map.set(s.severity, s.total_cases));
      return {
        MILD: map.get('MILD') ?? 0,
        MODERATE: map.get('MODERATE') ?? 0,
        SEVERE: map.get('SEVERE') ?? 0,
      };
    }

    // Fallback from multi-month historical series if available
    if (historicalData?.historical_series && historicalData.historical_series.length > 0) {
      let mild = 0, mod = 0, sev = 0;
      historicalData.historical_series.forEach(pt => {
        mild += pt.severity_breakdown?.MILD ?? 0;
        mod += pt.severity_breakdown?.MODERATE ?? 0;
        sev += pt.severity_breakdown?.SEVERE ?? 0;
      });
      return { MILD: mild, MODERATE: mod, SEVERE: sev };
    }

    return { MILD: 0, MODERATE: 0, SEVERE: 0 };
  }, [seasonalityData, historicalData]);

  const totalSeverityCases = severityData.MILD + severityData.MODERATE + severityData.SEVERE;

  const topSeverity = useMemo(() => {
    if (totalSeverityCases === 0) return null;
    if (severityData.SEVERE >= severityData.MODERATE && severityData.SEVERE >= severityData.MILD && severityData.SEVERE > 0) {
      return { name: 'Severe', level: 'SEVERE', count: severityData.SEVERE };
    }
    if (severityData.MODERATE >= severityData.MILD && severityData.MODERATE > 0) {
      return { name: 'Moderate', level: 'MODERATE', count: severityData.MODERATE };
    }
    if (severityData.MILD > 0) {
      return { name: 'Mild', level: 'MILD', count: severityData.MILD };
    }
    return null;
  }, [severityData, totalSeverityCases]);

  // 4. Vulnerable Population Data
  const vulnerableData = useMemo(() => {
    const list = seasonalityData?.seasonal_vulnerable_groups || [];
    if (list.length === 0) return [];
    return list.map(item => {
      const label =
        item.vulnerable_group === 'PREGNANT'
          ? 'Pregnant'
          : item.vulnerable_group === 'ELDERLY'
          ? 'Elderly'
          : item.vulnerable_group === 'DISABILITY'
          ? 'Disability'
          : item.vulnerable_group === 'CHRONIC_CONDITION'
          ? 'Chronic Condition'
          : item.vulnerable_group === 'LOW_INCOME_SLUM'
          ? 'Low Income / Slum'
          : item.vulnerable_group === 'GENERAL'
          ? 'General'
          : 'Unknown';
      return {
        label,
        rawGroup: item.vulnerable_group,
        cases: item.total_cases,
      };
    });
  }, [seasonalityData]);

  const topVulnerable = useMemo(() => {
    if (vulnerableData.length === 0) return null;
    const sorted = [...vulnerableData].sort((a, b) => b.cases - a.cases);
    return sorted[0]?.cases > 0 ? sorted[0] : null;
  }, [vulnerableData]);

  // 5. Patient Type Data: New vs Follow-up
  const patientTypeData = useMemo(() => {
    const list = seasonalityData?.seasonal_patient_types || [];
    if (list.length === 0) return [];
    return list
      .map(item => ({
        name: item.patient_type === 'NEW' ? 'New' : item.patient_type === 'FOLLOW_UP' ? 'Follow-up' : 'Unknown',
        rawType: item.patient_type,
        value: item.total_cases,
      }))
      .filter(p => p.name !== 'Unknown' || p.value > 0);
  }, [seasonalityData]);

  const totalPatientTypeCases = useMemo(() => {
    return patientTypeData.reduce((acc, item) => acc + item.value, 0);
  }, [patientTypeData]);

  return (
    <div className="space-y-6" data-testid="demographics-section">
      {/* Row 1: Age Distribution & Gender Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Section 5: 👥 Age Distribution */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="age-distribution-card">
          <div className="pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>👥 Age Distribution</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Shows reported cases across standard epidemiological age brackets.
            </p>
          </div>

          <div className="h-64 sm:h-72 w-full pt-1" data-testid="age-distribution-chart-container">
            {ageData.length === 0 || ageData.every(d => d.cases === 0) ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <HelpCircle className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                <span>No age demographic records found for the selected filters.</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={240}>
                <BarChart
                  layout="vertical"
                  data={ageData}
                  margin={{ top: 10, right: 30, left: 20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                  <XAxis
                    type="number"
                    allowDecimals={false}
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    axisLine={{ stroke: '#cbd5e1' }}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="age_group"
                    tick={{ fontSize: 11, fill: '#1e293b', fontWeight: 600 }}
                    axisLine={false}
                    tickLine={false}
                    width={55}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '0.75rem',
                      border: 'none',
                      color: '#f8fafc',
                      fontSize: '12px'
                    }}
                    formatter={(val: any) => [`${val} cases`, 'Reported Cases']}
                  />
                  <Bar
                    dataKey="cases"
                    name="Cases"
                    fill="#3b82f6"
                    radius={[0, 6, 6, 0]}
                    label={{ position: 'right', fill: '#475569', fontSize: 11, fontWeight: 700 }}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {topAgeGroup && (
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
              <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-900 mr-1">💡 What this means:</span>
                <span>
                  Most cases are in the <strong>{topAgeGroup.age_group}</strong> group ({topAgeGroup.cases} cases).
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Section 6: Gender Distribution */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="gender-distribution-card">
          <div className="pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>Gender Distribution</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Distribution of patient presentations across recorded genders.
            </p>
          </div>

          <div className="h-64 sm:h-72 w-full flex items-center justify-center">
            {genderData.length === 0 || totalGenderCases === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <HelpCircle className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                <span>No gender demographic records available.</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={240}>
                <PieChart>
                  <Pie
                    data={genderData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                    nameKey="name"
                  >
                    {genderData.map(entry => (
                      <Cell
                        key={`cell-${entry.name}`}
                        fill={GENDER_COLORS[entry.name] || '#94a3b8'}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '0.75rem',
                      border: 'none',
                      color: '#f8fafc',
                      fontSize: '12px'
                    }}
                    formatter={(val: any) => {
                      const pct = totalGenderCases > 0 ? ((Number(val) / totalGenderCases) * 100).toFixed(1) : '0';
                      return [`${val} cases (${pct}%)`, 'Count & Percentage'];
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    align="center"
                    wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {topGender && (
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
              <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-900 mr-1">💡 What this means:</span>
                <span>
                  Highest reported cases are among <strong>{topGender.name}</strong> patients ({topGender.value} cases).
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Row 2: Case Severity & Vulnerable Population */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Section 7: 🩺 Case Severity */}
        <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="case-severity-section">
          <div className="pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>🩺 Case Severity</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Clinical classification of patient disease severity levels.
            </p>
          </div>

          {/* Severity Cards */}
          <div className="grid grid-cols-3 gap-3">
            {/* Mild */}
            <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 text-center flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-extrabold text-emerald-800 uppercase tracking-wider block">
                  MILD
                </span>
                <span className="text-2xl font-black text-emerald-950 mt-1 block">
                  {severityData.MILD}
                </span>
              </div>
              <span className="text-[10px] text-emerald-700 font-medium mt-2">
                {totalSeverityCases > 0 ? `${((severityData.MILD / totalSeverityCases) * 100).toFixed(0)}% of total` : '0%'}
              </span>
            </div>

            {/* Moderate */}
            <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-center flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-extrabold text-amber-800 uppercase tracking-wider block">
                  MODERATE
                </span>
                <span className="text-2xl font-black text-amber-950 mt-1 block">
                  {severityData.MODERATE}
                </span>
              </div>
              <span className="text-[10px] text-amber-700 font-medium mt-2">
                {totalSeverityCases > 0 ? `${((severityData.MODERATE / totalSeverityCases) * 100).toFixed(0)}% of total` : '0%'}
              </span>
            </div>

            {/* Severe */}
            <div className="p-4 rounded-xl bg-rose-50/80 border-2 border-rose-300 text-center flex flex-col justify-between shadow-2xs">
              <div>
                <span className="text-[10px] font-extrabold text-rose-900 uppercase tracking-wider block">
                  SEVERE
                </span>
                <span className="text-2xl font-black text-rose-950 mt-1 block">
                  {severityData.SEVERE}
                </span>
              </div>
              <span className="text-[10px] text-rose-800 font-bold mt-2">
                {totalSeverityCases > 0 ? `${((severityData.SEVERE / totalSeverityCases) * 100).toFixed(0)}% of total` : '0%'}
              </span>
            </div>
          </div>

          {topSeverity && (
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
              <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-900 mr-1">💡 What this means:</span>
                <span>
                  Most reported cases are <strong>{topSeverity.name}</strong> ({topSeverity.count} cases).
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Section 8: 🤝 Vulnerable Population */}
        <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="vulnerable-population-section">
          <div className="pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>🤝 Vulnerable Population</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Breakdown across identified vulnerable cohorts requiring prioritized intervention.
            </p>
          </div>

          {vulnerableData.length === 0 ? (
            <div className="h-40 flex flex-col items-center justify-center text-slate-400 text-xs">
              <HelpCircle className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
              <span>No vulnerable cohort records available.</span>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {vulnerableData.map(v => (
                <div
                  key={v.rawGroup}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between"
                >
                  <span className="text-[11px] font-bold text-slate-600 block">{v.label}</span>
                  <span className="text-lg font-black text-slate-900 mt-1 block">{v.cases}</span>
                </div>
              ))}
            </div>
          )}

          {topVulnerable && (
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
              <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-900 mr-1">💡 What this means:</span>
                <span>
                  Most cases in vulnerable groups are <strong>{topVulnerable.label}</strong> ({topVulnerable.cases} cases).
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Row 3: Section 9: Patient Type */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="patient-type-section">
        <div className="pb-3 border-b border-slate-100">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>Patient Type</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Distribution between initial diagnostic presentations and recurring follow-up consultations.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-12 gap-5 items-center">
          <div className="sm:col-span-5 h-56 flex items-center justify-center">
            {patientTypeData.length === 0 || totalPatientTypeCases === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <HelpCircle className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                <span>No patient type records available.</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={200}>
                <PieChart>
                  <Pie
                    data={patientTypeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="value"
                    nameKey="name"
                  >
                    {patientTypeData.map(entry => (
                      <Cell
                        key={`pt-cell-${entry.name}`}
                        fill={PATIENT_TYPE_COLORS[entry.name] || '#94a3b8'}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '0.75rem',
                      border: 'none',
                      color: '#f8fafc',
                      fontSize: '12px'
                    }}
                    formatter={(val: any, name: any) => {
                      const pct = totalPatientTypeCases > 0 ? ((Number(val) / totalPatientTypeCases) * 100).toFixed(1) : '0';
                      return [`${name}: ${val} cases (${pct}%)`, 'Consultation Volume'];
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    align="center"
                    wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="sm:col-span-7 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-200">
                <span className="text-[10px] font-extrabold text-indigo-700 uppercase tracking-wider block">
                  New Diagnoses
                </span>
                <span className="text-2xl font-black text-indigo-950 mt-1 block">
                  {patientTypeData.find(p => p.rawType === 'NEW')?.value ?? 0}
                </span>
                <span className="text-[11px] text-indigo-700 font-medium mt-1 block">
                  First-time disease reports
                </span>
              </div>

              <div className="p-4 rounded-xl bg-cyan-50/70 border border-cyan-200">
                <span className="text-[10px] font-extrabold text-cyan-800 uppercase tracking-wider block">
                  Follow-Up Visits
                </span>
                <span className="text-2xl font-black text-cyan-950 mt-1 block">
                  {patientTypeData.find(p => p.rawType === 'FOLLOW_UP')?.value ?? 0}
                </span>
                <span className="text-[11px] text-cyan-700 font-medium mt-1 block">
                  Continuing treatment consultations
                </span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
              <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-900 mr-1">💡 What this means:</span>
                <span>
                  New cases represent primary transmission detection, while follow-up cases reflect treatment management and retention.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
