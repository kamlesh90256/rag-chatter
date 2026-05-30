"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ChatPanel } from "@/components/chat-panel";
import { ComparisonMetrics } from "@/components/comparison-metrics";
import { ConversationHistory } from "@/components/conversation-history";
import { HookAnalysisCard } from "@/components/hook-analysis";
import { IngestForm } from "@/components/ingest-form";
import { SourcePanel } from "@/components/source-panel";
import { VideoCard } from "@/components/video-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getSources } from "@/services/api";
import { useChat } from "@/hooks/use-chat";
import { useIngest } from "@/hooks/use-ingest";
import { useMetadata } from "@/hooks/use-metadata";
import type { VideoRecord } from "@/types/api";

export default function Page() {
  const ingest = useIngest();
  const metadataQuery = useMetadata();
  const [videos, setVideos] = useState<VideoRecord[]>([]);
  const [threadId] = useState(() => crypto.randomUUID());

  const currentVideos = videos.length ? videos : metadataQuery.data?.videos.slice(0, 2) ?? [];
  const videoIds = useMemo(() => currentVideos.map((video) => video.id), [currentVideos]);
  const chat = useChat(threadId, videoIds.length ? videoIds : undefined);

  const sourcesQuery = useQuery({
    queryKey: ["sources", threadId, videoIds.join(",")],
    queryFn: () => getSources({ threadId, videoId: videoIds.join(",") }),
    enabled: videoIds.length > 0,
    staleTime: 30_000,
  });

  const handleIngest = async (youtubeUrl: string, instagramUrl: string) => {
    const result = await ingest.mutateAsync({ youtube_url: youtubeUrl, instagram_url: instagramUrl });
    setVideos(result.videos);
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <IngestForm onSubmit={handleIngest} isLoading={ingest.isPending} />
        <Card className="border-white/10 bg-white/5">
          <CardHeader>
            <CardTitle>System status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-mutedForeground">
            <p>OpenAI embeddings: <span className="text-foreground">text-embedding-3-small</span></p>
            <p>LLM: <span className="text-foreground">gpt-4o-mini</span></p>
            <p>Vector DB: <span className="text-foreground">ChromaDB</span></p>
            <p>Streaming: <span className="text-foreground">Server-Sent Events</span></p>
            <p>Memory: <span className="text-foreground">LangGraph MemorySaver</span></p>
            <p>Active thread: <span className="text-foreground">{threadId}</span></p>
            {ingest.error ? <p className="text-red-300">{ingest.error.message}</p> : null}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        {currentVideos.length === 2 ? (
          <>
            <VideoCard label="Video A" video={currentVideos[0]} />
            <VideoCard label="Video B" video={currentVideos[1]} />
          </>
        ) : (
          <>
            <Card className="border-white/10 bg-white/5">
              <CardHeader><CardTitle>Video A</CardTitle></CardHeader>
              <CardContent className="space-y-3"><Skeleton className="h-6 w-3/4" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-5/6" /></CardContent>
            </Card>
            <Card className="border-white/10 bg-white/5">
              <CardHeader><CardTitle>Video B</CardTitle></CardHeader>
              <CardContent className="space-y-3"><Skeleton className="h-6 w-3/4" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-5/6" /></CardContent>
            </Card>
          </>
        )}
      </section>

      {ingest.data ? (
        <section className="space-y-6">
          <ComparisonMetrics
            winner={ingest.data.comparison.winner}
            engagementRate={ingest.data.comparison.engagement_rate}
            table={ingest.data.comparison.table}
          />
          <div className="grid gap-6 xl:grid-cols-2">
            <HookAnalysisCard label="Video A hook analysis" analysis={ingest.data.hook_analysis.video_a} />
            <HookAnalysisCard label="Video B hook analysis" analysis={ingest.data.hook_analysis.video_b} />
          </div>
        </section>
      ) : metadataQuery.data?.videos.length ? (
        <section className="space-y-6">
          <Card className="border-white/10 bg-white/5">
            <CardHeader>
              <CardTitle>Latest metadata</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-mutedForeground">
              The platform has existing ingests. Build a new comparison to refresh the dashboard.
            </CardContent>
          </Card>
        </section>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <ChatPanel
          onAsk={chat.sendQuestion}
          isStreaming={chat.isStreaming}
          answer={chat.streamingAnswer}
          citations={chat.citations}
          error={chat.error}
        />
        <SourcePanel
          citations={chat.citations}
          sources={sourcesQuery.data?.sources ?? []}
          memory={sourcesQuery.data?.memory ?? ""}
        />
      </section>

      <ConversationHistory messages={chat.messages} />
    </div>
  );
}
