import React from 'react';
import { AlertCircle, Terminal, HelpCircle } from 'lucide-react';

export default function ScamSignals({ signals = [] }) {
  if (!signals || signals.length === 0) {
    return (
      <div className="border border-editorial-border p-6 bg-paper text-center">
        <h3 className="font-serif font-bold text-lg text-ink mb-1">No Deceptive Patterns Detected</h3>
        <p className="text-xs text-stone-500 uppercase tracking-widest">
          AI analysis found no scam signals, hidden fees, or manipulative terms.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-editorial-border bg-paper p-6 space-y-4">
      <div className="border-b border-editorial-border pb-4">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-editorial-red" />
          <h3 className="font-serif font-black text-xl text-ink uppercase tracking-wide">
            Deceptive Pattern Warnings
          </h3>
        </div>
        <p className="text-[11px] text-stone-500 uppercase tracking-widest mt-0.5">
          Scan findings for manipulative clauses, hidden fees, and asymmetric liabilities
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {signals.map((sig, index) => (
          <div 
            key={index}
            className="border-l-4 border-editorial-red bg-red-50/30 p-4 border border-y-stone-200 border-r-stone-200 premium-hover"
          >
            <div className="flex justify-between items-center mb-1.5">
              <h4 className="font-serif font-bold text-sm text-red-950">
                {sig.pattern}
              </h4>
              <span className="px-1.5 py-0.5 text-[8px] font-mono font-bold bg-editorial-red text-white uppercase tracking-widest">
                {sig.severity || 'CRITICAL'}
              </span>
            </div>
            <p className="text-xs text-stone-600 leading-relaxed font-sans">
              {sig.explanation}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
