"use client";

import { useMemo, useState, useTransition } from "react";

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

  const sendQuestion = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || isStreaming) return;
    setError(null);
    setStreamingAnswer("");
    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setIsStreaming(true);
    let finalAnswer = "";

    try {
      await streamChat(
        { question: trimmed, thread_id: threadId, video_ids: videoIds },
        (chunk) => {
          if (chunk.answer) {
            startTransition(() => {
              finalAnswer += chunk.answer ?? "";
              setStreamingAnswer(finalAnswer);
            });
          }
          if (chunk.citations) {
            setCitations(chunk.citations);
          }
          if (chunk.done) {
            setMessages((current) => [...current, { role: "assistant", content: finalAnswer }]);
          }
        }
      );
      setMessages((current) => {
        const next = [...current];
        if (next.at(-1)?.role !== "assistant") {
          next.push({ role: "assistant", content: finalAnswer });
        }
        return next;
      });
    } catch (streamError) {
      setError(streamError instanceof Error ? streamError.message : "Failed to send question");
    } finally {
      setIsStreaming(false);
    }
  };

  const combinedAnswer = useMemo(() => streamingAnswer, [streamingAnswer]);

  return {
    messages,
    citations,
    streamingAnswer: combinedAnswer,
    isStreaming: isStreaming || isPending,
    error,
    sendQuestion,
    setMessages,
  };
}
