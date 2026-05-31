import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { ChatCitation, SourceChunk } from "@/types/api";

export function SourcePanel({ citations, sources, memory }: { citations: ChatCitation[]; sources: SourceChunk[]; memory: string }) {
  return (
    <Card className="border-white/10 bg-white/5">
      <CardHeader>
        <CardTitle>Source panel</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div>
          <p className="mb-2 text-xs uppercase tracking-[0.25em] text-mutedForeground">Citations</p>
          <div className="space-y-2">
            {citations.length ? citations.map((citation, index) => (
              <div key={`${citation.title}-${index}`} className="rounded-xl border border-white/10 bg-black/20 p-3">
                <p className="font-medium text-foreground">Source: {citation.title} | Chunk {citation.chunk_id ?? "?"}</p>
                <p className="text-mutedForeground">{citation.creator}</p>
              </div>
            )) : <p className="text-mutedForeground">Run a question to populate source citations.</p>}
          </div>
        </div>
        <Separator className="bg-white/10" />
        <div>
          <p className="mb-2 text-xs uppercase tracking-[0.25em] text-mutedForeground">Retrieved context</p>
          <div className="space-y-2">
            {sources.length ? sources.map((source, index) => (
              <div key={index} className="rounded-xl border border-white/10 bg-black/20 p-3">
                <p className="text-foreground">{String(source.metadata.title ?? "Unknown")}</p>
                <p className="text-mutedForeground">Chunk {String(source.metadata.chunk_id ?? index + 1)} {source.metadata.timestamp_start ? `• ${new Date((source.metadata.timestamp_start as number) * 1000).toISOString().substr(14,5)}` : ""}</p>
                {source.metadata.url ? <a href={`${source.metadata.url}${String(source.metadata.url).includes("?")?"&":"?"}${source.metadata.timestamp_start?`t=${Math.floor(source.metadata.timestamp_start as number)}`:""}`} target="_blank" rel="noreferrer" className="text-xs text-sky-300">Open source</a> : null}
                <p className="mt-2 max-h-24 overflow-hidden text-mutedForeground">{source.text}</p>
              </div>
            )) : <p className="text-mutedForeground">No sources loaded.</p>}
          </div>
        </div>
        <Separator className="bg-white/10" />
        <div>
          <p className="mb-2 text-xs uppercase tracking-[0.25em] text-mutedForeground">Memory</p>
          <p className="whitespace-pre-wrap rounded-xl border border-white/10 bg-black/20 p-3 text-mutedForeground">{memory || "No memory available yet."}</p>
        </div>
      </CardContent>
    </Card>
  );
}
