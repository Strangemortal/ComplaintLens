import React, { useState } from 'react';
import Navbar from './components/Navbar';
import ComplaintForm from './components/ComplaintForm';
import RiskAssessment from './components/RiskAssessment';
import AIChat from './components/AIChat';
import Dashboard from './pages/Dashboard';
import { AlertCircle, CheckCircle } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('logger');
  const [toast, setToast] = useState(null);

  const triggerToast = (msg, type = 'success') => {
    setToast({ message: msg, type });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  return (
    <div className="app-container">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="page-content">
        {activeTab === 'logger' ? (
          <div className="copilot-layout">
            <ComplaintForm onShowToast={triggerToast} />
            <RiskAssessment />
          </div>
        ) : (
          <Dashboard onSwitchTab={setActiveTab} onShowToast={triggerToast} />
        )}
      </main>

      {/* Global Floating AI Co-Pilot */}
      <AIChat />

      {/* Toast Notification */}
      {toast && (
        <div className={`toast ${toast.type === 'error' ? 'toast-error' : ''}`}>
          {toast.type === 'error' ? (
            <AlertCircle size={18} style={{ color: '#ef4444' }} />
          ) : (
            <CheckCircle size={18} style={{ color: '#10b981' }} />
          )}
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}

