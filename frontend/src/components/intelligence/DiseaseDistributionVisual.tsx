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
import type { DiseaseTrendsResponse } from '../../types/intelligence';

interface DiseaseDistributionVisualProps {
  trendsData: DiseaseTrendsResponse | null;
}

const PALETTE = [
  '#6366f1', // Indigo
  '#06b6d4', // Cyan
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#ec4899', // Pink
  '#8b5cf6', // Violet
  '#f43f5e', // Rose
  '#64748b', // Slate
];

export const DiseaseDistributionVisual: React.FC<DiseaseDistributionVisualProps> = ({ trendsData }) => {
  // Sort diseases by current cases descending
  const sortedDiseases = useMemo(() => {
    const list = trendsData?.disease_trends || [];
    return [...list]
      .filter(d => (d.current_cases ?? 0) > 0)
      .sort((a, b) => (b.current_cases ?? 0) - (a.current_cases ?? 0));
  }, [trendsData?.disease_trends]);

  const topDiseases = useMemo(() => {
    return sortedDiseases.slice(0, 6);
  }, [sortedDiseases]);

  const hasMultipleDiseases = sortedDiseases.length > 1;
  const highestDisease = sortedDiseases[0];

  // Pie chart data with safe "Other" grouping if > 5 diseases
  const pieData = useMemo(() => {
    if (sortedDiseases.length <= 5) {
      return sortedDiseases.map(d => ({
        name: d.disease,
        value: d.current_cases,
      }));
    }
    const top4 = sortedDiseases.slice(0, 4).map(d => ({
      name: d.disease,
      value: d.current_cases,
    }));
    const otherSum = sortedDiseases.slice(4).reduce((acc, d) => acc + (d.current_cases ?? 0), 0);
    return [...top4, { name: 'Other Conditions', value: otherSum }];
  }, [sortedDiseases]);

  const totalCasesAll = useMemo(() => {
    return pieData.reduce((acc, item) => acc + item.value, 0);
  }, [pieData]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5" data-testid="disease-distribution-section">
      {/* 1. Horizontal Bar Chart: 🦠 Disease Distribution */}
      <div className={`${hasMultipleDiseases ? 'lg:col-span-7' : 'lg:col-span-12'} bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>🦠 Disease Distribution</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Shows which diseases have the highest number of reported cases.
            </p>
          </div>
          {sortedDiseases.length > 6 && (
            <span className="text-[11px] font-semibold text-slate-500 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
              Showing top 6 of {sortedDiseases.length} diseases
            </span>
          )}
        </div>

        <div className="h-64 sm:h-72 w-full pt-1" data-testid="disease-distribution-bar-container">
          {topDiseases.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
              <HelpCircle className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
              <span>No disease cases recorded for the selected scope.</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={240}>
              <BarChart
                layout="vertical"
                data={topDiseases}
                margin={{ top: 10, right: 35, left: 40, bottom: 0 }}
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
                  dataKey="disease"
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
                    fontSize: '12px',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
                  }}
                  formatter={(val: any) => [`${val} cases`, 'Current Cases']}
                />
                <Bar
                  dataKey="current_cases"
                  name="Current Cases"
                  fill="#6366f1"
                  radius={[0, 6, 6, 0]}
                  label={{ position: 'right', fill: '#475569', fontSize: 11, fontWeight: 700 }}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {highestDisease && (
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2">
            <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-slate-900 mr-1">💡 What this means:</span>
              <span>
                Highest reported disease: <strong>{highestDisease.disease}</strong> ({highestDisease.current_cases} cases).
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 2. Donut Chart: 🍩 Disease Share (Only shown when >1 disease has cases) */}
      {hasMultipleDiseases && (
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4" data-testid="disease-share-section">
          <div className="pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>🍩 Disease Share</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Shows how reported cases are distributed across diseases.
            </p>
          </div>

          <div className="h-64 sm:h-72 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={240}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                  nameKey="name"
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
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
                    const pct = totalCasesAll > 0 ? ((Number(val) / totalCasesAll) * 100).toFixed(1) : '0';
                    return [`${val} cases (${pct}%)`, 'Share'];
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  align="center"
                  wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600">
            <span className="font-semibold text-slate-900">Total Cases Analyzed: </span>
            <span className="font-bold">{totalCasesAll}</span> across {sortedDiseases.length} conditions
          </div>
        </div>
      )}
    </div>
  );
};
