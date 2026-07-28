import React from 'react';
import { Bot, LayoutDashboard } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Bot size={28} />
        AIVOA <span>QMS Complaint Co-Pilot</span>
      </div>
      <div className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === 'logger' ? 'active' : ''}`}
          onClick={() => setActiveTab('logger')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Bot size={16} />
            AI Co-Pilot Logger
          </div>
        </button>
        <button
          className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <LayoutDashboard size={16} />
            Dashboard
          </div>
        </button>
      </div>
    </nav>
  );
}
