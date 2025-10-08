'use client';

import { useSocialMediaTracker } from '@/hooks/useSocialMediaTracker';
import { LeaderManager } from '@/components/LeaderManager';
import type { Leader } from '@/types';

export default function LeadersPage() {
  const { leaders, isLoading, error, addLeader, removeLeader, fetchPostsForLeader } = useSocialMediaTracker();

  const handleAddLeader = async (leaderName: string, facebookHandle: string, topics: string[]) => {
    const newLeader: Leader = {
      id: Date.now().toString(),
      name: leaderName,
      handles: { facebook: facebookHandle },
      trackingTopics: topics,
    };
    await addLeader(newLeader);
  };

  return (
    <LeaderManager
      leaders={leaders}
      onAddLeader={handleAddLeader}
      onRemoveLeader={removeLeader}
      onRefreshLeader={fetchPostsForLeader}
      isLoading={isLoading}
      error={error}
    />
  );
}
