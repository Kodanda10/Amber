import React, { useMemo, useRef, useEffect } from 'react';
import type { Leader, ReportData, Sentiment } from '@/types';
import { PostCard } from '@/components/PostCard';
import { SentimentChart } from '@/components/SentimentChart';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { getLanguageLabel, toDevanagariDigits } from '@/utils/localization';

interface DashboardProps {
  reportData: ReportData;
  leaders: Leader[];
  isLoading: boolean;
  error: string | null;
  onLoadMore?: () => void;
  canLoadMore?: boolean;
  isLoadingMore?: boolean;
  onRemoveLeader?: (leaderId: string) => void | Promise<void>;
  onRefreshLeader?: (leaderId: string) => void | Promise<void>;
}

export const Dashboard: React.FC<DashboardProps> = ({
  reportData,
  leaders,
  isLoading,
  error,
  onLoadMore,
  canLoadMore,
  isLoadingMore,
  onRemoveLeader,
  onRefreshLeader,
}) => {
  const sentinelRef = useRef<HTMLDivElement>(null as unknown as HTMLDivElement);
  // Activate intersection observer for infinite scroll
  useInfiniteScroll(sentinelRef, !!canLoadMore, onLoadMore, isLoadingMore);
  const sentimentData = useMemo(() => {
    const counts = reportData.posts.reduce((accumulator, post) => {
      accumulator[post.sentiment] = (accumulator[post.sentiment] || 0) + 1;
      return accumulator;
    }, {} as Record<Sentiment, number>);

    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [reportData.posts]);

  const languageStats = useMemo(() => {
    const counts = new Map<string, number>();
    for (const post of reportData.posts) {
      const code = (post.metrics.language || 'unknown').toLowerCase();
      counts.set(code, (counts.get(code) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([code, count]) => {
        const label = getLanguageLabel(code) ?? code.toUpperCase();
        const displayCount = label === 'हिन्दी' ? toDevanagariDigits(String(count)) : String(count);
        return { code, label, count, displayCount };
      })
      .sort((a, b) => b.count - a.count);
  }, [reportData.posts]);

  return (
    <div className="container mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <SummaryCard title="Tracked Leaders" value={leaders.length.toString()} />
        <SummaryCard title="Total Posts Analyzed" value={reportData.totalPosts.toString()} />
        <SummaryCard title="Positive Sentiment" value={`${sentimentData.find(d => d.name === 'Positive')?.value || 0}`} />
        <SummaryCard title="Negative Sentiment" value={`${sentimentData.find(d => d.name === 'Negative')?.value || 0}`} />
        <LanguageSummaryCard languages={languageStats.map(({ label, displayCount }) => ({ label, displayCount }))} />
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative mb-6" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      <LeaderRoster
        leaders={leaders}
        onRemoveLeader={onRemoveLeader}
        onRefreshLeader={onRefreshLeader}
        isBusy={isLoading}
      />

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
          <div className="h-[calc(100vh-20rem)] overflow-y-auto space-y-4">
            {isLoading && !reportData.posts.length ? (
              <div className="flex justify-center items-center h-full">
                <LoadingSpinner />
              </div>
            ) : reportData.posts.length > 0 ? (
              <>
                {reportData.posts.map(post => <PostCard key={post.id} post={post} />)}
                {onLoadMore && canLoadMore && (
                  <div ref={sentinelRef} className="flex justify-center py-6 text-xs text-gray-500 dark:text-gray-400">
                    {isLoadingMore ? 'Loading more…' : 'Scroll to load more'}
                  </div>
                )}
              </>
            ) : (
              <p className="text-center text-gray-500 dark:text-gray-400 p-10">No posts found. Add a leader to begin tracking.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface LeaderRosterProps {
  leaders: Leader[];
  onRemoveLeader?: (leaderId: string) => void | Promise<void>;
  onRefreshLeader?: (leaderId: string) => void | Promise<void>;
  isBusy: boolean;
}

const LeaderRoster: React.FC<LeaderRosterProps> = ({ leaders, onRemoveLeader, onRefreshLeader, isBusy }) => (
  <section className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-200">Leader Roster</h3>
      {isBusy && (
        <div className="flex items-center text-xs font-medium text-indigo-600 dark:text-indigo-300">
          <LoadingSpinner />
          <span className="ml-2">Syncing…</span>
        </div>
      )}
    </div>
    {leaders.length > 0 ? (
      <ul className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {leaders.map(leader => (
          <li key={leader.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-start justify-between bg-gray-50 dark:bg-gray-700/40">
            <div className="flex items-start gap-3">
              {leader.avatarUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={leader.avatarUrl} alt={leader.name} className="h-12 w-12 rounded-full object-cover border border-gray-300 dark:border-gray-600" />
              ) : (
                <div className="h-12 w-12 rounded-full bg-indigo-500 text-white flex items-center justify-center font-semibold">
                  {leader.name.charAt(0)}
                </div>
              )}
              <div>
                <p className="font-semibold text-gray-800 dark:text-gray-100">{leader.name}</p>
                {leader.handles.facebook && (
                  <p className="text-sm text-indigo-500">{leader.handles.facebook}</p>
                )}
                {leader.trackingTopics.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {leader.trackingTopics.map(topic => (
                      <span
                        key={topic}
                        className="text-xs font-medium px-2 py-1 rounded-full bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {onRefreshLeader && (
                <button
                  type="button"
                  onClick={() => {
                    void onRefreshLeader(leader.id);
                  }}
                  className="px-3 py-1 text-xs rounded-full border border-indigo-200 text-indigo-600 hover:bg-indigo-50 dark:border-indigo-700 dark:text-indigo-300 dark:hover:bg-indigo-900/40"
                  aria-label={`Refresh ${leader.name}`}
                >
                  Refresh
                </button>
              )}
              {onRemoveLeader && (
                <button
                  type="button"
                  onClick={() => {
                    void onRemoveLeader(leader.id);
                  }}
                  className="px-3 py-1 text-xs rounded-full border border-red-200 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-300 dark:hover:bg-red-900/40"
                  aria-label={`Remove ${leader.name}`}
                >
                  Remove
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    ) : (
      <p className="text-sm text-gray-500 dark:text-gray-400">No leaders are being tracked yet.</p>
    )}
  </section>
);

function useInfiniteScroll(ref: React.RefObject<HTMLElement>, enabled: boolean | undefined, cb: (() => void) | undefined, loading: boolean | undefined) {
  useEffect(() => {
    if (!enabled || !ref.current || !cb) return;
    const el = ref.current;
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting && !loading) {
          cb();
        }
      }
    }, { root: null, rootMargin: '200px', threshold: 0 });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref, enabled, cb, loading]);
}

const SummaryCard: React.FC<{ title: string; value: string }> = ({ title, value }) => (
  <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md flex flex-col justify-between">
    <p className="text-gray-500 dark:text-gray-400 font-medium">{title}</p>
    <p className="text-3xl font-bold text-gray-800 dark:text-white mt-2">{value}</p>
  </div>
);

const LanguageSummaryCard: React.FC<{ languages: Array<{ label: string; displayCount: string }> }> = ({ languages }) => {
  if (!languages.length) {
    return <SummaryCard title="Languages" value="—" />;
  }
  const topLanguages = languages.slice(0, 3);
  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md flex flex-col">
      <p className="text-gray-500 dark:text-gray-400 font-medium">Languages</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {topLanguages.map(language => (
          <span
            key={language.label}
            className="text-xs font-semibold uppercase tracking-wide rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 px-3 py-1"
          >
            {language.label} · {language.displayCount}
          </span>
        ))}
        {languages.length > topLanguages.length && (
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
            +{languages.length - topLanguages.length} more
          </span>
        )}
      </div>
    </div>
  );
};
