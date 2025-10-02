
import React from 'react';
import type { View } from '../App';

interface SidebarProps {
  currentView: View;
  setCurrentView: (view: View) => void;
}

const NavItem: React.FC<{
  viewName: View;
  label: string;
  currentView: View;
  setCurrentView: (view: View) => void;
  children: React.ReactNode;
}> = ({ viewName, label, currentView, setCurrentView, children }) => {
  const isActive = currentView === viewName;
  const baseClasses = 'flex items-center px-4 py-3 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200';
  const activeClasses = 'bg-indigo-500 text-white dark:bg-indigo-500 dark:text-white hover:bg-indigo-600 dark:hover:bg-indigo-600';
  
  return (
    <a
      href="#"
      className={`${baseClasses} ${isActive ? activeClasses : ''}`}
      onClick={(e) => {
        e.preventDefault();
        setCurrentView(viewName);
      }}
    >
      {children}
      <span className="mx-4 font-medium">{label}</span>
    </a>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({ currentView, setCurrentView }) => {
  return (
    <aside className="hidden md:flex flex-col w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-center h-20 border-b border-gray-200 dark:border-gray-700">
        <span className="text-2xl font-semibold text-indigo-500">PoliTrack</span>
      </div>
      <nav className="flex-1 px-4 py-4">
        <NavItem viewName="dashboard" label="Dashboard" currentView={currentView} setCurrentView={setCurrentView}>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16v16H4zM4 9h16M9 4v16"/></svg>
        </NavItem>
        <NavItem viewName="leaders" label="Manage Leaders" currentView={currentView} setCurrentView={setCurrentView}>
         <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/></svg>
        </NavItem>
      </nav>
    </aside>
  );
};
