import React from 'react';
import { useSelector } from 'react-redux';
import { ShieldAlert, AlertOctagon, AlertTriangle, Play, HelpCircle } from 'lucide-react';

export default function RiskAssessment() {
  const risk = useSelector((state) => state.complaints.activeRisk);

  const getSeverityStyle = (severity) => {
    const s = (severity || '').toLowerCase();
    if (s.includes('critical')) return 'severity-critical';
    if (s.includes('major')) return 'severity-major';
    if (s.includes('minor')) return 'severity-minor';
    return '';
  };

  const getSeverityIcon = (severity) => {
    const s = (severity || '').toLowerCase();
    if (s.includes('critical')) return <AlertOctagon />;
    if (s.includes('major')) return <AlertTriangle />;
    return <ShieldAlert />;
  };

  const isRiskEmpty = !risk.severity && !risk.priority && !risk.reason;

  return (
    <div className="glass" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <h2>
          <ShieldAlert size={20} className="icon-orange" />
          AI Risk Assessment & Routing
        </h2>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-dark)', fontWeight: '600', textTransform: 'uppercase' }}>
          Real-time
        </span>
      </div>

      {isRiskEmpty ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <HelpCircle size={48} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
          <p>Provide a complaint to generate an automated QMS risk assessment.</p>
        </div>
      ) : (
        <div className="risk-container">
          <div className="risk-badges-row">
            <div className={`risk-badge-card ${getSeverityStyle(risk.severity)}`}>
              {getSeverityIcon(risk.severity)}
              <div>
                <div className="risk-label">Severity</div>
                <div className="risk-value">{risk.severity || 'Unknown'}</div>
              </div>
            </div>

            <div className="risk-badge-card">
              <Play size={20} style={{ color: 'var(--color-indigo)' }} />
              <div>
                <div className="risk-label">Priority</div>
                <div className="risk-value" style={{ color: 'var(--color-indigo)' }}>
                  {risk.priority || 'Medium'}
                </div>
              </div>
            </div>
          </div>

          <div className="risk-grid">
            <div className="risk-item full-width">
              <h4>Safety Impact Analysis</h4>
              <p>{risk.impact || 'Analyzing potential patient safety or product efficacy impact...'}</p>
            </div>

            <div className="risk-item full-width">
              <h4>QA Recommended SOP Actions</h4>
              <p>{risk.recommended_action || 'Determining appropriate standard operating procedures...'}</p>
            </div>

            <div className="risk-item full-width">
              <h4>Assessment Reasoning</h4>
              <p>{risk.reason || 'No reasoning provided.'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
