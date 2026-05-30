import React from "react";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import type { VideoRecord } from "../types/api";

export function VideoCard({ label, video }: { label: string; video: VideoRecord }) {
  return (
    <Card className="h-full border-white/10 bg-white/5">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle>{label}</CardTitle>
          <Badge variant={video.platform === "youtube" ? "success" : "warning"}>{video.platform}</Badge>
        </div>
        <CardDescription>{video.title}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-mutedForeground">
        <p><span className="text-foreground">Creator:</span> {video.creator}</p>
        <p><span className="text-foreground">Views:</span> {video.views.toLocaleString()}</p>
        <p><span className="text-foreground">Likes:</span> {video.likes.toLocaleString()}</p>
        <p><span className="text-foreground">Comments:</span> {video.comments.toLocaleString()}</p>
        <p><span className="text-foreground">Followers:</span> {video.follower_count?.toLocaleString() ?? "Unavailable"}</p>
        <p><span className="text-foreground">Hashtags:</span> {video.hashtags.length ? video.hashtags.map((hashtag) => `#${hashtag}`).join(" ") : "None detected"}</p>
      </CardContent>
    </Card>
  );
}
