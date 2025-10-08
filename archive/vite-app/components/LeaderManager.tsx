import React, { useState } from 'react';
import type { Leader } from '../types';
import { LoadingSpinner } from './LoadingSpinner';

interface LeaderManagerProps {
  leaders: Leader[];
  onAddLeader: (name: string, facebookHandle: string, topics: string[]) => Promise<void>;
  onRemoveLeader: (leaderId: string) => void;
  onRefreshLeader: (leaderId: string) => void;
  isLoading: boolean;
}

export const LeaderManager: React.FC<LeaderManagerProps> = ({ leaders, onAddLeader, onRemoveLeader, onRefreshLeader, isLoading }) => {
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [facebookHandle, setFacebookHandle] = useState('');
  const [topics, setTopics] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    await onAddLeader(name, facebookHandle, topics.split(',').map(t => t.trim()));
    setIsSubmitting(false);
    setShowModal(false);
    setName('');
    setFacebookHandle('');
    setTopics('');
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Tracked Leaders</h2>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50 transition-colors"
        >
          Add Leader
        </button>
      </div>
      <div className="space-y-4">
        {leaders.map(leader => (
          <LeaderCard 
            key={leader.id} 
            leader={leader} 
            onRemove={onRemoveLeader} 
            onRefresh={onRefreshLeader}
          />
        ))}
        {leaders.length === 0 && (
            <p className="text-center text-gray-500 dark:text-gray-400 py-10">No leaders are being tracked. Add one to get started.</p>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-8 w-full max-w-md m-4">
            <h3 className="text-xl font-bold mb-4">Add a New Leader</h3>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-gray-700 dark:text-gray-300 mb-2" htmlFor="name">Leader's Name</label>
                <input type="text" id="name" value={name} onChange={e => setName(e.target.value)} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" required />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 dark:text-gray-300 mb-2" htmlFor="facebook">Facebook Handle (e.g., @handle)</label>
                <input type="text" id="facebook" value={facebookHandle} onChange={e => setFacebookHandle(e.target.value)} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" required/>
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 dark:text-gray-300 mb-2" htmlFor="topics">Tracking Topics (comma-separated)</label>
                <input type="text" id="topics" value={topics} onChange={e => setTopics(e.target.value)} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" placeholder="e.g., economy, healthcare" required />
              </div>
              <div className="flex justify-end space-x-4">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 bg-gray-200 dark:bg-gray-600 rounded-lg hover:bg-gray-300">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 flex items-center" disabled={isSubmitting}>
                   {isSubmitting && <LoadingSpinner />} 
                   <span className={isSubmitting ? 'ml-2' : ''}>Add Leader</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};


const LeaderCard: React.FC<{ leader: Leader; onRemove: (id: string) => void; onRefresh: (id: string) => void; }> = ({ leader, onRemove, onRefresh }) => (
    <div className="p-4 border dark:border-gray-700 rounded-lg flex justify-between items-center bg-gray-50 dark:bg-gray-700/50">
        <div>
            <p className="font-bold text-lg text-gray-800 dark:text-gray-100">{leader.name}</p>
            <p className="text-sm text-indigo-500">{leader.handles.facebook || leader.handles.twitter}</p>
            <div className="mt-2 flex flex-wrap gap-2">
                {leader.trackingTopics.map(topic => (
                    <span key={topic} className="text-xs font-medium px-2 py-1 rounded-full bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300">{topic}</span>
                ))}
            </div>
        </div>
        <div className="flex space-x-2">
            <button onClick={() => onRefresh(leader.id)} className="p-2 text-gray-500 hover:text-blue-500 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600" title="Refresh Data">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
            </button>
            <button onClick={() => onRemove(leader.id)} className="p-2 text-gray-500 hover:text-red-500 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600" title="Remove Leader">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
        </div>
    </div>
);