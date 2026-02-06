import { IdeaForm } from "@/components/idea-form";

export default function Home() {
  return (
    <main className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center px-4 py-16">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-zinc-100 mb-2">Pain Radar</h1>
        <p className="text-zinc-400 max-w-lg">
          Decision-grade idea validation. Evidence-backed pain maps,
          competitor reality checks, and falsifiable 7-day validation plans.
        </p>
      </div>
      <IdeaForm />
    </main>
  );
}
