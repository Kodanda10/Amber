'use client';

import { useMemo } from 'react';
import { Dashboard } from '@/components/Dashboard';
import { useSocialMediaTracker } from '@/hooks/useSocialMediaTracker';

export default function DashboardPage() {
  const { leaders, posts, isLoading, error, removeLeader, fetchPostsForLeader } = useSocialMediaTracker();

  const reportData = useMemo(() => {
    return {
      totalPosts: posts.length,
      totalLeaders: leaders.length,
      posts,
    };
  }, [posts, leaders]);

  return (
    <Dashboard
      reportData={reportData}
      leaders={leaders}
      isLoading={isLoading}
      error={error}
      onRemoveLeader={removeLeader}
      onRefreshLeader={fetchPostsForLeader}
    />
  );
}
