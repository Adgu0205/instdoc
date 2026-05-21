import React from 'react';
import { Scale, ShieldAlert } from 'lucide-react';

export default function Navigation() {
  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <header className="w-full max-w-7xl mx-auto px-4 md:px-8 pt-8 pb-4 bg-cream">
      {/* Newspaper Top Info Row */}
      <div className="flex justify-between items-center text-xs uppercase tracking-widest text-stone-500 font-medium pb-2 border-b border-editorial-border">
        <span>Volume I • Edition 1.0</span>
        <span className="flex items-center gap-1.5 font-semibold text-editorial-gold">
          <Scale className="w-3.5 h-3.5" />
          AI Legal Analyst
        </span>
        <span className="hidden sm:inline">{currentDate}</span>
      </div>

      {/* Main Newspaper Title (Masthead) */}
      <div className="text-center py-6 md:py-8 select-none">
        <h1 className="text-5xl md:text-7xl font-serif font-black tracking-tight text-ink">
          VERITAS LEDGER
        </h1>
        <p className="mt-2 text-sm md:text-base font-serif italic tracking-wide text-stone-600">
          Independent Contract Analysis, Risk Intelligence & Negotiation Journal
        </p>
      </div>

      {/* Double Border Separator with Metadata */}
      <div className="double-border-y py-2.5 flex flex-col sm:flex-row justify-between items-center text-xs uppercase tracking-wider text-stone-700 font-semibold gap-2">
        <div className="flex items-center gap-4">
          <span>Daily Briefing</span>
          <span className="text-stone-300">•</span>
          <span>SaaS terms & Agreements</span>
        </div>
        <div className="text-center sm:text-right flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-editorial-gold animate-pulse"></span>
          <span>Secured Pipeline (In-Memory Processing Only)</span>
        </div>
      </div>
    </header>
  );
}
