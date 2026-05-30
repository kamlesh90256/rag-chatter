import { describe, expect, it, vi } from "vitest";

import { ingestVideos, getMetadata } from "../services/api";

describe("api service", () => {
  it("posts ingest payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ videos: [], comparison: { engagement_rate: 0, winner: "", table: [] }, hook_analysis: { video_a: {}, video_b: {} }, analysis_id: "1" }),
    });
    global.fetch = fetchMock as never;
    await ingestVideos({ youtube_url: "https://youtube.com/watch?v=1", instagram_url: "https://instagram.com/reel/2" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("fetches metadata with the correct endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ videos: [] }),
    });
    global.fetch = fetchMock as never;
    await getMetadata("video-1");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
