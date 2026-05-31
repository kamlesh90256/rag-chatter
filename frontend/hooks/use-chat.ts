"use client";

import { useMemo, useState, useTransition, useRef, useEffect } from "react";

import { streamChat } from "@/services/api";
import type { ChatCitation } from "@/types/api";

type Message = { role: "user" | "assistant"; content: string };

export function useChat(threadId: string, videoIds?: string[]) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [citations, setCitations] = useState<ChatCitation[]>([]);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const abortRef = useRef<AbortController | null>(null);
  const lastEventAt = useRef<number>(Date.now());
  const retryCount = useRef<number>(0);
  const currentQuestion = useRef<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "reconnecting" | "disconnected">("disconnected");
  const [isThinking, setIsThinking] = useState(false);

  // Heartbeat / inactivity settings
  const HEARTBEAT_TIMEOUT = 12_000; // ms
  const MAX_RETRIES = 5;

  useEffect(() => {
    const t = setInterval(() => {
      if (!isStreaming || !currentQuestion.current) return;
      if (Date.now() - lastEventAt.current > HEARTBEAT_TIMEOUT) {
        // trigger reconnect
        // abort current stream (will cause cleanup and a retry)
        abortRef.current?.abort();
      }
    }, 3000);
    return () => clearInterval(t);
  }, [isStreaming]);

  const startStream = async (question: string) => {
    // Initialize controls
    currentQuestion.current = question;
    abortRef.current = new AbortController();
    lastEventAt.current = Date.now();
    retryCount.current = 0;
    setIsStreaming(true);
    setError(null);
    setStreamingAnswer("");
    setIsThinking(true);
    setConnectionStatus("connected");

    let accumulated = "";

    let committed = false;

    const tryStream = async () => {
      try {
        await streamChat(
          { question, thread_id: threadId, video_ids: videoIds },
          (chunk) => {
            lastEventAt.current = Date.now();
            // first token arrived
            if (isThinking) setIsThinking(false);
            // update connection state
            setConnectionStatus("connected");
            if (chunk.answer) {
              startTransition(() => {
                accumulated += chunk.answer ?? "";
                setStreamingAnswer(accumulated);
              });
            }
            if (chunk.citations) {
              setCitations(chunk.citations);
            }
            if (chunk.done) {
              // final result — commit to messages
              if (!committed) {
                setMessages((current) => [...current, { role: "assistant", content: accumulated }]);
                committed = true;
              }
            }
          },
          abortRef.current?.signal
        );
        // streamChat completes normally — commit assistant if not already
        setMessages((current) => {
          const next = [...current];
          if (!committed && next.at(-1)?.role !== "assistant") {
            next.push({ role: "assistant", content: accumulated });
          }
          return next;
        });
        setIsStreaming(false);
        setConnectionStatus("connected");
        setIsThinking(false);
      } catch (err) {
        // If aborted by us, attempt reconnection with exponential backoff
        if (abortRef.current?.signal.aborted) {
          if (retryCount.current < MAX_RETRIES) {
            retryCount.current += 1;
            setConnectionStatus("reconnecting");
            const backoff = Math.min(30000, 500 * 2 ** retryCount.current);
            await new Promise((r) => setTimeout(r, backoff));
            // reset abort controller for next attempt
            abortRef.current = new AbortController();
            tryStream();
            return;
          }
        }

        // mark disconnected after retries
        setConnectionStatus("disconnected");

        // If stream repeatedly fails, fall back to non-streaming fetch of final answer
        try {
          // Fetch final answer via non-streaming endpoint
          const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, thread_id: threadId, video_ids: videoIds, stream: false }),
          });
          if (resp.ok) {
            const json = await resp.json();
            const final = json.answer ?? json;
            setStreamingAnswer(final);
            setMessages((current) => {
              const next = [...current];
              if (!committed && next.at(-1)?.role !== "assistant") {
                next.push({ role: "assistant", content: final });
              }
              return next;
            });
            setIsStreaming(false);
            setConnectionStatus("connected");
            setIsThinking(false);
            return;
          }
          const text = await resp.text();
          throw new Error(text || "chat failed");
        } catch (finalErr) {
          setError(finalErr instanceof Error ? finalErr.message : String(finalErr));
          setIsStreaming(false);
          setConnectionStatus("disconnected");
        }
      }
    };

    tryStream();
  };

  const sendQuestion = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || isStreaming) return;
    setError(null);
    setStreamingAnswer("");
    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    await startStream(trimmed);
  };

  const combinedAnswer = useMemo(() => streamingAnswer, [streamingAnswer]);

  const retry = async () => {
    // attempt to restart the stream with the last question
    if (currentQuestion.current) {
      setConnectionStatus("reconnecting");
      abortRef.current?.abort();
      await startStream(currentQuestion.current);
    }
  };

  return {
    messages,
    citations,
    streamingAnswer: combinedAnswer,
    isStreaming: isStreaming || isPending,
    error,
    sendQuestion,
    setMessages,
    connectionStatus,
    isThinking,
    retry,
  };
}
