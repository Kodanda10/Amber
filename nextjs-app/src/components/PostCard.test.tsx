import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PostCard } from './PostCard';
import { Platform, Sentiment, VerificationStatus, type SocialMediaPost } from '@/types';

const buildPost = (overrides: Partial<SocialMediaPost> = {}): SocialMediaPost => {
  const { metrics: metricOverrides, ...rest } = overrides;
  return {
    id: 'post-1',
    leaderId: 'leader-1',
    leaderName: 'Leader One',
    platform: Platform.Facebook,
    content: 'Content body',
    timestamp: '2025-10-04T12:00:00.000Z',
    sentiment: Sentiment.Positive,
    metrics: {
      likes: 10,
      comments: 2,
      shares: 1,
      source: 'Example News',
      origin: 'graph',
      link: 'https://example.com',
      avatarUrl: 'https://graph.facebook.com/leaderone/picture?type=large',
      language: 'hi-IN',
      ...(metricOverrides ?? {}),
    },
    verificationStatus: VerificationStatus.Verified,
    ...rest,
  };
};

describe('PostCard', () => {
  it('renders Hindi language badge and formatted date for Hindi posts', () => {
    const post = buildPost();
    render(<PostCard post={post} />);

    expect(screen.getByText('हिन्दी')).toBeInTheDocument();
    const badge = screen.getByTestId('hindi-date-badge');
    expect(badge).toHaveTextContent('०४ अक्तूबर २०२५');
  });

  it('renders post avatar from backend metadata when available', () => {
    const post = buildPost();
    render(<PostCard post={post} />);

    const avatar = screen.getByTestId('post-avatar');
    expect(avatar).toHaveAttribute('src', 'https://graph.facebook.com/leaderone/picture?type=large');
  });

  it('renders media attachment when Graph API provides mediaUrl', () => {
    const post = buildPost({
      id: 'post-2',
      metrics: {
        mediaUrl: 'https://graph.facebook.com/leaderone/posts/12345/media',
      } as SocialMediaPost['metrics'],
    });
    render(<PostCard post={post} />);

    const media = screen.getByTestId('post-media');
    expect(media).toHaveAttribute('src', 'https://graph.facebook.com/leaderone/posts/12345/media');
    expect(media).toHaveAttribute('alt', 'Graph media for Leader One');
  });

  // FE-CORE-001: Sentiment visualization test
  it('renders sentiment bar when sentimentScore is present', () => {
    const post = buildPost({
      sentiment: Sentiment.Positive,
      metrics: {
        sentimentScore: 0.75,
      } as SocialMediaPost['metrics'],
    });
    render(<PostCard post={post} />);

    expect(screen.getByTestId('sentiment-bar-container')).toBeInTheDocument();
    expect(screen.getByTestId('sentiment-score')).toHaveTextContent('0.75');
    // Verify sentiment bar fill has correct width
    const fill = screen.getByTestId('sentiment-bar-fill');
    expect(fill.style.width).toBe('87.5%'); // (0.75 + 1) / 2 * 100 = 87.5%
  });

  it('does not render sentiment bar when sentimentScore is missing', () => {
    const post = buildPost({
      sentiment: Sentiment.Neutral,
      metrics: {
        sentimentScore: undefined,
      } as SocialMediaPost['metrics'],
    });
    render(<PostCard post={post} />);

    expect(screen.queryByTestId('sentiment-bar-container')).not.toBeInTheDocument();
  });
});
