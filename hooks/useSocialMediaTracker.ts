
import { useState, useCallback, useEffect } from 'react';
import type { Leader, SocialMediaPost } from '../types';
import { generateSocialMediaPosts } from '../services/geminiService';
import { INITIAL_LEADERS } from '../constants';

export const useSocialMediaTracker = () => {
  const [leaders, setLeaders] = useState<Leader[]>(INITIAL_LEADERS);
  const [posts, setPosts] = useState<SocialMediaPost[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllPosts = useCallback(async (currentLeaders: Leader[]) => {
    setIsLoading(true);
    setError(null);
    try {
      const allPostsPromises = currentLeaders.map(leader => generateSocialMediaPosts(leader));
      const postsByLeader = await Promise.all(allPostsPromises);
      const flattenedPosts = postsByLeader.flat().sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      setPosts(flattenedPosts);
    } catch (e) {
      setError("Failed to fetch social media data. Please check your API key and try again.");
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
      const newPosts = await generateSocialMediaPosts(leader);
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
      const newPosts = await generateSocialMediaPosts(leader);
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
