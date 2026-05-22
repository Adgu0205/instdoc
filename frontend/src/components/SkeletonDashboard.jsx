import React from 'react';
import { Loader2, Sparkles, FileText, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function SkeletonDashboard({ stage = 'Processing', progress = 0 }) {
  // Map stages to step completion status
  const stages = [
    { name: 'Parsing', minProg: 15 },
    { name: 'Risk Analysis', minProg: 40 },
    { name: 'AI Processing', minProg: 65 },
    { name: 'Generating Report', minProg: 90 }
  ];

  const getStageStatus = (item) => {
    if (progress >= 100) return 'complete';
    
    // Find index of current stage
    const currentStageIndex = stages.findIndex(s => s.name === stage);
    const itemStageIndex = stages.findIndex(s => s.name === item.name);
    
    if (itemStageIndex < currentStageIndex) return 'complete';
    if (itemStageIndex === currentStageIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 md:px-8 py-6 space-y-8 bg-cream">
      {/* Top Controls Shimmer */}
      <div className="flex justify-between items-center border-b border-editorial-border pb-3">
        <div className="h-4 w-48 bg-stone-300 animate-pulse" />
        <div className="h-8 w-44 bg-stone-300 animate-pulse" />
      </div>

      {/* Progress & Stage Status Display */}
      <div className="border border-editorial-border p-6 bg-paper space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-editorial-border-light pb-4">
          <div>
            <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono block mb-1">
              Assessment In Progress
            </span>
            <h2 className="font-serif font-black text-2xl md:text-3xl text-ink uppercase tracking-wide flex items-center gap-2">
              <Loader2 className="w-6 h-6 animate-spin text-editorial-gold" />
              Scanning Document
            </h2>
          </div>
          <div className="text-right w-full md:w-auto">
            <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono block mb-0.5">
              Overall Progress
            </span>
            <span className="font-mono text-3xl font-bold text-editorial-gold tracking-tight">
              {progress}%
            </span>
          </div>
        </div>

        {/* Newspaper Progress Bar */}
        <div className="w-full h-4 bg-stone-100 border border-editorial-border relative overflow-hidden">
          <div 
            className="h-full bg-editorial-gold border-r border-editorial-border transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
          {/* Shimmer overlay for bar */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full animate-[shimmer_1.5s_infinite]" />
        </div>

        {/* Stage Timeline */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stages.map((stg) => {
            const status = getStageStatus(stg);
            return (
              <div 
                key={stg.name}
                className={`border p-3 flex flex-col justify-between transition-colors duration-150 ${
                  status === 'complete' 
                    ? 'border-editorial-green bg-green-50/10 text-green-900' 
                    : status === 'active'
                    ? 'border-editorial-gold bg-amber-50/10 text-amber-950 font-bold shadow-sm'
                    : 'border-editorial-border-light bg-stone-50/40 text-stone-400'
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[9px] font-mono uppercase tracking-widest">
                    {status === 'complete' ? 'Done' : status === 'active' ? 'Running' : 'Queued'}
                  </span>
                  {status === 'complete' && <CheckCircle2 className="w-3.5 h-3.5 text-editorial-green" />}
                  {status === 'active' && <Sparkles className="w-3.5 h-3.5 text-editorial-gold animate-pulse" />}
                </div>
                <h4 className="font-serif text-xs md:text-sm uppercase tracking-wider mt-1">
                  {stg.name}
                </h4>
              </div>
            );
          })}
        </div>
      </div>

      {/* Shimmer Layout mimicking the Dashboard */}
      <div className="space-y-8 pointer-events-none opacity-60">
        {/* Shimmer Header */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 border-b border-editorial-border pb-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="border border-editorial-border p-4 bg-paper space-y-2">
              <div className="h-3 w-16 bg-stone-300 animate-pulse" />
              <div className="h-6 w-28 bg-stone-300 animate-pulse" />
            </div>
          ))}
        </div>

        {/* Shimmer Executive Summary */}
        <div className="border-b border-editorial-border pb-8 space-y-3">
          <div className="h-3 w-32 bg-stone-300 animate-pulse" />
          <div className="h-4 w-full bg-stone-300 animate-pulse" />
          <div className="h-4 w-5/6 bg-stone-300 animate-pulse" />
          <div className="h-4 w-4/6 bg-stone-300 animate-pulse" />
        </div>

        {/* Shimmer Multi-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left: Action items (5 Things You Must Know) */}
          <div className="lg:col-span-4 border border-editorial-border p-6 bg-paper space-y-6">
            <div className="h-4 w-32 bg-stone-300 animate-pulse" />
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="flex gap-2">
                  <div className="h-5 w-5 rounded bg-stone-300 shrink-0 animate-pulse" />
                  <div className="space-y-2 w-full">
                    <div className="h-3.5 w-full bg-stone-300 animate-pulse" />
                    <div className="h-3 w-5/6 bg-stone-300 animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Heatmap and Lists */}
          <div className="lg:col-span-8 space-y-8">
            {/* Shimmer Featured Box */}
            <div className="border border-editorial-border bg-paper p-6 space-y-4">
              <div className="h-3 w-36 bg-stone-300 animate-pulse" />
              <div className="h-6 w-3/4 bg-stone-300 animate-pulse" />
              <div className="h-3.5 w-full bg-stone-300 animate-pulse" />
              <div className="h-12 w-full bg-stone-200 animate-pulse" />
              <div className="h-10 w-full bg-stone-100 border border-stone-200 animate-pulse" />
            </div>

            {/* Shimmer Heatmap Grid */}
            <div className="border border-editorial-border p-6 bg-paper space-y-4">
              <div className="h-4 w-40 bg-stone-300 animate-pulse" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                  <div key={i} className="h-10 bg-stone-250 animate-pulse" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
