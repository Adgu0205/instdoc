import React, { useState, useEffect } from 'react';
import Navigation from './components/Navigation';
import UploadZone from './components/UploadZone';
import Dashboard from './components/Dashboard';
import SkeletonDashboard from './components/SkeletonDashboard';
import { AlertCircle, RefreshCcw } from 'lucide-react';
import { analyzeFileWithProgress, analyzeText, getAnalytics, API_BASE_URL } from './services/api';

function App() {
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('Initializing');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  
  // Track submission details to enable retry functionality
  const [lastSubmission, setLastSubmission] = useState(null);
  // Anonymized stats from backend
  const [stats, setStats] = useState(null);

  // Fetch stats on mount and whenever analysis state changes
  useEffect(() => {
    let active = true;
    const fetchStats = async () => {
      const data = await getAnalytics();
      if (data && active) {
        setStats(data);
      }
    };
    fetchStats();
    return () => { active = false; };
  }, [analysisData]);

  const handleAnalysisComplete = (data) => {
    setError(null);
    setAnalysisData(data);
    setIsLoading(false);
  };

  const handleError = (errMsg) => {
    setError(errMsg);
    setAnalysisData(null);
    setIsLoading(false);
  };

  const handleReset = () => {
    setAnalysisData(null);
    setError(null);
    setProgress(0);
  };

  // 1. File Upload Handler (Tracks Upload progress + SSE)
  const handleFileAnalysis = async (file) => {
    setError(null);
    setIsLoading(true);
    setLoadingStage('Uploading');
    setProgress(0);
    setLastSubmission({ type: 'file', file });

    try {
      // Upload progress maps to 0% - 30% of total bar
      const response = await analyzeFileWithProgress(file, (percent) => {
        setProgress(Math.round(percent * 0.3));
        if (percent === 100) {
          setLoadingStage('Parsing');
        }
      });
      handleServerResponse(response);
    } catch (err) {
      handleError(err.message || 'An error occurred during file upload and analysis.');
    }
  };

  // 2. Text Analysis Handler
  const handleTextAnalysis = async (text) => {
    setError(null);
    setIsLoading(true);
    setLoadingStage('Submitting');
    setProgress(5);
    setLastSubmission({ type: 'text', text });

    try {
      const response = await analyzeText(text);
      handleServerResponse(response);
    } catch (err) {
      handleError(err.message || 'An error occurred during text resubmission.');
    }
  };

  // 3. Central Router for Async/Sync endpoints
  const handleServerResponse = (response) => {
    if (response.taskId) {
      // Connect to Server-Sent Events stream for background execution
      connectToSSE(response.taskId);
    } else {
      // Synchronous return for small files
      setProgress(100);
      setTimeout(() => {
        handleAnalysisComplete(response);
      }, 500);
    }
  };

  // 4. SSE Stream connection
  const connectToSSE = (taskId) => {
    const eventSource = new EventSource(`${API_BASE_URL}/api/analyze/stream/${taskId}`);

    eventSource.addEventListener('progress', (e) => {
      try {
        const update = JSON.parse(e.data);
        setLoadingStage(update.stage);
        setProgress(update.progress);
      } catch (err) {
        console.error('Error parsing SSE progress:', err);
      }
    });

    eventSource.addEventListener('completed', (e) => {
      try {
        const result = JSON.parse(e.data);
        setProgress(100);
        setTimeout(() => {
          handleAnalysisComplete(result);
          eventSource.close();
        }, 500);
      } catch (err) {
        handleError('Failed to decode structured report payload.');
        eventSource.close();
      }
    });

    eventSource.addEventListener('failed', (e) => {
      try {
        const data = JSON.parse(e.data);
        handleError(data.error || 'Background contract analysis failed.');
      } catch (err) {
        handleError('Analysis task failed on backend.');
      }
      eventSource.close();
    });

    eventSource.onerror = () => {
      handleError('Connection to processing engine lost. Please check connection and retry.');
      eventSource.close();
    };
  };

  // 5. Retry trigger
  const handleRetry = () => {
    if (!lastSubmission) return;
    if (lastSubmission.type === 'file') {
      handleFileAnalysis(lastSubmission.file);
    } else if (lastSubmission.type === 'text') {
      handleTextAnalysis(lastSubmission.text);
    }
  };

  return (
    <div className="min-h-screen bg-cream text-charcoal flex flex-col justify-between selection:bg-editorial-gold selection:text-white">
      <div>
        {/* Newspaper Masthead */}
        <Navigation />

        <main className="max-w-7xl mx-auto px-4 md:px-8 py-4">
          {/* Error Message styled as a newspaper correction/retraction box */}
          {error && (
            <div className="max-w-4xl mx-auto mb-6 border border-editorial-red bg-red-50/50 p-5 animate-[fadeIn_0.2s_ease-out]">
              <div className="flex gap-4 items-start">
                <AlertCircle className="w-5 h-5 text-editorial-red shrink-0 mt-0.5" />
                <div className="space-y-3 w-full">
                  <h4 className="font-serif font-black text-sm uppercase tracking-wider text-ink border-b border-red-200 pb-1">
                    System Exception Report
                  </h4>
                  <p className="text-xs text-stone-600 font-mono bg-white p-3 border border-stone-250 overflow-x-auto whitespace-pre-wrap">
                    {error}
                  </p>
                  <div className="flex gap-2">
                    {lastSubmission && (
                      <button
                        onClick={handleRetry}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-serif font-bold uppercase tracking-wider border border-charcoal bg-charcoal text-cream hover:bg-white hover:text-charcoal transition-colors duration-150"
                      >
                        <RefreshCcw className="w-3 h-3" />
                        Retry Analysis
                      </button>
                    )}
                    <button
                      onClick={() => setError(null)}
                      className="px-3 py-1.5 text-[10px] font-serif font-bold uppercase tracking-wider border border-stone-300 bg-white hover:bg-stone-100 text-stone-700 transition-colors duration-150"
                    >
                      Dismiss Report
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Interactive Flow */}
          {isLoading ? (
            <SkeletonDashboard stage={loadingStage} progress={progress} />
          ) : !analysisData ? (
            <div className="space-y-6 animate-[fadeIn_0.3s_ease-out]">
              {/* Headline Intro */}
              <div className="max-w-4xl mx-auto text-center mt-8 space-y-3">
                <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono font-bold bg-stone-100 px-3 py-1 border border-editorial-border">
                  Legal Document Intelligence
                </span>
                <h2 className="font-serif font-black text-3xl md:text-5xl text-ink leading-tight">
                  Evidence-Based Contract Assessment & Auditing
                </h2>
                <p className="text-sm md:text-base text-stone-600 max-w-2xl mx-auto font-serif leading-relaxed">
                  Analyze agreement structures to identify safeguards, standard procedural boilerplate, and risk exposure, translating complex legal terminology into actionable negotiation items.
                </p>

                {/* Audit Stats Block */}
                {stats && stats.total_analyzed > 0 && (
                  <div className="border-double border-4 border-editorial-border p-4 bg-paper max-w-md mx-auto mt-6 font-serif text-charcoal">
                    <h4 className="text-center font-black uppercase text-[10px] tracking-widest border-b border-editorial-border pb-1 mb-2.5">
                      Contract Audit Statistics
                    </h4>
                    <div className="grid grid-cols-3 gap-2 text-center items-center">
                      <div className="border-r border-editorial-border">
                        <span className="block font-mono text-xl font-bold">{stats.total_analyzed}</span>
                        <span className="text-[8px] uppercase tracking-widest text-stone-500 font-sans">Audits Conducted</span>
                      </div>
                      <div className="border-r border-editorial-border">
                        <span className="block font-mono text-xl font-bold text-editorial-red">{stats.average_risk_score}%</span>
                        <span className="text-[8px] uppercase tracking-widest text-stone-500 font-sans">Avg Risk Score</span>
                      </div>
                      <div>
                        <span className="block font-sans font-bold text-[10px] uppercase tracking-wider truncate px-1 text-editorial-gold">
                          {Object.keys(stats.contract_types).reduce((a, b) => stats.contract_types[a] > stats.contract_types[b] ? a : b, 'NDA')
                            .replace(/Contract|Agreement/gi, '').trim() || 'NDA'}
                        </span>
                        <span className="text-[8px] uppercase tracking-widest text-stone-500 font-sans">Top Document</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Upload panel */}
              <UploadZone
                onFileSelected={handleFileAnalysis}
                onTextSubmitted={handleTextAnalysis}
              />

              {/* Legal Features Column Grid */}
              <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 pt-12 border-t border-editorial-border">
                <div className="space-y-1.5">
                  <h4 className="font-serif font-bold text-xs uppercase tracking-wider text-ink border-b border-editorial-border pb-1">
                    01. Risk & Protective Clause Audit
                  </h4>
                  <p className="text-[11px] text-stone-500 leading-relaxed">
                    Verify the exact balance of favorable safeguards, standard procedural clauses, and one-sided liabilities.
                  </p>
                </div>
                <div className="space-y-1.5">
                  <h4 className="font-serif font-bold text-xs uppercase tracking-wider text-ink border-b border-editorial-border pb-1">
                    02. Omission & Completeness Check
                  </h4>
                  <p className="text-[11px] text-stone-500 leading-relaxed">
                    Analyze the document's structure for missing protections like liability limits, payment cure windows, or termination rights.
                  </p>
                </div>
                <div className="space-y-1.5">
                  <h4 className="font-serif font-bold text-xs uppercase tracking-wider text-ink border-b border-editorial-border pb-1">
                    03. Scenario-Based Simulation
                  </h4>
                  <p className="text-[11px] text-stone-500 leading-relaxed">
                    Model contract performance outcomes to predict financial and legal liabilities under scenarios like early exits or payment defaults.
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
