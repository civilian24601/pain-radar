import { IdeaForm } from "@/components/idea-form";
import { Search, ShieldCheck, Clock } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-16">
      {/* Hero */}
      <div className="text-center mb-10 max-w-xl">
        <div className="inline-flex items-center gap-3 mb-4">
          {/* Mini radar icon */}
          <svg
            width="40"
            height="40"
            viewBox="0 0 40 40"
            fill="none"
            className="opacity-80"
          >
            <circle cx="20" cy="20" r="18" stroke="#3f3f46" strokeWidth="1" />
            <circle cx="20" cy="20" r="12" stroke="#3f3f46" strokeWidth="1" />
            <circle cx="20" cy="20" r="6" stroke="#3f3f46" strokeWidth="1" />
            <line x1="20" y1="2" x2="20" y2="38" stroke="#3f3f46" strokeWidth="0.5" />
            <line x1="2" y1="20" x2="38" y2="20" stroke="#3f3f46" strokeWidth="0.5" />
            <line
              x1="20"
              y1="20"
              x2="20"
              y2="4"
              stroke="#818cf8"
              strokeWidth="2"
              strokeLinecap="round"
              style={{
                transformOrigin: "20px 20px",
                animation: "radar-sweep 4s linear infinite",
              }}
            />
            <circle cx="20" cy="20" r="2" fill="#818cf8" />
          </svg>
          <h1
            className="text-4xl font-bold tracking-tight"
            style={{
              background: "linear-gradient(135deg, #fafafa 0%, #a1a1aa 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Pain Radar
          </h1>
        </div>
        <p className="text-zinc-400 text-lg mb-2">
          Decision-grade idea validation. Evidence, not vibes.
        </p>
        <p className="text-zinc-500 text-sm">
          We scan Reddit, reviews, job boards, and the open web to map real pain
          signals and build you an evidence-backed verdict.
        </p>
      </div>

      <IdeaForm />

      {/* Trust strip */}
      <div className="mt-10 flex items-center gap-6 text-[11px] uppercase tracking-widest text-zinc-600">
        <span className="flex items-center gap-1.5">
          <Search size={12} />
          50+ sources per idea
        </span>
        <span className="text-zinc-800">|</span>
        <span className="flex items-center gap-1.5">
          <ShieldCheck size={12} />
          Evidence-gated
        </span>
        <span className="text-zinc-800">|</span>
        <span className="flex items-center gap-1.5">
          <Clock size={12} />
          ~6-8 minutes
        </span>
      </div>
    </main>
  );
}
