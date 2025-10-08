import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, waitFor } from '@testing-library/react';
import React from 'react';
import type { Leader, SocialMediaPost } from '@/types';
import { Platform, Sentiment, VerificationStatus } from '@/types';
import { useSocialMediaTracker } from './useSocialMediaTracker';

let tracker: ReturnType<typeof useSocialMediaTracker>;

const HookHarness: React.FC = () => {
  tracker = useSocialMediaTracker();
  return (
    <div>
      <span data-testid="leaders-count">{tracker.leaders.length}</span>
      <span data-testid="posts-count">{tracker.posts.length}</span>
      <span data-testid="is-loading">{tracker.isLoading ? 'yes' : 'no'}</span>
      <span data-testid="error">{tracker.error ?? ''}</span>
    </div>
  );
};

describe('useSocialMediaTracker', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('loads leaders and posts from the dashboard API', async () => {
    const leaders: Leader[] = [
      {
        id: 'leader-1',
        name: 'Leader 1',
        handles: { facebook: '@leader1' },
        trackingTopics: ['policy'],
      },
    ];
    const posts: SocialMediaPost[] = [
      {
        id: 'post-1',
        leaderId: 'leader-1',
        leaderName: 'Leader 1',
        platform: Platform.Facebook,
        content: 'Older update',
        timestamp: '2024-10-01T10:00:00Z',
        sentiment: Sentiment.Neutral,
        metrics: { likes: 1, comments: 0, shares: 0 },
        verificationStatus: VerificationStatus.NeedsReview,
      },
      {
        id: 'post-2',
        leaderId: 'leader-1',
        leaderName: 'Leader 1',
        platform: Platform.Facebook,
        content: 'Latest headline',
        timestamp: '2024-10-02T12:00:00Z',
        sentiment: Sentiment.Neutral,
        metrics: { likes: 3, comments: 1, shares: 1 },
        verificationStatus: VerificationStatus.NeedsReview,
      },
    ];

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ leaders, posts }),
    } as Response);

    render(<HookHarness />);

    await waitFor(() => expect(tracker.isLoading).toBe(false));
    expect(tracker.error).toBeNull();
    expect(tracker.leaders).toEqual(leaders);
    expect(tracker.posts.map(post => post.id)).toEqual(['post-2', 'post-1']);
  });

  it('surfaces an error message when dashboard fetch fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    } as Response);

    render(<HookHarness />);

    await waitFor(() => expect(tracker.isLoading).toBe(false));
    expect(tracker.error).toMatch(/Failed to fetch social media data/);
    expect(tracker.leaders).toHaveLength(0);
    expect(tracker.posts).toHaveLength(0);
  });
});
