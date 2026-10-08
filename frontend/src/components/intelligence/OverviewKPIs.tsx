import React from 'react';
import {
  Users,
  Layers,
  Sparkles,
  ShieldAlert,
  Calendar,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  HelpCircle,
  Activity
} from 'lucide-react';
import type {
  DiseaseTrendsResponse,
  ForecastSummaryResponse,
  IntelligenceAlert,
  TrendDirection
} from '../../types/intelligence';

interface OverviewKPIsProps {
  trendsData: DiseaseTrendsResponse | null;
  forecastData: ForecastSummaryResponse | null;
  alerts: IntelligenceAlert[];
  totalPopulationCases: number;
}

export const OverviewKPIs: React.FC<OverviewKPIsProps> = ({
  trendsData,
  forecastData,
  alerts,
  totalPopulationCases
}) => {
  // Authoritative case count from observation period
  const authoritativeTotalCases = totalPopulationCases;
  const currentPeriodCases = trendsData?.summary?.total_current_cases ?? authoritativeTotalCases;

  // Active diseases count
  const activeDiseasesCount =
    trendsData?.summary?.diseases_monitored_count ??
    trendsData?.disease_trends?.length ??
    0;

  // Forecast cases: sum of predicted cases in forecast horizon points
  const forecastCasesSum =
    forecastData?.forecast?.status === 'AVAILABLE' && forecastData?.forecast?.points
      ? forecastData.forecast.points.reduce((acc, pt) => acc + (pt.predicted_cases || 0), 0)
      : 0;

  // High Risk Signals count
  const highRiskSignalsCount =
    forecastData?.forecast_risk?.status === 'AVAILABLE'
      ? (forecastData.forecast_risk.high_risk_points_count ?? 0)
      : alerts.filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH').length;

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

  return (
    <div className="space-y-4">
      {/* 4 Primary Top KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="overview-kpi-section">
        {/* Card 1: Total Cases / Current Period Cases */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-200 transition">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Total Cases
              </p>
              <span className="text-[10px] text-slate-400 font-medium block">Current Period Cases</span>
              <h3 className="text-3xl font-black text-slate-900 mt-1">
                {currentPeriodCases.toLocaleString()}
              </h3>
              <p className="text-xs text-indigo-700 font-semibold mt-1">
                Cases in selected population
              </p>
            </div>
            <div className="p-3 bg-indigo-50 rounded-xl text-indigo-600 border border-indigo-100">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500 text-[11px]">vs Previous ({trendsData?.summary.total_previous_cases ?? 0}):</span>
            {renderPercentageBadge(trendsData?.summary.percentage_change)}
          </div>
        </div>

        {/* Card 2: Active Diseases */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-teal-200 transition">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Active Diseases
              </p>
              <span className="text-[10px] text-slate-400 font-medium block">Monitored Diseases</span>
              <h3 className="text-3xl font-black text-teal-900 mt-1">
                {activeDiseasesCount}
              </h3>
              <p className="text-xs text-teal-700 font-semibold mt-1">
                Monitored diseases active
              </p>
            </div>
            <div className="p-3 bg-teal-50 rounded-xl text-teal-600 border border-teal-100">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-[11px] font-semibold text-slate-500">Overall Trend:</span>
            {renderTrendBadge(trendsData?.summary.overall_trend_direction)}
          </div>
        </div>

        {/* Card 3: Forecast Cases */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-purple-200 transition">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Forecast Cases
              </p>
              <span className="text-[10px] text-slate-400 font-medium block">Statistical Projection</span>
              <h3 className="text-3xl font-black text-purple-900 mt-1">
                {forecastCasesSum > 0 ? forecastCasesSum.toLocaleString() : '—'}
              </h3>
              <p className="text-xs text-purple-700 font-semibold mt-1">
                Expected cases in forecast period
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-xl text-purple-600 border border-purple-100">
              <Sparkles className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500 font-medium truncate">
            {forecastData?.forecast?.horizon_weeks ? `Horizon: Next ${forecastData.forecast.horizon_weeks} weeks` : '4-week projection window'}
          </div>
        </div>

        {/* Card 4: High Risk Signals */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-rose-200 transition">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                High Risk Signals
              </p>
              <span className="text-[10px] text-slate-400 font-medium block">Surveillance Alerts</span>
              <h3 className="text-3xl font-black text-rose-900 mt-1">
                {highRiskSignalsCount}
              </h3>
              <p className="text-xs text-rose-700 font-semibold mt-1">
                Areas requiring attention
              </p>
            </div>
            <div className="p-3 bg-rose-50 rounded-xl text-rose-600 border border-rose-100">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500 font-medium">
            {highRiskSignalsCount > 0 ? 'Requires clinical review' : 'No acute risk signals detected'}
          </div>
        </div>
      </div>

      {/* Supporting Velocity & Cumulative Strips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div className="bg-slate-50/80 px-4 py-3 rounded-xl border border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-100 text-blue-700 rounded-lg">
              <Calendar className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase block">7-Day Case Velocity</span>
              <span className="text-sm font-bold text-slate-800">
                {trendsData?.summary.total_7d_cases?.toLocaleString() ?? 0} cases
              </span>
            </div>
          </div>
          <span className="text-[11px] text-slate-500">Trailing 7 days</span>
        </div>

        <div className="bg-slate-50/80 px-4 py-3 rounded-xl border border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase block">30-Day Cumulative</span>
              <span className="text-sm font-bold text-slate-800">
                {trendsData?.summary.total_30d_cases?.toLocaleString() ?? 0} cases
              </span>
            </div>
          </div>
          <span className="text-[11px] text-slate-500">90-Day: {trendsData?.summary.total_90d_cases?.toLocaleString() ?? 0}</span>
        </div>

        <div className="bg-slate-50/80 px-4 py-3 rounded-xl border border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-100 text-emerald-700 rounded-lg">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-500 font-bold uppercase block">Observation Period</span>
              <span className="text-sm font-bold text-slate-800">
                {trendsData?.summary.observation_period?.duration_days ?? 7} days window
              </span>
            </div>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            {trendsData?.summary.observation_period?.end_date || 'Current'}
          </span>
        </div>
      </div>
    </div>
  );
};
