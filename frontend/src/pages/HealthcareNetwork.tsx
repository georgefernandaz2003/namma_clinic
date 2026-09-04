import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Facility, NetworkNode } from '../types';
import { Network, Building2, ChevronRight, ChevronDown, Search } from 'lucide-react';

interface HierarchyNode {
  id: string | number;
  code: string;
  name: string;
  type: string;
  district?: string;
  vulnerable_population?: number;
  children: HierarchyNode[];
}

export const HealthcareNetwork: React.FC = () => {
  const [hierarchy, setHierarchy] = useState<HierarchyNode[]>([]);
  const [graphNodes, setGraphNodes] = useState<NetworkNode[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(null);
  const [viewMode, setViewMode] = useState<'TREE' | 'GRAPH'>('TREE');

  const loadData = async () => {
    try {
      const treeRes = await api.get('facilities/hierarchy/');
      setHierarchy(treeRes.data.hierarchy || []);

      const graphRes = await api.get('facilities/network-graph/');
      setGraphNodes(graphRes.data.nodes || []);

      // Auto-expand all top level nodes
      const initExp: Record<string, boolean> = {};
      (treeRes.data.hierarchy || []).forEach((n: HierarchyNode) => {
        initExp[n.id] = true;
      });
      setExpandedNodes(initExp);
    } catch (e) {
      console.error('Failed to load network topology', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const toggleExpand = (id: string | number) => {
    setExpandedNodes((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleFacilityClick = async (facId: number) => {
    try {
      const res = await api.get(`facilities/${facId}/`);
      setSelectedFacility(res.data);
    } catch (e) {
      console.error('Failed to load facility details', e);
    }
  };

  const renderTree = (node: HierarchyNode) => {
    const isExpanded = expandedNodes[node.id];
    const hasChildren = node.children && node.children.length > 0;
    const isMatch = searchQuery ? node.name.toLowerCase().includes(searchQuery.toLowerCase()) : true;

    if (searchQuery && !isMatch && !hasChildren) return null;

    const facIdNum = typeof node.id === 'number' ? node.id : parseInt(String(node.id).replace('district-', ''));

    return (
      <div key={node.id} className="ml-4 my-1">
        <div
          className={`flex items-center justify-between p-2.5 rounded-xl border transition-all ${
            selectedFacility?.id === facIdNum
              ? 'bg-emerald-50 border-emerald-500 text-slate-900 shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300 text-slate-800'
          }`}
        >
          <div className="flex items-center gap-2 font-medium text-xs">
            {hasChildren ? (
              <button
                onClick={() => toggleExpand(node.id)}
                className="p-1 rounded hover:bg-slate-100 text-slate-500"
              >
                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
            ) : (
              <span className="w-6" />
            )}

            <Building2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span
              onClick={() => typeof node.id === 'number' && handleFacilityClick(node.id)}
              className={`hover:underline cursor-pointer ${typeof node.id === 'number' ? 'font-bold text-slate-900' : 'font-extrabold text-emerald-800'}`}
            >
              {node.name}
            </span>
          </div>

          <div className="flex items-center gap-2 text-[10px]">
            <span className="px-2 py-0.5 rounded font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200">
              {node.type.replace('_', ' ')}
            </span>
            {node.vulnerable_population ? (
              <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-900 border border-amber-200 font-semibold hidden sm:inline">
                Target: {node.vulnerable_population.toLocaleString()}
              </span>
            ) : null}
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="border-l-2 border-slate-200 ml-3 pl-1 space-y-1">
            {node.children.map((child) => renderTree(child))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Network className="w-6 h-6 text-emerald-600" />
            Healthcare Network & Referral Topology Canvas
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Database-driven facility hierarchy and dynamic referral routing graph across Karnataka / GBA
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('TREE')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              viewMode === 'TREE'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            Hierarchy Tree View
          </button>
          <button
            onClick={() => setViewMode('GRAPH')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              viewMode === 'GRAPH'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            SVG Visual Canvas
          </button>
        </div>
      </div>

      {/* Main Grid View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Interactive Canvas Container */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-4">
          <div className="flex items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search facility name or district..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 focus:outline-none focus:border-emerald-600 font-medium"
              />
            </div>
            <button
              onClick={loadData}
              className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-lg border border-slate-200"
            >
              Refresh Graph
            </button>
          </div>

          {viewMode === 'TREE' ? (
            <div className="max-h-[600px] overflow-y-auto pr-2 space-y-2">
              {hierarchy.map((node) => renderTree(node))}
            </div>
          ) : (
            /* SVG Visual Topology Graph Canvas */
            <div className="relative w-full h-[550px] bg-slate-50 rounded-xl border border-slate-200 overflow-hidden flex items-center justify-center p-4">
              <svg className="w-full h-full" viewBox="0 0 800 500">
                <defs>
                  <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
                  </marker>
                </defs>

                {/* Draw Node Connecting Lines */}
                <line x1="400" y1="60" x2="200" y2="160" stroke="#94A3B8" strokeWidth="2" strokeDasharray="4" />
                <line x1="400" y1="60" x2="600" y2="160" stroke="#94A3B8" strokeWidth="2" strokeDasharray="4" />

                <line x1="200" y1="160" x2="120" y2="300" stroke="#10b981" strokeWidth="2" markerEnd="url(#arrow)" />
                <line x1="200" y1="160" x2="280" y2="300" stroke="#10b981" strokeWidth="2" markerEnd="url(#arrow)" />

                <line x1="600" y1="160" x2="520" y2="300" stroke="#10b981" strokeWidth="2" markerEnd="url(#arrow)" />
                <line x1="600" y1="160" x2="680" y2="300" stroke="#10b981" strokeWidth="2" markerEnd="url(#arrow)" />

                {/* Dynamic Referral Loop Link */}
                <path d="M 280 300 Q 400 420 520 300" fill="none" stroke="#f43f5e" strokeWidth="2.5" strokeDasharray="6" markerEnd="url(#arrow)" />
                <text x="400" y="390" textAnchor="middle" fill="#e11d48" fontSize="10" fontWeight="bold">Cross-Facility Referral Link</text>

                {/* Render SVG Nodes */}
                {graphNodes.map((n, idx) => {
                  const x = (idx % 3) * 260 + 140;
                  const y = Math.floor(idx / 3) * 140 + 80;
                  return (
                    <g key={n.id} className="cursor-pointer transform hover:scale-105 transition" onClick={() => handleFacilityClick(parseInt(n.id))}>
                      <rect x={x - 80} y={y - 25} width="160" height="50" rx="10" fill="#ffffff" stroke={n.emergency ? '#f43f5e' : '#10b981'} strokeWidth="2" />
                      <text x={x} y={y - 5} textAnchor="middle" fill="#0f172a" fontSize="11" fontWeight="bold">
                        {n.name}
                      </text>
                      <text x={x} y={y + 12} textAnchor="middle" fill="#64748b" fontSize="9">
                        {n.type}
                      </text>
                    </g>
                  );
                })}
              </svg>

              <div className="absolute bottom-3 left-3 bg-white/90 p-2.5 rounded-lg border border-slate-200 backdrop-blur-xs text-[10px] space-y-1 shadow-xs">
                <span className="font-bold text-slate-800 block">Canvas Graph Legend</span>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-0.5 bg-emerald-500 inline-block" />
                  <span className="text-slate-600">Parent / Child Hierarchy Link</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-0.5 bg-rose-500 border-dashed inline-block" />
                  <span className="text-slate-600">Multi-Destination Referral Routing</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Facility Details Drawer */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-4">
          <h2 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-emerald-600" />
            Selected Facility Inspector
          </h2>

          {selectedFacility ? (
            <div className="space-y-4 text-xs">
              <div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  {selectedFacility.facility_type.replace('_', ' ')}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1">{selectedFacility.facility_name}</h3>
                <p className="text-slate-500 font-mono text-[11px]">{selectedFacility.facility_code}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div>
                  <span className="text-slate-500 text-[10px] block font-semibold">Population Served</span>
                  <span className="font-bold text-slate-900">{selectedFacility.population_served.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block font-semibold">Vulnerable Target</span>
                  <span className="font-bold text-amber-700">{selectedFacility.vulnerable_population.toLocaleString()}</span>
                </div>
              </div>

              <div className="space-y-1.5 text-slate-700">
                <p><strong>District / Zone:</strong> {selectedFacility.district_name || 'BBMP Central'}</p>
                <p><strong>Opening Hours:</strong> {selectedFacility.opening_time} - {selectedFacility.closing_time}</p>
                <p><strong>Configured Services:</strong> {selectedFacility.services}</p>
                <p><strong>Lab / Pharmacy:</strong> {selectedFacility.lab_available ? 'Available' : 'No'} / {selectedFacility.pharmacy_available ? 'Available' : 'No'}</p>
              </div>

              {/* Connected Referral Links */}
              <div className="pt-3 border-t border-slate-100 space-y-2">
                <h4 className="font-bold text-slate-900">Configured Referral Links ({selectedFacility.outgoing_relationships?.length || 0})</h4>
                {selectedFacility.outgoing_relationships && selectedFacility.outgoing_relationships.length > 0 ? (
                  <div className="space-y-2">
                    {selectedFacility.outgoing_relationships.map((rel) => (
                      <div key={rel.id} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-slate-900">{rel.destination_name}</span>
                          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                            {rel.relationship_type}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-600">Service: {rel.service} • Distance: {rel.distance_km} km</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 italic text-[11px]">No direct outgoing referral links defined.</p>
                )}
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400">
              Select any facility from the tree or visual canvas to view details, demographics, and referral links.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
