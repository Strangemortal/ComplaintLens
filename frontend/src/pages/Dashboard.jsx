import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchComplaintsList, loadComplaintRecord, deleteComplaintFromDb } from '../redux/complaintSlice';
import { Search, Trash2, ClipboardList, ShieldCheck, AlertCircle, RefreshCw, Eye, Download, FileSpreadsheet, ShieldAlert, X, ExternalLink } from 'lucide-react';

export default function Dashboard({ onSwitchTab, onShowToast }) {
  const dispatch = useDispatch();
  const { complaintsList, loading } = useSelector((state) => state.complaints);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all'); // 'all' | 'critical' | 'major' | 'minor'
  const [inspectModalRecord, setInspectModalRecord] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    dispatch(fetchComplaintsList());
  }, [dispatch]);

  const handleInspectInLogger = (complaint) => {
    dispatch(loadComplaintRecord(complaint));
    setInspectModalRecord(null);
    if (onSwitchTab) {
      onSwitchTab('logger');
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await dispatch(deleteComplaintFromDb(deleteTarget.id)).unwrap();
      if (onShowToast) {
        onShowToast(`Complaint #${deleteTarget.id} successfully removed from QMS database.`);
      }
      setDeleteTarget(null);
    } catch (err) {
      if (onShowToast) {
        onShowToast(`Failed to delete record: ${err}`, 'error');
      }
    } finally {
      setIsDeleting(false);
    }
  };

  // Export to CSV Function
  const handleExportCSV = () => {
    if (complaintsList.length === 0) {
      if (onShowToast) onShowToast('No complaints to export.', 'error');
      return;
    }

    const headers = [
      'ID',
      'Product Name',
      'Strength',
      'Batch Number',
      'Quantity Affected',
      'MFG Date',
      'EXP Date',
      'Complaint Description',
      'Severity',
      'Priority',
      'Risk Justification',
      'Patient Impact',
      'Recommended SOP Action',
      'Logged At (UTC)'
    ];

    const rows = complaintsList.map((c) => [
      c.id,
      `"${(c.product_name || '').replace(/"/g, '""')}"`,
      `"${(c.strength || '').replace(/"/g, '""')}"`,
      `"${(c.batch_number || '').replace(/"/g, '""')}"`,
      `"${(c.quantity || '').replace(/"/g, '""')}"`,
      `"${(c.manufacturing_date || '').replace(/"/g, '""')}"`,
      `"${(c.expiry_date || '').replace(/"/g, '""')}"`,
      `"${(c.complaint_description || '').replace(/"/g, '""')}"`,
      `"${(c.risk_assessment?.severity || '').replace(/"/g, '""')}"`,
      `"${(c.risk_assessment?.priority || '').replace(/"/g, '""')}"`,
      `"${(c.risk_assessment?.reason || '').replace(/"/g, '""')}"`,
      `"${(c.risk_assessment?.impact || '').replace(/"/g, '""')}"`,
      `"${(c.risk_assessment?.recommended_action || '').replace(/"/g, '""')}"`,
      `"${c.created_at || ''}"`
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `QMS_Complaint_Logs_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    if (onShowToast) onShowToast('CSV Report downloaded successfully!');
  };

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

  // Filter complaints by search AND severity chip
  const filteredComplaints = complaintsList.filter((c) => {
    const term = searchTerm.toLowerCase();
    const product = (c.product_name || '').toLowerCase();
    const batch = (c.batch_number || '').toLowerCase();
    const desc = (c.complaint_description || '').toLowerCase();
    const matchesSearch = product.includes(term) || batch.includes(term) || desc.includes(term);

    if (!matchesSearch) return false;

    if (severityFilter === 'all') return true;
    const itemSev = (c.risk_assessment?.severity || 'minor').toLowerCase();
    return itemSev === severityFilter;
  });

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
        <div className="glass metric-card" style={{ cursor: 'pointer' }} onClick={() => setSeverityFilter('all')}>
          <div className="metric-info">
            <h3>Total Complaints</h3>
            <div className="metric-number">{total}</div>
          </div>
          <div className="metric-icon-wrapper icon-blue">
            <ClipboardList size={24} />
          </div>
        </div>

        <div className="glass metric-card" style={{ cursor: 'pointer' }} onClick={() => setSeverityFilter('critical')}>
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

        <div className="glass metric-card" style={{ cursor: 'pointer' }} onClick={() => setSeverityFilter('major')}>
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

        <div className="glass metric-card" style={{ cursor: 'pointer' }} onClick={() => setSeverityFilter('minor')}>
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
        <div className="history-header" style={{ flexWrap: 'wrap', gap: '1rem' }}>
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

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {/* Export CSV Button */}
            <button
              onClick={handleExportCSV}
              className="btn btn-secondary"
              style={{ padding: '0.45rem 0.85rem', fontSize: '0.82rem' }}
              title="Export all complaints to CSV spreadsheet"
            >
              <FileSpreadsheet size={15} style={{ color: '#10b981' }} />
              Export CSV
            </button>

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
        </div>

        {/* Quick Severity Filter Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', marginBottom: '0.25rem' }}>
          <button
            className={`filter-chip ${severityFilter === 'all' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('all')}
          >
            All Complaints ({total})
          </button>
          <button
            className={`filter-chip chip-critical ${severityFilter === 'critical' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('critical')}
          >
            Critical ({critical})
          </button>
          <button
            className={`filter-chip chip-major ${severityFilter === 'major' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('major')}
          >
            Major ({major})
          </button>
          <button
            className={`filter-chip chip-minor ${severityFilter === 'minor' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('minor')}
          >
            Minor ({minor})
          </button>
        </div>

        <div className="table-container">
          {filteredComplaints.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No records found matching current criteria.
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
                      <div className="table-actions-cell">
                        <button
                          onClick={() => setInspectModalRecord(c)}
                          className="table-action-btn inspect-btn"
                          title={`View full details of Record #${c.id}`}
                          aria-label={`Inspect Record #${c.id}`}
                        >
                          <Eye size={15} />
                          <span>Inspect</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget(c)}
                          className="table-action-btn delete-btn"
                          title={`Delete Record #${c.id}`}
                          aria-label={`Delete Record #${c.id}`}
                        >
                          <Trash2 size={15} />
                          <span>Delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Detailed QMS Investigation Inspection Modal */}
      {inspectModalRecord && (
        <div className="modal-backdrop" onClick={() => setInspectModalRecord(null)}>
          <div className="modal-card" style={{ maxWidth: '640px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="metric-icon-wrapper icon-blue">
                <ClipboardList size={22} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3>QMS Complaint Investigation Record #{inspectModalRecord.id}</h3>
                  <button
                    onClick={() => setInspectModalRecord(null)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  >
                    <X size={18} />
                  </button>
                </div>
                <p>Logged on {formatDate(inspectModalRecord.created_at)}</p>
              </div>
            </div>

            <div className="modal-body" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Product Name</span>
                  <p style={{ fontWeight: '600', color: '#fff' }}>{inspectModalRecord.product_name || '-'}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Strength / Dosage</span>
                  <p style={{ fontWeight: '600', color: '#fff' }}>{inspectModalRecord.strength || '-'}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Batch Number</span>
                  <p style={{ fontFamily: 'monospace', color: '#60a5fa' }}>{inspectModalRecord.batch_number || '-'}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Quantity Affected</span>
                  <p style={{ fontWeight: '600', color: '#fff' }}>{inspectModalRecord.quantity || '-'}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Manufacturing Date</span>
                  <p style={{ color: '#fff' }}>{inspectModalRecord.manufacturing_date || '-'}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Expiry Date</span>
                  <p style={{ color: '#fff' }}>{inspectModalRecord.expiry_date || '-'}</p>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Full Defect Narrative</span>
                <p style={{ background: 'rgba(255,255,255,0.03)', padding: '0.65rem', borderRadius: '6px', marginTop: '0.25rem', fontSize: '0.88rem' }}>
                  {inspectModalRecord.complaint_description || 'No description provided.'}
                </p>
              </div>

              {inspectModalRecord.risk_assessment && (
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: '600', fontSize: '0.85rem', color: '#fff' }}>AI Risk Assessment</span>
                    <span className={`table-badge ${getSeverityBadgeClass(inspectModalRecord.risk_assessment.severity)}`}>
                      {inspectModalRecord.risk_assessment.severity} ({inspectModalRecord.risk_assessment.priority} Priority)
                    </span>
                  </div>

                  <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div>
                      <strong style={{ color: 'var(--text-muted)' }}>Risk Justification:</strong>
                      <p style={{ marginTop: '0.15rem' }}>{inspectModalRecord.risk_assessment.reason || '-'}</p>
                    </div>
                    <div>
                      <strong style={{ color: 'var(--text-muted)' }}>Clinical / Patient Impact:</strong>
                      <p style={{ marginTop: '0.15rem' }}>{inspectModalRecord.risk_assessment.impact || '-'}</p>
                    </div>
                    <div>
                      <strong style={{ color: 'var(--text-muted)' }}>Recommended SOP Corrective Action:</strong>
                      <p style={{ marginTop: '0.15rem', color: '#60a5fa' }}>{inspectModalRecord.risk_assessment.recommended_action || '-'}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="btn-cancel"
                onClick={() => setInspectModalRecord(null)}
              >
                Close
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => handleInspectInLogger(inspectModalRecord)}
              >
                <ExternalLink size={14} />
                Load in Logger to Edit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="modal-backdrop" onClick={() => !isDeleting && setDeleteTarget(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-icon-danger">
                <Trash2 size={22} />
              </div>
              <div>
                <h3>Delete Complaint Record</h3>
                <p>This action will permanently delete the record and its risk assessment.</p>
              </div>
            </div>
            <div className="modal-body">
              Are you sure you want to permanently delete record <strong>#{deleteTarget.id}</strong> (
              <span style={{ color: '#60a5fa', fontWeight: '600' }}>
                {deleteTarget.product_name || 'Unnamed Product'}
              </span>
              {deleteTarget.batch_number ? ` - Batch: ${deleteTarget.batch_number}` : ''}) from the QMS database?
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="btn-cancel"
                disabled={isDeleting}
                onClick={() => setDeleteTarget(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-danger"
                disabled={isDeleting}
                onClick={handleConfirmDelete}
              >
                {isDeleting ? (
                  <>
                    <RefreshCw size={14} className="spinner" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 size={14} />
                    <span>Confirm Delete</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
