export type VideoRecord = {
  id: string;
  platform: "youtube" | "instagram" | string;
  url: string;
  title: string;
  creator: string;
  views: number;
  likes: number;
  comments: number;
  upload_date: string | null;
  duration_seconds: number | null;
  hashtags: string[];
  follower_count: number | null;
  metadata_json: string;
  error_message: string | null;
  created_at: string;
};

export type ComparisonRow = {
  metric: string;
  video_a: string | number;
  video_b: string | number;
};

export type IngestResponse = {
  videos: VideoRecord[];
  comparison: {
    engagement_rate: number;
    winner: string;
    table: ComparisonRow[];
  };
  hook_analysis: {
    video_a: HookAnalysis;
    video_b: HookAnalysis;
  };
  analysis_id: string;
};

export type HookAnalysis = {
  hook_score: number;
  curiosity_score: number;
  emotion_score: number;
  retention_score: number;
  cta_score: number;
  reasoning: string;
};

export type ChatCitation = {
  title: string;
  creator: string;
  chunk_id: number | null;
  url: string | null;
};

export type ChatResponse = {
  answer: string;
  citations: ChatCitation[];
  thread_id: string;
};

export type SourceChunk = {
  text: string;
  metadata: Record<string, string | number | null>;
};

export type MetadataResponse = {
  videos: VideoRecord[];
};
