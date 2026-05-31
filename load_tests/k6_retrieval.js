import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const retrievalTrend = new Trend('retrieval_latency_ms');
const API_BASE = __ENV.API_BASE || 'http://localhost:8000';

export const options = {
  vus: 50,
  duration: '2m',
  thresholds: {
    'retrieval_latency_ms': ['p(95)<500'],
    'http_req_failed': ['rate<0.01'],
  },
};

export default function () {
  const payload = JSON.stringify({ question: 'Why did Video A outperform Video B?', thread_id: 'load-test-thread', video_ids: [] , stream: false});
  const params = { headers: { 'Content-Type': 'application/json' } };
  const start = Date.now();
  const res = http.post(`${API_BASE}/chat`, payload, params);
  const duration = Date.now() - start;
  retrievalTrend.add(duration);

  check(res, {
    'retrieval success (200)': (r) => r.status === 200,
    'response contains answer': (r) => r.body && r.body.indexOf('answer') !== -1,
  });
  sleep(0.5);
}
