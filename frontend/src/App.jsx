import React, { useState } from 'react';
import Navbar from './components/Navbar';
import ComplaintForm from './components/ComplaintForm';
import RiskAssessment from './components/RiskAssessment';
import AIChat from './components/AIChat';
import Dashboard from './pages/Dashboard';
import { AlertCircle, CheckCircle } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('logger');
  const [toastMessage, setToastMessage] = useState(null);

  const triggerToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
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
          <Dashboard />
        )}
      </main>

      {/* Global Floating AI Co-Pilot */}
      <AIChat />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="toast">
          <CheckCircle size={18} style={{ color: '#10b981' }} />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}
