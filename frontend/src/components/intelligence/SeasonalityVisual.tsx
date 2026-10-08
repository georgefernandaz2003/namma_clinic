import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell
} from 'recharts';
import { Calendar, Info } from 'lucide-react';
import type { SeasonalityData } from '../../types/intelligence';

interface SeasonalityVisualProps {
  seasonalityData: SeasonalityData | null;
}

export const SeasonalityVisual: React.FC<SeasonalityVisualProps> = ({ seasonalityData }) => {
  const monthlyPatterns = useMemo(() => seasonalityData?.monthly_patterns || [], [seasonalityData]);
  const highestMonthName = seasonalityData?.highest_case_month?.month_name;

  // Chart data
  const chartData = useMemo(() => {
    return monthlyPatterns.map(m => ({
      name: m.month_name.slice(0, 3),
      fullName: m.month_name,
      cases: m.average_cases,
      totalCases: m.total_cases,
      isPeak: m.month_name === highestMonthName,
    }));
  }, [monthlyPatterns, highestMonthName]);

  // Insight strictly from actual data
  const seasonalityInsight = useMemo(() => {
    if (!seasonalityData || seasonalityData.seasonal_status === 'NOT_ENOUGH_DATA') return null;
    if (seasonalityData.highest_case_month && seasonalityData.highest_case_month.total_cases > 0) {
      return `Highest reported activity occurred in ${seasonalityData.highest_case_month.month_name} (averaging ${seasonalityData.highest_case_month.average_cases} cases / month).`;
    }
    return null;
  }, [seasonalityData]);

  if (!seasonalityData) return null;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="seasonality-section">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-slate-900">
              🗓️ Seasonal Pattern Analysis ({seasonalityData.disease})
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Shows when cases are more common during the selected period.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500">Pattern Status:</span>
          <span
            className={`px-2.5 py-0.5 rounded-full text-[11px] font-extrabold border ${
              seasonalityData.seasonal_status === 'DETECTED'
                ? 'bg-amber-100 text-amber-900 border-amber-300'
                : seasonalityData.seasonal_status === 'WEAK'
                ? 'bg-blue-100 text-blue-900 border-blue-300'
                : 'bg-slate-100 text-slate-700 border-slate-300'
            }`}
          >
            {seasonalityData.seasonal_status}
          </span>
        </div>
      </div>

      {seasonalityData.seasonal_status === 'NOT_ENOUGH_DATA' ? (
        <div className="p-6 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 text-center">
          <p className="font-semibold text-slate-800">{seasonalityData.explanation}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <p className="text-[10px] font-bold text-slate-500 uppercase">Seasonal Strength Index</p>
              <h4 className="text-xl font-black text-slate-900 mt-1">{seasonalityData.seasonal_strength}</h4>
              <p className="text-[10px] text-slate-400 mt-0.5">Normalized variation metric [0.0 - 1.0]</p>
            </div>

            <div className="bg-rose-50/60 p-3.5 rounded-xl border border-rose-200">
              <p className="text-[10px] font-bold text-rose-700 uppercase">Highest Case Month</p>
              <h4 className="text-xl font-black text-rose-950 mt-1">
                {seasonalityData.highest_case_month?.month_name || 'N/A'}
              </h4>
              <p className="text-[10px] text-rose-700 mt-0.5 font-semibold">
                Averaging {seasonalityData.highest_case_month?.average_cases ?? 0} cases / month
              </p>
            </div>

            <div className="bg-emerald-50/60 p-3.5 rounded-xl border border-emerald-200">
              <p className="text-[10px] font-bold text-emerald-700 uppercase">Lowest Case Month</p>
              <h4 className="text-xl font-black text-emerald-950 mt-1">
                {seasonalityData.lowest_case_month?.month_name || 'N/A'}
              </h4>
              <p className="text-[10px] text-emerald-700 mt-0.5 font-semibold">
                Averaging {seasonalityData.lowest_case_month?.average_cases ?? 0} cases / month
              </p>
            </div>
          </div>

          {/* Month-by-month bar chart */}
          {chartData.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Monthly Average Case Trajectory
              </h4>
              <div className="h-56 w-full pt-1">
                <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={200}>
                  <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      axisLine={{ stroke: '#cbd5e1' }}
                      tickLine={false}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderRadius: '0.75rem',
                        border: 'none',
                        color: '#f8fafc',
                        fontSize: '12px'
                      }}
                      formatter={(val: any, _, item: any) => [
                        `${val} avg cases (${item.payload.totalCases} total)`,
                        'Monthly Activity'
                      ]}
                      labelFormatter={(_, item) => item[0]?.payload.fullName || ''}
                    />
                    <Bar dataKey="cases" name="Average Cases" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.isPeak ? '#f43f5e' : '#10b981'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Monthly Pattern Bar Cards */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Calendar Month Historical Distribution
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
              {monthlyPatterns.map((m, idx) => {
                const isPeak = m.month_name === highestMonthName;
                return (
                  <div
                    key={idx}
                    className={`p-2.5 rounded-lg border text-center transition ${
                      isPeak
                        ? 'bg-rose-50/80 border-rose-300 shadow-2xs'
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    <p className={`text-[11px] font-bold ${isPeak ? 'text-rose-900' : 'text-slate-700'}`}>
                      {m.month_name} {isPeak ? '★' : ''}
                    </p>
                    <p className="text-base font-black text-slate-900 mt-0.5">{m.average_cases}</p>
                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                      Total: {m.total_cases} ({m.occurrences}x)
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Derived insight */}
          {seasonalityInsight && (
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
              <Info className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-900 mr-1">💡 What this means:</span>
                <span>{seasonalityInsight}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
