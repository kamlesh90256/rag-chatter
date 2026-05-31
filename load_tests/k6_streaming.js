import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const ttfbTrend = new Trend('streaming_ttfb_ms');
const fullTrend = new Trend('streaming_full_ms');
const API_BASE = __ENV.API_BASE || 'http://localhost:8000';

export const options = {
  vus: 20,
  duration: '2m',
  thresholds: {
    'streaming_ttfb_ms': ['p(95)<2000'],
    'streaming_full_ms': ['p(95)<10000'],
  },
};

export default function () {
  const payload = JSON.stringify({ question: 'Compare Video A and B engagement', thread_id: 'stream-thread', stream: true });
  const params = { headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' }, timeout: '120s' };

  const start = Date.now();
  const res = http.post(`${API_BASE}/chat`, payload, params);
  // k6 provides timings.waiting as TTFB (time to first byte)
  ttfbTrend.add(res.timings.waiting);
  fullTrend.add(res.timings.duration);

  check(res, {
    'streaming endpoint returns 200': (r) => r.status === 200,
  });

  sleep(1);
}
