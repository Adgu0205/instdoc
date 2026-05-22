import React from 'react';
import { EyeOff, AlertTriangle, CheckSquare } from 'lucide-react';

export default function MissingClauses({ missing = [] }) {
  if (!missing || missing.length === 0) {
    return (
      <div className="border border-editorial-border p-6 bg-paper text-center">
        <h3 className="font-serif font-bold text-lg text-ink mb-1">Protections Fully Present</h3>
        <p className="text-xs text-stone-500 uppercase tracking-widest">
          AI analysis confirms all standard security, liability, and refund clauses are included.
        </p>
      </div>
    );
  }

  // Get styles based on severity
  const getSeverityStyles = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'text-red-800 border-red-200 bg-red-50/10';
      case 'HIGH':
        return 'text-orange-850 border-orange-200 bg-orange-50/10';
      case 'MEDIUM':
      default:
        return 'text-amber-800 border-amber-200 bg-amber-50/10';
    }
  };

  // Get border styles based on severity
  const getSeverityBorder = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
      case 'HIGH':
        return 'border-l-4 border-l-editorial-red';
      case 'MEDIUM':
      default:
        return 'border-l-4 border-l-editorial-orange';
    }
  };

  return (
    <div className="border border-editorial-border bg-paper p-6 space-y-6">
      <div className="border-b border-editorial-border pb-4">
        <div className="flex items-center gap-2">
          <EyeOff className="w-5 h-5 text-editorial-gold" />
          <h3 className="font-serif font-black text-xl text-ink uppercase tracking-wide">
            Missing Protections & Vulnerabilities
          </h3>
        </div>
        <p className="text-[11px] text-stone-500 uppercase tracking-widest mt-0.5">
          Vulnerabilities caused by the absence of standard defensive legal clauses
        </p>
      </div>

      <div className="space-y-4">
        {missing.map((clause, index) => (
          <div 
            key={index}
            className={`border p-4 flex flex-col md:flex-row justify-between gap-6 premium-hover ${getSeverityBorder(
              clause.severity
            )} ${getSeverityStyles(
              clause.severity
            )}`}
          >
            {/* Title / Description */}
            <div className="md:w-1/2 space-y-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                <h4 className="font-serif font-bold text-sm md:text-base text-ink">
                  {clause.clause}
                </h4>
                <span className="text-[9px] font-mono px-1.5 py-0.5 bg-stone-100 border border-stone-250 font-bold uppercase">
                  {clause.severity}
                </span>
              </div>
              <p className="text-xs text-stone-600 leading-relaxed font-sans">
                {clause.explanation}
              </p>
            </div>

            {/* Insertion Recommendation */}
            <div className="md:w-1/2 p-3 bg-white border border-editorial-border-light text-xs flex flex-col justify-between">
              <span className="font-serif font-bold text-editorial-gold uppercase tracking-widest text-[9px] block mb-1">
                Insert Recommended Wording
              </span>
              <div className="font-mono text-stone-700 bg-cream-light/40 p-2.5 italic border-l border-editorial-gold leading-relaxed select-all">
                "{clause.suggestion}"
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
