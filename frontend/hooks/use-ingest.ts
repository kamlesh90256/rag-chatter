"use client";

import { useMutation } from "@tanstack/react-query";

import { ingestVideos } from "@/services/api";

export function useIngest() {
  return useMutation({ mutationFn: ingestVideos });
}
