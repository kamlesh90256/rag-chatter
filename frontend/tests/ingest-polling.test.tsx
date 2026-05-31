import { describe, it, expect, vi } from 'vitest';
import { ingestVideos, getIngestStatus } from '@/services/api';

// Mock fetch for ingest + polling
describe('ingest polling', () => {
  it('polls ingest status until success', async () => {
    const jobId = 'job-1';
    // first call to /ingest returns job_id
    vi.stubGlobal('fetch', vi.fn()
      // ingest call
      .mockResolvedValueOnce({ ok: true, json: async () => ({ job_id: jobId }) })
      // first poll returns PENDING
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: jobId, state: 'PENDING' }) })
      // second poll returns SUCCESS with payload
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: jobId, state: 'SUCCESS', status: { videos: [] } }) })
    );

    const res = await ingestVideos({ youtube_url: 'y', instagram_url: 'i' });
    expect(res.job_id).toBe(jobId);

    const s1 = await getIngestStatus(jobId);
    expect(s1.state).toBe('PENDING');

    const s2 = await getIngestStatus(jobId);
    expect(s2.state).toBe('SUCCESS');
  });
});
