import React, { useState } from 'react';
import { AlertOctagon, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

export default function RiskList({ risks = [] }) {
  const [expandedIndices, setExpandedIndices] = useState(
    risks.reduce((acc, _, index) => {
      // Expand critical and high risks by default
      if (risks[index].severity === 'CRITICAL' || risks[index].severity === 'HIGH') {
        acc[index] = true;
      }
      return acc;
    }, {})
  );

  const toggleExpand = (index) => {
    setExpandedIndices(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  if (!risks || risks.length === 0) {
    return (
      <div className="border border-editorial-border p-6 bg-paper text-center">
        <h3 className="font-serif font-bold text-lg text-ink mb-1">No Clause Risks Detected</h3>
        <p className="text-xs text-stone-500 uppercase tracking-widest">
          AI analysis found no specific risky clauses. Review missing clauses and scam signals.
        </p>
      </div>
    );
  }

  // Get color styles for badge
  const getSeverityBadge = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-800 text-white';
      case 'HIGH':
        return 'bg-orange-700 text-white';
      case 'MEDIUM':
        return 'bg-amber-600 text-white';
      case 'SAFE':
      default:
        return 'bg-emerald-800 text-white';
    }
  };

  return (
    <div className="border border-editorial-border bg-paper p-6 space-y-6">
      <div className="border-b border-editorial-border pb-4">
        <h3 className="font-serif font-black text-xl text-ink uppercase tracking-wide">
          Risky Clauses & Highlighted Provisions
        </h3>
        <p className="text-[11px] text-stone-500 uppercase tracking-widest mt-0.5">
          Detailed breakdown of identified legal vulnerabilities & renegotiation protocols
        </p>
      </div>

      <div className="space-y-4">
        {risks.map((risk, index) => {
          const isExpanded = expandedIndices[index];
          const isSeverityHigh = risk.severity === 'CRITICAL' || risk.severity === 'HIGH';

          return (
            <div 
              key={index} 
              className={`border transition-all duration-200 ${
                isSeverityHigh ? 'border-editorial-border' : 'border-stone-200'
              }`}
            >
              {/* Header Toggle */}
              <button
                onClick={() => toggleExpand(index)}
                className="w-full flex items-center justify-between p-4 bg-cream-light hover:bg-stone-50 text-left transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 text-[9px] font-mono font-bold tracking-widest uppercase ${getSeverityBadge(risk.severity)}`}>
                    {risk.severity}
                  </span>
                  <h4 className="font-serif font-bold text-sm md:text-base text-ink">
                    {risk.clauseName}
                  </h4>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-stone-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-stone-500" />
                )}
              </button>

              {/* Collapsible Content */}
              {isExpanded && (
                <div className="p-4 bg-white border-t border-editorial-border-light space-y-4 animate-[fadeIn_0.2s_ease-out]">
                  {/* Extract Text Quote */}
                  <div>
                    <span className="text-[9px] uppercase tracking-widest text-stone-400 font-mono block mb-1">
                      Matched Document Text
                    </span>
                    <blockquote className="border-l-2 border-editorial-gold pl-3 py-1 font-mono text-[11px] md:text-xs text-stone-700 leading-relaxed italic bg-cream-light/30">
                      "{risk.text}"
                    </blockquote>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-stone-100 text-xs">
                    {/* Plain English Explanation */}
                    <div className="space-y-1">
                      <span className="font-serif font-bold text-ink uppercase tracking-wide block">
                        Plain-English Translation
                      </span>
                      <p className="text-stone-600 leading-relaxed">
                        {risk.explanation}
                      </p>
                    </div>

                    {/* Negotiation Advice */}
                    <div className="space-y-1">
                      <span className="font-serif font-bold text-editorial-gold uppercase tracking-wide block">
                        Negotiation Recommendation
                      </span>
                      <p className="text-stone-700 leading-relaxed font-serif italic bg-amber-50/40 p-2 border border-amber-800/10">
                        {risk.suggestion}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
