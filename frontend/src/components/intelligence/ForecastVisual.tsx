import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import {
  Sparkles,
  ShieldAlert,
  HelpCircle,
  Info,
  TrendingUp,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';
import type {
  ForecastSummaryResponse,
  HistoricalDiseaseResponse,
  ForecastRiskLevel
} from '../../types/intelligence';

interface ForecastVisualProps {
  forecastData: ForecastSummaryResponse | null;
  historicalData: HistoricalDiseaseResponse | null;
  totalPopulationCases: number;
  hasActiveDemographicFilters: boolean;
  filters: {
    age_group: string;
    gender: string;
    severity: string;
    vulnerable_group: string;
    patient_type: string;
  };
}

export const ForecastVisual: React.FC<ForecastVisualProps> = ({
  forecastData,
  historicalData,
  totalPopulationCases,
  hasActiveDemographicFilters,
  filters
}) => {
  // Combined chart series: Historical actuals + Forecast predicted points
  const combinedChartData = useMemo(() => {
    const list: Array<{
      period: string;
      actual: number | null;
      forecast: number | null;
      lower?: number | null;
      upper?: number | null;
    }> = [];

    // Historical points
    if (forecastData?.historical_series && forecastData.historical_series.length > 0) {
      forecastData.historical_series.forEach(pt => {
        list.push({
          period: pt.week_start,
          actual: pt.cases,
          forecast: null,
        });
      });
    } else if (historicalData?.historical_series && historicalData.historical_series.length > 0) {
      historicalData.historical_series.forEach(pt => {
        list.push({
          period: pt.period_label,
          actual: pt.total_cases,
          forecast: null,
        });
      });
    }

    // Bridge point to connect actual line to forecast line
    const lastActual = list.length > 0 ? list[list.length - 1] : null;

    // Forecast points
    if (forecastData?.forecast?.status === 'AVAILABLE' && forecastData.forecast.points.length > 0) {
      if (lastActual) {
        // Connect lines visually at boundary
        lastActual.forecast = lastActual.actual;
      }
      forecastData.forecast.points.forEach((pt, idx) => {
        list.push({
          period: `+${idx + 1} (${pt.forecast_week_start})`,
          actual: null,
          forecast: pt.predicted_cases,
          lower: pt.lower_bound,
          upper: pt.upper_bound,
        });
      });
    }

    return list;
  }, [forecastData, historicalData]);

  // Visual risk level badge with accessible aria labels
  const renderRiskLevelBadge = (level?: ForecastRiskLevel | string) => {
    switch (level) {
      case 'HIGH_RISK':
        return (
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black tracking-wide bg-rose-500/20 text-rose-300 border border-rose-400/40 shadow-xs"
            aria-label="HIGH RISK"
            title="HIGH RISK"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            <span>HIGH RISK</span>
          </span>
        );
      case 'ELEVATED':
        return (
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black tracking-wide bg-amber-500/20 text-amber-300 border border-amber-400/40 shadow-xs"
            aria-label="ELEVATED"
            title="ELEVATED"
          >
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
            <span>ELEVATED</span>
          </span>
        );
      case 'NORMAL':
        return (
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black tracking-wide bg-emerald-500/20 text-emerald-300 border border-emerald-400/40 shadow-xs"
            aria-label="NORMAL"
            title="NORMAL"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>NORMAL</span>
          </span>
        );
      case 'INSUFFICIENT_DATA':
      default:
        return (
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black tracking-wide bg-slate-500/20 text-slate-300 border border-slate-400/40 shadow-xs"
            aria-label="INSUFFICIENT DATA"
            title="INSUFFICIENT DATA"
          >
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            <span>INSUFFICIENT DATA</span>
          </span>
        );
    }
  };

  // Forecast insight strictly derived from actual data
  const forecastInsight = useMemo(() => {
    if (forecastData?.forecast?.status !== 'AVAILABLE') return null;
    const points = forecastData.forecast.points || [];
    if (points.length === 0) return null;
    const avgPred = Math.round(points.reduce((acc, p) => acc + p.predicted_cases, 0) / points.length);
    const baseline = forecastData.forecast_risk?.historical_baseline ?? 0;
    if (baseline > 0 && avgPred > baseline * 1.2) {
      return 'Forecast indicates increased case activity in the next period relative to historical baseline.';
    } else if (baseline > 0 && avgPred < baseline * 0.8) {
      return 'Forecast indicates reduced case activity in the next period relative to historical baseline.';
    }
    return `Forecast projects stable baseline activity (~${avgPred} cases/wk) over the upcoming projection horizon.`;
  }, [forecastData]);

  return (
    <div className="bg-gradient-to-br from-indigo-900 via-slate-900 to-indigo-950 rounded-2xl p-6 text-white shadow-md border border-indigo-800/50 space-y-6">
      {/* Forecast Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-indigo-800/60">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 uppercase tracking-wider">
              Forecast / Surveillance Signal
            </span>
            <span className="text-xs text-indigo-300 font-semibold">• Statistical Projection</span>
          </div>
          <h3 className="text-lg font-black tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            🔮 Case Forecast — Public Health Epidemiological Forecast ({forecastData?.disease || 'Selected Condition'})
          </h3>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Forecast values are estimates based on historical case patterns.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-300">Method:</span>
          <span className="px-2.5 py-1 bg-white/10 rounded-lg text-indigo-200 font-mono font-bold text-[11px] border border-white/10">
            {forecastData?.forecast.method || 'WEIGHTED_MOVING_AVERAGE'}
          </span>
        </div>
      </div>

      {/* Selected Population Summary in Forecast Section */}
      <div
        className="p-3.5 bg-white/5 rounded-xl border border-white/10 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2"
        data-testid="forecast-selected-population"
      >
        <div>
          <span className="font-bold text-indigo-300 uppercase tracking-wider block text-[11px]">
            Selected Population
          </span>
          {hasActiveDemographicFilters ? (
            <div className="flex flex-wrap items-center gap-2.5 mt-1 text-slate-200">
              {filters.age_group && (
                <span>Age: <strong className="text-white font-bold">{filters.age_group}</strong></span>
              )}
              {filters.gender && (
                <span>Gender: <strong className="text-white font-bold">{filters.gender === 'MALE' ? 'Male' : filters.gender === 'FEMALE' ? 'Female' : 'Other'}</strong></span>
              )}
              {filters.severity && (
                <span>Severity: <strong className="text-white font-bold">{filters.severity === 'MILD' ? 'Mild' : filters.severity === 'MODERATE' ? 'Moderate' : 'Severe'}</strong></span>
              )}
              {filters.vulnerable_group && (
                <span>Vulnerable Group: <strong className="text-white font-bold">{
                  filters.vulnerable_group === 'PREGNANT' ? 'Pregnant' :
                  filters.vulnerable_group === 'ELDERLY' ? 'Elderly' :
                  filters.vulnerable_group === 'DISABILITY' ? 'Disability' :
                  filters.vulnerable_group === 'CHRONIC_CONDITION' ? 'Chronic Condition' :
                  filters.vulnerable_group === 'LOW_INCOME_SLUM' ? 'Low Income / Slum' : 'General'
                }</strong></span>
              )}
              {filters.patient_type && (
                <span>Patient Type: <strong className="text-white font-bold">{filters.patient_type === 'NEW' ? 'New' : 'Follow-up'}</strong></span>
              )}
            </div>
          ) : (
            <span className="text-slate-300 italic block mt-1">All eligible population</span>
          )}
        </div>

        <div className="font-mono text-xs shrink-0">
          {totalPopulationCases > 0 ? (
            <span className="text-indigo-200 bg-white/10 px-2.5 py-1 rounded-lg border border-white/10 inline-block">
              Cases in selected population: <strong className="text-white font-bold">{totalPopulationCases}</strong>
            </span>
          ) : (
            <span className="text-amber-300 bg-amber-500/10 px-2.5 py-1 rounded-lg border border-amber-500/20 inline-block">
              No cases found for the selected filters.
            </span>
          )}
        </div>
      </div>

      {/* Section 15: Combined Line/Area Chart for Actual vs Forecast */}
      {forecastData?.forecast.status === 'AVAILABLE' && combinedChartData.length > 0 && (
        <div className="bg-white/5 p-4 rounded-xl border border-white/10 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h4 className="text-xs font-bold text-indigo-200 uppercase tracking-wider">
              Historical Actuals vs Forecast Projections
            </h4>
            <div className="flex items-center gap-4 text-xs font-medium">
              <span className="flex items-center gap-1.5 text-indigo-300">
                <span className="w-3 h-0.5 bg-indigo-400 rounded-full inline-block" /> Actual Cases
              </span>
              <span className="flex items-center gap-1.5 text-purple-300">
                <span className="w-3 h-0.5 border-t-2 border-dashed border-purple-400 inline-block" /> Forecast (Projected)
              </span>
            </div>
          </div>

          <div className="h-60 sm:h-64 w-full">
            <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={220}>
              <LineChart data={combinedChartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />
                <XAxis
                  dataKey="period"
                  tick={{ fontSize: 10, fill: '#cbd5e1' }}
                  axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
                  tickLine={false}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 10, fill: '#cbd5e1' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderRadius: '0.75rem',
                    border: '1px solid rgba(255,255,255,0.15)',
                    color: '#f8fafc',
                    fontSize: '12px'
                  }}
                  formatter={(val: any, name: any) => [
                    `${val} cases`,
                    name === 'actual' ? 'Actual Historical Cases' : 'Forecast Projected Cases'
                  ]}
                />
                <Legend verticalAlign="top" align="right" wrapperStyle={{ display: 'none' }} />
                <Line
                  type="monotone"
                  dataKey="actual"
                  name="actual"
                  stroke="#818cf8"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#818cf8' }}
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  name="forecast"
                  stroke="#c084fc"
                  strokeWidth={2.5}
                  strokeDasharray="5 5"
                  dot={{ r: 4, fill: '#c084fc' }}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Forecast Body */}
      {forecastData?.forecast.status === 'INSUFFICIENT_DATA' ? (
        <div className="my-6 p-6 rounded-xl bg-white/5 border border-white/10 text-center">
          <HelpCircle className="w-8 h-8 text-amber-400 mx-auto mb-2 opacity-80" />
          <h4 className="text-sm font-bold text-slate-100">
            Insufficient historical surveillance data for a reliable forecast.
          </h4>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto font-medium">
            {forecastData.forecast.explanation || 'A minimum observation baseline of at least 3 cases is required to construct a valid statistical forecast model.'}
          </p>
          {forecastData.forecast_risk && (
            <div className="mt-4 pt-3 border-t border-white/10 text-xs text-amber-300/90 font-medium" data-testid="insufficient-forecast-risk">
              <span>{forecastData.forecast_risk.explanation || 'Insufficient historical data for reliable forecast risk classification.'}</span>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-5">
          {/* Explanation Banner */}
          <div className="p-3.5 bg-indigo-950/60 rounded-xl border border-indigo-700/40 text-xs text-indigo-200 flex items-start gap-2.5">
            <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
            <span>{forecastData?.forecast.explanation}</span>
          </div>

          {/* Forecast Weekly Horizon Points */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {forecastData?.forecast.points.map((pt, idx) => {
              const riskPt = forecastData?.forecast_risk?.risk_points?.find(
                rp => rp.forecast_week_start === pt.forecast_week_start
              ) || forecastData?.forecast_risk?.risk_points?.[idx];

              return (
                <div key={idx} className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center text-[10px] font-bold text-indigo-300 uppercase font-mono">
                      <span>Week +{idx + 1}</span>
                      <span>{pt.forecast_week_start}</span>
                    </div>
                    <div className="mt-2">
                      <span className="text-[10px] text-slate-400 block font-semibold">Predicted Volume</span>
                      <div className="text-2xl font-black text-white mt-0.5">
                        {pt.predicted_cases}
                        <span className="text-xs text-indigo-300 font-normal ml-1">cases</span>
                      </div>
                    </div>
                    <div className="mt-2 pt-2 border-t border-white/10 flex justify-between items-center text-[11px] font-mono">
                      <span className="text-slate-400">Range:</span>
                      <span className="text-indigo-200 font-bold">
                        [{pt.lower_bound} — {pt.upper_bound}]
                      </span>
                    </div>
                  </div>

                  {/* Forecast Week Risk Point Badge & Ratio */}
                  {riskPt && forecastData?.forecast_risk?.status === 'AVAILABLE' && (
                    <div className="mt-3 pt-2.5 border-t border-white/10 space-y-1 text-[11px]">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold uppercase text-slate-400">Risk:</span>
                        {renderRiskLevelBadge(riskPt.risk_level)}
                      </div>
                      <div className="flex justify-between items-center font-mono text-[10px] text-slate-300">
                        <span>Ratio:</span>
                        <span className="font-bold text-white">
                          {riskPt.ratio_to_baseline !== null ? `${riskPt.ratio_to_baseline}×` : 'N/A'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Section 16: 🚦 Forecast Risk Section */}
          {forecastData?.forecast_risk && (
            <div className="mt-6 pt-5 border-t border-indigo-800/60 space-y-4" data-testid="forecast-risk-section">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-indigo-400" />
                  <h4 className="text-sm font-black text-white uppercase tracking-wider">
                    🚦 Forecast Risk & Surveillance Thresholds
                  </h4>
                </div>
                {forecastData.forecast_risk.status === 'AVAILABLE' && (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-indigo-200 font-semibold">Highest Risk Level:</span>
                    {renderRiskLevelBadge(forecastData.forecast_risk.highest_risk_level)}
                  </div>
                )}
              </div>

              {forecastData.forecast_risk.status === 'INSUFFICIENT_DATA' ? (
                <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center" data-testid="insufficient-forecast-risk">
                  <HelpCircle className="w-7 h-7 text-amber-400 mx-auto mb-2 opacity-80" />
                  <h5 className="text-sm font-bold text-slate-100">
                    Not enough historical cases to calculate reliable forecast risk.
                  </h5>
                  <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto font-medium">
                    {forecastData.forecast_risk.explanation || 'Insufficient historical data for reliable forecast risk classification.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Risk Overview KPI Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {/* 1. Highest Risk Level */}
                    <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10" data-testid="kpi-highest-risk">
                      <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Highest Risk Level</p>
                      <div className="mt-2">
                        {renderRiskLevelBadge(forecastData.forecast_risk.highest_risk_level)}
                      </div>
                      <p className="text-[11px] text-slate-300 mt-2 font-medium">
                        {forecastData.forecast_risk.highest_risk_level === 'HIGH_RISK'
                          ? 'High projected surveillance risk'
                          : forecastData.forecast_risk.highest_risk_level === 'ELEVATED'
                          ? 'Elevated surveillance signal'
                          : 'Normal baseline projection'}
                      </p>
                    </div>

                    {/* 2. Historical Baseline */}
                    <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10" data-testid="kpi-historical-baseline">
                      <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Historical Baseline</p>
                      <div className="mt-2 flex items-baseline gap-1">
                        <span className="text-2xl font-black text-white">{forecastData.forecast_risk.historical_baseline ?? 0}</span>
                        <span className="text-xs text-indigo-300 font-medium">cases/wk</span>
                      </div>
                      <p className="text-[11px] text-slate-300 mt-1 font-mono">
                        Observation window weekly baseline
                      </p>
                    </div>

                    {/* 3. Elevation & High-Risk Thresholds */}
                    <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10" data-testid="kpi-thresholds">
                      <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Surveillance Thresholds</p>
                      <div className="mt-2 space-y-1 text-xs font-mono">
                        <div className="flex justify-between items-center text-amber-300">
                          <span>Elevation Threshold:</span>
                          <span className="font-bold">≥ {forecastData.forecast_risk.elevation_ratio_threshold}×</span>
                        </div>
                        <div className="flex justify-between items-center text-rose-300">
                          <span>High-Risk Threshold:</span>
                          <span className="font-bold">≥ {forecastData.forecast_risk.high_risk_ratio_threshold}×</span>
                        </div>
                      </div>
                    </div>

                    {/* 4. Projected Week Counts */}
                    <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10" data-testid="kpi-risk-counts">
                      <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Projected Week Distribution</p>
                      <div className="mt-2 grid grid-cols-3 gap-1.5 text-center font-mono">
                        <div className="p-1.5 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                          <span className="text-[10px] text-emerald-300 block font-bold">Normal Projected Weeks</span>
                          <span className="text-sm font-black text-white">{forecastData.forecast_risk.normal_points_count}</span>
                        </div>
                        <div className="p-1.5 bg-amber-500/10 rounded-lg border border-amber-500/20">
                          <span className="text-[10px] text-amber-300 block font-bold">Elevated Projected Weeks</span>
                          <span className="text-sm font-black text-white">{forecastData.forecast_risk.elevated_points_count}</span>
                        </div>
                        <div className="p-1.5 bg-rose-500/10 rounded-lg border border-rose-500/20">
                          <span className="text-[10px] text-rose-300 block font-bold">High-Risk Projected Weeks</span>
                          <span className="text-sm font-black text-white">{forecastData.forecast_risk.high_risk_points_count}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Risk Explanation */}
                  <div className="p-3.5 bg-indigo-950/70 rounded-xl border border-indigo-700/50 text-xs text-indigo-200 flex items-start gap-2.5" data-testid="risk-explanation">
                    <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-white block">Risk Explanation:</span>
                      <span>{forecastData.forecast_risk.explanation}</span>
                    </div>
                  </div>

                  {/* Weekly Forecast Risk Points Table */}
                  {forecastData.forecast_risk.risk_points && forecastData.forecast_risk.risk_points.length > 0 && (
                    <div className="space-y-2 mt-4" data-testid="forecast-risk-points-table">
                      <h5 className="text-xs font-bold text-indigo-200 uppercase tracking-wider">
                        Forecast Risk Points
                      </h5>
                      <div className="overflow-x-auto rounded-xl border border-white/10 bg-white/5">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-white/10 text-indigo-200 font-bold border-b border-white/10">
                            <tr>
                              <th className="p-3">Forecast Week</th>
                              <th className="p-3">Predicted Cases</th>
                              <th className="p-3">Historical Baseline</th>
                              <th className="p-3">Ratio to Baseline</th>
                              <th className="p-3">Risk Level</th>
                              <th className="p-3">Explanation</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/5 text-slate-200 font-medium">
                            {forecastData.forecast_risk.risk_points.map((rp, idx) => (
                              <tr key={idx} className="hover:bg-white/5 transition" data-testid={`risk-point-row-${idx}`}>
                                <td className="p-3 font-mono font-bold text-white">
                                  Week +{rp.forecast_week ?? idx + 1}
                                </td>
                                <td className="p-3 font-mono font-bold text-white">
                                  {rp.predicted_cases}
                                </td>
                                <td className="p-3 font-mono text-slate-300">
                                  {rp.historical_baseline}
                                </td>
                                <td className="p-3 font-mono font-bold">
                                  {rp.ratio_to_baseline !== null ? `${rp.ratio_to_baseline}×` : 'N/A'}
                                </td>
                                <td className="p-3">
                                  {renderRiskLevelBadge(rp.risk_level)}
                                </td>
                                <td className="p-3 text-[11px] text-slate-300 max-w-sm">
                                  {rp.explanation}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Derived insight */}
          {forecastInsight && (
            <div className="p-3 bg-white/10 rounded-xl border border-white/15 text-xs text-indigo-200 flex items-start gap-2">
              <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-white mr-1">💡 What this means:</span>
                <span>{forecastInsight}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
