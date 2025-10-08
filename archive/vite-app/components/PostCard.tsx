
import React from 'react';
import type { SocialMediaPost } from '../types';
import { Sentiment, VerificationStatus, Platform } from '../types';
import { PLATFORM_ICONS } from '../constants';

interface PostCardProps {
  post: SocialMediaPost;
}

const sentimentColors: Record<Sentiment, string> = {
  [Sentiment.Positive]: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  [Sentiment.Negative]: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  [Sentiment.Neutral]: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

const verificationColors: Record<VerificationStatus, string> = {
  [VerificationStatus.Verified]: 'border-blue-500',
  [VerificationStatus.NeedsReview]: 'border-yellow-500',
  [VerificationStatus.Unverified]: 'border-red-500',
};

const platformTextColors: Record<Platform, string> = {
    [Platform.Twitter]: 'text-blue-400',
    [Platform.Facebook]: 'text-blue-600',
    [Platform.Instagram]: 'text-pink-500',
}

export const PostCard: React.FC<PostCardProps> = ({ post }) => {
  const Icon = PLATFORM_ICONS[post.platform];
  const timeAgo = new Intl.RelativeTimeFormat('en', { style: 'short' }).format(Math.floor((new Date(post.timestamp).getTime() - Date.now()) / (1000 * 60 * 60 * 24)), 'day');

  return (
    <div className={`p-5 border-b border-gray-200 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors duration-200 border-l-4 ${verificationColors[post.verificationStatus]}`}>
      <div className="flex justify-between items-start">
        <div className="flex items-center space-x-3">
           <div className="flex-shrink-0">
             {Icon && <Icon className={`w-6 h-6 ${platformTextColors[post.platform]}`} />}
           </div>
           <div>
            <p className="font-bold text-gray-800 dark:text-gray-100">{post.leaderName}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">posted on {post.platform} &bull; {timeAgo}</p>
           </div>
        </div>
        <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${sentimentColors[post.sentiment]}`}>{post.sentiment}</span>
      </div>
      <p className="my-3 text-gray-700 dark:text-gray-300">{post.content}</p>
      <div className="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
        <Metric icon={<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a2 2 0 0 1 1.79 1.11L15 5.88Z"/></svg>} value={post.metrics.likes.toLocaleString()} />
        <Metric icon={<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>} value={post.metrics.comments.toLocaleString()} />
        <Metric icon={<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/></svg>} value={post.metrics.shares.toLocaleString()} />
      </div>
    </div>
  );
};


const Metric: React.FC<{ icon: React.ReactNode, value: string | number }> = ({ icon, value }) => (
    <div className="flex items-center space-x-1.5 hover:text-indigo-500">
        {icon}
        <span>{value}</span>
    </div>
);
