import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchComplaintsList } from '../redux/complaintSlice';
import { Search, Trash2, ClipboardList, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';

export default function Dashboard() {
  const dispatch = useDispatch();
  const { complaintsList, loading } = useSelector((state) => state.complaints);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    dispatch(fetchComplaintsList());
  }, [dispatch]);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this complaint record from the database?')) {
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/api/complaints/${id}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        dispatch(fetchComplaintsList());
      } else {
        alert('Failed to delete complaint record.');
      }
    } catch (err) {
      alert(`Error deleting record: ${err.message}`);
    }
  };

  // Filter complaints
  const filteredComplaints = complaintsList.filter((c) => {
    const term = searchTerm.toLowerCase();
    const product = (c.product_name || '').toLowerCase();
    const batch = (c.batch_number || '').toLowerCase();
    const desc = (c.complaint_description || '').toLowerCase();
    return product.includes(term) || batch.includes(term) || desc.includes(term);
  });

  // Calculate metrics
  const total = complaintsList.length;
  const critical = complaintsList.filter(
    (c) => (c.risk_assessment?.severity || '').toLowerCase() === 'critical'
  ).length;
  const major = complaintsList.filter(
    (c) => (c.risk_assessment?.severity || '').toLowerCase() === 'major'
  ).length;
  const minor = complaintsList.filter(
    (c) => (c.risk_assessment?.severity || '').toLowerCase() === 'minor'
  ).length;

  const getSeverityBadgeClass = (severity) => {
    const s = (severity || '').toLowerCase();
    if (s.includes('critical')) return 'table-badge-critical';
    if (s.includes('major')) return 'table-badge-major';
    return 'table-badge-minor';
  };

  const formatDate = (dateStr) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="dashboard-layout">
      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="glass metric-card">
          <div className="metric-info">
            <h3>Total Complaints</h3>
            <div className="metric-number">{total}</div>
          </div>
          <div className="metric-icon-wrapper icon-blue">
            <ClipboardList size={24} />
          </div>
        </div>

        <div className="glass metric-card">
          <div className="metric-info">
            <h3>Critical Risk</h3>
            <div className="metric-number" style={{ color: 'var(--color-critical)' }}>
              {critical}
            </div>
          </div>
          <div className="metric-icon-wrapper icon-red">
            <AlertCircle size={24} />
          </div>
        </div>

        <div className="glass metric-card">
          <div className="metric-info">
            <h3>Major Defects</h3>
            <div className="metric-number" style={{ color: 'var(--color-major)' }}>
              {major}
            </div>
          </div>
          <div className="metric-icon-wrapper icon-orange">
            <AlertCircle size={24} />
          </div>
        </div>

        <div className="glass metric-card">
          <div className="metric-info">
            <h3>Minor Defects</h3>
            <div className="metric-number" style={{ color: 'var(--color-minor)' }}>
              {minor}
            </div>
          </div>
          <div className="metric-icon-wrapper icon-green">
            <ShieldCheck size={24} />
          </div>
        </div>
      </div>

      {/* History and Actions */}
      <div className="glass history-section" style={{ padding: '1.5rem' }}>
        <div className="history-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h2 style={{ fontFamily: 'var(--font-title)', fontSize: '1.25rem' }}>
              QMS Quality Complaints Database Logs
            </h2>
            <button
              onClick={() => dispatch(fetchComplaintsList())}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
              }}
              title="Refresh Logs"
            >
              <RefreshCw size={16} className={loading ? 'spinner' : ''} />
            </button>
          </div>

          <div className="search-input-wrapper">
            <Search size={16} />
            <input
              type="text"
              className="search-input"
              placeholder="Search product, batch, details..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="table-container">
          {filteredComplaints.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No records found.
            </div>
          ) : (
            <table className="qms-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Product</th>
                  <th>Strength</th>
                  <th>Batch</th>
                  <th>Qty</th>
                  <th>Severity</th>
                  <th>Recommended SOP Action</th>
                  <th>Logged Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredComplaints.map((c) => (
                  <tr key={c.id}>
                    <td>#{c.id}</td>
                    <td style={{ fontWeight: '600' }}>{c.product_name}</td>
                    <td>{c.strength || '-'}</td>
                    <td style={{ fontFamily: 'monospace', letterSpacing: '0.05em' }}>
                      {c.batch_number || '-'}
                    </td>
                    <td>{c.quantity || '-'}</td>
                    <td>
                      <span className={`table-badge ${getSeverityBadgeClass(c.risk_assessment?.severity)}`}>
                        {c.risk_assessment?.severity || 'Minor'}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.85rem' }}>
                        {c.risk_assessment?.recommended_action || '-'}
                      </span>
                    </td>
                    <td>{formatDate(c.created_at)}</td>
                    <td>
                      <button
                        onClick={() => handleDelete(c.id)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#ef4444',
                          cursor: 'pointer',
                          opacity: 0.8,
                        }}
                        title="Delete Record"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
