// DEPRECATED MODULE
// This frontend news fetching & sentiment code is deprecated. All ingestion and sentiment
// classification have been unified in the backend API. This file is retained temporarily
// to avoid breaking imports during transition. Any function invocation will throw to make
// accidental usage obvious. Remove this file once references are cleaned up.
import type { SocialMediaPost } from '@/types';

export const fetchArticlesForLeader = async (): Promise<never> => {
  throw new Error('fetchArticlesForLeader is deprecated. Use backend API /api/leaders/:id/refresh');
};

export const buildPostsFromArticles = (): SocialMediaPost[] => {
  throw new Error('buildPostsFromArticles is deprecated. Backend provides sentiment + mapping');
};

export const fetchLiveDashboard = async (): Promise<never> => {
  throw new Error('fetchLiveDashboard is deprecated. Use backend API /api/dashboard');
};