import { vi, describe, it, expect } from 'vitest';
import { streamChat } from '@/services/api';

// helper to simulate a ReadableStream reader
function makeReader(frames: string[]) {
  let i = 0;
  return {
    read: async () => {
      if (i >= frames.length) return { done: true, value: undefined };
      const chunk = new TextEncoder().encode(frames[i]);
      i += 1;
      return { done: false, value: chunk };
    },
  };
}

describe('streamChat', () => {
  it('parses event stream frames and calls onMessage', async () => {
    const frames = [
      'data: {"type":"retrieved","citations":[{"title":"Video A","chunk_id":1}]}\n\n',
      'data: {"type":"partial","text":"Hello"}\n\n',
      'data: {"type":"partial","text":" world"}\n\n',
      'data: {"type":"done","answer":"Hello world","citations":[{"title":"Video A","chunk_id":1}]}\n\n',
    ];

    const reader = makeReader(frames);

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      body: {
        getReader: () => reader,
      },
    } as any));

    const messages: any[] = [];
    await streamChat({ question: 'Q', thread_id: 't1' }, (chunk) => messages.push(chunk));

    expect(messages.some((m) => m.citations && m.citations.length)).toBe(true);
    expect(messages.some((m) => m.answer && m.answer.includes('Hello'))).toBe(true);
    expect(messages.some((m) => m.done)).toBe(true);
  });
});
