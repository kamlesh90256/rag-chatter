"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function IngestForm({ onSubmit, isLoading }: { onSubmit: (youtubeUrl: string, instagramUrl: string) => Promise<void>; isLoading: boolean }) {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [instagramUrl, setInstagramUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!youtubeUrl.trim() || !instagramUrl.trim()) {
      setError("Both URLs are required.");
      return;
    }
    setError(null);
    await onSubmit(youtubeUrl.trim(), instagramUrl.trim());
  };

  return (
    <Card className="border-white/10 bg-white/5">
      <CardHeader>
        <CardTitle>Ingest creator videos</CardTitle>
        <CardDescription>Enter one YouTube URL and one Instagram Reel URL. Metadata, transcripts, embeddings, and comparisons are generated automatically.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4" onSubmit={handleSubmit}>
          <Input value={youtubeUrl} onChange={(event) => setYoutubeUrl(event.target.value)} placeholder="https://www.youtube.com/watch?v=..." />
          <Input value={instagramUrl} onChange={(event) => setInstagramUrl(event.target.value)} placeholder="https://www.instagram.com/reel/..." />
          {error ? <p className="text-sm text-red-300">{error}</p> : null}
          <Button type="submit" disabled={isLoading} className="w-full sm:w-auto">
            {isLoading ? "Processing..." : "Build comparison"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
