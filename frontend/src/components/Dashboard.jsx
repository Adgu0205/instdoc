import React from 'react';
import RiskHeader from './RiskHeader';
import RiskHeatmap from './RiskHeatmap';
import RiskList from './RiskList';
import ScamSignals from './ScamSignals';
import MissingClauses from './MissingClauses';
import Simulations from './Simulations';
import ActionItems from './ActionItems';
import { AlertOctagon, HelpCircle, FileText, CornerDownRight } from 'lucide-react';

export default function Dashboard({ data, onReset }) {
  if (!data) return null;

  // Find the single most dangerous clause (critical or high severity)
  const sortedRisks = [...(data.risks || [])].sort((a, b) => {
    const severityWeight = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'SAFE': 1 };
    return (severityWeight[b.severity] || 0) - (severityWeight[a.severity] || 0);
  });

  const chiefConcern = sortedRisks.length > 0 ? sortedRisks[0] : null;

  return (
    <div className="w-full max-w-7xl mx-auto px-4 md:px-8 py-6 space-y-8 bg-cream animate-[fadeIn_0.5s_ease-out]">
      {/* Top Controls */}
      <div className="flex justify-between items-center border-b border-editorial-border pb-3">
        <span className="text-xs font-mono uppercase text-stone-500">
          Journal Reference ID: #{Math.random().toString(36).substr(2, 9).toUpperCase()}
        </span>
        <button
          onClick={onReset}
          className="px-4 py-1.5 text-xs font-serif font-bold uppercase tracking-wider border border-charcoal bg-white hover:bg-charcoal hover:text-cream transition-colors duration-150"
        >
          Analyze Another Contract
        </button>
      </div>

      {/* 1. Header (Badge, Score, Classification) */}
      <RiskHeader
        contractType={data.contractType}
        overallRisk={data.overallRisk}
        riskLevel={data.riskLevel}
        confidence={data.confidence}
        apiWarning={data.apiWarning}
      />

      {/* 2. Executive Editorial Summary */}
      <div className="border-b border-editorial-border pb-8">
        <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono block mb-1">
          Executive Opinion
        </span>
        <p className="newspaper-lead font-serif text-ink text-lg leading-relaxed italic first-letter:text-5xl first-letter:font-bold first-letter:float-left first-letter:mr-3 first-letter:mt-1 first-letter:text-editorial-gold">
          {data.summary}
        </p>
      </div>

      {/* 3. Multi-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Action Items (5 Things You Must Know) - Occupies 4 Cols */}
        <div className="lg:col-span-4 space-y-6">
          <ActionItems thingsToKnow={data.thingsToKnow} />
        </div>

        {/* Right Column: Heatmap, Most Dangerous Clause, & Risks List - Occupies 8 Cols */}
        <div className="lg:col-span-8 space-y-8">
          {/* Most Dangerous Clause Featured Box */}
          {chiefConcern && (
            <div className="border border-editorial-border bg-paper p-6 relative overflow-hidden">
              {/* Highlight ribbon */}
              <div className="absolute top-0 right-0 w-24 h-24 bg-red-50 text-red-800 border-l border-b border-editorial-border flex items-center justify-center font-mono font-bold text-[9px] uppercase tracking-wider rotate-45 translate-x-7 -translate-y-7 shadow-sm">
                Concern
              </div>
              <span className="text-[9px] uppercase tracking-widest text-editorial-red font-mono font-bold flex items-center gap-1.5 mb-1.5">
                <AlertOctagon className="w-3.5 h-3.5" />
                Featured Editorial: Chief Clause Concern
              </span>
              <h3 className="font-serif font-black text-2xl text-ink mb-3 leading-tight">
                Dangerous exposure detected in {chiefConcern.clauseName} clause
              </h3>
              
              <p className="text-xs text-stone-600 leading-relaxed font-sans mb-4">
                "{chiefConcern.explanation}"
              </p>

              <div className="p-3 bg-red-50/20 border-l-2 border-editorial-red text-xs italic font-mono text-stone-700 mb-4">
                "{chiefConcern.text}"
              </div>

              <div className="flex gap-2 items-start text-xs bg-stone-50 border border-stone-200 p-3">
                <CornerDownRight className="w-4 h-4 text-editorial-gold shrink-0 mt-0.5" />
                <div>
                  <span className="font-serif font-bold text-ink">Proposed Redline Amendment: </span>
                  <span className="text-stone-600 font-serif">{chiefConcern.suggestion}</span>
                </div>
              </div>
            </div>
          )}

          {/* Heatmap Grid */}
          <RiskHeatmap matches={data.deterministicMatches} />

          {/* AI Detailed Risks List */}
          <RiskList risks={data.risks} />
        </div>
      </div>

      {/* 4. Scam Signals & Missing Protections Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 border-t border-editorial-border pt-8">
        <ScamSignals signals={data.scamSignals} />
        <MissingClauses missing={data.missingClauses} />
      </div>

      {/* 5. Consequence Simulation Panel */}
      <div className="border-t border-editorial-border pt-8">
        <Simulations simulations={data.simulations} />
      </div>

      {/* Privacy disclaimer footer */}
      <div className="text-center pt-8 border-t border-stone-200 text-[10px] text-stone-400 uppercase tracking-widest">
        Veritas Ledger Legal Engine • All computations are run in sandboxed memory. Uploads are strictly deleted upon final output delivery.
      </div>
    </div>
  );
}
