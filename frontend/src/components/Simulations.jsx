import React, { useState } from 'react';
import { Play, ShieldAlert, Sparkles, HelpCircle } from 'lucide-react';

export default function Simulations({ simulations = [] }) {
  const [activeScenarioIndex, setActiveScenarioIndex] = useState(0);

  if (!simulations || simulations.length === 0) {
    return (
      <div className="border border-editorial-border p-6 bg-paper text-center">
        <h3 className="font-serif font-bold text-lg text-ink mb-1">No Simulation Data</h3>
        <p className="text-xs text-stone-500 uppercase tracking-widest">
          AI analysis could not construct simulation cases for this text type.
        </p>
      </div>
    );
  }

  const activeSimulation = simulations[activeScenarioIndex];

  return (
    <div className="border border-editorial-border bg-paper p-6 space-y-6">
      <div className="border-b border-editorial-border pb-4">
        <div className="flex items-center gap-2">
          <Play className="w-5 h-5 text-editorial-gold fill-editorial-gold" />
          <h3 className="font-serif font-black text-xl text-ink uppercase tracking-wide">
            Consequence Simulator
          </h3>
        </div>
        <p className="text-[11px] text-stone-500 uppercase tracking-widest mt-0.5">
          Simulate legal scenarios and forecast financial and operations liabilities
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Scenario Selectors Sidebar */}
        <div className="md:w-1/3 flex flex-row md:flex-col gap-2 overflow-x-auto md:overflow-x-visible pb-2 md:pb-0 border-b md:border-b-0 md:border-r border-editorial-border md:pr-4">
          {simulations.map((sim, index) => (
            <button
              key={index}
              onClick={() => setActiveScenarioIndex(index)}
              className={`w-full text-left px-4 py-3 border text-xs font-serif font-bold uppercase tracking-wider transition-all duration-150 shrink-0 md:shrink ${
                activeScenarioIndex === index
                  ? 'bg-charcoal text-cream border-charcoal'
                  : 'bg-cream-light border-stone-200 text-stone-600 hover:bg-stone-100 hover:text-stone-850'
              }`}
            >
              ⚡ Scenario #{index + 1}:
              <span className="block mt-1 font-sans font-medium text-[10px] text-stone-400 normal-case line-clamp-1">
                {sim.scenario}
              </span>
            </button>
          ))}
        </div>

        {/* Simulator Results Output */}
        <div className="md:w-2/3 space-y-6 min-h-60 flex flex-col justify-between">
          <div>
            <span className="text-[9px] uppercase tracking-widest text-stone-400 font-mono block mb-1">
              Hypothetical Query
            </span>
            <h4 className="font-serif font-black text-lg text-ink">
              "{activeSimulation.scenario}"
            </h4>
          </div>

          <div className="border-y border-editorial-border py-4 my-2">
            <span className="text-[9px] uppercase tracking-widest text-editorial-red font-mono flex items-center gap-1 mb-1.5 font-bold">
              <ShieldAlert className="w-3.5 h-3.5" />
              Forecasted Consequence
            </span>
            <p className="text-xs md:text-sm text-stone-700 leading-relaxed font-sans font-medium">
              {activeSimulation.consequence}
            </p>
          </div>

          <div>
            <span className="text-[9px] uppercase tracking-widest text-editorial-green font-mono block mb-1 font-bold">
              🛡️ Safeguard & Mitigation Strategy
            </span>
            <p className="text-xs text-stone-600 leading-relaxed font-serif italic bg-stone-50 border border-stone-200 p-3">
              {activeSimulation.mitigation}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
