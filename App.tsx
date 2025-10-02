import React, { useState, useMemo } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { LeaderManager } from './components/LeaderManager';
import { useSocialMediaTracker } from './hooks/useSocialMediaTracker';
import type { Leader } from './types';

export type View = 'dashboard' | 'leaders';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { 
    leaders, 
    posts, 
    isLoading, 
    error, 
    addLeader, 
    removeLeader,
    fetchPostsForLeader
  } = useSocialMediaTracker();

  const handleAddLeader = async (leaderName: string, facebookHandle: string, topics: string[]) => {
    const newLeader: Leader = {
      id: Date.now().toString(),
      name: leaderName,
      handles: { facebook: facebookHandle },
      trackingTopics: topics,
    };
    await addLeader(newLeader);
  };

  const reportData = useMemo(() => {
    return {
      totalPosts: posts.length,
      totalLeaders: leaders.length,
      posts,
    };
  }, [posts, leaders]);

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard reportData={reportData} isLoading={isLoading} error={error} />;
      case 'leaders':
        return (
          <LeaderManager 
            leaders={leaders}
            onAddLeader={handleAddLeader}
            onRemoveLeader={removeLeader}
            onRefreshLeader={fetchPostsForLeader}
            isLoading={isLoading}
          />
        );
      default:
        return <Dashboard reportData={reportData} isLoading={isLoading} error={error} />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200">
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 dark:bg-gray-900 p-4 sm:p-6">
          {renderView()}
        </main>
      </div>
    </div>
  );
};

export default App;