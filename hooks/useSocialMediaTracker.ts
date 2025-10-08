
import { useState, useCallback, useEffect } from 'react';
import type { Leader, SocialMediaPost } from '../types';
import { INITIAL_LEADERS } from '../constants';
import { fetchPostsFromBackend } from '../services/api';


export const useSocialMediaTracker = () => {
  const [leaders, setLeaders] = useState<Leader[]>(INITIAL_LEADERS);
  const [posts, setPosts] = useState<SocialMediaPost[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllPosts = useCallback(async (currentLeaders: Leader[]) => {
    setIsLoading(true);
    setError(
        "This app is now configured to fetch live data. " +
        "Since there is no backend connected, no posts will appear. " +
        "You need to build a server-side component to connect to the real social media APIs."
    );
    try {
      // In a real app, you might have a single endpoint to fetch all posts
      // or you might loop like this.
      const allPostsPromises = currentLeaders.map(leader => fetchPostsFromBackend(leader));
      const postsByLeader = await Promise.all(allPostsPromises);
      const flattenedPosts = postsByLeader.flat().sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      setPosts(flattenedPosts);
    } catch (e) {
      setError("Failed to fetch social media data from the backend.");
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllPosts(leaders);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const addLeader = useCallback(async (leader: Leader) => {
    setIsLoading(true);
    try {
      const newPosts = await fetchPostsFromBackend(leader);
      setLeaders(prev => [...prev, leader]);
      setPosts(prev => [...newPosts, ...prev].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()));
    } catch (e) {
      setError("Failed to add leader and fetch their posts.");
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const removeLeader = useCallback((leaderId: string) => {
    setLeaders(prev => prev.filter(l => l.id !== leaderId));
    setPosts(prev => prev.filter(p => p.leaderId !== leaderId));
  }, []);
  
  const fetchPostsForLeader = useCallback(async (leaderId: string) => {
    const leader = leaders.find(l => l.id === leaderId);
    if (!leader) return;

    setIsLoading(true);
    try {
      const newPosts = await fetchPostsFromBackend(leader);
      // Remove old posts for this leader and add the new ones
      setPosts(prev => 
        [...prev.filter(p => p.leaderId !== leaderId), ...newPosts]
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      );
    } catch (e) {
      setError(`Failed to refresh posts for ${leader.name}.`);
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, [leaders]);

  return { leaders, posts, isLoading, error, addLeader, removeLeader, fetchPostsForLeader };
};
