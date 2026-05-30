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
}: {
  onAsk: (question: string) => Promise<void>;
  isStreaming: boolean;
  answer: string;
  citations: ChatCitation[];
  error: string | null;
}) {
  const [question, setQuestion] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    await onAsk(question);
    setQuestion("");
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
          <p className="mb-2 text-xs uppercase tracking-[0.25em] text-mutedForeground">Answer</p>
          <p className="whitespace-pre-wrap text-sm leading-6 text-foreground">{answer || "Waiting for a question..."}</p>
        </div>
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.25em] text-mutedForeground">Citations</p>
          {citations.length ? citations.map((citation, index) => (
            <div key={`${citation.title}-${index}`} className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm">
              <p className="text-foreground">Source: {citation.title} | Chunk {citation.chunk_id ?? "?"}</p>
              <p className="text-mutedForeground">{citation.creator}</p>
            </div>
          )) : <p className="text-sm text-mutedForeground">No citations yet.</p>}
        </div>
      </CardContent>
    </Card>
  );
}
