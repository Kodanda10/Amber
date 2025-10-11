
import { useState, useCallback, useEffect } from 'react';
import type { Leader, SocialMediaPost } from '@/types';

const jsonHeaders = { 'Content-Type': 'application/json' } as const;

const sortPosts = (items: SocialMediaPost[]): SocialMediaPost[] =>
  [...items].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

interface DashboardResponse {
  leaders: Leader[];
  posts: SocialMediaPost[];
}

const normalizeLeaderPayload = (leader: Leader) => ({
  name: leader.name,
  handles: leader.handles,
  trackingTopics: leader.trackingTopics,
});

export const useSocialMediaTracker = () => {
  const [leaders, setLeaders] = useState<Leader[]>([]);
  const [posts, setPosts] = useState<SocialMediaPost[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async (manageLoading: boolean = true) => {
    if (manageLoading) {
      setIsLoading(true);
    }
    try {
      setError(null);
      const response = await fetch('/api/dashboard');
      if (!response.ok) {
        throw new Error(`Failed to load dashboard (status ${response.status})`);
      }
      const data = (await response.json()) as DashboardResponse;
      setLeaders(data.leaders);
      setPosts(sortPosts(data.posts));
    } catch (err) {
      console.error(err);
      setError('Failed to fetch social media data from the backend.');
    } finally {
      if (manageLoading) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const addLeader = useCallback(
    async (leader: Leader) => {
      setIsLoading(true);
      try {
        setError(null);
        const response = await fetch('/api/leaders', {
          method: 'POST',
          headers: jsonHeaders,
          body: JSON.stringify(normalizeLeaderPayload(leader)),
        });
        if (!response.ok) {
          throw new Error(`Failed to add leader (status ${response.status})`);
        }
        await loadDashboard(false);
      } catch (err) {
        console.error(err);
        setError(`Failed to add leader ${leader.name}.`);
      } finally {
        setIsLoading(false);
      }
    },
    [loadDashboard],
  );

  const removeLeader = useCallback(async (leaderId: string) => {
    setIsLoading(true);
    try {
      setError(null);
      const response = await fetch(`/api/leaders/${leaderId}`, { method: 'DELETE' });
      if (!response.ok) {
        throw new Error(`Failed to remove leader (status ${response.status})`);
      }
      setLeaders(prev => prev.filter(leader => leader.id !== leaderId));
      setPosts(prev => prev.filter(post => post.leaderId !== leaderId));
    } catch (err) {
      console.error(err);
      setError('Failed to remove leader.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchPostsForLeader = useCallback(
    async (leaderId: string) => {
      const leader = leaders.find(item => item.id === leaderId);
      if (!leader) {
        return;
      }

      setIsLoading(true);
      try {
        setError(null);
        const response = await fetch(`/api/leaders/${leaderId}/refresh`, { method: 'POST' });
        if (!response.ok) {
          throw new Error(`Failed to refresh posts (status ${response.status})`);
        }
        const data = (await response.json()) as { posts: SocialMediaPost[] };
        setPosts(prev =>
          sortPosts([
            ...prev.filter(post => post.leaderId !== leaderId),
            ...(data.posts ?? []),
          ]),
        );
      } catch (err) {
        console.error(err);
        setError(`Failed to refresh posts for ${leader.name}.`);
      } finally {
        setIsLoading(false);
      }
    },
    [leaders],
  );

  return { leaders, posts, isLoading, error, addLeader, removeLeader, fetchPostsForLeader, reload: loadDashboard };
};
