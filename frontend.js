"use client";
import { useState } from 'react';

// --- Helper Components ---
const TabButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors duration-200 ${
      active
        ? 'bg-gray-800 text-white border-b-2 border-blue-400'
        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
    }`}
  >
    {children}
  </button>
);

const Card = ({ children, title }) => (
    <div className="bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
        <h2 className="text-xl font-semibold text-white mb-4 border-b border-gray-600 pb-2">{title}</h2>
        {children}
    </div>
);


// --- Main Page Component ---
export default function HomePage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView />;
      case 'ingestion':
        return <IngestionControlView />;
      case 'configuration':
        return <ConfigurationView />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-gray-900 min-h-screen text-gray-200 font-sans">
      <header className="bg-gray-800/50 backdrop-blur-sm shadow-md sticky top-0 z-10">
        <nav className="container mx-auto px-6 py-3">
          <h1 className="text-2xl font-bold text-white">Project Sentinel</h1>
          <p className="text-sm text-gray-400">Political Intelligence Platform</p>
        </nav>
      </header>

      <main className="container mx-auto p-6">
        <div className="border-b border-gray-700 mb-6">
          <div className="flex space-x-2">
            <TabButton active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')}>Dashboard</TabButton>
            <TabButton active={activeTab === 'ingestion'} onClick={() => setActiveTab('ingestion')}>Ingestion Control</TabButton>
            <TabButton active={activeTab === 'configuration'} onClick={() => setActiveTab('configuration')}>Configuration</TabButton>
          </div>
        </div>
        <div>{renderContent()}</div>
      </main>
    </div>
  );
}

// --- View Components ---
const DashboardView = () => (
    <div>
        <Card title="Search & Analysis">
            <div className="space-y-4">
                <input type="text" placeholder="Search for a Politician, Bill, or Topic..." className="w-full bg-gray-700 text-white rounded-md p-2 border border-gray-600 focus:ring-blue-500 focus:border-blue-500"/>
                <div className="flex justify-end">
                    <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition-colors">Analyze</button>
                </div>
            </div>
        </Card>
        <Card title="Key Metrics Overview">
             <p className="text-gray-400">Analysis results and data visualizations will appear here...</p>
        </Card>
    </div>
);

const IngestionControlView = () => (
    <Card title="Manual Data Ingestion">
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Target URL</label>
                <input type="url" placeholder="https://www.congress.gov/bill/..." className="w-full bg-gray-700 text-white rounded-md p-2 border border-gray-600"/>
            </div>
             <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Crawl Depth</label>
                <select className="w-full bg-gray-700 text-white rounded-md p-2 border border-gray-600">
                    <option>0 (This page only)</option>
                    <option>1 (This page and linked pages)</option>
                    <option>2</option>
                </select>
            </div>
            <div className="flex justify-end">
                <button className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md transition-colors">Start Ingestion Job</button>
            </div>
        </div>
    </Card>
);

const ConfigurationView = () => (
     <Card title="System Configuration">
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-semibold text-blue-400 mb-2">Crawler Sources</h3>
                <textarea rows={8} className="w-full bg-gray-700 text-white rounded-md p-2 border border-gray-600" defaultValue={"https://www.congress.gov/\nhttps://www.whitehouse.gov/briefing-room/\nhttps://www.cia.gov/readingroom/"}></textarea>
                 <p className="text-xs text-gray-500 mt-1">One URL per line. These are the root URLs for the automated Document Scout Agent.</p>
            </div>
             <div>
                <h3 className="text-lg font-semibold text-blue-400 mb-2">API Keys & Secrets</h3>
                <div className="space-y-2">
                    <input type="text" placeholder="LANGFUSE_SECRET_KEY" className="w-full bg-gray-700 text-white rounded-md p-2 border border-gray-600"/>
                    <input type="password" placeholder="CLOUDFLARE_API_TOKEN" className="w-full bg-gray-700 text-white rounded-md p-2 border border-gray-600"/>
                </div>
            </div>
            <div className="flex justify-end">
                <button className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-md transition-colors">Save Configuration</button>
            </div>
        </div>
    </Card>
);
