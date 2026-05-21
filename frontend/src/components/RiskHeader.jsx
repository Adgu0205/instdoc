import React from 'react';
import { Shield, ShieldAlert, ShieldCheck, Activity, Award } from 'lucide-react';

export default function RiskHeader({ contractType, overallRisk, riskLevel, confidence, apiWarning }) {
  // Determine styling based on risk level
  const getRiskStyles = (level) => {
    switch (level?.toUpperCase()) {
      case 'SAFE':
        return {
          bg: 'bg-emerald-50/70 border-emerald-200',
          text: 'text-emerald-900',
          accent: 'bg-emerald-800',
          border: 'border-emerald-800/10',
          icon: ShieldCheck
        };
      case 'LOW RISK':
        return {
          bg: 'bg-yellow-50/80 border-yellow-200',
          text: 'text-yellow-900',
          accent: 'bg-yellow-600',
          border: 'border-yellow-600/10',
          icon: Shield
        };
      case 'MODERATE RISK':
        return {
          bg: 'bg-amber-50/80 border-amber-200',
          text: 'text-amber-900',
          accent: 'bg-amber-700',
          border: 'border-amber-700/10',
          icon: Shield
        };
      case 'RISKY':
        return {
          bg: 'bg-orange-50/80 border-orange-200',
          text: 'text-orange-900',
          accent: 'bg-orange-800',
          border: 'border-orange-800/10',
          icon: ShieldAlert
        };
      case 'DANGEROUS':
      default:
        return {
          bg: 'bg-red-50/70 border-red-200',
          text: 'text-red-955',
          accent: 'bg-red-800',
          border: 'border-red-800/10',
          icon: ShieldAlert
        };
    }
  };

  const styles = getRiskStyles(riskLevel);
  const Icon = styles.icon;

  return (
    <div className="w-full border-b border-editorial-border pb-6">
      {apiWarning && (
        <div className="mb-6 p-3 text-xs border border-amber-200 bg-amber-50/50 text-amber-900 font-serif italic flex items-center justify-center gap-2">
          <span>⚠️ {apiWarning}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
        {/* Document Classification */}
        <div className="md:col-span-4 flex flex-col justify-center border-b md:border-b-0 md:border-r border-editorial-border pb-6 md:pb-0 md:pr-6">
          <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono mb-1">
            Document Type
          </span>
          <h2 className="text-2xl font-serif font-black text-ink leading-tight">
            {contractType}
          </h2>
          <p className="text-xs text-stone-500 mt-2">
            Classified by Veritas NLP Layer.
          </p>
        </div>

        {/* Safety Badge Callout */}
        <div className="md:col-span-4 flex items-center gap-4 border-b md:border-b-0 md:border-r border-editorial-border pb-6 md:pb-0 md:px-6">
          <div className={`p-4 border rounded-none ${styles.bg} flex items-center justify-center`}>
            <Icon className={`w-8 h-8 ${styles.text}`} />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono">
              Classification
            </span>
            <div className={`text-xl font-serif font-bold uppercase tracking-wider ${styles.text}`}>
              {riskLevel}
            </div>
            <p className="text-xs text-stone-500 mt-0.5">
              Subject to negotiation thresholds.
            </p>
          </div>
        </div>

        {/* Numeric Indexes */}
        <div className="md:col-span-4 grid grid-cols-2 gap-4 items-center pl-0 md:pl-6">
          {/* Risk Index */}
          <div className="text-left">
            <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono flex items-center gap-1">
              <Activity className="w-3 h-3 text-editorial-gold" />
              Risk Index
            </span>
            <div className="flex items-baseline mt-1">
              <span className="text-4xl font-serif font-bold text-ink">
                {overallRisk}
              </span>
              <span className="text-stone-400 text-xs font-serif ml-0.5">/100</span>
            </div>
            {/* Small bar */}
            <div className="w-full h-1 bg-stone-200 mt-2">
              <div 
                className="h-full bg-charcoal" 
                style={{ width: `${overallRisk}%` }}
              ></div>
            </div>
          </div>

          {/* AI Confidence */}
          <div className="text-left">
            <span className="text-[10px] uppercase tracking-widest text-stone-500 font-mono flex items-center gap-1">
              <Award className="w-3 h-3 text-editorial-gold" />
              Confidence
            </span>
            <div className="flex items-baseline mt-1">
              <span className="text-4xl font-serif font-bold text-ink">
                {confidence}
              </span>
              <span className="text-stone-400 text-xs font-serif ml-0.5">%</span>
            </div>
            {/* Small bar */}
            <div className="w-full h-1 bg-stone-200 mt-2">
              <div 
                className="h-full bg-editorial-gold" 
                style={{ width: `${confidence}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
