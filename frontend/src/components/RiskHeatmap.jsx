import React, { useState } from 'react';
import { Sparkles, MessageSquareWarning, Eye } from 'lucide-react';

export default function RiskHeatmap({ matches = [] }) {
  const [selectedMatch, setSelectedMatch] = useState(null);

  if (!matches || matches.length === 0) {
    return (
      <div className="border border-editorial-border p-6 bg-paper text-center">
        <h3 className="font-serif font-bold text-lg text-ink mb-1">Baseline Scanner Clear</h3>
        <p className="text-xs text-stone-500 uppercase tracking-widest">
          No deterministic keyword risk patterns matched in the document.
        </p>
      </div>
    );
  }

  // Get color styles for heatmap blocks based on severity
  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 hover:bg-red-200 border-red-300 text-red-900';
      case 'HIGH':
        return 'bg-orange-100 hover:bg-orange-200 border-orange-300 text-orange-900';
      case 'MEDIUM':
        return 'bg-amber-100 hover:bg-amber-200 border-amber-300 text-amber-900';
      case 'LOW':
      default:
        return 'bg-stone-100 hover:bg-stone-200 border-stone-200 text-stone-700';
    }
  };

  return (
    <div className="border border-editorial-border bg-paper p-6">
      <div className="flex items-center justify-between border-b border-editorial-border pb-4 mb-4">
        <div>
          <h3 className="font-serif font-black text-xl text-ink uppercase tracking-wide">
            Clause Signature Heatmap
          </h3>
          <p className="text-[11px] text-stone-500 uppercase tracking-widest mt-0.5">
            Deterministic Rule Engine Matches ({matches.length} Alerts Detected)
          </p>
        </div>
        <span className="text-xs font-serif italic text-stone-600 bg-stone-100 px-3 py-1 border border-editorial-border">
          Click blocks to inspect clauses
        </span>
      </div>

      {/* Grid of matches */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
        {matches.map((match) => (
          <button
            key={match.id}
            onClick={() => setSelectedMatch(selectedMatch?.id === match.id ? null : match)}
            className={`p-3 border text-left flex flex-col justify-between transition-all duration-200 relative h-28 group ${getSeverityColor(
              match.severity
            )} ${selectedMatch?.id === match.id ? 'ring-2 ring-charcoal' : ''}`}
          >
            <div className="flex justify-between items-start w-full">
              <span className="text-[9px] uppercase tracking-widest font-mono opacity-80">
                {match.severity}
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.5 bg-white/60 border border-black/5 font-mono">
                +{match.scoreImpact}
              </span>
            </div>
            
            <div className="mt-2">
              <h4 className="font-serif font-bold text-xs leading-tight line-clamp-2">
                {match.name}
              </h4>
              <p className="text-[10px] opacity-75 font-mono mt-0.5">
                {match.occurrenceCount} {match.occurrenceCount === 1 ? 'match' : 'matches'}
              </p>
            </div>

            <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Eye className="w-3.5 h-3.5" />
            </div>
          </button>
        ))}
      </div>

      {/* Expanded Match Details */}
      {selectedMatch && (
        <div className="mt-6 border-t border-editorial-border pt-6 animate-[fadeIn_0.3s_ease-out]">
          <div className="bg-cream-light border border-editorial-border p-4">
            <div className="flex justify-between items-start gap-4 mb-2">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 text-[9px] font-mono font-bold uppercase bg-charcoal text-white">
                  {selectedMatch.severity}
                </span>
                <h4 className="font-serif font-black text-base text-ink">
                  {selectedMatch.name}
                </h4>
              </div>
              <span className="text-xs font-mono text-stone-500">
                Risk Engine Penalty: +{selectedMatch.scoreImpact}
              </span>
            </div>
            
            {/* Clause Snippet Highlight */}
            <div className="mb-4">
              <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono block mb-1">
                Contract Clause Snippet
              </span>
              <div className="p-3 bg-white border border-editorial-border-light text-xs font-mono text-stone-800 leading-relaxed italic select-all whitespace-pre-wrap">
                {selectedMatch.snippet}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="font-serif font-bold text-stone-800 block mb-0.5">
                  Why this is dangerous:
                </span>
                <p className="text-stone-600 leading-relaxed">
                  {selectedMatch.explanation}
                </p>
              </div>
              <div>
                <span className="font-serif font-bold text-stone-800 block mb-0.5">
                  How to renegotiate:
                </span>
                <p className="text-stone-600 leading-relaxed">
                  {selectedMatch.suggestion}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
