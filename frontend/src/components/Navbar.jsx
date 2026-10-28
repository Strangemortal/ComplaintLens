import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { Bot, LayoutDashboard, PlusCircle, RefreshCw, Zap, ShieldAlert } from 'lucide-react';
import { clearActiveComplaint } from '../redux/complaintSlice';

export default function Navbar({ activeTab, setActiveTab }) {
  const dispatch = useDispatch();
  const [llmStatus, setLlmStatus] = useState({
    llm_live: true,
    mode: 'live',
    provider: 'Groq (qwen/qwen3.8-27b)',
    reason: null
  });
  const [checkingStatus, setCheckingStatus] = useState(false);

  const fetchHealth = async () => {
    setCheckingStatus(true);
    try {
      const res = await fetch('http://localhost:8000/api/health');
      if (res.ok) {
        const data = await res.json();
        if (data.llm) {
          setLlmStatus(data.llm);
        }
      }
    } catch (_) {
      // Backend not yet reachable or restarting
    } finally {
      setCheckingStatus(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleResetCircuit = async () => {
    try {
      await fetch('http://localhost:8000/api/chat/reset-circuit', { method: 'POST' });
      fetchHealth();
    } catch (_) {}
  };

  const handleNewComplaint = () => {
    dispatch(clearActiveComplaint());
    setActiveTab('logger');
  };

  return (
    <nav className="navbar">
      <div className="nav-brand" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('logger')}>
        <Bot size={28} />
        ComplaintLens <span>QMS AI Co-Pilot</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Live LLM Provider Status Badge */}
        <div
          className={`status-pill ${llmStatus.llm_live ? 'status-pill-live' : 'status-pill-mock'}`}
          title={llmStatus.llm_live ? `Connected to ${llmStatus.provider}` : `Using local rule engine: ${llmStatus.reason || 'Mock'}. Click to retry.`}
          onClick={!llmStatus.llm_live ? handleResetCircuit : fetchHealth}
          style={{ cursor: 'pointer' }}
        >
          <span className={`status-dot ${llmStatus.llm_live ? 'dot-pulse' : ''}`} />
          {checkingStatus ? (
            <span style={{ fontSize: '0.78rem' }}>Checking AI...</span>
          ) : llmStatus.llm_live ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.78rem' }}>
              <Zap size={12} /> {llmStatus.provider || 'AI Live'}
            </span>
          ) : (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.78rem' }}>
              <ShieldAlert size={12} /> Local Mock Engine (Click to Reset)
            </span>
          )}
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

        <button
          className="btn btn-primary"
          style={{ padding: '0.45rem 1rem', fontSize: '0.85rem' }}
          onClick={handleNewComplaint}
          title="Start fresh complaint entry"
        >
          <PlusCircle size={15} />
          New Complaint
        </button>
      </div>
    </nav>
  );
}
