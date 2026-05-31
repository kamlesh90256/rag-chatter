"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { SendHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import type { ChatCitation } from "@/types/api";

export function ChatPanel({
  onAsk,
  isStreaming,
  answer,
  citations,
  error,
  connectionStatus = 'disconnected',
  isThinking = false,
  onRetry,
}: {
  onAsk: (question: string) => Promise<void>;
  isStreaming: boolean;
  answer: string;
  citations: ChatCitation[];
  error: string | null;
  connectionStatus?: string;
  isThinking?: boolean;
  onRetry?: () => void;
}) {
  const [question, setQuestion] = useState("");
  const [showRetry, setShowRetry] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    await onAsk(question);
    setQuestion("");
  };

  const handleRetry = () => {
    if (onRetry) onRetry();
    setShowRetry(false);
  };

  return (
    <Card className="border-white/10 bg-white/5">
      <CardHeader>
        <CardTitle>Chat window</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form className="space-y-3" onSubmit={submit}>
          <Textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask why Video A outperformed Video B, compare hooks, or suggest improvements..." className="min-h-[120px] bg-black/20" />
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-mutedForeground">Streaming via SSE</p>
            <Button type="submit" disabled={isStreaming} className="min-w-36">
              <SendHorizontal className="h-4 w-4" />
              {isStreaming ? "Streaming" : "Ask"}
            </Button>
          </div>
        </form>
        {error ? <p className="text-sm text-red-300">{error}</p> : null}
        <div className="rounded-xl border border-white/10 bg-black/30 p-4">
          <div className="flex items-center justify-between">
            <p className="mb-2 text-xs uppercase tracking-[0.25em] text-mutedForeground">Answer</p>
            <div className="flex items-center gap-3">
              <span className={`text-xs ${connectionStatus === 'connected' ? 'text-emerald-300' : connectionStatus === 'reconnecting' ? 'text-amber-300' : 'text-rose-400'}`}>{connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'reconnecting' ? 'Reconnecting' : 'Disconnected'}</span>
              {connectionStatus !== 'connected' ? <button onClick={handleRetry} className="text-xs text-sky-300">Retry</button> : null}
            </div>
          </div>
          <p className="whitespace-pre-wrap text-sm leading-6 text-foreground">
            {isThinking ? <span className="text-mutedForeground">AI is thinking...</span> : null}
            <span className="inline-block">
              {answer || (isThinking ? '' : 'Waiting for a question...')}
              {/* typing cursor */}
              {isThinking || isStreaming ? <span className="ml-1 inline-block h-4 w-1 bg-foreground animate-blink align-middle" /> : null}
            </span>
          </p>
          {isStreaming && !answer ? (
            <div className="mt-3 space-y-2">
              <div className="h-3 w-full rounded bg-white/5 animate-pulse" />
              <div className="h-3 w-5/6 rounded bg-white/5 animate-pulse" />
            </div>
          ) : null}
        </div>
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.25em] text-mutedForeground">Citations</p>
          {citations.length ? citations.map((citation, index) => {
            const ts = citation.timestamp_start ?? null;
            const link = citation.url ? `${citation.url}${citation.url.includes("?") ? "&" : "?"}${ts ? `t=${Math.floor(ts)}` : ""}` : citation.url;
            return (
              <div key={`${citation.title}-${index}`} className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm">
                <p className="text-foreground">Source: {citation.title} | Chunk {citation.chunk_id ?? "?"}</p>
                <p className="text-mutedForeground">{citation.creator}</p>
                {ts ? <a href={link} target="_blank" rel="noreferrer" className="text-sm text-sky-300">Jump to {new Date((ts || 0) * 1000).toISOString().substr(14, 5)}</a> : null}
              </div>
            );
          }) : <p className="text-sm text-mutedForeground">No citations yet.</p>}
        </div>
      </CardContent>
    </Card>
  );
}
