import React, { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { saveComplaintToDb, updateFormField, clearActiveComplaint } from '../redux/complaintSlice';
import { FileText, Database, RotateCcw } from 'lucide-react';

export default function ComplaintForm({ onShowToast }) {
  const dispatch = useDispatch();
  const form = useSelector((state) => state.complaints.activeComplaint);
  const risk = useSelector((state) => state.complaints.activeRisk);
  const loading = useSelector((state) => state.complaints.loading);

  const prevForm = useRef(form);
  const [flash, setFlash] = useState({});

  useEffect(() => {
    const newFlash = {};
    Object.keys(form).forEach((key) => {
      if (prevForm.current[key] !== form[key] && form[key]) {
        newFlash[key] = true;
      }
    });

    if (Object.keys(newFlash).length > 0) {
      setFlash((prev) => ({ ...prev, ...newFlash }));
      Object.keys(newFlash).forEach((key) => {
        setTimeout(() => {
          setFlash((prev) => ({ ...prev, [key]: false }));
        }, 1500);
      });
    }
    prevForm.current = form;
  }, [form]);

  const handleInputChange = (field, value) => {
    dispatch(updateFormField({ field, value }));
  };

  const handleClear = () => {
    dispatch(clearActiveComplaint());
  };

  const handleSave = () => {
    dispatch(saveComplaintToDb({ form, risk }))
      .unwrap()
      .then(() => {
        onShowToast('Complaint logged and saved in QMS Database successfully!');
      })
      .catch((err) => {
        onShowToast(`Failed to save complaint: ${err}`, 'error');
      });

  };

  const isFormEmpty = !form.product_name && !form.complaint_description;

  return (
    <div className="glass" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <h2>
          <FileText size={20} className="icon-blue" />
          Complaint Registration Form
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-primary-light)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Interactive & AI Synced
          </span>
          {!isFormEmpty && (
            <button
              onClick={handleClear}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem',
                fontSize: '0.8rem',
              }}
              title="Clear Form"
            >
              <RotateCcw size={14} /> Clear
            </button>
          )}
        </div>
      </div>

      <div className="form-content">
        <div className="form-group">
          <label htmlFor="product_name">Product Name</label>
          <input
            id="product_name"
            type="text"
            className={`form-input ${flash.product_name ? 'flash-updated' : ''}`}
            value={form.product_name || ''}
            onChange={(e) => handleInputChange('product_name', e.target.value)}
            disabled={loading}
            placeholder="e.g. Paracetamol"
          />
        </div>

        <div className="form-group">
          <label htmlFor="strength">Strength</label>
          <input
            id="strength"
            type="text"
            className={`form-input ${flash.strength ? 'flash-updated' : ''}`}
            value={form.strength || ''}
            onChange={(e) => handleInputChange('strength', e.target.value)}
            disabled={loading}
            placeholder="e.g. 500 mg"
          />
        </div>

        <div className="form-group">
          <label htmlFor="batch_number">Batch Number</label>
          <input
            id="batch_number"
            type="text"
            className={`form-input ${flash.batch_number ? 'flash-updated' : ''}`}
            value={form.batch_number || ''}
            onChange={(e) => handleInputChange('batch_number', e.target.value)}
            disabled={loading}
            placeholder="e.g. PCM24015"
          />
        </div>

        <div className="form-group">
          <label htmlFor="quantity">Quantity</label>
          <input
            id="quantity"
            type="text"
            className={`form-input ${flash.quantity ? 'flash-updated' : ''}`}
            value={form.quantity || ''}
            onChange={(e) => handleInputChange('quantity', e.target.value)}
            disabled={loading}
            placeholder="e.g. 300 strips"
          />
        </div>

        <div className="form-group">
          <label htmlFor="manufacturing_date">MFG Date</label>
          <input
            id="manufacturing_date"
            type="text"
            className={`form-input ${flash.manufacturing_date ? 'flash-updated' : ''}`}
            value={form.manufacturing_date || ''}
            onChange={(e) => handleInputChange('manufacturing_date', e.target.value)}
            disabled={loading}
            placeholder="e.g. January 2026"
          />
        </div>

        <div className="form-group">
          <label htmlFor="expiry_date">EXP Date</label>
          <input
            id="expiry_date"
            type="text"
            className={`form-input ${flash.expiry_date ? 'flash-updated' : ''}`}
            value={form.expiry_date || ''}
            onChange={(e) => handleInputChange('expiry_date', e.target.value)}
            disabled={loading}
            placeholder="e.g. December 2028"
          />
        </div>

        <div className="form-group full-width">
          <label htmlFor="complaint_description">Complaint Description</label>
          <textarea
            id="complaint_description"
            className={`form-input form-textarea ${flash.complaint_description ? 'flash-updated' : ''}`}
            value={form.complaint_description || ''}
            onChange={(e) => handleInputChange('complaint_description', e.target.value)}
            disabled={loading}
            placeholder="Describe defect details or let AI extract from chat/PDF..."
            rows={3}
          />
        </div>
      </div>

      <div className="form-footer" style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
        <button
          className="btn btn-primary"
          disabled={isFormEmpty || loading}
          onClick={handleSave}
        >
          <Database size={16} />
          {loading ? 'Saving...' : 'Submit to QMS Database'}
        </button>
      </div>
    </div>
  );
}

