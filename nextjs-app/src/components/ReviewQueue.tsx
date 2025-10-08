import React from 'react';
import type { ReviewItem } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { PostCard } from '@/components/PostCard';

interface ReviewQueueProps {
  items: ReviewItem[];
  isLoading: boolean;
  onApprove: (id: string) => void;
  onReject: (id: string, notes?: string) => void;
  error: string | null;
}

export const ReviewQueue: React.FC<ReviewQueueProps> = ({ items, isLoading, onApprove, onReject, error }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Review Queue</h2>
      </div>
      {error && (
        <div className="mb-4 text-sm text-red-600 dark:text-red-400">{error}</div>
      )}
      {isLoading && !items.length && (
        <div className="flex items-center justify-center flex-1">
          <LoadingSpinner />
        </div>
      )}
      <div className="space-y-4 overflow-y-auto pr-1 flex-1">
        {items.map(item => (
          <div key={item.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-700/40">
            {item.post && <PostCard post={item.post} />}
            <div className="mt-3 flex items-center gap-2">
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 font-medium capitalize">{item.state}</span>
              {item.notes && <span className="text-xs text-gray-500 dark:text-gray-400">Notes: {item.notes}</span>}
              <div className="ml-auto flex gap-2">
                <button
                  onClick={() => onApprove(item.id)}
                  disabled={isLoading}
                  className="px-3 py-1 text-xs font-medium rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  onClick={() => {
                    const value = prompt('Rejection notes (optional)') || undefined;
                    onReject(item.id, value);
                  }}
                  disabled={isLoading}
                  className="px-3 py-1 text-xs font-medium rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                >
                  Reject
                </button>
              </div>
            </div>
          </div>
        ))}
        {!isLoading && items.length === 0 && (
          <p className="text-center text-gray-500 dark:text-gray-400 py-10">No items pending review.</p>
        )}
      </div>
    </div>
  );
};
