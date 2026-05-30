import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { HookAnalysis } from "@/types/api";

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-4">
      <p className="text-xs uppercase tracking-[0.25em] text-mutedForeground">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

export function HookAnalysisCard({ label, analysis }: { label: string; analysis: HookAnalysis }) {
  return (
    <Card className="border-white/10 bg-white/5">
      <CardHeader>
        <CardTitle>{label}</CardTitle>
        <CardDescription>First 5 seconds analysis with reasoning.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          <Metric label="Hook" value={analysis.hook_score} />
          <Metric label="Curiosity" value={analysis.curiosity_score} />
          <Metric label="Emotion" value={analysis.emotion_score} />
          <Metric label="Retention" value={analysis.retention_score} />
          <Metric label="CTA" value={analysis.cta_score} />
        </div>
        <p className="rounded-xl border border-white/10 bg-black/20 p-4 text-sm text-mutedForeground">{analysis.reasoning}</p>
      </CardContent>
    </Card>
  );
}
