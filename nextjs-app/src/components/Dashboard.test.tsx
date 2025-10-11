import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, beforeAll, afterAll, expect } from 'vitest';
import { Dashboard } from './Dashboard';
import { Platform, Sentiment, VerificationStatus } from '@/types';

class IntersectionObserverMock {
  constructor() {}
  observe() {}
  disconnect() {}
  unobserve() {}
}

class ResizeObserverMock {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
}

describe('Dashboard', () => {
  beforeAll(() => {
    (global as any).IntersectionObserver = IntersectionObserverMock;
    (global as any).ResizeObserver = ResizeObserverMock;
  });

  afterAll(() => {
    delete (global as any).IntersectionObserver;
    delete (global as any).ResizeObserver;
  });

  it('highlights language distribution for Hindi posts', () => {
    render(
      <Dashboard
        reportData={{
          totalLeaders: 2,
          totalPosts: 2,
          posts: [
            {
              id: 'post-hindi',
              leaderId: 'leader-1',
              leaderName: 'Leader One',
              platform: Platform.Facebook,
              content: 'Hindi content',
              timestamp: '2025-10-04T09:00:00.000Z',
              sentiment: Sentiment.Neutral,
              metrics: {
                likes: 1,
                comments: 1,
                shares: 0,
                language: 'hi-IN',
              },
              verificationStatus: VerificationStatus.Verified,
            },
            {
              id: 'post-english',
              leaderId: 'leader-2',
              leaderName: 'Leader Two',
              platform: Platform.Facebook,
              content: 'English content',
              timestamp: '2025-10-03T09:00:00.000Z',
              sentiment: Sentiment.Positive,
              metrics: {
                likes: 2,
                comments: 0,
                shares: 0,
                language: 'en',
              },
              verificationStatus: VerificationStatus.NeedsReview,
            },
          ],
        }}
        leaders={[
          {
            id: 'leader-1',
            name: 'Leader One',
            handles: { facebook: '@leaderone' },
            trackingTopics: ['development'],
          },
          {
            id: 'leader-2',
            name: 'Leader Two',
            handles: { facebook: '@leadertwo' },
            trackingTopics: ['policy'],
          },
        ]}
        isLoading={false}
        error={null}
      />,
    );

    expect(screen.getByText(/हिन्दी ·/)).toBeInTheDocument();
    expect(screen.getByText(/English ·/)).toBeInTheDocument();
  });
});
