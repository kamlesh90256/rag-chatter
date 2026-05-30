import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ConversationHistory({ messages }: { messages: { role: "user" | "assistant"; content: string }[] }) {
  return (
    <Card className="border-white/10 bg-white/5">
      <CardHeader>
        <CardTitle>Conversation history</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {messages.length === 0 ? (
          <p className="text-sm text-mutedForeground">No conversation yet.</p>
        ) : (
          messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className="rounded-xl border border-white/10 bg-black/20 p-4">
              <p className="text-xs uppercase tracking-[0.25em] text-mutedForeground">{message.role}</p>
              <p className="mt-2 text-sm text-foreground whitespace-pre-wrap">{message.content}</p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
