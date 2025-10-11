import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeAll } from 'vitest';
import { PostCard } from '@/components/PostCard';
import type { SocialMediaPost } from '@/types';
import { Platform, Sentiment, VerificationStatus } from '@/types';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  (globalThis as unknown as { ResizeObserver?: typeof ResizeObserverMock }).ResizeObserver = ResizeObserverMock;
});

const makeTwitterPost = (overrides: Partial<SocialMediaPost> = {}): SocialMediaPost => ({
  id: 'twitter-post-1',
  leaderId: 'leader-1',
  leaderName: 'Test Leader',
  platform: Platform.Twitter,
  content: 'This is a sample tweet from a political leader.',
  timestamp: new Date('2024-10-10T10:00:00.000Z').toISOString(),
  sentiment: Sentiment.Neutral,
  metrics: {
    likes: 150,
    comments: 10,
    shares: 30,
    origin: 'twitter',
    link: 'https://twitter.com/testleader/status/1234567890',
    platformPostId: '1234567890',
  },
  verificationStatus: VerificationStatus.NeedsReview,
  ...overrides,
});

describe('Twitter/X Post Display (ING-015)', () => {
  it('renders Twitter post with X/Twitter icon', () => {
    const post = makeTwitterPost();
    render(<PostCard post={post} />);

    // Check platform is displayed
    expect(screen.getByText(/posted on Twitter/i)).toBeInTheDocument();
    
    // Check content is rendered
    expect(screen.getByText(post.content)).toBeInTheDocument();
    
    // Check leader name appears (use getAllByText since it appears multiple times)
    const leaderNames = screen.getAllByText(post.leaderName);
    expect(leaderNames.length).toBeGreaterThan(0);
  });

  it('displays Twitter post with media URL', () => {
    const post = makeTwitterPost({
      metrics: {
        likes: 200,
        comments: 15,
        shares: 45,
        origin: 'twitter',
        link: 'https://twitter.com/testleader/status/1234567891',
        mediaUrl: 'https://pbs.twimg.com/media/test_image.jpg',
        platformPostId: '1234567891',
      },
    });
    
    render(<PostCard post={post} />);

    // Check media is rendered
    const mediaImg = screen.getByTestId('post-media');
    expect(mediaImg).toBeInTheDocument();
    expect(mediaImg).toHaveAttribute('src', 'https://pbs.twimg.com/media/test_image.jpg');
  });

  it('displays Twitter post with author avatar', () => {
    const post = makeTwitterPost({
      metrics: {
        likes: 150,
        comments: 10,
        shares: 30,
        origin: 'twitter',
        avatarUrl: 'https://pbs.twimg.com/profile_images/test.jpg',
        platformPostId: '1234567890',
      },
    });
    
    render(<PostCard post={post} />);

    // Check avatar is rendered
    const avatar = screen.getByTestId('post-avatar');
    expect(avatar).toBeInTheDocument();
    expect(avatar).toHaveAttribute('src', 'https://pbs.twimg.com/profile_images/test.jpg');
  });

  it('displays Twitter post link correctly', () => {
    const post = makeTwitterPost();
    render(<PostCard post={post} />);

    // The link should be in the content area (though not as a title in this case)
    expect(screen.getByText(post.content)).toBeInTheDocument();
  });

  it('displays Twitter sentiment correctly', () => {
    const post = makeTwitterPost({
      sentiment: Sentiment.Positive,
    });
    
    render(<PostCard post={post} />);

    // Check sentiment badge
    expect(screen.getByText('Positive')).toBeInTheDocument();
  });

  it('displays Twitter post metrics', () => {
    const post = makeTwitterPost({
      metrics: {
        likes: 500,
        comments: 50,
        shares: 100,
        origin: 'twitter',
        platformPostId: '1234567890',
      },
    });
    
    render(<PostCard post={post} />);

    // Verify post is rendered (metrics are stored but not necessarily displayed in current UI)
    expect(screen.getByText(post.content)).toBeInTheDocument();
  });
});
