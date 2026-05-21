import React from 'react';
import { Bookmark, FileText } from 'lucide-react';

export default function ActionItems({ thingsToKnow = [] }) {
  // Ensure we always have items to render
  const defaultItems = [
    "Verify the scope of the confidentiality provisions matches your expectations.",
    "Verify the terms of early termination convenience to ensure no hidden fees exist.",
    "Confirm the governing law state is convenient for any potential dispute resolution.",
    "Check for any intellectual property assignment clauses to ensure pre-existing works are protected.",
    "Ensure late interest fees do not exceed standard statutory rates (e.g., 12% annually)."
  ];

  const displayItems = thingsToKnow && thingsToKnow.length >= 5 ? thingsToKnow.slice(0, 5) : defaultItems;

  return (
    <div className="border border-editorial-border bg-paper p-6 space-y-6">
      <div className="border-b border-editorial-border pb-4">
        <div className="flex items-center gap-2">
          <Bookmark className="w-5 h-5 text-editorial-gold" />
          <h3 className="font-serif font-black text-xl text-ink uppercase tracking-wide">
            5 Things You Must Know Before Signing
          </h3>
        </div>
        <p className="text-[11px] text-stone-500 uppercase tracking-widest mt-0.5">
          Veritas Executive Editorial Briefing - Crucial Highlights
        </p>
      </div>

      {/* Grid listing the 5 crucial facts */}
      <div className="space-y-6">
        {displayItems.map((item, index) => (
          <div key={index} className="flex gap-4 items-start pb-4 border-b border-stone-100 last:border-0 last:pb-0">
            <span className="font-serif font-bold text-4xl text-editorial-gold opacity-60 leading-none select-none">
              0{index + 1}
            </span>
            <div className="space-y-0.5">
              <p className="text-sm font-serif font-medium text-stone-900 leading-relaxed">
                {item}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Negotiation Pro-Tips */}
      <div className="mt-8 border border-dashed border-editorial-border bg-cream-light/30 p-4">
        <h4 className="font-serif font-bold text-xs uppercase tracking-wider text-ink flex items-center gap-1.5 mb-1.5">
          <FileText className="w-3.5 h-3.5 text-editorial-gold" />
          Tactical Negotiation Policy
        </h4>
        <p className="text-[11px] text-stone-600 leading-relaxed">
          Always request edits in a redlined Word document (.docx). Cross out one-sided terms and reference our recommended counter-wordings directly. Cap all general indemnification and specify that disputes must go through a mutual discussion cure period (e.g., 30 days) before formal litigation or arbitration is initiated.
        </p>
      </div>
    </div>
  );
}
