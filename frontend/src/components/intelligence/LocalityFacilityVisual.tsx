import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';
import {
  MapPin,
  Building2,
  Search,
  HelpCircle,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import type {
  DiseaseLocalityResponse,
  DistrictAggregationResponse,
  TrendDirection
} from '../../types/intelligence';

interface LocalityFacilityVisualProps {
  localityData: DiseaseLocalityResponse | null;
  districtAggData: DistrictAggregationResponse | null;
  isDistrictOfficer: boolean;
}

export const LocalityFacilityVisual: React.FC<LocalityFacilityVisualProps> = ({
  localityData,
  districtAggData,
  isDistrictOfficer
}) => {
  const [localitySearch, setLocalitySearch] = useState<string>('');

  const filteredLocalities = useMemo(() => {
    const list = localityData?.locality_aggregations || [];
    if (!localitySearch.trim()) return list;
    return list.filter(l => l.locality.name.toLowerCase().includes(localitySearch.toLowerCase()));
  }, [localityData?.locality_aggregations, localitySearch]);

  // Ranked localities for horizontal bar chart (top 6)
  const rankedLocalities = useMemo(() => {
    const list = localityData?.locality_aggregations || [];
    return [...list]
      .sort((a, b) => b.current_cases - a.current_cases)
      .slice(0, 6)
      .map(loc => ({
        name: loc.locality.name || 'Unknown Locality',
        cases: loc.current_cases,
        share: loc.locality_share_pct,
      }));
  }, [localityData?.locality_aggregations]);

  // Ranked hospital comparison data for district officer
  const rankedHospitals = useMemo(() => {
    const list = districtAggData?.hospital_comparison || [];
    return [...list]
      .sort((a, b) => b.cases_reported - a.cases_reported)
      .map(h => ({
        name: h.hospital_name,
        code: h.hospital_code,
        cases: h.cases_reported,
        type: h.facility_type,
      }));
  }, [districtAggData?.hospital_comparison]);

  const renderTrendBadge = (direction: TrendDirection | string | undefined) => {
    switch (direction) {
      case 'INCREASING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-rose-100 text-rose-800 border border-rose-300">
            <TrendingUp className="w-3 h-3 text-rose-700" />
            INCREASING
          </span>
        );
      case 'DECREASING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <TrendingDown className="w-3 h-3 text-emerald-700" />
            DECREASING
          </span>
        );
      case 'POSSIBLE_INCREASE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-amber-100 text-amber-900 border border-amber-300">
            <TrendingUp className="w-3 h-3 text-amber-700" />
            POSSIBLE INCREASE
          </span>
        );
      case 'NORMAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-blue-100 text-blue-800 border border-blue-300">
            <Minus className="w-3 h-3 text-blue-700" />
            NORMAL
          </span>
        );
      case 'INSUFFICIENT_DATA':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-slate-100 text-slate-700 border border-slate-300">
            <HelpCircle className="w-3 h-3 text-slate-500" />
            INSUFFICIENT DATA
          </span>
        );
    }
  };

  const renderPercentageBadge = (pct: number | null | undefined) => {
    if (pct === null || pct === undefined) {
      return <span className="text-slate-400 font-mono text-xs">Baseline 0</span>;
    }
    const isPositive = pct > 0;
    const isZero = pct === 0;
    return (
      <span
        className={`font-mono font-bold text-xs ${
          isZero ? 'text-slate-600' : isPositive ? 'text-rose-600' : 'text-emerald-600'
        }`}
      >
        {isPositive ? `+${pct}%` : `${pct}%`}
      </span>
    );
  };

  return (
    <div className="space-y-6" data-testid="locality-facility-section">
      {/* Section 18: 📍 Case Concentration by Locality */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-rose-600" />
              <span>📍 Case Concentration by Locality</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Cases distributed across urban wards, slum pockets, and reporting hospitals.
            </p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter localities..."
              value={localitySearch}
              onChange={e => setLocalitySearch(e.target.value)}
              className="w-full text-xs pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Visual Ranking Bar Chart (if data exists) */}
        {rankedLocalities.length > 0 && (
          <div className="p-5 border-b border-slate-100 bg-white">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Top Ranked Localities by Case Volume
            </h4>
            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={180}>
                <BarChart
                  layout="vertical"
                  data={rankedLocalities}
                  margin={{ top: 5, right: 30, left: 30, bottom: 0 }}
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
                    dataKey="name"
                    tick={{ fontSize: 11, fill: '#1e293b', fontWeight: 600 }}
                    axisLine={false}
                    tickLine={false}
                    width={110}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '0.75rem',
                      border: 'none',
                      color: '#f8fafc',
                      fontSize: '12px'
                    }}
                    formatter={(val: any) => [`${val} cases`, 'Reported Volume']}
                  />
                  <Bar
                    dataKey="cases"
                    fill="#f43f5e"
                    radius={[0, 6, 6, 0]}
                    label={{ position: 'right', fill: '#475569', fontSize: 11, fontWeight: 700 }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Locality Table View */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Locality / Ward</th>
                <th className="p-4 text-center">Current Cases</th>
                <th className="p-4 text-center">Previous</th>
                <th className="p-4 text-center">Change %</th>
                <th className="p-4">Locality Share</th>
                <th className="p-4 text-center">Trend Signal</th>
                <th className="p-4">Reporting Hospitals</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredLocalities.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400 font-medium">
                    No locality case concentrations observed in this window.
                  </td>
                </tr>
              ) : (
                filteredLocalities.map((loc, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80 transition">
                    <td className="p-4">
                      <div className="font-bold text-slate-900 flex items-center gap-2">
                        {loc.locality.ward_id === null ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                            Unknown Locality
                          </span>
                        ) : (
                          <span>{loc.locality.name}</span>
                        )}
                      </div>
                      {loc.locality.zone && (
                        <span className="text-[10px] text-slate-500 block mt-0.5">
                          Zone: {loc.locality.zone} {loc.locality.ward_number ? `• Ward #${loc.locality.ward_number}` : ''}
                        </span>
                      )}
                    </td>
                    <td className="p-4 text-center font-bold text-slate-900 text-sm">
                      {loc.current_cases}
                    </td>
                    <td className="p-4 text-center text-slate-600">
                      {loc.previous_period_cases}
                    </td>
                    <td className="p-4 text-center">
                      {renderPercentageBadge(loc.percentage_change)}
                    </td>
                    <td className="p-4 min-w-[140px]">
                      <div className="flex items-center justify-between text-[11px] font-bold text-slate-700 mb-1">
                        <span>{loc.locality_share_pct}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-indigo-600 h-1.5 rounded-full"
                          style={{ width: `${Math.min(100, loc.locality_share_pct)}%` }}
                        />
                      </div>
                    </td>
                    <td className="p-4 text-center">
                      {renderTrendBadge(loc.trend_direction)}
                    </td>
                    <td className="p-4">
                      <div className="flex flex-wrap gap-1">
                        {loc.reporting_hospitals.map((h, hIdx) => (
                          <span
                            key={hIdx}
                            className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-medium border border-slate-200"
                            title={`Reported ${h.cases_reported} cases`}
                          >
                            {h.hospital_name} ({h.cases_reported})
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 17: 🏥 Facility Comparison & 📍 District Comparison (District Officer Scope) */}
      {isDistrictOfficer && districtAggData && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden" data-testid="facility-comparison-section">
          <div className="p-5 border-b border-slate-100 bg-slate-50/50">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-emerald-600" />
              <span>🏥 Facility Comparison — District Hospital Case Comparison ({districtAggData.district.name})</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Comparative disease reporting volume across all authorized facilities within {districtAggData.district.name}.
            </p>
          </div>

          {/* Ranked Hospital Bar Chart */}
          {rankedHospitals.length > 0 && (
            <div className="p-5 border-b border-slate-100 bg-white">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Facility Case Reporting Volume (Ranked)
              </h4>
              <div className="h-52 w-full">
                <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={180}>
                  <BarChart
                    layout="vertical"
                    data={rankedHospitals}
                    margin={{ top: 5, right: 30, left: 30, bottom: 0 }}
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
                      dataKey="name"
                      tick={{ fontSize: 11, fill: '#1e293b', fontWeight: 600 }}
                      axisLine={false}
                      tickLine={false}
                      width={120}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderRadius: '0.75rem',
                        border: 'none',
                        color: '#f8fafc',
                        fontSize: '12px'
                      }}
                      formatter={(val: any) => [`${val} cases reported`, 'Hospital Volume']}
                    />
                    <Bar
                      dataKey="cases"
                      fill="#10b981"
                      radius={[0, 6, 6, 0]}
                      label={{ position: 'right', fill: '#475569', fontSize: 11, fontWeight: 700 }}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Hospital Comparison Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-4">Hospital Name</th>
                  <th className="p-4">Facility Code</th>
                  <th className="p-4">Facility Type</th>
                  <th className="p-4 text-right">Cases Reported</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {districtAggData.hospital_comparison.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-6 text-center text-slate-400 font-medium">
                      No hospital records found in this district.
                    </td>
                  </tr>
                ) : (
                  districtAggData.hospital_comparison.map((hosp, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/80 transition">
                      <td className="p-4 font-bold text-slate-900 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                        {hosp.hospital_name}
                      </td>
                      <td className="p-4 font-mono text-slate-600">{hosp.hospital_code}</td>
                      <td className="p-4 text-slate-700">{hosp.facility_type}</td>
                      <td className="p-4 text-right font-black text-slate-900 text-sm">
                        {hosp.cases_reported}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
