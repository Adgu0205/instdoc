import React, { useState } from 'react';
import Navigation from './components/Navigation';
import UploadZone from './components/UploadZone';
import Dashboard from './components/Dashboard';
import { AlertCircle } from 'lucide-react';

function App() {
  const [analysisData, setAnalysisData] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalysisComplete = (data) => {
    setError(null);
    setAnalysisData(data);
  };

  const handleError = (errMsg) => {
    setError(errMsg);
    setAnalysisData(null);
  };

  const handleReset = () => {
    setAnalysisData(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-cream text-charcoal flex flex-col justify-between selection:bg-editorial-gold selection:text-white">
      <div>
        {/* Newspaper Masthead */}
        <Navigation />

        <main className="max-w-7xl mx-auto px-4 md:px-8 py-4">
          {/* Error Message styled as a newspaper correction/retraction box */}
          {error && (
            <div className="max-w-4xl mx-auto mb-6 border border-editorial-red bg-red-50/50 p-4 animate-[fadeIn_0.2s_ease-out]">
              <div className="flex gap-3 items-start">
                <AlertCircle className="w-5 h-5 text-editorial-red shrink-0 mt-0.5" />
                <div className="space-y-2">
                  <h4 className="font-serif font-black text-sm uppercase tracking-wider text-ink">
                    System Exception Report
                  </h4>
                  <p className="text-xs text-stone-600 font-mono bg-white p-3 border border-stone-200 overflow-x-auto whitespace-pre-wrap">
                    {error}
                  </p>
                  <button
                    onClick={() => setError(null)}
                    className="px-3 py-1 text-[10px] font-serif font-bold uppercase tracking-wider border border-charcoal bg-white hover:bg-charcoal hover:text-cream transition-colors duration-150"
                  >
                    Dismiss Report
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Interactive Flow */}
          {!analysisData ? (
            <div className="space-y-6">
              {/* Headline Article Intro */}
              <div className="max-w-4xl mx-auto text-center mt-8 space-y-3">
                <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono font-bold bg-stone-100 px-3 py-1 border border-editorial-border">
                  Daily Editorial Feature
                </span>
                <h2 className="font-serif font-black text-3xl md:text-5xl text-ink leading-tight">
                  Demystifying one-sided contracts.
                </h2>
                <p className="text-sm md:text-base text-stone-600 max-w-2xl mx-auto font-serif italic leading-relaxed">
                  "Most agreements are drafted to shield the party that writes them. Veritas Ledger runs a hybrid scan to isolate hidden liabilities, flag missing protections, and translate legal jargon into plain-English negotiation redlines."
                </p>
              </div>

              {/* Upload panel */}
              <UploadZone
                onAnalysisComplete={handleAnalysisComplete}
                onError={handleError}
              />

              {/* Editorial bottom feature boxes (decorative columns to feel premium) */}
              <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 pt-12 border-t border-editorial-border">
                <div className="space-y-1.5">
                  <h4 className="font-serif font-bold text-xs uppercase tracking-wider text-ink border-b border-editorial-border pb-1">
                    01. Scan for Predatory Clauses
                  </h4>
                  <p className="text-[11px] text-stone-500 leading-relaxed">
                    Identify unlimited liabilities, automatic renewals, non-competes, and binding jury waivers. Review visual contract extracts.
                  </p>
                </div>
                <div className="space-y-1.5">
                  <h4 className="font-serif font-bold text-xs uppercase tracking-wider text-ink border-b border-editorial-border pb-1">
                    02. Highlight Omissions
                  </h4>
                  <p className="text-[11px] text-stone-500 leading-relaxed">
                    Contracts often harm you by what they leave out. Verify the absence of refund rights, payment grace periods, or mutual exit terms.
                  </p>
                </div>
                <div className="space-y-1.5">
                  <h4 className="font-serif font-bold text-xs uppercase tracking-wider text-ink border-b border-editorial-border pb-1">
                    03. Run Scenario Trials
                  </h4>
                  <p className="text-[11px] text-stone-500 leading-relaxed">
                    Forecast dispute outcomes using the consequence simulator. Predict liability under early exit terms or default notice windows.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <Dashboard data={analysisData} onReset={handleReset} />
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="w-full border-t border-editorial-border bg-stone-50 mt-16 py-8 px-4 text-center text-[10px] text-stone-550 uppercase tracking-widest space-y-2">
        <p>© 2026 Veritas Ledger Publishing Group. All Rights Reserved.</p>
        <p className="text-stone-405 font-sans normal-case text-stone-400">
          Disclaimer: Veritas Ledger is an AI-assisted analysis tool and does not constitute formal legal counsel. For complex disputes, always seek bar-admitted legal advice.
        </p>
      </footer>
    </div>
  );
}

export default App;
