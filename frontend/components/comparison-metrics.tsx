import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { ComparisonRow } from "@/types/api";

export function ComparisonMetrics({ winner, table, engagementRate }: { winner: string; table: ComparisonRow[]; engagementRate: number }) {
  return (
    <Card className="border-white/10 bg-white/5">
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <CardTitle>Comparison metrics</CardTitle>
          <Badge variant="success">Winner: {winner}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <p className="text-mutedForeground">Top engagement rate</p>
            <p className="mt-2 text-2xl font-semibold text-emerald-300">{engagementRate.toFixed(2)}%</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <p className="text-mutedForeground">Evidence rows</p>
            <p className="mt-2 text-2xl font-semibold">{table.length}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <p className="text-mutedForeground">Outcome</p>
            <p className="mt-2 text-2xl font-semibold text-sky-300">{winner}</p>
          </div>
        </div>
        <Separator className="bg-white/10" />
        <div className="overflow-hidden rounded-xl border border-white/10">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/5 text-mutedForeground">
              <tr>
                <th className="px-4 py-3">Metric</th>
                <th className="px-4 py-3">Video A</th>
                <th className="px-4 py-3">Video B</th>
              </tr>
            </thead>
            <tbody>
              {table.map((row) => (
                <tr key={row.metric} className="border-t border-white/10">
                  <td className="px-4 py-3 font-medium text-foreground">{row.metric}</td>
                  <td className="px-4 py-3 text-mutedForeground">{row.video_a}</td>
                  <td className="px-4 py-3 text-mutedForeground">{row.video_b}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
