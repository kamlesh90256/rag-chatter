import type { ChatResponse, IngestResponse, MetadataResponse, SourceChunk } from "@/types/api";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || response.statusText);
  }
  return response.json() as Promise<T>;
}

export async function ingestVideos(payload: { youtube_url: string; instagram_url: string }) {
  const response = await fetch(`${apiBaseUrl}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse<IngestResponse>(response);
}

export async function getIngestStatus(jobId: string) {
  const response = await fetch(`${apiBaseUrl}/ingest/status/${jobId}`, { cache: "no-store" });
  return parseResponse<{ id: string; state: string; status: any }>(response);
}

export async function getMetadata(videoId?: string) {
  const url = new URL(`${apiBaseUrl}/metadata`);
  if (videoId) url.searchParams.set("video_id", videoId);
  const response = await fetch(url.toString(), { cache: "no-store" });
  return parseResponse<MetadataResponse>(response);
}

export async function getSources(params: { videoId?: string; threadId?: string }) {
  const url = new URL(`${apiBaseUrl}/sources`);
  if (params.videoId) url.searchParams.set("video_ids", params.videoId);
  if (params.threadId) url.searchParams.set("thread_id", params.threadId);
  const response = await fetch(url.toString(), { cache: "no-store" });
  return parseResponse<{ sources: SourceChunk[]; memory: string }>(response);
}

export async function streamChat(
  payload: { question: string; thread_id: string; video_ids?: string[] },
  onMessage: (chunk: { answer?: string; citations?: ChatResponse["citations"]; done?: boolean }) => void,
  signal?: AbortSignal
) {
  const response = await fetch(`${apiBaseUrl}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ ...payload, stream: true }),
    signal,
  });

  if (!response.ok || !response.body) {
    const body = await response.text();
    throw new Error(body || response.statusText);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary).trim();
      buffer = buffer.slice(boundary + 2);
      if (frame.startsWith("data: ")) {
        const data = frame.slice(6).trim();
        if (data === "[DONE]") {
          onMessage({ done: true });
          return;
        }
        try {
          const parsed = JSON.parse(data);
          // Map server-side event types to frontend-friendly shape
          if (parsed.type === "retrieved") {
            onMessage({ citations: parsed.citations });
          } else if (parsed.type === "partial") {
            onMessage({ answer: parsed.text });
          } else if (parsed.type === "done") {
            onMessage({ answer: parsed.answer, citations: parsed.citations, done: true });
            return;
          } else if (parsed.type === "error") {
            throw new Error(parsed.error || "Streaming error");
          } else {
            // fallback: pass entire payload
            onMessage(parsed);
          }
        } catch (err) {
          // if JSON.parse fails, treat as partial text
          onMessage({ answer: data });
        }
      }
      boundary = buffer.indexOf("\n\n");
    }
  }
}
