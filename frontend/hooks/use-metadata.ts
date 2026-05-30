"use client";

import { useQuery } from "@tanstack/react-query";

import { getMetadata } from "@/services/api";

export function useMetadata(videoId?: string) {
  return useQuery({ queryKey: ["metadata", videoId ?? "all"], queryFn: () => getMetadata(videoId) });
}