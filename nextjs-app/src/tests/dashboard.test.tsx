import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, beforeAll, expect } from 'vitest';
import { Dashboard } from '@/components/Dashboard';
import type { Leader, ReportData, SocialMediaPost } from '@/types';
import { Platform, Sentiment, VerificationStatus } from '@/types';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  (globalThis as unknown as { ResizeObserver?: typeof ResizeObserverMock }).ResizeObserver = ResizeObserverMock;
});

const makePost = (overrides: Partial<SocialMediaPost> = {}): SocialMediaPost => ({
  id: 'post-1',
  leaderId: 'leader-1',
  leaderName: 'Sample Leader',
  platform: overrides.platform ?? Platform.Facebook,
  content: 'Sample content',
  timestamp: new Date().toISOString(),
  sentiment: overrides.sentiment ?? Sentiment.Neutral,
  metrics: {
    likes: 0,
    comments: 0,
    shares: 0,
    origin: 'news',
  },
  verificationStatus: overrides.verificationStatus ?? VerificationStatus.NeedsReview,
  ...overrides,
});

describe('Dashboard leader roster', () => {
  it('renders leaders and allows removal', () => {
    const leaders: Leader[] = [
      {
        id: 'leader-1',
        name: 'Lakhan Lal Dewangan',
        handles: { facebook: '@lakhanlal.dewangan' },
        trackingTopics: ['infrastructure', 'industry'],
        avatarUrl: 'https://graph.facebook.com/lakhanlal.dewangan/picture',
      },
      {
        id: 'leader-2',
        name: 'S. B. Jaiswal',
        handles: { facebook: '@sbjaiswalbjp' },
        trackingTopics: ['education'],
      },
    ];

    const reportData: ReportData = {
      totalPosts: 1,
      totalLeaders: leaders.length,
      posts: [makePost()],
    };

    const onRemoveLeader = vi.fn();

    render(
      <Dashboard
        reportData={reportData}
        isLoading={false}
        error={null}
        leaders={leaders}
        onRemoveLeader={onRemoveLeader}
      />,
    );

    expect(screen.getByText('Lakhan Lal Dewangan')).toBeInTheDocument();

    const removeButton = screen.getByRole('button', { name: /Remove Lakhan Lal Dewangan/i });
    fireEvent.click(removeButton);

    expect(onRemoveLeader).toHaveBeenCalledWith('leader-1');
  });
});
