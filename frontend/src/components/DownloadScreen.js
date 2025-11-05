// src/components/DownloadScreen.js
import React from "react";
import "./DownloadScreen.css";

function DownloadScreen({ memoData, onReset }) {
  const handleOpenDoc = () => {
    if (memoData.docUrl) {
      window.open(memoData.docUrl, '_blank');
    }
  };

  return (
    <div className="download-screen">
      <div className="success-icon">
        <svg viewBox="0 0 52 52" className="checkmark">
          <circle className="checkmark-circle" cx="26" cy="26" r="25" fill="none" />
          <path
            className="checkmark-check"
            fill="none"
            d="M14.1 27.2l7.1 7.2 16.7-16.8"
          />
        </svg>
      </div>

      <h2 className="success-title">Memo Generated Successfully</h2>

      <div className="memo-info">
        <div className="info-item">
          <span className="info-label">Company</span>
          <span className="info-value">{memoData.companyName}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Sections</span>
          <span className="info-value">{memoData.sections} completed</span>
        </div>
        <div className="info-item">
          <span className="info-label">Location</span>
          <span className="info-value">Google Drive (shared with wyldvc.com)</span>
        </div>
      </div>

      <div className="action-buttons">
        {memoData.docUrl && (
          <button
            onClick={handleOpenDoc}
            className="download-button"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Open Google Doc
          </button>
        )}

        <button onClick={onReset} className="new-memo-button">
          Generate Another Memo
        </button>
      </div>
    </div>
  );
}

export default DownloadScreen;
