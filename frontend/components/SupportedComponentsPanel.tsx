// components/SupportedComponentsPanel.tsx
"use client";

import { useState } from "react";
import { SUPPORTED_COMPONENTS, SUPPORTED_BOARDS, type ComponentCategory } from "@/lib/supportedComponents";

const CATEGORY_ORDER: ComponentCategory[] = [
  "Sensors",
  "Input Devices",
  "LEDs",
  "Displays",
  "Motors",
  "Communication",
  "Logic & Shift Registers",
  "Passives & Other",
];

export default function SupportedComponentsPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<ComponentCategory>("Sensors");

  return (
    <div className="w-full">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm font-medium text-zinc-300 hover:text-teal-400 transition-colors duration-200"
      >
        <span
          className={`inline-block w-1.5 h-1.5 rounded-full bg-teal-400 transition-transform duration-300 ${
            isOpen ? "scale-125" : ""
          }`}
        />
        What can I build?
        <svg
          className={`w-3.5 h-3.5 text-zinc-500 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="mt-3 rounded-lg border border-zinc-700 bg-zinc-900 overflow-hidden shadow-lg shadow-black/40">
          <div className="px-4 py-3 border-b border-zinc-700 flex flex-wrap gap-2 items-center bg-zinc-900/80">
            <span className="text-xs uppercase tracking-wide text-zinc-400 mr-1">Boards</span>
            {SUPPORTED_BOARDS.map((board) => (
              <span
                key={board}
                className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-200 border border-zinc-600"
              >
                {board}
              </span>
            ))}
          </div>

          <div className="flex">
            <div className="w-40 shrink-0 border-r border-zinc-700 py-2 bg-zinc-900/60">
              {CATEGORY_ORDER.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`w-full text-left px-4 py-2 text-xs transition-colors duration-150 ${
                    activeCategory === cat
                      ? "text-teal-300 bg-teal-500/10 border-l-2 border-teal-400 font-medium"
                      : "text-zinc-400 hover:text-zinc-200 border-l-2 border-transparent"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <div className="flex-1 p-4 grid grid-cols-2 gap-x-4 gap-y-2.5 bg-zinc-900">
              {SUPPORTED_COMPONENTS[activeCategory].map((comp) => (
                <div key={comp.name} className="flex flex-col">
                  <span className="text-sm text-zinc-100">{comp.name}</span>
                  {comp.note && (
                    <span className="text-[10px] text-amber-400">{comp.note}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}