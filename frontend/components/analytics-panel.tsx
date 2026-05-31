"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { VideoRecord } from "@/types/api";

export function AnalyticsPanel({ videos }: { videos: VideoRecord[] }) {
  const data = videos.map((v, idx) => ({ name: `Video ${idx === 0 ? "A" : "B"}`, views: v.views, likes: v.likes, comments: v.comments, followers: v.follower_count ?? 0 }));

  return (
    <Card className="border-white/10 bg-white/5">
      <CardHeader>
        <CardTitle>Analytics</CardTitle>
      </CardHeader>
      <CardContent className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical">
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" />
            <Tooltip />
            <Legend />
            <Bar dataKey="views" stackId="a" fill="#60a5fa" />
            <Bar dataKey="likes" stackId="a" fill="#34d399" />
            <Bar dataKey="comments" stackId="a" fill="#f472b6" />
            <Bar dataKey="followers" stackId="a" fill="#fbbf24" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
