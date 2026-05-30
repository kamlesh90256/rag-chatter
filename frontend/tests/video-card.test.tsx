import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { VideoCard } from "../components/video-card";

const video = {
  id: "video-1",
  platform: "youtube",
  url: "https://youtube.com/watch?v=1",
  title: "Launch Hook",
  creator: "Creator One",
  views: 1200,
  likes: 150,
  comments: 24,
  upload_date: null,
  duration_seconds: 42,
  hashtags: ["growth", "hook"],
  follower_count: 5000,
  metadata_json: "{}",
  error_message: null,
  created_at: new Date().toISOString(),
};

describe("VideoCard", () => {
  it("renders metadata", () => {
    render(<VideoCard label="Video A" video={video} />);
    expect(screen.getByText("Video A")).toBeInTheDocument();
    expect(screen.getByText("Launch Hook")).toBeInTheDocument();
    expect(screen.getByText(/Creator One/)).toBeInTheDocument();
  });
});
