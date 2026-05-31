import React from "react";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import type { VideoRecord } from "../types/api";

export function VideoCard({ label, video }: { label: string; video: VideoRecord }) {
  return (
    <Card className="h-full border-white/10 bg-white/5">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-sm sm:text-base">{label}</CardTitle>
          <Badge variant={video.platform === "youtube" ? "success" : "warning"}>
            {video.platform}
          </Badge>
        </div>
        <CardDescription className="line-clamp-2">{video.title}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-mutedForeground">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-1 md:grid-cols-2">
          <p>
            <span className="text-foreground">Creator:</span> {video.creator}
          </p>
          <p>
            <span className="text-foreground">Upload:</span> {video.upload_date ?? "Unknown"}
          </p>
          <p>
            <span className="text-foreground">Views:</span> {video.views.toLocaleString()}
          </p>
          <p>
            <span className="text-foreground">Likes:</span> {video.likes.toLocaleString()}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs text-mutedForeground">
          <p>
            <span className="text-foreground">Comments:</span> {video.comments.toLocaleString()}
          </p>
          <p>
            <span className="text-foreground">Followers:</span> {video.follower_count?.toLocaleString() ?? "Unavailable"}
          </p>
        </div>
        <p className="text-xs">
          <span className="text-foreground">Hashtags:</span> {video.hashtags.length ? video.hashtags.map((h) => `#${h}`).join(" ") : "None"}
        </p>
      </CardContent>
    </Card>
  );
}
