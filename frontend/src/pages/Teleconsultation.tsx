import React, { useState } from 'react';
import { Video, PhoneCall, Mic, MicOff } from 'lucide-react';

export const Teleconsultation: React.FC = () => {
  const [inCall, setInCall] = useState(false);
  const [muted, setMuted] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Video className="w-6 h-6 text-purple-600" />
          Internal Simulated Teleconsultation Workspace
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Doctor-to-Specialist virtual consultation workflow (Offline local simulation mode)
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Video Canvas Simulation */}
        <div className="lg:col-span-2 glass-panel p-4 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
          <div className="relative w-full h-[400px] bg-slate-900 rounded-xl border border-slate-700 overflow-hidden flex flex-col justify-between p-4">
            {/* Top Video Header */}
            <div className="flex justify-between items-center z-10 bg-slate-800/90 p-2.5 rounded-lg border border-slate-700 text-white">
              <div>
                <span className="font-bold text-xs block">Specialist Hub: Victoria Hospital Cardiology</span>
                <span className="text-[10px] text-emerald-400 font-semibold">Dr. K. V. Sharma (Senior Cardiologist)</span>
              </div>
              <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${inCall ? 'bg-emerald-500/20 text-emerald-300 animate-pulse' : 'bg-slate-700 text-slate-300'}`}>
                {inCall ? 'LIVE SIMULATED CALL' : 'STANDBY'}
              </span>
            </div>

            {/* Video Body Content */}
            <div className="flex-1 flex items-center justify-center relative">
              {inCall ? (
                <div className="text-center space-y-2">
                  <div className="w-24 h-24 rounded-full bg-indigo-600/30 border-2 border-indigo-400 mx-auto flex items-center justify-center text-indigo-300 font-bold text-2xl animate-pulse">
                    DR
                  </div>
                  <p className="text-xs font-semibold text-slate-200">Connected with Victoria Hospital Specialist</p>
                  <p className="text-[10px] text-slate-400 font-mono">Audio / Video Streams Active (Local Simulation)</p>
                </div>
              ) : (
                <div className="text-center space-y-2">
                  <Video className="w-12 h-12 text-slate-500 mx-auto" />
                  <p className="text-xs text-slate-400">Click "Start Simulated Teleconsultation" to launch video consult</p>
                </div>
              )}

              {/* Self Video PiP */}
              <div className="absolute bottom-4 right-4 w-32 h-24 bg-slate-800 rounded-lg border border-slate-600 flex flex-col justify-end p-2 text-white">
                <span className="text-[9px] font-bold">Rural Clinic A4 (MO)</span>
              </div>
            </div>

            {/* Video Control Bar */}
            <div className="flex justify-center items-center gap-3 z-10 bg-slate-800/90 p-3 rounded-xl border border-slate-700">
              <button
                onClick={() => setMuted(!muted)}
                className={`p-3 rounded-full transition ${muted ? 'bg-rose-600 text-white' : 'bg-slate-700 text-slate-200'}`}
              >
                {muted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>

              {inCall ? (
                <button
                  onClick={() => setInCall(false)}
                  className="px-6 py-2.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl shadow-md"
                >
                  End Teleconsult
                </button>
              ) : (
                <button
                  onClick={() => setInCall(true)}
                  className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-md flex items-center gap-2"
                >
                  <PhoneCall className="w-4 h-4" />
                  <span>Start Simulated Teleconsultation</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Teleconsult Patient Case Summary */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-4 text-xs shadow-xs">
          <h2 className="font-bold text-slate-900 pb-2 border-b border-slate-100">Active Teleconsultation Case</h2>
          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2">
            <span className="font-bold text-slate-900 text-sm block">Ramesh Kumar (52/M)</span>
            <span className="text-slate-600 block font-medium">Chief Complaint: Severe Dizziness & Uncontrolled BP</span>
            <span className="text-emerald-700 font-bold block">Vitals: BP 148/96 mmHg • Glucose 185 mg/dL</span>
          </div>

          <div className="space-y-2">
            <label className="block text-slate-700 font-bold">Specialist Advice Notes</label>
            <textarea
              rows={4}
              placeholder="Record specialist advice received during teleconsultation..."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600 font-medium"
              defaultValue="Specialist recommended upgrading Amlodipine to 10mg OD, adding Telmisartan 40mg, and review in 14 days."
            />
          </div>

          <button
            onClick={() => alert('Teleconsultation advice notes saved to patient visit EMR!')}
            className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded-xl shadow-md"
          >
            Save Advice to Patient Record
          </button>
        </div>
      </div>
    </div>
  );
};
