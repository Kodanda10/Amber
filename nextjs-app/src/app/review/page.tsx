'use client';

import { useState } from 'react';
import { ReviewQueue } from '@/components/ReviewQueue';
import type { ReviewItem } from '@/types';
import { Sentiment, Platform, VerificationStatus } from '@/types';

const mockItems: ReviewItem[] = [
  {
    id: '1',
    postId: 'p1',
    state: 'pending',
    post: {
      id: 'p1',
      leaderId: 'l1',
      leaderName: 'Leader 1',
      platform: Platform.Facebook,
      content: 'This is a post that needs review.',
      timestamp: new Date().toISOString(),
      sentiment: Sentiment.Neutral,
      metrics: { likes: 10, comments: 5, shares: 2 },
      verificationStatus: VerificationStatus.NeedsReview,
    },
  },
  {
    id: '2',
    postId: 'p2',
    state: 'pending',
    post: {
      id: 'p2',
      leaderId: 'l2',
      leaderName: 'Leader 2',
      platform: Platform.Twitter,
      content: 'Another post requiring approval.',
      timestamp: new Date().toISOString(),
      sentiment: Sentiment.Positive,
      metrics: { likes: 100, comments: 50, shares: 20 },
      verificationStatus: VerificationStatus.NeedsReview,
    },
  },
];

export default function ReviewPage() {
  const [items, setItems] = useState<ReviewItem[]>(mockItems);

  const handleApprove = (id: string) => {
    console.log(`Approved item ${id}`);
    setItems(items.filter(item => item.id !== id));
  };

  const handleReject = (id: string, notes?: string) => {
    console.log(`Rejected item ${id} with notes: ${notes}`);
    setItems(items.filter(item => item.id !== id));
  };

  return (
    <ReviewQueue
      items={items}
      isLoading={false}
      onApprove={handleApprove}
      onReject={handleReject}
      error={null}
    />
  );
}
