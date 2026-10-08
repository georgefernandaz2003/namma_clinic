import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { BarChart3, HelpCircle, Info } from 'lucide-react';
import type {
  HistoricalDiseaseResponse,
  DiseaseTrendsResponse,
  ForecastSummaryResponse,
  TrendDirection
} from '../../types/intelligence';

interface DiseaseTrendVisualProps {
  historicalData: HistoricalDiseaseResponse | null;
  trendsData: DiseaseTrendsResponse | null;
  forecastData: ForecastSummaryResponse | null;
  selectedDisease: string;
}

export const DiseaseTrendVisual: React.FC<DiseaseTrendVisualProps> = ({
  historicalData,
  trendsData,
  forecastData,
  selectedDisease
}) => {
  // Map historical chronological series directly from backend historical_series
  const chartData = useMemo(() => {
    if (historicalData?.historical_series && historicalData.historical_series.length > 0) {
      return historicalData.historical_series.map(pt => ({
        period_label: pt.period_label,
        total_cases: pt.total_cases,
        MILD: pt.severity_breakdown?.MILD ?? 0,
        MODERATE: pt.severity_breakdown?.MODERATE ?? 0,
        SEVERE: pt.severity_breakdown?.SEVERE ?? 0,
      }));
    }

    if (forecastData?.historical_series && forecastData.historical_series.length > 0) {
      return forecastData.historical_series.map(pt => ({
        period_label: pt.week_start,
        total_cases: pt.cases,
        MILD: pt.cases,
        MODERATE: 0,
        SEVERE: 0,
      }));
    }

    return [];
  }, [historicalData, forecastData]);

  // Derive trend direction strictly from backend data
  const trendDirection: TrendDirection | string = useMemo(() => {
    if (historicalData?.trend_direction) return historicalData.trend_direction;
    if (forecastData?.trend?.direction) return forecastData.trend.direction;
    if (trendsData?.summary?.overall_trend_direction) return trendsData.summary.overall_trend_direction;
    return 'NORMAL';
  }, [historicalData, forecastData, trendsData]);

  // Meaningful insight strictly calculated from actual data
  const trendInsight = useMemo(() => {
    if (chartData.length === 0) return null;
    const totalCasesInHistory = chartData.reduce((acc, p) => acc + p.total_cases, 0);
    if (totalCasesInHistory === 0) return 'No cases reported during this observation period.';

    if (trendDirection === 'INCREASING') {
      return 'Cases are increasing over the selected period. Surveillance vigilance recommended.';
    } else if (trendDirection === 'DECREASING') {
      return 'Cases are decreasing over the selected period, indicating a downward transmission trajectory.';
    } else if (trendDirection === 'POSSIBLE_INCREASE') {
      return 'Cases show a possible increase compared to the prior window.';
    } else if (trendDirection === 'NORMAL') {
      return 'Cases remained stable within expected seasonal variations over the selected period.';
    }
    return null;
  }, [chartData, trendDirection]);

  return (
    <div
      className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4"
      data-testid="disease-trend-section"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            <span>📈 Disease Trend — Historical Disease Trajectory ({historicalData?.disease || selectedDisease || 'Monitored Conditions'})</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Shows how reported cases have changed over time with clinical severity distributions.
          </p>
        </div>

        {historicalData && (
          <div className="flex items-center gap-3 text-xs font-semibold text-slate-600 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
            <span>Current Month: <strong className="text-slate-900">{historicalData.current_month_cases}</strong></span>
            <span>•</span>
            <span>Prior Month: <strong className="text-slate-900">{historicalData.previous_month_cases}</strong></span>
            {historicalData.percentage_change !== null && (
              <>
                <span>•</span>
                <span className={`font-mono font-bold ${historicalData.percentage_change > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                  {historicalData.percentage_change > 0 ? `+${historicalData.percentage_change}%` : `${historicalData.percentage_change}%`}
                </span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Historical Trend Chart */}
      <div
        className="h-64 sm:h-72 w-full pt-2"
        data-testid="historical-chart-container"
        role="region"
        aria-label="Historical Disease Trend Chart"
      >
        {chartData.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
            <HelpCircle className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
            <span>No historical trend records found for the selected filters.</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={240}>
            <BarChart
              data={chartData}
              margin={{ top: 10, right: 20, left: -10, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis
                dataKey="period_label"
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
                  fontSize: '12px',
                  boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
                }}
                formatter={(value: any, name: any) => [
                  `${value} cases`,
                  name === 'MILD' ? 'Mild Severity' : name === 'MODERATE' ? 'Moderate Severity' : name === 'SEVERE' ? 'Severe Case' : name
                ]}
                labelStyle={{ fontWeight: 'bold', color: '#cbd5e1', marginBottom: '4px' }}
              />
              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ paddingBottom: '10px', fontSize: '11px', fontWeight: 600 }}
              />
              <Bar dataKey="MILD" name="MILD" stackId="severity" fill="#10b981" radius={[0, 0, 0, 0]} />
              <Bar dataKey="MODERATE" name="MODERATE" stackId="severity" fill="#f59e0b" radius={[0, 0, 0, 0]} />
              <Bar dataKey="SEVERE" name="SEVERE" stackId="severity" fill="#f43f5e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Monthly Breakdown Cards */}
      {historicalData?.historical_series && historicalData.historical_series.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {historicalData.historical_series.map((item, idx) => (
            <div key={idx} className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 flex flex-col justify-between">
              <div>
                <p className="text-[11px] font-bold text-slate-600 uppercase font-mono">{item.period_label}</p>
                <h4 className="text-xl font-black text-slate-900 mt-1">{item.total_cases}</h4>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-200/80 space-y-1 text-[10px]">
                <div className="flex justify-between text-emerald-700 font-semibold">
                  <span>Mild:</span>
                  <span>{item.severity_breakdown.MILD}</span>
                </div>
                <div className="flex justify-between text-amber-700 font-semibold">
                  <span>Moderate:</span>
                  <span>{item.severity_breakdown.MODERATE}</span>
                </div>
                <div className="flex justify-between text-rose-700 font-semibold">
                  <span>Severe:</span>
                  <span>{item.severity_breakdown.SEVERE}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Insight Section */}
      {trendInsight && (
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
          <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-900 mr-1">💡 What this means:</span>
            <span>{trendInsight}</span>
          </div>
        </div>
      )}
    </div>
  );
};
