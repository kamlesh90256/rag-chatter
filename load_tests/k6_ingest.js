import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

// Measure ingestion request latency (time to HTTP accept)
const ingestTrend = new Trend('ingest_latency_ms');

// Replace with your deployed backend URL or use env var via k6 -e API_BASE=...
const API_BASE = __ENV.API_BASE || 'http://localhost:8000';

export const options = {
  scenarios: {
    small: {
      executor: 'constant-vus',
      vus: 10,
      duration: '1m',
    },
    medium: {
      executor: 'constant-vus',
      startTime: '1m',
      vus: 50,
      duration: '2m',
    },
    spike: {
      executor: 'ramping-vus',
      startTime: '3m',
      stages: [
        { duration: '30s', target: 100 },
        { duration: '30s', target: 0 },
      ],
    },
  },
  thresholds: {
    'ingest_latency_ms': ['p(95)<5000'],
    'http_req_failed': ['rate<0.01'],
  },
};

function randomYoutubeUrl() {
  // use sample public video ids — in production use real test videos
  const ids = ['dQw4w9WgXcQ', 'kXYiU_JCYtU', '3JZ_D3ELwOQ'];
  const id = ids[Math.floor(Math.random() * ids.length)];
  return `https://www.youtube.com/watch?v=${id}`;
}

function randomInstagramUrl() {
  const ids = ['CRWEW7Qqx5x', 'B8QaZW4AQY_', 'BxK6m4Ilg1K'];
  const id = ids[Math.floor(Math.random() * ids.length)];
  return `https://www.instagram.com/reel/${id}/`;
}

export default function () {
  const payload = JSON.stringify({ youtube_url: randomYoutubeUrl(), instagram_url: randomInstagramUrl() });
  const params = { headers: { 'Content-Type': 'application/json' } };
  const start = Date.now();
  const res = http.post(`${API_BASE}/ingest`, payload, params);
  const duration = Date.now() - start;
  ingestTrend.add(duration);

  check(res, {
    'ingest accepted (200 or 202)': (r) => r.status === 200 || r.status === 202,
  });

  // If response contains job_id, optionally poll status (lightweight)
  if (res.status === 200 || res.status === 202) {
    try {
      const body = res.json();
      if (body.job_id) {
        // record that job was enqueued; skip waiting for completion here
      }
    } catch (e) {
      // ignore parsing errors
    }
  }

  sleep(1);
}
