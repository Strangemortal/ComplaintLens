import React, { useState, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { uploadComplaintPDF } from '../redux/complaintSlice';
import { FileUp, CheckCircle, AlertCircle } from 'lucide-react';

export default function DocumentUploader() {
  const dispatch = useDispatch();
  const loading = useSelector((state) => state.complaints.loading);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // 'success' | 'error' | null
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processFile(files[0]);
    }
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processFile(files[0]);
    }
    // Reset file input value so selecting the same file again works
    e.target.value = '';
  };

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const processFile = (file) => {
    if (!file || !file.name || !file.name.toLowerCase().endsWith('.pdf')) {
      setUploadStatus('error');
      setErrorMessage('Only PDF documents are supported.');
      return;
    }


    setUploadStatus(null);
    setErrorMessage('');

    dispatch(uploadComplaintPDF(file))
      .unwrap()
      .then(() => {
        setUploadStatus('success');
        setTimeout(() => setUploadStatus(null), 3000);
      })
      .catch((err) => {
        setUploadStatus('error');
        setErrorMessage(err || 'Failed to upload PDF.');
      });
  };

  return (
    <div className="uploader-wrapper">
      <div className="uploader-container">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf"
          style={{ display: 'none' }}
        />

        {loading ? (
          <div className="uploading-spinner">
            <div className="spinner"></div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              AI parsing PDF document. Extracting form values & assessing risk...
            </p>
          </div>
        ) : uploadStatus === 'success' ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-minor)' }}>
            <CheckCircle size={18} />
            <span style={{ fontSize: '0.85rem', fontWeight: '500' }}>
              PDF processed and complaint extracted successfully!
            </span>
          </div>
        ) : (
          <div
            className={`uploader-dropzone ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={triggerFileInput}
          >
            <FileUp size={24} />
            <p>
              Drag & drop a <strong>Complaint.pdf</strong> report here or <span>browse files</span>
            </p>
            {uploadStatus === 'error' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--color-critical)', marginTop: '0.25rem' }}>
                <AlertCircle size={14} />
                <span style={{ fontSize: '0.75rem', fontWeight: '600' }}>{errorMessage}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
