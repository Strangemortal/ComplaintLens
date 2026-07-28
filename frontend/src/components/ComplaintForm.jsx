import React, { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { saveComplaintToDb } from '../redux/complaintSlice';
import { FileText, Database } from 'lucide-react';

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

  const handleSave = () => {
    dispatch(saveComplaintToDb({ form, risk }))
      .unwrap()
      .then(() => {
        onShowToast('Complaint logged and saved in QMS Database successfully!');
      })
      .catch((err) => {
        alert(`Failed to save complaint: ${err}`);
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
        <span style={{ fontSize: '0.8rem', color: 'var(--text-dark)', fontWeight: '600', textTransform: 'uppercase' }}>
          AI Controlled
        </span>
      </div>

      <div className="form-content">
        <div className="form-group">
          <label htmlFor="product_name">Product Name</label>
          <input
            id="product_name"
            type="text"
            className={`form-input ${flash.product_name ? 'flash-updated' : ''}`}
            value={form.product_name || ''}
            disabled
            placeholder="Awaiting AI extraction..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="strength">Strength</label>
          <input
            id="strength"
            type="text"
            className={`form-input ${flash.strength ? 'flash-updated' : ''}`}
            value={form.strength || ''}
            disabled
            placeholder="Awaiting AI extraction..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="batch_number">Batch Number</label>
          <input
            id="batch_number"
            type="text"
            className={`form-input ${flash.batch_number ? 'flash-updated' : ''}`}
            value={form.batch_number || ''}
            disabled
            placeholder="Awaiting AI extraction..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="quantity">Quantity</label>
          <input
            id="quantity"
            type="text"
            className={`form-input ${flash.quantity ? 'flash-updated' : ''}`}
            value={form.quantity || ''}
            disabled
            placeholder="Awaiting AI extraction..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="manufacturing_date">MFG Date</label>
          <input
            id="manufacturing_date"
            type="text"
            className={`form-input ${flash.manufacturing_date ? 'flash-updated' : ''}`}
            value={form.manufacturing_date || ''}
            disabled
            placeholder="Awaiting AI extraction..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="expiry_date">EXP Date</label>
          <input
            id="expiry_date"
            type="text"
            className={`form-input ${flash.expiry_date ? 'flash-updated' : ''}`}
            value={form.expiry_date || ''}
            disabled
            placeholder="Awaiting AI extraction..."
          />
        </div>

        <div className="form-group full-width">
          <label htmlFor="complaint_description">Complaint Description</label>
          <textarea
            id="complaint_description"
            className={`form-input form-textarea ${flash.complaint_description ? 'flash-updated' : ''}`}
            value={form.complaint_description || ''}
            disabled
            placeholder="Awaiting AI extraction..."
          />
        </div>
      </div>

      <div className="form-footer">
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
