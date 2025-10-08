import type { Leader, SocialMediaPost } from '@/types';
// Ingestion unified: all data must come from backend API. Fallback paths removed.

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:5000';

type Source = 'backend';

// Fallback removed; keep minimal cache for quick UI hydration if needed in future.
const cache: { leaders: Leader[]; posts: SocialMediaPost[] } = { leaders: [], posts: [] };

const headers = { 'Content-Type': 'application/json' } as const;

const api = async (path: string, options?: RequestInit) => {
  const response = await fetch(`${BACKEND_URL}${path}`, options);
  if (!response.ok) {
    throw new Error(`Backend responded with status ${response.status}`);
  }
  return response;
};

// No rebuild fallback; placeholder kept for potential offline cache.

export const backendClient = {
  async getDashboard(): Promise<{ leaders: Leader[]; posts: SocialMediaPost[]; source: Source }> {
    const response = await api('/api/dashboard');
    const data = (await response.json()) as { leaders: Leader[]; posts: SocialMediaPost[] };
    cache.leaders = data.leaders;
    cache.posts = data.posts;
    return { leaders: data.leaders, posts: data.posts, source: 'backend' };
  },

  async createLeader(payload: Omit<Leader, 'id'>): Promise<{ leader: Leader; source: Source }> {
    const response = await api('/api/leaders', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    const leader = (await response.json()) as Leader;
    cache.leaders = [...cache.leaders, leader];
    return { leader, source: 'backend' };
  },

  async removeLeader(id: string): Promise<{ success: boolean; source: Source }> {
    await api(`/api/leaders/${id}`, {
      method: 'DELETE',
    });
    cache.leaders = cache.leaders.filter(l => l.id !== id);
    cache.posts = cache.posts.filter(p => p.leaderId !== id);
    return { success: true, source: 'backend' };
  },

  async refreshLeader(id: string): Promise<{ posts: SocialMediaPost[]; source: Source }> {
    const response = await api(`/api/leaders/${id}/refresh`, {
      method: 'POST',
    });
    const data = (await response.json()) as { posts: SocialMediaPost[] };
    const otherPosts = cache.posts.filter(post => post.leaderId !== id);
    cache.posts = [...otherPosts, ...data.posts];
    return { posts: data.posts, source: 'backend' };
  },
};
