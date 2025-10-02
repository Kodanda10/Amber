
import React, { useMemo } from 'react';
import type { ReportData, SocialMediaPost, Sentiment } from '../types';
import { PostCard } from './PostCard';
import { SentimentChart } from './SentimentChart';
import { LoadingSpinner } from './LoadingSpinner';

interface DashboardProps {
  reportData: ReportData;
  isLoading: boolean;
  error: string | null;
}

export const Dashboard: React.FC<DashboardProps> = ({ reportData, isLoading, error }) => {
  const sentimentData = useMemo(() => {
    const counts = reportData.posts.reduce((acc, post) => {
      acc[post.sentiment] = (acc[post.sentiment] || 0) + 1;
      return acc;
    }, {} as Record<Sentiment, number>);

    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [reportData.posts]);

  return (
    <div className="container mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <SummaryCard title="Tracked Leaders" value={reportData.totalLeaders.toString()} />
        <SummaryCard title="Total Posts Analyzed" value={reportData.totalPosts.toString()} />
        <SummaryCard title="Positive Sentiment" value={`${sentimentData.find(d => d.name === 'Positive')?.value || 0}`} />
        <SummaryCard title="Negative Sentiment" value={`${sentimentData.find(d => d.name === 'Negative')?.value || 0}`} />
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative mb-6" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4 text-gray-700 dark:text-gray-200">Sentiment Distribution</h3>
          {isLoading && !reportData.posts.length ? (
             <div className="flex justify-center items-center h-64">
                <LoadingSpinner />
             </div>
          ) : sentimentData.length > 0 ? (
            <SentimentChart data={sentimentData} />
          ) : (
            <p className="text-center text-gray-500 dark:text-gray-400 h-64 flex items-center justify-center">No sentiment data available.</p>
          )}
        </div>

        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-md">
           <h3 className="text-xl font-semibold p-6 border-b border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200">Latest Activity Feed</h3>
           <div className="h-[calc(100vh-20rem)] overflow-y-auto">
            {isLoading && !reportData.posts.length ? (
              <div className="flex justify-center items-center h-full">
                <LoadingSpinner />
              </div>
            ) : reportData.posts.length > 0 ? (
              reportData.posts.map(post => <PostCard key={post.id} post={post} />)
            ) : (
              <p className="text-center text-gray-500 dark:text-gray-400 p-10">No posts found. Add a leader to begin tracking.</p>
            )}
           </div>
        </div>
      </div>
    </div>
  );
};


const SummaryCard: React.FC<{ title: string; value: string }> = ({ title, value }) => (
  <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md flex flex-col justify-between">
    <p className="text-gray-500 dark:text-gray-400 font-medium">{title}</p>
    <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">{value}</p>
  </div>
);
